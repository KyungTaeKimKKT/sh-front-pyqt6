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
from modules.PyQt.Tabs.재고관리.ui.Ui_tab_재고관리_제품_관리 import Ui_Tab_App as Ui_Tab
###################

from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class 제품_관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		self._init_api_get()

		
		self.is_Auto_조회_Start = True
		self.selected_rows:list[dict] = []
		self.판금처_list_dict:list[dict] = []
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
		
		if hasattr(self, 'url_db_fields') and self.url_db_fields :
			self._get_DB_Field(self.url_db_fields  )	
			#### db filed에 update 하기 위해서 여기 위치	
			_isOk, _json= APP.API.getlist( INFO.URL_생산관리_판금처DB + INFO.PARAM_NO_PAGE )
			if _isOk:
				ic( _json )
				self.판금처_list_dict = _json
				self.db_fields['table_config']['판금처_list_dict'] = _json				
			else:
				Utils.generate_QMsg_critical(self)

					
		

		self._init_helpPage()

		if self.is_Auto_조회_Start :
			self.slot_search_for(self.param if self.param else self.defaultParam )



	def _init_api_get(self) :
		threadingTargets = [ INFO.URL_생산계획_DDAY+INFO.PARAM_NO_PAGE, INFO.URL_생산계획_ProductionLine+INFO.PARAM_NO_PAGE, INFO.URL_일일보고_휴일+INFO.PARAM_NO_PAGE ]
		threadingTargets = [{'url':url }  for url in threadingTargets ]

		futures = Utils._concurrent_Job( APP.API.getlist , threadingTargets )
		result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		if all(result):
			self.dday_obj:dict[str:int] = futures[0].result()[1][0]
			self.producionLine:list[dict] = futures[1].result()[1]
			self.휴일_list: list[dict] = futures[2].result()[1]

			# for _json in [  future.result()[1] for index,future in futures.items()  ]:


		else:
			Utils.generate_QMsg_critical(self)

	def triggerConnect(self):
		self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()))
		self.ui.PB_In.clicked.connect(lambda: self.slot_Wh_In())
		self.ui.PB_Out.clicked.connect(lambda: self.slot_Wh_Out())

		self.ui.pb_info.clicked.connect(lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
		self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))

		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_In.setEnabled(len(select_list) > 0))
		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Out.setEnabled(len(select_list) > 0))
		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: setattr(self, 'selected_rows', select_list))
	

	@pyqtSlot()
	def slot_Wh_In (self):
		""" talble 에서 select row를 해서 mrp 돌림"""

		def _get_sendData(rowDict:dict) -> dict:
			sendData = {}
			sendData['상태'] = 'IN'
			sendData['처리시간'] = datetime.now()
			sendData['처리자'] = INFO.USERID
			return sendData
		
		dlg_res_button =  Utils.generate_QMsg_question(self, title="HI 제품창고 입고 처리", text=f" 입고처리 건수 : {len(self.selected_rows)} \n ")
		if dlg_res_button == QMessageBox.StandardButton.Ok  :
			### 이송 목록 전송
			### server에서 일괄절으로 처리함	
			try:
				threadingTargets = [ {'url':self.url, 'dataObj':{ 'id': rowDict['id']}, 'sendData': _get_sendData(rowDict) } for rowDict in self.selected_rows  ]
				futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
				result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
				if all(result):
					Utils.generate_QMsg_Information(self, title='입고처리', text='😀😀😀 입고처리 완료 되었읍니다. \n', autoClose= 2000 )
				else:
					Utils.generate_QMsg_critical(self)
			except Exception as e:
				ic (e)
				Utils.generate_QMsg_critical(self)


	@pyqtSlot()
	def slot_Wh_Out (self):
		""" talble 에서 selectd_row를 out 처리함"""

		def _get_sendData(rowDict:dict) -> dict:
			sendData = {}
			sendData['상태'] = 'OUT'
			sendData['처리시간'] = datetime.now()
			sendData['처리자'] = INFO.USERID
			sendData['출고처_fk'] = Utils.get_Obj_From_ListDict_by_subDict(self.판금처_list_dict, {'판금처': rowDict['생관_출고처']})['id']
			ic(sendData)
			return sendData
		
		dlg_res_button = Utils.generate_QMsg_question(self, title="HI 제품창고 출고 처리", text=f" 출고처리 건수 : {len(self.selected_rows)} \n ")
		if dlg_res_button == QMessageBox.StandardButton.Ok:
			### 이송 목록 전송
			### server에서 일괄절으로 처리함	
			try:
				threadingTargets = [{'url': self.url, 'dataObj': {'id': rowDict['id']}, 'sendData': _get_sendData(rowDict)} for rowDict in self.selected_rows]
				futures = Utils._concurrent_Job(APP.API.Send, threadingTargets)
				result = [future.result()[0] for index, future in futures.items()]  ### 정상이면 [True, True, True] 형태
				if all(result):
					Utils.generate_QMsg_Information(self, title='출고처리', text='😀😀😀 출고처리 완료 되었읍니다. \n', autoClose=2000)
				else:
					Utils.generate_QMsg_critical(self)
			except Exception as e:
				ic(e)
				Utils.generate_QMsg_critical(self)


	@pyqtSlot()
	def slot_PB_Save (self):
		""" 생산계획반영  btn clicked """
		# self.ui.Wid_Tabel은 modules/PyQt/Tabs/생산관리/tables/table_생산공정일정표.py 임

		# currentDatas = self.ui.Wid_Table.save_current_by_공정상세Set()		
		
		currentDatas = self.ui.Wid_Table.save_current()		
		if currentDatas :
			ic ( currentDatas[0])
		else:
			ic('No currentData')
			return 

		url = INFO.URL_생산계획_공정상세
		threadingTargets = [{'url':url , 'dataObj' : {'id':_dict.pop('id', -1)}, 'sendData': _dict }  for _dict in  currentDatas]

		futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
		result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		if all(result):
			Utils.generate_QMsg_Information ( self, title='생산계획 반영 성공',  text=f" {len(currentDatas)} 건수 변경되었읍니다.")
			# self.slot_search_for(self.param if self.param else self.defaultParam )
		else:
			Utils.generate_QMsg_critical(self)


	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	

	def _get_selected_row_생산지시서_ID(self) -> int:
		# 선택된 행 정보 가져오기
		return self.ui.Wid_Table.view_selected_row()


	@pyqtSlot()
	def slot_Saengji_View(self):
		from modules.PyQt.Tabs.생산지시서.dialog.dlg_생산지시서_form import Dialog_생산지시서_Form

		생산지시_fk_id = self._get_selected_row_생산지시서_ID()
		ic ( 생산지시_fk_id )
		if 생산지시_fk_id > 0 :
			_isOk, _json = APP.API.getObj( INFO.URL_생산지시서_관리, id= 생산지시_fk_id)
			if _isOk:
				dlg =Dialog_생산지시서_Form(self, url=INFO.URL_생산지시서_관리,  dataObj = _json , is_Edit=False )
			else:
				Utils.generate_QMsg_critical(self)



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
		ic ( is_Pagenation, _isOk, api_datas )
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

		return 


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