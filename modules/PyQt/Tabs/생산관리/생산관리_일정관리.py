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
from modules.PyQt.Tabs.생산관리.ui.Ui_tab_생산관리_일정관리 import Ui_Tab_App as Ui_Tab
###################

from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
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

class 일정관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		
		self.is_Auto_조회_Start = True

		self.param = ''		
		self.defaultParam = f"page_size=25"

		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		### wid_search hide
		# self.ui.Wid_Search_for.hide()
		###😀 label_target text update
		self.ui.label_target.setText( "관리자를 위한 화면")

		self.triggerConnect()
		
		if hasattr(self, 'url_db_fields'):
			self._get_DB_Field(self.url_db_fields  )		
			ui_search_config_dict = {}
			for key in ['고객사list', '구분list']:
				if hasattr( self, key) :
					ic ( getattr( self, key ) )
					ui_search_config_dict[key] = getattr( self, key )

			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
					
		

		self._init_helpPage()

		self._init_AutoStart()


	def triggerConnect(self):
	
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

		self.ui.PB_Jakji_search.clicked.connect ( self.slot_Jakji_search )

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		### frame_info layout 임
		self.PB_MRP = QPushButton('MRP')
		self.ui.horizontalLayout.addWidget(self.PB_MRP)
		self.PB_MRP.clicked.connect ( self.slot_MRP)
		self.PB_MRP.setEnabled(False)

		### frame_info layout 임
		self.PB_ProdPlan = QPushButton('생산계획')
		self.ui.horizontalLayout.addWidget(self.PB_ProdPlan)
		self.PB_ProdPlan.clicked.connect ( self.slot_ProdPlan)
		self.PB_ProdPlan.setEnabled(False)
		# self.ui.Wid_Table.tableView._enable_Mutl_Selection_Mode()
		# self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_MRP.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))

	@pyqtSlot()
	def slot_ProdPlan (self):
		""" talble 에서 select row를 해서 mrp 돌림"""
		# 선택된 모든 행의 고유한 인덱스 가져오기
		rows = set(index.row() for index in self.ui.Wid_Table.tableView.selectedIndexes())
		datas = [ self.api_datas[row]  for row in rows ]
		# all_process_fks = [pk for data in datas for pk in data['process_fks']]

		param = f"?시작일=2024-05-01&종료일=2025-03-01&page_size=0"
		_isOk, _json = APP.API.getlist(INFO.URL_일일보고_휴일 + param )
		if _isOk:
			ic ( _json )
		else:
			Utils.generate_QMsg_critical(self)

		param = f"?page_size=0"
		_isOk, _json = APP.API.getlist(INFO.URL_생산계획_DDAY + param )
		if _isOk:
			ic ( _json )
		else:
			Utils.generate_QMsg_critical(self)




	@pyqtSlot()
	def slot_MRP (self):
		""" talble 에서 select row를 해서 mrp 돌림"""
		# 선택된 모든 행의 고유한 인덱스 가져오기
		rows = set(index.row() for index in self.ui.Wid_Table.tableView.selectedIndexes())
		datas = [ self.api_datas[row]  for row in rows ]
		all_process_fks = [pk for data in datas for pk in data['process_fks']]

		#### 😀 Process_fks : 즉, HTM_Table
		if len(all_process_fks) > 0:
			param = f"?ids={(',').join( [str(id) for id in all_process_fks] )}&page_size=0"
			is_ok, _json = APP.API.getlist(INFO.URL_생산지시_HTM_Table + param )
			if is_ok:
				ic ( sum ([  obj['수량'] for obj in _json if isinstance(obj['수량'], (int, float))   ]))
				from modules.PyQt.Tabs.구매.dialog.dlg_구매_MRP import PivotTableDialog
				dlg = PivotTableDialog(self, _json)
				dlg.exec()

			else:
				Utils.generate_QMsg_critical(self)


	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	
	@pyqtSlot()
	def slot_Jakji_search(self):
		from modules.PyQt.Tabs.작업지침서.작업지침서_이력조회 import 이력조회__for_Tab

		dlg = QDialog(self)
		dlg.setMinimumSize ( 800, 1000 )
		vLayout = QVBoxLayout()
		hlayout = QHBoxLayout()
		label = QLabel("생산지시서를 발행 하고자 하는 작업지침서를 선택하시기 바랍니다.")
		label.setStyleSheet("background-color:black;color:yellow;font-weight:bold")
		hlayout.addWidget(label)
		PB_Select = QPushButton('Select')
		hlayout.addWidget(PB_Select)
		# hlayout.addStretch()
		vLayout.addLayout(hlayout)

		wid  = 이력조회__for_Tab(dlg, '작업지침서_이력조회', **Utils.get_Obj_From_ListDict_by_subDict ( INFO.APP_권한, {'div':'작업지침서', 'name':'이력조회'}) )
		vLayout.addWidget(wid)

		dlg.setLayout(vLayout)
		
		dlg.setWindowTitle( "생산지시서 대상 작업지침서 검색")
		dlg.show()

		# wid.ui.Wid_Table._get_selected_row_Dict()
		PB_Select.clicked.connect ( lambda : self.slot_Prod_Instruction_target_selected ( dlg, wid.ui.Wid_Table ) )


	@pyqtSlot(QDialog, QWidget)
	def slot_Prod_Instruction_target_selected (self, dlg:QDialog , wid_Table:QWidget ):

		if ( selectObj := wid_Table._get_selected_row_Dict() ):
			dlg.close()
			ic ( selectObj )

			today = datetime.today().date()
			# newObj:dict = copy.deepcopy( selectObj )
			newObj = { 'id':-1, '작성일': today, '작성자':INFO.USERNAME, '납기일' :today+timedelta(days=30), '작성자_fk': INFO.USERID } 

			dlg =Dialog_생산지시서_Form(self, url=self.url,  dataObj = newObj , is_update_By_Jakji=True , 작업지침_obj = selectObj )
			dlg.setWindowTitle (f"생산지시서 작성 : {selectObj['제목']} - Rev : {selectObj['Rev']} 작업지침서")

			dlg.signal_refresh.connect ( lambda:self.slot_search_for(self.param) )
		else:
			Utils.generate_QMsg_critical(self, title="생산지시서 대상 작업지침서 오류",  text='선택된 작업지침서가 없읍니다.')

	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""
		self.loading_start_animation()	

		self.param = param 
		
		url = self.url + '?' + param

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
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
		else:
			self.api_datas = api_datas
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
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

		###  😀table select에 따라 PB_MRP, ProdPlan enable/disable
		self.ui.Wid_Table.tableView._enable_Mutl_Selection_Mode()
		self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_MRP.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))
		self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_ProdPlan.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))


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