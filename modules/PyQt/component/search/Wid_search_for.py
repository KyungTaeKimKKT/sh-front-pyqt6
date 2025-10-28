from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.component.search.Ui_search_compenet import Ui_Form 
from modules.PyQt.component.search.Ui_search_compenet_망관리DB import Ui_Form as Ui_form_망관리db_search
from modules.PyQt.component.search.Ui_search_compenet_망관리DB_Album import Ui_Form as Ui_form_망관리Album_search

from info import Info_SW as INFO
import modules.user.utils as Utils
from stylesheet import StyleSheet as ST
from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Search_for(QWidget, Ui_Form, Qwidget_Utils):
	signal_search = pyqtSignal(dict, list)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.url = parent.url
		self.pageSize = 25

		for key, value in kwargs.items():
			setattr( self, key, value)
		
	def init_InputDict(self) ->None:
		self.inputDict = {
			'기준' : self.comboBox_Gijun,
			'고객사' : self.comboBox_Gogaek,
			'구분' : self.comboBox_Gubun,
			'From일자' : self.dateEdit_From,
			'To일자' : self.dateEdit_To,
		}
	
	def user_defined_ui_setting(self):
		now = QDate.currentDate()
		self.dateEdit_From.setDate( now.addMonths(-1))
		self.dateEdit_To.setDate( now )
	
	def triggerConnect(self):				
		self.PB_Search.clicked.connect (self.slot_PB_search)
		self.trigger_style_inputDict_textChanged()
	
	def run(self):
		if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		self.setupUi(self)
		self.init_InputDict()
		self.user_defined_ui_setting()	
		self.triggerConnect()

	def slot_PB_search(self):
		if (query_params := self._get_api_query_params( self._get_value_from_InputDict() ) ):
			if self.get_api_Result(query_params) :
				self.signal_search.emit(  self.app_query_result, self.app_DB_data )

	def _get_api_query_params(self, search_dict:dict) -> str:
		self.기준 = search_dict.pop('기준')
		query_params = ''
		if search_dict:
			query_params = '?'
			for (key, value ) in search_dict.items():
				if value == 'All' : continue
				match key:
					case key if '일자' in key:
						query_params += f"{self.기준}_{key}={value}&"
					case _:
						query_params += f"{key}={value}&"
			query_params += f'page_size={self.pageSize}'

		return query_params
	
	def get_api_Result(self, query_params:str) -> bool:
		if self.pageSize :
			is_ok, self.app_query_result = APP.API.getlist(self.url+query_params)
			if is_ok:

				self.app_DB_data = self.app_query_result.get('results')
				del self.app_query_result['results']
			# else:
			# 	User_Toast(self, text='server not connected', style='ERROR')
		else:
			is_ok, self.app_DB_data = self._get_app_DB_data(self.url, query_params)
		return is_ok
	


