from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime
import copy

import pathlib
import openpyxl
import typing

import concurrent.futures
import asyncio
import time

### 😀😀 user : ui...
from modules.PyQt.Tabs.영업mbo.ui.Ui_tab_영업mob_년간보고 import Ui_Tab_App as Ui_Tab

###################
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 년간목표입력_개인별__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		
		self.is_Auto_조회_Start = True

		self.param = ''		
		now = datetime.now()		
		self.defaultParam =  f"매출년도={str(now.year)}&page_size=0"
		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		### wid_search hide
		# self.ui.Wid_Search_for.hide()

		self.triggerConnect()
		
		if hasattr(self, 'url_db_fields'):
			self._get_DB_Field(self.url_db_fields  )		
			ui_search_config_dict = {}
			for listName in ['매출년도list']:
				if hasattr( self, listName) :
					ui_search_config_dict[listName] = [ str(year) for year in getattr( self, listName ) ]

			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
					
		

		self._init_helpPage()

		self._init_AutoStart()


	def triggerConnect(self):
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	
	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""
		self.loading_start_animation()	

		self.param = param 
		
		url = self.url + '?' + param

		###😀 GUI FREEZE 방지 ㅜㅜ;;
		pool = QThreadPool.globalInstance()
		self.work = Worker(url)
		self.work.signal_worker_finished.signal.connect ( self.table_update )
		pool.start( self.work )



	@pyqtSlot(bool, bool, object)
	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
		if not _isOk:
			self._disconnect_signal (self.work.signal_worker_finished)
			self.loading_stop_animation()
			Utils.generate_QMsg_critical(self)
			return 

		if is_Pagenation :
			search_result_info:dict = copy.deepcopy(api_datas)
			self.api_datas = search_result_info.pop('results')
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
		else:
			self.api_datas = api_datas
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )

		#### table_config update 😀 table wid에서 modify 하는지 확인 필요.
		self._modity_table_config()

		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()


	def _modity_table_config(self) -> None:
		""" 여기서 필요에 따라 table_config modify """
		t_config = self.db_fields.get('table_config')
		t_config['no_Edit_rows'] = [  idx  for idx, api_data in enumerate(self.api_datas) if api_data.get('분류') != '계획' ]
	# def _generate_default_api_data(self) ->list[dict]:		
	# 	return [ { key: self._generate_default_value_by_Type(key, value)  for key, value in self.fields_model.items()  } ]

	# def _generate_default_value_by_Type(self, key:str, value:str) :
	# 	if  'id' == key  : return  -1 

	# 	match value.lower():
	# 		case 'charfield'|'textfield':
	# 			return ''
	# 		case 'integerfield'|'floatfield':
	# 			return 0
	# 		case 'datetimefield':
	# 			# return QDateTime.currentDateTime().addDays(3)
	# 			return datetime.now()
	# 		case 'datefield':
	# 			# return QDate.currentDate().addDays(3)
	# 			return datetime.now().date()
	# 		case 'timefield':
	# 			# return QTime.currentTime()
	# 			return datetime.now().time()
			
	# 		case _:
	# 			return None


