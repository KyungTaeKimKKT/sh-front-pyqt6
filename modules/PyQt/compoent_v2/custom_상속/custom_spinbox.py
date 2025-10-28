from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback

from local_db.models import Search_History

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Custom_DobleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)



    def event(self, event):
        match event.type():
            case QEvent.Type.FocusIn:
                self.setStyleSheet("background-color: #f4f5b8;font-weight: bold;")
            case QEvent.Type.FocusOut:
                self.setStyleSheet("background-color: #ffffff;")
            case QEvent.Type.KeyPress:
                self.setStyleSheet("background-color: #f4f5b8; font-weight: bold;")
        return super().event(event)

    ### 아래는 chaining builder 패턴

    def _set_value(self, value:float):
        self.setValue(value)
        return self

    def _set_minimum(self, value:float):
        self.setMinimum(value)
        return self
    
    def _set_maximum(self, value:float):
        self.setMaximum(value)
        return self
    
    def _set_step(self, value:float):
        self.setSingleStep(value)
        return self
    
    def _set_prefix(self, text:str):
        self.setPrefix(text)
        return self
    
    def _set_suffix(self, text:str):
        self.setSuffix(text)
        return self
    
    def _set_alignment(self, alignment:Qt.AlignmentFlag=Qt.AlignmentFlag.AlignCenter):
        self.setAlignment(alignment)
        return self
    
    def _set_range(self, min:float, max:float):
        self.setRange(min, max)
        return self
    
    def _set_toolTip(self, text:str):
        self.setToolTip(text)
        return self
   
    def _set_styleSheet(self, styleSheet:str):
        self.setStyleSheet(styleSheet)
        return self
    
    def _get_value(self) -> float:
        return self.value()
    
   