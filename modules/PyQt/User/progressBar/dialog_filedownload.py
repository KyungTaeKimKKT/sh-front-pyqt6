from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.User.progressBar.ui.Ui_dialog_filedownload import Ui_Dialog
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_FileDownload(QDialog, Qwidget_Utils):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.dataObj = {
            'fileSize' : '0',
            'time'     : '0', 
            'progress' : 0,
        }

        self.inputDict = {
            'fileSize' : self.ui.label_fileSize,
            'time'      : self.ui.label_TimeEstimated,
            'progress'  : self.ui.progressBar,
        }

        self.show()