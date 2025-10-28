from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from datetime import date, datetime
import copy

### 😀😀 user : ui...
from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table
from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_년간보고 import Wid_table_영업mbo_년간보고 as Wid_table
from modules.PyQt.Tabs.영업mbo.graph.wid_chart_개인별 import Wid_Chart_개인별
###################
from modules.utils.api_response_분석 import handle_api_response
from modules.PyQt.Tabs.plugins.BaseTab_Slot_Handler import BaseTab_Slot_Handler

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class 년간보고_개인별__for_stacked_Table( Base_Stacked_Table ):
	default_view = '그래프'

	def init_ui(self):
		self.mapping_tables = {
			'그래프': Wid_Chart_개인별(self),
			'테이블': Wid_table(self),
		}
		self.add_Widgets(self.mapping_tables )
		if INFO._get_is_table_config_admin():
			self.addWidget('config table', self.create_config_table() )

	def apply_api_datas(self, datas:Optional[list[dict]]=None):
		"""on_api_method에서 호출됨"""
		logger.debug(f"{self.__class__.__name__} : apply_api_datas: {len(datas)}")
		logger.debug(f"{self.__class__.__name__} : apply_api_datas: {self.default_view}")
		if datas:
			self.setCurrentWidget(self.default_view)


class 년간보고_개인별__for_Tab(BaseTab):
	no_edit_columns_by_coding = ['ALL']
	is_no_config_initial = False		### table config 없음
	default_view = '그래프'
	edit_mode = 'None'
	custom_editor_info = {}
	### 지사_구분용
	# set_row_span_list = [
	# 	('구분', ['부서']),
	# 	('부서', [])
	# ]
	### 지사_고객사
	# set_row_span_list = [
	# 	('부서', [])
	# ]
	# ### 개인별
	set_row_span_list = [
		('담당자', []),
		('부서', [])
	]

	url_year = '영업mbo/get-매출년도list/'


	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)


		self.stacked_table = 년간보고_개인별__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })


	def custom_ui(self):
		 # 기존의 wid_search 객체를 삭제
		self.ui.h_search.removeWidget(self.ui.wid_search)
		self.ui.wid_search.setParent(None)
		self.ui.wid_search.deleteLater()		

		self.ui.v_pagination.removeWidget(self.ui.wid_pagination)
		self.ui.wid_pagination.setParent(None)
		self.ui.wid_pagination.deleteLater()
		

		# 년도 선택 삽입
		self.label_year = QLabel('년도 선택 :  ', self)
		self.ui.h_search.addWidget(self.label_year)
		from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_with_fetch, Custom_Combo
		self.combo_selected_year = Custom_Combo_with_fetch(self, url=self.url_year)
		self.combo_selected_year.run(self.url_year)
		self.ui.h_search.addWidget(self.combo_selected_year)

		self.ui.h_search.addSpacing( 16*3 )
		### view 선택 combo 삽입		
		self.label_view = QLabel(' 보기 선택 :  ')
		self.ui.h_search.addWidget(self.label_view)
		self.combo_view = Custom_Combo(self)
		self.combo_view.addItems(['그래프', '테이블'])
		self.combo_view.currentTextChanged.connect(lambda view_name: self.stacked_table.setCurrentWidget(view_name))
		self.combo_view.setCurrentText(self.default_view)
		self.ui.h_search.addWidget(self.combo_view)

		### 조회 버튼 삽입
		self.ui.h_search.addStretch()
		self.pb_query = QPushButton('조회')
		self.ui.h_search.addWidget(self.pb_query)
		self.pb_query.clicked.connect(lambda: self.slot_search_for(self.combo_selected_year.currentText()))


		self.combo_view.hide()
		self.label_view.hide()



	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:datas_changed")


	def on_datas_changed(self, api_datas:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_datas_changed : {len(api_datas)}")
		if api_datas:
			self.combo_view.show()
			self.label_view.show()
		else:
			self.combo_view.hide()
			self.label_view.hide()


	def slot_search_for(self, selected_year:Optional[str]=None) :
		self.param = f"매출_year={selected_year}"
		self.url = '영업mbo/영업MBO_보고서_개인별_apiview/'
		url = self.url + '?' + self.param
		logger.debug(f" slot_search_for: url: {url}")

		self.api_channel_name = f"fetch_{url}"

		self.event_bus.subscribe(self.api_channel_name, self.slot_fetch_finished)
		worker = Api_Fetch_Worker(url)
		worker.start()

	def slot_fetch_finished(self, msg) -> tuple[bool, dict, list[dict]]:
		is_ok, pagination, api_datas = handle_api_response(msg)
		if is_ok:
			logger.debug(f"slot_fetch_finished: {api_datas} 적용됨 ")
			logger.debug(f"{self.__class__.__name__} : slot_fetch_finished : {len(api_datas)}")
			self.event_bus.publish(f"{self.table_name}:datas_changed", copy.deepcopy(api_datas))
		else:
			Utils.generate_QMsg_critical(self, title="서버 조회 오류", msg=msg if msg else "서버 조회 오류")







	# def __init__(self, parent:QWidget,   **kwargs):
	# 	super().__init__( parent)
	# 	self.start_time = 0
	# 	self.event_bus = event_bus
	# 	self.kwargs = kwargs
	# 	self._init_kwargs(**kwargs)

	# 	self.param = ''

	# 	self.url_year = '영업mbo/영업mbo_설정DB/get-매출년도list/'		


	# 	self.wid_chart = Wid_Chart_개인별(self)
	# 	self.wid_table = Wid_table(self)
	# 	self.mapping_widgets = {
	# 		'그래프': self.wid_chart,
	# 		'테이블': self.wid_table,
	# 	}

	# 	self.default_view = '그래프'

	# 	self.init_ui()
	# 	self.init_attributes()

	# 	self.connect_signals()


	# def init_attributes(self):
	# 	self._init_kwargs(**self.kwargs)

	# 	self.table_name = f"{self.div}_{self.name}_appID_{self.id}"
	# 	self.wid_table.setObjectName(self.table_name)
	# 	#### table을 초기 설정 하지 않음. ==> api_datas로 초기 설정 함.
	# 	self.wid_table.set_is_no_config_initial(True)



	# def init_ui(self):
	# 	super().init_ui()
	# 	# # 기존의 wid_search 객체를 삭제
	# 	self.ui.h_search.removeWidget(self.ui.wid_search)
	# 	self.ui.wid_search.setParent(None)
	# 	self.ui.wid_search.deleteLater()		

	# 	self.ui.v_pagination.removeWidget(self.ui.wid_pagination)
	# 	self.ui.wid_pagination.setParent(None)
	# 	self.ui.wid_pagination.deleteLater()
		

	# 	# 년도 선택 삽입
	# 	self.label_year = QLabel('년도 선택 :  ', self)
	# 	self.ui.h_search.addWidget(self.label_year)
	# 	from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_with_fetch, Custom_Combo
	# 	self.combo_selected_year = Custom_Combo_with_fetch(self, url=self.url_year)
	# 	self.combo_selected_year.run(self.url_year)
	# 	self.ui.h_search.addWidget(self.combo_selected_year)

	# 	self.ui.h_search.addStretch()
	# 	### view 선택 combo 삽입
	# 	self.label_view = QLabel(' 보기 선택 :  ')
	# 	self.ui.h_search.addWidget(self.label_view)
	# 	self.combo_view = Custom_Combo(self)
	# 	self.combo_view.addItems(['그래프', '테이블'])
	# 	self.ui.h_search.addWidget(self.combo_view)
	# 	self.combo_view.setCurrentText(self.default_view)

	# 	### 조회 버튼 삽입
	# 	self.ui.h_search.addStretch()
	# 	self.pb_query = QPushButton('조회')
	# 	self.ui.h_search.addWidget(self.pb_query)

	# 	## stacked widget 삽입
	# 	self.wid_stacked = Custom_QStackedWidget(self)
	# 	self.wid_stacked.add_Widgets(self.mapping_widgets)
	# 	self.wid_stacked.setCurrentWidget('empty')
	# 	#### v_table layout에  stacked widget 삽입
	# 	self.ui.v_table.addWidget(self.wid_stacked)

	# 	self.combo_view.hide()
	# 	self.label_view.hide()

	# def connect_signals(self):
	# 	""" 일반적인 baseTab 이 아니라서 완전 override함. """
	# 	self.pb_query.clicked.connect(lambda: self.slot_search_for(self.combo_selected_year.currentText()))

	# 	self.combo_view.currentTextChanged.connect(
	# 		lambda view_name: self.wid_stacked.setCurrentWidget(view_name)
	# 	)
	# 	# self.ui.wid_select_year.selected_year.connect(self.slot_search_for)

	# #### app마다 update 할 것.😄
	# def run(self):
	# 	self.init_attributes()
	# 	self.wid_table.run()
	# 	self.wid_chart.run()

	# 	self.wid_table.set_row_span_list = [
	# 		('담당자', ['부서']),
	# 		('부서', [])
	# 	]

	# 	self.url = '영업mbo/영업MBO_보고서_개인별_apiview/'

	# def slot_search_for(self, selected_year:Optional[str]=None) :
	# 	"""
	# 	결론적으로 main 함수임.
	# 	Wid_Search_for에서 query param를 받아서, api get list 후,
	# 	table에 _update함.	
	# 	"""		
	# 	self.start_time = time.time()
	# 	self.param = f"매출_year={selected_year}"
	# 	url = self.url + '?' + self.param
	# 	logger.debug(f" slot_search_for: url: {url}")

	# 	self.event_bus.subscribe(f"fetch_{url}", self.slot_fetch_finished)
	# 	worker = Api_Fetch_Worker(url)
	# 	worker.start()

	# 	# API 요청 후 페이지 파라미터 제거하여 self.param에 저장
	# 	# if param and 'page=' in param:
	# 	# 	parts = param.split('&')
	# 	# 	parts = [p for p in parts if not p.startswith('page=')]
	# 	# 	self.param = '&'.join(parts)

		
	# def slot_fetch_finished(self, msg):
	# 	is_ok, pagination, api_datas = handle_api_response(msg)
	# 	if is_ok:
	# 		if api_datas:
	# 			self.label_view.show()
	# 			self.combo_view.show()
	# 			self.wid_table.apply_api_datas(api_datas)
	# 			self.wid_chart.apply_api_datas(api_datas)
	# 			self.wid_stacked.setCurrentWidget( self.combo_view.currentText())
	# 		else:
	# 			self.label_view.hide()
	# 			self.combo_view.hide()
	# 			self.wid_stacked.setCurrentWidget('empty')
	# 		logger.debug(f"slot_fetch_finished: {len(api_datas)} 적용됨 ")
	# 	else:
	# 		logger.error(f"slot_fetch_finished: {api_datas}")
	# 	# self.ui.wid_pagination.update_page_info(pagination)

	# 	self.end_time = time.time()
	# 	logger.debug(f"slot_fetch_finished: { int((self.end_time - self.start_time) * 1000) } msec")








	


