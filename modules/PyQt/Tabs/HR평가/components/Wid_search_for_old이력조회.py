from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import datetime

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
### ui import
from modules.PyQt.Tabs.HR평가.ui.Ui_search_compenet_old이력조회 import Ui_Search

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
	signal_download = pyqtSignal(str)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		for key, value in kwargs.items():
			setattr( self, key, value)

		self.ui = Ui_Search()
		self.ui.setupUi(self)
		# self.ui.frame_Date.setVisible( self.ui.checkBox_Date.isChecked() )
		# self.ui.frame_Surang.setVisible( self.ui.checkBox_EL_Su.isChecked() )
		self.ui.frame_Pagenation.hide()
		self.ui.frame_7.hide()

		self.init_InputDict()
		self.init_PagenationDict()
		self.prevPageNo = 1
		
		self.user_defined_ui_setting()	
		self.triggerConnect()

		
	def init_InputDict(self) ->None:
		self.inputDict = {
			'평가제목_fk' : self.ui.comboBox,	### db는 integer filed
			'page_size' : self.ui.comboBox_pageSize,
		}
	
	def init_PagenationDict(self)->None:
		self.pagenationDict = {
			'countTotal' : self.ui.label_countTotal, ### 총 건수,
			'countOnPage': self.ui.comboBox_countOnPage, ### pageSize
			'current_Page' : self.ui.comboBox_current_Page,
			'total_Page' : self.ui.label_total_Page,
		}
	
	def user_defined_ui_setting(self):
		self.ui.comboBox_pageSize.addItems(['ALL'])
		self.ui.comboBox_pageSize.setCurrentIndex(0)	### default 25로

	def _update_config(self, **kwargs):
		""" kwargs : \n
			평가제목_fk_list : list[str],  \n
		"""
		for k, v in kwargs.items():
			setattr( self, k, v)

		if hasattr( self, '평가제목_fk_list') :
			self.ui.comboBox.addItems( getattr( self, '평가제목_fk_list') )
			self.ui.comboBox_pageSize.setCurrentIndex(0)
		

	def triggerConnect(self):				
		self.ui.PB_Search.clicked.connect (self.slot_PB_search)
		self.trigger_style_inputDict_textChanged()
		# self.ui.checkBox_Date.clicked.connect (lambda: self.ui.frame_Date.setVisible( self.ui.checkBox_Date.isChecked() ) )
		# self.ui.checkBox_EL_Su.clicked.connect (lambda: self.ui.frame_Surang.setVisible( self.ui.checkBox_EL_Su.isChecked() ) )
		self.ui.comboBox_current_Page.currentTextChanged.connect(self.slot_currentPage_changed)

		self.ui.PB_DownloadAll.clicked.connect(lambda:self.signal_download.emit(self.param if hasattr(self, 'param') else 'page_size=0') )
	
	def run(self):
		pass

	@pyqtSlot()
	def slot_PB_search(self):
		self.ui.PB_Search.setEnabled(False)
		self.ui.PB_Search.setStyleSheet('background-color:gray;')

		inputDict =  self._get_value_from_InputDict()
		self.param =  self._get_api_query_params(inputDict)
		self.signal_search.emit(self.param )

	@pyqtSlot()
	def slot_currentPage_changed(self):
		self.ui.comboBox_current_Page.currentTextChanged.disconnect(self.slot_currentPage_changed)
		try:
			pageNo = int (self.ui.comboBox_current_Page.currentText() )
			if self.prevPageNo == pageNo :
				return 
			self.prevPageNo = pageNo
			self.param += f'&page={str(pageNo)}'
			self.signal_search.emit(self.param )
		except:
			pass	


	def _get_api_query_params(self, search_dict:dict) -> str:
		# option_Date_enabled = self.ui.checkBox_Date.isChecked()
		# option_수량_enabled = self.ui.checkBox_EL_Su.isChecked()
	
		query_params = ''
	
		# query_params = '?' ==> parent에서 handling
		for (key, value ) in search_dict.items():
			if isinstance(value, str) and len(value) == 0 : continue
			# if not option_Date_enabled and key in ['시작일', '종료일']: continue				
			# if not option_수량_enabled and key in ['From수량', 'To수량']: continue	

			if key == 'page_size' and str(value).upper() == 'ALL': 
				query_params += f"{key}=0"+'&'
			else:
				if 	str(value).upper() == 'ALL':
					continue
				else:			
					###😀 평가설정_fk=15 형태
					query_params += f"{key}={str(value).split('--')[0]}" + '&'

		return query_params if query_params[-1] != '&' else query_params[:-1]   ### 마지막 &는 제외
	
	
	def _update_Pagination(self, isPagenation:bool, **kwargs) ->None:		
		self.ui.PB_Search.setEnabled(True)
		self.ui.PB_Search.setStyleSheet('background-color:blue;')

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
			self.ui.frame_3.show()

		else :
			wid:QLabel = self.pagenationDict['countTotal']
			wid.setText (f" {str(kwargs.get('countTotal'))}건"  )
			self.ui.frame_3.hide()
			self.ui.frame_7.hide()

		self.ui.comboBox_current_Page.currentTextChanged.connect(self.slot_currentPage_changed)
		self.ui.frame_Pagenation.show()