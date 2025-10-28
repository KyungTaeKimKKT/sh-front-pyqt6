from __future__ import annotations  ### SyntaxError: from __future__ imports must occur at the beginning of the file
from typing import Optional, TYPE_CHECKING
from modules.global_event_bus import event_bus
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from local_db.models import Table_Config
import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import concurrent.futures

import pathlib
import typing
import copy
import json


from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model, TableModelBuilder
# from modules.PyQt.compoent_v2.table.Base_Table_Delegate import Base_Table_Delegate
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu



from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer

# from modules.PyQt.Tabs.생산지시서.dialog.list_edit.dlg_판금처선택 import 판금처선택다이얼로그

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger	# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

if TYPE_CHECKING:
	from modules.PyQt.Tabs.plugins.table.Base_Wid_Table import Base_Wid_Table


class TableDataManager:
	"""테이블 데이터 관리를 담당하는 클래스"""

	def __init__(self, handler: Base_Wid_Table):
		self.handler = handler
		self.table_name = handler.table_name
		self.api_data = []
		self.model_data = []
		self.table_config = {}
		self.header_type = {}
		self.table_header = []
		self.fields_model = {}
		self.fields_append = {}

		logger.info ( f" :__init__ : self.handler : {self.handler}")
		logger.info ( f"self.handler.table_name : {self.handler.table_name}")
		if hasattr(self.handler, 'table_name'):
			self.table_name = self.handler.table_name
		else:
			self.table_name = self.handler.make_table_name()
		logger.info ( f" :__init__ : self.table_name : {self.table_name}")
		# self.register_event()
	
	def register_event(self):
		logger.info(f" :register_event : {self.table_name}")
		event_bus.subscribe(f'{self.table_name}:{GBus.API_DATA_REFRESH}', self.refresh_data)
		# event_bus.subscribe(f'{self.table_name}:{GBus.API_DATA_UPDATED}', self.refresh)

	def refresh_data(self, data:list[dict]):
		logger.info(f" :refresh_data : {len(data)} 개 수신")
		self.api_data = data
		self.model_data = self.create_model_data()
		event_bus.publish(f'{self.table_name}:{GBus.TABLE_DATA_REFRESH}', self.model_data)
		logger.info(f" :refresh_data : event_bus.publish : {GBus.TABLE_DATA_REFRESH}")

	### builder
	def builder(self):
		logger.info ( f" builder : self.handler : {self.handler}")
		self.table_name = self.table_name or self.handler.table_name
		self.api_data = self.api_data or self.handler.api_data
		logger.info(f"builder : {self.table_name}")
		self.load_table_config()
		self.create_model_data()
		return self.get_all_table_datas()
	
	def with_api_data(self, api_data:list[dict]):
		"""API 데이터를 설정하고 자신을 반환하는 빌더 메서드"""
		self.set_api_data(api_data)
		return self
	
		#### getter 
	def get_all_table_datas(self) ->tuple[list[list[any]], list[dict]]:
		""" 모델 데이터와 테이블 설정을 반환 """
		return self.model_data, self.table_config

	def get_table_config(self):
		return self.table_config
		
	def get_model_data(self):
		return self.model_data
	
	#### setter
	def set_table_name(self, table_name:str):
		self.table_name = table_name	
	
	def set_api_data(self, api_data:list[dict]):
		self.api_data = api_data
	
	def set_update_api_data(self, api_data:list[dict]):
		""" api_data 중 일부만 업데이트 """
		if not api_data:
			return
			
		# ID 기준으로 기존 데이터에서 업데이트할 항목 제거
		update_ids = [item.get('id') for item in api_data if item.get('id')]
		self.api_data = [item for item in self.api_data if item.get('id') not in update_ids]
		# 새 데이터 추가
		self.api_data.extend(api_data)

	def set_add_api_data(self, api_data:list[dict]):
		"""API 데이터에 새 항목 추가"""
		if api_data:
			self.api_data.extend(api_data)

	def set_delete_api_data(self, api_data:list[dict]):
		"""API 데이터에서 항목 삭제"""
		if not api_data:
			return
			
		delete_ids = [item.get('id') for item in api_data if item.get('id')]
		self.api_data = [item for item in self.api_data if item.get('id') not in delete_ids]

	def set_update_model_data(self, model_data:list[dict]):
		"""모델 데이터 중 일부만 업데이트"""
		if not model_data:
			return
			
		# 업데이트 로직 구현
		# 참고: 모델 데이터는 리스트의 리스트이므로 ID 기반 업데이트 로직은 별도 구현 필요
		pass

	def load_table_config(self) -> bool:
		logger.info(f"load_table_config : {self.table_name}")
		self.table_name = self.table_name or getattr(self.handler, 'table_name', None)
		if not self.table_name:
			logger.error("테이블 이름이 설정되지 않았읍니다")
			return False

		# 로컬 DB에서 먼저 시도
		table_config_dict = self.load_table_config_from_local_db(self.table_name)
		logger.info(f"load_table_config : {self.table_name} 로컬 DB : {len(table_config_dict)} 로드 완료")
		if table_config_dict:
			self.process_table_config(table_config_dict)
			return True    

		# 로컬 DB에 없으면 API에서 시도
		table_config_dict = self.load_table_config_from_api(self.table_name)
		logger.info(f"load_table_config : {self.table_name} API {len(table_config_dict)} 로드 완료")
		if table_config_dict:
			self.process_table_config(table_config_dict)
			return True
			
		logger.warning(f"테이블 설정을 찾을 수 없읍니다: {self.table_name}")
		return False


	def load_table_config_from_local_db(self, table_name:str) ->list[dict]:
		""" 로컬 DB에서 테이블 설정 로드 """
		try:
			table_config_dict = Table_Config.objects.filter(table_name=table_name).values()
			return table_config_dict
		except Exception as e:
			logger.error(f"로컬 DB에서 테이블 설정 로드 실패: {e}")
			return []


	def load_table_config_from_api(self, table_name:str) ->list[dict]:
		""" API에서 테이블 설정 로드 """
		try:
			is_ok, json_data = APP.API.getlist(f"{INFO.URL_JOB_INFONAME}?table_name={table_name}&page_size=0")
			if is_ok:
				return json_data
			logger.error(f"API에서 테이블 설정 로드 실패: {json_data}")
		except Exception as e:
			logger.error(f"API 호출 중 오류 발생: {e}")
		return []

	def process_table_config(self, config_data):
		"""API에서 받은 테이블 설정 처리"""
		if not config_data:
			logger.warning("처리할 테이블 설정 데이터가 없읍니다")
			return
			
		DBs = config_data
		표시명 = 'display_name'
		
		self.table_config = {
			'_table_name': self.table_name,
			'_table_config_api_datas': DBs,
			'_headers': [_obj.get(표시명) for _obj in DBs],
			'_hidden_columns': [idx for idx, _obj in enumerate(DBs) if _obj.get('is_hidden', False)],
			'_no_edit_cols': [idx for idx, _obj in enumerate(DBs) if not _obj.get('is_editable', True)],
			'_column_types': {_obj.get(표시명): _obj.get('column_type') for _obj in DBs},
			'_column_styles': {_obj.get(표시명): _obj.get('cell_style') for _obj in DBs},
			'_column_widths': {_obj.get(표시명): _obj.get('column_width', 0) for _obj in DBs},
			'_table_style': DBs[0].get('table_style') if DBs else None
		}
		
	def create_model_data(self):
		"""API 데이터로부터 모델 데이터 생성"""
		logger.info(f"create_model_data : {self.table_name}")
		logger.info(f"api_data : {len(self.api_data)}")
		
		if not self.api_data:
			logger.warning("API 데이터가 없읍니다")
			return []
			
		if not self.table_config.get('_headers'):
			logger.warning("테이블 헤더가 설정되지 않았읍니다")
			return []
			
		model_data = []
		for _obj in self.api_data:
			row_data = []
			for headName in self.table_config.get('_headers', []):
				row_data.append(_obj.get(headName, ''))
			model_data.append(row_data)
		
		self.model_data = model_data
		return model_data
		
	def update_config(self, **kwargs):
		"""설정 업데이트"""
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
				
		# 헤더 타입 설정
		self.header_type = copy.deepcopy(self.fields_model)
		self.header_type.update(self.fields_append)
		
		# 테이블 헤더 설정
		if hasattr(self, 'table_config') and (table_header := self.table_config.get('table_header', None)):
			self.table_header = table_header
		else:
			self.table_header = list(self.header_type.keys())
			
		# 테이블 설정 로드
		self.load_table_config()


