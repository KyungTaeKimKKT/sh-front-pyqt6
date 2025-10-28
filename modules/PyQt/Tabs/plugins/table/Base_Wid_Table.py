from __future__ import annotations  ### SyntaxError: from __future__ imports must occur at the beginning of the file
from typing import Optional, TYPE_CHECKING
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

from modules.PyQt.Tabs.plugins.tablemanager.tablemenumanager import TableMenuManager
from modules.PyQt.Tabs.plugins.tablemanager.tabledatamanager import TableDataManager
from modules.PyQt.Tabs.plugins.tablemanager.tableuimanager import TableUiManager

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
from stylesheet import StyleSheet as ST

### 필수 : logger & class 자동 생성 🤣🤣🤣🤣🤣
import traceback
from modules.logging_config import get_plugin_logger	# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()


module_postfix = __name__.split('.')[-1].split('__')[-1]
# logger.info(f"module_prefix: {module_postfix}")
modules_dict = {'TableView':Base_Table_View,'TableModel':Base_Table_Model,'Delegate':My_Table_Delegate}
for prefix, _class in modules_dict.items():
	class_name = f"{prefix}_{module_postfix}"
	globals()[class_name] = type ( class_name, (_class,), {})
# logger.info ( f" globals().keys(): {globals().keys()}")

manager_dict = {'TableDataManager':TableDataManager,'TableMenuManager':TableMenuManager ,'TableUiManager':TableUiManager}
for prefix, _class in manager_dict.items():
	class_name = f"{prefix}_{module_postfix}"
	globals()[class_name] = type ( class_name, (_class,), {})
    # 만약 TableUiManager라면 module_postfix 재설정
	### 🤣key가 globals() 와 module_postfix를 override하는 것이 필요함 ==> 자동 생성가능
	if prefix == 'TableUiManager':
		globals()[class_name].__init__ = ( lambda self, parent_widget: 
		(_class.__init__(self, parent_widget), setattr( self, 'globals_dict', globals() ), setattr(self, 'module_postfix', module_postfix))[0] )

###### 🤣🤣🤣🤣🤣




# class TableUiManager_JOB_INFO(TableUiManager):
#     def __init__(self, parent_widget: QWidget):
#         super().__init__(parent_widget)
#         # 부모 클래스에서 설정된 module_postfix를 JOB_INFO로 재설정
#         self.module_postfix = module_postfix
#         self.globals_dict = globals()

