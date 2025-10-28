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

from modules.PyQt.Tabs.HR평가.tables.Wid_table_역량평가 import Wid_table_역량평가
from modules.PyQt.Tabs.HR평가.tables.Wid_table_성과평가 import Wid_table_성과평가
from modules.PyQt.Tabs.HR평가.tables.Wid_table_특별평가 import Wid_table_특별평가

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

DEFAULT_VIEW = '역량평가'

URL_평가설정_COPY_CREATE = '평가설정_copy_create'

PB_SUBMIT_TEXT = {
	'제출완료': '제출 완료되었읍니다.',
	'제출가능': '제출 가능',
	'제출취소': '제출 취소',
}

class 본인평가__for_stacked_Table( Base_Stacked_Table ):
	default_view_name = DEFAULT_VIEW
	map_api_datas = {
		'역량평가': [],
		'성과평가': [],
		'특별평가': [],
	}

	def init_ui(self):
		self.map_table_name = {
			'역량평가': Wid_table_역량평가(self),
			'성과평가': Wid_table_성과평가(self),
			'특별평가': Wid_table_특별평가(self),
		}
		self.add_Widgets(self.map_table_name)

		self.map_table_name['성과평가'].data_changed.connect(lambda: self.parent().on_check_submit_enable())
		self.map_table_name['특별평가'].data_changed.connect(lambda: self.parent().on_check_submit_enable())

	def set_api_datas(self, api_datas:dict):
		self.api_datas = api_datas
		self.평가체계_dict = api_datas['평가체계_data']
		for k, v in self.map_api_datas.items():
			세부_api_datas:list[dict] = api_datas[f"{k}_fk"][f"{k}_api_datas"]	
			self.map_api_datas[k] = 세부_api_datas
			self.map_table_name[k].set_api_datas(세부_api_datas, self.평가체계_dict)


	def get_api_datas(self ) -> dict[str:list[dict]]:
		for k, wid in self.map_table_name.items():
			self.map_api_datas[k] = wid.get_api_datas()
		return self.map_api_datas
	

	def set_url(self, url:str):
		self.url = url
		for k, v in self.map_table_name.items():
			v.set_url(url)

	def get_가중치_합_flag(self) -> list[bool]:
		### 미제출시, 가중치 합 체크
		all_가중치_합_flag:list[bool]=[]
		for k, wid in self.map_table_name.items():
			wid : Union[Wid_table_역량평가, Wid_table_성과평가, Wid_table_특별평가]
			if hasattr(wid, '가중치_합_flag') :
				all_가중치_합_flag.append(wid.가중치_합_flag)
		return all_가중치_합_flag