class Wid_Search_for_망관리(QWidget, Qwidget_Utils):
	signal_search = pyqtSignal(dict, list)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.app_DB_data = []
		self.app_query_result = {}

		self.url = parent.url
		self.pageSize = 25
		self.ui =  Ui_form_망관리db_search()

		for key, value in kwargs.items():
			setattr( self, key, value)
		
	def init_InputDict(self) ->None:
		self.inputDict = {
			'search' : self.ui.lineEdit_Search,
			'고객사' : self.ui.comboBox_Gogaek,
			'의장종류' : self.ui.comboBox_Gubun,
			'From일자' : self.ui.dateEdit_From,
			'To일자' : self.ui.dateEdit_To,
		}

		self.page_InputDict = {
			'countOnPage' : self.ui.comboBox_table_row,
			'current_Page' : self.ui.comboBox_curPage,
		}
	
	def user_defined_ui_setting(self):
		self.ui.frame_Pagenation.hide()
		now = QDate.currentDate()
		self.ui.dateEdit_From.setDate( now.addMonths(-1))
		self.ui.dateEdit_To.setDate( now )

		self.ui.comboBox_Gogaek.clear()
		self.ui.comboBox_Gubun.clear()
		self.ui.comboBox_Gogaek.addItems( INFO.Combo_망관리_고객사_Items )
		self.ui.comboBox_Gubun.addItems( INFO.Combo_망관리_의장종류_Items )

		self.handle_checkBox_Date_enabled()
	
	def display_frame_Date(self, is_show:bool=False):
		self.ui.frame_FromDate.setVisible(is_show)
		self.ui.frame_ToDate.setVisible(is_show)


	def triggerConnect(self):				
		self.ui.PB_Search.clicked.connect (self.slot_PB_search)
		self.ui.comboBox_curPage.currentTextChanged.connect(self.slot_curPage_changed)
		self.ui.comboBox_table_row.currentTextChanged.connect(self.slot_table_row_changed )
		self.ui.checkBox_Date_enabled.clicked.connect(self.handle_checkBox_Date_enabled)
		self.trigger_style_inputDict_textChanged()
	
	def run(self):
		if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		self.ui.setupUi(self)
		self.init_InputDict()
		self.user_defined_ui_setting()	
		self.triggerConnect()

	@pyqtSlot()
	def slot_PB_search(self):
		if (query_params := self._get_api_query_params( self._get_value_from_InputDict() ) ):
			self.get_api_and_signal_emit(query_params)

	@pyqtSlot()
	def slot_curPage_changed(self):
		self.pageNo = self._get_curPage()
		query_params = self.query_params + f'&page={self.pageNo}'

		self.get_api_and_signal_emit(query_params)
	
	@pyqtSlot()
	def slot_table_row_changed (self):
		query_params = self._get_api_query_params(self._get_value_from_InputDict() )
		query_params = query_params + f'&page={ self._get_calcurated_pageNo() }'
		self.get_api_and_signal_emit(query_params)

	@pyqtSlot()
	def handle_checkBox_Date_enabled(self):
		self.display_frame_Date( is_show= self._is_enabled_등록일조회() )

	def get_api_and_signal_emit(self, query_params) :
		if self.get_api_Result(query_params) :
			self._set_PageValue( self.app_query_result )
			self.signal_search.emit(  self.app_query_result, self.app_DB_data )

	def _get_api_query_params(self, search_dict:dict) -> str:
		self.pageSize = self._get_curTableRow()

		self.search = search_dict.pop('search')
		query_params = f'?search={self.search}&'
		if search_dict:
			for (key, value ) in search_dict.items():
				if value == 'All' : continue
				match key:
					case 'From일자'|'To일자':
						if not self._is_enabled_등록일조회(): continue
						else: query_params += f"{key}={value}&"
					case _:
						query_params += f"{key}={value}&"

			query_params += f'page_size={self.pageSize}'

		self.query_params = query_params
		return query_params
	
	def get_api_Result(self, query_params:str) -> bool:
		if self.pageSize :
			is_ok, self.app_query_result = APP.API.getlist(self.url+query_params)
			if is_ok:

				self.app_DB_data = self.app_query_result.get('results')
				del self.app_query_result['results']
			# else:
			# 	User_Toast(self, text='server not connected', style='ERROR')
		else:
			is_ok, self.app_DB_data = self._get_app_DB_data(self.url, query_params)
		return is_ok
	
	def _set_PageValue(self, valueDict:dict):
		"""  valueDict = {'links': {'next': None, 'previous': None}, 'countTotal': 2, 'countOnPage': 25, 'current_Page': 1, 'total_Page': 1} 형태"""
		if not valueDict : return 
		self.ui.comboBox_curPage.currentTextChanged.disconnect()
		self.ui.comboBox_curPage.clear()
		self.ui.comboBox_curPage.addItems ( [ str(i) for i in range(1, valueDict['total_Page'] + 1) ] )


		for key, value in valueDict.items():
			match key:
				case 'countOnPage' | 'current_Page' :
					input :QComboBox = self.page_InputDict[key]
					input.setCurrentText ( str(value) )					
				case  'countTotal' :
					self.ui.label_search_result.setText( f" {value}건" )
				case 'total_Page':
					self.ui.label_totalPage.setText( f"전체 {value} Page")
		self.ui.frame_Pagenation.show()
		self.ui.comboBox_curPage.currentTextChanged.connect(self.slot_curPage_changed)


	def _get_curPage(self) -> int:
		self.prevPageNo = self.pageNo if hasattr(self, 'pageNo') else 1
		return int ( curPage if ( curPage:= self.ui.comboBox_curPage.currentText() ) else 1 )
	
	def _get_curTableRow(self) -> int:
		self.prevPageSize = self.pageSize
		return int( self.ui.comboBox_table_row.currentText() )
	
	def _get_calcurated_pageNo(self) -> int|None:
		if not self.app_query_result : return None
		countOnPage = self.app_query_result.get('countOnPage')
		current_Page = self.app_query_result.get('current_Page')
		start_cnt = (current_Page -1) * countOnPage + 1
		return start_cnt // self._get_curTableRow() + 1
	
	def _is_enabled_등록일조회(self) -> bool:
		return self.ui.checkBox_Date_enabled.isChecked()


class Wid_Search_for_망관리_Album( Wid_Search_for_망관리 ):
	signal_search = pyqtSignal(dict, list)

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		self.ui = Ui_form_망관리Album_search()
		self.albumSizes = {
						'대' : (400,500), 
						'중' : (300, 400),
						'소' : (200, 250) 
							}
		self.tableRow_max = 12

	def init_page_combobox(self):
		self.ui.comboBox_Size.clear()
		self.ui.comboBox_Size.addItems( list(self.albumSizes.keys()) )
		self.ui.comboBox_Size.setCurrentText('중')

		self.ui.comboBox_NoPerRow.clear()
		self.ui.comboBox_NoPerRow.addItems( [str(i) for i in range(2,self.tableRow_max, 2) ] )
		self.ui.comboBox_NoPerRow.setCurrentText('4')

		self.ui.comboBox_table_row.clear()
		self.ui.comboBox_table_row.addItems( ['10','20','30','40','50' ] )
		self.ui.comboBox_table_row.setCurrentText('4')

	def run(self):
		if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		self.ui.setupUi(self)
		self.init_page_combobox()

		self.init_InputDict()
		self.page_InputDict.update({'albumSize' : self.ui.comboBox_Size})

		self.user_defined_ui_setting()	

		self.triggerConnect()

	def triggerConnect(self):
		super().triggerConnect()
		self.ui.comboBox_Size.currentTextChanged.connect( self.signalEmit )
		self.ui.comboBox_NoPerRow.currentTextChanged.connect( self.signalEmit )

	@pyqtSlot()
	def signalEmit(self):
		self.signal_search.emit(  self.app_query_result, self.app_DB_data )

	def _get_AlbumSize(self) -> tuple[str, tuple]:
		""" self.albumSize의 key, value를  return"""
		key =  self.ui.comboBox_Size.currentText()
		return ( key , self.albumSizes[key])
	
	def _get_NoPerRow(self) -> int:
		return int( self.ui.comboBox_NoPerRow.currentText() )
	