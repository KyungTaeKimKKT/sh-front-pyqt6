from __future__ import annotations  ### SyntaxError: from __future__ imports must occur at the beginning of the file
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from local_db.models import Table_Config

from datetime import date, datetime, timedelta
import copy, json

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

from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger	# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

if TYPE_CHECKING:
	from modules.PyQt.Tabs.plugins.table.Base_Wid_Table import Base_Wid_Table

class TableUiManager:
	"""테이블 UI 관리를 담당하는 클래스"""

	def __init__(self, handler:QWidget):
		self.event_bus = event_bus
		self.handler:Optional[Base_Wid_Table] = handler
		self.table_view: Optional[Base_Table_View] = None
		self.table_model: Optional[Base_Table_Model] = None
		self.delegate: Optional[My_Table_Delegate] = None
		self.layout: Optional[QVBoxLayout] = None
		self.module_postfix = __name__.split('.')[-1].split('__')[-1]
		self.globals_dict = globals()
		self.table_name = self.handler.table_name
		self.register_events()
		logger.info(f" :__init__ : {self.table_name}")
	
	def register_events(self):
		"""이벤트 등록 ... 여기서 key가 module_postfix"""
		event_bus.subscribe(f'{self.module_postfix}:{GBus.TABLE_DATA_REFRESH}', self.refresh_ui)
		# self.module_postfix = self.find_module_postfix()
		logger.info(f" :register_events : module_postfix : {self.module_postfix}")

	def refresh_ui(self, data:list[dict]):
		""" 테이블 UI 업데이트 Event 처리"""
		logger.info(f" :refresh_ui : {GBus.TABLE_DATA_REFRESH} 수신: {len(data)}개 table model 업데이트")
		self.table_model.beginResetModel()
		self.table_model.set_data(data)
		self.table_model.endResetModel()


	def setup_layout(self):
		"""레이아웃 설정"""
		try:
			self.layout = QVBoxLayout()
			self.handler.setLayout(self.layout)
			self.layout.addWidget(self.ui_header_widget())
			return self.layout
		except Exception as e:
			logger.error(f"레이아웃 설정 중 오류 발생: {e}")
			return None
	
	def ui_header_widget(self):
		"""헤더 위젯 생성"""
		self.header_widget = QWidget()
		self.header_layout = QHBoxLayout()
		self.label_header = QLabel("Data Update시간")
		self.label_header.setStyleSheet("font-weight: bold;")
		self.label_update_time = QLabel("")		
		self.header_layout.addWidget(self.label_header)
		self.header_layout.addWidget(self.label_update_time)
		self.header_layout.addStretch()

		self.label_mode = QLabel("테이블 설정 모드")
		self.label_mode.setStyleSheet("font-weight: bold;")
		self.header_layout.addWidget(self.label_mode)
		self.label_mode_status = QLabel("비활성")
		self.label_mode_status.setStyleSheet("font-weight: bold;")
		self.header_layout.addWidget(self.label_mode_status)
		self.header_layout.addStretch()

		self.button_cancel = QPushButton("설정 취소")
		self.button_cancel.setStyleSheet("font-weight: bold;")
		self.header_layout.addWidget(self.button_cancel)

		self.button_save = QPushButton("설정 저장")
		self.button_save.setStyleSheet("font-weight: bold;")
		self.header_layout.addWidget(self.button_save)
		self.header_layout.addStretch()	

		self.header_widget.setLayout(self.header_layout)

		self.set_mode_status(False)
		return self.header_widget
	
	def set_mode_status(self, is_active:bool):
		"""테이블 설정 모드 상태 설정"""
		self.label_mode_status.setText("활성" if is_active else "비활성")
		self.label_mode.setVisible(is_active)
		self.label_mode_status.setVisible(is_active)
		self.button_cancel.setVisible(is_active)
		self.button_save.setVisible(is_active)
	
	def set_update_time(self, time_str:str):
		"""업데이트 시간 설정"""
		if not self.label_update_time:
			time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
		self.label_update_time.setText(time_str)
		self.label_update_time.setStyleSheet("font-weight: bold;")

	def clear_layout(self):
		"""레이아웃 초기화"""
		try:
			if self.layout:
				Utils.deleteLayout(self.layout)
				self.layout = self.setup_layout()
		except Exception as e:
			logger.error(f"레이아웃 초기화 중 오류 발생: {e}")
			
	def create_table_view(self):
		"""테이블 뷰 생성"""
		# raise NotImplementedError("테이블 뷰 생성 메서드는 하위 클래스에서 구현")
		try:
			logger.info(f"테이블 뷰 생성 시작: {self.module_postfix}")			
			self.table_view = self.globals_dict.get(f"TableView_{self.module_postfix}")(self.handler)
			logger.info(f"테이블 뷰 생성 완료: {self.table_view}")
			return self.table_view
		except Exception as e:
			logger.error(f"테이블 뷰 생성 중 오류 발생: {e}")
			logger.error(f"{traceback.format_exc()}")
			return None
			
	def create_table_model(self, model_data, table_config):
		"""테이블 모델 Instance ( self.table_model ) 생성"""
		# raise NotImplementedError("테이블 모델 생성 메서드는 하위 클래스에서 구현")
		try:
			if not model_data or not table_config:
				logger.warning("모델 데이터 또는 테이블 설정이 없읍니다")
				return None
				
			self.table_model = (
				TableModelBuilder()
				.with_data(model_data)
				.with_table_config(table_config)
				.build()
			)
			return self.table_model
		except Exception as e:
			logger.error(f"테이블 모델 생성 중 오류 발생: {e}")
			return None
		
	def connect_model_to_view(self):
		"""모델과 뷰 연결"""
		logger.info(f"connect_model_to_view : {self.table_model}, {self.table_view}")
		try:
			if self.table_model and self.table_view:
				self.table_model.configure_table_view(self.table_view)
				return True
			else:
				logger.warning("모델 또는 뷰가 없어 연결할 수 없읍니다")
				return False
		except Exception as e:
			logger.error(f"모델과 뷰 연결 중 오류 발생: {e}")
			logger.error(f"{traceback.format_exc()}")
			return False
			
	def add_table_to_layout(self):
		"""테이블을 레이아웃에 추가"""
		try:
			if not self.layout:
				self.layout = self.setup_layout()
				logger.info(f"add_table_to_layout - layout 생성: {self.layout}")
			
			if not self.table_view:
				logger.error("테이블 뷰가 생성되지 않았읍니다")
				return False
				
			logger.info("테이블 뷰를 레이아웃에 추가합니다")
			self.layout.addWidget(self.table_view)
			
			# 테이블 뷰 크기 정책 설정
			self.table_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
			self.table_view.setMinimumHeight(300)
			
			logger.info(f"테이블 뷰 크기: {self.table_view.size()}")
			logger.info(f"테이블 뷰 가시성: {self.table_view.isVisible()}")
			return True
		except Exception as e:
			logger.error(f"테이블을 레이아웃에 추가하는 중 오류 발생: {e}")
			logger.error(f"{traceback.format_exc()}")
			return False

	def connect_ui_signals(self):
		"""UI 관련 시그널 연결"""
		try:
			# 버튼 시그널 연결
			self.button_cancel.clicked.connect(self.on_cancel_config)
			self.button_save.clicked.connect(self.on_save_config)
			
			# 기타 UI 관련 시그널 연결
			return True
		except Exception as e:
			logger.error(f"UI 시그널 연결 중 오류 발생: {e}")
			return False

	def on_cancel_config(self):
		"""설정 취소 버튼 클릭 시 처리"""
		if self.table_view:
			# 테이블 설정 모드 비활성화
			self.table_view.set_config_mode(False)
			# 원래 데이터로 복원
			self.set_mode_status(False)
			logger.info("테이블 설정 취소됨")

	def on_save_config(self):
		"""설정 저장 버튼 클릭 시 처리"""
		if self.table_view:
			# 테이블 설정 저장 로직
			self.table_view.save_config()
			self.set_mode_status(False)
			logger.info("테이블 설정 저장됨")

	
	def find_module_postfix(self):
		"""
		현재 객체에서 시작하여 부모 객체들을 재귀적으로 탐색하며
		'module_postfix' 속성을 찾아 반환합니다.
		
		Returns:
			module_postfix 속성 값 또는 속성을 찾지 못한 경우 None
		"""
		# 현재 객체에 module_postfix 속성이 있는지 확인
		if hasattr(self, 'module_postfix'):
			return self.module_postfix
		
		# 현재 객체에 parent 속성이 있는지 확인
		if hasattr(self, 'parent'):
			parent = self.parent
			
			# parent가 None이 아니고 객체인 경우
			if parent is not None and isinstance(parent, object):
				# parent 객체에서 재귀적으로 module_postfix 찾기
				try:
					# parent 객체에 find_module_postfix 메서드가 있는 경우
					if hasattr(parent, 'find_module_postfix') and callable(getattr(parent, 'find_module_postfix')):
						return parent.find_module_postfix()
					# parent 객체에 module_postfix 속성이 있는 경우
					elif hasattr(parent, 'module_postfix'):
						return parent.module_postfix
					# 그 외의 경우 None 반환
					else:
						return None
				except Exception:
					return None
		
		# module_postfix를 찾지 못한 경우 None 반환
		return None