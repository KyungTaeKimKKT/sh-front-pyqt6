from __future__ import annotations
from typing import Optional, TYPE_CHECKING,  Any, Union, Callable
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6 import sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table_v2.table_mixin import TableConfigMixin, TableMenuMixin
from modules.PyQt.compoent_v2.table_v2.Base_Table_Model_Role_Mixin import Base_Table_Model_Role_Mixin, CustomRoles
from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config
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
logger = get_plugin_logger()

class Base_Table_Model_Mixin:

	def on_new_row(self, **kwargs):
		self.request_add_row(rowNo=0, **kwargs)

	def on_new_row_by_template(self, added_url:str="template/", **kwargs):
		""" drf template 호출 후 데이터 추가 """
		url = f"{self.url}{added_url}".replace('//', '/')
		is_ok, _json = APP.API.getObj_byURL(url= url)
		if is_ok:
			self.mixin_add_row_data(rowNo=0, dataObj=_json)
			# 기존 modified row index 전부 +1 shift
			self._modified_rows = {r + 1 for r in self._modified_rows}
			self._mark_row_as_modified(0)
		else:
			Utils.generate_QMsg_critical(None, title="템플릿 오류", text="템플릿 오류")

	def on_copy_new_row_by_template(self, rowNo:int, **kwargs):
		""" self.url 에 따라, template_copyed url 로 호출"""
		rowDict = self._data[rowNo]
		if rowDict['id'] < 1:
			Utils.generate_QMsg_critical(None, title="복사 실패", text="복사할 행은 정규 db data이이야 합니다.")
			return

		url = f"{self.url}{rowDict['id']}/template_copyed/".replace('//', '/')
		if INFO.IS_DEV:
			print(f"on_copy_new_row_by_template: {url}")
		
		_isOk, _json = APP.API.getObj_byURL(url= url)
		if _isOk:
			self.mixin_add_row_data(rowNo, _json)
		else:
			Utils.generate_QMsg_critical(None, title="복사 실패", text="복사 실패")

	def on_copy_new_row(self, rowDict:dict, **kwargs):
		rowNo = self._data.index(rowDict)
		self.request_add_row(rowNo=rowNo, **kwargs)

	def on_delete_row(self, rowNo:Optional[int]=None, rowDict:Optional[dict]=None, **kwargs):
		if rowNo is None:
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
		self._original_data.insert(rowNo, dataObj)
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

