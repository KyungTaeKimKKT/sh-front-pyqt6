from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Dict, List, Tuple, Any, Union, Callable
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config

from datetime import date
import os
import copy
import time
from pathlib import Path

#### import Custom StyleSheet
from stylesheet import StyleSheet
### import custom widgets 😀😀


import modules.user.utils as Utils
from modules.envs.resources import resources as RES
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

# 위젯 매니저 임포트
from modules.PyQt.compoent_v2.widget_manager import WidgetManager, FieldTypes

if TYPE_CHECKING:
	from modules.PyQt.compoent_v2.table_v3.Base_Table_Model import Base_Table_Model


class AlignDelegate(QStyledItemDelegate):
	def __init__(self, parent: Optional[QObject], user_pks:list):
		super().__init__()
		self.user_pks = user_pks
		self.selected_row = -1
	
	def initStyleOption(self, option, index):
		super(AlignDelegate, self).initStyleOption(option, index)
		option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
		value = index.data()
		if (value:=index.data()) in self.user_pks:
			self.selected_row = index.row()
		
		if self.selected_row  == index.row():
			option.palette.setBrush(
				QPalette.Text, QBrush(QColor("black"))
			)
			option.backgroundBrush = QBrush(QColor("yellow"))
		else:
			option.backgroundBrush = QBrush(QColor("white"))



