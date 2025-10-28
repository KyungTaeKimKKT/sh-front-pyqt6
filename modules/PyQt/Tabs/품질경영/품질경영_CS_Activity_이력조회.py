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
from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS_Project_Form 

from modules.PyQt.Tabs.품질경영.tables.Wid_table_품질경영_CS_Activity_이력조회 import Wid_table_품질경영_CS_Activity_이력조회 as Wid_table

from modules.PyQt.Tabs.품질경영.chart.gantt_chart import GanttView

from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
# from modules.PyQt.Tabs.품질경영.품질경영_CS_form import CS_Form as CS_Project_Form
from modules.PyQt.Tabs.품질경영.CS_활동현황_form import CS_활동현황_Form, CS_활동현황_Form_View
from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit
from modules.PyQt.compoent_v2.Wid_label_and_pushbutton import Wid_label_and_pushbutton
from modules.PyQt.compoent_v2.Wid_lineedit_and_pushbutton import Wid_lineedit_and_pushbutton
from modules.PyQt.compoent_v2.widget_manager import WidManager
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly
###################
from modules.utils.api_response_분석 import handle_api_response
from modules.PyQt.Tabs.plugins.BaseTab_Slot_Handler import BaseTab_Slot_Handler

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()



from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS관리__for_stacked_Table, CS관리__for_Tab

DEFAULT_VIEW = '테이블'

class CS_Activity_이력조회__for_stacked_Table(CS관리__for_stacked_Table):
	default_view_name = DEFAULT_VIEW

	def create_table(self):
		return Wid_table(self)




class CS_Activity_이력조회__for_Tab( CS관리__for_Tab ):
	# is_no_config_initial = True		### table config 없음
	skip_generate = [
		'id', 'el_info_fk','등록자_fk', '등록자','등록일', '완료자_fk','완료자','완료일' ,
		'claim_file_수','action_수', 'claim_files_ids', 'claim_files_url',
		'activty_files_ids', 'activty_files_url', 'activty_files_수',
	]
	default_view_name = DEFAULT_VIEW

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = CS_Activity_이력조회__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		self.custom_ui_add_combo_view()

		self.PB_Map_View = QPushButton("지도보기")
		self.ui.h_search.addWidget(self.PB_Map_View)
		self.PB_Map_View.clicked.connect( self.on_map_view )



	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
		self.event_bus.subscribe(f"{self.table_name}:data_deleted", self.on_data_deleted)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_datas_changed(self, api_datas:list[dict]):
		super().on_datas_changed(api_datas)

	def on_data_deleted(self, is_deleted:bool):
		super().on_data_deleted(is_deleted)


	def on_selected_rows(self, selected_rows:list[dict]):
		super().on_selected_rows(selected_rows)









# from PyQt6 import QtCore, QtGui, QtWidgets
# from PyQt6.QtWidgets import *
# from PyQt6.QtCore import *
# from PyQt6.QtGui import *
# from typing import TypeAlias

# import pandas as pd
# import urllib
# from datetime import date, datetime, timedelta
# import copy

# import pathlib
# import openpyxl
# import typing

# import concurrent.futures
# import asyncio
# import time


# from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS관리__for_Tab
# ### 😀😀 user : ui...
# from modules.PyQt.Tabs.품질경영.ui.Ui_tab_품질경영_CS관리 import Ui_Tab_App as Ui_Tab
# ###################
# from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
# from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_activity import Dlg_CS_Activity

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

# class Dialog_조회조건(Dialog_Base_조회조건):
#     def __init__(self, parent, **kwargs):
#         super().__init__(parent, **kwargs)

# class CS_Activity_이력조회__for_Tab( CS관리__for_Tab ):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent, appFullName, **kwargs )

# 		self._init_CS_Activity_이력조회()

# 	def _init_CS_Activity_이력조회(self):
# 		self.ui.PB_New.hide()
# 		self.ui.PB_Edit.hide()
# 		self.ui.PB_Del.hide()
# 		self.ui.PB_Open.hide()
# 		self.ui.PB_Activity.hide()
# 		self.ui.PB_Complete.hide()

# 		### activate push button
# 		self.ui.PB_Activity_View.show()
# 		self.ui.PB_Activity.setDisabled(True)
		

