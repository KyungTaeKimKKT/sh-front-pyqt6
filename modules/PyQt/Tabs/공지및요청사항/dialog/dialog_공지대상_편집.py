from __future__ import annotations
from modules.common_import_v2 import *


class Dialog_공지대상_편집(QDialog):
    def __init__(self, parent, all_data: list[dict], obj: dict, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.all_data = all_data
        self.all_data_map = { obj.get('id'): obj for obj in self.all_data }
        self.obj = obj
        self.selected_ids = self._parse_selected_ids_from_obj()     ### app 권한 아이디 리스트 
        
        self.UI()

        # self.checkbox_all.setTristate(False)  # ✅ 반드시 추가 : 왜냐면 트리 항목(QTreeWidgetItem)에 ItemIsAutoTristate 플래그를 사용하고 있음.
        self.checkbox_all.stateChanged.connect(self.on_checkbox_all_changed)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        self.update_HeaderLabel()

    def _parse_selected_ids_from_obj(self):
        try:
            popup_대상:str = self.obj.get('popup_대상', '')
            if not popup_대상:
                return []
            if popup_대상.lower() == 'all':
                return [ obj.get('id') for obj in self.all_data ]

            split_ids = popup_대상.split(',')
            return [int(i.strip()) for i in split_ids if i.strip().isdigit()]
        except Exception as e:
            logger.error(f"get_selected_ids: {e}")
            return []


    def UI(self):
        제목 = self.obj.get('제목', '')
        default_title = f"{제목} : 공지 대상 앱 선택" if 제목 else "공지 대상 앱 선택"
        self.setWindowTitle(self.kwargs.get('title', default_title))
        self.resize(self.kwargs.get('width', 400), self.kwargs.get('height', 500))
        self.v_layout = QVBoxLayout()
        ### 1. 전체 선택 체크박스
        self.checkbox_all = QCheckBox("전체 선택")
        self.checkbox_all.setTristate(True) 
        self.checkbox_all.setChecked(self.obj.get('popup_대상', '') == 'all' )      ## all 이면 체크
        self.v_layout.addWidget(self.checkbox_all)

        self.v_layout.addSpacing(16)

        ### 2. 트리
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("공지할 앱 : 선택된 앱 수 : {}".format(len(self.selected_ids)))

        self._build_tree(self.all_data, self.selected_ids)
        self.v_layout.addWidget(self.tree)

        ### 3. 버튼
        btn_ok = QPushButton("확인")
        btn_cancel = QPushButton("취소")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        self.v_layout.addLayout(btn_layout)

        self.setLayout(self.v_layout)


    def on_checkbox_all_changed(self, state):
        if state == Qt.CheckState.Checked.value:
            self.set_all_items_check_state(Qt.CheckState.Checked)
        elif state == Qt.CheckState.Unchecked.value:
            self.set_all_items_check_state(Qt.CheckState.Unchecked)
        else:
            # PartiallyChecked는 무시
            pass

        self.update_HeaderLabel()

    def set_all_items_check_state(self, state: Qt.CheckState):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                child.setCheckState(0, state)
        self.tree.blockSignals(False)


    def on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        checked_status, checked_ids = self.get_selected_ids()
        # 전체 선택 상태 체크박스 갱신은 시그널 끊고 설정
        self.checkbox_all.blockSignals(True)
        match checked_status:
            case 'all':
                self.checkbox_all.setCheckState(Qt.CheckState.Checked)
            case 'none':
                self.checkbox_all.setCheckState(Qt.CheckState.Unchecked)
            case 'partial':
                self.checkbox_all.setCheckState(Qt.CheckState.PartiallyChecked)
        self.checkbox_all.blockSignals(False)

        self.update_HeaderLabel()

    def update_HeaderLabel(self):
        checked_status, checked_ids  = self.get_selected_ids()
        target_users = self.get_target_users(checked_ids)

        _txt = f"공지할 앱 : 선택된 앱 수 : {len(self.get_selected_ids())}   공지할 사용자 수: {len(target_users)}"
        self.tree.setHeaderLabel(_txt)

    def get_target_users(self, ids: list[int]) -> list[int]:
        target_users = []
        for id in ids:
            user_list = self.all_data_map.get(id, {}).get('user_pks', [])
            target_users.extend(user_list)
        return list(set(target_users))

    def _build_tree(self, all_data: list[dict], selected_ids: list[int]):
        grouped = defaultdict(list)
        for row in all_data:
            grouped[row['표시명_구분']].append(row)

        for group, items in grouped.items():
            parent = QTreeWidgetItem([group])
            # ✅ PyQt6에서 Tree 항목에 checkable & auto-tristate 설정
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)


            for item in items:
                child = QTreeWidgetItem([item['표시명_항목']])
                child.setData(0, Qt.ItemDataRole.UserRole, item['id'])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Checked if item['id'] in selected_ids else Qt.CheckState.Unchecked)
                parent.addChild(child)

            self.tree.addTopLevelItem(parent)

    def get_selected_ids(self) -> tuple[str, list[int]]:
        total = 0
        checked = 0
        checked_ids = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                total += 1
                if child.checkState(0) == Qt.CheckState.Checked:
                    checked += 1
                    checked_ids.append(child.data(0, Qt.ItemDataRole.UserRole))
        if total == checked:
            return 'all', checked_ids
        elif checked == 0:
            return 'none', checked_ids
        else:
            return 'partial', checked_ids




def main():
    import sys
    from PyQt6.QtWidgets import QApplication
    all_data = [
        {'id': 90, '표시명_구분': '작업지침서', '표시명_항목': '이력조회', '순서': 20003},
        {'id': 91, '표시명_구분': '작업지침서', '표시명_항목': '의장도', '순서': 20004},
        {'id': 68, '표시명_구분': '작업지침서', '표시명_항목': '관리', '순서': 20009},
        {'id': 92, '표시명_구분': '생산지시서', '표시명_항목': '관리', '순서': 21000},
        {'id': 96, '표시명_구분': '생산관리', '표시명_항목': '일정관리', '순서': 22000},
        {'id': 95, '표시명_구분': '생산관리', '표시명_항목': '확정Branch', '순서': 23010},
        {'id': 143, '표시명_구분': '망관리', '표시명_항목': '관리', '순서': 24000},
        {'id': 154, '표시명_구분': '망관리', '표시명_항목': '등록', '순서': 24001},
    ]
    selected_ids = [90, 92, 154]

    app = QApplication(sys.argv)
    dialog = Dialog_공지대상_편집(None, all_data, selected_ids)
    result = dialog.exec()
    if result:
        ids = dialog.get_selected_ids()
        print ( ids )
        print ( ','.join(map(str, ids)) )
    sys.exit(0)

if __name__ == "__main__":
    main()