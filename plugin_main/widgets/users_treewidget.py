from typing import Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

import requests, copy


class UsersTreeWidget(QTreeWidget):
    selected_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None,pre_selected_ids:Optional[list[dict]]=None,  all_users=None , view_type:str='select'):
        super().__init__(parent)
        self.view_type = view_type
        self.map_id_to_selected_ids = {}
        self.setHeaderLabels(['선택(필수)', '이름', '직책', '직급', '부서'])
        self.all_users = all_users or self.get_all_users_from_info()
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.itemClicked.connect(self.handle_item_clicked)
        self.map_id_to_selected_ids = {}
        self.pre_selected_ids = set()
        self.populate_tree()

        if pre_selected_ids :
            self.map_id_to_selected_ids = { selected.get('user'): selected for selected in pre_selected_ids }
            self.pre_selected_ids = set( self.map_id_to_selected_ids.keys())
            self.update_pre_selected_ids(pre_selected_ids)

    def get_all_users_from_info(self):
        return INFO.ALL_USER

    def update_pre_selected_ids(self, pre_selected_ids:list[dict]):
        self.pre_selected_ids = pre_selected_ids
        for selected in pre_selected_ids:
            self.simulate_click_user_by_id(selected.get('user'))

    def simulate_click_user_by_id(self, user_id: int):
        def recursive_click(item):
            user = item.data(0, Qt.ItemDataRole.UserRole)
            if user and user.get('id') == user_id:
                # 현재 상태 읽고 토글
                current_state = item.checkState(0)
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(0, new_state)

                # 클릭한 것처럼 이벤트 트리거
                self.handle_item_clicked(item, 0)
                return True
            for i in range(item.childCount()):
                if recursive_click(item.child(i)):
                    return True
            return False

        for i in range(self.topLevelItemCount()):
            if recursive_click(self.topLevelItem(i)):
                break

    def populate_tree(self):
        self.clear()
        departments = self.group_users_by_department()

        for dept3, dept2_data in departments.items():
            dept3_item = self._create_department_item(self, dept3)
            self._populate_department(dept3_item, dept2_data)

    def group_users_by_department(self):
        grouped = {}
        for user in self.all_users:
            if user.get('user_성명') == 'admin':
                continue
            d1 = user.get('기본조직1', '')
            d2 = user.get('기본조직2', '')
            d3 = user.get('기본조직3', '')
            grouped.setdefault(d3, {}).setdefault(d2, {}).setdefault(d1, []).append(user)
        return grouped

    def _create_department_item(self, parent, dept_name):
        item = QTreeWidgetItem(parent)
        item.setText(1, dept_name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setExpanded(False)

        if self.view_type == 'preview':
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

        return item

    def _populate_department(self, parent_item, dept_data):
        if isinstance(dept_data, list):
            for user in dept_data:
                self._create_user_item(parent_item, user)
        elif isinstance(dept_data, dict):
            for sub_dept, sub_data in dept_data.items():
                sub_item = self._create_department_item(parent_item, sub_dept)
                self._populate_department(sub_item, sub_data)

    def _create_user_item(self, parent, user):
        """ 0 column은 userObj가 아닌, self.pre_selected_ids 에 있는 사용자 정보를 사용 """
        item = QTreeWidgetItem(parent)
        item.setText(1, user.get('user_성명', ''))
        item.setText(2, user.get('user_직책', ''))
        item.setText(3, user.get('user_직급', ''))
        item.setText(4, user.get('기본조직1', ''))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        #####
        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, user )

        if self.view_type == 'preview':
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

        return item
    
    def get_selected_user(self, user_id:int):
        if user_id in self.map_id_to_selected_ids:
            return self.map_id_to_selected_ids.get(user_id)
        else :
            defaultObj = self.selected_ids[0] if self.selected_ids else {}
            defaultObj['id'] = -1
            defaultObj['user'] = user_id
            return defaultObj
        

    def handle_item_clicked(self, item, column):
        user = item.data(0, Qt.ItemDataRole.UserRole)
        new_state = item.checkState(0)

        if user is None:
            # 조직 노드인 경우 하위 사용자 항목도 같이 적용
            self._apply_check_to_children(item, new_state)
            self._apply_check_to_parent (item.parent())
            return
            
        print ( user, item.checkState(0)) 
        self._apply_check_to_parent(item.parent())
        # self.parent().update_select_user({'checked':item.checkState(0), 'user_id':user.get('id')})
        self.selected_changed.emit({
            'is_선택': item.checkState(0) == Qt.CheckState.Checked,
            'user_id': user.get('id')
        })

        # self._apply_check_to_parent (item.parent())

    def _apply_check_to_children(self, parent_item, state):
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(0, state)
            self.handle_item_clicked(child, 0)  # 하위 노드에 재귀 호출

    def _apply_check_to_parent(self, item):
        if item is None:
            return

        checked = 0
        partial = 0
        total = item.childCount()

        for i in range(total):
            child = item.child(i)
            state = child.checkState(0)
            if state == Qt.CheckState.Checked:
                checked += 1
            elif state == Qt.CheckState.PartiallyChecked:
                partial += 1

        if checked == total:
            item.setCheckState(0, Qt.CheckState.Checked)
        elif checked == 0 and partial == 0:
            item.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            item.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self._apply_check_to_parent(item.parent())

    def get_checked_user_ids(self) -> list[int]:
        checked_ids = []
        for i in range(self.topLevelItemCount()):
            self._collect_checked_users(self.topLevelItem(i), checked_ids)
        return [ user.get('id') for user in checked_ids ]


    def _collect_checked_users(self, item, checked_users):
        """재귀적으로 체크된 사용자 수집"""
        # 리프 노드(사용자)인 경우 체크 상태 확인
        if item.childCount() == 0 and item.checkState(0) == Qt.CheckState.Checked:
            user_data = item.data(0, Qt.ItemDataRole.UserRole)
            if user_data:
                checked_users.append(user_data)
        
        # 하위 항목에 대해 재귀 호출
        for i in range(item.childCount()):
            self._collect_checked_users(item.child(i), checked_users)


