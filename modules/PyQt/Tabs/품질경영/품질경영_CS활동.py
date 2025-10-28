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

from modules.PyQt.Tabs.품질경영.tables.Wid_table_품질경영_CS_Activity import Wid_table_품질경영_CS_Activity as Wid_table

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


class CS_Project_Activity_Form(Base_Form_Dialog):
	minium_size = (600, 600)
	# _url_list_for_label_pb = {
	# 	'Elevator사': INFO.URL_CS_CLAIM_GET_ELEVATOR사,
	# 	'부적합유형': INFO.URL_CS_CLAIM_GET_부적합유형,
	# }

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

	def on_save(self):

		if self.url and self.inputDict:
			sendData, sendFiles = self.get_send_data()
			id = sendData.pop('id')
			_isOk, _json = APP.API.Send(
				url=self.url, 
				dataObj = {'id': id}, 
				sendData = sendData,
				sendFiles = sendFiles
				)
			if _isOk:
				Utils.generate_QMsg_Information(None, title='저장 완료', text='저장 완료', autoClose=1000)
				self.api_send_result = _json
				self.accept()
			else:
				logger.error(f"저장 실패: {_json}")
				QMessageBox.warning(self, "경고", "저장 실패")
		else:
			logger.error(f"저장 실패: {self.url}")
			QMessageBox.warning(self, "경고", "저장 실패")
			
	def get_send_data(self):
		""" override """
		send_data, send_files = super().get_send_data()
		send_data['id'] = -1
		send_data['claim_fk'] = self.dataObj.get('id')
		send_data['등록자_fk'] = INFO.USERID
		send_data['활동일'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		send_data['등록일'] = send_data['활동일']

		### drf 와 연동되는 것으로, 파일 전송 시 파일 경로와 파일 아이디를 따로 보내야 함.
		keyNamesFile = 'activity_files'
		if keyNamesFile in send_data:
			send_files_dict_list = send_data.pop(keyNamesFile)
			file_paths = [ item.get('file') for item in send_files_dict_list  if item.get('type') == 'local']
			send_files = [
    			(keyNamesFile, (open(path, "rb"))) for path in file_paths
			]
			claim_files_ids = [ item.get('id') for item in send_files_dict_list  if item.get('type') == 'server']
			send_data['claim_files_ids'] = claim_files_ids
		logger.debug(f"send_data : {send_data}")
		
		return send_data, send_files
			
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

class CS활동__for_stacked_Table( Base_Stacked_Table ):

	def create_active_table(self):
		return Wid_table(self)


class CS활동__for_Tab( CS관리__for_Tab ):
	is_no_config_initial = True		### table config 없음
	skip_generate = [
		'id', 'el_info_fk','등록자_fk', '등록자','등록일', '완료자_fk','완료자','완료일' ,
		'claim_file_수','action_수', 'claim_files_ids', 'claim_files_url',
		'activty_files_ids', 'activty_files_url', 'activty_files_수',
	]

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = CS활동__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		### view 선택 combo 삽입		
		self.pb_form = QPushButton("클레임 Activity 추가")
		self.ui.h_search.addWidget(self.pb_form)
		self.pb_form.clicked.connect( self.on_claim_project_activity )

		self.pb_claim_close = QPushButton("클레임 Close")
		self.ui.h_search.addWidget(self.pb_claim_close)
		self.pb_claim_close.clicked.connect( self.on_claim_close )
		self.pb_claim_close.setDisabled(True)

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
			self.pb_claim_close.setDisabled(True)

	def on_selected_rows(self, selected_rows:list[dict]):
		super().on_selected_rows(selected_rows)
		self.pb_claim_close.setDisabled(False)

	def on_claim_project_activity(self):
		logger.debug(f"on_claim_project_activity : {self.selected_rows}")

		dataObj = self.selected_rows[0] if self.selected_rows and self.selected_rows[0] else {'id':-1}

		inputType = {
			'활동현황': 'TextField',
			'activity_files': 'MultiFileField',
		}
		
		form = CS_Project_Activity_Form(
			parent=self, 						
			url = INFO.URL_CS_ACTIVITY,
			win_title=f'{dataObj.get("현장명")} Claim 활동 등록',
			inputType= inputType, #self.appData._get_form_type(),
			title= f'{dataObj.get("현장명")} Claim 활동 등록',		
			dataObj = dataObj,
			skip_generate=self.skip_generate,
			order_attrNames= ['활동현황', 'activity_files',]
			)
		if form.exec():			
			resultObj = form.get_api_result()
			if resultObj:
				self.event_bus.publish(f"AppID:{self.id}_{GBus.SEARCH_REQUESTED}",  self.param)

	def on_claim_close(self):
		"""
		 	사용자 경우, activity_Complete 버튼 click시, 
			정상 : 	self.api_datas에서 해당 데이터를 삭제함	
			비정상 : 메시지 출력
		"""
		# super().slot_complte()
		if not self.selected_rows or not isinstance(self.selected_rows, list) or not isinstance(self.selected_rows[0], dict):
			return
		dataObj = self.selected_rows[0]
		
		dlg_res_button = Utils.generate_QMsg_question(
			self, 
			title='CS Claim 처리완료',
			text = f"현장명 : {dataObj.get('현장명')}\n"
					+f"현장주소 : {dataObj.get('현장주소')}\n"
					+f"고객명 : {dataObj.get('고객명')}\n"
					+f"불만요청사항 : {dataObj.get('불만요청사항')}\n"
					+f"고객연락처 : {dataObj.get('고객연락처')}\n"
					+f"처리완료하시겠습니까?"
			)
		if dlg_res_button != QMessageBox.StandardButton.Ok :
			return 
		_sendData = {'진행현황':'Close', '완료일':datetime.now(), '완료자_fk':INFO.USERID }
		_isOk, _json = APP.API.Send(self.url, dataObj, _sendData )
		if _isOk:
			self.event_bus.publish(f"AppID:{self.id}_{GBus.SEARCH_REQUESTED}",  self.param)
			Utils.generate_QMsg_Information(self, title='CS Claim 처리완료', text='처리완료로 종료합니다.', autoClose=1000)

			self.selected_rows = []
			self.pb_claim_close.setDisabled(True)

		else:
			Utils.generate_QMsg_critical(self, title='CS Claim 처리 실패', text='처리완료 실패')









































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

# class CS활동__for_Tab( CS관리__for_Tab ):
# 	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
# 		super().__init__( parent, appFullName, **kwargs )

# 		self._init_CS활동()

# 	def _init_CS활동(self):
# 		self.ui.PB_New.hide()
# 		self.ui.PB_Edit.hide()
# 		self.ui.PB_Del.hide()
# 		self.ui.PB_Open.hide()
# 		### activate push button
# 		self.ui.PB_Activity.show()
# 		self.ui.PB_Activity_View.show()
# 		self.ui.PB_Complete.show()

# 		self.ui.PB_Activity.setDisabled(True)
# 		self.ui.PB_Activity_View.setDisabled(True)
# 		self.ui.PB_Complete.setDisabled(True)
		

# 	@pyqtSlot()
# 	def slot_activity_New(self):
# 		"""
# 		 	사용자 경우, activity_New 버튼 click시, 

# 		"""
# 		super().slot_activity_New()

# 	@pyqtSlot()
# 	def slot_activity_View(self):
# 		"""
# 		 	사용자 경우, activity_View 버튼 click시, 
# 		"""
# 		super().slot_activity_View()

# 	@pyqtSlot()
# 	def slot_complete(self):
# 		"""
# 		 	사용자 경우, activity_Complete 버튼 click시, 
# 			정상 : 	self.api_datas에서 해당 데이터를 삭제함	
# 			비정상 : 메시지 출력
# 		"""
# 		# super().slot_complte()
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
# 					# {{ edit_1 }}: 해당 항목 삭제
# 					del self.api_datas[index]
# 					break	
# 			Utils.generate_QMsg_Information(self, title='CS Claim 처리완료', text='처리완료로 종료합니다.', autoClose=1000)
# 			self.ui.Wid_Table._update_data(api_data=self.api_datas, url=self.url)
# 			self._diable_pb()
# 		else:
# 			Utils.generate_QMsg_critical(self)

