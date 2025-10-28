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
from modules.PyQt.Tabs.생산_하이.ui.Ui_tab_생산_하이_생산완료 import Ui_Tab_App as Ui_Tab
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

class 생산완료__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		self._init_api_get()

		
		self.is_Auto_조회_Start = True
		self.job_running_obj = {}
		self.생산실적_fks = []
		self.selected_rows = []
		self.창고_list = []
		self.param = ''		
		self.defaultParam = f"warehouse_ready=True&page_size=25"

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

		# self._init_AutoStart()
		# self.url = INFO.URL_생산계획_공정상세 + 'get_merged_processes/'
		if hasattr(self, 'is_Auto_조회_Start') and self.is_Auto_조회_Start:
			self.slot_search_for(self.param if self.param else self.defaultParam )

		# 창고DB 조회
		_isOk, _json = APP.API.getlist( INFO.URL_재고관리_창고DB +INFO.PARAM_NO_PAGE)
		if _isOk:
			self.창고_list = _json	
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
		self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()))
		self.ui.PB_Save.clicked.connect(lambda: self.slot_save())
		self.ui.pb_info.clicked.connect(lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
		self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))

		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Save.setEnabled(len(select_list) > 0))
		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: setattr(self, 'selected_rows', select_list))
		
	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	

	def _get_selected_row_생산지시서_ID(self) -> int:
		# 선택된 행 정보 가져오기
		return self.ui.Wid_Table.view_selected_row()

	def _get_param(self) ->str:
		searchtDict = {
			'div' : self.ui.lineEdit_Div,
			'name' : self.ui.lineEdit_APP,
			'user_pks' : self.ui.lineEdit_User,
			'is_Active' : self.ui.checkBox_isActive,
			'is_Run' : self.ui.checkBox_isRun,
			'page_size' : self.ui.comboBox_pageSize,
		}
		option_enabled = self.ui.checkBox_options.isChecked()
	
		query_params = ''
		for (key, _wid ) in searchtDict.items():
			from modules.PyQt.User.object_value import Object_Get_Value
			value = Object_Get_Value(_wid).get()

			if isinstance(value, str) and len(value) == 0 : continue
			if not option_enabled and key in ['is_Active', 'is_Run']: continue				

			if key == 'page_size' and str(value).upper() == 'ALL': 
				query_params += f"{key}=0"+'&'
			else:
				query_params += f"{key}={value}" + '&'

		return query_params if query_params[-1] != '&' else query_params[:-1]   ### 마지막 &는 제외


	@pyqtSlot()
	def slot_save(self):
		def _update(rowDict) -> dict:
			rowDict['is_HI_complte'] = True
			rowDict['완료일시'] = datetime.now()
			rowDict['완료자'] = INFO.USERID
			rowDict['창고_fk'] = Utils.get_Obj_From_ListDict_by_subDict( self.창고_list, {'창고명': 'HI제품창고'} )['id']
			return rowDict
		
		dlg_res_button =  Utils.generate_QMsg_question(self, title="HI->HI 제품창고 이송", text=f" 이송 건수 : {len(self.selected_rows)} \n 이송 목록 : {self.selected_rows}")
		if dlg_res_button == QMessageBox.StandardButton.Ok  :
			### 이송 목록 전송
			### server에서 일괄절으로 처리함	
			try:
				threadingTargets = [ {'url':INFO.URL_생산계획_제품완료, 'dataObj':{ 'id': -1}, 'sendData': _update(rowDict) } for rowDict in self.selected_rows  ]
				futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
				result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
				if all(result):
					Utils.generate_QMsg_Information(self, title='생산완료', text='😀😀😀 생산완료가 되었읍니다. \n')
				else:
					Utils.generate_QMsg_critical(self)
			except Exception as e:
				ic (e)
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
			self.ui.wid_pagination._update_Pagination( is_Pagenation,  countTotal=len(api_datas) )
		
		if len(self.api_datas) == 0 :
			self.api_datas = self._generate_default_api_datas()
		

		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self.work.signal_worker_finished.signal.disconnect( self.table_update )
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
	