from plugin_main.widgets.users_tablewidget import TableModel_Users, TableView_Users, Delegate_Users, UsersTableWidget


class UsersDialog(QDialog):
    """사용자 목록을 표시하는 다이얼로그
        kwargs:
            app_ID:int : 앱 권한 ID
            pre_selected_ids:list[dict] : 이전 선택된 사용자 ID 목록  [{'id': 528, 'user': 32}, {'id': 529, 'user': 38}, {'id': 530, 'user': 5}, {'id': 2668, 'user': 71}]
            all_users:list[dict] : 전체 사용자 목록
            api_url:str : 사용자 목록 조회 API URL
            on_complete_callback:callable : 완료 콜백 함수
    """
    users_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, app_ID:int=None, pre_selected_ids:list[dict]=None, 
                 all_users=None, api_url=None, on_complete_channelName=None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle('사용자 목록')
        self.resize(600, 500)
        self.event_bus = event_bus
        self.app_ID = app_ID
        self.pre_selected_ids = pre_selected_ids or []
        self.map_id_to_selected_ids = { selected.get('user'): selected for selected in pre_selected_ids }
        self.pre_selected_user_ids = set(self.map_id_to_selected_ids.keys())
        self.original_pre_selected_ids = copy.deepcopy(pre_selected_ids) 
        self.all_users = all_users or self.get_all_users_from_info()
        self.api_url = api_url or API_URLS.APP권한_사용자_M2M_Bulk
        self.is_initialized = False

        self.pre_selected_user_count = len(self.pre_selected_user_ids)
        
        self.on_complete_channelName = on_complete_channelName
        self.response_data = None

        if 'index' in kwargs:
            self.index = kwargs['index']
        
             
        self.setup_ui()
        self.update_title_label()
        self.set_enable_ok_button()

    def get_all_users_from_info(self):
        return copy.deepcopy(INFO.ALL_USER)

       
    def setup_ui(self):
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        
        # 타이틀 레이블 추가
        self.title_label = QLabel(self)
        layout.addWidget(self.title_label)
        
        # 검색 필드 추가
        search_layout = QHBoxLayout()
        search_label = QLabel("검색:", self)
        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText("이름 또는 부서명으로 검색")
        self.search_field.textChanged.connect(self.filter_search_field)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_field)
        layout.addLayout(search_layout)
        
        # 트리 위젯 추가 - 사용자 ID 목록 전달
        self.tree_widget = UsersTreeWidget(self, self.pre_selected_ids, self.all_users)
        self.tree_widget.selected_changed.connect(self.slot_selected_changed_from_tree)
        layout.addWidget(self.tree_widget)

        self.table_widget = UsersTableWidget(self, self.pre_selected_ids, self.all_users)
        self.table_widget.selected_changed.connect(self.slot_selected_changed_from_table)
        layout.addWidget(self.table_widget)

        self.table_widget.sort(3, Qt.SortOrder.AscendingOrder)
        self.table_widget.row_deleted_signal.connect( lambda dataObj: self.remove_select_user(dataObj))
        
       
        # 확인 및 닫기 버튼 추가
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton('확인', self)
        self.ok_button.clicked.connect(self.on_ok_button_clicked)
        self.cancel_button = QPushButton('취소', self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def set_enable_ok_button(self, enable:Optional[bool]=None):
        if enable is None:
            enable = self.is_users_changed()
        self.ok_button.setEnabled(enable)
        
    def slot_selected_changed_from_tree(self, userObj:dict):
        """ userObj : {'is_선택':bool, 'user_id':int} 형태"""
        self.table_widget.sync_with_tree(userObj)
        self.update_title_label()
        self.set_enable_ok_button()
        print(f"slot_selected_changed_from_tree: {userObj}")

    def slot_selected_changed_from_table(self, userObj:dict):
        """ {'id': -1, 'user': 55, '조직(3차)': '경영지원실', '조직(2차)': '경영지원실', '조직(1차)': '경영지원실', '성명': '조규섭', 'is_선택': True}"""
        self.tree_widget.simulate_click_user_by_id(userObj.get('user'))
        self.update_title_label()
        self.set_enable_ok_button()
        print(f"slot_selected_changed_from_table: {userObj}")

    def update_title_label(self):
        """타이틀 레이블 업데이트"""
        current_selected_count = len(self.get_checked_user_ids())        
        self.title_label.setText(f"이전 선택된 사람: {self.pre_selected_user_count}명, 현재 선택된 사람: {current_selected_count}명")
    
    def filter_search_field(self, text):
        self.filter_tree_widget(text)
        self.filter_table_widget(text)

    def filter_tree_widget(self, text):
        """검색어에 따라 트리 필터링"""
        if not text:
            # 검색어가 없으면 모든 항목 표시하고 최상위 항목은 접기
            for i in range(self.tree_widget.topLevelItemCount()):
                top_item = self.tree_widget.topLevelItem(i)
                self.show_all_items(top_item)
                top_item.setExpanded(False)  # 최상위 항목 접기
            return
        
        # 검색어가 있으면 필터링
        text = text.lower()
        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)
            # 최상위 항목(조직3)은 항상 표시
            top_item.setHidden(False)
            
            # 조직3 이름 확인
            dept3_visible = text in top_item.text(1).lower()
            
            # 하위 항목 확인
            has_visible_child = self.filter_item(top_item, text)
            
            # 검색 결과가 있으면 해당 항목 확장, 없으면 접기
            top_item.setExpanded(dept3_visible or has_visible_child)
        
    def filter_table_widget(self, text):
        # table widget 필터링 : direct 로 view 에서 호출
        self.table_widget.view.mixin_filter_rows(text)

    
    def filter_item(self, item, text):
        """재귀적으로 항목 필터링"""
        has_visible_child = False
        
        # 하위 항목 확인
        for i in range(item.childCount()):
            child = item.child(i)
            
            # 리프 노드(사용자)인 경우
            if child.childCount() == 0:
                # 이름에 검색어가 포함되는지 확인
                name_visible = text in child.text(1).lower()
                # 부서명에 검색어가 포함되는지 확인
                dept_visible = text in child.text(4).lower()
                
                # 이름이나 부서명에 검색어가 포함되면 표시, 아니면 숨김
                child.setHidden(not (name_visible or dept_visible))
                
                if name_visible or dept_visible:
                    has_visible_child = True
            else:
                # 중간 노드(부서)인 경우
                # 부서명에 검색어가 포함되는지 확인
                dept_visible = text in child.text(1).lower()
                
                # 하위 항목 확인 (재귀 호출)
                child_visible = self.filter_item(child, text)
                
                # 부서명에 검색어가 포함되거나 하위 항목 중 표시할 항목이 있으면 표시, 아니면 숨김
                child.setHidden(not (dept_visible or child_visible))
                
                if dept_visible or child_visible:
                    has_visible_child = True
                    child.setExpanded(True)  # 검색 결과가 있는 항목만 확장
                else:
                    child.setExpanded(False)  # 검색 결과가 없는 항목은 접기
        
        return has_visible_child
    
    def show_all_items(self, item):
        """모든 항목을 표시 상태로 설정 (재귀적)"""
        if item is None:
            return
            
        item.setHidden(False)
        
        # 모든 하위 항목도 표시 (재귀 호출)
        for i in range(item.childCount()):
            self.show_all_items(item.child(i))
    
    def get_checked_user_ids(self) -> list[int]:
        """선택된 사용자 목록 반환"""
        return self.table_widget.get_checked_user_ids()
    
    
    def is_users_changed(self, selected_ids=None) -> bool:
        """선택된 사용자 ID 목록이 초기 선택과 다른지 확인"""
        if selected_ids is None:
            selected_ids = set(self.get_checked_user_ids())        
        return self.pre_selected_user_ids != selected_ids

    
    def on_ok_button_clicked(self):
        """확인 버튼 클릭 시 선택된 사용자 ID 목록을 저장하고 다이얼로그 종료"""
        selected_users = self.get_checked_user_ids()
        
        added_users = [user_id for user_id in selected_users if user_id not in self.pre_selected_user_ids]
        deleted_ids = [user_id  for user_id in self.pre_selected_user_ids 
                       if user_id not in selected_users]            
        _text = f"""
        <b>기존 사용자</b>: {self.pre_selected_user_count}명 → <b>변경 사용자</b>: {len(selected_users)}명<br><br>
        <u>상세내역</u><br>
        <span style="color:green;">➕ 추가 사용자</span>: {len(added_users)}명<br>
        <span style="color:red;">➖ 삭제 사용자</span>: {len(deleted_ids)}명<br><br>
        <b>저장하시겠습니까?</b><br><br>
        <small><i>참조: 저장 후 사용자에게 즉시 적용은 <b>"모든 사용자에게 전송"</b> 버튼을 눌러야 합니다.</i></small>
        """
        if not Utils.QMsg_question (self, title="사용자 변경 정보", text=_text):
            return
        # 버튼 비활성화
        self.ok_button.setEnabled(False)
        self.ok_button.setText('저장 중...')
        
        # API 호출 처리
        import json
        final_result = {
            'added': json.dumps(added_users, ensure_ascii=False),  # 사용자 ID만 포함
            'removed': json.dumps(deleted_ids, ensure_ascii=False)  # ID 값만 포함
        }
        if self.save_to_api(final_result):
            self.accept()
        else:
            # 실패 시 버튼 다시 활성화
            self.ok_button.setEnabled(True)
            self.ok_button.setText('확인')

    def get_response_data(self):
        return self.response_data

    def save_to_api(self, data) -> bool:
        """API 저장 처리"""
        try:            
            # API 호출 (네트워크 요청)
            from config import Config as APP
            data['app_id'] = self.app_ID
            is_ok, _json = APP.API.post(self.api_url, data=data)            
            if is_ok:
                if self.on_complete_channelName:
                    self.event_bus.publish(self.on_complete_channelName,
                                       { 'index':self.index,
                                        'value' : data })
                self.response_data = _json
            else:
                QMessageBox.warning(self, "오류", f"저장 실패: {_json}")
            return is_ok
        except Exception as e:
            QMessageBox.critical(self, "오류", f"예외 발생: {str(e)}")
            logger.exception("사용자 저장 중 오류 발생")
            return False

