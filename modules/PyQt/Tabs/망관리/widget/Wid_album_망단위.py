from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.Tabs.망관리.widget.ui.Ui_Wid_album_망단위 import Ui_Form
from modules.PyQt.component.imageviewer.wid_image_view import Wid_Image_Viewer

from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_album_망단위(QWidget, Ui_Form, Qwidget_Utils):
    """ kwargs \n
        dataObj : dict \n
    """
    def __init__(self, parent, **kwargs ):
        super().__init__(parent)
        self.dataObj : dict = {}
        for k, v in kwargs.items():
            setattr( self, k, v)

        self.setupUi(self)
        self.fileKeyNames = ['file1','file2']
        self.inputDict = {
            '망번호' : self.LB_MangNo,
            '고객사' : self.LB_Gogaek,
            '현장명' : self.LB_Hyunjang,
            '문양'   : self.LB_Munyang,
            '의장종류' : self.LB_Uljang,
            '할부치수' : self.LB_Halbu,
            '품명'     :  self.LB_Pummyung,
            '망사'     : self.LB_Mangsa,
            '사용구분' : self.LB_Sayong,
            # '세부내용' : self.plainTextEdit_Sebu,
            # '비고'     : self.plainTextEdit_Bigo,
            # '검색key'  : self.lineEdit_Gumsaek,
        }
        # self.widget_Image1._resizeFlag = False
        # self.widget_Image2._resizeFlag = False

        self.viewMode()

    def _update_data ( self, **kwargs) :
        for k, v in kwargs.items():
            setattr( self, k, v)
        if hasattr(self, 'dataObj') and self.dataObj:
            self.viewMode()
        else:
            self._clear()
    
    def _clear(self):
        for k, wid in self.inputDict.items():
            wid : QLabel
            wid.clear()
        self.widget_Image1._clear()
        self.widget_Image2._clear()

    def viewMode(self, **kwargs):
        super().viewMode()

        for idx, key in enumerate( self.fileKeyNames ):
            if ( url := self.dataObj.get(key,'') ):
                if url is not None and len(url) > 10 :
                    url = str(url).replace('192.168.7.108:9999','mes.swgroup.co.kr:10000')
                    wid_image :  Wid_Image_Viewer  = getattr(self, f"widget_Image{idx+1}")
                    wid_image._update_Data( _url = url )
            # if idx == 0: self.widget_Image1.set_image_from_URL( url )
            # if idx == 1: self.widget_Image2.set_image_from_URL( url )