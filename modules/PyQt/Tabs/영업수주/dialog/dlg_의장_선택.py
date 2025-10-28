from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from info import Info_SW as INFO
from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dlg_의장_선택(QDialog):
    """
    의장 선택 다이얼로그
    kwargs:
        _list: 의장 목록 , 없으면 API 호출
        pos: 위치
    """

    def __init__(self, parent=None, _list=None, pos=None, url=None):
        super().__init__(parent)
        self._list = _list or []
        self.url = url or INFO.URL_영업수주_자재내역_To_의장_Mapping_DB
        self.setWindowTitle("의장 선택")
        self.selected_value = ""
        
        if not self._list and url:
            params = '?page_size=0'
            _isOk, _json = APP.API.getlist( self.url+ params)
            if _isOk:
                self._list = [ _dict.get('의장') for _dict in _json ]
        if pos:
            self.move(pos)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 주의문구 추가
        주의문구 = QLabel("※ 의장 삭제 시 기존 DATA에 모두 삭제되므로 관리자에게 문의 바람")
        주의문구.setStyleSheet("background-color:black;color: yellow;font-weight:bold;")
        layout.addWidget(주의문구)

        # 의장선택위젯 추가
        self._위젯 = 의장선택위젯(self, self._list)
        layout.addWidget(self._위젯)
        
        # 확인/취소 버튼
        btn_layout = QHBoxLayout()
        self.확인버튼 = QPushButton("확인")
        취소버튼 = QPushButton("취소")
        
        # 초기에 확인 버튼 비활성화
        self.확인버튼.setEnabled(False)
        
        self.확인버튼.clicked.connect(self.accept)
        취소버튼.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.확인버튼)
        btn_layout.addWidget(취소버튼)
        layout.addLayout(btn_layout)
        
        # _위젯의 선택 상태 변경 시 확인 버튼 활성화 상태 업데이트
        self._위젯.selection_changed.connect(self.update_confirm_button)
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

    def update_confirm_button(self, has_selection):
        self.확인버튼.setEnabled(has_selection)

    def get_value(self):
        return self._위젯.get_value()

class 의장선택위젯(QWidget):
    selection_changed = pyqtSignal(bool)  # 선택 상태 변경 시그널 추가
    
    def __init__(self, parent=None, _list=None):
        super().__init__(parent)
        self._list = _list or []
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self._list)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("의장 입력 (예: 1.6T*1000*2750)")
		# # Validator 추가
        # self.validator = 생산지시서_의장_Validator(wid=self.line_edit)
        # self.line_edit.setValidator(self.validator)
        
        self.select_btn = QPushButton("선택")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.on_select)
        
        layout.addWidget(self.list_widget)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.select_btn)
        
        self.list_widget.itemClicked.connect(self.on_list_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_list_item_double_clicked)  # 더블클릭 이벤트 추가
        self.line_edit.textChanged.connect(self.on_text_changed)

        self.line_edit.hide()
        self.select_btn.hide()

    # 더블클릭 핸들러 함수 추가
    def on_list_item_double_clicked(self, item):
        self.on_list_item_clicked(item)  # 일반 클릭 처리를 먼저 수행
        self.on_select()  # 선택 버튼 클릭과 동일한 동작 수행

    def on_list_item_clicked(self, item):
        selected_text = item.text()
        # 선택된 텍스트가 validator 형식과 일치하는지 확인
        if hasattr(self, 'validator'):
            state, _, _ = self.validator.validate(selected_text, 0)
            if state == QValidator.State.Acceptable:
                self.line_edit.setText(selected_text)
            else:
                # validator 형식과 일치하지 않으면 line_edit은 비우고 선택만 표시
                self.line_edit.clear()
                self.list_widget.setCurrentItem(item)
        else:
            self.line_edit.setText(selected_text)
        
        self.select_btn.setEnabled(True)
        self.selection_changed.emit(True)

    def on_text_changed(self, text):
        if hasattr(self, 'validator'):
            # validator 상태에 따라 버튼 활성화
            state, _, _ = self.validator.validate(text, 0)
            is_valid = state == QValidator.State.Acceptable
        else:
            is_valid = True
        self.select_btn.setEnabled(is_valid)
        self.selection_changed.emit(is_valid)

    def on_select(self):
        if self.line_edit.text().strip():
            self.line_edit.setText(self.line_edit.text().strip())
            if isinstance(self.parent(), Dlg_의장_선택):
                self.parent().accept()

    def get_value(self):
        return self.line_edit.text().strip()