# 메인 실행 코드
if __name__ == "__main__":
    import sys
    from datas import ALL_USERS
    app = QApplication(sys.argv)

#     # 테스트용 미리 선택된 ID 목록 (딕셔너리 리스트 형태)
# class UsersTreeWidget(QTreeWidget):
#     """사용자 목록을 트리 형태로 표시하는 위젯"""
    
#     def __init__(self, parent=None, pre_selected_ids=None, all_users=None):
#         super().__init__(parent)
#         self.setHeaderLabels(['', '이름', '직책', '직급', '부서'])
#         self.all_users = all_users or self.get_all_users(all_users)
#         # pre_selected_ids를 딕셔너리 리스트로 처리
#         self.pre_selected_ids = pre_selected_ids or []
#         # 사용자 ID 목록 추출 (호환성 유지)
#         # pre_selected_user_ids 초기화 부분 수정
#         if self.pre_selected_ids:
#             if isinstance(self.pre_selected_ids[0], dict):
#                 self.pre_selected_user_ids = [item.get('user') for item in self.pre_selected_ids]
#             else:
#                 self.pre_selected_user_ids = self.pre_selected_ids
#         else:
#             self.pre_selected_user_ids = []
        
#         # 체크박스 표시 설정
#         self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        
#         # 이벤트 처리 중인지 추적하는 플래그
#         self.is_processing_event = False
        