class Base_Delegate(
	QStyledItemDelegate, 
	# LazyParentAttrMixin, 
	Mixin_Table_Config 
	):
	""" V3 버전 
	필수 kwarg \n
		table_header= list[str], \n
		header_type = dict{str:str}, \n
		no_Edit_cols = list[str]
	"""

	def __init__(self, parent:Optional[QWidget], **kwargs):
		"""
		Base_Delegate 초기화
		
		Args:
			parent: 부모 위젯 ( table_view )
			**kwargs: 추가 설정 (table_header, header_type, no_Edit_cols 등)
		"""
		super().__init__(parent)
		# self.lazy_attr_names = INFO.Table_Delegate_Lazy_Attr_Names  #['table_name', 'no_edit_columns_by_coding', 'custom_editor_info']
		# self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
		# self.lazy_ready_flags: dict[str, bool] = {}
		self.lazy_attr_values: dict[str, Any] = {}

		self.start_init_time = time.perf_counter()
		self.event_bus = event_bus
		self.table_name = ''

		self.map_name_to_editor_instance: dict[str, Any] = {}
		

		self._init_attributes()
		self._initialize_from_kwargs(**kwargs)
		# 위젯 매니저 인스턴스 가져오기
		self.widget_manager = WidgetManager.instance()
		# self.run_lazy_attr()

	def get_cached_editor(self, db_attr_name:str) -> Optional[Any]:
		return self.map_name_to_editor_instance.get(db_attr_name, None)

	def set_cached_editor(self, db_attr_name:str, editor_instance:Any):
		self.map_name_to_editor_instance[db_attr_name] = editor_instance


	def _init_attributes(self):
		"""
		속성을 초기화합니다.
		"""
		pass
		
	def _initialize_from_kwargs(self, **kwargs):
		"""kwargs로부터 모델 속성 초기화"""
		# kwargs로 초기화
		if kwargs  :
			self.kwargs = kwargs
			if 'set_kwargs_to_attr' not in kwargs or kwargs['set_kwargs_to_attr']:
				for key, value in kwargs.items():			
					setattr(self, key, value)

	def on_all_lazy_attrs_ready(self, APP_ID:Optional[int] = None, lazy_attr_values:dict = {}, **kwargs):
		self.mixin_on_all_lazy_attrs_ready(APP_ID, lazy_attr_values=lazy_attr_values, **kwargs)
		self.lazy_attr_values = lazy_attr_values
		self.custom_editor_info = lazy_attr_values.get('custom_editor_info', {})
		self.no_edit_columns_by_coding = lazy_attr_values.get('no_edit_columns_by_coding', [])
	
	def on_table_config_refresh(self, is_refresh:bool=True):
		self.mixin_on_table_config_refresh(is_refresh)



	def subscribe_gbus(self):				
		return 
		self.event_bus.subscribe( f"{self.table_name}:table_config", self.on_table_config_refresh )

		# self.event_bus.subscribe( f"{self.table_name}:table_config_api_datas", self.on_table_config_api_datas )

	def unsubscribe_gbus(self):
		return 
		self.event_bus.unsubscribe( f"{self.table_name}:table_config" )
		# self.event_bus.unsubscribe( f"{self.table_name}:table_config_api_datas" )

	
	def is_all_no_edit(self) ->bool:
		model : Base_Table_Model = self.parent().model()
		return model.is_all_no_edit()
	
	
	def _is_editable(self, index:QModelIndex) ->bool:
		model : Base_Table_Model = self.parent().model()
		return model._is_editable(index)


	def createEditor(self, parent: Optional[QObject], option: QStyleOptionViewItem, index: QModelIndex) -> Optional[QWidget]:
		"""
		인덱스 위치에 맞는 에디터 위젯을 생성합니다.
		_column_types에 정의된 타입에 따라 적절한 위젯을 반환합니다.
		"""
		display_name, db_attr_name, api_data_value, display_value, value_type = self.get_column_info(index)
		if not self._is_editable(index) or self._is_custom_editor_column(db_attr_name):
			return None

		# 위젯 매니저를 통해 위젯 생성
		widget = self.widget_manager.create_widget(parent, value_type)
		
		# 사용자 정의 설정 적용
		return self.user_defined_creatorEditor_설정(
			widget, 
			headerName=display_name, 
			value=api_data_value, 
			parent=parent, 
			index=index, 
			option=option
			)



	def setEditorData(self, editor:QWidget, index:QModelIndex):
		"""
		에디터에 데이터 설정
		"""
		try:
			# 재귀 방지를 위한 플래그 추가
			if hasattr(self, '_setting_editor_data') and self._setting_editor_data:
				return
			
			self._setting_editor_data = True
			
			row = index.row()
			col = index.column()
			
			# 테이블 헤더 정보 가져오기
			display_name, db_attr_name, api_data_value, display_value, value_type = self.get_column_info(index)		
				

			if isinstance(editor, QComboBox):
				model: Base_Table_Model = index.model()
				choices = model.get_choices(index)
				if choices:
					map_value_to_display = {item['value']: item['display'] for item in choices}
					editor.addItems( [item['display'] for item in choices] )
					value = model.data(index, Qt.ItemDataRole.EditRole)
					editor.setCurrentText(map_value_to_display.get(value, value))
					return 


			self.widget_manager.set_value(editor, api_data_value)
			
			# 사용자 정의 설정 적용
			self.user_defined_setEditorData(
				editor, 
				index, 
				row=row, 
				col=col, 
				headerName=display_name, 
				value=api_data_value
				)

		except Exception as e:
			logger.error(f"에디터 데이터 설정 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
		finally:
			# 플래그 초기화
			self._setting_editor_data = False

	def setModelData(self, editor: QWidget, model: Base_Table_Model, index: QModelIndex) -> None:
		if isinstance(editor, QDateEdit ):
			model.setData(index, editor.date().toString('yyyy-MM-dd'), Qt.ItemDataRole.EditRole)
		
		elif isinstance(editor , QDateTimeEdit):
			model.setData(index, editor.dateTime().toString('yyyy-MM-dd HH:mm:ss'), Qt.ItemDataRole.EditRole)
		
		else:
			return super().setModelData(editor, model, index)



	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex, headerName:str, value:Any, **kwargs) -> None:
		pass 

	def user_defined_creatorEditor_설정(self, widget:object, headerName:str, value:Any,  parent, index, option) -> object:
		self.current_editor = widget
		return widget




	def editorEvent(self, 
					event: QEvent, 
					model: Base_Table_Model, 
					option: QStyleOptionViewItem, 
					index: QModelIndex
					) -> bool:
		"""
		셀 이벤트 처리 - 커스텀 에디터 핸들러 호출
		"""
		try:
			display_name, db_attr_name, api_data_value, display_value, value_type = self.get_column_info(index)
			if not self._is_editable(index) or not self._is_custom_editor_column(db_attr_name):
				return False
			# editor_class = self.get_custom_editor( db_attr_name )
			
			# 더블클릭 이벤트 및 등록된 핸들러가 있는 경우
			if  event.type() == QEvent.Type.MouseButtonDblClick:
				return self.custom_editor_handler(db_attr_name, event, model, option, index)

			# 기본 이벤트 처리
			return super().editorEvent(event, model, option, index)
		
		except Exception as e:
			logger.error(f"에디터 이벤트 처리 오류: {e}")
			logger.error(traceback.format_exc())
			return False
	

	def custom_editor_handler(self, db_attr_name:str,  event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
		return False


	### method override
	def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
		super().initStyleOption(option, index)
		if self.is_all_no_edit():
			return None
			
		model : Base_Table_Model = index.model()

		is_editable = self._is_editable(index)
		
		# 마우스 오버 시 글자 굵게 or 기울임
		if option.state & QStyle.State_MouseOver:
			if is_editable:
				option.font.setBold(True)
			else:
				option.font.setItalic(True)

		option.textElideMode = Qt.TextElideMode.ElideRight

		if not is_editable:
			option.font.setItalic(True)

	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):

		opt = QStyleOptionViewItem(option)  # 원본 훼손 막기 위해 복사
		super().paint(painter, opt, index)
		if self.is_all_no_edit():
			return None
		
		if not self._is_editable(index):
			try:
				painter.save()

				# 반투명하게 덮기 (기존 내용 살리면서 배경 느낌만)
				overlay = QColor("#f0f0f0")
				overlay.setAlpha(100)  # 반투명도 조정
				painter.fillRect(opt.rect, overlay)

				# 텍스트 다시 쓰기 (덮인 배경 위에 글씨)
				# painter.setPen(opt.palette.color(QPalette.Text))
				# text = index.data(Qt.DisplayRole)
				# painter.drawText(opt.rect.adjusted(20, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, str(text))

				# 아이콘
				# pixmap = RES.get_pixmap('toast:close')
				# if not pixmap.isNull():
				# 	lock_rect = QRect(opt.rect.left() + 4, opt.rect.top() + 2, 14, 14)
				# 	painter.drawPixmap(lock_rect, pixmap)

				painter.restore()
			except Exception as e:
				logger.error(f"paint error: {e}")

	def run(self):
		logger.info(f"Base_Delegate.run() : self._table_name : {self._table_name} , self._headers : {self._headers} , self._no_edit_cols : {self._no_edit_cols}")
		

	def get_column_info(self, index:QModelIndex) -> tuple[str, str, Any, Any, str]:
		"""
		열 정보를 가져오는 함수, 
		return은 tuple( header_name, db_attr_name, api_data_value, display_value, value_type )
		"""
		try:
			model : Base_Table_Model = index.model()
			display_name = model.get_display_name_by_index(index)
			db_attr_name = model.get_field_name_by_index(index)
			api_data_value = index.data(Qt.ItemDataRole.EditRole)
			display_value = index.data(Qt.ItemDataRole.DisplayRole)
			value_type = model.get_type_by_index(index)

			return display_name, db_attr_name, api_data_value, display_value, value_type
		except Exception as e:
			logger.error(f"get_column_info error: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"get_column_info error: {e}")
		
	def _is_custom_editor_column(self, db_attr_name:str) -> bool:
		""" custom_editor_info 속성이 있는지 확인함 """
		return db_attr_name in self.custom_editor_info
	
	
	def get_custom_editor(self, db_attr_name:str) -> Optional[Callable]:
		try:
			info= self.custom_editor_info[db_attr_name]
			print(f"info: {info}")
			import importlib
			module = importlib.import_module(info['module_name'])
			return getattr(module, info['class_name'])
		except Exception as e:
			logger.error(f"get_custom_editor error: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"get_custom_editor error: {e}")

