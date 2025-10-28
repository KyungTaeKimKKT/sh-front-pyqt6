from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from datetime import date, datetime
import copy, json

### 😀😀 user : ui...
from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table

from modules.PyQt.Tabs.HR평가.tables.Wid_table_종합평가_결과 import Wid_table_종합평가 as Wid_table


import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger		
logger = get_plugin_logger()


class 종합평가_결과__for_stacked_Table( Base_Stacked_Table ):
	default_view_name = '종합평가'

	def init_ui(self):
		self.map_table_name = {
			self.default_view_name: Wid_table(self),
		}
		self.add_Widgets(self.map_table_name)

	def set_api_datas(self, api_datas:dict[str, dict]):
		self.api_datas = api_datas
		for name, widget in self.map_table_name.items():
			widget.set_api_datas( api_datas )
		self.setCurrentWidget(self.default_view_name)

	def set_url(self, url:str):
		self.url = url

class 종합평가_결과__for_Tab( BaseTab ):

	is_no_config_initial = True		### table config 없음
	is_auto_api_query = True


	def create_ui(self):
		logger.debug(f"create_ui : self._ui_initialized : {hasattr(self, '_ui_initialized')}")
		if hasattr(self, '_ui_initialized') and self._ui_initialized:
			logger.debug(f"create_ui : {self._ui_initialized}")
			return
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 종합평가_결과__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		
		self._ui_initialized = True

	def create_combo_HR_Evaluation(self) -> Optional[QComboBox]:
		url = 'HR평가_V2/평가설정_DB/'
		param = f"?page_size=0"
		_isOk, _json = APP.API.getlist(f"{url}{param}".replace('//', '/'))
		self.Combo_HR_Evaluation = QComboBox()
		if _isOk:
			self.Combo_HR_Evaluation.addItems([f"{obj.get('id')}--{obj.get('제목')}" for obj in _json])
			self.Combo_HR_Evaluation.currentTextChanged.connect(self.on_combo_HR_Evaluation_changed)
		else:
			Utils.generate_QMsg_critical(self, title="HR평가 설정 조회 실패", text="HR평가 설정 조회 실패")
		return self.Combo_HR_Evaluation
	
	def on_combo_HR_Evaluation_changed(self, text:str):
		logger.info(f"on_combo_HR_Evaluation_changed : text : {text}")
		### 평가설정_fk 추출
		eval_id = text.split('--')[0]
		eval_title = text.split('--')[1]
		logger.info(f"on_combo_HR_Evaluation_changed : eval_id : {eval_id}, eval_title : {eval_title}")
		pass

	def custom_ui(self):
		#### HR평가 설정 ComboBox를 맨앞으로 추가
		combo = self.create_combo_HR_Evaluation()
		if combo:
			# 맨 앞에 삽입
			self.ui.h_search.insertWidget(0, combo)
			self.ui.h_search.addSpacing(16*2)

		#### 
		self.ui.h_search.addStretch()
		self.PB_Refresh = QPushButton()
		self.PB_Refresh.setText('새로고침')
		self.PB_Refresh.clicked.connect(self.on_refresh)
		self.ui.h_search.addWidget(self.PB_Refresh)
		self.ui.h_search.addSpacing(16*3)
		### 임시저장 버튼	
		self.PB_Close_HR_Evaluation = QPushButton()
		self.PB_Close_HR_Evaluation.setText('HR평가 닫기')
		self.PB_Close_HR_Evaluation.setEnabled(False)
		self.PB_Close_HR_Evaluation.clicked.connect(self.on_close_HR_Evaluation)
		self.ui.h_search.addWidget(self.PB_Close_HR_Evaluation)
		self.ui.h_search.addSpacing(16*3)


	def on_close_HR_Evaluation(self):
		logger.info(f"on_close_HR_Evaluation")
		if self.api_datas:
			평가설정 = self.api_datas['평가설정_data']
			dlg_res_button = Utils.generate_QMsg_question(self, title=f"HR평가 : {평가설정['제목']} 닫기", text="HR평가를 닫으시겠습니까?")
			if dlg_res_button != QMessageBox.StandardButton.Ok :
				return 
			
			eval_id = 평가설정['id']
			param = f"평가설정_fk={eval_id}"
			print(f"on_close_HR_Evaluation : param : {param}")
		else:
			Utils.generate_QMsg_critical(self, title="HR평가 설정 조회 실패", text="HR평가 조회된 data가 없습니다.")

		

	def on_refresh(self):
		combo_text = self.Combo_HR_Evaluation.currentText()
		eval_id = combo_text.split('--')[0]
		param = f"평가설정_fk={eval_id}"
		self.run_by_(self.url, param)

	def run_by_(self,  url:str=None, param:str=None, is_external_exec:bool=False):
		""" class 외부에서 호출 가능."""
		self.is_external_exec = is_external_exec
		self.stacked_table.set_url(url if url else self.url)
		self.url = url if url else self.url
		self.param = param if param else self.param
		url = f"{self.url}?{self.param}".replace('//', '/').replace('??', '?')
		QTimer.singleShot( 100, lambda: self.on_fetch_start(url))

	def run(self):		
		# self.url = 'HR평가_V2/평가결과_종합_API_View/'
		# self.stacked_table.set_url(self.url)
		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
			param = f"page_size=0"
			self.run_by_(self.url, param)
			# url = f"{self.url}?{param}".replace('//', '/')
			# QTimer.singleShot( 100, lambda: self.on_fetch_start(url))

	def on_fetch_start(self, url:str ):		
		_isok, _json = APP.API.getlist(url)
		# logger.debug(f"on_fetch_start : _json : {_json}")
		if _isok:
			self.hanle_api_datas(_json)
		else:
			Utils.generate_QMsg_critical( self, title="서버 조회 오류", text=json.dumps(_json) 
								if _json else "서버 조회 오류" )
	
	def hanle_api_datas(self, api_datas:dict):
		### 1. self.map_api_datas 업데이트
		self.api_datas = api_datas
		#### 동작을 시켜서 적용 ( style 등 자동 적용 위해 )
		QTimer.singleShot( 100, lambda: self.stacked_table.set_api_datas(api_datas) )
		print(f"hanle_api_datas : api_datas['평가설정_data'] : {api_datas['평가설정_data']}")
		평가설정 = api_datas['평가설정_data']
		if 평가설정:
			is_cloes_enabled = bool ( 평가설정['is_시작'] and not 평가설정['is_종료'] )
			self.PB_Close_HR_Evaluation.setEnabled(is_cloes_enabled)
		else:
			self.PB_Close_HR_Evaluation.setEnabled(False)


	def slot_fetch_finished(self, msg) -> tuple[bool, dict, list[dict]]:
		logger.debug(f"{self.__class__.__name__} : slot_fetch_finished : {msg}")
		return True, {}, []


























