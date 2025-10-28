from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy
from modules.PyQt.dialog.file.ui.Ui_dialog_file_upload_with_listwidget import Ui_Dialog
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_file_upload_with_listwidget(QDialog):
    signal_save = pyqtSignal( QDialog, dict, dict, str)
    # signal__ = pyqtSignal()

    def __init__(self, parent , **kwargs):
        super().__init__(parent)
        self.m2mField : str  ### '의뢰file_fks'등
        self.original_dict : dict ### api_data[row]
        self.display_dict : dict[int:str]  ### [fname....] 등

        for k,v in kwargs.items():
            setattr(self, k, v)
        
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        if hasattr(self, 'original_dict') and hasattr(self, 'display_dict'):
            self.ui.widget._update_attribute( **kwargs )

        self.show()

        self.ui.PB_Save.clicked.connect(self.slot_PB_Save)

  
    @pyqtSlot()
    def slot_PB_Save(self):
        """ listWidget의 _data :list[str]을 가져와서 \n
            최초 보내준 original_dict:dict(api data) 와 display_dict :list[str] ==> listWidget의 _data임. \n 
            를 비교해서 기존것과 new를 합쳐서 signal emit함. 
        """
        sendData = {}
        sendData['fileNames'] = self.ui.widget._getValue()
        self.signal_save.emit( self, 
                              self.original_dict if hasattr(self, 'original_dict') else {}, 
                              sendData ,
                              self.m2mField if hasattr(self, 'm2mField') else '',
                              )