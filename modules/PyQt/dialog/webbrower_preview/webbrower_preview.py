from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_Webbrower_Preview(QDialog):
    """ by kwargs 에 따라서 setting \n
        title = str,\n
        minimumSize = (int, int)\n
    """
    def __init__(self, parent, url:str, **kwargs):
        super().__init__(parent)
        self.url = url
        self.qurl = QUrl( url )

        self.kwargs = kwargs
        # for k, v in kwargs.items():
        #     setattr(self, k, v)
        
        self.UI()
        self.user_defined_UI()

        self.show()


    def UI(self):
        hLayout = QVBoxLayout()
        self.browser = QWebEngineView()						
        self.browser.setUrl ( self._get_QUrl() )
        hLayout.addWidget ( self.browser )
        self.setLayout(hLayout)

    def user_defined_UI(self):
        """ by kwargs 에 따라서 setting \n
            title = str,
            minimumSize = (int, int)
        """
        self.setWindowTitle ( self.kwargs.get('title', 'Web Preview') )
        self.setMinimumSize ( QSize ( *self.kwargs.get('minimumSize', (500, 600) ) ) )

    def _get_QUrl(self, url:str=''):
        return QUrl(url) if 'http' in url else self.qurl