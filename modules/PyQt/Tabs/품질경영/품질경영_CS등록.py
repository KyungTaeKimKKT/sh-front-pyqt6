from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from datetime import date, datetime
import copy

### 😀😀 user : ui...
from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table
from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS_Project_Form 

from modules.PyQt.Tabs.품질경영.tables.Wid_table_품질경영_CS등록 import Wid_table_품질경영_CS등록 as Wid_table

from modules.PyQt.Tabs.품질경영.chart.gantt_chart import GanttView

from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
# from modules.PyQt.Tabs.품질경영.품질경영_CS_form import CS_Form as CS_Project_Form
from modules.PyQt.Tabs.품질경영.CS_활동현황_form import CS_활동현황_Form, CS_활동현황_Form_View
from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit
from modules.PyQt.compoent_v2.Wid_label_and_pushbutton import Wid_label_and_pushbutton
from modules.PyQt.compoent_v2.Wid_lineedit_and_pushbutton import Wid_lineedit_and_pushbutton
from modules.PyQt.compoent_v2.widget_manager import WidManager
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly
###################
from modules.utils.api_response_분석 import handle_api_response
from modules.PyQt.Tabs.plugins.BaseTab_Slot_Handler import BaseTab_Slot_Handler

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.base_form_dialog import Base_Form_Dialog


# class CS_Project_Form(Base_Form_Dialog):
# 	minium_size = (600, 600)
# 	_url_list_for_label_pb = {
# 		'Elevator사': INFO.URL_CS_CLAIM_GET_ELEVATOR사,
# 		'부적합유형': INFO.URL_CS_CLAIM_GET_부적합유형,
# 	}

# 	el_info_fk:Optional[int] = None

# 	def _gen_inputWidget(self, attrName:str='', attrType:str='') -> QWidget:
# 		self.map_attrName_to_button_dict = {
# 			'Elevator사': {'button_dict':{'text':'선택', 'clicked':self.on_select_Elevator_Company}},
# 			'부적합유형': {'button_dict':{'text':'선택', 'clicked':self.on_select_NCR_Type}	},
# 			'현장명': {'button_dict':{'text':'검색', 'clicked':self.on_hyunjang_search}},
# 		}

# 		match attrName:
# 			case 'Elevator사' | '부적합유형' :
# 				self.inputDict[attrName] = WidManager._create_label_and_pushbutton_widget(
# 					self, 
# 					self.dataObj.get(attrName, attrName),
# 					is_readonly=self.is_readonly,
# 					**self.map_attrName_to_button_dict[attrName]
# 					)
# 				return self.inputDict[attrName]
# 			case '현장명':
# 				self.inputDict['현장명'] = WidManager._create_lineedit_and_pushbutton_widget(
# 					self, 
# 					self.dataObj.get(attrName, ''),
# 					is_readonly=self.is_readonly,
# 					**self.map_attrName_to_button_dict[attrName]
# 					)
# 				return self.inputDict[attrName]
# 			# 	self.wid_elevator_company = Wid_label_and_pushbutton(self, attrName, button_dict={'text':'선택', 'clicked':self.on_select_Elevator_Company})
# 			# 	self.inputDict['Elevator사'] = self.wid_elevator_company
# 			# 	return self.wid_elevator_company
# 			# case '현장명':
# 			# 	self.wid_hyunjang = Wid_lineedit_and_pushbutton(self, '', button_dict={'text':'검색', 'clicked':self.on_hyunjang_search})
# 			# 	self.wid_hyunjang.set_qe_placeholder('현장명 검색(현장명 검색 결과가 많으면 검색 조건을 좁히세요.)')
# 			# 	self.inputDict['현장명'] = self.wid_hyunjang
# 			# 	return self.wid_hyunjang
# 			# case '부적합유형':
# 			# 	self.wid_ncr_type = Wid_label_and_pushbutton(self, attrName, button_dict={'text':'선택', 'clicked':self.on_select_NCR_Type})
# 			# 	self.inputDict['부적합유형'] = self.wid_ncr_type
# 				# return self.wid_ncr_type
# 			case 'claim_files':
# 				claim_files_url = self.dataObj.get( 'claim_files_url', [])
# 				if claim_files_url and isinstance(claim_files_url, list) :
# 					if claim_files_url[0].startswith('http://') or claim_files_url[0].startswith('https://'):
# 						pass
# 					else:
# 						claim_files_url = [ f'http://{INFO.API_SERVER}:{INFO.HTTP_PORT}' + item for item in claim_files_url ]
# 				claim_files = []
# 				for (id, url) in zip(self.dataObj.get('claim_files_ids', []), claim_files_url):
# 					claim_files.append( {'id':id, 'file':url} )

# 				logger.debug(f"claim_files : {claim_files_url}")
# 				self.inputDict['claim_files'] = WidManager._create_file_upload_list_widget(
# 					self, 
# 					claim_files,
# 					is_readonly=self.is_readonly,
# 					)
# 				return self.inputDict[attrName]
# 				# from modules.PyQt.compoent_v2.FileListWidget.wid_fileUploadList import File_Upload_ListWidget
# 				# self.wid_claim_files = File_Upload_ListWidget(self)
# 				# self.inputDict['claim_files'] = self.wid_claim_files
# 				# return self.wid_claim_files
# 			case _:
# 				return super()._gen_inputWidget(attrName, attrType)
			
