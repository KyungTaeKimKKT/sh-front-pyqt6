from modules.common_import_v2 import *

class Base_List_Select(QDialog):
    def __init__(self, parent:QWidget, data:list[dict]=[],  url:str=None, list_name_key:str=None, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self._data = data
        self.filtered_data = self._data.copy()
        self.url = url
        self.is_auto_fetch = self.kwargs.get('is_auto_fetch', True)
        self.list_name_key = list_name_key or 'table_name'
        self.title = self.kwargs.get('title', '선택')
        self.default_size = self.kwargs.get('size', (400, 600))

        self.is_init_ui = False

        self.init_ui()

        if self.kwargs.get('hovable', True):
            self.setMouseTracking(True)

        if self.is_auto_fetch:
            self.fetch_data()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(*self.default_size)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)

        self.main_layout = QVBoxLayout(self)

        # 1. refresh button

        self.pb_refresh = CustomPushButton(self, 'Refresh')
        self.pb_refresh.clicked.connect(self.fetch_data)
        self.main_layout.addWidget(self.pb_refresh)


		# 2. 검색창
        self.search_input = Custom_LineEdit(self)
        self.search_input.setPlaceholderText(f"{self.kwargs.get('search_placeholder', '테이블 이름 검색...')}")
        self.search_input.textChanged.connect(self.update_filter)
        self.main_layout.addWidget(self.search_input)

		# 3. 리스트 widget
        self.list_widget = QListWidget(self)
        self.populate_list()
        self.main_layout.addWidget(self.list_widget)

		# 4. 버튼
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("확인")
        self.btn_cancel = QPushButton("취소")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        self.main_layout.addLayout(btn_layout)

        self.is_init_ui = True

    def fetch_data(self):
        is_ok, _json = APP.API.getlist(url=self.url)
        print ( is_ok )
        print ( _json )
        if is_ok:
            self._data = _json
            self.filtered_data = self._data.copy()
            self.update_filter(self.search_input.text())  # 🔹 검색어 유지하면서 갱신
        else:
            Utils.generate_QMsg_critical(None, 
                                         title=f'{self.title} 실패', 
                                         text=f'{ self.title} 실패: <br>{_json}'
                                            )
    
    def update_filter(self, text: str):
        keyword = text.strip().lower()
        self.filtered_data = [
            item for item in self._data if keyword in item[self.list_name_key]
        ]
        self.populate_list()


    def populate_list(self):
        self.list_widget.clear()
        for dataObj in self.filtered_data:
            item = QListWidgetItem(dataObj.get(self.list_name_key, 'Unknown'))
            item.setData(Qt.ItemDataRole.UserRole, dataObj)
            self.list_widget.addItem(item)
    


    def accept_selection(self):
        item = self.list_widget.currentItem()
        if item is not None:
            self.selected_item = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "선택 오류", f"{self.list_name_key}을 선택하세요.")

    def get_selected_item(self) -> dict:
        return self.selected_item

    def get_selected_name(self) -> str:
        return self.selected_item.get(self.list_name_key, 'Unknown')
    
    def mouseMoveEvent(self, event):
        item = self.list_widget.itemAt(event.pos())
        if item is not None:
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                # 보기 좋게 출력 (json 스타일)
                tooltip_text = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                tooltip_text = str(data)

            QToolTip.showText(event.globalPos(), tooltip_text)
        else:
            QToolTip.hideText()  # 항목 없을 때 툴팁 숨김 처리

        super().mouseMoveEvent(event)