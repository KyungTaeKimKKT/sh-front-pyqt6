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


from plugin_main.widgets.users_tablewidget import TableModel_Users, TableView_Users, Delegate_Users, UsersTableWidget
from plugin_main.widgets.dlg_user_select_with_tree_table import UsersDialog_with_tree_table

class TableModel_Users_Select(TableModel_Users):

    pass

    # @property
    # def map_id_to_selected_ids(self):
    #     return { selected.get('user_fk'): selected for selected in self.pre_selected_ids } if self.pre_selected_ids else {}
    

class TableView_Users_Select(TableView_Users):
    pass

class Delegate_Users_Select(Delegate_Users):
    pass

class UsersTableWidget_Select(UsersTableWidget):
    
    def create_table(self):
        self.view = TableView_Users_Select(self)
        self.model = TableModel_Users_Select(self, self.pre_selected_ids, self.all_users, view_type=self.view_type)
        self.model.selected_changed.connect(lambda userObj: self.selected_changed.emit(userObj) )
        self.delegate = Delegate_Users_Select(self)
        self.view.setModel(self.model) 
        self.view.setItemDelegate(self.delegate)


class Dlg_Users_Select_Only_Table(UsersDialog_with_tree_table):
    """ setup_ui 에서 tree 부분 제외함"""        

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
        
        self.table_widget = UsersTableWidget_Select(parent=self, all_users=self.all_users, pre_selected_ids=self.pre_selected_ids, view_type=self.view_type)
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

    # def slot_selected_changed_from_table(self, userObj:dict):
    #     """ override : tree"""
    #     self.update_title_label()
    #     self.set_enable_ok_button()
    # def get_all_users_from_info(self):
    #     return copy.deepcopy(INFO.ALL_USER)

    # def set_enable_ok_button(self, enable:Optional[bool]=None):
    #     if enable is None:
    #         enable = self.is_users_changed()
    #     self.ok_button.setEnabled(enable)
        
    # def slot_selected_changed_from_table(self, userObj:dict):
    #     """ {'id': -1, 'user': 55, '조직(3차)': '경영지원실', '조직(2차)': '경영지원실', '조직(1차)': '경영지원실', '성명': '조규섭', 'is_선택': True}"""
    #     self.set_enable_ok_button()

    # def update_title_label(self):
    #     """타이틀 레이블 업데이트"""        
    #     self.title_label.setText(f"사용자 선택 : 선택 check 또는 해당 row double click")
    
    # def filter_search_field(self, text):
    #     self.filter_table_widget(text)
       
    # def filter_table_widget(self, text):
    #     # table widget 필터링 : direct 로 view 에서 호출
    #     self.table_widget.view.mixin_filter_rows(text)
 
    
    # def get_checked_user_ids(self) -> list[int]:
    #     """선택된 사용자 목록 반환"""
    #     return self.table_widget.get_checked_user_ids()
    
    
    # def is_users_changed(self, selected_ids=None) -> bool:
    #     """선택된 사용자 ID 목록이 초기 선택과 다른지 확인"""
    #     return bool(self.table_widget.get_checked_user_ids())
    
   
    # def on_ok_button_clicked(self):
    #     """확인 버튼 클릭 시 선택된 사용자 ID 목록을 저장하고 다이얼로그 종료"""
    #     selected_users = self.get_checked_user_ids()
        
    #     added_users = [user_id for user_id in selected_users if user_id not in self.pre_selected_user_ids]
    #     deleted_ids = [user_id  for user_id in self.pre_selected_user_ids 
    #                    if user_id not in selected_users]            
    #     _text = f"""
    #     <b>기존 사용자</b>: {self.pre_selected_user_count}명 → <b>변경 사용자</b>: {len(selected_users)}명<br><br>
    #     <u>상세내역</u><br>
    #     <span style="color:green;">➕ 추가 사용자</span>: {len(added_users)}명<br>
    #     <span style="color:red;">➖ 삭제 사용자</span>: {len(deleted_ids)}명<br><br>
    #     <b>저장하시겠습니까?</b><br><br>
    #     <small><i>참조: 저장 후 사용자에게 즉시 적용은 <b>"모든 사용자에게 전송"</b> 버튼을 눌러야 합니다.</i></small>
    #     """
    #     if not Utils.QMsg_question (self, title="사용자 변경 정보", text=_text):
    #         return
    #     # 버튼 비활성화
    #     self.ok_button.setEnabled(False)
    #     self.ok_button.setText('저장 중...')
        
    #     # # API 호출 처리
    #     import json
    #     final_result = {
    #         'added': json.dumps(added_users, ensure_ascii=False),  # 사용자 ID만 포함
    #         'removed': json.dumps(deleted_ids, ensure_ascii=False)  # ID 값만 포함
    #     }
    #     if self.save_to_api(final_result):
    #         self.accept()
    #     else:
    #         # 실패 시 버튼 다시 활성화
    #         self.ok_button.setEnabled(True)
    #         self.ok_button.setText('확인')

  

class Dlg_User_선택_Only_Table_No_Api(UsersDialog_with_tree_table):

        def on_ok_button_clicked(self):
            self.accept()