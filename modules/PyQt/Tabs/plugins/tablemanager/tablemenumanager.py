from __future__ import annotations  ### SyntaxError: from __future__ imports must occur at the beginning of the file
from typing import Optional, TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from local_db.models import Table_Config
import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import concurrent.futures

import pathlib
import typing
import copy
import json


from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model, TableModelBuilder
# from modules.PyQt.compoent_v2.table.Base_Table_Delegate import Base_Table_Delegate
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu


from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer

# from modules.PyQt.Tabs.생산지시서.dialog.list_edit.dlg_판금처선택 import 판금처선택다이얼로그

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger	# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class TableMenuManager:
	"""테이블 메뉴 관리를 담당하는 클래스"""

	def __init__(self, handler=None):
		self.handler = handler
		self.menu_actions = {}
		
	def set_handler(self, widget):
		"""부모 위젯 설정"""
		self.handler = widget
		
	def register_menu_action(self, action_name, callback):
		"""메뉴 액션 등록"""
		self.menu_actions[action_name] = callback
		
	def handle_menu(self, msg):
		"""메뉴 처리"""
		action = msg.get('action')
		if action in self.menu_actions:
			self.menu_actions[action](msg)
		else:
			logger.error(f"미등록 메뉴 액션: {action}")