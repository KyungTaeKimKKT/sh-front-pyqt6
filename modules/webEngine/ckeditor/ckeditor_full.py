from PyQt6 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel, QtNetwork
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import os
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class CK_Editor(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        # channel = QtWebChannel.QWebChannel(self)
        # self.page().setWebChannel(channel)
        # channel.registerObject("qCK_Editor", self)
        # self.page().runJavaScript(JS)
        # file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "aa.html"))
        # file_path = '/home/kkt/development/python/PyQt6/sh_app/modules/webEngine/ckeditor/trials/index.html'
        # local_url = QUrl.fromLocalFile(file_path)
        # self.load(local_url)

        url = QUrl('http://127.0.0.1:5500/modules/webEngine/ckeditor/trials/index.html')
        self.load(url)

        self.loadFinished.connect(self.on_loadFinished)
        self.initialized = False



    @QtCore.pyqtSlot()
    def on_loadFinished(self):
        self.initialized = True







if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w =CK_Editor()

    w.resize(640, 480)
    w.show()

    sys.exit(app.exec())