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

from modules.PyQt.Tabs.HR평가.tables.Wid_table_상급자평가_개별 import Wid_table_상급자평가_개별
from modules.PyQt.Tabs.HR평가.tables.Wid_table_상급자평가_종합 import Wid_table_상급자평가_종합

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()



class 상급자평가__for_stacked_Table( Base_Stacked_Table ):
	# default_view_name = DEFAULT_VIEW

	def init_ui(self):
		self.map_table_name = {

		}
		if self.map_table_name:
			self.add_Widgets(self.map_table_name)

	def set_api_datas(self, key:str, api_datas:list[dict]):
		self.map_api_datas[key] = api_datas		
		self.map_table_name[key].set_api_datas(api_datas)


class 상급자평가__for_Tab( BaseTab ):
	is_no_config_initial = True		### table config 없음
	is_auto_api_query = True
	

	map_api_datas = {
		'역량평가': [],
		'성과평가': [],
		'특별평가': [],
	}

	

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		### api_datas에 따른 동적 UI 생성
		# self.stacked_table = 상급자평가__for_stacked_Table(self)
		# self.ui.v_table.addWidget(self.stacked_table)

		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def create_dynamic_ui(self, map_api_datas:dict[int, list[dict]]):
		#### h_search 기존 widgets 삭제
		#### refresh 버튼 때문에 clear 해야 함.
		self.clear_layout(self.ui.h_search)
		self.clear_layout(self.ui.v_table)

		from modules.PyQt.compoent_v2.custom_상속.custom_PB import HR평가_Stacked_PB		
		self.map_stacked_button :dict[str, HR평가_Stacked_PB ] = {}
		##### stacked_table 버튼 추가
		self.map_stacked_table :dict[str, Wid_table_상급자평가_개별|Wid_table_상급자평가_종합] = {}

		for 차수, api_datas in map_api_datas.items():

			logger.info(f"차수 : {차수}")
			logger.debug(f"type(api_datas) : {type(api_datas)}")
			logger.debug(f"api_datas : {api_datas}")
			if not api_datas:
				continue
			평가종류 = api_datas[0].get('역량평가_fk').get('평가종류')
			### pb 생성
			pb_text = f'{차수}차 평가({평가종류})'
			attr_name = f"PB_{차수}"
			object_name = attr_name
			setattr(self, attr_name, HR평가_Stacked_PB())
			pb:HR평가_Stacked_PB = getattr(self, attr_name)	
			pb.setObjectName(object_name)
			pb.setText(pb_text)
			pb.clicked.connect( self.on_stacked_button_clicked )
			self.ui.h_search.addWidget(pb)
			self.map_stacked_button[object_name] = pb
			self.ui.h_search.addWidget( pb )


			if 평가종류 == '개별':
				setattr(self, f"wid_table_{차수}", Wid_table_상급자평가_개별(self, api_datas))
			else:
				setattr(self, f"wid_table_{차수}", Wid_table_상급자평가_종합(self, api_datas))

			self.map_stacked_table[object_name] = getattr(self, f"wid_table_{차수}")

		self.label_warning = QLabel()
		self.label_warning.setText('피평가자의 각 성과 column을 클릭하여 개별 평가 후 제출하기 바랍니다.')
		self.ui.h_search.addWidget(self.label_warning)
		
		self.ui.h_search.addStretch()
		self.PB_Refresh = QPushButton()
		self.PB_Refresh.setText('새로고침')
		self.PB_Refresh.clicked.connect(self.on_refresh)
		self.ui.h_search.addWidget(self.PB_Refresh)
		# self.ui.h_search.addSpacing(16*3)
		### 임시저장 버튼	
		# self.PB_Save = QPushButton()
		# self.PB_Save.setText('임시저장')
		# self.PB_Save.clicked.connect(self.on_save)
		# self.ui.h_search.addWidget(self.PB_Save)
		# self.ui.h_search.addSpacing(16*3)

		# self.PB_Submit = QPushButton()
		# self.PB_Submit.setText('제출')
		# self.PB_Submit.setEnabled(False)
		# self.PB_Submit.clicked.connect(self.on_submit)
		# self.ui.h_search.addWidget(self.PB_Submit)

		self.stacked_table = 상급자평가__for_stacked_Table(self)
		self.stacked_table.add_Widgets(self.map_stacked_table)
		
		self.ui.v_table.addWidget(self.stacked_table)

		#### 

	def on_request_refresh(self, _is_request:bool):
		print ('상급자평가 : ','on_request_refresh')
		self.run()

	def on_refresh(self):
		print ('상급자평가 : ','on_refresh')
		self.run()


	def on_submit(self):
		### 제출
		api_datas = self.stacked_table.get_api_datas()
		logger.debug(f"api_datas : {api_datas}")

	def on_stacked_button_clicked(self):
		object_name = self.sender().objectName()
		logger.debug(f"on_stacked_button_clicked : {object_name}")
		self.stacked_table.setCurrentWidget(object_name)
		for k, wid_pb in self.map_stacked_button.items():
			if k != object_name:
				wid_pb.set_released()				
			else:
				wid_pb.set_pressed()



	def subscribe_gbus(self):
		super().subscribe_gbus()
		print ('상급자평가 : ','subscribe_gbus')
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
		self.event_bus.subscribe(f"{self.table_name}:request_refresh", self.on_request_refresh)


	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_datas_changed(self, api_datas:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_datas_changed : {len(api_datas)}")


	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		logger.debug(f" api_datas : {self.api_datas}")
		if hasattr(self, 'selected_rows'):
			self.selected_rows = selected_rows

	def run(self):
		# self.url = 'HR평가_V2/상급자평가_Api_View/'
		self.subscribe_gbus()
		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
			param = f"평가자_id={INFO.USERID}"
			url = f"{self.url}?{param}".replace('//', '/')
			QTimer.singleShot( 100, lambda: self.on_fetch_start(url))

	def on_fetch_start(self, url:str ):		
		_isok, _json = APP.API.getlist(url)
		if _isok:
			logger.debug(f"{self.__class__.__name__} : on_fetch_start : {_json}")
			self.map_api_datas = _json
			
			self.create_dynamic_ui(self.map_api_datas)

			#### 동작을 시켜서 적용 ( style 등 자동 적용 위해 )
			first_pb = list(self.map_stacked_button.values())[0]
			QTimer.singleShot( 100, lambda: first_pb.click() )

		else:
			Utils.generate_QMsg_critical( self, title="서버 조회 오류", text=json.dumps(_json) 
								if _json else "서버 조회 오류" )


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
# from modules.PyQt.Tabs.HR평가.ui.Ui_tab_HR평가_상급자평가 import Ui_Tab_App as Ui_Tab

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

# from icecream import ic
# import traceback
# from modules.logging_config import get_plugin_logger

# ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
# if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
# 	ic.enable()
# else :
# 	ic.disable()


# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()

# class 상급자평가__for_Tab( QWidget, Utils_QWidget):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent )
		
# 		self.is_Auto_조회_Start = True

# 		self.api_datas:list[dict] =[]
# 		self.dataObj :dict = {}
# 		self.ability_m2m : list[int] = []
# 		self.perform_m2m : list[int] = []
# 		self.sepcial_m2m : list[int] =[]

# 		self.activeWidTable:QWidget|None = None
# 		self.activeAppDatas:list[dict] = []
# 		self.active_PB_Text = ''
# 		self.pbText = ['']		### pbText original

# 		self.차수별_대상자 = {}

# 		self.param = ''		
# 		self.defaultParam = f"page_size=0"

# 		self._init_kwargs(**kwargs)

# 		###
# 		self.url = INFO.URL_HR평가_상급자평가_INFO

# 		self.ui = Ui_Tab()
# 		self.ui.setupUi(self)
# 		self._init_setting()
# 		self.default_button_style_sheet = self.ui.PB_1.styleSheet()

# 		self.triggerConnect()
		
		

# 		self._init_helpPage()

# 		# self._init_AutoStart()
# 		if self.is_Auto_조회_Start:
# 			self._init_AutoStart()

	
# 	def _init_AutoStart(self):
# 		### 자동 조회 BY DEFAULT_parameter
# 		# self.slot_search_for(self.param if self.param else self.defaultParam )
# 		_isOk, _json = APP.API.Send ( INFO.URL_HR평가_상급자평가_INFO, {}, {'request_INFO':True})
# 		if _isOk:				

# 			self.차수별_대상자 :dict[str:list[int]] = _json.get('차수별_대상자')	
# 			self.차수별_유형 :dict[str:str] = _json.get('차수별_유형')		
# 			self.차수별_is_submit : dict[str:list[bool]] = _json.get('차수별_is_submit')	

# 			self._render_buttons_평가(self.차수별_대상자, self.차수별_유형, self.차수별_is_submit )
# 		else:
# 			Utils.generate_QMsg_critical(self )

# 	def _render_buttons_평가(self,  차수별_대상자:dict[str:list[int]], 차수별_유형:dict[str:str], 차수별_is_submit : dict[str:list[bool]]) -> None:
# 		"""
# 		{'result': 'ok', '차수별_대상자': {'1': [450, 449, 379], '2': [517, 468]}}, \n
# 		'차수별_유형': {'0': '개별', '1': '개별', '2': '종합'}
# 		"""
# 		for 차수 in range(1, 6):
# 			getattr ( self.ui,f"PB_{차수}" ).hide()

# 		if len(self.pbText) == 1:
# 			self.pbText = [ getattr ( self.ui,f"PB_{차수}" ).text()  for 차수 in range(1, 6) ]
# 		ic ( 차수별_대상자)
# 		for key, value  in 차수별_대상자.items():
# 			if hasattr( self.ui, f"PB_{key}" ):
# 				ic ( key, value )
# 				pb:QPushButton = getattr( self.ui, f"PB_{key}" )
# 				if len(value) :
# 					ic (key, value )
# 					pb.setText ( self.pbText[int(key)-1] + f"( {len(value)}명 ) - {차수별_유형.get(str(key))}평가 - 미제출자:{차수별_is_submit.get(str(key)).count(False)} 명  ") 
# 					pb.show()
# 					# 😀state 필요함,... https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
# 					pb.clicked.connect ( lambda state, IDs=value, 유형=차수별_유형.get(str(key)), 미제출자=차수별_is_submit.get(str(key)) : self.slot_PB_clicked( IDs, 유형 , 미제출자))			


# 	def _init_setting(self):
# 		self.ui.PB_Submit.setEnabled(False)
# 		self._all_hide_평가_table()
	
# 	def _clearButtonsStyleSheet(self):
# 		for 차수 in range(1, 6):
# 			getattr ( self.ui,f"PB_{차수}" ).setStyleSheet ( self.default_button_style_sheet )

# 	def triggerConnect(self):
# 		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))
# 		self.ui.PB_Submit.clicked.connect ( self.slot_PB_Submit)

# 	#### app마다 update 할 것.😄
# 	def run(self):
		
# 		return 

# 	def slot_PB_clicked(self, IDs:list[int], 유형:str , 미제출자:list[bool]) :
# 		self._all_hide_평가_table()
# 		self.ui.PB_Submit.setEnabled ( not all(미제출자))
# 		self.active_PB_Text = self.sender().text()

# 		self.wid_btn =  self.sender() 
# 		차수 = int( self.sender().objectName().split('_')[1] )
# 		self._clearButtonsStyleSheet()
# 		self._render_activate( self.sender() )

# 		param = f"?ids={ ','.join( [str(id) for id in IDs ] ) }&page_size=0"
# 		_isOk1, _json = APP.API.getlist( INFO.URL_HR평가_상급자평가_DB + param )
# 		_isOk2, _db_field = APP.API.getlist( INFO.URL_DB_Field_상급자평가_개별 if 유형 == '개별' else INFO.URL_DB_Field_상급자평가_종합 )

# 		if _isOk1 and _isOk2 :
# 			self.activeAppDatas = _json
# 			self.active_db_field = _db_field
# 			if 유형 == '개별':		
# 				self.activeWidTable = self.ui.wid_Table_Pyungga_gaebul
# 				self.activeWidTable._update_data(
# 				api_data=_json, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 				url = self.url, #INFO.URL_HR평가_평가결과_DB,
# 				**self._update_db_fields(_db_field, _json),
# 				)	
			
# 			if 유형 == '종합':			
# 				self.activeWidTable = self.ui.wid_Table_Pyungga_Jonghab
# 				self.activeWidTable._update_data(
# 				api_data=_json, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 				url = INFO.URL_HR평가_평가결과_DB,
# 				**self._update_db_fields(_db_field, _json),
# 				)	
# 			self.activeWidTable.show()
# 			self.activeWidTable.signal_refresh.connect ( self.slot_pb_click_animation)

# 		else:
# 			Utils.generate_QMsg_critical(self )

# 	def _update_db_fields(self, _db_fields:dict, app_datas:list[dict]):
# 		_db_fields['table_config']['no_Edit_rows'] = [ idx for idx, obj in enumerate(app_datas) if obj.get('is_submit')]
# 		_db_fields['table_config']['cell_Menus'] = {} if all( [obj.get('is_submit') for obj in app_datas ] ) else _db_fields['table_config']['cell_Menus']
# 		return _db_fields


# 	def slot_pb_click_animation(self):
# 		self.activeWidTable.signal_refresh.disconnect ( self.slot_pb_click_animation)
# 		self.wid_btn.click()

# 	def _all_hide_평가_table(self):
# 		self.ui.wid_Table_Pyungga_gaebul.hide()
# 		self.ui.wid_Table_Pyungga_Jonghab.hide()

# 	@pyqtSlot()
# 	def slot_PB_Submit(self):
# 		dlg_res_button =  Utils.generate_QMsg_question(self, title="제출확인", text= f"\n\n {self.active_PB_Text } 에 대한 \n평가완료를 하시겠읍니까? \n")
# 		if dlg_res_button == QMessageBox.StandardButton.Ok :
# 			IDs = [ obj.get('id') for obj in self.activeAppDatas ]
# 			threadingTargets = [ {'url':INFO.URL_HR평가_평가결과_DB , 'dataObj':{ 'id': ID}, 'sendData':{'is_submit':True}} for ID in IDs ]
# 			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )

# 			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
# 			if all(result):
# 				Utils.generate_QMsg_Information ( self, title='제출확인', text = f"\n\n {self.active_PB_Text } 에 대한 \n평가완료 되었읍니다. \n" )
# 				for obj in self.activeAppDatas:
# 					obj['is_submit'] = True
# 				self.activeWidTable._update_data( api_data= self.activeAppDatas , **self._update_db_fields(self.active_db_field, self.activeAppDatas ) )
# 				self._init_AutoStart()
				
# 			else:
# 				Utils.generate_QMsg_critical(self)


# 	@pyqtSlot(int)
# 	def slot_add_m2m(self, m2m_field:str, m2m_id:int):

# 		if hasattr( self, m2m_field ) and m2m_id not in getattr( self, m2m_field ):
# 			m2m:list[int] = copy.deepcopy ( getattr( self, m2m_field ) )
# 			m2m.append ( m2m_id)
# 			_isOK, _json = APP.API.Send ( self.url, self.dataObj, { m2m_field : m2m  })
# 			if _isOK:
# 				setattr( self, m2m_field, m2m )
# 			else:
# 				Utils.generate_QMsg_critical(self)

# 	@pyqtSlot(int)
# 	def slot_del_m2m(self, m2m_field:str, m2m_id:int):
	
# 		if hasattr( self, m2m_field ) and m2m_id not in getattr( self, m2m_field ):
# 			m2m:list[int] = copy.deepcopy ( getattr( self, m2m_field ) )
# 			m2m.remove ( m2m_id)
# 			_isOK, _json = APP.API.Send ( self.url, self.dataObj, { m2m_field : m2m  })
# 			if _isOK:
# 				setattr( self, m2m_field, m2m )
# 			else:
# 				Utils.generate_QMsg_critical(self)

# 	@pyqtSlot(str)
# 	def slot_search_for(self, param:str) :
# 		"""
# 		결론적으로 main 함수임.
# 		Wid_Search_for에서 query param를 받아서, api get list 후,
# 		table에 _update함.	
# 		"""
# 		self.loading_start_animation()	

# 		self.param = param 
		
# 		url = self.url + '?' + param

# 		###😀 GUI FREEZE 방지 ㅜㅜ;;
# 		pool = QThreadPool.globalInstance()
# 		self.work = Worker(url)
# 		self.work.signal_worker_finished.signal.connect ( self.table_update )
# 		pool.start( self.work )



# 	@pyqtSlot(bool, bool, object)
# 	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
# 		if not _isOk:
# 			self._disconnect_signal (self.work.signal_worker_finished)
# 			self.loading_stop_animation()
# 			Utils.generate_QMsg_critical(self)
# 			return 

# 		self.api_datas = api_datas
# 		if len(api_datas) > 0 :
# 			self.dataObj : dict = api_datas[0]
# 			self.ability_m2m =self.dataObj.get('ability_m2m', [] )
# 			self.perform_m2m = self.dataObj.get('perform_m2m',[] )
# 			self.special_m2m = self.dataObj.get('special_m2m',[] )

# 		# param = f"?ids={ ','.join( [str(id) for id in api_datas[0].get('ability_m2m',[] ) ] ) }&page_size=0"
# 		# _isOk, _json = APP.API.getlist( INFO.URL_HR평가_역량_평가_DB + param )
# 		# if _isOk:

# 		# else:
# 		# 	Utils.generate_QMsg_critical(self )

# 		# param = f"?ids={ ','.join( [str(id) for id in api_datas[0].get('perform_m2m',[] ) ] ) }&page_size=0"
# 		# _isOk, _json = APP.API.getlist( INFO.URL_HR평가_성과_평가_DB + param )
# 		# if _isOk:

# 		# else:
# 		# 	Utils.generate_QMsg_critical(self )

# 		# param = f"?ids={ ','.join( [str(id) for id in api_datas[0].get('special_m2m',[] ) ] ) }&page_size=0"
# 		# _isOk, _json = APP.API.getlist( INFO.URL_HR평가_성과_평가_DB + param )
# 		# if _isOk:

# 		# else:
# 		# 	Utils.generate_QMsg_critical(self )


# 		# if is_Pagenation :
# 		# 	search_result_info:dict = copy.deepcopy(api_datas)
# 		# 	self.api_datas = search_result_info.pop('results')
# 		# 	self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
# 		# else:
# 		# 	self.api_datas = api_datas
# 		# 	self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
# 		# if len(self.api_datas) == 0 :
# 		# 	self.api_datas = self._generate_default_api_datas()

# 		# self.ui.Wid_Table._update_data(
# 		# 	api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 		# 	url = self.url,
# 		# 	**self.db_fields,
# 		# 	# table_header = 
# 		# )	
# 		self._disconnect_signal (self.work.signal_worker_finished)
# 		self.loading_stop_animation()


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