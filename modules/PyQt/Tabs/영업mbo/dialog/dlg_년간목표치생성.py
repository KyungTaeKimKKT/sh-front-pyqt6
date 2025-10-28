from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import datetime

from modules.PyQt.Tabs.영업mbo.dialog.ui.Ui_dlg_년간목표치생성 import Ui_Dialog 
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from modules.PyQt.User.validator import 망등록_망번호_Validator
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_년간목표생성(QDialog,   Qwidget_Utils):
    """ kwargs \n
        url = str,\n
        dataObj = {}
    """
    signal_data = pyqtSignal(dict)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.PB_Save.setEnabled(True)
        self.__init__default_setting()

        self.ui.checkBox_Jojik_new.setEnabled ( self.ui.checkBox_Jojik.checkState() == Qt.CheckState.Checked ) 
        self.ui.checkBox_Gaein_new.setEnabled (  self.ui.checkBox_Gaein.checkState() == Qt.CheckState.Checked ) 

        self.inputDict ={
            'year' : self.ui.spinBox,
            'is_조직' : self.ui.checkBox_Jojik,
            'is_조직_new' : self.ui.checkBox_Jojik_new,
            'is_개인' : self.ui.checkBox_Gaein,
            'is_개인_new' : self.ui.checkBox_Gaein_new,         
        }

        self.ui.PB_Save.clicked.connect (self.on_PB_Save_clicked )
        self.ui.checkBox_Jojik.stateChanged.connect( lambda: self.ui.checkBox_Jojik_new.setEnabled ( self.ui.checkBox_Jojik.checkState() == Qt.CheckState.Checked ) )
        self.ui.checkBox_Gaein.stateChanged.connect( lambda: self.ui.checkBox_Gaein_new.setEnabled ( self.ui.checkBox_Gaein.checkState() == Qt.CheckState.Checked ) )
        
        self.show()

    @pyqtSlot()
    def on_PB_Save_clicked(self):
        sendData = self._get_value_from_InputDict()
        ### is_조직, is_개인 checkbox tri-stage
        sendData['is_조직'] = self.ui.checkBox_Jojik.checkState() == Qt.CheckState.Checked 
        sendData['is_개인'] = self.ui.checkBox_Gaein.checkState() == Qt.CheckState.Checked 
        self.signal_data.emit (sendData)

    def __init__default_setting(self):
        now = datetime.now()
        self.ui.spinBox.setMaximum(2099)
        self.ui.spinBox.setMinimum(now.year )
        self.ui.spinBox.setValue ( now.year+1)
    