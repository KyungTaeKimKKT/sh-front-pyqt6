import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class My_DateTimeEdit(QDateTimeEdit):
    def __init__(self, parent:QWidget|None):
        super().__init__(parent)
        now = QDateTime.currentDateTime()
        self.setCalendarPopup(True)
        self.setMinimumDateTime(now)
        self.setDateTime(now)