# 	def get_send_data(self):
# 		""" override """
# 		send_data, send_files = super().get_send_data()
# 		if self.el_info_fk:
# 			send_data['el_info_fk'] = self.el_info_fk
# 		send_data['등록자_fk'] = INFO.USERID
# 		send_data['등록자'] = INFO.USERNAME
# 		send_data['등록일'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 		### drf 와 연동되는 것으로, 파일 전송 시 파일 경로와 파일 아이디를 따로 보내야 함.
# 		keyNamesFile = 'claim_files'
# 		if keyNamesFile in send_data:
# 			send_files_dict_list = send_data.pop(keyNamesFile)
# 			file_paths = [ item.get('file') for item in send_files_dict_list  if item.get('type') == 'local']
# 			send_files = [
#     			(keyNamesFile, (open(path, "rb"))) for path in file_paths
# 			]
# 			claim_files_ids = [ item.get('id') for item in send_files_dict_list  if item.get('type') == 'server']
# 			send_data['claim_files_ids'] = claim_files_ids
# 		logger.debug(f"send_data : {send_data}")
		
# 		return send_data, send_files
			
# 	def on_hyunjang_search(self):
# 		현장명 =  WidManager.get_value( self.inputDict['현장명'] )

# 		try:

# 			app_dict = INFO.APP_권한_MAP_ID_TO_APP[61]
# 			from modules.PyQt.compoent_v2.dlg_dict_selectable_table import DictTableSelectorDialog	

# 			url = app_dict.get('api_uri') + app_dict.get('api_url') + f"?search={현장명}&page_size=100"
# 			_isOk, _json = APP.API.getlist(url)
# 			if _isOk:
# 				datas = _json.pop('results', [])
# 				pagination = _json
# 				logger.debug(f"검색 결과 pagination : {pagination}")
# 				logger.debug(f"검색결과 datas : {len(datas)}")
# 				if pagination.get('countTotal') > 100:
# 					Utils.generate_QMsg_critical(self, title='경고', text="검색 결과가 많읍니다. <br>검색 조건을 좁히세요.")
# 				else:
# 					dlg = DictTableSelectorDialog(
# 							None, 
# 							datas=datas, 
# 							attrNames= [ '건물명', '건물주소_찾기용','수량','운행층수','최초설치일자' ]
# 						)
# 					dlg.setMinimumSize(1200, 1200)
# 					if dlg.exec():
# 						selected_data = dlg.get_selected()
# 						if selected_data:
# 							WidManager.set_value(self.inputDict['현장명'], selected_data.get('건물명'))
# 							WidManager.set_value(self.inputDict['현장주소'], selected_data.get('건물주소_찾기용'))
# 							WidManager.set_value(self.inputDict['el수량'], selected_data.get('수량'))
# 							WidManager.set_value(self.inputDict['운행층수'], selected_data.get('운행층수'))
# 							self.el_info_fk = selected_data.get('id')

# 						logger.debug(f"선택된 데이터 : {selected_data}")
# 			else:
# 				raise ValueError(f"검색 실패 : {_json}")
# 		except Exception as e:
# 			Utils.generate_QMsg_critical(self, title='경고', text="검색 권한이 없읍니다. <br>관리자에게 문의바랍니다.")
# 			logger.error(f"on_search : {e}")
# 			logger.error(traceback.format_exc())
# 			return
		
# 		# 	from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import 한국정보__for_Tab
# 		# 	dlg = QDialog(self)
# 		# 	hLayout = QVBoxLayout()
			
# 		# 	if app_dict.get('id') in INFO.APP_MAP_ID_TO_AppWidget :
# 		# 		wid = INFO.APP_MAP_ID_TO_AppWidget[app_dict.get('id')]
# 		# 		if wid is not None:
# 		# 			hLayout.addWidget(wid)
# 		# 		else:
# 		# 			raise ValueError(f"wid is not found in INFO.APP_MAP_ID_TO_AppWidget : {app_dict.get('id')}")		
# 		# 	else:
# 		# 		wid = 한국정보__for_Tab(
# 		# 			dlg, 
# 		# 			**app_dict,
# 		# 			table_name=f"{app_dict.get('div')}_{app_dict.get('name')}_appID_{app_dict.get('id')}"
# 		# 			)
# 		# 		wid.run()
# 		# 		INFO.APP_MAP_ID_TO_AppWidget[app_dict.get('id')] = wid
# 		# 		hLayout.addWidget(wid)
# 		# 	dlg.setLayout(hLayout)
# 		# 	dlg.setWindowTitle( 'MOD 현장명 검색')
# 		# 	dlg.setMinimumSize( 600, 1200)
# 		# 	if dlg.exec():
# 		# 		pass
# 		# except Exception as e:
# 		# 	logger.error(f"on_search : {e}")
# 		# 	logger.error(traceback.format_exc())
# 		# 	return
	
