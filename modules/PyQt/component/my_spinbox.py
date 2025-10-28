import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class My_SpinBox(QSpinBox):
    def __init__(self, parent:QWidget|None):
        super().__init__(parent)
        self.min = 0
        self.max = 100000
        self.stepValue = 1
        self.setRange(self.min, self.max)
        self.setValue( self.min )
        self.setSingleStep(self.stepValue)

class My_SpinBox_start1(My_SpinBox):
    def __init__(self, parent:QWidget|None):
        super().__init__(parent)
        self.min = 1
        self.setRange(self.min, self.max)
        self.setValue( self.min )

class EL수량_SpinBox(My_SpinBox_start1):
    def __init__(self, parent:QWidget|None):
        super().__init__(parent)
        self.setSuffix(' 대')