# from PyQt6 import QtCore, QtGui, QtWidgets
# from PyQt6.QtWidgets import *
# from PyQt6.QtCore import *
# from PyQt6.QtGui import *
# from typing import TypeAlias

# import pandas as pd
# import urllib
# from datetime import date, datetime
# import copy

# import pathlib
# import openpyxl
# import typing

# import concurrent.futures
# import asyncio
# import time

# ### 😀😀 user : ui...
# from modules.PyQt.Tabs.HR평가.ui.Ui_tab_HR평가_종합평가_결과 import Ui_Tab_App as Ui_Tab

# ###################
# from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

# from modules.user.utils_qwidget import Utils_QWidget
# from modules.PyQt.User.toast import User_Toast
# from config import Config as APP
# from modules.user.async_api import Async_API_SH
# from info import Info_SW as INFO
# import modules.user.utils as Utils
# 

# from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
# import traceback
# from modules.logging_config import get_plugin_logger



# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()

# class 종합평가_결과__for_Tab( QWidget, Utils_QWidget):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent )
		
# 		self.is_Auto_조회_Start = False

# 		self.param = ''		
# 		self.defaultParam = f"page_size=0"

# 		self._init_kwargs(**kwargs)

# 		self.ui = Ui_Tab()
# 		self.ui.setupUi(self)
# 		### wid_search hide
# 		# self.ui.Wid_Search_for.hide()

# 		self.triggerConnect()

# 		_isOk, self.평가설정_api_datas = APP.API.getlist( INFO.URL_HR평가_평가설정DB+INFO.PARAM_NO_PAGE )
# 		if _isOk:
# 			self.ui.Wid_Search_for._update_config ( 평가제목_fk_list = [ f"{obj.get('id')}--{obj.get('제목')}" for obj in self.평가설정_api_datas] )
		
		
# 		if hasattr(self, 'url_db_fields'):
# 			self._get_DB_Field(self.url_db_fields  )		
# 			ui_search_config_dict = {}
# 			if hasattr( self, '구분list') :
# 				ui_search_config_dict['구분list'] = self.구분list
# 			if hasattr( self, '고객사list'):
# 				ui_search_config_dict['고객사list'] = self.고객사list
# 			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
# 				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
					
		