# 	def on_select_Elevator_Company(self):
# 		""" PB_El_Company 클릭시 호출 , dialog 호출 후 선택된 값을 _update_El_company 호출 """
# 		self.handle_widget_for_label_pb('Elevator사')

	
# 	def on_select_NCR_Type(self):
# 		""" PB_NCR_Type 클릭시 호출 , dialog 호출 후 선택된 값을 _update_NCR_Type 호출 """
# 		self.handle_widget_for_label_pb('부적합유형')


# 	def handle_widget_for_label_pb(self, attrName:str):
# 		_isok, _list = APP.API.getlist(self._url_list_for_label_pb[attrName]+'?page_size=0')
# 		if _isok:
# 			dlg = Dialog_list_edit(self, title=f'{attrName} 선택', _list=_list, is_sorting=False)
# 			if dlg.exec():
# 				selected_item = dlg.get_value()
# 				Object_Set_Value(self.inputDict[attrName], selected_item)
# 		else:
# 			Utils.generate_QMsg_critical(self, '경고', f'{attrName} 선택 실패')
# 			return []

		
# 	def on_add_claim_file(self):
# 		pass


from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS관리__for_stacked_Table, CS관리__for_Tab

class CS등록__for_stacked_Table( Base_Stacked_Table ):

	def create_active_table(self):
		return Wid_table(self)


