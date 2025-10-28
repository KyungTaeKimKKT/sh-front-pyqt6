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
from modules.PyQt.Tabs.serial.ui.Ui_serial_관리 import Ui_Tab_App as Ui_Tab
###################
from modules.PyQt.Tabs.생산지시서.dialog.dlg_생산지시서_form import Dialog_생산지시서_Form
from modules.PyQt.Tabs.작업지침서.dialog.dlg_작업지침서_form import Dialog_작업지침서_Form
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
from modules.PyQt.User.object_value import Object_Get_Value

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

class 관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,  **kwargs):
		super().__init__(parent)

		
		self.is_Auto_조회_Start = False
		self.is_barcode_connected = False
		self.wid_barcode = None

		self.is_작업지침서 = False
		self.is_생산지시서 = False

		self.param = ''
		self.defaultParam = f"page_size=0"

		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)

		from modules.PyQt.User.validator import Serial번호_Validator
		self.ui.lineEdit_Serial.setValidator(Serial번호_Validator(wid=self.ui.lineEdit_Serial))
		# lineEdit 텍스트 변경 시그널 연결
		self.ui.lineEdit_Serial.textChanged.connect(self.slot_validate_serial)

		self.ui.label_target.setText("관리자를 위한 화면")

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

	def triggerConnect(self):
		self.ui.pb_scan.clicked.connect(self.slot_pb_scan)
		self.ui.pb_search.clicked.connect(self.slot_pb_search)
		self.ui.pb_info.clicked.connect(lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

        # frame_info layout
        # self.PB_Production_Barcode_Start = QPushButton('생산실적집계_Barcode')
        # self.ui.horizontalLayout.addWidget(self.PB_Production_Barcode_Start)
        # self.PB_Production_Barcode_Start.clicked.connect(self.slot_PB_Production_Barcode_Start)
        # self.PB_Production_Barcode_Start.setEnabled(True)

	@pyqtSlot(str)
	def slot_validate_serial(self, text:str):
		"""시리얼 번호 유효성 검사 결과에 따라 검색 버튼 활성화/비활성화"""
		validator = self.ui.lineEdit_Serial.validator()
		state = validator.validate(text, 0)[0]
		self.ui.pb_search.setEnabled(state == QValidator.State.Acceptable)

	@pyqtSlot()
	def slot_pb_search(self):
		""" 검색 """
		# 체크박스와 lineEdit 값을 가져와서 검색 파라미터 생성
		search_params = {}
		
		# Serial 번호 검색
		serial_no = self.ui.lineEdit_Serial.text().strip()
		if serial_no:
			search_params['serial'] = serial_no
			
		# 체크박스 상태 확인
		if self.ui.checkBox_Jakji.isChecked():
			self.is_작업지침서 = True
			search_params['작업지시서'] = True
		if self.ui.checkBox_Sangji.isChecked():
			self.is_생산지시서 = True
			search_params['생산지시서'] = True
			
		# API 호출을 위한 쿼리 파라미터 생성
		query_params = '&'.join([f"{k}={v}" for k, v in search_params.items()])
		if query_params:
			query_params = f"{self.defaultParam}&{query_params}"
		else:
			query_params = self.defaultParam

		ic ( query_params )

		_isOk, _json = APP.API.getlist(INFO.URL_SERIAL_개별이력조회 + '?' + query_params)
		if _isOk:
			ic ( _json )
			if self.is_작업지침서 :
				if ( dataObj := _json.get('작업지시서', {}) )  :
					dlg_작업지침서 = Dialog_작업지침서_Form(self, url=self.url,  dataObj = dataObj , is_Edit=False )
				else:
					Utils.generate_QMsg_critical(self, title="작업지침서 오류",  text='작업지침서가 없읍니다.')
			if self.is_생산지시서 :
				if ( dataObj := _json.get('생산지시서', {}) )  :	
					dlg_생산지시서 = Dialog_생산지시서_Form(self, url=self.url,  dataObj = dataObj , is_Edit=False )
				else:
					Utils.generate_QMsg_critical(self, title="생산지시서 오류",  text='생산지시서가 없읍니다.')
		else:
			Utils.generate_QMsg_critical(self)	
		# 검색 실행
		# self.slot_search_for(query_params)

	@pyqtSlot()
	def slot_pb_scan(self):
		""" barcode 인식 시작 """

		if not self.wid_barcode:
			from modules.PyQt.User.barcode.barcode_recoginize import Wid_Barcode
			self.wid_barcode = Wid_Barcode(self, recognition_cooldown=10, max_retries=10, frame_update_time=100)

		
		# QDialog 생성 및 설정
		dialog = QDialog(self)
		dialog.setWindowTitle("바코드 스캔")
		dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
		
		# 레이아웃 설정
		layout = QVBoxLayout()
		layout.addWidget(self.wid_barcode)
		dialog.setLayout(layout)
		
		# 기존 시그널 연결 해제
		try:
			self.wid_barcode.signal_barcode_scanned.disconnect()
		except:
			pass
		# 시그널 연결
		self.wid_barcode.signal_barcode_scanned.connect(lambda barcode: self.slot_barcode_scanned(barcode, dialog))
		
		# 다이얼로그 표시
		dialog.exec()

	@pyqtSlot(str, QDialog)
	def slot_barcode_scanned(self, barcode_data:str, dialog:QDialog):
		""" 바코드 인식 후 처리 : lineEdit 에 바코드 입력 후, dialog 닫기 """
		self.ui.lineEdit_Serial.setText(barcode_data)
		dialog.close()

	@pyqtSlot()
	def slot_Barcode_Print  (self):
		""" Barcode Print """
		if not self.job_running_obj : return 

		_sendData = { '공정코드':'HI' ,'고객사':self.job_running_obj['고객사'] }
		ic ( _sendData )
		_isOk, _json = APP.API.Send( INFO.URL_SERIAL, {}, _sendData )
		if _isOk:
			from modules.PyQt.User.barcode.dialog_barcode_generate import Dialog_Barcode_Generate
			dlg = Dialog_Barcode_Generate(self, _data={'serial':_json.get('serial'), 'obj':self.job_running_obj})

			ic ( _json )
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