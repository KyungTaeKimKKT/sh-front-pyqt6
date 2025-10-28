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
from modules.PyQt.Tabs.생산관리.ui.Ui_tab_생산관리_확정Branch import Ui_Tab_App as Ui_Tab
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

class 실적관리_통합공정__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		self._init_api_get()

		
		self.is_Auto_조회_Start = True
		self.job_running_obj = {}
		self.생산실적_fks = []

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
			ui_search_config_dict = {}
			for key in ['고객사list', '구분list']:
				if hasattr( self, key) :
					ic ( getattr( self, key ) )
					ui_search_config_dict[key] = getattr( self, key )

			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
					
		

		self._init_helpPage()

		self._init_AutoStart()

		URL = INFO.URL_생산계획_공정상세 + 'get_merged_processes/'
		_isOk, _json = APP.API.getlist( URL +INFO.PARAM_NO_PAGE)
		if _isOk:
			ic ( _json )
		else:
			Utils.generate_QMsg_critical(self)


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
	
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

		self.ui.PB_Saengji_View.clicked.connect ( self.slot_Saengji_View )

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		### frame_info layout 임
		self.PB_Production_Start = QPushButton('생산투입')
		self.ui.horizontalLayout.addWidget(self.PB_Production_Start)
		self.PB_Production_Start.clicked.connect ( self.slot_PB_Production_Start )
		self.PB_Production_Start.setEnabled(True)

		### frame_info layout 임
		self.PB_BarcodePrint = QPushButton('Barcode출력')
		self.ui.horizontalLayout.addWidget(self.PB_BarcodePrint)
		self.PB_BarcodePrint.clicked.connect ( self.slot_Barcode_Print )
		self.PB_BarcodePrint.setEnabled(False)
		# self.ui.Wid_Table.tableView._enable_Mutl_Selection_Mode()
		# self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_MRP.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))

	@pyqtSlot()
	def slot_PB_Production_Start  (self):
		""" """
		widTable = self.ui.Wid_Table
		_selected_rows:list[int] = widTable.tableView._get_selected_rows()
		if not ( _len := len(_selected_rows) ) == 1 : 
			_title = '투입 선택 오류'
			_text = '복수 투입' if _len else '먼저 투입하고자 하는 job을 선택하세요'
			Utils.generate_QMsg_critical(self, title=_title, text=_text )
			self.job_running_obj = {}
			self.PB_BarcodePrint.setEnabled(False)
			return
		rowNo = _selected_rows[0]
		self.job_running_obj  =  self.api_datas[rowNo]
		self.PB_BarcodePrint.setEnabled(True)

		### 공정상세_fk 는 merged_ids 에서 id임
		# threadingTargets = [ {'url':INFO.URL_생산계획_생산실적, 'dataObj':{'id':-1}, 'sendData': { '공정상세_fk':공정상세_fk, '시작시간':datetime.now().strftime('%Y-%m-%d %H:%M:%S') } } 
		# 			  for 공정상세_fk in self.job_running_obj['merged_ids'] ]

		# futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
		# result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		# if all(result):
		# 	self.생산실적_fks = [ future.result()[1].get('id') for index,future in futures.items() ]
		# 	self.PB_BarcodePrint.setEnabled(True)
		# else:
		# 	self.job_running_obj = {}
		# 	Utils.generate_QMsg_critical(self)

		return 


		url = INFO.URL_생산계획_공정상세
		threadingTargets = [{'url':url , 'dataObj' : {'id':_dict.pop('id', -1)}, 'sendData': _dict }  for _dict in  currentDatas]
		for _obj in threadingTargets:


		futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
		result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		if all(result):
			Utils.generate_QMsg_Information ( self, title='생산계획 반영 성공',  text=f" {len(currentDatas)} 건수 변경되었읍니다.")
			self.slot_search_for(self.param if self.param else self.defaultParam )
		else:
			Utils.generate_QMsg_critical(self)

	@pyqtSlot()
	def slot_Barcode_Print  (self):
		""" Barcode Print """
		if not self.job_running_obj : return 

		_sendData = { '공정코드':'HI' ,'고객사':self.job_running_obj['고객사'] ,'확정Branch_id':self.job_running_obj['확정Branch_fk'],'ProductionLine_id':self.job_running_obj['ProductionLine_fk']}
		ic ( _sendData )
		_isOk, _json = APP.API.Send( INFO.URL_SERIAL_DB, {}, _sendData )
		if _isOk:
			from modules.PyQt.User.barcode.dialog_barcode_generate import Dialog_Barcode_Generate
			_dialogObjData = self.job_running_obj.copy()
			_dialogObjData['수량'] = f"{_json.get('current_count')} / {_json.get('total_count')}"
			dlg = Dialog_Barcode_Generate(self, _data={'serial':_json.get('serial'), 'obj':_dialogObjData })

			ic ( _json )
		else:
			ic ( _json )
			if (errorMsg := _json.get('error')):
				if errorMsg == '해당 확정Branch의 계획수량을 초과하여 시리얼을 발행할 수 없읍니다.':
					Utils.generate_QMsg_critical(self, title="바코드 출력 완료된 상태입니다.", text=errorMsg)
				else:
					Utils.generate_QMsg_critical(self, title="바코드 출력 오류", text=errorMsg)
			else:
				Utils.generate_QMsg_critical(self)

		return 

		# 선택된 모든 행의 고유한 인덱스 가져오기
		rows = set(index.row() for index in self.ui.Wid_Table.tableView.selectedIndexes())
		datas = [ self.api_datas[row]  for row in rows ]
		all_process_fks = [pk for data in datas for pk in data['process_fks']]

		param = f"?시작일=2024-05-01&종료일=2025-03-01&page_size=0"
		_isOk, _json = APP.API.getlist(INFO.URL_일일보고_휴일 + param )
		if _isOk:
			ic ( _json )
		else:
			Utils.generate_QMsg_critical(self)

		param = f"?page_size=0"
		_isOk, _json = APP.API.getlist(INFO.URL_생산계획_DDay + param )
		if _isOk:
			ic ( _json )
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

		# dlg = QDialog(self)
		# dlg.setMinimumSize ( 800, 1000 )
		# vLayout = QVBoxLayout()
		# hlayout = QHBoxLayout()
		# label = QLabel("생산지시서를 발행 하고자 하는 작업지침서를 선택하시기 바랍니다.")
		# label.setStyleSheet("background-color:black;color:yellow;font-weight:bold")
		# hlayout.addWidget(label)
		# PB_Select = QPushButton('Select')
		# hlayout.addWidget(PB_Select)
		# # hlayout.addStretch()
		# vLayout.addLayout(hlayout)

		# wid  = 이력조회__for_Tab(dlg, '작업지침서_이력조회', **Utils.get_Obj_From_ListDict_by_subDict ( INFO.APP_권한, {'div':'작업지침서', 'name':'이력조회'}) )
		# vLayout.addWidget(wid)

		# dlg.setLayout(vLayout)
		
		# dlg.setWindowTitle( "생산지시서 대상 작업지침서 검색")
		# dlg.show()

		# wid.ui.Wid_Table._get_selected_row_Dict()
		# PB_Select.clicked.connect ( lambda : self.slot_Prod_Instruction_target_selected ( dlg, wid.ui.Wid_Table ) )


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
		
		ic ( self.api_datas[0])

		### replace Wid_Table
		# self.ui.verticalLayout.removeWidget( self.ui.Wid_Table)
		# self.ui.Wid_Table.deleteLater()


		# from modules.PyQt.Tabs.생산관리.tables.table_생산공정일정표 import Wid_ProcessSchedule
		# self.ui.Wid_Table = Wid_ProcessSchedule(self, 생산계획list=self.api_datas, dday_obj=self.dday_obj, 공정_구분=self.공정_구분, 휴일list=self.휴일_list , productionLine=self.producionLine)
		# self.ui.verticalLayout.addWidget( self.ui.Wid_Table )

		# self._disconnect_signal (self.work.signal_worker_finished)
		# self.loading_stop_animation()

		# return 


		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()

		###  😀table select에 따라 PB_MRP, ProdPlan enable/disable
		# self.ui.Wid_Table.tableView._enable_Mutl_Selection_Mode()
		# self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_MRP.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))
		# self.ui.Wid_Table.tableView.selectionModel().selectionChanged.connect ( lambda: self.PB_ProdPlan.setEnabled( len(self.ui.Wid_Table.tableView.selectedIndexes()) > 0 ))


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