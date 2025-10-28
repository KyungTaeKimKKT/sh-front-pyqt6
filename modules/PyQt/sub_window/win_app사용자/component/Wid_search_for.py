from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.sub_window.win_app사용자.ui.Ui_search_compenet import Ui_Search

from info import Info_SW as INFO
import modules.user.utils as Utils
from stylesheet import StyleSheet as ST
from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Search_for(QWidget, Qwidget_Utils):
	signal_search = pyqtSignal(str)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		for key, value in kwargs.items():
			setattr( self, key, value)

		self.ui = Ui_Search()
		self.ui.setupUi(self)

		self.init_InputDict()
		self.user_defined_ui_setting()	
		self.triggerConnect()

		
	def init_InputDict(self) ->None:
		self.inputDict = {
			'search' : self.ui.lineEdit_search,
		}
	
	def user_defined_ui_setting(self):
		return 

	
	def triggerConnect(self):				
		self.ui.PB_Search.clicked.connect (self.slot_PB_search)
		self.trigger_style_inputDict_textChanged()
	
	def run(self):
		pass
		# if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		# self.setupUi(self)
		# self.init_InputDict()
		# self.user_defined_ui_setting()	
		# self.triggerConnect()

	@pyqtSlot()
	def slot_PB_search(self):
		inputDict =  self._get_value_from_InputDict()
		self.signal_search.emit( self._get_api_query_params(inputDict))


	def _get_api_query_params(self, search_dict:dict) -> str:
	
		query_params = ''
		if search_dict:
			# query_params = '?' ==> parent에서 handling
			for (key, value ) in search_dict.items():
				if isinstance(value, str) and len(value) == 0 : continue
				else:
					if key == 'page_size' and str(value).upper() == 'ALL': 
						continue
					else:
						query_params += f"{key}={value}" + '&'
		if len(query_params) == 0 : 
			return ''
		return query_params if query_params[-1] != '&' else query_params[:-1]   ### 마지막 &는 제외
	
