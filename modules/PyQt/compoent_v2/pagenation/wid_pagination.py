from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import datetime

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
### ui import
from modules.PyQt.compoent_v2.pagenation.Ui_pagination import Ui_wid_pagination

from info import Info_SW as INFO
import modules.user.utils as Utils
from stylesheet import StyleSheet as ST
from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Pagination(QWidget, Qwidget_Utils):
	signal_currentPage_changed = pyqtSignal(str)
	signal_download = pyqtSignal()

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		for key, value in kwargs.items():
			setattr( self, key, value)

		self.ui = Ui_wid_pagination()
		self.ui.setupUi(self)

		self.init_PagenationDict()
		self.prevPageNo = 1
		
		self.user_defined_ui_setting()	
		self.triggerConnect()
		self.hide()
		
	def init_PagenationDict(self)->None:
		self.pagenationDict = {
			'countTotal' : self.ui.label_countTotal, ### 총 건수,
			'countOnPage': self.ui.comboBox_countOnPage, ### pageSize
			'current_Page' : self.ui.comboBox_current_Page,
			'total_Page' : self.ui.label_total_Page,
		}
	
	def user_defined_ui_setting(self):
		self.ui.comboBox_countOnPage.hide()
		self.ui.label_12.hide()
		return
		self.ui.comboBox_countOnPage.clear()
		self.ui.comboBox_countOnPage.addItems(['ALL']+INFO.Combo_table_row_Items)
		self.ui.comboBox_countOnPage.setCurrentIndex(1)	### default 25로
		now = datetime.datetime.now()


	def _update_config(self, **kwargs):
		""" kwargs : \n
			고객사list : list[str],  \n
			구분list :list[str] \n
		"""
		for k, v in kwargs.items():
			setattr( self, k, v)

	def triggerConnect(self):				
		self.ui.comboBox_current_Page.currentTextChanged.connect(lambda: self.signal_currentPage_changed.emit(self.ui.comboBox_current_Page.currentText()) )
		self.ui.PB_DownloadAll.clicked.connect( self.signal_download.emit )
	
	def run(self):
		pass
	
	def _get_page_size(self) -> int:
		return int(self.ui.comboBox_countOnPage.currentText())

	def _update_Pagination(self, isPagenation:bool, **kwargs) ->None:		
		self.ui.comboBox_current_Page.disconnect()
		if isPagenation:
			wid  = self.pagenationDict['current_Page']
			wid.clear()
			wid.addItems ( [str(no) for no in range(1,kwargs.get('total_Page', 1)+1 ) ] )
			for key, value in kwargs.items():
				if key in self.pagenationDict.keys():
					wid = self.pagenationDict[key]
					match key:
						case 'countTotal':
							if isinstance ( wid, QLabel):
								wid.setText(f" {str(value)}건"  )
						case 'countOnPage':
							if isinstance ( wid, QComboBox):
								wid.setCurrentText( str(value) )
						case 'current_Page' :
							if isinstance ( wid, QComboBox):
								wid.setCurrentText( str(value) )
						case 'total_Page' :
							if isinstance ( wid, QLabel):
								wid.setText(f" 전체 { str(value)} Page")
			self.show()

		else :
			wid:QLabel = self.pagenationDict['countTotal']
			wid.setText (f" {str(kwargs.get('countTotal'))}건"  )


		self.ui.comboBox_current_Page.currentTextChanged.connect(lambda: self.signal_currentPage_changed.emit(self.ui.comboBox_current_Page.currentText()) )
