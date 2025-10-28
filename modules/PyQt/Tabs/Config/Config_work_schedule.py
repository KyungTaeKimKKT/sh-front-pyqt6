from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

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

from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
### 😀😀 user : ui...
from modules.PyQt.Tabs.Config.ui.Ui_tab_Config_work_schedule import Ui_Tab_App as Ui_Tab
from modules.PyQt.Tabs.Config.tables.table_Config_work_schedule import Wid_Table_for_Work_Schedule as Wid_Table

###################
from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine
from modules.PyQt.User.validator import YearMonth_Validator
from modules.PyQt.Qthreads.background_api_thread import Background_API_Thread

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

from typing import Callable
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.Tabs.plugins.BaseTab_Slot_Handler import BaseTab_Slot_Handler

from modules.utils.api_response_분석 import handle_api_response

class Work_schedule__for_Tab_Slot_Handler(BaseTab_Slot_Handler):
	
	def __init__(self, handler: BaseTab):
		super().__init__(handler)
		self.handler = handler
		self.event_bus = event_bus

	def slot_search_for(self, url:str=None, param:str=None):
		url = ( url or self.handler.url ) + (param or '?page_size=25')
		self.event_bus.subscribe(f"fetch_{url}", self.slot_fetch_finished)
		worker = Api_Fetch_Worker(url)
		worker.start()

		
	def slot_fetch_finished(self, msg):
		is_ok, pagination, api_datas = handle_api_response(msg)
		logger.info(f'fetch_finished: {msg}')
		self.handler.set_api_datas(api_datas)
		self.handler.set_fetch_flag(True)
		self.handler.update_ui()




