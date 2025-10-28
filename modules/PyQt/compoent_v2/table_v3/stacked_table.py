from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.custom_상속.custom_qstacked import Custom_QStackedWidget 
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table.Wid_table_config_mode import Wid_TableConfigMode

from config import Config as APP
from info import Info_SW as INFO
import modules.user.utils as Utils

import copy, time
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class Base_Stacked_Table( Custom_QStackedWidget, LazyParentAttrMixin ):
# class App설정_개발자__for_stacked_Table( Custom_QStackedWidget, LazyParentAttrMixin ):
	""" name 은 반드시 넣어야 함. 
		default : 'empty',
		table은 'active table', 'config table'
	"""
	ignore_empty = False
	default_widget_name = 'empty'

	def __init__(self, parent:QWidget, **kwargs):
		super().__init__(parent)
		self.start_init_time = time.perf_counter()
		self.lazy_attr_names = ['APP_ID']
		self.lazy_ready_flags = {}
		self.lazy_attr_values = {}
		self.lazy_ws_names = []

		self.event_bus = event_bus
		self.kwargs = kwargs
		self.table_name = None
		
		self.config_mode_selected = False

		self.current_name = self.default_widget_name if self.ignore_empty else 'empty'

		self.map_config_mode = {
			True: 'config table',
			False: 'active table',
		}
		self.init_attributes()
		self.init_ui()

		self.run_lazy_attr()

		if self.ignore_empty:
			self.setCurrentWidget(self.current_name)
	

	def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
		super().on_lazy_attr_ready(attr_name, attr_value)

	def on_all_lazy_attrs_ready(self):		
		try:
			APP_ID = self.lazy_attr_values['APP_ID']
			self.table_name = Utils.get_table_name(APP_ID)
			self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
			if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
				self.url = Utils.get_api_url_from_appDict(self.appDict)
			self.subscribe_gbus()

		except Exception as e:
			logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")


	def subscribe_gbus(self):
		self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.on_api_datas )
		self.event_bus.subscribe( f"{self.table_name}:empty_data", self.on_empty_data )
		# self.event_bus.subscribe( f"{self.table_name}:table_config_mode", self.apply_table_config_mode )

	def unsubscribe_gbus(self):
		try:
			self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.on_api_datas )
			# self.event_bus.unsubscribe( f"{self.table_name}:table_config_mode", self.apply_table_config_mode )
			self.event_bus.unsubscribe( f"{self.table_name}:empty_data", self.on_empty_data )
		except Exception as e:
			logger.error(f"Error unsubscribing from gbus: {e}")


	def on_empty_data(self, is_empty:bool):
		if is_empty:
			self.set_empty_to_current()
		else:
			self.set_active_to_current()

	def on_api_datas(self, api_datas:list[dict]):
		self.api_datas = copy.deepcopy(api_datas)
		self.apply_api_datas(self.api_datas)

	def apply_table_config_mode(self, is_table_config_mode:bool) -> str:
		""" 현재 mode를 반환 ['active table', 'config table']"""
		logger.debug(f"{self.__class__.__name__} : apply_table_config_mode: {is_table_config_mode}")
		if is_table_config_mode:
			self.config_mode_selected = not self.config_mode_selected
		else:
			self.config_mode_selected = False
		logger.debug(f"{self.__class__.__name__} : apply_table_config_mode: {self.config_mode_selected}")
		self.setCurrentWidget(self.map_config_mode[self.config_mode_selected])
		return self.map_config_mode[self.config_mode_selected]
	
	def init_attributes(self):
		for k, v in self.kwargs.items():
			setattr(self, k, v)

	def init_ui(self):
		self.addWidget('active table', self.create_active_table())
			
	def create_active_table(self):
		raise NotImplementedError("create_active_table 메서드를 구현해야 합니다.")

		
	def run(self, **kwargs):
		self.setCurrentWidget('empty')

		return 


	def apply_api_datas(self, datas:Optional[list[dict]]=None):
		logger.debug(f"{self.__class__.__name__} : apply_api_datas: {len(datas)}")
		if datas:
			self.current_name = 'active table'
			self.setCurrentWidget(self.current_name)
		else:
			if self.ignore_empty:
				return
			else:
				self.current_name = 'empty'
				self.setCurrentWidget(self.current_name)

	def set_empty_to_current(self):
		self.current_name = 'empty'
		self.setCurrentWidget(self.current_name)

	def set_active_to_current(self):
		self.current_name = 'active table'
		self.setCurrentWidget(self.current_name)