from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from modules.PyQt.dialog.dialog_common import Dialog_Common

from modules.PyQt.component.imageviewer.wid_image_view import Wid_Image_Viewer
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_ImageView(QDialog,  Dialog_Common):
    """
        kwargs \n
        displayList = list[ { type: value}] \n
            여기사, type는 _url, _pixmap ... 이며, \n
            value는 url주소, QPixmpa object. \n

    """
    def __init__(self, parent , **kwargs):
        super().__init__(parent)
        self.displayList:list[dict[str:str] ] 
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.UI()

        ### 😀 Dialog_Common method
        self.common_setting()

    def UI(self):
        vLayout = QVBoxLayout()

        if hasattr(self, 'displayList') and self.displayList:
            for obj in self.displayList:

                wid_image = Wid_Image_Viewer( self, **obj )
                vLayout.addWidget( wid_image )
        
        self.setLayout ( vLayout )
        self.show()