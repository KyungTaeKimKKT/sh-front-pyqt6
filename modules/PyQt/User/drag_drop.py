from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Drag_Drop_Files:
    #### dragEnter => dragMove ==> drop Evnet 순
    def dragEnterEvent(self, event:QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event:QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event:QDropEvent) -> list:

        file_paths = []
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            file_paths = [ url.toLocalFile() for url in event.mimeData().urls() ]

            event.accept()
        else:
            event.ignore()
        return [1,2,3]

class Drag_Drop_Image:
    def dragEnterEvent(self, event:QDragEnterEvent):
        if event.mimeData().hasImage():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event:QDragMoveEvent):
        if event.mimeData().hasImage():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event:QDropEvent):
        if event.mimeData().hasImage():
            event.setDropAction(Qt.CopyAction)
            self.file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(self.file_path)

            event.accept()
        else:
            event.ignore()