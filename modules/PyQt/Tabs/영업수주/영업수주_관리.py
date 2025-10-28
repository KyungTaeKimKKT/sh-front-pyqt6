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
from modules.PyQt.Tabs.영업수주.ui.Ui_tab_영업수주_관리 import Ui_Tab_App as Ui_Tab
from modules.PyQt.Tabs.영업수주.tables.table_영업수주_관리 import Wid_Table_for_영업수주_관리 as Wid_Table
###################
from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine
from modules.PyQt.User.validator import YearMonth_Validator
from modules.PyQt.Qthreads.background_api_thread import Background_API_Thread

from modules.PyQt.Tabs.영업수주.dialog.수주등록_api_process import 영업수주_등록_ApiProcess_Message

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
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

class Dlg_FileViewer(QDialog):

	def __init__(self, parent, paths:list[str]):
		super().__init__(parent)
		from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer
		self.paths = paths
		self.dlg = QDialog()
		vLayout = QVBoxLayout()
		wid = Wid_FileViewer( paths=self.paths)
		vLayout.addWidget ( wid )
		self.dlg.setLayout(vLayout)
		self.dlg.show()

class Dlg_수주등록(QDialog):
	signal_ok = pyqtSignal(dict)	### 확인 버튼 클릭 시 호출됨. API 호출 후 정상이면 JSON 반환

	def __init__(self, parent, dataObj:dict|None=None, **kwargs):
		super().__init__(parent)

		self.url = kwargs.get('url', None) or INFO.URL_영업수주_관리
		self.dataObj = dataObj or {}
		# self.is_edit = kwargs.get('is_edit', False)
		self.setWindowTitle('수주등록')
		self.일정_file_path = ""
		self.금액_file_path = ""
		self.UI()

		if self.dataObj:
			self._update_data()

	def UI(self):
		layout = QVBoxLayout()
		form_layout = QFormLayout()
		
		# 기준년월 입력
		self.le_기준년월 = QLineEdit()
		self.le_기준년월.setText(datetime.now().strftime("%Y-%m"))
		self.le_기준년월.setPlaceholderText('YYYY-MM 입력형식입니다.')
		self.le_기준년월.setValidator(YearMonth_Validator())
		self.le_기준년월.textChanged.connect(self.validate_inputs)
		form_layout.addRow("기준년월:", self.le_기준년월)
		
		# 일정 파일 업로드
		file_layout1 = QHBoxLayout()
		self.pb_Schedule_Upload = QPushButton("일정파일 선택")
		self.pb_Schedule_Upload.clicked.connect(self.slot_schedule_file_upload)
		self.pb_Schedule_Upload.setFixedWidth(100)  # 버튼 크기 고정
		self.lbl_Schedule_file = QLabel("선택된 파일 없음")
		file_layout1.addWidget(self.pb_Schedule_Upload)
		file_layout1.addWidget(self.lbl_Schedule_file)
		form_layout.addRow("일정file:", file_layout1)
		
		# 금액 파일 업로드
		file_layout2 = QHBoxLayout()
		self.pb_Money_Upload = QPushButton("금액파일 선택")
		self.pb_Money_Upload.clicked.connect(self.slot_money_file_upload)
		self.pb_Money_Upload.setFixedWidth(100)  # 버튼 크기 고정
		self.lbl_Money_file = QLabel("선택된 파일 없음")
		file_layout2.addWidget(self.pb_Money_Upload)
		file_layout2.addWidget(self.lbl_Money_file)
		form_layout.addRow("금액file:", file_layout2)
		
		# 비고 입력 추가
		self.pte_Bigo = QPlainTextEdit()
		self.pte_Bigo.setMaximumHeight(100)  # 높이 제한
		form_layout.addRow("비고:", self.pte_Bigo)

		# 버튼 레이아웃
		btn_layout = QHBoxLayout()
		self.pb_Ok = QPushButton("확인")
		self.pb_Ok.setFixedWidth(100)  # 버튼 크기 고정
		self.pb_Ok.setEnabled(False)
		self.pb_Cancel = QPushButton("취소")
		self.pb_Ok.clicked.connect(self.slot_Ok)
		self.pb_Cancel.clicked.connect(self.close)
		btn_layout.addWidget(self.pb_Ok)
		btn_layout.addWidget(self.pb_Cancel)
		
		layout.addLayout(form_layout)
		layout.addLayout(btn_layout)
		self.setLayout(layout)
		

	def _update_data(self):
		""" 수주 등록 데이터 업데이트 """
		self.le_기준년월.setText(self.dataObj['기준년월'])
		self.lbl_Schedule_file.setText(self.dataObj['일정file'])
		self.lbl_Money_file.setText(self.dataObj['금액file'])
		self.pte_Bigo.setPlainText(self.dataObj['비고'])

	@pyqtSlot()
	def validate_inputs(self):
		"""기준년월, 일정파일, 금액파일 중 하나 이상이 유효할 때 확인 버튼 활성화"""
		# 기준년월 형식 검증 (YYYY-MM)
		기준년월 = self.le_기준년월.text()
		is_valid_date = False
		if 기준년월:
			import re
			is_valid_date = bool(re.match(r'^\d{4}-\d{2}$', 기준년월))
		
		# 파일 선택 여부 확인 (하나 이상의 파일이 선택되어야 함)
		has_file = bool(self.일정_file_path) or bool(self.금액_file_path)
		
		# 기준년월이 유효하고 하나 이상의 파일이 선택되었을 때 확인 버튼 활성화
		self.pb_Ok.setEnabled(is_valid_date and has_file)

	@pyqtSlot()
	def slot_schedule_file_upload(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "일정 파일 선택", "", "Excel Files (*.xlsx *.xls)")
		if file_path:
			self.일정_file_path = file_path
			file_name = pathlib.Path(file_path).name
			self.lbl_Schedule_file.setText(file_name)
			self.validate_inputs()
	
	@pyqtSlot()			
	def slot_money_file_upload(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "금액 파일 선택", "", "Excel Files (*.xlsx *.xls)")
		if file_path:
			self.금액_file_path = file_path
			file_name = pathlib.Path(file_path).name
			self.lbl_Money_file.setText(file_name)
			self.validate_inputs()

	@pyqtSlot()			
	def slot_Ok(self):
		기준년월 = self.le_기준년월.text()
		비고 = self.pte_Bigo.toPlainText()
		if not 기준년월:
			Utils.generate_QMsg_warning(self, "입력 오류", "기준년월을 입력해주세요.")
			return
			
		if not self.일정_file_path and not self.금액_file_path:
			Utils.generate_QMsg_warning(self, "파일 오류", "일정 파일 또는 금액 파일을 선택해주세요.")
			return
		
		sendData = {
			'기준년월' : 기준년월,
			'비고' : 비고,
			'등록자_fk' : INFO.USERID,
		}
		send_files = [
			('일정file', open( self.일정_file_path, 'rb') )	,
			('금액file', open( self.금액_file_path, 'rb') ),
		]
		# 여기에 파일 업로드 및 처리 로직 추가
		_isok, _json = APP.API.Send(self.url, self.dataObj, sendData, send_files)
		if _isok:
			Utils.generate_QMsg_Information(self, title="파일 업로드 완료", text="파일 업로드가 완료되었읍니다.", autoClose=1000)
			self.signal_ok.emit(_json)
			self.accept()
		else:
			Utils.generate_QMsg_critical(self, title="파일 업로드 실패", text="파일 업로드에 실패했읍니다.")
		