class Base_Wid_Table(QWidget):
	"""테이블 위젯을 구성하는 클래스"""
	signal_refresh = pyqtSignal()
	signal_select_row = pyqtSignal(dict)
	signal_select_rows = pyqtSignal(list)

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		
		self.globals_dict : dict = {} 
		self.module_postfix : str = ''
		self.table_name : str = ''
		self._update_data(**kwargs)
		self.run()


	def register_manager(self):
		"""manager 등록"""
		try:
			logger.info(f"register_manager : {self.globals_dict.get(f'TableDataManager_{self.module_postfix}')}")
			logger.info(f"register_manager : {self.globals_dict.get(f'TableMenuManager_{self.module_postfix}')}")
			logger.info(f"register_manager : {self.globals_dict.get(f'TableUiManager_{self.module_postfix}')}")
			logger.info ( f" register_manager : {self.table_name}")
			logger.info ( f" register_manager : {self}")
			self.data_manager:TableDataManager = self.globals_dict.get(f'TableDataManager_{self.module_postfix}')(self)
			self.menu_manager:TableMenuManager = self.globals_dict.get(f'TableMenuManager_{self.module_postfix}')(self)
			self.ui_manager:TableUiManager = self.globals_dict.get(f'TableUiManager_{self.module_postfix}')(self)
		except Exception as e:
			logger.error(f"register_manager 오류: {e}")
			logger.error(f"{traceback.format_exc()}")


	def _update_data(self, **kwargs):
		"""데이터 업데이트 및 테이블 구성"""
		self.kwargs = kwargs if kwargs else None
		if self.kwargs:
			# 기타 속성 설정
			for key, value in kwargs.items():
				setattr(self, key, value)
				# logger.info(f"{key} : {value}")
			
			if hasattr(self, 'div') and hasattr( self, 'name'):
				self.make_table_name()

	def make_table_name(self, div:str='', name:str='', id:str=''):
		""" table_name 생성 """    
		try: 
			if not div:
				div = self.div
			if not name:
				name = self.name
			if not id:
				id = self.id
			self.table_name = f"{div}_{name}_appID_{id}"
			return self.table_name
		except Exception as e:
			logger.error(f"make_table_name 오류: {e}")
			return None


	def run(self):
		"""테이블 구성 및 초기화"""
		try:
			logger.info(f"run : {self.table_name}")
			# UI 초기화
			self.ui_manager.clear_layout()
			
			# 모델 데이터 생성
			logger.info ( f" :run : self.data_manager : {self.data_manager}")
			model_data, table_config = self.data_manager.builder()
			logger.info(f"run : {self.table_name} 모델 데이터 {len(model_data)} 생성 완료")

				# 테이블 모델 및 뷰 생성
			self.ui_manager.create_table_model(model_data, table_config)
			self.ui_manager.create_table_view()
			
			# 모델과 뷰 연결
			self.ui_manager.connect_model_to_view()
			
			# 테이블 메뉴 핸들러 연결
			# self._connect_signals()
			
			# 레이아웃에 추가
			self.ui_manager.add_table_to_layout()

			self.connect_signals()

			
			self.show()
			logger.info(f"run : {self.table_name} 완료")
		except Exception as e:
			logger.error(f"run 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	def connect_signals(self):
		"""시그널 연결"""
		try:
			### ui 관련 시그널 연결
			self.ui_manager.connect_ui_signals()
		# 테이블 뷰 시그널
			# table_view = self.ui_manager.table_view
			# table_view.signal_select_rows.connect(self.signal_select_rows.emit)
			# table_view.signal_table_config_mode.connect ( self.slot_table_config_mode )
			# table_view.signal_table_config_mode.connect(lambda is_active: self.ui_manager.set_mode_status(is_active))
			# table_view.signal_table_save_config_api_datas.connect(lambda _is_ok: self.slot_save_table_config_api_datas(_is_ok))
			
			# 테이블 모델 시그널
			# table_model = self.ui_manager.table_model
			# table_model.signal_data_changed.connect(self.slot_signal_model_data_changed)
		
			# 메뉴 핸들러 설정
			# self._setup_menu_handler()
		
		except Exception as e:
			logger.error(f"시그널 연결 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	# def slot_table_config_mode(self, is_active:bool):
	# 	"""테이블 설정 모드 활성화"""
	# 	logger.info(f"slot_table_config_mode : {is_active}")
	# 	self.ui_manager.set_mode_status(is_active)

	# def slot_save_table_config_api_datas(self, is_ok:bool):
	# 	"""테이블 설정 모드 활성화"""
	# 	User_Toast(INFO.MAIN_WINDOW, duration=1000, text=f"테이블 설정 저장 완료" if is_ok else "테이블 설정 저장 실패")
	# 	logger.info(f"slot_table_config_api_datas : {is_ok}")

	# def _setup_menu_handler(self):
	# 	"""메뉴 핸들러 설정"""
	# 	return
	# 	# 메뉴 핸들러에 필요한 메서드 연결
	# 	# self.menu_manager.set_parent_widget(self)
	# 	# self.menu_manager.register_menu_action('파일_업로드', self.menu__파일_업로드)
	# 	# self.menu_manager.register_menu_action('파일_다운로드', self.menu__파일_다운로드)
	# 	# self.menu_manager.register_menu_action('new_row', self.menu__new_row)
	# 	# self.menu_manager.register_menu_action('upgrade_row', self.menu__upgrade_row)
		
	# 	# 테이블 뷰 메뉴 시그널 연결
	# 	table_view = self.ui_manager.table_view
	# 	table_view.signal_vMenu.connect(self.menu_manager.handle_menu)
	# 	table_view.signal_hMenu.connect(self.menu_manager.handle_menu)
	# 	table_view.signal_cellMenu.connect(self.menu_manager.handle_menu)

	# def slot_delegate_closeEditor(self, editor: QWidget, hint: QAbstractItemDelegate.EndEditHint):
	# 	"""
	# 	delegate의 closeEditor 시그널에 연결될 슬롯 함수
		
	# 	Args:
	# 		editor: 편집이 완료된 위젯
	# 		hint: 편집 종료 힌트
	# 	"""
	# 	# 필요한 처리 로직 구현
	# 	pass

	# def _create_model_data(self, api_data:list[dict]=[], table_header:list[str]=[] ) ->list[list]:
	# 	"""
	# 		api_data : list[dict]
	# 		table_header : list[str]
	# 	"""
	# 	api_data = api_data or self.api_data
	# 	table_header = table_header or self.table_config.get('_headers', [])
	# 	model_data = []
	# 	for _obj in api_data:
	# 		model_data.append ( [ _obj.get(headName, '') for headName in table_header ] )
	# 	return model_data

	# def gen_Model_data_from_API_data(self, api_DB_data:list[dict]=[] ) ->list[list]:  		
	# 	api_DB_data = api_DB_data if api_DB_data else self.api_data
		
	# 	_data = []
	# 	for obj in api_DB_data:
	# 		_data.append ( self.get_table_row_data(obj) )
	# 	return _data

	# def get_table_row_data(self, obj:dict) -> list:		
	# 	return [ self._get_table_cell_value(key, obj) for key in self.table_header ]

	# def _get_table_cell_value(self, key:str, obj:dict) ->str:
	# 	""" """
	# 	value = obj.get(key , None)
	# 	return value