#         # 항목 클릭 시 처리할 이벤트 연결
#         self.itemClicked.connect(self.handle_item_clicked)
        
#         self.populate_tree()
        
#         # 트리 채운 후 열 너비 설정
#         self.setColumnWidth(0, 100)   # 체크박스 열
#         self.setColumnWidth(1, 100)  # 이름
#         self.setColumnWidth(2, 80)   # 직책
#         self.setColumnWidth(3, 80)   # 직급
#         self.setColumnWidth(4, 150)  # 부서
        
#         # 초기화 후 모든 항목의 스타일 강제 업데이트
#         self.update_all_items_style()
        
#     def get_all_users(self, all_users=None):
#         if not all_users:
#             self.all_users = INFO.ALL_USER
#         return self.all_users
    
#     def update_pre_selected_user_ids(self, pre_selected_user_ids:list[int]):
#         self.pre_selected_user_ids = pre_selected_user_ids
#         self.clear()
#         self.populate_tree()

#     def populate_tree(self):
#         """사용자 데이터로 트리 위젯 채우기"""
#         # 부서별로 사용자 그룹화
#         departments = self._group_users_by_department()
        
#         # 선택된 항목을 저장할 리스트
#         self.pre_selected_items = []
        
#         # 트리 구성 (재귀적으로)
#         for dept3, sub_depts in departments.items():
#             dept3_item = self._create_department_item(self, dept3)
#             self._populate_department(dept3_item, sub_depts)
        