class CS등록__for_Tab( CS관리__for_Tab ):
	no_edit_columns_by_coding = ['id', 'el_info_fk','등록자_fk', '등록자','등록일', '완료자_fk','완료자','완료일' ,
									'claim_file_수','action_수', 'claim_files_ids', 'claim_files_url',
									'activty_files_ids', 'activty_files_url', 'activty_files_수',
								]

	edit_mode = 'row' ### 'row' | 'cell' | 'None'
	is_no_config_initial = True		### table config 없음
	skip_generate = [
		'id', 'el_info_fk','등록자_fk', '등록자','등록일', '완료자_fk','완료자','완료일' ,
		'claim_file_수','action_수', 'claim_files_ids', 'claim_files_url',
		'activty_files_ids', 'activty_files_url', 'activty_files_수',
	]
	custom_editor_info = {}

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = CS등록__for_stacked_Table(self)
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		### view 선택 combo 삽입		
		self.pb_form = QPushButton("클레임 프로젝트 추가")
		self.ui.h_search.addWidget(self.pb_form)
		self.pb_form.clicked.connect( self.on_claim_project )

		self.pb_claim_open = QPushButton("클레임 Open")
		self.ui.h_search.addWidget(self.pb_claim_open)
		self.pb_claim_open.clicked.connect( self.on_claim_open )
		self.pb_claim_open.setDisabled(True)

		self.PB_Map_View = QPushButton("지도보기")
		self.ui.h_search.addWidget(self.PB_Map_View)
		self.PB_Map_View.clicked.connect( self.on_map_view )



	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
		self.event_bus.subscribe(f"{self.table_name}:data_deleted", self.on_data_deleted)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_datas_changed(self, api_datas:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_datas_changed : {len(api_datas)}")

	def on_data_deleted(self, is_deleted:bool):
		if is_deleted:
			self.selected_rows = []
			self.pb_claim_open.setDisabled(True)

	def on_selected_rows(self, selected_rows:list[dict]):
		super().on_selected_rows(selected_rows)
		self.pb_claim_open.setDisabled(False)

	def on_claim_open(self):
		self.event_bus.publish(f"{self.table_name}:request_claim_open", self.selected_rows)

	# def on_selected_rows(self, selected_rows:list[dict]):
	# 	logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
	# 	logger.debug(f" api_datas : {self.api_datas}")
	# 	self.selected_rows = selected_rows

	# def on_map_view(self):
	# 	if self.selected_rows:
	# 		try:
	# 			address = self.selected_rows[0]['현장주소']
	# 			dlg = Dialog_Folium_Map(self, address)
	# 			dlg.exec()
	# 		except Exception as e:
	# 			logger.error(f"on_map_view : {e}")
	# 			logger.error(traceback.format_exc())
	# 			QMessageBox.warning(self, "경고", "pc 설정이 지도보기를 지원하지 않읍니다.")
	# 	else:
	# 		QMessageBox.warning(self, "경고", "선택된 행이 없읍니다.")

	# def on_claim_project(self):
	# 	### 클레임 프로젝트 Dialog 호출
	# 	dataObj = self.selected_rows[0] if self.selected_rows and self.selected_rows[0] else {'id':-1}
		
	# 	try:
	# 		if hasattr(self, 'table_name') and self.table_name:
	# 			logger.info(f"table_name : {self.table_name}")
	# 			table_config = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_TableConfig', {})
	# 			inputType = table_config.get('_column_types')
	# 			##### custom
	# 			inputType['claim_files'] = 'MultiFileField'
	# 			if not inputType:
	# 				raise ValueError(f"inputType is not found in {self.table_name}")
	# 			logger.info(f"inputType : {inputType}")
	# 	except Exception as e:
	# 		logger.error(f"on_claim_project : {e}")
	# 		logger.error(traceback.format_exc())
	# 		return


	# 	form = CS_Project_Form(
	# 		parent=self, 						
	# 		url = self.url,
	# 		win_title='고객불만_요청_관리',
	# 		inputType= inputType, #self.appData._get_form_type(),
	# 		title= '고객불만_요청_관리',		
	# 		dataObj = dataObj,
	# 		skip_generate=self.skip_generate,
	# 		order_attrNames= ['현장명', '현장주소', 'el수량','운행층수','Elevator사','부적합유형', '불만요청사항', '고객명','고객연락처','차수','claim_files','진행현황','완료요청일',]
	# 		)
	# 	if form.exec():
	# 		resultObj = form.get_api_result()

	# 		logger.debug(f"resultObj : {resultObj}")



		# form = CS_활동현황_Form(
		# 	parent=self,
		# 	url=self.url,
		# 	win_title='고객불만_활동추가',
		# 	inputType={},
		# 	title= '고객불만_활동추가',		
		# )
		# form.exec()





















# from PyQt6 import QtCore, QtGui, QtWidgets
# from PyQt6.QtWidgets import *
# from PyQt6.QtCore import *
# from PyQt6.QtGui import *
# from typing import TypeAlias

# import pandas as pd
# import urllib
# from datetime import date, datetime, timedelta
# import copy

# import pathlib
# import openpyxl
# import typing

# import concurrent.futures
# import asyncio
# import time


# ### 😀😀 user : ui...
# from modules.PyQt.Tabs.품질경영.ui.Ui_tab_품질경영_CS관리 import Ui_Tab_App as Ui_Tab
# ###################
# from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
# from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_activity import Dlg_CS_Activity

# from modules.user.utils_qwidget import Utils_QWidget
# from modules.PyQt.User.toast import User_Toast
# from config import Config as APP
# from modules.user.async_api import Async_API_SH
# from info import Info_SW as INFO
# import modules.user.utils as Utils
# 

# from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

# from icecream import ic
# import traceback
# from modules.logging_config import get_plugin_logger

# ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
# if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
# 	ic.enable()
# else :
# 	ic.disable()


# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()

# class Dialog_조회조건(Dialog_Base_조회조건):
#     def __init__(self, parent, **kwargs):
#         super().__init__(parent, **kwargs)

# class Dlg_FileViewer(QDialog):

# 	def __init__(self, parent, paths:list[str]):
# 		super().__init__(parent)
# 		from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer
# 		self.paths = paths
# 		self.dlg = QDialog()
# 		vLayout = QVBoxLayout()
# 		wid = Wid_FileViewer( paths=self.paths)
# 		vLayout.addWidget ( wid )
# 		self.dlg.setLayout(vLayout)
# 		self.dlg.show()

# class CS관리__for_Tab( QWidget, Utils_QWidget):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent )
		
# 		self.is_Auto_조회_Start = True
# 		self.selected_rows:list[dict] = []
# 		self.판금처_list_dict:list[dict] = []
# 		self.param = ''		
# 		self.defaultParam = f"page_size=25"
# 		self.기타조회조건 = {}
# 		self.기타조회조건_for_param = {}
# 		self._init_kwargs(**kwargs)

# 		self.ui = Ui_Tab()
# 		self.ui.setupUi(self)
# 		self._ui_custom()
# 		self.ui.comboBox_EL_Company.addItems( ['ALL'] + self._get_Elevator사list() )		

# 		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=self.기타조회조건)

# 		self.triggerConnect()
		
# 		if hasattr(self, 'url_db_fields') and self.url_db_fields :
# 			self._get_DB_Field(self.url_db_fields  )	
# 			#### db filed에 update 하기 위해서 여기 위치	

					
		

# 		self._init_helpPage()

# 		if self.is_Auto_조회_Start :
# 			self.slot_search_for(self.param if self.param else self.defaultParam )
	
# 	def _ui_custom(self):
# 		self.info_title = getattr(self, 'info_title',None) or "관리자를 위한 화면"
# 		# 기본 날짜 설정
# 		today = QDate.currentDate()
# 		self.ui.dateEdit_From.setDate(today)
# 		self.ui.dateEdit_To.setDate(today)
# 		self.ui.frame_Period.setVisible(False)

# 		self.ui.comboBox_pageSize.addItems( ['ALL'] + ['25', '50', '100'] )
# 		self.ui.comboBox_pageSize.setCurrentText('25')

# 		self._set_info_title(self.info_title)
# 		# self.ui.label_target.setText( self.info_title )


# 	def triggerConnect(self):
# 		#### checkBox 체크 여부에 따라 조회조건 설정
# 		# 체크박스 상태에 따라 frame_Period 보이기/숨기기
# 		self.ui.checkBox_Jaksung.stateChanged.connect(lambda: self.ui.frame_Period.setVisible(self.ui.checkBox_Jaksung.isChecked()))
		
# 		self.ui.PB_Search.clicked.connect(lambda: self.slot_search_for(self._get_param()) )
# 		self.ui.PB_Search_Condition.clicked.connect(  self.slot_search_condition )
# 		self.ui.PB_Search_Condition.search_conditions_cleared.connect(	lambda: setattr(self,'기타조회조건',{}) )

# 		###  등록,배포,처리완료 pb 연결
# 		self.ui.PB_New.clicked.connect(lambda: self.slot_new())
# 		self.ui.PB_Open.clicked.connect(lambda: self.slot_open())
# 		self.ui.PB_Edit.clicked.connect(lambda: self.slot_edit())
# 		self.ui.PB_Del.clicked.connect(lambda: self.slot_del())
# 		self.ui.PB_Activity.clicked.connect(lambda: self.slot_activity_New())
# 		self.ui.PB_Activity_View.clicked.connect(lambda: self.slot_activity_View())
# 		self.ui.PB_Complete.clicked.connect(lambda: self.slot_complete())

# 		# self.ui.pb_info.clicked.connect(lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))		
# 		self.ui.pb_info.clicked.connect(lambda: Dlg_FileViewer(self, paths=[self.help_page]))

# 		self.ui.wid_pagination.signal_currentPage_changed.connect(lambda page_no: self.slot_search_for(self.param + f"&page={page_no}"))
# 		self.ui.wid_pagination.signal_download.connect(lambda: self.save_data_to_file(is_Pagenation=True, _isOk=True, api_datas=self.api_datas))

# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Edit.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Activity_View.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Open.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Del.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Complete.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Activity.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: self.ui.PB_Activity_View.setEnabled(len(select_list) > 0))
# 		self.ui.Wid_Table.signal_select_rows.connect(lambda select_list: setattr(self, 'selected_rows', select_list))
		

# 	def _get_param(self):
# 		param_list = []
# 		if ( value := self.ui.lineEdit_search.text() ) :
# 			param_list.append ( f'search={value}' )
# 		if ( value := self.ui.comboBox_EL_Company.currentText() ) != 'ALL':
# 			param_list.append ( f'Elevator사={value}' )

# 		if self.ui.checkBox_Jaksung.isChecked():
# 			param_list.append ( f'작성일_From={self.ui.dateEdit_From.date().toString("yyyy-MM-dd")}' )
# 			param_list.append ( f'작성일_To={self.ui.dateEdit_To.date().toString("yyyy-MM-dd")}' )

# 		if (value := self.ui.comboBox_pageSize.currentText() ) != 'ALL':
# 			param_list.append ( f'page_size={value}' )
# 		else:
# 			param_list.append ( f'page_size=0' )

# 		param = '&'.join(param_list)
# 		return param

# 	### 조회조건 설정
# 	@pyqtSlot()
# 	def slot_search_condition(self):
# 		검색조건 = {
# 			'진행현황' : 'QRadioButton',
# 			'부적합유형' : 'QLineEdit',
# 			'차수' : 'Range_SpinBox',
# 			'el수량' : 'Range_SpinBox',
# 			'등록자' : 'QLineEdit',
# 			'등록일' : 'Range_DateEdit',
# 			'완료일' : 'Range_DateEdit',
# 			'완료자' : 'QLineEdit',
# 			'활동현황' : 'QLineEdit',
# 			'품질비용' : 'Range_SpinBox',
# 		}

# 		default_dict = {
# 			'진행현황' : 'ALL',
# 			'차수' : {'From':1, 'To':10},
# 			'el수량' : {'From':1, 'To':100},
# 			'품질비용' : {'From':1, 'To':100000000},
# 			'등록일' : {'From':datetime.now().date() + timedelta(days=-7), 'To':datetime.now().date() + timedelta(days=7)},
# 			'완료일' : {'From':datetime.now().date() + timedelta(days=-7), 'To':datetime.now().date() + timedelta(days=7)},

# 		}

# 		config_kwargs = {
# 			'radios' : {
# 				'진행현황' : ['ALL', 'Open', 'Close' ],
# 			}
# 		}
# 		_default_dict = self.기타조회조건 if self.기타조회조건 else default_dict
# 		### ALL인 경우 self.기타조회조건은 삭제되므로, 기본값을 넣어줌.
# 		if '진행현황' not in _default_dict :
# 			_default_dict['진행현황'] = 'ALL'

# 		dlg = Dialog_조회조건(
# 				self, 
# 				input_dict = 검색조건, 
# 				default_dict = _default_dict , 
# 				title = '조회조건 설정', 
# 				config_kwargs = config_kwargs
# 				)
# 		dlg.result_signal.connect( self.slot_update_etc_search_condition )


# 	@pyqtSlot(dict)
# 	def slot_update_etc_search_condition(self, 기타조회조건:dict):
# 		"""
# 			dialog_조회조건에서 조회조건 설정 후, 확인 버튼 클릭 시 호출됨.
# 		"""
# 		ic(기타조회조건)
# 		self.기타조회조건 = 기타조회조건
# 		def _convert_to_dict(기타조회조건: dict) -> dict:
# 			converted_dict = {}
# 			for key, value in 기타조회조건.items():
# 				if isinstance(value, dict) and 'From' in value and 'To' in value:
# 					converted_dict[f"{key}_From"] = value['From']
# 					converted_dict[f"{key}_To"] = value['To']
# 				else:
# 					converted_dict[key] = value
# 			return converted_dict

# 		self.기타조회조건_for_param = _convert_to_dict(기타조회조건)
# 		self.ui.PB_Search_Condition.update_kwargs(기타조회조건=기타조회조건)



# 	def _get_sendData(self, rowDict:dict, status:str) -> dict:
# 		sendData = {}
# 		sendData['상태'] = status
# 		sendData['처리시간'] = datetime.now()
# 		sendData['처리자'] = INFO.USERID
# 		return sendData

# 	#### app마다 update 할 것.😄
# 	def run(self):
		
# 		return 
	
# 	def _get_Elevator사list(self):
# 		is_ok, _json = APP.API.getlist(INFO.URL_CS_CLAIM_GET_ELEVATOR사)
# 		if is_ok:
# 			return _json
# 		else:
# 			return ['현대', 'OTIS', 'TKE']
		
# 	def _get_부적합유형list(self):
# 		is_ok, _json = APP.API.getlist(INFO.URL_CS_CLAIM_GET_부적합유형)
# 		if is_ok:
# 			return _json
# 		else:
# 			return ['현대', 'OTIS', 'TKE']

# 	@pyqtSlot()
# 	def slot_new(self):
# 		dataObj = { 'id' : -1 , '등록자_fk' : INFO.USERID }
# 		dlg = Dlg_CS_등록(self, self.url, dataObj=dataObj, Elevator사list=self._get_Elevator사list(), 부적합유형list=self._get_부적합유형list() )
# 		dlg.signal_ok.connect( lambda data_dict: self.slot_new_ok(data_dict))	

# 	def _diable_pb(self):
# 		self.selected_rows = []
# 		self.ui.PB_Edit.setEnabled(False)
# 		self.ui.PB_Del.setEnabled(False)
# 		self.ui.PB_Open.setEnabled(False)
# 		self.ui.PB_Complete.setEnabled(False)
# 		self.ui.PB_Activity.setEnabled(False)
# 		self.ui.PB_Activity_View.setEnabled(False)

# 	@pyqtSlot(dict, object)
# 	def slot_new_ok(self, data_dict:dict):
# 		self.api_datas.insert(0, data_dict)  # 맨 첫 번째에 data_dict 추가
# 		self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 		self._diable_pb()

		

# 	@pyqtSlot()
# 	def slot_edit(self):
# 		dataObj = self.selected_rows[0]
# 		dlg = Dlg_CS_등록(self, self.url, dataObj=dataObj, Elevator사list=self._get_Elevator사list(), 부적합유형list=self._get_부적합유형list() )
# 		dlg.signal_ok.connect( lambda data_dict: self.slot_edit_ok(data_dict))	

# 	@pyqtSlot(dict)
# 	def slot_edit_ok(self, data_dict:dict):

# 		for index, item in enumerate(self.api_datas):
# 			if item['id'] == data_dict['id']:
# 				self.api_datas[index] = data_dict
# 				break	

# 		self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 		self._diable_pb()

# 	@pyqtSlot()
# 	def slot_del(self):
# 		dataObj = self.selected_rows[0]
# 		dlg_res_button = Utils.generate_QMsg_question(self, title='CS Claim 삭제', text='삭제하시겠습니까?')
# 		if dlg_res_button != QMessageBox.StandardButton.Ok :
# 			return 
# 		if APP.API.delete(self.url+ str(dataObj['id']) ):
# 			self.api_datas.remove(dataObj)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 			self._diable_pb()
# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	@pyqtSlot()
# 	def slot_open(self):
# 		dataObj = self.selected_rows[0]
# 		dataObj['진행현황'] = 'Open'
# 		dlg_res_button = Utils.generate_QMsg_question(
# 			self, 
# 			title='CS Claim 배포',
# 			text = f"현장명 : {dataObj.get('현장명')}\n"
# 					+f"현장주소 : {dataObj.get('현장주소')}\n"
# 					+f"고객명 : {dataObj.get('고객명')}\n"
# 					+f"불만요청사항 : {dataObj.get('불만요청사항')}\n"
# 					+f"고객연락처 : {dataObj.get('고객연락처')}\n"
# 					+f"배포하시겠습니까?"
# 			)
# 		if dlg_res_button != QMessageBox.StandardButton.Ok :
# 			return 
		
# 		_sendData = {'진행현황':'Open', '등록일':datetime.now(), '등록자_fk':INFO.USERID }
# 		_isOk, _json = APP.API.Send(self.url, dataObj, _sendData )
# 		if _isOk:
# 			for index, item in enumerate(self.api_datas):
# 				if item['id'] == _json['id']:
# 					self.api_datas[index] = _json
# 					break	
# 			Utils.generate_QMsg_Information(self, title='CS Claim 배포', text='배포 완료', autoClose=1000)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 			self._diable_pb()
# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	@pyqtSlot()
# 	def slot_activity_New(self):
# 		dataObj = self.selected_rows[0]
# 		dlg = Dlg_CS_Activity(self, INFO.URL_CS_ACTIVITY, dataObj={'id':-1, 'claim_fk':dataObj['id']} )
# 		dlg.signal_ok.connect( lambda data_dict: self.slot_activity_New_ok(data_dict))	

# 	@pyqtSlot(dict)
# 	def slot_activity_New_ok(self, data_dict:dict):
# 		_isok, _jsonDict = APP.API.getObj_byURL( self.url + f"{data_dict['claim_fk']}")
# 		if _isok:
# 			for index, item in enumerate(self.api_datas):
# 				if item['id'] == _jsonDict['id']:
# 					self.api_datas[index] = _jsonDict
# 					break	
# 			Utils.generate_QMsg_Information(self, title='CS 활동 등록', text='CS 활동 등록 완료', autoClose=1000)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	@pyqtSlot()
# 	def slot_activity_View(self):
		
# 		dataObj = self.selected_rows[0]
# 		_param = f"?claim_fk={dataObj['id']}&page_size=0"
# 		is_ok1, _json = APP.API.getlist( INFO.URL_CS_ACTIVITY + _param)
# 		is_ok2,  _db_fields = APP.API.getAPI_View(url=INFO.URL_DB_Field_CS_ACTIVITY)
# 		# is_ok2, _db_field = APP.API.get( INFO.URL_DB_Field_CS_ACTIVITY )
# 		if is_ok1 and is_ok2:
# 			ic ( _db_fields )
# 			ic ( _json )
# 			from modules.PyQt.Tabs.품질경영.tables.table_품질경영_CS_Activity import Wid_Table_for_품질경영_CS_Activity			
# 			dlg = QDialog(self)
# 			hLayout = QVBoxLayout()
# 			wid = Wid_Table_for_품질경영_CS_Activity(dlg)
# 			wid._update_data (
# 				url=INFO.URL_CS_ACTIVITY,
# 				api_data = _json,
# 				**_db_fields,
# 				)
# 			hLayout.addWidget(wid)
# 			dlg.setLayout(hLayout)
# 			dlg.exec_()

# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	@pyqtSlot()
# 	def slot_complete(self):
# 		dataObj = self.selected_rows[0]
		
# 		dlg_res_button = Utils.generate_QMsg_question(
# 			self, 
# 			title='CS Claim 처리완료',
# 			text = f"현장명 : {dataObj.get('현장명')}\n"
# 					+f"현장주소 : {dataObj.get('현장주소')}\n"
# 					+f"고객명 : {dataObj.get('고객명')}\n"
# 					+f"불만요청사항 : {dataObj.get('불만요청사항')}\n"
# 					+f"고객연락처 : {dataObj.get('고객연락처')}\n"
# 					+f"처리완료하시겠습니까?"
# 			)
# 		if dlg_res_button != QMessageBox.StandardButton.Ok :
# 			return 
# 		_sendData = {'진행현황':'Close', '완료일':datetime.now(), '완료자_fk':INFO.USERID }
# 		_isOk, _json = APP.API.Send(self.url, dataObj, _sendData )
# 		if _isOk:
# 			for index, item in enumerate(self.api_datas):
# 				if item['id'] == _json['id']:
# 					self.api_datas[index] = _json
# 					break	
# 			Utils.generate_QMsg_Information(self, title='CS Claim 처리완료', text='처리완료로 종료합니다.', autoClose=1000)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 			self._diable_pb()
# 		else:
# 			Utils.generate_QMsg_critical(self)

# 	def _get_selected_row_생산지시서_ID(self) -> int:
# 		# 선택된 행 정보 가져오기
# 		return self.ui.Wid_Table.view_selected_row()

# 	@pyqtSlot(str)
# 	def slot_search_for(self, param:str) :
# 		"""
# 		결론적으로 main 함수임.
# 		Wid_Search_for에서 query param를 받아서, api get list 후,
# 		table에 _update함.	
# 		"""
# 		self.loading_start_animation()	

# 		if self.기타조회조건 and self.기타조회조건_for_param :
# 			param = param + '&' + '&'.join( [ f'{key}={value}' for key, value in self.기타조회조건_for_param.items() ] )

# 		self.param = param 
		
# 		url = self.url + '?' + param
# 		ic(url)

# 		###😀 GUI FREEZE 방지 ㅜㅜ;;
# 		pool = QThreadPool.globalInstance()
# 		self.work = Worker(url)
# 		self.work.signal_worker_finished.signal.connect ( self.table_update )
# 		pool.start( self.work )



# 	@pyqtSlot(bool, bool, object)
# 	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
# 		# ic ( is_Pagenation, _isOk, api_datas )
# 		if not _isOk:
# 			self._disconnect_signal (self.work.signal_worker_finished)
# 			self.loading_stop_animation()
# 			Utils.generate_QMsg_critical(self)
# 			return 

# 		if is_Pagenation :
# 			search_result_info:dict = copy.deepcopy(api_datas)
# 			self.api_datas = search_result_info.pop('results')
# 			self.ui.wid_pagination._update_Pagination( is_Pagenation, **search_result_info )
# 		else:
# 			self.api_datas = api_datas
# 			self.ui.wid_pagination._update_Pagination( is_Pagenation, countTotal=len(api_datas) )
		
# 		if len(self.api_datas) == 0:
# 			self.ui.Wid_Table.hide()
# 			if not hasattr(self.ui, 'label_table_empty'):
# 				self.ui.label_table_empty = QLabel('데이터가 없읍니다.')
# 				self.ui.label_table_empty.setAlignment(Qt.AlignCenter)
# 				self.ui.main_frame.layout().addWidget(self.ui.label_table_empty)
# 				self.ui.main_frame.setStyleSheet("background-color: #f0f0f0;")
# 				self._disconnect_signal (self.work.signal_worker_finished)
# 				self.loading_stop_animation()
# 			return
# 				# self.api_datas = self._generate_default_api_datas()
# 		else:
# 			self.ui.Wid_Table.show()
# 			if hasattr(self.ui, 'label_table_empty'):
# 				self.ui.label_table_empty.setParent(None)
# 				self.ui.label_table_empty.deleteLater()
# 				delattr(self.ui, 'label_table_empty')
# 				self.ui.main_frame.setStyleSheet("")

# 		self._update_update_time()   ### table 업데이트 시간 업데이트
# 		self.ui.Wid_Table._update_data(
# 			api_data=self.api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
# 			url = self.url,
# 			**self.db_fields,			
# 			# table_header = 
# 		)	

# 		self._disconnect_signal (self.work.signal_worker_finished)
# 		self.loading_stop_animation()

# 	def _update_table_by_ws_auto(self, api_datas:list[dict], _text:str|None=None):
# 		self._update_update_time(_text)
# 		self.ui.Wid_Table._update_data(
# 			api_data=api_datas,
# 			url = self.url,
# 			**self.db_fields,
# 		)
	
# 	def _generate_default_api_datas(self) ->list[dict]:		
# 		table_header:list[str] = self.db_fields['table_config']['table_header']
# 		obj = {}
# 		for header in table_header:
# 			if header == 'id' : obj[header] = -1
# 			else:
# 				match self.fields_model.get(header, '').lower():
# 					case 'charfield'|'textfield':
# 						obj[header] = ''
# 					case 'integerfield'|'floatfield':
# 						obj[header] = 0
# 					case 'datetimefield':
# 						# return QDateTime.currentDateTime().addDays(3)
# 						obj[header] =  datetime.now()
# 					case 'datefield':
# 						# return QDate.currentDate().addDays(3)
# 						obj[header] =  datetime.now().date()
# 					case 'timefield':
# 						# return QTime.currentTime()
# 						obj[header] = datetime.now().time()
# 					case _:
# 						obj[header] = ''
# 		return [ obj ]




# from PyQt6 import QtCore, QtGui, QtWidgets
# from PyQt6.QtWidgets import *
# from PyQt6.QtCore import *
# from PyQt6.QtGui import *
# from typing import TypeAlias

# import pandas as pd
# import urllib
# from datetime import date, datetime, timedelta
# import copy

# import pathlib
# import openpyxl
# import typing

# import concurrent.futures
# import asyncio
# import time


# from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import CS관리__for_Tab
# ### 😀😀 user : ui...
# from modules.PyQt.Tabs.품질경영.ui.Ui_tab_품질경영_CS관리 import Ui_Tab_App as Ui_Tab
# ###################
# from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
# from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_activity import Dlg_CS_Activity

# from modules.user.utils_qwidget import Utils_QWidget
# from modules.PyQt.User.toast import User_Toast
# from config import Config as APP
# from modules.user.async_api import Async_API_SH
# from info import Info_SW as INFO
# import modules.user.utils as Utils
# 

# from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

# from icecream import ic
# import traceback
# from modules.logging_config import get_plugin_logger

# ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
# if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
# 	ic.enable()
# else :
# 	ic.disable()


# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()

# class Dialog_조회조건(Dialog_Base_조회조건):
#     def __init__(self, parent, **kwargs):
#         super().__init__(parent, **kwargs)

# class CS등록__for_Tab( CS관리__for_Tab ):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent, appFullName, **kwargs )

# 		self._init_CS등록()

# 	def _init_CS등록(self):
# 		self.ui.PB_Activity.hide()
# 		self.ui.PB_Activity_View.hide()
# 		self.ui.PB_Complete.hide()

# 	@pyqtSlot()
# 	def slot_open(self):
# 		""" 사용자 경우, open 버튼 click시, 
# 			정상 : self.api_datas에서 해당 데이터를 삭제함	
# 			비정상 : 메시지 출력
# 		"""
# 		dataObj = self.selected_rows[0]
# 		dataObj['진행현황'] = 'Open'
# 		dlg_res_button = Utils.generate_QMsg_question(
# 			self, 
# 			title='CS Claim 배포',
# 			text = f"현장명 : {dataObj.get('현장명')}\n"
# 					+f"현장주소 : {dataObj.get('현장주소')}\n"
# 					+f"고객명 : {dataObj.get('고객명')}\n"
# 					+f"불만요청사항 : {dataObj.get('불만요청사항')}\n"
# 					+f"고객연락처 : {dataObj.get('고객연락처')}\n"
# 					+f"배포하시겠습니까?"
# 			)
# 		if dlg_res_button != QMessageBox.StandardButton.Ok :
# 			return 
		
# 		_sendData = {'진행현황':'Open', '등록일':datetime.now(), '등록자_fk':INFO.USERID }
# 		_isOk, _json = APP.API.Send(self.url, dataObj, _sendData )
# 		if _isOk:
# 			for index, item in enumerate(self.api_datas):
# 				if item['id'] == _json['id']:
# 					# {{ edit_1 }}: 해당 항목 삭제
# 					del self.api_datas[index]
# 					break	
# 			Utils.generate_QMsg_Information(self, title='CS Claim 배포', text='배포 완료', autoClose=1000)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 			self._diable_pb()
# 		else:
# 			Utils.generate_QMsg_critical(self)
