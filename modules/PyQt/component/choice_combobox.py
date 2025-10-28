from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Choice_ComboBox(QtWidgets.QComboBox):
    signal = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        self.choices = {}        
        self.choice_value = ''
        self.setStyleSheet("""
                        QComboBox {
                            border: 1px solid gray;
                            border-radius: 3px;
                            padding: 1px 5px 1px 3px;
     
                        }
                        QComboBox:hover {
                            background: blue;
                            color: #fff;
                        }
                        """)

    def _render(self):        
        for (key, value) in self.choices.items():
            self.addItem(value)
        self.resize(self.sizeHint())
        

    