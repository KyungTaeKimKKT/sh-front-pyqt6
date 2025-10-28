from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtCore import *

from modules.PyQt.compoent_v2.pdfViwer.pdfViewer_by_webengine import PDFViewer_by_Webengine
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dlg_Pdf_Viewer_by_webengine(QDialog):
    def __init__(self, parent , **kwargs ):
        super().__init__(parent)

        layout = QVBoxLayout()
        pdf_viewer = PDFViewer_by_Webengine(**kwargs)
        layout.addWidget(pdf_viewer)

        self.setLayout(layout)
        self.setWindowTitle ('HELP PAGE')
        self.setMinimumSize( 1200, 1000)
        self.show()