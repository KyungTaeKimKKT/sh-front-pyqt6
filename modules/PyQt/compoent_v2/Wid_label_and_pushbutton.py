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

class Wid_label_and_pushbutton(QWidget):
	lb_textChanged = pyqtSignal(str)
	def __init__(self, parent:QWidget, data:any=None, is_readonly:bool=False, **kwargs):
		super().__init__(parent)
		self.data = data
		self.lb_text = self.data or kwargs.get('default_text', '선택 필수입니다.')
		
		self.hlayout = QHBoxLayout(self)
		self.label = QLabel(self)
		self.label.setText(self.lb_text)
		self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self._update_label_style()
		self.is_readonly = is_readonly
		self.button_dict:dict[str, Any] = {}
		self.kwargs = kwargs
		for key, value in kwargs.items():
			setattr(self, key, value)

		####
		self.button = QPushButton(self)
		self.button.setText(self.button_dict.get('text', ''))
		if 'clicked' in self.button_dict :
			callable_func = self.button_dict.get('clicked', lambda: None)
			if callable(callable_func):
				self.button.clicked.connect(callable_func)
			else:
				raise ValueError(f"clicked is not callable in {self.button_dict}")
		####
		self.hlayout.addWidget(self.label, 1)
		self.hlayout.addWidget(self.button, 0)
		self.setLayout(self.hlayout)

		if self.is_readonly:
			self.button.setEnabled(False)

	def _update_label_style(self):
		if self.data:
			self.label.setStyleSheet("font-size:16px;color:yellow;background-color:black;")
		else:
			self.label.setStyleSheet("font-size:16px;color:red;background-color:black;")
	
	def set_label_text(self, text:str):
		self.label.setText(text)
		self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.label.setStyleSheet("font-size:16px;color:yellow;background-color:black;")
		self.lb_textChanged.emit(text)

	def get_value(self):		
		return self.label.text()
	
	def set_value(self, value:str):
		self.data = value
		self.label.setText(value)
		self._update_label_style()