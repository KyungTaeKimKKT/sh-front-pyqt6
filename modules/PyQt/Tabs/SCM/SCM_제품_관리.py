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
from modules.PyQt.Tabs.SCM.ui.Ui_tab_SCM_제품_관리 import Ui_Tab_App as Ui_Tab
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
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class 제품_관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )

		
		self.is_Auto_조회_Start = True
		self.selected_rows:list[dict] = []
		self.판금처_list_dict:list[dict] = []
		self.param = ''		
		self.defaultParam = f"page_size=25"

		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		
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


	def triggerConnect(self):
		self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()))
		###  In-처리 hide
		self.ui.PB_In.hide()
		self.ui.PB_In.clicked.connect(lambda: self.handle_warehouse_action('IN'))
		self.ui.PB_Out.clicked.connect(lambda: self.handle_warehouse_action('OUT'))

		self.ui.pb_info.clicked.connect(lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
		self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))

		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_In.setEnabled(len(select_list) > 0))
		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Out.setEnabled(len(select_list) > 0))
		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: setattr(self, 'selected_rows', select_list))
	

	def _get_sendData(self, rowDict:dict, status:str) -> dict:
		sendData = {}
		sendData['상태'] = status
		sendData['처리시간'] = datetime.now()
		sendData['처리자'] = INFO.USERID
		return sendData

	@pyqtSlot(str)
	def handle_warehouse_action(self, action: str):
		"""Handle warehouse IN/OUT actions."""
		action_text = action.upper()
		dlg_res_button = Utils.generate_QMsg_question(
			self, 
			title=f"협력업체 {self.ui.comboBox_SCM_Company.currentText()} {action_text} 처리", 
			text=f" {action_text} 처리 건수 : {len(self.selected_rows)} \n "
		)
		if dlg_res_button == QMessageBox.StandardButton.Ok:
			try:
				threadingTargets = [
					{
						'url': self.url,
						'dataObj': {'id': rowDict['id']},
						'sendData': self._get_sendData(rowDict, action)
					}
					for rowDict in self.selected_rows
				]
				futures = Utils._concurrent_Job(APP.API.Send, threadingTargets)
				result = [future.result()[0] for index, future in futures.items()]
				if all(result):
					Utils.generate_QMsg_Information(
						self, 
						title=f'{action_text} 처리', 
						text=f'😀😀😀 {action_text} 처리 완료 되었읍니다. \n', 
						autoClose=2000
					)
				else:
					Utils.generate_QMsg_critical(self)
			except Exception as e:
				ic(e)
				Utils.generate_QMsg_critical(self)

	# @pyqtSlot()
	# def slot_Wh_In (self):
	# 	""" talble 에서 select row를 해서 mrp 돌림"""
		
	# 	dlg_res_button =  Utils.generate_QMsg_question(self, title="HI 제품창고 입고 처리", text=f" 입고처리 건수 : {len(self.selected_rows)} \n ")
	# 	if dlg_res_button == QMessageBox.StandardButton.Ok  :
	# 		### 이송 목록 전송
	# 		### server에서 일괄절으로 처리함	
	# 		try:
	# 			threadingTargets = [ {'url':self.url, 
	# 					  			'dataObj':{ 'id': rowDict['id']}, 
	# 								'sendData': self._get_sendData(rowDict, 'IN') } 
	# 								for rowDict in self.selected_rows  ]
	# 			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
	# 			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
	# 			if all(result):
	# 				Utils.generate_QMsg_Information(self, title='입고처리', text='😀😀😀 입고처리 완료 되었읍니다. \n', autoClose= 2000 )
	# 			else:
	# 				Utils.generate_QMsg_critical(self)
	# 		except Exception as e:
	# 			ic (e)
	# 			Utils.generate_QMsg_critical(self)


	# @pyqtSlot()
	# def slot_Wh_Out (self):
	# 	""" talble 에서 selectd_row를 out 처리함"""
		
	# 	dlg_res_button = Utils.generate_QMsg_question(self, title=f"협력업체 {self.ui.comboBox_SCM_Company.currentText()} Out 처리", text=f" Out 처리 건수 : {len(self.selected_rows)} \n ")
	# 	if dlg_res_button == QMessageBox.StandardButton.Ok:
	# 		### 이송 목록 전송
	# 		### server에서 일괄절으로 처리함	
	# 		try:
	# 			threadingTargets = [{'url': self.url, 
	# 					  			'dataObj': {'id': rowDict['id']}, 
	# 								'sendData': self._get_sendData(rowDict, 'OUT') } 
	# 								for rowDict in self.selected_rows]
	# 			futures = Utils._concurrent_Job(APP.API.Send, threadingTargets)
	# 			result = [future.result()[0] for index, future in futures.items()]  ### 정상이면 [True, True, True] 형태
	# 			if all(result):
	# 				Utils.generate_QMsg_Information(self, title='Out 처리', text='😀😀😀 Out 처리 완료 되었읍니다. \n', autoClose=2000)
	# 			else:
	# 				Utils.generate_QMsg_critical(self)
	# 		except Exception as e:
	# 			ic(e)
	# 			Utils.generate_QMsg_critical(self)


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
		for _obj in threadingTargets:


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