class work_schedule__for_Tab( BaseTab ):
	def __init__(self, parent:QMainWindow,   **kwargs ):
		self.ui = Ui_Tab()
	
		super().__init__(parent=parent, **kwargs)

		self.slot_handler = Work_schedule__for_Tab_Slot_Handler(self)


	def closeEvent(self, event):
		"""위젯이 닫힐 때 호출되는 이벤트 핸들러"""
		super().closeEvent(event)

	def setup_ui(self):
		self.ui.setupUi(self)
		self.ui.wid_table = Wid_Table(self)
		self.ui.main_frame.layout().addWidget(self.ui.wid_table)

	def customize_ui(self):
		pass

	def update_ui(self):
		self.ui.wid_table._update_data(
			api_data=self.api_datas, 
			table_name=self.table_name, 
			**self.kwargs
		)
		self.ui.wid_table.run()

	def connect_signals(self):
		self.ui.PB_Search.clicked.connect(lambda: self.slot_handler.slot_search_for(self.url, self.get_param()))


	def get_param(self) -> str:
		""" param 반환 """
		검색어 = self.ui.lineEdit_search.text()
		try: 
			page_size = int(self.ui.comboBox_pageSize.currentText())
		except:
			page_size = 0
		self.last_param = f'?search={검색어}&page_size={page_size}'
		return self.last_param





	def _ui_custom(self):
		self.info_title = getattr(self, 'info_title',None) or "관리자를 위한 화면"
		# 기본 날짜 설정
		today = QDate.currentDate()
		self.ui.dateEdit_From.setDate(today)
		self.ui.dateEdit_To.setDate(today)
		self.ui.frame_Period.setVisible(False)

		self.ui.comboBox_pageSize.addItems( ['ALL'] + ['25', '50', '100'] )
		self.ui.comboBox_pageSize.setCurrentText('25')

		self._set_info_title(self.info_title)
		# self.ui.label_target.setText( self.info_title )


	def connect_signals(self):
		self.ui.PB_Search.clicked.connect( 
			lambda  : self.slot_handler.slot_search_for(self.url, self.get_param())  )
		

		# #### checkBox 체크 여부에 따라 조회조건 설정
		# # 체크박스 상태에 따라 frame_Period 보이기/숨기기
		# self.ui.checkBox_Jaksung.stateChanged.connect(lambda: self.ui.frame_Period.setVisible(self.ui.checkBox_Jaksung.isChecked()))

		# self.ui.PB_New.clicked.connect( self.slot_PB_New )
		# self.ui.PB_Edit.clicked.connect( self.slot_PB_Edit )
		# self.ui.PB_Confirm.clicked.connect( self.slot_PB_Confirm )
		# self.ui.PB_Del.clicked.connect(lambda: self.slot_del())

		# self.ui.PB_Schedule_upload.clicked.connect(lambda: self.slot_excel_schedule_upload())
		# self.ui.PB_Money_upload.clicked.connect(lambda: self.slot_excel_money_upload())
		# self.ui.PB_Mapping.clicked.connect(lambda: self.slot_Uljang_mapping())

		# self.ui.PB_Simulation.clicked.connect(self.slot_simulation )
		# self.ui.PB_Summary.clicked.connect(self.slot_summary )
		# self.ui.PB_Download.clicked.connect(self.slot_download )

		# self.triggerConnect_Search()
		# self.triggerConnect_Wid_Pagination()


	def triggerConnect_Search(self):
		if hasattr(self.ui, 'PB_Search'):
			self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()) )
		if hasattr(self.ui, 'PB_Search_Condition'):
			self.ui.PB_Search_Condition.clicked.connect(  self.slot_search_condition )
			self.ui.PB_Search_Condition.search_conditions_cleared.connect(	lambda: setattr(self,'기타조회조건',{}) )


	def triggerConnect_Wid_Pagination(self):
		if hasattr(self.ui, 'pb_info'):
			self.ui.pb_info.clicked.connect(lambda: Dlg_FileViewer(self, paths=[self.help_page]))
		if hasattr(self.ui, 'wid_pagination'):
			self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
			self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
			self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))


	def triggerConnect_Wid_Table(self):
		if hasattr(self.ui, 'Wid_Table'):
			self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: setattr(self, 'selected_rows', select_list))
			self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: print ( 'select_list : ', select_list ))
			self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Del.setEnabled(len(select_list) == 1))
			# self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Fileview.setEnabled(len(select_list) == 1) and  select_list[0]['file'] )
			self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Download.setEnabled(len(select_list) == 1) and  select_list[0]['file'] )
			self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Simulation.setEnabled(len(select_list) == 1) )
	
	def _get_param(self):
		param_list = []
		if ( value := self.ui.lineEdit_search.text() ) :
			param_list.append ( f'search={value}' )

		if self.ui.checkBox_Jaksung.isChecked():
			param_list.append ( f'작성일_From={self.ui.dateEdit_From.date().toString("yyyy-MM-dd")}' )
			param_list.append ( f'작성일_To={self.ui.dateEdit_To.date().toString("yyyy-MM-dd")}' )

		if (value := self.ui.comboBox_pageSize.currentText() ) != 'ALL':
			param_list.append ( f'page_size={value}' )
		else:
			param_list.append ( f'page_size=0' )

		param = '&'.join(param_list)
		return param

	### 조회조건 설정
	@pyqtSlot()
	def slot_search_condition(self):
		검색조건 = {
			'진행현황' : 'QRadioButton',
			'부적합유형' : 'QLineEdit',
			'차수' : 'Range_SpinBox',
			'el수량' : 'Range_SpinBox',
			'등록자' : 'QLineEdit',
			'등록일' : 'Range_DateEdit',
			'완료일' : 'Range_DateEdit',
			'완료자' : 'QLineEdit',
			'활동현황' : 'QLineEdit',
			'품질비용' : 'Range_SpinBox',
		}

		default_dict = {
			'진행현황' : 'ALL',
			'차수' : {'From':1, 'To':10},
			'el수량' : {'From':1, 'To':100},
			'품질비용' : {'From':1, 'To':100000000},
			'등록일' : {'From':datetime.now().date() + timedelta(days=-7), 'To':datetime.now().date() + timedelta(days=7)},
			'완료일' : {'From':datetime.now().date() + timedelta(days=-7), 'To':datetime.now().date() + timedelta(days=7)},

		}

		config_kwargs = {
			'radios' : {
				'진행현황' : ['ALL', 'Open', 'Close' ],
			}
		}
		_default_dict = self.기타조회조건 if self.기타조회조건 else default_dict
		### ALL인 경우 self.기타조회조건은 삭제되므로, 기본값을 넣어줌.
		if '진행현황' not in _default_dict :
			_default_dict['진행현황'] = 'ALL'

		dlg = Dialog_조회조건(
				self, 
				input_dict = 검색조건, 
				default_dict = _default_dict , 
				title = '조회조건 설정', 
				config_kwargs = config_kwargs
				)
		dlg.result_signal.connect( self.slot_update_etc_search_condition )


	@pyqtSlot(dict)
	def slot_update_etc_search_condition(self, 기타조회조건:dict):
		"""
			dialog_조회조건에서 조회조건 설정 후, 확인 버튼 클릭 시 호출됨.
		"""
		ic(기타조회조건)
		self.기타조회조건 = 기타조회조건
		def _convert_to_dict(기타조회조건: dict) -> dict:
			converted_dict = {}
			for key, value in 기타조회조건.items():
				if isinstance(value, dict) and 'From' in value and 'To' in value:
					converted_dict[f"{key}_From"] = value['From']
					converted_dict[f"{key}_To"] = value['To']
				else:
					converted_dict[key] = value
			return converted_dict

		self.기타조회조건_for_param = _convert_to_dict(기타조회조건)
		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=기타조회조건)



	def _get_sendData(self, rowDict:dict, status:str) -> dict:
		sendData = {}
		sendData['상태'] = status
		sendData['처리시간'] = datetime.now()
		sendData['처리자'] = INFO.USERID
		return sendData

	#### app마다 update 할 것.😄
	def run(self):
		if self.is_Auto_조회_Start :
			self.slot_handler.slot_search_for(self.param if self.param else self.defaultParam )

	

	def _diable_pb(self):
		self.selected_rows = []
		self.ui.PB_Del.setEnabled(False)
		# self.ui.PB_Fileview.setEnabled(False)
		self.ui.PB_Download.setEnabled(False)

	def _get_field_model_from_excel( self, data_list:list[dict]) -> dict:
		db_fields = {
			'table_config':{
				'table_header':list(data_list[0].keys()),

			}
		}
		return db_fields
	

	@pyqtSlot()	
	def slot_simulation(self):
		""" 시뮬레이션 버튼 클릭 시 호출됨. """
		dataObj = self.selected_rows[0] if self.selected_rows else None
		url = '영업수주/simulation/'
		is_ok, _json = APP.API.post( url, {'수주_id':dataObj['id']})
		if is_ok:
			print ( 'simulation_result : ', _json )
			User_Toast(parent=INFO.MAIN_WINDOW, title='시뮬레이션', text='시뮬레이션 완료', style='SUCCESS')
		else:
			User_Toast(parent=INFO.MAIN_WINDOW, title='시뮬레이션', text='시뮬레이션 실패', style='ERROR')


	@pyqtSlot()
	def slot_summary(self):
		""" 요약 버튼 클릭 시 호출됨. """
		# dataObj = self.selected_rows[0] if self.selected_rows else None
		sendData = {
			'기준년월' : '2025-03',
			'마감일기준' : '2025-03-31',
			'UV_마감일기준' : '2025-04-04',
			'category' : '호기번호',    #'의장', '호기번호','Proj_번호' 중
		}
		url = INFO.URL_영업수주_금액_Summary_Api
		is_ok, _json = APP.API.post( url, sendData )
		if is_ok:
			# print ( 'summary_result : ', _json['result'][:5], '\n\n',_json['db_fields'] )
			from modules.PyQt.Tabs.영업수주.tables.table_영업수주_Summary import Wid_Table_for_영업수주_Summary
			dlg = QDialog(self)
			dlg.setMinimumSize(800, 1200)
			dlg.setWindowTitle('요약')
			layout = QVBoxLayout()
			wid_table = Wid_Table_for_영업수주_Summary(dlg)
			wid_table._update_data(api_data=_json['result'], **_json['db_fields'])
			layout.addWidget(wid_table)
			dlg.setLayout(layout)
			dlg.show()
			dlg.exec()
			
			
		

	@pyqtSlot()	
	def slot_excel_schedule_upload(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
		
		if not file_path:
			return

		with open(file_path, 'rb') as file:
			sendFile = [('file', file)]
			is_ok, _json = APP.API.Send( INFO.URL_영업수주_일정_EXCEL_UPLOAD_BULK, {}, {}, sendFile)
			if is_ok:
				User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text=f'{ file_path}  데이터 업로드 완료', style='SUCCESS')
			else:
				User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text='다시 시도해 주십시요', style='WARNING')


	@pyqtSlot()
	def slot_excel_money_upload(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
		
		if not file_path:
			return

		with open(file_path, 'rb') as file:
			sendFile = [('file', file)]
			is_ok, _json = APP.API.Send( INFO.URL_영업수주_금액_EXCEL_UPLOAD_BULK, {}, {}, sendFile)
			if is_ok:
				error_logs = _json['error_logs']
				if error_logs:
					_txt = '\n'.join(error_logs[:10])
					Utils.generate_QMsg_critical(self, title='엑셀 업로드', text=_txt)
				else:
					User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text=f'{ file_path}  데이터 업로드 완료', style='SUCCESS')
			else:
				User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text='다시 시도해 주십시요', style='WARNING')
	
	@pyqtSlot()
	def slot_Uljang_mapping(self):
		""" 자재내역을 의장으로 mapping"""
		if not self.자재내역_to_의장_Datas:
			return
		from modules.PyQt.Tabs.영업수주.dialog.dlg_자재내역_to_의장_mapping import Dlg_자재내역_to_의장_Mapping
		dlg = Dlg_자재내역_to_의장_Mapping(self, api_data=self.자재내역_to_의장_Datas)
		dlg.exec()


	@pyqtSlot()
	def slot_excel_upload_local(self):
		""" excel file을 local에서 upload합니다 """
		file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
		
		if not file_path:
			return
		
		try:
			# 엑셀 파일 읽기
			s = time.time()
			df = pd.read_excel(file_path)
			e = time.time()
			print ( f'reading excel time : {e-s}' )
			
			# 데이터 타입 확인
			column_types = df.dtypes
			print("데이터 타입 정보:")
			print(column_types)
			
			# 필요한 경우 데이터 타입 변환
			# 날짜 형식 변환 예시
			field_model = {}
			table_header = []
			for col in df.columns:
				table_header.append(col)
				if pd.api.types.is_datetime64_any_dtype(df[col]):
					field_model[col] = 'datetimefield'
					print(f"{col} = datetimefield")
				elif pd.api.types.is_numeric_dtype(df[col]):
					field_model[col] = 'integerfield'
					print(f"{col} = integerfield")
				elif pd.api.types.is_string_dtype(df[col]):
					field_model[col] = 'charfield'
					print(f"{col} = charfield")
				elif pd.api.types.is_bool_dtype(df[col]):
					field_model[col] = 'booleanfield'
					print(f"{col} = booleanfield")
				elif pd.api.types.is_float_dtype(df[col]):
					field_model[col] = 'floatfield'
					print(f"{col} = floatfield")
				elif pd.api.types.is_integer_dtype(df[col]):
					field_model[col] = 'datefield'
					print(f"{col} = datefield")
				elif pd.api.types.is_datetime64_any_dtype(df[col]):
					field_model[col] = 'textfield'
					print(f"{col} = textfield")
				else:
					field_model[col] = 'charfield'
					print(f"{col} = charfield")
			for header in table_header:
				print (header)
			db_fields = {
				'fields_model':field_model,
				'fields_append':{},
				'fields_delete':{},
				'table_config':{
					'table_header':table_header,
					'no_Edit_cols' : [],
					'hidden_columns' : [],
				}
			}
			# DataFrame을 list of dict로 변환
			s = time.time()
			data_list = df.to_dict('records')
			e = time.time()
			print ( f'df to dict time : {e-s}' )
			
			if not data_list:
				User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text='데이터가 없읍니다.', style='WARNING')
				return
			
			# # 데이터 처리 및 테이블 업데이트
			# self.api_datas = data_list
			# self.db_fields = self._get_field_model_from_excel(data_list)
			self.ui.Wid_Table._update_data(api_data=data_list[0:50], url=self.url, **db_fields)
			User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드', text=f'{len(data_list)}개 데이터 업로드 완료', style='SUCCESS')
			
		except Exception as e:
			User_Toast(parent=INFO.MAIN_WINDOW, title='엑셀 업로드 오류', text=f'파일 처리 중 오류 발생: {str(e)}', style='ERROR')
	
	@pyqtSlot()
	def slot_save_to_db(self):
		pass

	@pyqtSlot()
	def slot_download(self):
		pass

	@pyqtSlot()
	def slot_fileview(self):
		pass	

	@pyqtSlot()
	def slot_PB_New(self):
		""" 신규 수주 등록 """
		dataObj = self.selected_rows[0] if self.selected_rows else None
		dlg_수주등록 = Dlg_수주등록(self, dataObj=dataObj)
		dlg_수주등록.signal_ok.connect(self.slot_new_ok)
		dlg_수주등록.exec()

	@pyqtSlot(dict)
	def slot_new_ok(self, data_dict:dict):
		print ( 'slot_new_ok', data_dict )
		self.api_datas.insert(0, data_dict)  # 맨 첫 번째에 data_dict 추가
		self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url, **self.db_fields )
		self._diable_pb()

	@pyqtSlot()
	def slot_PB_Edit(self):
		dataObj = self.selected_rows[0] if self.selected_rows else None
		print ( 'SLOT_PB_Edit', dataObj )
		dlg_수주등록 = Dlg_수주등록(self, dataObj=dataObj)
		dlg_수주등록.signal_ok.connect(self.slot_new_ok)
		dlg_수주등록.exec()


	@pyqtSlot()
	def slot_PB_Confirm(self):
		if not self.selected_rows:
			return
		dataObj = self.selected_rows[0]
		sendData = {'id' : dataObj['id'],	'기준년월':	dataObj['기준년월']}
		# 비동기 작업자 생성 및 실행
		worker = Worker_Post(INFO.URL_영업수주_등록ApiProcess, sendData)
		worker.signal_worker_finished.signal.connect(self.handle_confirm_response)
		# 작업 시작
		QThreadPool.globalInstance().start(worker)

		# 진행 중 다이얼로그 미리 표시
		self.dlg_api_process = 영업수주_등록_ApiProcess_Message(self, {'subject': '수주 확정 처리 중...', 'message': '서버에서 처리 중입니다.', 'progress': 0})
		self.dlg_api_process.exec()



	@pyqtSlot(bool, bool, object)
	def handle_confirm_response(self, is_Pagenation, _isOk, _json):
		# API 응답 처리
		if _isOk:
			User_Toast(parent=INFO.MAIN_WINDOW, title='수주 확정', text='수주 확정 요청 완료', style='SUCCESS')
		else:
			User_Toast(parent=INFO.MAIN_WINDOW, title='수주 확정', text='수주 확정 요청 실패', style='ERROR')
			if hasattr(self, 'dlg_api_process') and self.dlg_api_process:
				self.dlg_api_process.close()
		
		# 신호 연결 해제
		sender = self.sender()
		if sender and hasattr(sender, 'signal_worker_finished'):
			self._disconnect_signal(sender.signal_worker_finished.signal)

	@pyqtSlot(dict)
	def slot_ws_sales_order_register_api_process(self, data_dict:dict):
		if not hasattr(self, 'dlg_api_process') :
			self.dlg_api_process = 영업수주_등록_ApiProcess_Message(self, data_dict)
			self.dlg_api_process.show()

		self.dlg_api_process.update_message(data_dict)
			
		# 진행률이 100%이면 5초 후 자동으로 닫기
		if data_dict.get('progress', 0) == 100:
			QTimer.singleShot(5000, self.dlg_api_process.close)


	@pyqtSlot()
	def slot_del(self):
		dataObj = self.selected_rows[0]
		dlg_res_button = Utils.generate_QMsg_question(self, title='CS Claim 삭제', text='삭제하시겠습니까?')
		if dlg_res_button != QMessageBox.StandardButton.Ok :
			return 
		if APP.API.delete(self.url+ str(dataObj['id']) ):
			try:
				### 데이터 삭제 후 테이블 업데이트
				self.api_datas.remove(dataObj)
				if self.api_datas:
					self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
				else:
					self.ui.Wid_Table._update_data(api_data=[], url=self.url)
			except Exception as e:
				ic(e)
			self._diable_pb()
		else:
			Utils.generate_QMsg_critical(self)


	@pyqtSlot()
	def slot_fileview(self):
		""" 파일 뷰어 """
		file_path = [ _dict['file'] for _dict in self.selected_rows if _dict['file'] ]
		if file_path:
			dlg_fileviewer = Dlg_FileViewer(self, paths=file_path)
			self._diable_pb()

	@pyqtSlot()
	def slot_download(self):
		""" 파일 다운로드 """
		file_path = [ _dict['file'] for _dict in self.selected_rows if _dict['file'] ]
		if file_path:
			for file in file_path:
				fName = Utils.func_filedownload(file)
				User_Toast(parent=INFO.MAIN_WINDOW, title='File Download', text=f'{fName} 파일 다운로드 완료', style='SUCCESS')
			self._diable_pb()


	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""
		self.loading_start_animation()	

		if self.기타조회조건 and self.기타조회조건_for_param :
			param = param + '&' + '&'.join( [ f'{key}={value}' for key, value in self.기타조회조건_for_param.items() ] )

		self.param = param 
		
		url = self.url + '?' + param

		###😀 GUI FREEZE 방지 ㅜㅜ;;
		pool = QThreadPool.globalInstance()
		self.work = Worker(url)
		self.work.signal_worker_finished.signal.connect ( self.table_update )
		pool.start( self.work )



	@pyqtSlot(bool, bool, object)
	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
		# ic ( is_Pagenation, _isOk, api_datas )
		if not _isOk:
			self._disconnect_signal(signal=self.work.signal_worker_finished.signal)
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
		
		start_time = time.time()
		self._update_update_time()   ### table 업데이트 시간 업데이트
		if hasattr(self.ui, 'Wid_Table'):
			( self.ui.Wid_Table.set_api_datas(self.api_datas)
						.set_table_config(self.db_fields)
						.set_table_config_api_datas(self.db_fields)
						.set_header_types(self.db_fields)
						.set_hidden_columns(self.db_fields)
						.set_no_edit_cols(self.db_fields)
						.set_column_types(self.db_fields)
						.set_column_styles(self.db_fields)
						.set_column_widths(self.db_fields)
						.set_table_style(self.db_fields)
			)

		else:	
			wid_table = ( Wid_Table(self)
				.with_api_datas(api_datas=self.api_datas)
				.with_table_name(self.table_name)
			)
			wid_table.run()
			setattr ( self.ui, 'Wid_Table', wid_table )
			self.ui.main_frame.layout().addWidget(wid_table)
			self.triggerConnect_Wid_Table()

		self._disconnect_signal(signal=self.work.signal_worker_finished.signal)
		self.loading_stop_animation()
		print ( f"table_update finished : {time.time() - start_time:.2f} seconds")

	def _update_table_by_ws_auto(self, api_datas:list[dict], _text:str|None=None):
		self._update_update_time(_text)
		self.ui.Wid_Table._update_data(
			api_data=api_datas,
			url = self.url,
			**self.db_fields,
			
		)
	
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