# 		self._init_helpPage()

# 		self._init_AutoStart()

# 		# _isOk, self.종합평가_api_datas = APP.API.Send( self.url, {}, {'평가설정_fk':5})
# 		# if _isOk:
# 		# 	self.table_update ( False, True, self.종합평가_api_datas )

# 		### {'0': 1, '1': 1, '2': 1, '0_id': 1383, '0_평가자_ID': 1, '0_평가자_성명': 'admin', '1_id': 1384, '1_평가자_ID': 1, '1_평가자_성명': 'admin', '2_id': 1385, '2_평가자_ID': 1, '2_평가자_성명': 'admin'},



# 	def triggerConnect(self):
# 		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)	### 😀api send data : dict로 받음
# 		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download_without_param)
# 		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

# 		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))


# 	#### app마다 update 할 것.😄
# 	def run(self):
		
# 		return 
	
# 	@pyqtSlot(dict)
# 	def slot_search_for(self, send_Data:dict) :
# 		"""
# 		결론적으로 main 함수임.
# 		Wid_Search_for에서 query param를 받아서, api get list 후,
# 		table에 _update함.	
# 		"""
# 		self.loading_start_animation()	

# 		_isOk, self.종합평가_api_datas = APP.API.Send( self.url, {}, send_Data)
# 		if _isOk:
# 			self.table_update ( False, True, self.종합평가_api_datas )
# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	@pyqtSlot()
# 	def slot_download_without_param(self):
# 		self.save_data_to_file( False, True, self.api_datas )


# 	@pyqtSlot(bool, bool, object)
# 	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
# 		if not _isOk:
# 			self._disconnect_signal (self.work.signal_worker_finished)
# 			self.loading_stop_animation()
# 			Utils.generate_QMsg_critical(self)
# 			return 

# 		if is_Pagenation :
# 			search_result_info:dict = copy.deepcopy(api_datas)
# 			self.api_datas = search_result_info.pop('results')
# 			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
# 		else:
# 			self.api_datas = api_datas
# 			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
# 		if len(self.api_datas) == 0 :
# 			self.api_datas = self._generate_default_api_datas()

# 		self.db_fields = self._modify_db_fields( self.db_fields )	### is_submit 변경가능하도록

# 		self.ui.Wid_Table._update_data(
# 			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 			url = self.url,
# 			**self.db_fields,
# 			# table_header = 
# 		)	
# 		try:
# 			self._disconnect_signal (self.work.signal_worker_finished)
# 		except:
# 			pass
# 		self.loading_stop_animation()

# 	def _modify_db_fields( self, db_fields:dict ) -> dict:
# 		no_edit_cols:list[str] = copy.deepcopy ( db_fields['table_config']['no_Edit_cols'] )
# 		# del_is_submit = [ name for name in no_edit_cols if 'is_submit' not in name ]
# 		db_fields['table_config']['no_Edit_cols'] =  [ name for name in no_edit_cols if 'is_submit' not in name ]

# 		db_fields['fields_append'].update( {name: 'BooleanField' for name in no_edit_cols if 'is_submit' in name } )
		
# 		return db_fields


# 	def _generate_default_api_datas(self) ->list[dict]:		
# 		table_header:list[str] = self.db_fields['table_config']['table_header']
# 		obj = {}
# 		for header in table_header:
# 			if header == 'id' : obj[header] = -1
# 			else:
# 				match self.fields_model.get(header, '').lower():
# 					case 'charfield'|'textfield':
# 						obj[header] = ''
# 					case 'integerfield'|'floatfield':
# 						obj[header] = 0
# 					case 'datetimefield':
# 						# return QDateTime.currentDateTime().addDays(3)
# 						obj[header] =  datetime.now()
# 					case 'datefield':
# 						# return QDate.currentDate().addDays(3)
# 						obj[header] =  datetime.now().date()
# 					case 'timefield':
# 						# return QTime.currentTime()
# 						obj[header] = datetime.now().time()
# 					case _:
# 						obj[header] = ''
# 		return [ obj ]