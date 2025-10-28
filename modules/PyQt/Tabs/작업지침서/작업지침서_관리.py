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

### 😀😀 user : ui...

from modules.PyQt.Tabs.작업지침서.ui.Ui_tab_작업지침서_관리 import Ui_Tab_App as Ui_Tab
###################
from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils

from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

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

class Dialog_조회조건(Dialog_Base_조회조건):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
	        # QSpinBox 최대값 설정
        # for spinbox_name in ['Rev', '수량_From', '수량_To', '의장수_From', '의장수_To']:
        #     spinbox = self.findChild(QSpinBox, spinbox_name)
        #     if spinbox:
        #         spinbox.setMaximum(9999999)

        # # QDateEdit 캘린더 활성화
        # for dateedit_name in ['납기일_From', '납기일_To']:
        #     dateedit = self.findChild(QDateEdit, dateedit_name)
        #     if dateedit:
        #         dateedit.setCalendarPopup(True)



class 관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		
		self.is_Auto_조회_Start = True

		self.param = ''		
		self.defaultParam = f"page_size=25"
		self.기타조회조건 = {}
		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		self._ui_custom()
		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=self.기타조회조건)

		self.triggerConnect()
		
		if hasattr(self, 'url_db_fields')  and self.url_db_fields :
			self._get_DB_Field(self.url_db_fields  )		
			# ic(self.db_fields)
			#### db filed에 update 하기 위해서 여기 위치	

			if hasattr(self, '고객사list'):
				self.ui.comboBox_Gogaek.addItems( ['ALL'] + self.고객사list )
				self.ui.comboBox_Gogaek.setCurrentText('ALL')
			if hasattr(self, '구분list'):	
				self.ui.comboBox_Gubun.addItems( ['ALL'] + self.구분list )
				self.ui.comboBox_Gubun.setCurrentText('ALL')

				
		

		self._init_helpPage()

		if self.is_Auto_조회_Start :
			self.slot_search_for(self.param if self.param else self.defaultParam )

	def _ui_custom(self):
		self.info_title = getattr(self, 'info_title',None) or "관리자를 위한 화면"
		# 기본 날짜 설정
		today = QDate.currentDate()
		self.ui.dateEdit_From.setDate(today)
		self.ui.dateEdit_To.setDate(today)
		self.ui.frame_Period.setVisible(False)

		self.ui.comboBox_pageSize.addItems( ['ALL'] + ['25', '50', '100'] )
		self.ui.comboBox_pageSize.setCurrentText('25')

		self.ui.label_target.setText( self.info_title )

	def triggerConnect(self):
		#### checkBox 체크 여부에 따라 조회조건 설정
		# 체크박스 상태에 따라 frame_Period 보이기/숨기기
		self.ui.checkBox_Jaksung.stateChanged.connect(lambda: self.ui.frame_Period.setVisible(self.ui.checkBox_Jaksung.isChecked()))

		self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()) )
		self.ui.PB_Search_Condition.clicked.connect(  self.slot_search_condition )
		self.ui.PB_Search_Condition.search_conditions_cleared.connect(	lambda: setattr(self,'기타조회조건',{}) )

		self.ui.PB_New.clicked.connect(lambda: self.slot_new() )
		self.ui.PB_Del.clicked.connect(lambda: self.slot_del() )

		self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
		self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

	def _get_param(self):
		param_list = []
		if ( value := self.ui.lineEdit_search.text() ) :
			param_list.append ( f'search={value}' )
		if ( value := self.ui.comboBox_Gogaek.currentText() ) != 'ALL':
			param_list.append ( f'고객사={value}' )
		if ( value := self.ui.comboBox_Gubun.currentText() ) != 'ALL':
			param_list.append ( f'구분={value}' )

		if self.ui.checkBox_Jaksung.isChecked():
			param_list.append ( f'작성일_From={self.ui.dateEdit_From.date().toString("yyyy-MM-dd")}' )
			param_list.append ( f'작성일_To={self.ui.dateEdit_To.date().toString("yyyy-MM-dd")}' )

		if ( value := self.ui.comboBox_pageSize.currentText() ) != 'ALL':
			param_list.append ( f'page_size={value}' )
		else:
			param_list.append ( f'page_size=0' )

		param = '&'.join(param_list)
		return param

	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	
	

	### 조회조건 설정
	@pyqtSlot()
	def slot_search_condition(self):
		검색조건 = {
			'is_valid' : 'QCheckBox',
			'Rev' : 'QSpinBox',
			'수량_From' : 'QSpinBox',
			'수량_To' : 'QSpinBox',
			'의장수_From' : 'QSpinBox',
			'의장수_To' : 'QSpinBox',
			'작성자' : 'QLineEdit',
			'영업담당자' : 'QLineEdit',
			'고객요청사항' : 'QLineEdit',
			'고객성향' : 'QLineEdit',
			'특이사항' : 'QLineEdit',
			'집중점검항목' : 'QLineEdit',
			'검사요청사항' : 'QLineEdit',
			'납기일_From' : 'QDateEdit',
			'납기일_To' : 'QDateEdit',
		}
		default_dict = {
			'is_valid' : True,
			'Rev' : 1,
			'수량_From' : 1,
			'수량_To' : 50,
			'의장수_From' : 1,
			'의장수_To' : 10,
			'납기일_From' : datetime.now().date() + timedelta(days=10),
			'납기일_To' : datetime.now().date() + timedelta(days=30),
		}
		_default_dict = self.기타조회조건 if self.기타조회조건 else default_dict
		dlg = Dialog_조회조건(self, input_dict = 검색조건, default_dict = _default_dict , title = '조회조건 설정')
		dlg.result_signal.connect( self.slot_update_etc_search_condition )


	@pyqtSlot(dict)
	def slot_update_etc_search_condition(self, 기타조회조건:dict):
		self.기타조회조건 = 기타조회조건
		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=기타조회조건)

	@pyqtSlot()
	def slot_new(self):
		pass

	@pyqtSlot()
	def slot_del(self):
		pass	

	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""
		self.loading_start_animation()	

		if self.기타조회조건 :
			ic ( len( self.기타조회조건.keys() ) )
			ic(self.기타조회조건)
			param = param + '&' + '&'.join( [ f'{key}={value}' for key, value in self.기타조회조건.items() ] )

		self.param = param 
		
		url = self.url + '?' + param
		ic(url)

		###😀 GUI FREEZE 방지 ㅜㅜ;;
		pool = QThreadPool.globalInstance()
		self.work = Worker(url)
		self.work.signal_worker_finished.signal.connect ( self.table_update )
		pool.start( self.work )



	@pyqtSlot(bool, bool, object)
	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
		if not _isOk:
			self._disconnect_signal (self.work.signal_worker_finished)
			self.loading_stop_animation()
			Utils.generate_QMsg_critical(self)
			return 

		if is_Pagenation :
			search_result_info:dict = copy.deepcopy(api_datas)
			self.api_datas = search_result_info.pop('results')
			self.ui.wid_pagination._update_Pagination( is_Pagenation, **search_result_info )
		else:
			self.api_datas = api_datas
			self.ui.wid_pagination._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
		if len(self.api_datas) == 0 :
			self.api_datas = self._generate_default_api_datas()

		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()


	def _generate_default_api_datas(self) ->list[dict]:		
		table_header:list[str] = self.db_fields['table_config']['table_header']
		obj = {}
		for header in table_header:
			if header == 'id' : obj[header] = -1
			else:
				match self.fields_model.get(header, '').lower():
					case 'charfield'|'textfield':
						obj[header] = ''
					case 'integerfield'|'floatfield':
						obj[header] = 0
					case 'datetimefield':
						# return QDateTime.currentDateTime().addDays(3)
						obj[header] =  datetime.now()
					case 'datefield':
						# return QDate.currentDate().addDays(3)
						obj[header] =  datetime.now().date()
					case 'timefield':
						# return QTime.currentTime()
						obj[header] = datetime.now().time()
					case _:
						obj[header] = ''
		return [ obj ]