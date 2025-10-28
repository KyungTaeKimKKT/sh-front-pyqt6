from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Dict, List, Tuple, Any, Union, Callable
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table.table_mixin import TableConfigMixin, TableMenuMixin

from datetime import date
import os
import copy
import time
from pathlib import Path

#### import Custom StyleSheet
from stylesheet import StyleSheet
### import custom widgets 😀😀
from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.my_spinbox import My_SpinBox
from modules.PyQt.component.my_dateedit import My_DateEdit

# from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_ReadOnly
from modules.PyQt.User.wid_value import Widget_Get_Value, Widget_Set_Value
import modules.user.utils as Utils
from modules.envs.resources import resources as RES
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

# 위젯 매니저 임포트
from modules.PyQt.compoent_v2.widget_manager import WidgetManager, FieldTypes

if TYPE_CHECKING:
	from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model

class EditModes:
	ROW = 'row'
	CELL = 'cell'

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



class Base_Delegate(QStyledItemDelegate, LazyParentAttrMixin, TableConfigMixin ):
	""" 필수 kwarg \n
		table_header= list[str], \n
		header_type = dict{str:str}, \n
		no_Edit_cols = list[str]
	"""
	#### editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, 
	### _sendData:dict, files:object
	commitEdit = pyqtSignal(object, object, object, object, dict,dict, object) 

	def __init__(self, parent):
		"""
		Base_Delegate 초기화
		
		Args:
			parent: 부모 위젯
			**kwargs: 추가 설정 (table_header, header_type, no_Edit_cols 등)
		"""
		super().__init__(parent)
		self.lazy_attr_names = INFO.Table_Delegate_Lazy_Attr_Names  #['table_name', 'no_edit_columns_by_coding', 'custom_editor_info']
		self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
		self.lazy_ready_flags: dict[str, bool] = {}
		self.lazy_attr_values: dict[str, Any] = {}

		self.start_init_time = time.perf_counter()
		self.event_bus = event_bus
		self.table_name = ''
		

		self._init_attributes()
		# 위젯 매니저 인스턴스 가져오기
		self.widget_manager = WidgetManager.instance()
		self.run_lazy_attr()


	def _init_attributes(self):
		"""
		속성을 초기화합니다.
		"""

		# 내부 상태 변수
		self._setting_editor_data = False
		self._column_info_cache = {}
		
		# 테이블 설정 변수
		self.table_config: Dict[str, Any] = {}
		self._table_name: Optional[str] = None
		self._table_config_api_datas: Optional[List[Dict[str, Any]]] = None
		self._mapping_headers: Optional[Dict[str, str]] = {}	### { 'column_name': 'display_name' }
		self._mapping_reverse_headers: Optional[Dict[str, str]] = {}	### { 'display_name': 'column_name' }
		self._headers: List[str] = []
		self._hidden_columns: Optional[List[int]] = []
		self._no_edit_cols: Optional[List[str]] = []
		self._column_types: Dict[str, str] = {}
		self._column_styles: Dict[str, str] = {}
		self._column_widths: Dict[str, int] = {}
		self._table_style: Optional[str] = None

		# 커스텀 셀 에디터 관련 변수 추가
		self._custom_editors = {}  # 컬럼명 -> 에디터 정보
		self._custom_editor_handlers = {}  # 컬럼명 -> 핸들러 함수
		self._custom_data_updaters = {}  # 컬럼명 -> 데이터 업데이트 함수
		
		
		self.ST = StyleSheet
	

	def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
		if self.lazy_ready_flags.get(attr_name):
			return  # 이미 처리된 attr이면 무시
		if INFO.IS_DEV:
			logger.debug(f"{self.__class__.__name__} : on_lazy_attr_ready : {attr_name} : {attr_value}")
		self.lazy_ready_flags[attr_name] = True
		self.lazy_attr_values[attr_name] = attr_value
		
		if all(self.lazy_ready_flags.get(name, False) for name in self.lazy_attr_names + self.lazy_ws_names):
			if INFO.IS_DEV:
				logger.info(f" {self.parent().__class__.__name__}  {self.__class__.__name__} all lazy attrs ready : 소요시간 : {Utils.get_소요시간(self.start_init_time)}")
			self.on_all_lazy_attrs_ready()
		else:
			not_ready = [name for name in self.lazy_attr_names + self.lazy_ws_names if not self.lazy_ready_flags.get(name, False)]

	
	def on_all_lazy_attrs_ready(self):		
		try:

			APP_ID = self.lazy_attr_values['APP_ID']
			self.table_name = Utils.get_table_name(APP_ID)
			self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
			self.custom_editor_info = self.lazy_attr_values['custom_editor_info']
			self.no_edit_columns_by_coding = self.lazy_attr_values['no_edit_columns_by_coding']
			if 'is_no_config_initial' in self.lazy_attr_values and self.lazy_attr_values['is_no_config_initial']:
				return
			else:
				self.table_config = INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig']
			# self.subscribe_gbus()

		except Exception as e:
			logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			Utils.generate_QMsg_critical(None, title="서버 조회 오류: Base_Delegate", text="on_all_lazy_attrs_ready 오류{e}" )
			# raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")
		

	def subscribe_gbus(self):				
		self.event_bus.subscribe( f"{self.table_name}:table_config", self.on_table_config )

		# self.event_bus.subscribe( f"{self.table_name}:table_config_api_datas", self.on_table_config_api_datas )

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe( f"{self.table_name}:table_config" )
		# self.event_bus.unsubscribe( f"{self.table_name}:table_config_api_datas" )

	def on_table_config(self, table_config:dict):
		""" table_config를 받으면 속성값으로 setting함."""
		# self.on_lazy_attr_ready('table_config', table_config)
		if self.table_name and table_config and isinstance(table_config, dict):
			self.table_config = table_config
		else:
			logger.warning(f"table config is ready , but  api_datas is None")
	

	def is_all_no_edit(self):
		if 'no_edit_columns_by_coding' in self.lazy_attr_values:
			no_edit = self.lazy_attr_values['no_edit_columns_by_coding']
			return  'ALL' in no_edit  or 'All' in no_edit or 'all' in no_edit
		return False
	

	### method override
	def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
		super().initStyleOption(option, index)
		if self.is_all_no_edit():
			return None
			
		model : Base_Table_Model = index.model()
		if model is None:
			return None
		
		# 마우스 오버 시 글자 굵게 or 기울임
		if option.state & QStyle.State_MouseOver:
			if hasattr(model, "_is_editable") and callable(model._is_editable):
				if model._is_editable(index):
					option.font.setBold(True)
				else:
					option.font.setItalic(True)

		option.textElideMode = Qt.TextElideMode.ElideRight

		if hasattr(model, "_is_editable") and callable(model._is_editable):
			if not model._is_editable(index):
				option.font.setItalic(True)

	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
		model: Base_Table_Model = index.model()
		editable = model._is_editable(index)

		opt = QStyleOptionViewItem(option)  # 원본 훼손 막기 위해 복사
		super().paint(painter, opt, index)
		if self.is_all_no_edit():
			return None
		
		if not editable:
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
		if INFO.IS_DEV:
			logger.info(f"Base_Delegate.run() : self._table_name : {self._table_name} , self._headers : {self._headers} , self._no_edit_cols : {self._no_edit_cols}")
		

	def get_column_info(self, index:QModelIndex) -> tuple[str, str, Any, Any, str]:
		"""
		열 정보를 가져오는 함수, 
		return은 tuple( header_name, db_attr_name, api_data_value, display_value, value_type )
		"""
		try:
			model  = index.model()
			header_name = model._headers[index.column()]
			db_attr_name = self.table_config['_mapping_display_to_attr'][header_name] if self.table_config else header_name
			api_data_value = index.data(Qt.ItemDataRole.EditRole)
			display_value = index.data(Qt.ItemDataRole.DisplayRole)
			value_type = self.table_config['_column_types'].get(db_attr_name, 'C') if self.table_config else 'C'
			return header_name, db_attr_name, api_data_value, display_value, value_type
		except Exception as e:
			logger.error(f"get_column_info error: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"get_column_info error: {e}")

	def _is_no_editable(self, index:QModelIndex) -> bool:
		""" tablemodel의 _is_editable 메서드를 통해 편집 가능 여부를 확인함 """
		model : Base_Table_Model = index.model()
		if hasattr(model, '_is_editable') and callable(model._is_editable):
			return not model._is_editable(index)
		else:
			raise ValueError(f"model._is_editable is not callable: {model._is_editable}")
		
	def _is_custom_editor_column(self, db_attr_name:str) -> bool:
		""" custom_editor_info 속성이 있는지 확인함 """
		if 'custom_editor_info' in self.lazy_attr_values :
			return db_attr_name in self.lazy_attr_values['custom_editor_info']	
		return False
	
	def get_custom_editor(self, db_attr_name:str) -> Optional[Callable]:
		try:
			return self.lazy_attr_values['custom_editor_info'][db_attr_name]
		except Exception as e:
			logger.error(f"get_custom_editor error: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"get_custom_editor error: {e}")


	def createEditor(self, parent: Optional[QObject], option: QStyleOptionViewItem, index: QModelIndex) -> Optional[QWidget]:
		"""
		인덱스 위치에 맞는 에디터 위젯을 생성합니다.
		_column_types에 정의된 타입에 따라 적절한 위젯을 반환합니다.
		"""
		display_name, db_attr_name, api_data_value, display_value, value_type = self.get_column_info(index)
		if self._is_no_editable(index) or self._is_custom_editor_column(db_attr_name):
			return None

		# 테이블 헤더와 컬럼 타입 정보 가져오기

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
				
			Widget_Set_Value.setValue(editor, api_data_value)
			
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

	def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
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




	def editorEvent(self, event: QEvent, model: QAbstractItemModel, 
				   option: QStyleOptionViewItem, index: QModelIndex) -> bool:
		"""
		셀 이벤트 처리 - 커스텀 에디터 핸들러 호출
		"""
		try:
			display_name, db_attr_name, api_data_value, display_value, value_type = self.get_column_info(index)

			if self._is_no_editable(index) or not self._is_custom_editor_column(db_attr_name):
				return False
			editor_class = self.get_custom_editor( db_attr_name )
			
			# 더블클릭 이벤트 및 등록된 핸들러가 있는 경우
			if editor_class and event.type() == QEvent.Type.MouseButtonDblClick:
				return self.custom_editor_handler(db_attr_name, editor_class, event, model, option, index)

			# 기본 이벤트 처리
			return super().editorEvent(event, model, option, index)
		
		except Exception as e:
			logger.error(f"에디터 이벤트 처리 오류: {e}")
			logger.error(traceback.format_exc())
			return False
	

	def custom_editor_handler(self, db_attr_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
		return False