class 관리__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )

		
		self.is_Auto_조회_Start = True
		self.selected_rows:list[dict] = []
		self.판금처_list_dict:list[dict] = []
		self.param = ''		
		self.api_datas:list[dict] = []
		self.defaultParam = f"page_size=25"
		self.기타조회조건 = {}
		self.기타조회조건_for_param = {}
		self.자재내역_to_의장_Datas = []
		self._init_kwargs(**kwargs)
	
		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		self._ui_custom()

		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=self.기타조회조건)

		self.triggerConnect()

		if hasattr(self, 'url_db_fields') and self.url_db_fields :
			self._get_DB_Field(self.url_db_fields  )	

		self._start_bg_thread(INFO.URL_영업수주_자재내역_의장_Mapping+'?page_size=0')

		
		self._init_helpPage()


	def _start_bg_thread(self, url:str):
		self.bg_thread = Background_API_Thread(url)
		self.bg_thread.finished.connect(self.slot_api_mapping_datas_finished)
		self.bg_thread.error.connect(self.slot_api_mapping_datas_error)
		self.bg_thread.start()

	@pyqtSlot( bool, object)
	def slot_api_mapping_datas_finished(self, is_ok:bool, _json:object):
		if is_ok:
			self._render_PB_Mapping( _json )
		self._disconnect_signal(self.bg_thread.finished)
		self._disconnect_signal(self.bg_thread.error)
	
	@pyqtSlot(bool, object)
	def slot_api_mapping_datas_error(self, is_ok:bool, _json:object):
		self._disconnect_signal(self.bg_thread.finished)
		self._disconnect_signal(self.bg_thread.error)

	def closeEvent(self, event):
		"""위젯이 닫힐 때 호출되는 이벤트 핸들러"""
		# 웹소켓 연결 종료
		if hasattr(self, 'ws_manager') and self.ws_manager:
			self.ws_manager.close_all_connections()
		
		# Worker 객체의 신호 연결 해제
		if hasattr(self, 'work') and self.work:
			self.work.quit()
			self._disconnect_signal(self.work.signal_worker_finished.signal)
		
		if hasattr(self, 'bg_thread') and self.bg_thread:
			self.bg_thread.quit()
			self._disconnect_signal(self.bg_thread.finished)
			self._disconnect_signal(self.bg_thread.error)

		# 부모 클래스의 closeEvent 호출
		super().closeEvent(event)

	def __del__(self):
		"""소멸자"""
		# 웹소켓 연결 종료
		if hasattr(self, 'ws_manager') and self.ws_manager:
			self.ws_manager.close_all_connections()
		# Worker 객체의 신호 연결 해제
		if hasattr(self, 'work') and self.work:
			self._disconnect_signal(self.work.signal_worker_finished.signal)
	
	def _render_PB_Mapping(self, _list:list[dict]):
		self.자재내역_to_의장_Datas = _list
		no_의장_list = [ _dict for _dict in self.자재내역_to_의장_Datas if _dict.get('의장_fk',None) is None ]
		if no_의장_list:
			self.ui.PB_Mapping.setEnabled(True)
			self.ui.PB_Mapping.setText(f'의장 매핑 미완료 ({len(no_의장_list)}/{len(self.자재내역_to_의장_Datas)})')
			self.ui.PB_Mapping.setStyleSheet('QPushButton { background-color: red;color:white }')
		else:
			self.ui.PB_Mapping.setEnabled(False)
			self.ui.PB_Mapping.setText(f'의장 매핑 완료 ({len(no_의장_list)}/{len(self.자재내역_to_의장_Datas)})')
			self.ui.PB_Mapping.setStyleSheet('QPushButton { background-color: #008000; }')


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


	def triggerConnect(self):
		#### checkBox 체크 여부에 따라 조회조건 설정
		# 체크박스 상태에 따라 frame_Period 보이기/숨기기
		self.ui.checkBox_Jaksung.stateChanged.connect(lambda: self.ui.frame_Period.setVisible(self.ui.checkBox_Jaksung.isChecked()))

		self.ui.PB_New.clicked.connect( self.slot_PB_New )
		self.ui.PB_Edit.clicked.connect( self.slot_PB_Edit )
		self.ui.PB_Confirm.clicked.connect( self.slot_PB_Confirm )
		self.ui.PB_Del.clicked.connect(lambda: self.slot_del())

		self.ui.PB_Schedule_upload.clicked.connect(lambda: self.slot_excel_schedule_upload())
		self.ui.PB_Money_upload.clicked.connect(lambda: self.slot_excel_money_upload())
		self.ui.PB_Mapping.clicked.connect(lambda: self.slot_Uljang_mapping())

		self.ui.PB_Simulation.clicked.connect(self.slot_simulation )
		self.ui.PB_Summary.clicked.connect(self.slot_summary )
		self.ui.PB_Download.clicked.connect(self.slot_download )

		self.triggerConnect_Search()
		self.triggerConnect_Wid_Pagination()


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
			self.slot_search_for(self.param if self.param else self.defaultParam )
	

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

			
			# 데이터 타입 확인
			column_types = df.dtypes


			
			# 필요한 경우 데이터 타입 변환
			# 날짜 형식 변환 예시
			field_model = {}
			table_header = []
			for col in df.columns:
				table_header.append(col)
				if pd.api.types.is_datetime64_any_dtype(df[col]):
					field_model[col] = 'datetimefield'

				elif pd.api.types.is_numeric_dtype(df[col]):
					field_model[col] = 'integerfield'

				elif pd.api.types.is_string_dtype(df[col]):
					field_model[col] = 'charfield'

				elif pd.api.types.is_bool_dtype(df[col]):
					field_model[col] = 'booleanfield'

				elif pd.api.types.is_float_dtype(df[col]):
					field_model[col] = 'floatfield'

				elif pd.api.types.is_integer_dtype(df[col]):
					field_model[col] = 'datefield'

				elif pd.api.types.is_datetime64_any_dtype(df[col]):
					field_model[col] = 'textfield'

				else:
					field_model[col] = 'charfield'


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

		self.api_datas.insert(0, data_dict)  # 맨 첫 번째에 data_dict 추가
		self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url, **self.db_fields )
		self._diable_pb()

	@pyqtSlot()
	def slot_PB_Edit(self):
		dataObj = self.selected_rows[0] if self.selected_rows else None

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