import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# from modules.PyQt.Tabs.생산지시.ui.Ui_생산지지서_form_empty_tab import Ui_Form
from modules.PyQt.Tabs.생산지시서.dialog.ui.Ui_생산지지서_form_empty_tab import Ui_Form
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_생산지시서_SPG_Empty(QWidget):
    def __init__(self, parent, **kwargs):
        super().__init__(parent )
        self.kwargs = kwargs
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        if 'file' in kwargs and  kwargs['file'] :
            self.ui.Wid_imageViewer.update_kwargs ( url =  kwargs['file'] )
        
    #     self.dataObj = {}
    #     self.setupUi(self)
    
    def _getValue(self) -> dict:
        resultDict =  self.ui.Wid_imageViewer.getValue()
        resultDict['id'] = self.kwargs.get('id', -1)
        return resultDict

    # def editMode(self, dataObj:dict={} ):
    #     self.dataObj = dataObj if dataObj else self.dataObj
    #     if self.dataObj:
    #         self.Wid_imageViewer.set_image_from_URL(url=self.dataObj.get('file'))

    # def viewMode(self, dataObj:dict={} ):
    #     self.editMode ( dataObj)        
    #     self.Wid_imageViewer.readOnly()