class Base_Table_Model( #LazyParentAttrMixin,
					    QAbstractTableModel, 
						Base_Table_Model_Role_Mixin, 
						Base_Table_Model_Mixin,
						Mixin_Table_Config,
						):
	""" V2 : 확장성과 유연성이 개선된 기본 테이블 모델 클래스"""
	Roles = CustomRoles
	# 시그널 정의
	
	def __init__(self, parent=None, **kwargs):
		"""
        kwargs로 모델 속성을 초기화할 수 있는 생성자
        
        가능한 kwargs:

        """
		super().__init__(parent)
		### lazy_attr_values 초기화
		self.kwargs = kwargs
		if INFO.IS_DEV:
			print (f"{self.__class__.__name__} : __init__ : kwargs: {kwargs}")
		self.lazy_attr_values = {}
		

		###✅ 25-07-03 추가
		self._created_id = -1 #### 계속 증가시침	
		self.start_init_time = time.perf_counter()
		self.event_bus = event_bus
		self.table_name = ''
		self.table_config = {}
		
		# 기본 데이터
		self.appDict = {}
		self.api_datas :list[dict] = []
		self._original_api_datas :list[dict] = []
		self.map_id_to_api_data :dict[int, dict] = {}
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

		self._sort_column :int = -1
		self._sort_order :Qt.SortOrder = Qt.AscendingOrder


		self._initialize_from_kwargs(**kwargs)
	
	

	@property
	def created_id(self):
		"""  초기 -1 이후 계속 -2, -3 씩 증가시킴"""
		self._created_id -= 1
		return self._created_id
		
	def _initialize_from_kwargs(self, **kwargs):
		"""kwargs로부터 모델 속성 초기화"""
		# kwargs로 초기화
		if kwargs  :
			self.kwargs = kwargs
			if 'set_kwargs_to_attr' not in kwargs or kwargs['set_kwargs_to_attr']:
				for key, value in kwargs.items():			
					setattr(self, key, value)

	def closeEvent(self, event):
		self.unsubscribe_gbus()
		super().closeEvent(event)

	def on_all_lazy_attrs_ready(self, APP_ID:Optional[int] = None, **kwargs):
		self._initialize_from_kwargs(**kwargs)
		if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
			raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
		self.appDict =  copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
		self.table_name = Utils.get_table_name(APP_ID)
		if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
			self.url = Utils.get_api_url_from_appDict(self.appDict)
		self.subscribe_gbus()
	
	def set_table_config(self, table_config:dict, table_config_api_datas:list[dict]):
		self.table_config = table_config
		self.table_config_api_datas = table_config_api_datas
		self.map_display_name_to_obj = { obj['display_name']: obj for obj in self.table_config_api_datas }
		self._header_types = self.table_config.get('_headers_types', {})
		self._headers = self.table_config['_headers']
		if isinstance( self, QAbstractTableModel):
			self.layoutChanged.emit()

	
	def on_api_datas_received(self, api_datas:list[dict]):
		""" gbus subscribe 된 api_datas 받아오면 호출되는 함수 """
		self.api_datas = copy.deepcopy(api_datas)
		self._original_api_datas = copy.deepcopy(api_datas)
		self._original_data = self._original_api_datas
		#### ✅ 257-3 추가
		self.map_id_to_rowData = { rowData['id']: rowData for rowData in api_datas  if 'id' in rowData}
		self._data = api_datas

		

	def subscribe_gbus(self):
		# self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.on_api_datas_received )
		# self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
		self.event_bus.subscribe(f"{self.table_name}:custom_editor_complete", self.on_custom_editor_complete)
		# self.event_bus.subscribe(f"{self.table_name}:edit_mode", self.on_edit_mode)

		self.event_bus.subscribe( f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", self.on_request_download_from_pagination )
		self.event_bus.subscribe( f"{self.table_name}:request_excel_export", self.on_request_excel_export )
		# self.event_bus.subscribe( f"{self.table_name}:table_config_api_datas", self.on_table_config_api_datas )

	def unsubscribe_gbus(self):
		try:
			self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.on_api_datas_received  )
			self.event_bus.unsubscribe( f"{self.table_name}:custom_editor_complete", self.on_custom_editor_complete )
			self.event_bus.unsubscribe( f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", self.on_request_download_from_pagination )
		except Exception as e:
			logger.error(f"unsubscribe_gbus 오류: {e}")
			logger.error(f"traceback: {traceback.format_exc()}")
	
	def on_edit_mode(self, edit_mode:str):
		# Utils.generate_QMsg_Information(None, title="edit_mode 변경", text=f"edit_mode 변경 : {edit_mode}", autoClose=1000 )
		self.kwargs['edit_mode'] = edit_mode
		self._edit_mode = edit_mode.lower().strip()
		self.lazy_attr_values['edit_mode'] = self._edit_mode
		if INFO.IS_DEV:
			Utils.generate_QMsg_Information(None, title="edit_mode 변경", text=f"edit_mode 변경 : {edit_mode}", autoClose=1000 )

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
			if INFO.IS_DEV:
				logger.debug(f"on_custom_editor_complete: {data}")
			self.setData(data['index'], data['value'], role=Qt.ItemDataRole.EditRole)
		except Exception as e:
			logger.debug(f"on_custom_editor_complete 오류: {self.parent().__class__.__name__}")
			logger.error(f"on_custom_editor_complete 오류: {e}")
			logger.error(f"traceback: {traceback.format_exc()}")


	# QAbstractTableModel 필수 메서드 구현
	def rowCount(self, parent:QModelIndex=None):
		return len(self._data)
		
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
					_type = self.get_type_by_index(self.index(0, section))
					return f"db속성: {db_attr_name} <br> 타입: {_type}"
		return None
			
	def load_dataframe(self, df:pd.DataFrame):
		datas = df.to_dict(orient='records')
		self.on_api_datas_received(datas)

	def data(self, index:QModelIndex, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
		if not index.isValid():
			return None
			
		row = index.row()
		col = index.column()

		if row < 0 or row >= len(self._data) or col < 0 or col >= len(self._headers):
			return None
		
		if role == Qt.ItemDataRole.UserRole:
			return self._data[row]
		
		return self.role_data(row, col, role)
	
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
		if self.is_all_no_edit():
			return False
		
		db_attr_name = self.get_field_name_by_index( index )
		if db_attr_name in self.lazy_attr_values['no_edit_columns_by_coding']:
			return False

		if  '_no_edit_cols' in self.table_config and self.table_config['_no_edit_cols']:
			if col in self.table_config['_no_edit_cols']:
				return False

		return True
	
	def is_all_no_edit(self):
		if self.lazy_attr_values['no_edit_columns_by_coding']:
			values = self.lazy_attr_values['no_edit_columns_by_coding']
			return  'ALL' in values  or 'All' in values or 'all' in values
		return False
	

	def setHeaderData(self, section:int, orientation:Qt.Orientation, value, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
		if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
			if 0 <= section < len(self._headers):
				self._headers[section] = value
				self.layoutChanged.emit()

	def setData(self, index:QModelIndex, value, role:Qt.ItemDataRole=Qt.ItemDataRole.EditRole):
		if INFO.IS_DEV:
			print ( f"setData : {index} , {index.row()} , {index.column()} , {value} , {role}")
		if not index.isValid() or role != Qt.ItemDataRole.EditRole:
			return False
		
		try:
			row = index.row()
			col = index.column()
			display_name = self.get_display_name_by_index(index)
			db_attr_name = self.get_attrName_from_display(display_name)
			
			# 유효성 검사
			# if db_attr_name in self._validators:
			# 	if not self._validators[db_attr_name](value, index, self):
			# 		return False
					
			# 데이터 변경
			old_value = self._data[row][db_attr_name]
			
			# 값이 실제로 변경되었는지 확인 (개선된 비교 로직 사용)
			if self._is_equivalent_values(old_value, value):
				return False  # 값이 변경되지 않았으면 False 반환
			
			return self.setData_by_edit_mode(index, value, role)
		except Exception as e:
			logger.error(f"setData 오류: {e}")
			logger.error(f"traceback: {traceback.format_exc()}")
			return False
	
	
	def setData_by_edit_mode(self, index:QModelIndex, value, role:Qt.ItemDataRole=Qt.ItemDataRole.EditRole):
		row, col = index.row(), index.column()
		db_attr_name = self.get_field_name_by_index(index)
		match self.lazy_attr_values['edit_mode'].lower():
			case 'row':
				if INFO.IS_DEV:
					print(f" 'row mode' : setData_by_edit_mode : {row}, {col}, {value}, {db_attr_name}")
				self.update_cell_data(index, value)
				self._mark_row_as_modified(row)
				return True
			case 'cell':
				_isok, _json = APP.API.Send(
							url= self.url, 
				  			dataObj= self._data[row], 
							sendData={ db_attr_name: value}
							)
				if _isok:
					self.update_row_data(row, _json)
					self._mark_cell_as_modified(row, col)
					return True
				else:
					return False
			case 'none'|'no_edit':
				return False

			case _:
				raise ValueError(f"Invalid edit mode: {self.lazy_attr_values['edit_mode']}")

	### getter	

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

	def get_headers(self) -> list[str]:
		return self._headers
	
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
		return self.get_headers()[index.column()]
	
	def get_column_no_from_display_name(self, display_name:str) -> int:
		return self.get_headers().index(display_name)
	
	get_column_no_from_display_name = get_column_no_from_display_name
	
	def get_column_no_from_attr_name(self, attr_name:str) -> int:
		display_name = self.get_displayName_from_attr(attr_name)
		return self.get_headers().index(display_name)
	
	get_column_no_from_attr_name = get_column_no_from_attr_name
	get_column_no_from_field_name = get_column_no_from_attr_name

	def index_from_row_col(self, row: int, col: int) -> QModelIndex:
		return self.index(row, col)
	get_index_from_row_col = index_from_row_col
	
	def get_type_by_index(self, index:QModelIndex) -> str:
		db_attr_name = self.get_field_name_by_index(index)
		return self.table_config['_column_types'].get(db_attr_name, 'C') if self.table_config else 'C'
	

	def is_db_id(self, rowNo:int) -> bool:
		""" None, "", -1 은 False, """
		id_value = self._data[rowNo]['id']
		if id_value is None or id_value == "" or id_value == -1:
			return False		
		if isinstance(id_value, int) and id_value > 0:
			return True


	####
	

	### utils method


	def _is_equivalent_values(self, value1:Any, value2:Any) -> bool:
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
		self._original_data = copy.deepcopy(self._data)
		#### ✅ 25-7-3 추가
		self.map_id_to_rowData = { rowData['id'] : rowData for rowData in self._data  if 'id' in rowData }
		start_col = 0
		end_col = len(self._headers) - 1

		self.dataChanged.emit(self.index(rowNo, start_col), self.index(rowNo, end_col), [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
		return True


	def update_cell_data(self, index:QModelIndex, value:Any):
		""" Cell data 갱신"""
		if INFO.IS_DEV:
			print(f"update_cell_data : {index.row()}, {index.column()}, {value}, {self.get_attr_name_by_column_no(index.column())}")
		row = index.row()
		col = index.column()
		attr_name = self.get_attr_name_by_column_no(col)
		old_value = self._data[row][attr_name]
		
		# 값이 실제로 변경되었는지 확인 (개선된 비교 로직 사용)
		if self._is_equivalent_values(old_value, value):
			return False  # 값이 변경되지 않았으면 False 반환
		self._data[row][attr_name] = value
		self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])		
		return True

	def on_api_send_By_Row(self, send_type:str='formdata'):
		if send_type == 'formdata':
			return self.on_api_send_By_Row_by_formdata()
		elif send_type == 'json':
			return self.on_api_send_By_Row_by_json()


	def on_api_send_By_Row_by_formdata(self):
		""" 행 단위 저장 ==> requested by wid_table_header : signal로 연결됨."""
		if INFO.IS_DEV:
			logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
		if self._modified_rows:
			for row in list(self._modified_rows):
				_isok, _json = 	APP.API.Send(url= self.url, 
								dataObj= self._data[row],
								sendData=self._data[row]
								)
				if _isok:
					self.update_row_data(row, _json)
					Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
					self.clear_modified_rows([row])

				else:					
					Utils.generate_QMsg_critical(None, title="API 호출 실패", text=f"API 호출 실패<br> {json.dumps( _json, ensure_ascii=False )}")
					return False
			return True
		else:

			return False
		
	def on_api_send_By_Row_by_json(self):
		""" 행 단위 저장 ==> requested by wid_table_header : signal로 연결됨."""
		if INFO.IS_DEV:
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
					Utils.generate_QMsg_critical(None, title="API 호출 실패", text=f"API 호출 실패<br> {json.dumps( _json, ensure_ascii=False )}")
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
	
	def get_sendData_and_multiple_sendFiles(self, sendData:dict, file_field_name:str) -> tuple[dict, dict]:
		""" 파일 여러개 첨부 """
		sendFiles = []
		if file_field_name in sendData:
			file_paths = sendData.pop(file_field_name)
			for file_path in file_paths:
				#### 🔧 25-7-17 추가 :여기서는 신규가 아닌 경우는 dict 이므로 skip 함
				if isinstance(file_path, dict):
					continue
				if file_path and os.path.exists(file_path):
					try:
						sendFiles.append((file_field_name, open(file_path, 'rb')))
					except Exception as e:
						logger.error(f"파일 처리 오류: {e}")
						logger.error(traceback.format_exc())
		return sendData, sendFiles


	
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
		

		
	# 유틸리티 메서드

		

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
				if INFO.IS_DEV:
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


	def is_datas(self):
		return len(self._data) > 0
	

	def is_same_api_datas(self) -> bool:
		""" self.prev_api_datas 와 self.api_datas 비교 하여
			같으면 True, 다르면 False 반환
		"""
		return self.prev_api_datas == self.api_datas


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
		if not isinstance(self.parent(), QTableView	):
			Utils.generate_QMsg_critical(None, title='엑셀 내보내기 오류', text="엑셀 내보내기 오류<br> 부모가 테이블이 아닙니다.")			
			return
		tableview :QTableView = self.parent()
		path, _ = QFileDialog.getSaveFileName(
				tableview, "엑셀로 저장", "", "Excel Files (*.xlsx)"
			)
		if not path:
			return

		# 🔽 확장자 누락 시 추가
		if not path.endswith(".xlsx"):
			path += ".xlsx"
		if INFO.IS_DEV:
			logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export -> {path}")

		# Step 2: 숨겨지지 않은 열 인덱스 수집
		visible_columns = [
			col for col in range(self.columnCount())
			if not tableview.isColumnHidden(col)
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
		except Exception as e:
			logger.exception("엑셀 저장 실패")
			logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export")


	def data_to_excel_raw_data(self):
		""" 데이터를 엑셀로 저장 """
		if not isinstance(self.parent(), QTableView	):
			Utils.generate_QMsg_critical(None, title='엑셀 내보내기 오류', text="엑셀 내보내기 오류<br> 부모가 테이블이 아닙니다.")			
			return
		tableview :QTableView = self.parent()
		path, _ = QFileDialog.getSaveFileName(
				tableview, "엑셀로 저장", "", "Excel Files (*.xlsx)"
			)
		if not path:
			return

		# 🔽 확장자 누락 시 추가
		if not path.endswith(".xlsx"):
			path += ".xlsx"
		if INFO.IS_DEV:
			logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export -> {path}")

		try:
			df = pd.DataFrame(self._data)
			df.to_excel(path, index=False)
		except Exception as e:
			logger.error(f"엑셀 내보내기 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			return

		# # Step 2: 숨겨지지 않은 열 인덱스 수집
		# visible_columns = [
		# 	col for col in range(self.columnCount())
		# 	if not tableview.isColumnHidden(col)
		# ]

		# # Step 3: 헤더 추출
		# headers = [
		# 	self.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
		# 	for col in range(self.columnCount())
		# ]

		# # Step 4: 데이터 추출
		# data = []
		# for row in range(self.rowCount()):
		# 	row_data = [
		# 		self.data(self.index(row, col), Qt.ItemDataRole.EditRole)
		# 		for col in range(self.columnCount())
		# 	]
		# 	data.append(row_data)

		# # Step 5: DataFrame 생성 및 Excel 저장
		# df = pd.DataFrame(data, columns=headers)
		# try:
		# 	df.to_excel(path, index=False)
		# except Exception as e:
		# 	logger.exception("엑셀 저장 실패")
		# 	logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export")




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
	




class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df.copy()  # 모델 내부 데이터 저장

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._df.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._df.columns[section]
        else:
            return str(section + 1)

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False