from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import json
import copy

from modules.PyQt.Tabs.생산관리.ui.Ui_생산관리_D_DAY import Ui_Form
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config  import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_생관_DDay관리(QDialog, Ui_Form, Qwidget_Utils):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.URL = INFO.URL_생산계획_DDay
        self.dataObj = {}

        self.inputDict = {
            '_출하일' :  self.spinBox_chulha,
            '_PO' :      self.spinBox_PO,
            '_판금':     self.spinBox_Pangum,
            '_HI'  :     self.spinBox_HI,
            '_구매':     self.spinBox_Gumae,
            '_생지':     self.spinBox_Sangji,
            '_작지':     self.spinBox_Jakji,
        }

        self.get_api_data()

    def get_api_data(self):
        """ suffix를 안해서, {'links': {'next': None, 'previous': None}, 'countTotal': 1, 'countOnPage': 10, 'current_Page': 1, 'total_Page': 1, 'results': [{'id': 1, '_출하일': 0, '_PO': -1, '_판금': -5, '_HI': -10, '_구매': -14, '_생지': -16, '_작지': -17}]}"""
        is_ok, app_DB_Data= APP.API.getlist(self.URL)

        if is_ok and app_DB_Data:
            self.dataObj = app_DB_Data.get('results')[0]
            self.editMode()

    @pyqtSlot()
    def on_PB_save_clicked(self):
        api_send_data = self._get_value_from_InputDict()
        is_ok, _ = APP.API.Send( self.URL, {}, api_send_data)
        self.close()



if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	w =  Wid_생관_DDay관리()
	w.show()
	sys.exit(app.exec())