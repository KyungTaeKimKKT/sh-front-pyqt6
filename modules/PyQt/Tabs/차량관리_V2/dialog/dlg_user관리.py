import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import openpyxl
import typing

from modules.user.utils_qwidget import Utils_QWidget

from modules.PyQt.Tabs.차량관리.dialog.ui.Ui_tab_user관리 import Ui_Tab

# import user module
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.ui.Ui_tabs import Ui_Tabs

import modules.user.utils as utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO

from modules.PyQt.User.Tb_Model import Base_TableModel, Base_TableModel_Pandas
from modules.PyQt.User.Tb_Delegate import Base_Delegate, AlignDelegate
from modules.PyQt.Tabs.Base import Base_App
import traceback
from modules.logging_config import get_plugin_logger





# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_차량관리_User관리(QDialog, Utils_QWidget):
	signal = pyqtSignal(dict)
	signal_appDataChanged = pyqtSignal()

	def __init__(self, parent=None, url:str='', **kwargs):
		super().__init__(parent )
		self.isAppDataChanged = False
		self.app_Dict : dict
		self.url_APP설정 = url
		self.m2m_keyName :str
		# self.url = url if len(url) > 5 else INFO.URL_User_ALL
		self.url_UserInfo = INFO.URL_User_ALL
		for key, value in kwargs.items():			
			setattr(self, key, value )

		self.app_Dict : dict
		self._get_DB_Field(url=INFO.URL_DB_Field_User_View )

		self.ui = Ui_Tab()
		self.ui.setupUi(self)

		self.triggerConnect()

		self._create_APP사용자_table()

		self.show()

	def _create_APP사용자_table(self, api_datas:list[dict]=[] ):
		def add_사용자_User_table(app_Dict:dict, user_datas:list[dict]):
			user_pks:list[int] = app_Dict.get(self.m2m_keyName)
			for userDict in user_datas:
				if userDict.get('id') in user_pks:
					userDict['사용유무'] = True
				else:
					userDict['사용유무'] = False
			return user_datas

		if not api_datas :
			info = INFO()			
			api_datas = info._get_all_user()

		self.ui.Wid_Table._update_data(
			api_data=add_사용자_User_table(self.app_Dict, api_datas ),			
			url = self.url_UserInfo,
			url_APP설정 = self.url_APP설정,
			**self.db_fields,
			app_Dict = self.app_Dict,
			m2m_keyName = self.m2m_keyName,
		)

	def triggerConnect(self):
		search = self.ui.lineEdit_search
		search.textChanged.connect(lambda: self.ui.Wid_Table._search_table(search.text()) )
		### table에서 data가 바뀌면 signaling
		self.ui.Wid_Table.signal_appData_Changed.connect(self.slot_appData_changed )

	def run(self):
		return 


	@pyqtSlot(dict)
	def slot_appData_changed(self, msg:dict) -> None:
		self.isAppDataChanged = True
		

	def closeEvent(self, a0):
		if self.isAppDataChanged:
			self.signal_appDataChanged.emit()
		return super().closeEvent(a0)

	

	
	


# def main():    

#     app=QApplication(sys.argv)
#     window= Win_app사용자관리()
#     window.show()
#     app.exec_()


# if __name__ == "__main__":
#     sys.exit( main())