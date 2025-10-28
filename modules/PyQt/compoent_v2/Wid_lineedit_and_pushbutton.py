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
import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Wid_lineedit_and_pushbutton(QWidget):
	def __init__(self, parent:QWidget, data:str='', is_readonly:bool=False, button_dict:dict = {}, **kwargs):
		super().__init__(parent)

		self.hlayout = QHBoxLayout(self)
		self.qe = QLineEdit(self)
		self.qe.setText(data)
		####
		self.is_readonly = is_readonly
		self.button_dict = button_dict
		self.kwargs = kwargs
		for key, value in kwargs.items():
			setattr(self, key, value)
		
		self.button = QPushButton(self)
		self.button.setText(self.button_dict.get('text', ''))
		if 'clicked' in self.button_dict :
			callable_func = self.button_dict.get('clicked', lambda: None)
			if callable(callable_func):
				self.button.clicked.connect(callable_func)
			else:
				raise ValueError(f"clicked is not callable in {self.button_dict}")
		####
		self.hlayout.addWidget(self.qe, 1)
		self.hlayout.addWidget(self.button, 0)
		self.setLayout(self.hlayout)

		if self.is_readonly:
			self.button.setEnabled(False)
			self.qe.setEnabled(False)
			self.set_value(self.qe.text())
	
	def set_value(self, text:str):
		self.qe.setText(text)
		self.qe.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.qe.setStyleSheet("font-size:16px;color:yellow;background-color:black;")
		
	def set_qe_placeholder(self, text:str):
		self.qe.setPlaceholderText(text)
		
	def get_value(self):
		return self.qe.text().strip()