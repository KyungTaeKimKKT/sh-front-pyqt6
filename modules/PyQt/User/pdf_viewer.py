# https://github.com/BBC-Esq/PyQt6-PDF-Viewer/blob/main/pyqt6_pdf_viewer.py
from PyQt6.QtCore import * #QUrl, Qt
from PyQt6.QtWidgets import * #QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QFileDialog, QPushButton
from PyQt6.QtGui import *  #QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class SearchLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return:
            self.parent.search_text(self.text())

class Pdf_Viewer(QDialog):
    """ targetUrl {'file': fileName, 'url': url }형태"""
    def __init__(self, parent, targetUrl:dict={}):
        super().__init__(parent)
        self.targetUrl = targetUrl

        self.UI()
        self.view_pdf_file()
    
    def UI(self) -> None:        
        self.setWindowTitle("PDF Viewer")
        self.setGeometry(0, 28, 1000, 750)

        layout = QVBoxLayout()

        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)
        
        layout.addWidget(self.webView)

        # self.search_input = SearchLineEdit(self)
        # self.search_input.setPlaceholderText("Enter text to search...")
        # layout.addWidget(self.search_input)

        self.setLayout( layout)

        self.show()

    def create_file_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Choose PDF')

        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        filename, _ = file_dialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        self.view_pdf_file( filename)
    
    def view_pdf_file(self, targetUrl:dict={}) -> None:
        targetUrl = targetUrl if targetUrl else self.targetUrl
        if not targetUrl : return

        for key , url in targetUrl.items():
            match key:
                case 'file':                    
                    self.webView.setUrl(QUrl("file:///" + url.replace('\\', '/')))
                case 'url':
                    self.webView.setUrl(QUrl( Utils.get_Full_URL( url )))
        # self.webView.setUrl(QUrl("file:///" + fileName.replace('\\', '/')))

    def search_text(self, text):
        flag = QWebEnginePage.FindFlag.FindCaseSensitively
        if text:
            self.webView.page().findText(text, flag)
        else:
            self.webView.page().stopFinding()
