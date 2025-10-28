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
import json

### 😀😀 user : ui...
from modules.PyQt.Tabs.영업mbo.ui.Ui_tab_영업mob_관리자등록 import Ui_Tab_App as Ui_Tab

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

class 관리자등록__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		
		self.is_Auto_조회_Start = True
		self.param = ''		
		self.defaultParam = f"page_size=25"

		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		### wid_search hide
		# self.ui.Wid_Search_for.hide()

		self.triggerConnect()
		
		if hasattr(self, 'url_db_fields'):
			self._get_DB_Field(self.url_db_fields  )		
			ui_search_config_dict = {}
			if hasattr( self, '구분list') :
				ui_search_config_dict['구분list'] = self.구분list
			if hasattr( self, '고객사list'):
				ui_search_config_dict['고객사list'] = self.고객사list
			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
					
		

		self._init_helpPage()

		self._init_AutoStart()


	def triggerConnect(self):
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

		self.ui.PB_Sayongja_Magam.clicked.connect( self.slot_Sayongja_Magam )
		self.ui.PB_Admin_Magam.setEnabled ( False )
		self.ui.PB_Admin_Magam.clicked.connect ( self.slot_Admin_Magam)
		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	
	@pyqtSlot()
	def slot_Admin_Magam(self):
		dlg_res_button =  Utils.generate_QMsg_question(self, title="확인", text='관리자 입력을 마감하고, 최종 결과를 생성합니까? \n( 😀 월별 실적에 반영됩니다.)\n')
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			current_매출_year_month = {
				'매출_year' : self.api_datas[0].get('매출_year'),
				'매출_month' : self.api_datas[0].get('매출_month'),
			}
			is_ok, _json = APP.API.Send( INFO.URL_영업MBO_관리자마감 , {}, { 'is_관리자마감':True, 'query': json.dumps(current_매출_year_month,ensure_ascii=False ) } )
			if is_ok:

				Utils.generate_QMsg_Information(self, text="월별 실적에 반영되었읍니다.")
				self.slot_search_for()
				# self.slot_search_for('')
	
	@pyqtSlot()
	def slot_Sayongja_Magam(self):
		dlg_res_button =  Utils.generate_QMsg_question(self, title="확인", text='각 사용자가 입려한 값으로 관리자가 입력 형태로 변환합니까? \n( 😀기존에 관리자가 입력한 값은 초기화가 됩니다.)\n')
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			current_매출_year_month = {
				'매출_year' : self.api_datas[0].get('매출_year'),
				'매출_month' : self.api_datas[0].get('매출_month'),
			}
			is_ok, _json = APP.API.Send( INFO.URL_영업MBO_사용자마감 , {}, current_매출_year_month )
			if is_ok:
				self.slot_search_for('')

	
	@pyqtSlot(str)
	def slot_search_for(self, param:str='') :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""

		self.loading_start_animation()	

		self.param = param if len(param) >0 else self.param

		
		url = self.url + '?' + self.param

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

		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()

		### 마감 enable : 모든 admin_input_fk가 >0 있을때 and  관리자마감이 안 되어을 때
		### 😀 사용자등록 마감  : enabled ==>  관리자 등록 마감과 같이 움직임.
		_enabled =  all ([ bool( obj.get('admin_input_fk',-1) > 0   ) for obj in self.api_datas ] ) 

		# for obj in self.api_datas:

		self.ui.PB_Admin_Magam.setEnabled (_enabled  )
		self.ui.PB_Sayongja_Magam.setEnabled ( True )

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


