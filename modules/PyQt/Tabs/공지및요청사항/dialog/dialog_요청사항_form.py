from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.Tabs.공지및요청사항.ui.Ui_dialog_요청사항_form import Ui_Dialog
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_요청사항_form(QDialog, Qwidget_Utils):
    signal_save = pyqtSignal(QDialog, dict)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.triggerConnect()        

        self._init_Ui_comboBox_Gubun()

        self.inputDict ={
            '제목' : self.ui.lineEdit_Jemok,
            '요청구분' : self.ui.comboBox_Gubun,
            '내용' : self.ui.plainTextEdit_Naeyong,
        }

        self.ui.lineEdit_Jemok.textChanged.connect( self.check_lineEdit_Jemok_validation)
        self.show()

    def triggerConnect(self):
        self.ui.PB_Save.clicked.connect( self.on_PB_Save_clicked)
  
    def _init_Ui_comboBox_Gubun(self):
        self.ui.comboBox_Gubun.addItems(INFO.Combo_요청사항_구분_Items)

    @pyqtSlot()
    def on_PB_Save_clicked(self):
        sendData = self._get_value_from_InputDict()
        ### sendData 보완         
        sendData['등록자'] = INFO.USERID

        fileNames = self.ui.widget_fileupload_listwidget._getValue()

        sendData['fileNames'] = fileNames
        if INFO.IS_DebugMode :print ( sendData )

        self.signal_save.emit(self, sendData )


    @pyqtSlot()
    def check_lineEdit_Jemok_validation(self) -> None:
        self.ui.PB_Save.setEnabled ( len(self.ui.lineEdit_Jemok.text()) >= 3 )