class 본인평가__for_Tab( BaseTab ):
	""" 본인평가 ( 여기서는 기본으로 개별평가 이므로, 개별평가를 의미함 , 단 호환성을 위해 이름 그대로 유지함 )"""
	api_data_changed = pyqtSignal(dict)
	
	is_no_config_initial = True		### table config 없음
	is_auto_api_query = True
	
	default_view_name = DEFAULT_VIEW
	api_datas = {}
	map_api_datas = {
		'역량평가': [],
		'성과평가': [],
		'특별평가': [],
	}

	is_external_exec = False
	평가체계_fk:Optional[int] = None

	def create_ui(self):
		logger.debug(f"create_ui : self._ui_initialized : {hasattr(self, '_ui_initialized')}")
		if hasattr(self, '_ui_initialized') and self._ui_initialized:
			logger.debug(f"create_ui : {self._ui_initialized}")
			return
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 본인평가__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		
		self._ui_initialized = True
		


	def custom_ui(self):
		#### h_search 기존 widgets 삭제
		self.clear_layout(self.ui.h_search)
		
		##### stacked_table 버튼 추가
		from modules.PyQt.compoent_v2.custom_상속.custom_PB import HR평가_Stacked_PB
		self.PB_역량평가 = HR평가_Stacked_PB()
		self.PB_역량평가.setText('역량평가')
		self.PB_역량평가.clicked.connect( lambda: self.on_stacked_button_clicked('역량평가') )
		self.ui.h_search.addWidget(self.PB_역량평가)

		self.PB_성과평가 = HR평가_Stacked_PB()
		self.PB_성과평가.setText('성과평가')
		self.PB_성과평가.clicked.connect( lambda: self.on_stacked_button_clicked('성과평가') )
		self.ui.h_search.addWidget(self.PB_성과평가)

		self.PB_특별평가 = HR평가_Stacked_PB()
		self.PB_특별평가.setText('특별평가')
		self.PB_특별평가.clicked.connect( lambda: self.on_stacked_button_clicked('특별평가') )
		self.ui.h_search.addWidget(self.PB_특별평가)
		#### 
		self.ui.h_search.addStretch()
		self.PB_Refresh = QPushButton()
		self.PB_Refresh.setText('새로고침')
		self.PB_Refresh.clicked.connect(self.on_refresh)
		self.ui.h_search.addWidget(self.PB_Refresh)
		self.ui.h_search.addSpacing(16*3)
		### 임시저장 버튼	
		self.PB_Save = QPushButton()
		self.PB_Save.setText('임시저장')
		self.PB_Save.clicked.connect(self.on_save)
		self.ui.h_search.addWidget(self.PB_Save)
		self.ui.h_search.addSpacing(16*3)

		self.PB_Submit = QPushButton()
		self.PB_Submit.setText('제출')
		self.PB_Submit.setEnabled(False)
		self.PB_Submit.clicked.connect(self.on_submit)
		self.ui.h_search.addWidget(self.PB_Submit)
		
		self.map_stacked_button = {
			'역량평가': self.PB_역량평가,
			'성과평가': self.PB_성과평가,
			'특별평가': self.PB_특별평가,
		}

	def on_refresh(self):
		### 새로고침
		if hasattr(self, 'is_external_exec') and self.is_external_exec:
			self._fetch_start()
		else:
			self.run()

	def on_save(self):
		### 임시저장
		self.map_api_datas = self.stacked_table.get_api_datas()
		param = f"?action=임시저장&평가체계_fk={self.평가체계_fk}"
		url = f"{self.url}{param}".replace('//', '/')
		_isok, _json = APP.API.Send_json(  url, dataObj={'id':-1}, sendData=self.map_api_datas)
		if _isok:
			Utils.generate_QMsg_Information(self, title="임시저장 완료", text="정상적으로 임시저장되었읍니다.", autoClose=1000)
			self.hanle_api_datas(_json)
		else:
			Utils.generate_QMsg_critical(self, title="임시저장 실패", text=json.dumps(_json))


	def on_submit(self):
		pb_text = self.PB_Submit.text()

		if pb_text == PB_SUBMIT_TEXT['제출완료']:
			return

		elif pb_text == PB_SUBMIT_TEXT['제출취소']:
			### admin 인 경우 제출 취소 가능하게 설정함
			if INFO.USERID == 1:
				url = f"{INFO.URI}HR평가/평가체계_DB/{self.평가체계_fk}/action_제출취소"
				_isok, _json = APP.API.getlist(url)
				if _isok:
					Utils.generate_QMsg_Information(self, title="제출 취소", text="정상적으로 제출 취소되었읍니다.", autoClose=1000)
					self.hanle_api_datas(_json)
				else:
					Utils.generate_QMsg_critical(self, title="제출 취소 실패", text=json.dumps(_json))

			else:
				Utils.generate_QMsg_critical(self, title="제출 취소 실패", text="관리자가 아닙니다.")
			return 

		elif pb_text == PB_SUBMIT_TEXT['제출가능']:
			### 제출
			self.map_api_datas = self.stacked_table.get_api_datas()
			_text = ''
			for k, v in self.map_api_datas.items():
				if k == '역량평가':
					평균 = sum([item.get('평가점수') for item in v ] ) /len(v) 
					_text += f"{k} : {len(v)} 항목 : 평균 {float(평균):.2f}<br>"
				else:
					평균 = sum([ item.get('가중치')*item.get('평가점수')/100 for item in v ])
					_text += f"{k} : {len(v)} 항목 : 평균 {float(평균):.2f}<br>"

			_text += f"<br><br> 제출 하시겠습니까?<br> (평가가 완료됩니다.)<br>"

			if Utils.QMsg_question( self, title="제출 확인", text=_text):	
				### 제출 로직
				param = f"?action=제출&평가체계_fk={self.평가체계_fk}"
				url = f"{self.url}{param}".replace('//', '/')
				_isok, _json = APP.API.Send_json(  url, dataObj={'id':-1}, sendData=self.map_api_datas)
				if _isok:
					Utils.generate_QMsg_Information(self, title="제출 완료", text="정상적으로 제출되었읍니다.", autoClose=1000)
					self.hanle_api_datas(_json)

				else:
					Utils.generate_QMsg_critical(self, title="제출 실패", text=json.dumps(_json))

	def on_stacked_button_clicked(self, view_name:str):
		logger.debug(f"on_stacked_button_clicked : {view_name}")
		self.stacked_table.setCurrentWidget(view_name)
		for k, wid_pb in self.map_stacked_button.items():
			if k != view_name:
				wid_pb.set_released()				
			else:
				wid_pb.set_pressed()


	def on_check_submit_enable(self):
		""" submit 버튼 활성화 여부 체크 : 활성화 조건 
		1. 각 역량평가_fk, 성과평가_fk, 특별평가_fk 가 is_submit 가 Flase 인 경우
		2. 가중치 합이 100 이어야 함.

		비활성화시, 
		1 . 제출된 경우는 : text 변경 (제출 완료) 
		2. 제출 안된 경우 : 현행대로 (제출)
		"""
		#### 비활성화 check
		#### 1. 제출 여부
		is_submit_flag = self.api_datas['평가체계_data']['is_submit']
		if is_submit_flag:
			if INFO.USERID == 1:
				self.PB_Submit.setText(PB_SUBMIT_TEXT['제출취소'])
				self.PB_Submit.setEnabled(True)
				self.PB_Save.setEnabled(True)
				return 
			else:
				self.PB_Submit.setText(PB_SUBMIT_TEXT['제출완료'])
				self.PB_Submit.setEnabled(False )
				self.PB_Save.setEnabled(False)	
				#### 각 wid에 			
				return 
		else:
			self.PB_Submit.setText(PB_SUBMIT_TEXT['제출가능'])
			self.PB_Save.setEnabled(True)
			### 미제출시, 가중치 합 체크
			is_all_가중치_합_flag = all(self.stacked_table.get_가중치_합_flag())
			self.PB_Submit.setEnabled(is_all_가중치_합_flag)


	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)


	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_datas_changed(self, api_datas:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_datas_changed : {len(api_datas)}")


	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		logger.debug(f" api_datas : {self.api_datas}")
		if hasattr(self, 'selected_rows'):
			self.selected_rows = selected_rows

	def run_by_(self,  url:str, param:str, is_external_exec:bool=False, external_data:dict=None):
		""" class 외부에서 호출 가능."""
		self.is_external_exec = is_external_exec
		self.url = url
		if self.is_external_exec:
			self.external_url = url
			self.external_param = param

			self._fetch_start()

		else:
			self.internal_url = url
			self.internal_param = param
			self._fetch_start()


		# if external_data:
		# 	converted_external_data = self.conversion_external_data(external_data)
		# 	self.hanle_api_datas(converted_external_data)
		# else:
		# 	param = f"?{param}".replace('//', '/').replace('??', '?')
		# 	url = f"{url}{param}".replace('//', '/')
		# 	QTimer.singleShot( 100, lambda: self.on_fetch_start(url))
	
	def _fetch_start(self):
		if self.is_external_exec:
			url = self.external_url
			param = self.external_param
		else:
			url = self.internal_url
			param = self.internal_param
		param = f"?{param}".replace('//', '/').replace('??', '?')
		url = f"{url}{param}".replace('//', '/')
		QTimer.singleShot( 100, lambda: self.on_fetch_start(url))

	def conversion_external_data(self, external_data:dict):
		""" 외부 데이터를 내부 데이터로 변환 """
		copyed_external_data = copy.deepcopy(external_data)
		### 1. 외부 데이터 추출
		역량평가_api_datas = external_data['역량평가_fk']['역량평가_api_datas']
		성과평가_api_datas = external_data['성과평가_fk']['성과평가_api_datas']
		특별평가_api_datas = external_data['특별평가_fk']['특별평가_api_datas']
		if all ( [ bool(역량평가_api_datas), bool(성과평가_api_datas), bool(특별평가_api_datas) ] ):
			return external_data
		else: 
			피평가자_본인평가:dict = external_data.get('피평가자_본인평가', {})
			### 피평가자_본인평가 에서 역량평가_fk, 성과평가_fk, 특별평가_fk 추출
			역량평가_api_datas = 피평가자_본인평가['역량평가_fk']['역량평가_api_datas']	
			성과평가_api_datas = 피평가자_본인평가['성과평가_fk']['성과평가_api_datas']
			특별평가_api_datas = 피평가자_본인평가['특별평가_fk']['특별평가_api_datas']
			### 역량평가_fk, 성과평가_fk, 특별평가_fk 가 있는 경우 추출
			if all ( [ bool(역량평가_api_datas), bool(성과평가_api_datas), bool(특별평가_api_datas) ] ):
				for api_data in 역량평가_api_datas:
					api_data['id'] = None
					api_data['역량평가_fk'] = external_data['역량평가_fk']['id']
					api_data['평가점수'] = 0					
				for api_data in 성과평가_api_datas:
					api_data['id'] = None
					api_data['성과평가_fk'] = external_data['성과평가_fk']['id']
					api_data['평가점수'] = 0
				for api_data in 특별평가_api_datas:
					api_data['id'] = None
					api_data['특별평가_fk'] = external_data['특별평가_fk']['id']
					api_data['평가점수'] = 0
				copyed_external_data['역량평가_fk']['역량평가_api_datas'] = 역량평가_api_datas
				copyed_external_data['성과평가_fk']['성과평가_api_datas'] = 성과평가_api_datas
				copyed_external_data['특별평가_fk']['특별평가_api_datas'] = 특별평가_api_datas
				return copyed_external_data
			else:
				raise ValueError(f"피평가자_본인평가 에서 역량평가_fk, 성과평가_fk, 특별평가_fk 추출 실패")

	def run(self):		
		# self.url = 'HR평가_V2/세부평가_Api_View/'
		# self.stacked_table.set_url(self.url)
		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query and self.url:
			param = f"?action=본인평가"
			self.run_by_(self.url, param)
			# url = f"{self.url}?{param}".replace('//', '/')
			# QTimer.singleShot( 100, lambda: self.on_fetch_start(url))
			

	def on_fetch_start(self, url:str ):		
		_isok, _json = APP.API.getlist(url)
		logger.debug(f"{url} : on_fetch_start : _json : {_json}")
		if _isok:
			self.hanle_api_datas(_json)
		else:
			Utils.generate_QMsg_critical( self, title="서버 조회 오류", text=json.dumps(_json) 
								if _json else "서버 조회 오류" )
	
	def hanle_api_datas(self, api_datas:dict):
		### 1. self.map_api_datas 업데이트
		self.api_datas = api_datas
		self.평가체계_fk = api_datas['평가체계_data']['id']
		### 2. 테이블 업데이트
		for k, v in self.map_api_datas.items():
			self.map_api_datas[k] = api_datas.get(f"{k}_api_datas", [])
		logger.debug(f"hanle_api_datas : self.map_api_datas : {api_datas}")
		self.stacked_table.set_api_datas(api_datas)
		#### 동작을 시켜서 적용 ( style 등 자동 적용 위해 )
		QTimer.singleShot( 100, lambda: self.map_stacked_button[self.default_view_name].click() )
		QTimer.singleShot( 100, lambda: self.on_check_submit_enable() )
		### 3. parent로  변경 신호 발생
		self.api_data_changed.emit(api_datas)

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
# from modules.PyQt.Tabs.HR평가.ui.Ui_tab_HR평가_설정 import Ui_Tab_App as Ui_Tab

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

# class 설정__for_Tab( QWidget, Utils_QWidget):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent )
		
# 		self.is_Auto_조회_Start = True

# 		self.param = ''		
# 		self.defaultParam = f"page_size=25"

# 		self._init_kwargs(**kwargs)

# 		self.ui = Ui_Tab()
# 		self.ui.setupUi(self)
# 		### wid_search hide
# 		# self.ui.Wid_Search_for.hide()

# 		self.triggerConnect()
		
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


# 	def triggerConnect(self):
# 		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
# 		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
# 		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

# 		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))
# 		self.ui.PB_Crate_Year_Goal.clicked.connect (self.slot_create_year_goal )

# 	#### app마다 update 할 것.😄
# 	def run(self):
		
# 		return 
	
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

# 		if is_Pagenation :
# 			search_result_info:dict = copy.deepcopy(api_datas)
# 			self.api_datas = search_result_info.pop('results')
# 			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
# 		else:
# 			self.api_datas = api_datas
# 			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
# 		if len(self.api_datas) == 0 :
# 			self.api_datas = self._generate_default_api_datas()

# 		self.ui.Wid_Table._update_data(
# 			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 			url = self.url,
# 			**self.db_fields,
# 			# table_header = 
# 		)	
# 		self._disconnect_signal (self.work.signal_worker_finished)
# 		self.loading_stop_animation()

# 	@pyqtSlot()
# 	def slot_create_year_goal (self):		
# 		pass

# 	def _create_year_goal(self, data:dict, wid:QDialog) :

# 		is_ok, _json = APP.API.Send( INFO.URL_HR평가_Create_YEAHR평가L, {}, sendData=data)
# 		year = data.get('year')
# 		if is_ok:
# 			Utils.generate_QMsg_Information(self, title=f' {str(year)}년 목표 db 생성', text='정상적으로 생성되었읍니다.')
# 		else:
# 			Utils.generate_QMsg_critical (self, title=f' {str(year)}년 목표 db 생성 Error', text='확인 후 다시 생성바랍니다.')

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
# from modules.PyQt.Tabs.HR평가.ui.Ui_tab_HR평가_본인평가 import Ui_Tab_App as Ui_Tab

# ###################
# # from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine
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

# class 본인평가__for_Tab( QWidget, Utils_QWidget):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent )
		
# 		self.is_Auto_조회_Start = True

# 		self.api_datas:list[dict] =[]
# 		self.dataObj :dict = {}
# 		self.ability_m2m : list[int] = []
# 		self.perform_m2m : list[int] = []
# 		self.special_m2m : list[int] =[]

# 		self.param = ''		
# 		self.defaultParam = f"page_size=0"

# 		self._init_kwargs(**kwargs)

# 		self.ui = Ui_Tab()
# 		self.ui.setupUi(self)
# 		self._init_setting()
# 		self.default_button_style_sheet = self.ui.PB_Sungka.styleSheet()

# 		self.triggerConnect()
		
		

# 		self._init_helpPage()

# 		# self._init_AutoStart()
# 		if self.is_Auto_조회_Start:
# 			### 자동 조회 BY DEFAULT_parameter
# 			self.slot_search_for(self.param if self.param else self.defaultParam )

# 	def _init_setting(self):		
# 		self._all_hide_평가_table()
	
# 	def _clearButtonsStyleSheet(self):
# 		self.ui.PB_Yoklang.setStyleSheet ( self.default_button_style_sheet )
# 		self.ui.PB_Sungka.setStyleSheet ( self.default_button_style_sheet )
# 		self.ui.PB_Tkbul.setStyleSheet ( self.default_button_style_sheet )

# 	def triggerConnect(self):
# 		# self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))
# 		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

# 		self.ui.PB_Yoklang.clicked.connect( self.slot_PB_Yoklang)
# 		self.ui.PB_Sungka.clicked.connect( self.slot_PB_Sungka)
# 		self.ui.PB_Tkbul.clicked.connect( self.slot_PB_Tkbul)

# 		self.ui.PB_Submit.clicked.connect ( self.slot_PB_Submit )

# 	#### app마다 update 할 것.😄
# 	def run(self):
		
# 		return 

# 	def _all_hide_평가_table(self):
# 		self.ui.wid_Table_Sungka.hide()
# 		self.ui.wid_Table_Yoklang.hide()
# 		self.ui.wid_Table_Tkbul.hide()

# 	@pyqtSlot()
# 	def slot_PB_Submit(self):
# 		def _get_가중치_txt( _평가검증결과:dict[str:dict]) -> str:
# 			"""
# 			 _평가검증결과 = {'역량check': {'항목수': 14, '평균': 3.142857142857143}, 
# 			 				'성과check': {'가중치': 100, '항목수': 2, '평균': 3.75}, 
# 							'특별check': {'가중치': 100, '항목수': 1, '평균': 4.0}}
# 			"""
# 			성과check = _평가검증결과.get('성과check')
# 			특별check = _평가검증결과.get('특별check')
# 			txt = ''
# 			if not 성과check.get('가중치') == 100:
# 				txt += f"성과평가 가중치가 {성과check.get('가중치')} 입니다.\n "
# 			if not 특별check.get('가중치') ==  100:
# 				txt += f"특별평가 가중치가 {특별check.get('가중치')} 입니다.\n "
			
# 			if len(txt) > 0:
# 				txt += "가중치의 합은 100이 되어야 합니다.\n"
# 			return txt

# 		_isOk, _평가검증결과 = APP.API.Send( INFO.URL_HR평가_CHECK_평가점수, {}, {'id':self.dataObj.get('id')})
# 		if _isOk:
# 			txt = _get_가중치_txt (_평가검증결과 )
# 			if  len( txt ) == 0 :
# 				text = ''
# 				for 항목, _valueDict in _평가검증결과.items():
# 					text += f"\n--{str(항목).replace('check','평가')}--\n"
# 					for key, value in _valueDict.items():
# 						text += f"  {key} : {str(value)} \n"

# 				dlg_res_button =  Utils.generate_QMsg_question(self, title="확인", text= text + '\n\n 평가완료를 하시겠읍니까? \n')
# 				if dlg_res_button == QMessageBox.StandardButton.Ok :
# 					is_ok, self.dataObj = APP.API.Send ( self.url, self.dataObj, {'is_submit':True})
# 					if is_ok:
# 						self._db_field['table_config']['no_Edit_cols'] = self._db_field['table_config']['table_header']
# 						self._db_field['table_config']['h_Menus'] = {}
# 						self.active_Wid_Table._update_data( **self._db_field )

# 						self.ui.PB_Submit.setEnabled(False)
# 						self.ui.label_submit.setVisible( True )
# 						self.ui.label_Not_submit.setVisible( False )
# 					else:
# 						Utils.generate_QMsg_critical(self)
# 			else:				
# 				Utils.generate_QMsg_critical ( self, title="평가 재확인 요청", text= txt)
# 		else:
# 			Utils.generate_QMsg_critical(self)
		
# 		return 
		


# 	@pyqtSlot()
# 	def slot_PB_Yoklang(self):
# 		self._clearButtonsStyleSheet()
# 		self._render_activate( self.sender() )
# 		self._all_hide_평가_table()

# 		param = f"?ids={ ','.join( [str(id) for id in self.ability_m2m ] ) }&page_size=0"
# 		_isOk1, _json = APP.API.getlist( INFO.URL_HR평가_역량_평가_DB + param )
# 		_isOk2, _db_field = APP.API.getlist( INFO.URL_DB_Field_역량_평가_DB )
# 		if _isOk1 and _isOk2 :
# 			self.active_Wid_Table = self.ui.wid_Table_Sungka
# 			self._update_Active_Table( _json, INFO.URL_HR평가_역량_평가_DB , _db_field )

# 		else:
# 			Utils.generate_QMsg_critical(self )

# 	@pyqtSlot()
# 	def slot_PB_Sungka(self):
# 		self._clearButtonsStyleSheet()
# 		self._render_activate( self.sender() )
# 		self._all_hide_평가_table()

# 		param = f"?ids={ ','.join( [str(id) for id in self.perform_m2m ] ) }&page_size=0"
# 		_isOk1, _json = APP.API.getlist( INFO.URL_HR평가_성과_평가_DB + param )
# 		_isOk2, _db_field = APP.API.getlist( INFO.URL_DB_Field_성과_평가_DB )
# 		if _isOk1 and _isOk2 :		
# 			self.active_Wid_Table = self.ui.wid_Table_Sungka
# 			self._update_Active_Table( _json, INFO.URL_HR평가_성과_평가_DB, _db_field )
# 			self.active_Wid_Table.signal_new_m2m.connect ( lambda m2m_id: self.slot_add_m2m('perform_m2m',m2m_id ))
# 			self.active_Wid_Table.signal_del_m2m.connect ( lambda m2m_id: self.slot_del_m2m('perform_m2m',m2m_id ))
# 		else:
# 			Utils.generate_QMsg_critical(self )

	
# 	@pyqtSlot()
# 	def slot_PB_Tkbul(self):
# 		self._clearButtonsStyleSheet()
# 		self._render_activate( self.sender() )
# 		self._all_hide_평가_table()

# 		if len(self.special_m2m) :
# 			param = f"?ids={ ','.join( [str(id) for id in self.special_m2m ] ) }&page_size=0"
# 			_isOk1, _json = APP.API.getlist( INFO.URL_HR평가_특별_평가_DB + param )
# 			_isOk2, _db_field = APP.API.getlist( INFO.URL_DB_Field_특별_평가_DB )
# 			if _isOk1 and _isOk2 :		
# 				self.active_Wid_Table = self.ui.wid_Table_Tkbul
# 				self._update_Active_Table( _json, INFO.URL_HR평가_특별_평가_DB, _db_field )
# 				self.active_Wid_Table.signal_new_m2m.connect ( lambda m2m_id: self.slot_add_m2m('special_m2m',m2m_id ))
# 				self.active_Wid_Table.signal_del_m2m.connect ( lambda m2m_id: self.slot_del_m2m('special_m2m',m2m_id ))

# 		else:
# 			self.dataObj.get('special_m2m',[] )
# 			new_Data = {'평가설정_fk': self.dataObj['평가설정_fk'], '등록자_fk': INFO.USERID ,'평가점수': 0 }			
# 			_isOk1, _json_특별 = APP.API.Send(INFO.URL_HR평가_특별_평가_DB, {'id':-1}, new_Data )
# 			if _isOk1 :
# 				_isOk, _json = APP.API.Send( self.url, self.dataObj, {'special_m2m':[ _json.get('id')]})
# 				if not _isOk : 
# 					Utils.generate_QMsg_critical(self )
# 					return
# 				else:
# 					self.dataObj = _json
# 					self.special_m2m = self.dataObj.get('special_m2m',[] )

# 				_isOk2, _db_field = APP.API.getlist( INFO.URL_DB_Field_특별_평가_DB )
# 				if _isOk2:
# 					self.active_Wid_Table = self.ui.wid_Table_Tkbul
# 					self._update_Active_Table( [_json_특별], INFO.URL_HR평가_특별_평가_DB, _db_field )
# 					self.active_Wid_Table.signal_new_m2m.connect ( lambda m2m_id: self.slot_add_m2m('special_m2m',m2m_id ))
# 					self.active_Wid_Table.signal_del_m2m.connect ( lambda m2m_id: self.slot_del_m2m('special_m2m',m2m_id ))
# 				else:
# 					Utils.generate_QMsg_critical(self )
# 			else:
# 				Utils.generate_QMsg_critical(self )

# 	def _update_Active_Table(self, api_data:list[dict], url:str, _db_field:dict ):
# 		if self.dataObj.get('is_submit'):
# 			_db_field['table_config']['no_Edit_cols'] = _db_field['table_config']['table_header']
# 			_db_field['table_config']['h_Menus'] = {}
# 		self._db_field = _db_field	
# 		self.active_Wid_Table._update_data(
# 			api_data=api_data,  ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 			url = url,
# 			**self._db_field,
# 		)
# 		self.active_Wid_Table.show()


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
# 			self.ability_m2m = self.dataObj.get('ability_m2m', [] )
# 			self.perform_m2m = self.dataObj.get('perform_m2m',[] )
# 			self.special_m2m = self.dataObj.get('special_m2m',[] )

# 			self.ui.PB_Submit.setEnabled ( not self.dataObj.get('is_submit') )
# 			self.ui.label_submit.setVisible( self.dataObj.get('is_submit') )
# 			self.ui.label_Not_submit.setVisible( not self.dataObj.get('is_submit') )

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