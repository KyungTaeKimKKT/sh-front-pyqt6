from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class PB_기타조회조건 (QPushButton):
    # 시그널 추가
    search_conditions_cleared = pyqtSignal()

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.기타조회조건 = {}
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.update_button_style()

    def update_button_style(self):
        """Update the style of the button based on 기타조회조건."""
        if self.기타조회조건:
            self.setStyleSheet("background-color: yellow;")
        else:
            self.setStyleSheet("")

    def show_context_menu(self, position):
        """Show context menu for clearing 기타조회조건."""
        menu = QMenu()
        clear_action = QAction("Clear Search Conditions", self)
        clear_action.setEnabled(bool(self.기타조회조건))  # 기타조회조건이 없으면 비활성화
        clear_action.triggered.connect(self.clear_search_conditions)
        menu.addAction(clear_action)
        menu.exec_(self.mapToGlobal(position))

    def clear_search_conditions(self):
        """Clear 기타조회조건 and update button style."""
        self.기타조회조건 = {}
        self.update_button_style()
        # 시그널 emit
        self.search_conditions_cleared.emit()
    
    def update_kwargs(self, **kwargs):
        """Update the enabled state of the menu action based on 기타조회조건."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.update_button_style()