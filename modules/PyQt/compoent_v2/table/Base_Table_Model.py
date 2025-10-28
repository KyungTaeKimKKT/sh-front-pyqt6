from __future__ import annotations
from typing import Optional, TYPE_CHECKING,  Any, Union, Callable
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6 import sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table.table_mixin import TableConfigMixin, TableMenuMixin
from modules.PyQt.compoent_v2.table.Base_Table_Model_Role_Mixin import Base_Table_Model_Role_Mixin, CustomRoles
from modules.PyQt.compoent_v2.table.mixin_create_config import Mixin_Create_Config
from modules.envs.api_urls import API_URLS
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import pandas as pd

import time
import datetime
import json, copy
import traceback
import os
from modules.logging_config import get_plugin_logger

if TYPE_CHECKING:
	from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Base_Table_Model_Mixin:

	def on_new_row(self, **kwargs):
		self.request_add_row(rowNo=0, **kwargs)

	def on_copy_new_row(self, rowDict:dict, **kwargs):
		rowNo = self._data.index(rowDict)
		self.request_add_row(rowNo=rowNo, **kwargs)

	def on_delete_row(self, rowDict:dict, **kwargs):
		rowNo = self._data.index(rowDict)
		self.request_delete_row(rowNo=rowNo, **kwargs)

	def request_new_row(self:Base_Table_Model, **kwargs):
		if self.rowCount() > 0:
			self.request_add_row(rowNo=0, **kwargs)
		else:
			self.request_add_row(
				rowNo=0, 
				copyed_rowDict=kwargs.get('new_default_dict',{}), 
				**kwargs
				)
			


	def request_copy_new_row(self, rowDict:dict, **kwargs):
		rowNo = self._data.index(rowDict)
		self.request_add_row(rowNo=rowNo, **kwargs)

	def request_add_row(
			self, 
			rowNo:Optional[int] = None, 
			dlg_question: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			dlg_info: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			dlg_critical: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			copyed_rowDict: Optional[dict] = None,
			api_send: bool = True,
			):
		logger.info(f"{self.__class__.__name__} : request_add_row : {rowNo} {dlg_question} {dlg_info} {dlg_critical}")
		if dlg_question is not None:
			if dlg_question() != QMessageBox.StandardButton.Ok:
				return
		try:	
			if copyed_rowDict is None:	
				copyed_row = self.copy_row(
					rowNo, 
					**self.add_row_dict,
				)
			else:
				copyed_row = copyed_rowDict

		# api send 및 model, view 업데이트
			if api_send:
				self.mixin_api_add_row(rowNo, copyed_row)
				if dlg_info:
					dlg_info()
			else:
				self.mixin_add_row_data(rowNo, copyed_row)

		except Exception as e:
			logger.error(f"request_add_row: {e}")
			logger.error(f"{traceback.format_exc()}")
			if dlg_critical:	
				dlg_critical()

	request_on_add_row = request_add_row

	def request_delete_row(
			self, 
			rowNo:int | None = None, 
			dlg_question: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			dlg_info: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			dlg_critical: Optional[Callable[[], QMessageBox.StandardButton]] = None,
			rowObj: Optional[dict] = None,
			) -> bool:
		"""
		dlg_question: 삭제 여부 물어보는 대화창 : lambda:Utils.generate_QMsg_question(None, title="삭제 여부", text="삭제하시겠습니까?")
		dlg_info: 삭제 성공 대화창 : lambda:Utils.generate_QMsg_Information(None, title="삭제 성공", text="삭제 성공", autoClose=1000)
		dlg_critical: 삭제 실패 대화창 : lambda:Utils.generate_QMsg_critical(None, title="삭제 실패", text="삭제 실패")
		rowObj: 삭제할 행 데이터==> 우선순위가 높음 : dict
		"""
		if dlg_question is not None and callable(dlg_question):
			result = dlg_question()
			if isinstance(result, QMessageBox.StandardButton):
				if result != QMessageBox.StandardButton.Ok:
					return
			elif isinstance(result, bool):
				if not result:
					return
			else:
				raise ValueError(f"request_delete_row: dlg_question 함수의 반환 값이 올바르지 않습니다. 반환 값: {result}, 타입: {type(result)}")

		try:
			if rowObj is not None:
				id = rowObj['id']	
				rowNo = self._data.index(rowObj)
			else:
				id = self._data[rowNo]['id']	
			print(f"request_delete_row: {id}, {rowNo}")
			if id > 0:
				_isOk = self.mixin_api_delete_row(id)	
				if _isOk:			
					self.delete_row_and_emit(rowNo)
					self.event_bus.publish(f"{self.table_name}:data_deleted", True)
					if dlg_info and callable(dlg_info):
						dlg_info()
				else:
					raise Exception(f"API 호출 실패: {_isOk}")
			else:
				self.delete_row_and_emit(rowNo)
			return True
		except Exception as e:
			logger.error(f"request_delete_row: {e}")
			logger.error(f"{traceback.format_exc()}")
			if dlg_critical and callable(dlg_critical):
				dlg_critical()
			return False

	request_on_delete_row = request_delete_row

	def delete_row_and_emit(self, rowNo:int):
		self.beginRemoveRows(QModelIndex(), rowNo, rowNo)
		self._data.pop(rowNo)
		self.endRemoveRows()
		self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])
		### 데이터가 없으면 empty_data 이벤트 발생
		if not self._data:
			self.event_bus.publish(f"{self.table_name}:empty_data", True)

	def request_file_view(self, rowNo:int, colNo:int):
		""" file view 시 호출되는 함수 """
		logger.info(f"request_on_file_view: {rowNo}, {colNo}")  
		attribute_name = self.get_field_name_by_display_name( self._headers[colNo])
		data = self._data[rowNo][attribute_name]
		from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
		dlg = FileViewer_Dialog(self.parent())
		dlg.add_file(data)
		dlg.exec()

	request_on_file_view = request_file_view

	def request_file_download(self, rowNo:int, colNo:int):
		""" file download 시 호출되는 함수 """
		logger.info(f"request_on_file_download: {rowNo}, {colNo}")  
		attribute_name = self.get_field_name_by_column_no ( colNo)
		data = self._data[rowNo][attribute_name]
		Utils.func_filedownload(data)

	request_on_file_download = request_file_download

	def request_file_delete(self, rowNo:int, colNo:int):
		""" file delete 시 호출되는 함수 """

		logger.info(f"request_on_file_delete: {rowNo}, {colNo}")  
		attribute_name = self.get_field_name_by_display_name( self._headers[colNo])
		
		#### json 형태로 None ==> DRF는 JSONParser 처리함.
		is_ok, _json = APP.API.Send_json( url= self.url,
										dataObj=  self._data[rowNo],
										sendData= { attribute_name: None }
										)
		if is_ok:
			self.update_row_data(rowNo, _json)
		else:
			Utils.generate_QMsg_critical(None, title="파일 삭제 실패", text="파일 삭제 실패")
	
	request_on_file_delete = request_file_delete

	def mixin_api_delete_row(self:Base_Table_Model, id:int):
		""" 행 삭제 후 데이터 저장 """
		_isOk = APP.API.delete(self.url + f"{id}")
		if _isOk:
			return True
		else:
			raise Exception(f"API 호출 실패: {_isOk}")

	def mixin_api_add_row(self:Base_Table_Model, rowNo:int, dataObj:dict):
		""" 행 추가 후 데이터 저장 """
		_isOk, _json = APP.API.Send(url= self.url,  dataObj=dataObj, sendData=dataObj )
		if _isOk:
			self.mixin_add_row_data(rowNo, _json)
		else:
			raise Exception(f"API 호출 실패: {_json}")    
		
	def mixin_add_row_data(self:Base_Table_Model, rowNo:int, dataObj:dict):
		""" 행 업데이트 후 데이터 저장 """
		self.beginInsertRows(QModelIndex(), rowNo, rowNo)
		self._data.insert(rowNo, dataObj)    
		self.endInsertRows()
		self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])


	def mixin_sort_by_display_role(self:Base_Table_Model, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
		""" display role 기준으로 정렬 """
		index_func = lambda row_idx: self.index(row_idx, column)
		key_func = lambda row_idx: self.data(index_func(row_idx), Qt.ItemDataRole.DisplayRole) or ""
		reverse = order == Qt.SortOrder.DescendingOrder

		try:
			row_indices = list(range(len(self._data)))
			row_indices.sort(key=key_func, reverse=reverse)
			self._data = [self._data[i] for i in row_indices]
		except Exception as e:
			print(f"정렬 오류: {e}")
		self.layoutChanged.emit()

class Base_Table_Model( LazyParentAttrMixin,
					    QAbstractTableModel, 
						Base_Table_Model_Role_Mixin, 
						Base_Table_Model_Mixin,
						Mixin_Create_Config,
						):
	"""확장성과 유연성이 개선된 기본 테이블 모델 클래스"""
	Roles = CustomRoles
	# 시그널 정의
	user_data_changed = pyqtSignal(bool) ### bool: 데이터의 유무 : 있으면 True, 없으면 False
	cell_clicked = pyqtSignal(int, int, object)  # row, col, value
	selection_changed = pyqtSignal(list)  # selected indices
	
	def __init__(self, parent=None, **kwargs):
		"""
        kwargs로 모델 속성을 초기화할 수 있는 생성자
        
        가능한 kwargs:
        - _headers: 컬럼 헤더 리스트
        - _data: 테이블 데이터 2차원 리스트
        - _header_types: 컬럼 타입 딕셔너리
        - _formatters: 컬럼별 포맷터 함수 딕셔너리
        - _validators: 컬럼별 유효성 검사 함수 딕셔너리
        - _decorators: 컬럼별 장식 함수 딕셔너리
        - _style_rules: 스타일 규칙 함수 리스트
        - _edit_rules: 편집 가능 여부 규칙 함수 리스트
        - _sort_rules: 컬럼별 정렬 함수 딕셔너리
        - _filter_rules: 컬럼별 필터링 함수 딕셔너리
        - context_menu_actions: 컨텍스트 메뉴 액션 딕셔너리
        """
		super().__init__(parent)
		self.lazy_attr_names = INFO.Table_Model_Lazy_Attr_Names # ['APP_ID', 'no_edit_columns_by_coding', 'edit_mode']
		self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
		self.lazy_ready_flags: dict[str, bool] = {}
		self.lazy_attr_values: dict[str, Any] = {}

		###✅ 25-07-03 추가
		self._created_id = -1 #### 계속 증가시침	
		self.start_init_time = time.perf_counter()
		self.event_bus = event_bus
		self.table_name = ''
		self.table_config = {}
		self._table_view :Optional[Base_Table_View] = None

		self._fieldname_to_col_index_cache = {}  # ✅ 캐시 딕셔너리
		
		# 기본 데이터
		self.api_datas :list[dict] = []
		self.prev_api_datas :list[dict] = []

		self._headers :list[str] = []
		self._headers_api_datas :list[str] = []
		self._data :list[list] = []				#### ✅ tableview 기준 data
		self._original_data :list[list] = []		#### ✅ db 기준 data => db 데이터 변경 시 deepcopy 해서 저장
		self._header_types :dict = {}
		
		# 편집 모드 설정 (초기값은 lazy_attr_values 에서 가져오고, 이후 변경시 update 함)
		self._edit_mode :str = 'row'  ### 'row' or 'cell' or 'None'

		# 변경된 셀/행 표시를 위한 속성 추가
		self._modified_cells = {}  # {(row, col): timer} 형태로 저장
		self._modified_rows = set()  # 변경된 행 인덱스 집합

		# 동적 규칙 저장소
		self._formatters :dict = {}  # 컬럼별 데이터 포맷 함수
		self._validators :dict = {}  # 컬럼별 데이터 유효성 검사 함수
		self._decorators :dict = {}  # 컬럼별 장식 함수        if self.lazy_ready_flags.get(attr_name):

		self._style_rules :list[callable] = []  # 스타일 규칙 함수 목록
		self._edit_rules :list[callable] = []  # 편집 가능 여부 규칙 함수 목록
		self._sort_rules :dict = {}  # 컬럼별 정렬 함수
		self._filter_rules :dict = {}  # 컬럼별 필터링 함수
		self._context_menu_actions :dict = {}  # 컨텍스트 메뉴 액션
		
		# 스타일 관련 속성 추가
		self._background_colors :dict = {}  # 컬럼별 배경색
		self._foreground_colors :dict = {}  # 컬럼별 글자색
		self._fonts :dict = {}  # 컬럼별 폰트
		self._text_alignments :dict = {}  # 컬럼별 텍스트 정렬
		self._tooltips :dict = {}  # 컬럼별 툴팁

		# 필터링 및 정렬 상태
		self._filtered_data :list[list] = []
		self._is_filtered :bool = False
		self._sort_column :int = -1
		self._sort_order :Qt.SortOrder = Qt.AscendingOrder


		# kwargs로 초기화
		if kwargs:
			self.kwargs = kwargs
			self._initialize_from_kwargs(**kwargs)

		self.run_lazy_attr()

	@property
	def created_id(self):
		"""  초기 -1 이후 계속 -2, -3 씩 증가시킴"""
		self._created_id -= 1
		return self._created_id
		
	def _initialize_from_kwargs(self, **kwargs):
		"""kwargs로부터 모델 속성 초기화"""
		if 'headers' in kwargs:
			self.set_headers(kwargs['headers'])
			
		if 'data' in kwargs:
			self.set_data(kwargs['data'])
			
		if 'header_types' in kwargs:
			self.set_header_types(kwargs['header_types'])
			
		if 'formatters' in kwargs:
			self.set_formatters(kwargs['formatters'])
			
		if 'validators' in kwargs:
			self.set_validators(kwargs['validators'])
			
		if 'decorators' in kwargs:
			self.set_decorators(kwargs['decorators'])
			
		if 'style_rules' in kwargs:
			self.set_style_rules(kwargs['style_rules'])
			
		if 'edit_rules' in kwargs:
			self.set_edit_rules(kwargs['edit_rules'])
			
		if 'sort_rules' in kwargs:
			self.set_sort_rules(kwargs['sort_rules'])
			
		if 'filter_rules' in kwargs:
			self.set_filter_rules(kwargs['filter_rules'])
			
		if 'context_menu_actions' in kwargs:
			self.set_context_menu_actions(kwargs['context_menu_actions'])

				# 스타일 관련 속성 초기화 추가
		if 'background_colors' in kwargs:
			self.set_background_colors(kwargs['background_colors'])
			
		if 'foreground_colors' in kwargs:
			self.set_foreground_colors(kwargs['foreground_colors'])
			
		if 'fonts' in kwargs:
			self.set_fonts(kwargs['fonts'])
			
		if 'text_alignments' in kwargs:
			self.set_text_alignments(kwargs['text_alignments'])
			
		if 'tooltips' in kwargs:
			self.set_tooltips(kwargs['tooltips'])

	def closeEvent(self, event):
		self.unsubscribe_gbus()
		super().closeEvent(event)
	
	def on_all_lazy_attrs_ready(self):		
		try:
			APP_ID = self.lazy_attr_values['APP_ID']
			self.table_name = Utils.get_table_name(APP_ID)
			self.appDict = copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
			if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
				self.url = Utils.get_api_url_from_appDict(self.appDict)

			if self.mixin_check_config_data():
				self.table_config = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig'])
				self.table_config_api_datas = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas'])
				self.on_table_config_refresh(False)
			self.subscribe_gbus()

		except Exception as e:
			logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			Utils.generate_QMsg_critical(None, title="서버 조회 오류", text="on_all_lazy_attrs_ready 오류" )
			# raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")

	def on_table_config_refresh(self, is_refresh:bool=True):
		""" table_config 적용 """
		try:
			if is_refresh:
				if not self.check_table_config_changed():
					return
				else:
					self.table_config = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig'])
					self.table_config_api_datas = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas'])
			self.map_display_name_to_obj = { obj['display_name']: obj for obj in self.table_config_api_datas }
			self._header_types = self.table_config.get('_headers_types', {})
			self._headers = self.table_config['_headers']
			self.layoutChanged.emit()

		except Exception as e:
			logger.error(f"on_table_config 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"on_table_config 오류: {e}")
	
	def check_table_config_changed(self):
		""" table_config 변경 시 True 반환 """
		if self.table_config != INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig']:
			return True
		if self.table_config_api_datas != INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas']:
			return True
		return False
		
	def on_api_datas_received(self, api_datas:list[dict]):
		""" gbus subscribe 된 api_datas 받아오면 호출되는 함수 """
		self.api_datas = copy.deepcopy(api_datas)
		#### ✅ 257-3 추가
		self.map_id_to_rowData = { rowData['id']: rowData for rowData in api_datas  if 'id' in rowData}
		self._original_data = copy.deepcopy(api_datas)
		self._data = api_datas
		# if hasattr(self, '_modified_rows'):
		# 	self.clear_all_modifications()

		if self.mixin_check_config_data():
			self.layoutChanged.emit()			
		else:
			self.table_config, self.table_config_api_datas = self.mixin_create_config(api_datas)
			print (f"self._data : {self._data}")
			print(f"self.table_config : {self.table_config}")
			print(f"self.table_config_api_datas : {self.table_config_api_datas}")
			self.on_table_config_refresh(True)
		

	

	def subscribe_gbus(self):

		self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.on_api_datas_received )
		self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
		self.event_bus.subscribe(f"{self.table_name}:custom_editor_complete", self.on_custom_editor_complete)
		# self.event_bus.subscribe(f"{self.table_name}:edit_mode", self.on_edit_mode)

		self.event_bus.subscribe( f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", self.on_request_download_from_pagination )
		self.event_bus.subscribe( f"{self.table_name}:request_excel_export", self.on_request_excel_export )
		# self.event_bus.subscribe( f"{self.table_name}:table_config_api_datas", self.on_table_config_api_datas )

	def unsubscribe_gbus(self):
		try:
			self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.on_api_datas_received  )
			self.event_bus.unsubscribe( f"{self.table_name}:table_config", self.on_table_config )
			self.event_bus.unsubscribe( f"{self.table_name}:custom_editor_complete", self.on_custom_editor_complete )
			self.event_bus.unsubscribe( f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", self.on_request_download_from_pagination )
		except Exception as e:
			logger.error(f"unsubscribe_gbus 오류: {e}")
			logger.error(f"traceback: {traceback.format_exc()}")
	
	def on_edit_mode(self, edit_mode:str):
		# Utils.generate_QMsg_Information(None, title="edit_mode 변경", text=f"edit_mode 변경 : {edit_mode}", autoClose=1000 )
		self.lazy_attr_values['edit_mode'] = edit_mode

	def on_request_download_from_pagination(self, is_download:bool):
		if 'TableConfigMode' in self.__class__.__name__:
			return
		if is_download and self.api_datas:
			self.data_to_excel_only_visible_columns()



	
	def on_custom_editor_complete(self, data:dict):
		""" 사용자 선택 에디터 완료 시 호출되는 함수 
			data : { 'index':index, 'value':value }
		"""
		try:
			logger.debug(f"on_custom_editor_complete: {data}")
			self.setData(data['index'], data['value'], role=Qt.ItemDataRole.EditRole)
		except Exception as e:
			logger.debug(f"on_custom_editor_complete 오류: {self.parent().__class__.__name__}")
			logger.error(f"on_custom_editor_complete 오류: {e}")
			logger.error(f"traceback: {traceback.format_exc()}")


			

	### getters : table_config 에서 가져오기
	def get_table_view(self) -> Optional[Base_Table_View]:
		return self._table_view
	
	def get_table_config(self) -> dict:
		return self.table_config
	
	def get_headers(self) -> list[str]:
		return self.table_config.get('_headers', [])
	
	def get_data(self) -> list[list]:
		return self._data
	
	def get_header_types(self) -> dict[str, str]:
		return self.table_config.get('_headers_types', {})
	
	def get_hidden_columns(self) -> list[int]:
		return self.table_config.get('_hidden_columns', [])
	
	def get_no_edit_cols(self) -> list[int]:
		return self.table_config.get('_no_edit_cols', [])
	

	### 신규 함수	
	def get_attrName_from_display(self, display_name:str) -> str:
		return self.table_config['_mapping_display_to_attr'][display_name]
	
	def get_displayName_from_attr(self, attrName:str) -> dict:
		return self.table_config['_mapping_attr_to_display'][attrName]	

		
	def get_field_name_by_index(self, index:QModelIndex) -> str:
		display_name = self.get_headers()[index.column()]
		return self.get_attrName_from_display(display_name)
	
	def get_attr_name_by_column_no(self, column_no:int) -> str:
		display_name = self.get_headers()[column_no]
		return self.get_attrName_from_display(display_name)
	
	get_attr_name_by_index = get_field_name_by_index
	
	def get_field_name_by_column_no(self, column_no:int) -> str:
		display_name = self.get_headers()[column_no]
		return self.get_attrName_from_display(display_name)

	def get_display_name_by_index(self, index:QModelIndex) -> str:
		display_name = self.get_headers()[index.column()]
		return self.get_displayName_from_attr(display_name)
	

	def index_from_row_col(self, row: int, col: int) -> QModelIndex:
		return self.index(row, col)
	

	def is_db_id(self, rowNo:int) -> bool:
		""" None, "", -1 은 False, """
		id_value = self._data[rowNo]['id']
		if id_value is None or id_value == "" or id_value == -1:
			return False		
		if isinstance(id_value, int) and id_value > 0:
			return True


	####
	
	def run(self):
		return 


	### utils method

	# def api_send(self, url:str=None, dataObj:dict=None, sendData:dict=None):
	# 	""" api 호출 함수 """
	# 	send_url = url or self.url
	# 	time_start = time.perf_counter()
	# 	_isok, _json = APP.API.Send ( url=send_url, dataObj=dataObj, sendData=sendData )
	# 	self.event_bus.publish_trace_time( { 'Action': f"{url} send", 'Duration':time.perf_counter() - time_start })
	# 	if _isok:
	# 		Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
	# 		return _isok, _json
	# 	else:
	# 		Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
	# 		return _isok, None


	# # def create_model_data_by_row(self, obj:dict) -> list:
	# # 	""" obj를 table row data로 변환 """
	# # 	try:
	# # 		reverse_headers = self.get_mapping_reverse_headers()
	# # 		# logger.debug(f"{self.__class__.__name__} | create_model_data_by_row | obj : {obj}")
	# # 		# logger.debug(f"{self.__class__.__name__} | create_model_data_by_row | self.get_headers() : {self.get_headers()}")
	# # 		# logger.debug(f"{self.__class__.__name__} | create_model_data_by_row | reverse_headers : {reverse_headers}")	
	# # 		return [ obj.get( reverse_headers[display_headname], '') 
	# # 	  			for display_headname in self.get_headers() ]
	# # 	except Exception as e:
	# # 		logger.error(f"{self.__class__.__name__} : create_model_data_by_row 오류: {e}")
	# # 		logger.error(f"{traceback.format_exc()}")
	# # 		return []
	
	# def apply_api_datas(self, api_datas:list[dict]):
	# 	""" api_datas를 model의 _data에 적용 """
	# 	logger.debug(f"{self.__class__.__name__} | apply_api_datas | api_datas : {len(api_datas)} row 적용시작 ")
	# 	self.set_api_datas(api_datas=copy.deepcopy(api_datas))
    	
	# 	# 모델 데이터 생성
	# 	model_datas = []
	# 	headers:Optional[list[str]] = None
	# 	if self._table_view.check_api_datas_available():
	# 		logger.debug(f"{self.__class__.__name__} | apply_api_datas | api_datas : No config 적용시작 ")
	# 		if api_datas:
	# 			logger.debug(f"{self.__class__.__name__} | apply_api_datas | api_datas : {api_datas[0]} ")
	# 			headers = list(api_datas[0].keys())
	# 			self.table_config['_headers'] = headers
	# 			self._headers = headers
	# 			self._headers_api_datas = headers
	# 			for obj in api_datas:
	# 				model_datas.append( [ obj.get(key, '') for key in headers ] )
	# 		else:
	# 			return False
	# 	else:
	# 		logger.debug(f"{self.__class__.__name__} | apply_api_datas | api_datas : Table config 적용시작 ")
	# 		if api_datas:
	# 			headers = self.get_headers()
	# 			for obj in api_datas:
	# 				model_datas.append(self.create_model_data_by_row(obj))
	# 		else:
	# 			return False

	# 	# 데이터 변경 시작을 알림
	# 	logger.debug(f"apply_api_datas : model_datas 및 beginResetModel 시작 ")
	# 	if sip.isdeleted(self):
	# 		logger.debug(f"apply_api_datas : model_datas 및 beginResetModel 종료 : sip.isdeleted(self) ")
	# 		return False
	# 	self.beginResetModel()		
	# 	# 데이터 설정
	# 	# logger.debug(f"apply_api_datas : model_datas : {(model_datas)} 적용됨 ")
	# 	self._data = model_datas	
	# 	self._original_data = copy.deepcopy(model_datas)
	# 	if headers:
	# 		logger.debug(f"apply_api_datas : headers : {(headers)} 적용됨 ")
	# 		self._headers = headers
	# 	else:
	# 		logger.debug(f"apply_api_datas : headers :  headers 없음 ")
	# 		return False
		
	# 	# 필터링된 데이터도 업데이트
	# 	if self._is_filtered:
	# 		self._filtered_data = self._data.copy()
	# 		# 필터 다시 적용 (필요한 경우)
	# 		# self.filter_data(self._current_filter_criteria)
		
	# 	# 정렬 상태 유지 (필요한 경우)
	# 	if hasattr(self, '_sort_column') and self._sort_column >= 0:
	# 		self.sort(self._sort_column, self._sort_order)
	
	# # 데이터 변경 완료를 알림
	# 	self.endResetModel()

	# 	# self._table_view.apply_table_config()
		
	# 	channel_name = f"{self.table_name}:apply_table_config"	

	# 	구독자수 = self.event_bus.publish(channel_name, True)
	# 	logger.debug(f"{self.__class__.__name__} | apply_api_datas | 구독자수 : {구독자수} | channel_name : {channel_name}")
	# 	# 데이터 변경 시그널 발생
	# 	self.user_data_changed.emit(self.is_datas())
	# 	top_left = self.index(0, 0)
	# 	bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
	# 	self.dataChanged.emit(top_left, bottom_right)
		
	# 	return True


	# setters
	def set_api_datas(self, api_datas:list[dict]):
		""" self.prev_api_datas 와 self.api_datas 를 교환 """
		self.prev_api_datas = self.api_datas
		self.api_datas = api_datas


	def set_headers(self, headers: list[str]):
		self._headers = headers
		self.layoutChanged.emit()
		
	def set_data(self, data: list[any]):
		self._data = data
		self._filtered_data = data.copy() if self._is_filtered else []
		self.layoutChanged.emit()

	def set_table_config(self, table_config: dict):
		self._table_config = table_config
		for key, value in table_config.items():
			setattr(self, key, value)
		return self

	def set_table_config_api_datas(self, api_datas: list[dict]):
		self._table_config_api_datas = api_datas
		return self

	def set_header_types(self, types: dict[str, str]):
		self._header_types = types

	def set_hidden_columns(self, columns: list[int]):
		""" column index 로 숨김 설정 """
		logger.info(f"set_hidden_columns : {columns}")
		self._hidden_columns = columns
		# 실제로 테이블 뷰에 적용하는 로직 추가
		if self._table_view:
			for col_idx in columns:
				self._table_view.setColumnHidden(col_idx, True)
		self.layoutChanged.emit()
		
	def set_no_edit_cols(self, columns: list[str]):
		"""편집 불가능한 컬럼 설정
		
		Args:
			columns: 편집 불가능하게 설정할 컬럼 이름 목록
		"""
		self._no_edit_cols = columns
		self.layoutChanged.emit()
	
	def set_column_widths(self, column_widths: dict[str, int]):
		self._column_widths = column_widths or self._column_widths
		if self._table_view and self._column_widths:
			for col_name, width in self._column_widths.items():
				col_idx = self._headers.index(col_name)
				# 모든 컬럼은 사용자가 조정 가능하도록 Interactive 모드로 설정
				self._table_view.horizontalHeader().setSectionResizeMode(
					col_idx, QHeaderView.ResizeMode.Interactive)
				
				if width == 0:
					# 초기 너비를 내용에 맞게 자동 조정
					self._table_view.resizeColumnToContents(col_idx)
				else:
					# 지정된 초기 너비 설정
					self._table_view.setColumnWidth(col_idx, width)
			self.layoutChanged.emit()

	def set_column_types(self, types: dict[str, str]):
		self._column_types = types		
		
	def set_column_styles(self, styles: dict[str, str]):
		self._column_styles = styles
		if self._table_view and self._column_styles:
			for col_name, style in self._column_styles.items():
				col_idx = self._headers.index(col_name)
				self._table_view.setStyleSheet(f"QHeaderView::section {{ {style} }}")
			self.layoutChanged.emit()

	def set_edit_mode(self, mode:str):
		self._edit_mode = mode

	def set_formatters(self, formatters: dict[str, callable]):
		self._formatters = formatters
		
	def set_validators(self, validators: dict[str, callable]):
		self._validators = validators
		
	def set_decorators(self, decorators: dict[str, callable]):
		self._decorators = decorators
		
	def set_style_rules(self, rules: list[callable]):
		self._style_rules = rules
		
	def set_edit_rules(self, rules: list[callable]):
		self._edit_rules = rules
		
	def set_sort_rules(self, rules: dict[str, callable]):
		self._sort_rules = rules
		
	def set_filter_rules(self, rules: dict[str, callable]):
		self._filter_rules = rules
		
	def set_context_menu_actions(self, actions: dict[str, callable]):
		self._context_menu_actions = actions

	def set_background_colors(self, colors: dict[str, QColor]):
		"""컬럼별 배경색 설정"""
		self._background_colors = colors
		self.layoutChanged.emit()
		
	def set_foreground_colors(self, colors: dict[str, QColor]):
		"""컬럼별 글자색 설정"""
		self._foreground_colors = colors
		self.layoutChanged.emit()
		
	def set_fonts(self, fonts: dict[str, QFont]):
		"""컬럼별 폰트 설정"""
		self._fonts = fonts
		self.layoutChanged.emit()
		
	def set_text_alignments(self, alignments: dict[str, Qt.ItemDataRole.TextAlignmentRole]):
		"""컬럼별 텍스트 정렬 설정"""
		self._text_alignments = alignments
		self.layoutChanged.emit()
		
	def set_tooltips(self, tooltips: dict[str, str]):
		"""컬럼별 툴팁 설정"""
		self._tooltips = tooltips

	def set_table_style(self, style: str):		
		self._table_style = style
		if self._table_view and style:
			self._table_view.setStyleSheet(style)
			self.layoutChanged.emit()

	def set_table_view(self, table_view:QTableView):
		self._table_view = table_view


	def set_Table_name(self, table_name:str):
		self.table_name = table_name
		
	# 동적 규칙 추가 메서드
	def add_formatter(self, column_name: str, formatter: callable):
		self._formatters[column_name] = formatter
		self.layoutChanged.emit()
		
	def add_validator(self, column_name: str, validator: callable):
		self._validators[column_name] = validator
		
	def add_decorator(self, column_name: str, decorator: callable):
		self._decorators[column_name] = decorator
		self.layoutChanged.emit()
		
	def add_style_rule(self, rule: callable):
		self._style_rules.append(rule)
		
	def add_edit_rule(self, rule: callable):
		self._edit_rules.append(rule)
		
	def add_sort_rule(self, column_name: str, sort_func: callable):
		self._sort_rules[column_name] = sort_func
		
	def add_filter_rule(self, column_name: str, filter_func: callable):
		self._filter_rules[column_name] = filter_func
		
	def add_context_menu_action(self, action_name: str, action_func: callable):
		self._context_menu_actions[action_name] = action_func
	
	def add_background_color(self, column_name: str, color: QColor):
		"""특정 컬럼의 배경색 추가"""
		self._background_colors[column_name] = color
		self.layoutChanged.emit()
		
	def add_foreground_color(self, column_name: str, color: QColor):
		"""특정 컬럼의 글자색 추가"""
		self._foreground_colors[column_name] = color
		self.layoutChanged.emit()
		
	def add_font(self, column_name: str, font: QFont):
		"""특정 컬럼의 폰트 추가"""
		self._fonts[column_name] = font
		self.layoutChanged.emit()
		
	def add_text_alignment(self, column_name: str, alignment: Qt.ItemDataRole.TextAlignmentRole):
		"""특정 컬럼의 텍스트 정렬 추가"""
		self._text_alignments[column_name] = alignment
		self.layoutChanged.emit()
		
	def add_tooltip(self, column_name: str, tooltip: str):
		"""특정 컬럼의 툴팁 추가"""
		self._tooltips[column_name] = tooltip
		
	# QAbstractTableModel 필수 메서드 구현
	def rowCount(self, parent:QModelIndex=None):
		return len(self._filtered_data) if self._is_filtered else len(self._data)
		
	def columnCount(self, parent:QModelIndex=None):
		return len(self._headers)

	def headerData(self, section:int, orientation:Qt.Orientation, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
		if role == Qt.ItemDataRole.DisplayRole:
			if orientation == Qt.Orientation.Vertical:
				return str(section+1)
			if orientation == Qt.Orientation.Horizontal:
				if 0 <= section < len(self._headers):
					return self._headers[section]
		if role == Qt.ItemDataRole.ToolTipRole:
			if INFO.USERID == 1 and orientation == Qt.Orientation.Horizontal:
				if 0 <= section < len(self._headers):
					display_name = self._headers[section]
					db_attr_name = self.get_attrName_from_display(display_name)
					return db_attr_name
		return None
	
	def _is_equivalent_values(self, value1, value2):
		"""두 값이 동등한지 비교하는 메서드
		
		문자열 타입에서는 None, null, 빈 문자열('')을 동등하게 처리
		"""
		# 두 값이 정확히 같으면 동등
		if value1 == value2:
			return True
		
		# 문자열 타입 처리
		if isinstance(value1, str) or isinstance(value2, str):
			# None, 'null', 빈 문자열을 동등하게 처리
			empty_values = [None, 'null', 'NULL', 'None', 'NONE', '']
			return (value1 in empty_values and value2 in empty_values)
		
		return False
	
	def update_row_data(self, rowNo:int, value:Any):
		""" Row data 갱신"""
		old_value = self._data[rowNo]
		self._data[rowNo] = value
		#### ✅ 25-7-3 추가
		self.map_id_to_rowData = { rowData['id'] : rowData for rowData in self._data  if 'id' in rowData }
		start_col = 0
		end_col = len(self._headers) - 1
		self.dataChanged.emit(self.index(rowNo, start_col), self.index(rowNo, end_col), [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])


	def update_cell_data(self, index:QModelIndex, value:Any):
		""" Cell data 갱신"""
		row = index.row()
		col = index.column()
		old_value = self._data[row][col]
		
		# 값이 실제로 변경되었는지 확인 (개선된 비교 로직 사용)
		if self._is_equivalent_values(old_value, value):
			return False  # 값이 변경되지 않았으면 False 반환
		
		self._data[row][col] = value
		self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
		
		# 변경된 셀/행 표시
		if self._edit_mode.lower() == 'cell':
			self._mark_cell_as_modified(row, col)
		elif self._edit_mode.lower() == 'row':
			self._mark_row_as_modified(row)
		
		self.user_data_changed.emit(self.is_datas())
		
		return True

		
	def data(self, index:QModelIndex, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
		if not index.isValid():
			return None
			
		row = index.row()
		col = index.column()
		# 데이터 범위 확인
		data_list = self._filtered_data if self._is_filtered else self._data
		if row < 0 or row >= len(data_list) or col < 0 or col >= len(self._headers):
			return None
		
		if role == Qt.ItemDataRole.UserRole:
			return self._data[row]

		return self.role_data(row, col, role)
	

	
	def setHeaderData(self, section:int, orientation:Qt.Orientation, value, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
		if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
			if 0 <= section < len(self._headers):
				self._headers[section] = value
				self.layoutChanged.emit()

	def on_api_send_By_Row(self):
		""" 행 단위 저장 ==> requested by wid_table_header : signal로 연결됨."""
		logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
		if self._modified_rows:
			for row in list(self._modified_rows):
				_isok, _json = 	APP.API.Send_json(url= self.url, 
								dataObj= self._data[row],
								sendData=self._data[row]
								)
				if _isok:
					self.update_row_data(row, _json)
					Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
					self.clear_modified_rows([row])

				else:
					Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
					return False
			return True
		else:
			return False
		
	def on_api_send_By_Row_with_file(self, file_field_name:str):
		""" 행 단위 저장 시 파일 첨부 

			Base_Table_Model 은 파일 첨부 없이 저장함.
			여기서는 파일 첨부 처리함.
		"""
		logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
		if self._modified_rows:
			for row in list(self._modified_rows):
				# sendData, sendFiles = self.get_sendData_and_sendFiles(self.get_row_data(row), ['help_page'])
				sendData, sendFiles = self.get_sendData_and_sendFiles(self._data[row], [file_field_name])
				logger.info(f"sendData: {sendData}")
				logger.info(f"sendFiles: {sendFiles}")                
				_isok, _json = 	APP.API.Send(url= self.url, 
								dataObj=  self._data[row],
								sendData=sendData,
								sendFiles=sendFiles
								)
				if _isok:
					# self.update_api_response( _json )
					self.update_row_data(row, _json)
					Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
					self.clear_modified_rows([row])
				else:
					Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
					return False
			return True
		else:
			return False
		
	def get_sendData_and_sendFiles(self, sendData:dict, file_headers:list[str]) -> tuple[dict, dict]:
		""" 행 단위 저장 시 파일 첨부 """
		sendFiles = {}
		for file_header in file_headers:
			if file_header in sendData:
				files_path = sendData.pop (  file_header , None)
				# files_path = sendData.pop( self.get_mapping_reverse_headers().get(file_header, file_header) )
				files = None
				if files_path and os.path.exists(files_path):
					try:
						# 파일 객체를 열어서 유지
						sendFiles[file_header] = open(files_path, 'rb')

					except Exception as e:
						logger.error(f"파일 처리 오류: {e}")
						logger.error(f"{traceback.format_exc()}")
		return sendData, sendFiles

	def setData(self, index:QModelIndex, value, role:Qt.ItemDataRole=Qt.ItemDataRole.EditRole):
		print ( f"setData : {index} , {value} , {role}")
		if not index.isValid() or role != Qt.ItemDataRole.EditRole:
			return False
			
		row = index.row()
		col = index.column()
		header_name = self._headers[col]
		db_attr_name = self.table_config["_mapping_display_to_attr"][header_name] if self.table_config else header_name
		
		# 유효성 검사
		if header_name in self._validators:
			if not self._validators[db_attr_name](value, index, self):
				return False
				
		# 데이터 변경
		data_list = self._filtered_data if self._is_filtered else self._data
		old_value = data_list[row][db_attr_name]
		
		# 값이 실제로 변경되었는지 확인 (개선된 비교 로직 사용)
		if self._is_equivalent_values(old_value, value):
			return False  # 값이 변경되지 않았으면 False 반환
		
		data_list[row][db_attr_name] = value
		
		# 필터링된 데이터인 경우 원본 데이터도 업데이트
		if self._is_filtered:
			# 원본 데이터에서 해당 행 찾기 (구현 필요)
			pass
		return self.setData_by_edit_mode(index, value, role)
	
	def setData_by_edit_mode(self, index:QModelIndex, value, role:Qt.ItemDataRole=Qt.ItemDataRole.EditRole):
		row = index.row()
		col = index.column()
		db_attr_name = self.get_field_name_by_index(index)
		match self.lazy_attr_values['edit_mode'].lower():
			case 'row':
				self._mark_row_as_modified(row)
				self.dataChanged.emit(index, index, [role])
				return True
			case 'cell':
				_isok, _json = APP.API.Send(
							url= self.url, 
				  			dataObj= self._data[row], 
							sendData={ db_attr_name: value}
							)
				if _isok:
					self._mark_cell_as_modified(row, col)
					self._data[row] = _json
					self.dataChanged.emit(
						self.index( index.row(), 0),
						self.index( index.row(), self.columnCount() - 1),
						[Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
					)
					self.dataChanged.emit(index, index, [role])
					return True
				else:
					return False
			case 'none'|'no_edit':
				return False

			case _:
				raise ValueError(f"Invalid edit mode: {self.lazy_attr_values['edit_mode']}")

	
	def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
		if not self._data: 
			return 

		if isinstance(self._data[0], list):
			self._data.sort(
				key=lambda row: row[column],
				reverse=(order == Qt.DescendingOrder)
			)
		elif isinstance(self._data[0], dict):
			header_key = self._headers[column]  # column index → column name
			self._data.sort(
				key=lambda row: row.get(header_key, None),  # None-safe
				reverse=(order == Qt.DescendingOrder)
			)

		self.layoutChanged.emit()

	def sort_by_display_role(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
		""" display role 기준으로 정렬 """
		index_func = lambda row_idx: self.index(row_idx, column)
		key_func = lambda row_idx: self.data(index_func(row_idx), Qt.ItemDataRole.DisplayRole) or ""
		reverse = order == Qt.SortOrder.DescendingOrder

		try:
			row_indices = list(range(len(self._data)))
			row_indices.sort(key=key_func, reverse=reverse)
			self._data = [self._data[i] for i in row_indices]
		except Exception as e:
			print(f"정렬 오류: {e}")
		self.layoutChanged.emit()
		
	def flags(self, index:QModelIndex):
		if not index.isValid():
			return Qt.ItemFlag.NoItemFlags
			
		base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
		if self._is_editable(index):
			return base_flags | Qt.ItemFlag.ItemIsEditable
		else:
			return base_flags


	
	def _is_editable(self, index:QModelIndex) -> bool:
		col = index.column()
		### 코딩으로 편집 제한 ==> tableview에서 생성한 것을 사용
		if  'no_edit_columns_by_coding' in self.lazy_attr_values:
			no_edit_columns = self.lazy_attr_values['no_edit_columns_by_coding']
			if 'ALL' in no_edit_columns or 'all' in no_edit_columns or 'All' in no_edit_columns:
				return False
			else :
				db_attr_name = self.get_field_name_by_index( index )
				if db_attr_name in self.lazy_attr_values['no_edit_columns_by_coding']:
					return False

		if  '_no_edit_cols' in self.table_config and self.table_config['_no_edit_cols']:
			if col in self.table_config['_no_edit_cols']:
				return False

		for rule in self._edit_rules:
			if not rule(index, self):
				return False

		return True
		
	# 유틸리티 메서드

		
	# row 에 대한 데이터 get 메서드
	def get_row_data(self, row_idx:int=None):
		"""특정 행의 데이터를 API 형식(dict)으로 반환
			특히, self._proecess_field_value를 통한 validation 강화
			( 즉, None이나 빈 문자열은 제거됨 )
		
		Args:
			row_idx (int): 행 인덱스
			
		Returns:
			dict: 행 데이터의 딕셔너리. 키는 tableview의 _mapping_reverse_headers를 이용
			None: 유효하지 않은 행 인덱스인 경우
		"""
		if row_idx < 0 or row_idx >= len(self._data):
			return None

		row_data:dict = self._data[row_idx]
		### 변환은 나중에 ==> 가능한 생성시 문제 없도록 할것
		# for attrName, value in row_data.items():
		# 	col_idx = self.get_column_No_by_field_name(attrName)
		# 	if self._is_editable(self.index(row_idx, col_idx)) :
		# 		if value is not None :
		# 			# 필드 값 처리
		# 			row_data[db_header_name] = self._process_field_value(header, value)
		
		return row_data

	def get_rows_data(self, data_type='all') -> list[dict]:
		"""행 데이터를 API 형식(list of dict)으로 반환
		
		Args:
			data_type (str): 데이터 타입 - 'all': 모든 행, 'modified': 변경된 행만
		
		Returns:
			list: 행 데이터의 리스트. 각 행은 딕셔너리 형태로 변환됨
				키는  _mapping_reverse_headers를 이용
		"""
		result = []
		
		# 처리할 행 인덱스 결정
		if data_type == 'modified':
			row_indices = self._modified_rows
		else:  # 'all' 또는 기타 값
			row_indices = range(len(self._data))
		
		# 행 데이터 수집
		for row_idx in row_indices:
			row_data = self.get_row_data(row_idx)
			if row_data:  # None이 아닌 경우에만 추가
				row_data['rowNo'] = row_idx
				result.append(row_data)
		
		return result

	def _process_field_value(self, header, value):
		"""필드 값을 처리하는 메서드
		
		Args:
			header (str): 헤더 이름
			value: 필드 값
			
		Returns:
			처리된 필드 값
		"""
		# filefield 타입인 경우 파일 객체로 처리
		if hasattr(self, '_column_types') and header in self._column_types and self._column_types[header] == 'filefield':
			# 파일 경로가 있는 경우에만 처리
			if value and isinstance(value, str):
				try:
					import os
					if os.path.exists(value):
						# 파일 객체 생성
						with open(value, 'rb') as f:
							file_name = os.path.basename(value)
							return {'file': f, 'filename': file_name}
				except Exception as e:
					# 로거가 정의되어 있다면 사용
					if 'logger' in globals():
						logger.error(f"파일 처리 오류: {e}")
					# 오류 발생 시 원래 값 반환
		# header_type에 따른 유효성 검사
		header_type = self._header_types.get(header, '').lower()
		if 'int' in header_type and not isinstance(value, int):
			return None
		elif 'float' in header_type and not isinstance(value, float):
			return None
		elif 'char' in header_type  and not isinstance(value, str):
			return None
		elif 'bool' in header_type and not isinstance(value, bool):
			return None
		elif 'date' in header_type:
			# 날짜 문자열을 datetime.date로 변환 가능해야 함
			try:
				if isinstance(value, str):
					return datetime.datetime.strptime(value, "%Y-%m-%d").date()
			except ValueError:
				return None
		elif 'datetime' in header_type:
			# 날짜 및 시간 문자열을 datetime.datetime으로 변환 가능해야 함
			try:
				if isinstance(value, str):
					return datetime.datetime.fromisoformat(value)
			except ValueError:
				return None
		
		# 기본적으로 원래 값 반환
		return value




	# 변경된 셀/행 표시 관련 메서드 추가
	def _mark_cell_as_modified(self, row, col):
		"""셀을 변경됨으로 표시하고 타이머 설정"""
		# 이미 타이머가 있으면 제거
		if (row, col) in self._modified_cells:
			timer = self._modified_cells[(row, col)]
			timer.stop()
			timer.deleteLater()
		
		# 새 타이머 생성
		timer = QTimer()
		timer.setSingleShot(True)
		timer.timeout.connect(lambda: self._clear_modified_cell(row, col))
		self._modified_cells[(row, col)] = timer
		
		# 5초 후 변경 표시 제거
		timer.start(5000)
		
		# 화면 갱신
		self.dataChanged.emit(
			self.index(row, col),
			self.index(row, col),
			[Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole]
		)
	
	def _clear_modified_cell(self, row, col):
		"""셀의 변경 표시 제거"""
		if (row, col) in self._modified_cells:
			timer = self._modified_cells.pop((row, col))
			timer.deleteLater()
			
			# 화면 갱신
			self.dataChanged.emit(
				self.index(row, col),
				self.index(row, col),
				[Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole]
			)
	
	def _mark_row_as_modified(self, row:int):
		"""행을 변경됨으로 표시"""
		self._modified_rows.add(row)
		
		# 화면 갱신
		self.dataChanged.emit(
			self.index(row, 0),
			self.index(row, self.columnCount() - 1),
			[Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole]
		)
	
	def clear_modified_rows(self, rows=None):
		"""행의 변경 표시 제거
		
		Args:
			rows: 제거할 행 인덱스 리스트. None이면 모든 행 제거
		"""
		if rows is None:		
			prev_modified_rows = list(self._modified_rows)
			self._modified_rows.clear()
			self._clear_render_modifed_rows(prev_modified_rows)

		else:
			# 지정된 행만 제거
			for row in rows:
				logger.warning (f"clear_modified_rows : {self._modified_rows} : {row}")
				logger.warning (f" row in self._modified_rows : {bool(row in self._modified_rows)}")
				if row in self._modified_rows:
					self._modified_rows.remove(row)
					self._clear_render_modifed_rows(rows)

	def _clear_render_modifed_rows(self, modified_rows:list):
		for row in modified_rows:
			self.dataChanged.emit(
				self.index(row, 0),
				self.index(row, self.columnCount() - 1),
				[Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole]
			)

	
	def update_api_response(self, api_response:dict, rowNo:int=-1):
		""" api 응답 업데이트 """
		self.prev_api_datas = copy.deepcopy(self.api_datas)
		    # API 응답을 self.api_datas에 반영
		api_index = self._find_api_index_by_id(api_response['id'])
		if api_index is not None:
			self.api_datas[api_index] = api_response
		else:
			self.api_datas.insert(0, api_response)

		# row_index = self._find_row_index_by_id(api_response['id'])
		if rowNo >= 0:
			self._data[rowNo] = self.create_model_data_by_row(api_response)
		else:
			self._data.insert(0, self.create_model_data_by_row(api_response))
			rowNo = 0
		self._original_data = copy.deepcopy(self._data)
		self.dataChanged.emit(
			self.index(rowNo, 0),
			self.index(rowNo, self.columnCount() - 1),
			[Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
		)
		self.clear_modified_rows([rowNo])
		self.user_data_changed.emit(self.is_datas())

	def _find_api_index_by_id(self, id_value) -> int|None:
		"""주어진 ID 값으로 행 인덱스를 찾는 헬퍼 메서드, 없으면 None 반환"""
		for row_index, _obj in enumerate(self.api_datas):
			if _obj.get('id') == id_value:  # ID가 첫 번째 컬럼에 있다고 가정
				return row_index
		return None
	
	def _find_row_index_by_id(self, id_value) -> int|None:
		"""주어진 ID 값으로 행 인덱스를 찾는 헬퍼 메서드, 없으면 None 반환"""
		modified_rows = list(self._modified_rows)
		if modified_rows:
			if len(modified_rows) == 1:
				return modified_rows[0]
			else:
				id_colNo = self._headers.index(self._table_view._mapping_headers['id'])
				for rowNo in modified_rows:
						if self._data[rowNo][id_colNo] == id_value:
							return rowNo
				else:
					return None
		else:
			return None
		

	def clear_all_modifications(self):
		"""모든 변경 표시 제거"""
		# 셀 단위 변경 표시 제거
		for (row, col), timer in list(self._modified_cells.items()):
			timer.stop()
			timer.deleteLater()
		self._modified_cells.clear()
		
		# 행 단위 변경 표시 제거
		self.clear_modified_rows()
		
		# 전체 화면 갱신
		self.layoutChanged.emit()

	def get_modified_rows_data(self):
		"""변경된 행의 데이터를 API 형식(list of dict)으로 반환
		
		Returns:
			list: 변경된 행 데이터의 리스트
		"""
		return self.get_rows_data(data_type='modified')

	def get_all_rows_data(self):
		"""모든 행의 데이터를 API 형식(list of dict)으로 반환
		
		Returns:
			list: 모든 행 데이터의 리스트
		"""
		return self.get_rows_data(data_type='all')
	

	def insertRow(self, row, parent=QModelIndex()):
		self._data.insert(row, [""] * self.columnCount())  # 혹은 적절한 디폴트 row
		self.user_data_changed.emit(self.is_datas())
		return True

	def removeRow(self, row, parent=QModelIndex()):
		del self._data[row]
		self.user_data_changed.emit(self.is_datas())
		return True

	def reset_data(self):
		self._data = []
		self.user_data_changed.emit(self.is_datas())


	def is_datas(self):
		return len(self._data) > 0
	

	def is_same_api_datas(self) -> bool:
		""" self.prev_api_datas 와 self.api_datas 비교 하여
			같으면 True, 다르면 False 반환
		"""
		return self.prev_api_datas == self.api_datas


	def get_column_No_by_field_name(self, field_name:str) -> int:
		""" field_name 에 해당하는 컬럼 번호를 반환 """
		return self._headers.index(self.get_displayName_from_attr(field_name))
		if field_name not in self._fieldname_to_col_index_cache:
			self._fieldname_to_col_index_cache[field_name] = self._headers.index( self.get_displayName_from_attr(field_name))
		return self._fieldname_to_col_index_cache.get(field_name, -1)
	
	def clear_fieldname_to_col_index_cache(self):
		self._fieldname_to_col_index_cache = {}
	
	def get_id_dict(self, rowNo:int) -> dict:
		""" rowNo 에 해당하는 행의 id 값을 반환 """
		id_value = self._data[rowNo][self.get_column_No_by_field_name('id')]
		if id_value and isinstance(id_value, int) and id_value > 0:
			return {'id': id_value}
		else:
			return {'id': -1}

	

	def request_api_update_row(self, rowNo:int):
		""" rowNo 에 해당하는 행을 API 업데이트 요청 """
		_isOk, _json = APP.API.getObj ( self.url, id=int( self._data[rowNo][self.get_column_No_by_field_name('id')] ) )
		if _isOk:
			self.update_api_response( _json, rowNo )
		else:
			Utils.generate_QMsg_critical( self, title='API 업데이트 실패', text= json.dumps( _json, ensure_ascii=False ) )

	

	
	def on_request_excel_export(self, is_ok:bool=True):
		if not is_ok:
			return
		self.data_to_excel_only_visible_columns()

	def data_to_excel_only_visible_columns(self):
		""" 데이터를 엑셀로 저장 """
		path, _ = QFileDialog.getSaveFileName(
				self._table_view, "엑셀로 저장", "", "Excel Files (*.xlsx)"
			)
		if not path:
			return

		# 🔽 확장자 누락 시 추가
		if not path.endswith(".xlsx"):
			path += ".xlsx"
		logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export -> {path}")

		# Step 2: 숨겨지지 않은 열 인덱스 수집
		visible_columns = [
			col for col in range(self.columnCount())
			if not self._table_view.isColumnHidden(col)
		]

		# Step 3: 헤더 추출
		headers = [
			self.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
			for col in visible_columns
		]

		# Step 4: 데이터 추출
		data = []
		for row in range(self.rowCount()):
			row_data = [
				self.data(self.index(row, col), Qt.ItemDataRole.DisplayRole)
				for col in visible_columns
			]
			data.append(row_data)

		# Step 5: DataFrame 생성 및 Excel 저장
		df = pd.DataFrame(data, columns=headers)
		try:
			df.to_excel(path, index=False)
			logger.info(f"엑셀 저장 성공: {path}")
		except Exception as e:
			logger.exception("엑셀 저장 실패")
			logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export")


	def data_to_excel_raw_data(self):
		""" 데이터를 엑셀로 저장 """
		path, _ = QFileDialog.getSaveFileName(
				self._table_view, "엑셀로 저장", "", "Excel Files (*.xlsx)"
			)
		if not path:
			return

		# 🔽 확장자 누락 시 추가
		if not path.endswith(".xlsx"):
			path += ".xlsx"
		logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export -> {path}")

		# Step 2: 숨겨지지 않은 열 인덱스 수집
		visible_columns = [
			col for col in range(self.columnCount())
			if not self._table_view.isColumnHidden(col)
		]

		# Step 3: 헤더 추출
		headers = [
			self.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
			for col in range(self.columnCount())
		]

		# Step 4: 데이터 추출
		data = []
		for row in range(self.rowCount()):
			row_data = [
				self.data(self.index(row, col), Qt.ItemDataRole.EditRole)
				for col in range(self.columnCount())
			]
			data.append(row_data)

		# Step 5: DataFrame 생성 및 Excel 저장
		df = pd.DataFrame(data, columns=headers)
		try:
			df.to_excel(path, index=False)
			logger.info(f"엑셀 저장 성공: {path}")
		except Exception as e:
			logger.exception("엑셀 저장 실패")
			logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export")




	def copy_row(
		self: Base_Table_Model,
		rowNo: int,
		remaining_keys: Optional[list[str]] = [],
		remaining_add_dict: Optional[dict] = {},
		update_dict: Optional[dict] = {}
	):
		""" 행 복사 후 데이터 저장 """
		if not (0 <= rowNo < len(self._data)):
			raise IndexError(f"Invalid rowNo: {rowNo}")

		origin_row = self._data[rowNo]

		if not remaining_keys:
			copyed_row = {key: '' for key in origin_row}
		elif any(k.lower() == 'all' for k in remaining_keys):
			copyed_row = copy.deepcopy(origin_row)
		else:
			copyed_row = {}
			for key in origin_row:
				if key in remaining_keys:
					prefix = remaining_add_dict.get(key, '') if remaining_add_dict else ''
					copyed_row[key] = f"{prefix}{origin_row[key]}"
				else:
					copyed_row[key] = ''

		if update_dict:
			copyed_row.update(update_dict)

		return copyed_row