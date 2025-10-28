from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime
import concurrent.futures

import pathlib
import typing
import copy
import json

from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate


from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Delegate_디자인관리(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	### 😀 override
	def user_defined_creatorEditor_설정(self, widget, **kwargs):

		match kwargs.get('key'):
			case '고객사':
				widget = QComboBox(kwargs['parent'] )
				widget.addItems (self.고객사list if hasattr(self, '고객사list') else [] )
			case '구분' :
				widget = QComboBox(kwargs['parent'] )
				widget.addItems ( self.구분list if hasattr(self, '구분list') else [])			
			case '접수디자이너':
				widget = QComboBox(kwargs['parent'])
				widget.addItems (  [ user['user_성명'] for user in INFO.ALL_USER if user['id'] in self.접수디자이너list ] if hasattr(self, '접수디자이너list') else [] )
			# case '완료디자이너':
			# 	widget = QComboBox(kwargs['parent'])
			# 	widget.addItems (  [ user['user_성명'] for user in INFO.ALL_USER if user['id'] in self.접수디자이너list ] if hasattr(self, '접수디자이너list') else [] )
			case '완료요청일':
				# widget = QDateTimeEdit(kwargs['parent'])
				widget: QDateTimeEdit
				widget.setMinimumDateTime ( QDateTime.currentDateTime() )
			

		return widget

	def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex, **kwargs) -> None:
		match kwargs.get('key'):
			case '고객사':
				if isinstance( editor, QComboBox ):
					editor.setCurrentText( kwargs.get('value'))				
			case '구분' :
				if isinstance( editor, QComboBox ):
					editor.setCurrentText( kwargs.get('value'))				