#     def _group_users_by_department(self):
#         """사용자를 부서별로 그룹화"""
#         departments = {}
        
#         for user in self.get_all_users():
#             # admin 사용자 제외 (ID=1 제외 로직 제거)
#             if user['user_성명'] == 'admin' or user['user_직책'] == 'admin':
#                 continue
                
#             dept3 = user['기본조직3']
#             dept2 = user['기본조직2']
#             dept1 = user['기본조직1']
            
#             # 조직3 = 조직2 = 조직1 인 경우 (모두 같은 경우)
#             if dept3 == dept2 and dept2 == dept1:
#                 if dept3 not in departments:
#                     departments[dept3] = {"users": []}
#                 elif "users" not in departments[dept3]:
#                     departments[dept3]["users"] = []
#                 departments[dept3]["users"].append(user)
#                 continue
                
#             # 조직2 = 조직1 인 경우
#             if dept2 == dept1:
#                 if dept3 not in departments:
#                     departments[dept3] = {}
#                 if dept2 not in departments[dept3]:
#                     departments[dept3][dept2] = {"users": []}
#                 elif "users" not in departments[dept3][dept2]:
#                     departments[dept3][dept2]["users"] = []
#                 departments[dept3][dept2]["users"].append(user)
#                 continue
                
#             # 일반적인 경우 (모두 다른 경우)
#             if dept3 not in departments:
#                 departments[dept3] = {}
#             if dept2 not in departments[dept3]:
#                 departments[dept3][dept2] = {}
#             if dept1 not in departments[dept3][dept2]:
#                 departments[dept3][dept2][dept1] = []
#             departments[dept3][dept2][dept1].append(user)
        
#         return departments

#     def _create_department_item(self, parent, dept_name):
#         """부서 항목 생성"""
#         dept_item = QTreeWidgetItem(parent)
#         dept_item.setText(1, dept_name)
#         # 체크박스 추가
#         dept_item.setFlags(dept_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
#         dept_item.setCheckState(0, Qt.CheckState.Unchecked)
#         # 시작 시 확장하지 않음
#         dept_item.setExpanded(False)
#         return dept_item

