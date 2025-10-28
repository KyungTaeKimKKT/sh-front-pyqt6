from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_Confirm(QDialog):
    """
        kwargs: \n
        title :text,\n
        QBtn : (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel),\n
        msgText : text,\n
        msgStyleSheet : text,\n

    """
    def __init__(self, parent , **kwargs ):
        super().__init__(parent)

        for (key, value) in kwargs.items():

            setattr(self, key, value)

        self.title : str = self.title if hasattr(self, 'title') else "확인"
        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.QBtn = self.QBtn if hasattr(self, 'QBtn') else QBtn
        msgText : str = "확인하였습니까?"
        self.msgText = self.msgText if hasattr(self, 'msgText') else msgText

        msgStyleSheet = "background-color:black;color:yellow;font-weight:bold;"
        self.msgStyleSheet = self.msgStyleSheet if hasattr(self, 'msgStyleSheet') else msgStyleSheet

        self.setWindowTitle(self.title)
        self.buttonBox = QDialogButtonBox(self.QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setFixedSize( 300, 400)

        layout = QVBoxLayout()
        message = QLabel(self.msgText)
        message.setStyleSheet( self.msgStyleSheet )
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)