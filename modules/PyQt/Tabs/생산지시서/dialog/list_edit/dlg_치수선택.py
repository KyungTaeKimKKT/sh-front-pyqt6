from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.User.validator import 생산지시서_치수_Validator
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 치수선택다이얼로그(QDialog):
    def __init__(self, parent=None, 치수_list=None, pos=None):
        super().__init__(parent)
        self.치수_list = 치수_list or []
        self.setWindowTitle("치수 선택")
        self.selected_value = ""
        
        if pos:
            self.move(pos)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 치수선택위젯 추가
        self.치수위젯 = 치수선택위젯(self, self.치수_list)
        layout.addWidget(self.치수위젯)
        
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
        
        # 치수위젯의 선택 상태 변경 시 확인 버튼 활성화 상태 업데이트
        self.치수위젯.selection_changed.connect(self.update_confirm_button)
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

    def update_confirm_button(self, has_selection):
        self.확인버튼.setEnabled(has_selection)

    def get_value(self):
        return self.치수위젯.get_value()

class 치수선택위젯(QWidget):
    selection_changed = pyqtSignal(bool)  # 선택 상태 변경 시그널 추가
    
    def __init__(self, parent=None, 치수_list=None):
        super().__init__(parent)
        self.치수_list = 치수_list or []
        self.selected_list_item = None  # 리스트에서 선택된 아이템 저장
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 왼쪽 레이아웃 추가 (리스트 위젯 + 검색창)
        left_layout = QVBoxLayout()
        
        # 검색창 추가
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("목록(대소문자 구분 않음) 검색...")
        self.search_edit.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.setSortingEnabled(True)  # 정렬 기능 활성화
        self.list_widget.addItems(self.치수_list)
        self.list_widget.sortItems()  # 초기 정렬
        left_layout.addWidget(self.list_widget)
        
        layout.addLayout(left_layout)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("치수 입력 (예: 1.6T*1000*2750)")
		# Validator 추가
        self.validator = 생산지시서_치수_Validator(wid=self.line_edit)
        self.line_edit.setValidator(self.validator)
        
        self.select_btn = QPushButton("선택")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.on_select)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.select_btn)
        
        self.list_widget.itemClicked.connect(self.on_list_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_list_item_double_clicked)  # 더블클릭 이벤트 핸들러 변경
        self.line_edit.textChanged.connect(self.on_text_changed)

    # 검색 필터 함수 추가
    def filter_list(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # 더블클릭 핸들러 함수 추가
    def on_list_item_double_clicked(self, item):
        self.selected_list_item = item  # 선택된 아이템 저장
        if isinstance(self.parent(), 치수선택다이얼로그):
            self.parent().accept()  # 다이얼로그 종료

    def on_list_item_clicked(self, item):
        self.selected_list_item = item
        selected_text = item.text()
        # validator 검증 - 유효한 경우에만 lineEdit에 설정
        state, _, _ = self.validator.validate(selected_text, 0)
        if state == QValidator.State.Acceptable:
            self.line_edit.setText(selected_text)
        
        # 리스트 아이템이 선택되면 확인 버튼 활성화
        self.selection_changed.emit(True)

    def on_text_changed(self, text):
        # validator 상태에 따라 버튼 활성화
        state, _, _ = self.validator.validate(text, 0)
        is_valid = state == QValidator.State.Acceptable
        self.select_btn.setEnabled(is_valid)

    def on_select(self):
        if self.line_edit.text().strip():
            self.line_edit.setText(self.line_edit.text().strip())
            if isinstance(self.parent(), 치수선택다이얼로그):
                self.parent().accept()

    def get_value(self):
        # 리스트에서 선택된 항목이 있으면 우선 반환
        if self.selected_list_item:
            return self.selected_list_item.text()
        # 없으면 lineEdit의 내용 반환
        return self.line_edit.text().strip()

