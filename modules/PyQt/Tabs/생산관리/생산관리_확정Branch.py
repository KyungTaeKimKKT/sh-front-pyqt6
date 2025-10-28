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
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class 확정Branch__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		self._init_api_get()

		
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
		self.PB_Save = QPushButton('생산계획반영')
		self.ui.horizontalLayout.addWidget(self.PB_Save)
		self.PB_Save.clicked.connect ( self.slot_PB_Save)
		self.PB_Save.setEnabled(True)

		### frame_info layout 임
		self.PB_ProdPlan = QPushButton('Reserved')
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
			logger.info(f"생산계획 반영 요청: {_obj}")

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
		

		### replace Wid_Table
		self.ui.verticalLayout.removeWidget( self.ui.Wid_Table)
		self.ui.Wid_Table.deleteLater()

		# dday_json = [{'_HI': -11,
		# 		'_PO': -2,
		# 		'_구매': -15,
		# 		'_생지': -17,
		# 		'_작지': -18,
		# 		'_출하일': 0,
		# 		'_판금': -6,
		# 		'id': 2},
		# 		{'_HI': -10,
		# 		'_PO': -1,
		# 		'_구매': -14,
		# 		'_생지': -16,
		# 		'_작지': -17,
		# 		'_출하일': 0,
		# 		'_판금': -5,
		# 		'id': 1}]

		# dday_obj = dday_json[0]
		self.공정_구분 = {
			'HI': ['하도',],
			'PO': ['분체', 'UHC'],
		}
		# 휴일list= [{'id': 440, '휴일': '2025-03-01', '휴일내용': None},
		# {'id': 439, '휴일': '2025-02-23', '휴일내용': None},
		# {'id': 438, '휴일': '2025-02-22', '휴일내용': None},
		# {'id': 437, '휴일': '2025-02-16', '휴일내용': None},
		# {'id': 435, '휴일': '2025-02-15', '휴일내용': None},
		# {'id': 436, '휴일': '2025-02-09', '휴일내용': None},
		# {'id': 434, '휴일': '2025-02-08', '휴일내용': None},
		# {'id': 433, '휴일': '2025-02-02', '휴일내용': None},
		# {'id': 432, '휴일': '2025-02-01', '휴일내용': None},
		# {'id': 549, '휴일': '2025-01-30', '휴일내용': None},
		# {'id': 548, '휴일': '2025-01-29', '휴일내용': None},
		# {'id': 547, '휴일': '2025-01-28', '휴일내용': None},
		# {'id': 546, '휴일': '2025-01-27', '휴일내용': None},
		# {'id': 431, '휴일': '2025-01-26', '휴일내용': None},
		# {'id': 428, '휴일': '2025-01-25', '휴일내용': None},
		# {'id': 429, '휴일': '2025-01-19', '휴일내용': None},
		# {'id': 427, '휴일': '2025-01-18', '휴일내용': None},
		# {'id': 420, '휴일': '2025-01-12', '휴일내용': None},
		# {'id': 421, '휴일': '2025-01-11', '휴일내용': None},
		# {'id': 419, '휴일': '2025-01-05', '휴일내용': None},
		# {'id': 415, '휴일': '2025-01-04', '휴일내용': None},
		# {'id': 418, '휴일': '2025-01-01', '휴일내용': None},
		# {'id': 332, '휴일': '2024-12-29', '휴일내용': None},
		# {'id': 331, '휴일': '2024-12-28', '휴일내용': None},
		# {'id': 330, '휴일': '2024-12-25', '휴일내용': None},
		# {'id': 329, '휴일': '2024-12-22', '휴일내용': None},
		# {'id': 328, '휴일': '2024-12-21', '휴일내용': None},
		# {'id': 327, '휴일': '2024-12-15', '휴일내용': None},
		# {'id': 326, '휴일': '2024-12-14', '휴일내용': None},
		# {'id': 325, '휴일': '2024-12-08', '휴일내용': None},
		# {'id': 324, '휴일': '2024-12-07', '휴일내용': None},
		# {'id': 323, '휴일': '2024-12-01', '휴일내용': None},
		# {'id': 322, '휴일': '2024-11-30', '휴일내용': None},
		# {'id': 321, '휴일': '2024-11-24', '휴일내용': None},
		# {'id': 320, '휴일': '2024-11-23', '휴일내용': None},
		# {'id': 319, '휴일': '2024-11-17', '휴일내용': None},
		# {'id': 318, '휴일': '2024-11-16', '휴일내용': None},
		# {'id': 317, '휴일': '2024-11-10', '휴일내용': None},
		# {'id': 316, '휴일': '2024-11-09', '휴일내용': None},
		# {'id': 315, '휴일': '2024-11-03', '휴일내용': None},
		# {'id': 314, '휴일': '2024-11-02', '휴일내용': None},
		# {'id': 313, '휴일': '2024-10-27', '휴일내용': None},
		# {'id': 312, '휴일': '2024-10-26', '휴일내용': None},
		# {'id': 311, '휴일': '2024-10-20', '휴일내용': None},
		# {'id': 310, '휴일': '2024-10-19', '휴일내용': None},
		# {'id': 309, '휴일': '2024-10-13', '휴일내용': None},
		# {'id': 308, '휴일': '2024-10-12', '휴일내용': None},
		# {'id': 307, '휴일': '2024-10-09', '휴일내용': None},
		# {'id': 301, '휴일': '2024-10-06', '휴일내용': None},
		# {'id': 300, '휴일': '2024-10-05', '휴일내용': None},
		# {'id': 299, '휴일': '2024-10-03', '휴일내용': None},
		# {'id': 441, '휴일': '2024-10-01', '휴일내용': '국군의날 임시공휴일'},
		# {'id': 295, '휴일': '2024-09-29', '휴일내용': None},
		# {'id': 294, '휴일': '2024-09-28', '휴일내용': None},
		# {'id': 293, '휴일': '2024-09-22', '휴일내용': None},
		# {'id': 292, '휴일': '2024-09-21', '휴일내용': None},
		# {'id': 291, '휴일': '2024-09-18', '휴일내용': None},
		# {'id': 289, '휴일': '2024-09-17', '휴일내용': None},
		# {'id': 288, '휴일': '2024-09-16', '휴일내용': None},
		# {'id': 287, '휴일': '2024-09-15', '휴일내용': None},
		# {'id': 286, '휴일': '2024-09-14', '휴일내용': None},
		# {'id': 285, '휴일': '2024-09-08', '휴일내용': None},
		# {'id': 284, '휴일': '2024-09-07', '휴일내용': None},
		# {'id': 283, '휴일': '2024-09-01', '휴일내용': None},
		# {'id': 282, '휴일': '2024-08-31', '휴일내용': None},
		# {'id': 281, '휴일': '2024-08-25', '휴일내용': None},
		# {'id': 280, '휴일': '2024-08-24', '휴일내용': None},
		# {'id': 279, '휴일': '2024-08-18', '휴일내용': None},
		# {'id': 278, '휴일': '2024-08-17', '휴일내용': None},
		# {'id': 277, '휴일': '2024-08-15', '휴일내용': None},
		# {'id': 272, '휴일': '2024-08-11', '휴일내용': None},
		# {'id': 271, '휴일': '2024-08-10', '휴일내용': None},
		# {'id': 270, '휴일': '2024-08-04', '휴일내용': None},
		# {'id': 269, '휴일': '2024-08-03', '휴일내용': None},
		# {'id': 268, '휴일': '2024-07-28', '휴일내용': None},
		# {'id': 267, '휴일': '2024-07-27', '휴일내용': None},
		# {'id': 266, '휴일': '2024-07-21', '휴일내용': None},
		# {'id': 265, '휴일': '2024-07-20', '휴일내용': None},
		# {'id': 264, '휴일': '2024-07-14', '휴일내용': None},
		# {'id': 263, '휴일': '2024-07-13', '휴일내용': None},
		# {'id': 262, '휴일': '2024-07-07', '휴일내용': None},
		# {'id': 261, '휴일': '2024-07-06', '휴일내용': None},
		# {'id': 260, '휴일': '2024-06-30', '휴일내용': None},
		# {'id': 259, '휴일': '2024-06-29', '휴일내용': None},
		# {'id': 258, '휴일': '2024-06-23', '휴일내용': None},
		# {'id': 257, '휴일': '2024-06-22', '휴일내용': None},
		# {'id': 256, '휴일': '2024-06-16', '휴일내용': None},
		# {'id': 255, '휴일': '2024-06-15', '휴일내용': None},
		# {'id': 254, '휴일': '2024-06-09', '휴일내용': None},
		# {'id': 253, '휴일': '2024-06-08', '휴일내용': None},
		# {'id': 252, '휴일': '2024-06-06', '휴일내용': None},
		# {'id': 251, '휴일': '2024-06-02', '휴일내용': None},
		# {'id': 250, '휴일': '2024-06-01', '휴일내용': None},
		# {'id': 249, '휴일': '2024-05-26', '휴일내용': None},
		# {'id': 248, '휴일': '2024-05-25', '휴일내용': None},
		# {'id': 247, '휴일': '2024-05-19', '휴일내용': None},
		# {'id': 246, '휴일': '2024-05-18', '휴일내용': None},
		# {'id': 245, '휴일': '2024-05-15', '휴일내용': None},
		# {'id': 244, '휴일': '2024-05-12', '휴일내용': None},
		# {'id': 242, '휴일': '2024-05-11', '휴일내용': None},
		# {'id': 241, '휴일': '2024-05-06', '휴일내용': None},
		# {'id': 240, '휴일': '2024-05-05', '휴일내용': None},
		# {'id': 239, '휴일': '2024-05-04', '휴일내용': None}]



		from modules.PyQt.Tabs.생산관리.tables.table_생산공정일정표 import Wid_ProcessSchedule
		self.ui.Wid_Table = Wid_ProcessSchedule(self, 생산계획list=self.api_datas, dday_obj=self.dday_obj, 공정_구분=self.공정_구분, 휴일list=self.휴일_list , productionLine=self.producionLine)
		self.ui.verticalLayout.addWidget( self.ui.Wid_Table )

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