from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_Common:
    """ method Class
        methods \n
            common_setting()
    """

    def common_setting(self):
        default_Dict = {
            '_windowTitle' : 'Dialog',
            '_fixedSize' : QSize(400, 800),
        }
        self : QDialog
        self.setWindowTitle ( self._windowTitle if hasattr(self, '_windowTitle') else default_Dict.get('_windowTitle'))
        self.setFixedSize ( self._fixedSize if hasattr(self, '_fixedSize') else default_Dict.get('_fixedSize'))