#     def _create_user_item(self, parent, user, dept_name=None):
#         """사용자 항목 생성"""
#         user_item = QTreeWidgetItem(parent)
#         user_item.setText(1, user['user_성명'])
#         user_item.setText(2, user['user_직책'])
#         user_item.setText(3, user['user_직급'])
#         # 부서명 설정 (지정된 경우 사용, 아니면 기본조직3 사용)
#         user_item.setText(4, dept_name if dept_name else user['기본조직3'])
        
#         # 체크박스 추가
#         user_item.setFlags(user_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
#         user_item.setCheckState(0, Qt.CheckState.Unchecked)
        
#         # 사용자 데이터 저장
#         user_item.setData(0, Qt.ItemDataRole.UserRole, user)
        
#         # 미리 선택된 ID 목록에 있으면 저장
#         if int(user.get('id', 0)) in self.pre_selected_user_ids:
#             self.pre_selected_items.append(user_item)
        
#         return user_item

#     def _populate_department(self, parent_item, dept_data):
#         """재귀적으로 부서 및 사용자 항목 추가"""
#         # 직속 사용자 추가self.on_complete_callback = on_complete_callback
#         if "users" in dept_data:
#             for user in dept_data["users"]:
#                 self._create_user_item(parent_item, user)
            
#             # users 키 처리 후 제거하여 나머지 하위 부서만 처리
#             dept_data_copy = dept_data.copy()
#             dept_data_copy.pop("users")
#             dept_data = dept_data_copy
        
#         # 하위 부서 처리
#         for sub_dept_name, sub_dept_data in dept_data.items():
#             # 실제 하위 부서인 경우만 추가
#             if isinstance(sub_dept_data, dict):
#                 sub_dept_item = self._create_department_item(parent_item, sub_dept_name)
#                 self._populate_department(sub_dept_item, sub_dept_data)
#             # 사용자 목록인 경우 (최하위 부서)
#             elif isinstance(sub_dept_data, list) and sub_dept_data:
#                 sub_dept_item = self._create_department_item(parent_item, sub_dept_name)
#                 for user in sub_dept_data:
#                     self._create_user_item(sub_dept_item, user, user['기본조직1'])
    
#     def handle_item_clicked(self, item, column):
#         """항목 클릭 시 처리 (선택 상태 변경)"""
#         # 이미 이벤트 처리 중이면 무시
#         if self.is_processing_event:
#             return
            
#         # 이벤트 처리 시작
#         self.is_processing_event = True
        
#         # 현재 체크 상태 가져오기
#         current_state = item.checkState(0)
#         # 체크 상태 토글
#         new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
#         # 새 체크 상태 설정
#         item.setCheckState(0, new_state)
        
#         # 하위 항목들의 체크 상태 변경
#         self.update_children_check_state(item, new_state == Qt.CheckState.Checked)
        
#         # 상위 항목들의 체크 상태 업데이트
#         self.update_parent_check_state(item.parent())
        
#         # 스타일 업데이트
#         self.update_item_style(item)
#         self.update_item_styles_recursive(item)  # 모든 하위 항목의 스타일도 업데이트
        
#         # 이벤트 처리 종료
#         self.is_processing_event = False
        
#         # 타이틀 레이블 업데이트 (부모 다이얼로그가 있는 경우)
#         if self.parent() and hasattr(self.parent(), 'update_title_label'):
#             self.parent().update_title_label()

#         if not self.parent().is_initialized:
#             return
    
 

    
#     def update_children_check_state(self, item, is_checked):
#         """하위 항목들의 체크 상태 변경"""
#         if item is None:
#             return
            
#         # 체크 상태 설정
#         check_state = Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
        
#         # 모든 하위 항목에 대해 체크 상태 변경
#         for i in range(item.childCount()):
#             child = item.child(i)
#             child.setCheckState(0, check_state)
#             # 스타일 업데이트
#             self.update_item_style(child)
#             # 재귀적으로 하위 항목 처리
#             self.update_children_check_state(child, is_checked)
    
#     def update_item_style(self, item):
#         """항목의 스타일 업데이트"""
#         if item is None:
#             return
            
#         # 체크 상태에 따라 스타일 설정
#         is_checked = item.checkState(0) == Qt.CheckState.Checked
        
