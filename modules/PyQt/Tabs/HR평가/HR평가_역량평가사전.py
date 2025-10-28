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

from modules.PyQt.Tabs.HR평가.tables.Wid_table_HR평가_역량평가사전 import Wid_table_HR평가_역량평가사전 as Wid_table


import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

DEFAULT_VIEW = '테이블'

class 역량평가사전__for_stacked_Table( Base_Stacked_Table ):
	default_view_name = DEFAULT_VIEW
	
	def create_active_table(self ):
		return Wid_table(self)


class 역량평가사전__for_Tab( BaseTab ):
	no_edit_columns_by_coding = ['id', '등록일','등록자_fk'
								]

	edit_mode = 'row' ### 'row' | 'cell' | 'None'
	custom_editor_info = {}
	is_no_config_initial = True		### table config 없음
	
	default_view_name = DEFAULT_VIEW

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 역량평가사전__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		


	def custom_ui(self):
		return 

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



# ### 😀😀 user : ui...

