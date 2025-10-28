#!/usr/bin/env python3

import sys
from pathlib import Path

from PyQt6.QtCore import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

# REQUIREMENTS
#
# PyQt6
# =============
# pip3 install PyQt6
# pip3 install PyQtWebEngine
#
# PDF.js
# ============
# only the `web` and `build` folders are required from the the pdfjs project:
# git clone --depth 1 https://github.com/mozilla/pdf.js ~/js/pdfjs


# PDFJS = f'file://{Path.home()}/js/pdfjs/web/viewer.html'
PDFJS = f'file:/home/kkt/development/python/gui/Shinwoo_APP_ver0.09/modules/PyQt6/User/pdfjs/web/viewer.html'

class QWebView(QWebEngineView):
    def __init__(self, parent=None, url=None):
        QWebEngineView.__init__(self)
        self.current_url = ''
        if url:
            # self.load ( QUrl(url) )
            self.load(QUrl.fromUserInput(f'{PDFJS}?file={url}'))
        self.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self):



class PDFBrother(QMainWindow):
    def __init__(self, parent=None, args=None):
        super(PDFBrother, self).__init__(parent)
        self.create_menu()
        self.path = len(args) > 1 and args[1] or None
        self.add_web_widget()
        self.show()

    def create_menu(self):
        self.main_menu = self.menuBar()
        self.main_menu_actions = {}

        self.file_menu = self.main_menu.addMenu("File")
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogStart)
        self.actionOpen = QAction(icon,"Open", self)
        self.actionOpen.triggered.connect(self.onOpen)
        self.file_menu.addAction(self.actionOpen)


    def add_web_widget(self):
        # self.path = f"http://naver.com"
        self.web_widget = QWebView(self, url=self.path)
        # view = QWebEngineView(self)
        # view.load( QUrl("http://qt-project.org/"))
        # view.show()
        self.setCentralWidget(self.web_widget)
        # self.setCentralWidget(self.web_widget)

        
    def onOpen(self):
        path = QFileDialog.getOpenFileName(
            self, 'Select file',
            str(Path.home()/'Books'),
            'PDF files (*.pdf)')
        self.web_widget.load(QUrl.fromUserInput(f'{PDFJS}?file={path[0]}'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFBrother(args=sys.argv)
    window.setGeometry(600, 50, 800, 600)
    sys.exit(app.exec())