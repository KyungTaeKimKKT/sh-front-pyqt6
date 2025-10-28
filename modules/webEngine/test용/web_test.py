from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView

import os
import sys
import traceback
from modules.logging_config import get_plugin_logger


GOOGLE_MAP_API_KEY = 'AIzaSyD2MaeSd0PSAjuK1zcnkEdyryVYdL6oGFA'

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(f"https://maps.googleapis.com/maps/api/staticmap?center=Berkeley,CA&zoom=14&size=400x400&key=AIzaSyD2MaeSd0PSAjuK1zcnkEdyryVYdL6oGFA"))
        self.setCentralWidget(self.browser)


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()