#         # 모든 항목에 스타일 적용 (리프 노드 여부와 상관없이)
#         if is_checked:
#             # 체크된 항목: 노란색 배경, 굵은 글꼴
#             for col in range(5):  # 모든 열에 스타일 적용 (체크박스 열 포함)
#                 item.setBackground(col, QBrush(QColor(255, 255, 200)))  # 연한 노란색 배경
#                 font = QFont()
#                 font.setBold(True)
#                 item.setFont(col, font)  # 굵은 글꼴 적용
#         else:
#             # 체크 해제된 항목: 기본 스타일로 복원
#             for col in range(5):  # 모든 열에 스타일 적용 (체크박스 열 포함)
#                 item.setBackground(col, QBrush())  # 기본 배경색
#                 font = QFont()
#                 font.setBold(False)
#                 item.setFont(col, font)  # 기본 글꼴
    
#     def update_parent_check_state(self, parent):
#         """상위 항목의 체크 상태 업데이트"""
#         if parent is None:
#             return
            
#         # 하위 항목들의 체크 상태 확인
#         child_count = parent.childCount()
#         checked_count = 0
        
#         for i in range(child_count):
#             if parent.child(i).checkState(0) == Qt.CheckState.Checked:
#                 checked_count += 1
        
#         # 상위 항목의 체크 상태 설정
#         if checked_count == 0:
#             parent.setCheckState(0, Qt.CheckState.Unchecked)
#         elif checked_count == child_count:
#             parent.setCheckState(0, Qt.CheckState.Checked)
#         else:
#             parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        
#         # 상위 항목의 부모에 대해서도 체크 상태 업데이트
#         self.update_parent_check_state(parent.parent())
    
#     def get_checked_users(self):
#         """체크된 사용자 목록 반환"""
#         checked_users = []
        
#         # 모든 최상위 항목에 대해 체크된 사용자 찾기
#         for i in range(self.topLevelItemCount()):
#             self._collect_checked_users(self.topLevelItem(i), checked_users)
            
#         return checked_users
    
#     def get_checked_user_ids(self):
#         """체크된 사용자의 ID 목록 반환"""
#         checked_users = self.get_checked_users()
#         # ID=1 제외 로직 제거
#         return [int(user.get('id', 0)) for user in checked_users]
    
#     def _collect_checked_users(self, item, checked_users):
#         """재귀적으로 체크된 사용자 수집"""
#         # 리프 노드(사용자)인 경우 체크 상태 확인
#         if item.childCount() == 0 and item.checkState(0) == Qt.CheckState.Checked:
#             user_data = item.data(0, Qt.ItemDataRole.UserRole)
#             if user_data:
#                 checked_users.append(user_data)
        
#         # 하위 항목에 대해 재귀 호출
#         for i in range(item.childCount()):
#             self._collect_checked_users(item.child(i), checked_users)
    
#     def update_item_styles_recursive(self, item):
#         """모든 항목의 스타일을 재귀적으로 업데이트"""
#         if item is None:
#             return
            
#         # 현재 항목의 스타일 업데이트
#         self.update_item_style(item)
        
#         # 모든 하위 항목에 대해 재귀 호출
#         for i in range(item.childCount()):
#             self.update_item_styles_recursive(item.child(i))

#     def update_all_items_style(self):
#         """모든 항목의 스타일을 강제로 업데이트"""
#         for i in range(self.topLevelItemCount()):
#             top_item = self.topLevelItem(i)
#             self.update_item_styles_recursive(top_item)
            
#             # 부모 항목의 체크 상태도 업데이트
#             self.update_parent_check_state(top_item)
            
#         # 모든 항목 업데이트 후 화면 갱신
#         self.update()
#     pre_selected_ids = [
#         {'id': 101, 'user': 32}, 
#         {'id': 102, 'user': 31}, 
#         {'id': 103, 'user': 30}, 
#         {'id': 104, 'user': 38}, 
#         {'id': 105, 'user': 37}, 
#         {'id': 106, 'user': 52}, 
#         {'id': 107, 'user': 34}, 
#         {'id': 108, 'user': 106}
#     ]

#     dialog = UsersDialog(pre_selected_ids=pre_selected_ids, all_users=ALL_USERS)
#     dialog.show()

#     sys.exit(app.exec())  # sys.exit() 없이 실행