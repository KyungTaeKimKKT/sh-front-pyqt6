from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import copy

import pathlib
import openpyxl
import typing

import concurrent.futures
import asyncio
import time
import base64
import os

### 😀😀 user : ui...
from modules.PyQt.Tabs.영업수주.ui.Ui_tab_영업수주_관리 import Ui_Tab_App as Ui_Tab
###################
from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine
from modules.PyQt.User.validator import YearMonth_Validator
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dlg_자재내역_to_의장_Mapping(QDialog):
	def __init__(self, parent, api_data:list[dict]=[],**kwargs):
		super().__init__(parent)
		self.api_data = api_data

		self.current_subject = None
		self.current_sub_subject = None
		self.completed_steps = set()

		self.UI()

		if self.api_data:					
			self.wid_table._update_data(api_data=self.api_data, **self._get_default_tableConfig())
		# 웹소켓 연결 설정
		# self.ws_manager = WS_Thread_Sync(self, url=INFO.WS_영업수주_등록_ApiProcess)
		# self.ws_manager.signal_receive_message.connect(self.update_message)
		# self.ws_manager.start()

	def closeEvent(self, event):
		"""위젯이 닫힐 때 호출되는 이벤트 핸들러"""
		# 웹소켓 연결 종료
		if hasattr(self, 'ws_manager') and self.ws_manager:
			self.ws_manager.close()
		super().closeEvent(event)

	def _get_default_tableConfig(self) -> dict:
		fields_model = {
			'자재내역': 'charfield',
			'의장_fk': 'integerfield',
			'의장': 'charfield',
		}
		table_header = list(fields_model.keys())
		self.db_fields = {
				'fields_model':fields_model,
				'fields_append':{},
				'fields_delete':{},				
				'table_config':{
					'table_header':table_header,
					'no_Edit_cols' : ['의장_fk'],
					'hidden_columns' : [],
				}
			}
		return self.db_fields

	def UI(self):
		self.setMinimumSize(600, 600)
		self.setWindowTitle('자재내역을 의장으로 매핑!!!')
		layout = QVBoxLayout()
		from modules.PyQt.Tabs.영업수주.tables.table_자재내역_to_의장 import Wid_Table_for_영업수주_자재내역_To_의장_Mapping
		self.wid_table = Wid_Table_for_영업수주_자재내역_To_의장_Mapping(self)
		self.setStyleSheet("background-color: #f0f0f0;")
		layout.addWidget(self.wid_table)
		self.wid_table.show()
		self.setLayout(layout)
		self.show()
	
