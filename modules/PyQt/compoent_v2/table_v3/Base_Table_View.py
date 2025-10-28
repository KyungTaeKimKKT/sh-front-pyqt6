from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing
import copy, json, time
from datetime import datetime

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table_v2.table_mixin import TableConfigMixin, TableMenuMixin
from modules.PyQt.compoent_v2.table_v2.Base_Table_Menu_Handler import Base_Table_Menu_Handler
from info import Info_SW as INFO
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
####
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()



from modules.PyQt.compoent_v2.table_v2.mixin_table_view import Mixin_Table_View
from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config
class Base_Table_View( QTableView,  
					  #LazyParentAttrMixin, 
					  Mixin_Table_View, 
					  Mixin_Table_Config
					  ):
	""" V3 버전 

	"""
	signal_vMenu = pyqtSignal(dict)
	signal_hMenu = pyqtSignal(dict)
	signal_cellMenu = pyqtSignal(dict)
	signal_hover = pyqtSignal(bool, int, QPoint) ### show 여부, rowNo와 mouse QPoint를 줌
	signal_select_row = pyqtSignal(dict)
	signal_select_rows = pyqtSignal(list)
	signal_table_config_mode = pyqtSignal(bool)
	signal_table_save_config_api_datas = pyqtSignal(bool)



	def __init__(self, parent: typing.Optional[QWidget] , **kwargs) -> None: 
		super().__init__(parent)

		self.wid_table = parent
		self.lazy_attr_values: dict[str, Any] = {}
		self.lazy_attrs = self.lazy_attr_values
		self._lazy_start_time = QTime.currentTime()
		self.start_init_time = time.perf_counter()

		self.basic_config_done = False
		self.event_bus = event_bus

		self.table_config_api_datas:list[dict] = []
		self.table_config:dict = {}

		self.model_instance = None
		self.table_name = None
		### self.table_config에 의해 설정됨

		# self.cell_menu_by_coding = []
		# self.v_header_menu_by_coding = []
		# self.h_header_menu_by_coding = []

		# ### action 3 ea 로 분리 ==> context.connect 도 3개로 분리
		# self.v_header_actions = []
		# self.h_header_actions = []
		# self.cell_menu_actions = {}
		# self.v_header_menus = []
		# self.h_header_menus = []
		# self.cell_menus = []

		self._selection_model_connected = False
		
		# self.menu_handler = Base_Table_Menu_Handler(self)


		# 모델 변경 감지 연결은 setModel 시점에, 모델 변경 시 자동으로 컬럼 너비 조정을 위한 연결
		self.model_connection = None
		self._span_connected = False

		# self.init_basic_config()

		# self.run_lazy_attr()


	def apply_stylesheet(self):
		# 수직 헤더 스타일시트 적용
		self.horizontalHeader().setStyleSheet("""
			QHeaderView::section { 
				color: blue;
				border: 1px solid #6c6c6c;
				font-weight:bold;
				font-size:bolder;
				text-align:center;			logger.debug(f"on_all_lazy_attrs_ready : self.table_name : {self.table_name}")
				padding-top:5px;
				padding-bottom: 5px;
						}
        """)                     
		self.verticalHeader().setStyleSheet("""
			QHeaderView::section {
				background-color: #e0e0e0;
				color: blue;
				border: 1px solid #6c6c6c;
				padding: 4px;
				width: 40px;
			}
		""")

	def init_basic_config(self):

		self.setWordWrap(True)

		self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers |
							QAbstractItemView.EditTrigger.DoubleClicked)
		# 수평 헤더 번호 표시 설정
		self.horizontalHeader().setVisible(True)
		self.verticalHeader().setVisible(True)

		# 수직 헤더에 번호 표시 설정
		self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
		# 수직 헤더 너비 설정
		self.verticalHeader().setDefaultSectionSize(30)  # 행 높이
		self.verticalHeader().setMinimumWidth(30)  # 최소 너비
		# self.verticalHeader().setFixedWidth(60)  # 고정 너비
		self.verticalHeader().setMaximumWidth(80)  # 고정 너비

		self.setFocusPolicy( Qt.FocusPolicy.StrongFocus)  # 키 이벤트 받을 수 있도록
		
		self.installEventFilter(self)

		self.setMouseTracking(True)

		# 컨텍스트 메뉴 정책 설정
		# self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		# self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		# self.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		# self.enable_context_menu_normal_mode()
		self.connect_signals()

		self.basic_config_done = True



	def enable_context_menu_normal_mode(self):
		try:
			self.customContextMenuRequested.connect(self.show_cell_context_menu)
			self.horizontalHeader().customContextMenuRequested.connect(self.show_h_header_context_menu)
			self.verticalHeader().customContextMenuRequested.connect(self.show_v_header_context_menu)
		except Exception as e:
			logger.error(f"enable_context_menu_normal_mode 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	def disable_context_menu_normal_mode(self):
		try:
			self.customContextMenuRequested.disconnect()
			self.horizontalHeader().customContextMenuRequested.disconnect()
			self.verticalHeader().customContextMenuRequested.disconnect()
		except Exception as e:
			logger.error(f"disable_context_menu_normal_mode 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	def keyPressEvent(self, event: QKeyEvent):           
		# Ctrl+F 누르면 검색 창 오픈
		if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
			self.mixin_open_search_dialog()
		else:
			super().keyPressEvent(event)

	def _initialize_from_kwargs(self, **kwargs):
		"""kwargs로부터 모델 속성 초기화"""
		# kwargs로 초기화
		if kwargs  :
			self.kwargs = kwargs
			if 'set_kwargs_to_attr' not in kwargs or kwargs['set_kwargs_to_attr']:
				for key, value in kwargs.items():			
					setattr(self, key, value)
	
	def on_all_lazy_attrs_ready(self, APP_ID:Optional[int]=None, **kwargs):
		if not self.basic_config_done:
			self.init_basic_config()
		self._initialize_from_kwargs(**kwargs)
		self.lazy_attr_values = kwargs.get('lazy_attr_values', {} )		
		self.lazy_attrs = self.lazy_attr_values
		if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
			raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
		self.appDict =  getattr(self.wid_table, "appDict", False)  or INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
		self.table_name = getattr( self.wid_table, "table_name", False ) or Utils.get_table_name(APP_ID)
		self.url = getattr( self.wid_table, "url", False )
		if not all ( [ self.appDict, self.table_name, self.url]):
			logger.error ( f'on_all_lazy_attrs_ready : self.appdict : {self.appDict}')
			logger.error ( f'on_all_lazy_attrs_ready : self.table_name : {self.table_name}')
			logger.error ( f'on_all_lazy_attrs_ready : self.url : {self.url}')
			raise ValueError( f'on_all_lazy_attrs_ready : self.appdict : {self.appDict} , self.table_name :{self.table_name}, self.url:{self.url}')
		# self.subscribe_gbus()

	def set_table_config(self, table_config:dict, table_config_api_datas:list[dict]):
		"""사장됨. 단 호환성 위해 유지됨 ==> 더이상 tableview 는  tableconfig 를 가지지 않음 : model에서 관리함"""
		return 
		
	
	def subscribe_gbus(self):
		pass
		# event_bus.subscribe(f"{self._table_name}:{GBus.TABLE_CONFIG_REFRESH}", self.slot_table_config_refresh)
		# event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)


	def unsubscribe_gbus(self):
		pass
		# event_bus.unsubscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
		# event_bus.unsubscribe(f"{self.table_name}:apply_table_config", self.apply_table_config)
	#####





	def on_selected_row_data(self, selected:QItemSelection, deselected:QItemSelection):
		""" 선택된 행의 데이터를 리스트 딕셔너리로 gbus emit """
		selected_rows = selected.indexes()
		selected_rows = set(index.row() for index in selected.indexes())
		if not selected_rows:
			return
		row_data = [self._get_row_data(row) for row in selected_rows]
		if INFO.IS_DEV:
			logger.info(f"{self.__class__.__name__} : on_selected_row_data : row_data : {row_data}")
		if self.table_name:
			self.event_bus.publish(f"{self.table_name}:selected_rows", row_data)
			#### ✅ 257-3 추가
			latest_rowNo = max(selected_rows)
			self.event_bus.publish(f"{self.table_name}:selected_rows_with_rowNo", {latest_rowNo: self._get_row_data(latest_rowNo)})
			### ✅ 25-8-20 추가 : 선택된 행에 따라 활성/비활성 처리
			if ( validate_menu_pb := getattr(self.parent(), 'validate_menu_pb', None) ) and callable(validate_menu_pb):
				validate_menu_pb(latest_rowNo)
			else:
				logger.info(f"validate_menu_pb is not found in parent widget")
		else:
			raise ValueError(f"table_name is not set")


	def _get_row_data(self, row) -> dict:
		"""주어진 행 번호의 데이터를 딕셔너리로 반환"""
		model:Base_Table_Model = self.model()
		return model.data(model.index(row, 0), Qt.ItemDataRole.UserRole)


	### override method
	
	def setModel(self, model:Base_Table_Model):
		""" 모델 설정시 layoutChanged signal 연결"""
		super().setModel(model)
		# 이전 연결이 있으면 해제
		if self.model_connection is not None:
			try:
				self.model().layoutChanged.disconnect(self.model_connection)
			except TypeError:
				pass  # 이전 모델이 사라졌거나 잘못된 연결
		
		# 새 모델의 layoutChanged 시그널에 컬럼 너비 조정 메서드 연결
		if model is not None:
			self.model_connection = model.layoutChanged.connect(self.layoutChanged_from_model)
			# dataChanged 연결
			try:
				model.dataChanged.disconnect(self.layoutChanged_from_model)
			except TypeError:
				pass
			model.dataChanged.connect(self.layoutChanged_from_model)
			### ✅ 25-8-20 추가 :  model 변경에  따라 self.parent().validate_menu_pb 실행함 : 즉 pb 활성/비활성 처리
			if ( validate_menu_pb := getattr(self.parent(), 'validate_menu_pb', None) ) and callable(validate_menu_pb):
				model.dataChanged.connect(validate_menu_pb)
				model.layoutChanged.connect(validate_menu_pb)
				model.modelReset.connect(validate_menu_pb)
				model.rowsInserted.connect(validate_menu_pb)
				model.rowsRemoved.connect(validate_menu_pb)
			else:
				logger.info(f"validate_menu_pb is not found in parent widget")



	def layoutChanged_from_model(self):
		""" 모델의 layoutChanged 시그널 처리 """
		try:
			model = self.model()
			col_hidden = getattr( model, '_column_hidden', None )
			col_width = getattr( model, '_column_widths', None )
			if col_hidden is None:
				raise ValueError('No col_hidden')
			if col_width is None:
				raise ValueError('No col width')			
			
			for col, header in enumerate( model._headers):
				self.setColumnHidden(col, col_hidden[header])
				width = col_width[header]
				if width == 0 :
					self.resizeColumnToContents(col)
				else:
					self.setColumnWidth(col, width)
			self._apply_spans()
		except Exception as e:
			logger.error (f" layoutChanged_from_model :{e}")


	def dataChanged_from_model(self):
		""" 모델의 dataChanged 시그널 처리 : 현재는 layoutChanged_from_model에서 다 처리함 """
		return 


	def connect_signals(self):
		try:
			if self.selectionModel():
				if not self._selection_model_connected:
					self.selectionModel().selectionChanged.connect(self.on_selected_row_data)
					self._selection_model_connected = True  # 연결 상태를 True로 설정
		except Exception as e:
			logger.error(f"connect_signals 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	def disconnect_signals(self):
		try:
			self.selectionModel().selectionChanged.disconnect()
		except Exception as e:
			logger.error(f"disconnect_signals 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
		finally:
			self._selection_model_connected = False

	def run(self):
		""" tablconfig를 가져옴 """
		pass


	def eventFilter(self, obj, event:QEvent):
		return super().eventFilter(obj, event)


	# def mousePressEvent(self, event):
	# 	if event.button() == Qt.MouseButton.RightButton:
	# 		logger.debug("Right click detected")
	# 	super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		index = self.indexAt(event.pos())
		if index.isValid():
			model = self.model()
			if hasattr( model, '_is_editable') and callable(model._is_editable):
				if not model._is_editable(index):
					self.viewport().setCursor(Qt.CursorShape.ForbiddenCursor)  # 🔒 또는 X 커서
				else:
					self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
		super().mouseMoveEvent(event)


	

	### span 적용 : clear 이후 setRowSpan 호출
	def _apply_spans(self):
		""" span 적용 : trigger 는 setModel 시점에 연결됨 
			self.set_row_span_list 가 있으면 적용 ;  [ ('일자', [] ), ] 형태로 attribute 이름과 병합할 컬럼 이름을 전달함
		"""
		self.clear_all_span()
		if hasattr( self, 'set_row_span_list') and self.set_row_span_list:     
			print(f"set_row_span_list: {self.set_row_span_list}")        
			for colName, subNames in self.set_row_span_list:
				print(f"colName: {colName}, subNames: {subNames}")
				self.setRowSpan(colName, subNames)
		### ✅ 25-7-21 추가 : table_view용 설정이 있으면 적용 ( app dict lazy_attr 에서 설정됨 )
		if hasattr ( self, 'lazy_attr_values' ) :
			if 'table_view용' in self.lazy_attr_values:
				set_row_span_list = self.lazy_attr_values['table_view용'].get('set_row_span_list', [])
				for colName, subNames in set_row_span_list:
					self.setRowSpan(colName, subNames)

	######## setSpan
	def setRowSpan( self, colName: str, subNames: list[str]) -> None:
		"""
		특정 컬럼의 행 병합
		kwargs:
			colName: str ( db attribute name)
			subNames: list[str] ( db attribute name list)
		"""
		model : Base_Table_Model = self.model()
		table_config =getattr ( model , 'table_config', None )
		if not table_config:
			logger.error(f"setRowSpan : table_config is not set")
			return

		if not model._data:
			logger.error(f"setRowSpan : _data is not set")
			return

		col_index = model.get_column_no_from_attr_name( colName )
		sub_indexes = [model.get_column_no_from_attr_name(subName) for subName in subNames]

		start_row = 0
		row_count = model.rowCount()

		def rows_match(r1: int, r2: int) -> bool:
			for idx in [col_index] + sub_indexes:
				v1 = self.model().index(r1, idx).data(Qt.ItemDataRole.DisplayRole)
				v2 = self.model().index(r2, idx).data(Qt.ItemDataRole.DisplayRole)
				if v1 != v2:
					return False
			return True

		while start_row < row_count:
			span = 1
			for next_row in range(start_row + 1, row_count):
				if rows_match(start_row, next_row):
					span += 1
				else:
					break
			if span > 1:
				self.setSpan(start_row, col_index, span, 1)
			start_row += span

	def clear_all_span(self):
		try:
			for row in range(self.model().rowCount()):
				for col in range(self.model().columnCount()):
					if self.rowSpan(row, col) > 1 or self.columnSpan(row, col) > 1:
						self.setSpan(row, col, 1, 1)
		except Exception as e:
			logger.error(f"clear_all_span 오류: {e}")
			logger.error(f"{traceback.format_exc()}")





	def on_file_view(self, rowNo:int, colNo:int):
		""" file view 시 호출되는 함수 """
		logger.info(f"on_file_view: {rowNo}, {colNo}")
		self.model().request_on_file_view(rowNo, colNo)

	def on_file_download(self, rowNo:int, colNo:int):
		""" file download 시 호출되는 함수 """
		logger.info(f"on_file_download: {rowNo}, {colNo}")
		self.model().request_on_file_download(rowNo, colNo)

	def on_file_delete(self, rowNo:int, colNo:int):
		""" file delete 시 호출되는 함수 """
		logger.info(f"on_file_delete: {rowNo}, {colNo}")
		self.model().request_on_file_delete(rowNo, colNo)

	def on_file_upload(self, rowNo:int, colNo:int):
		""" file upload 시 호출되는 함수 """
		logger.info(f"on_file_upload: {rowNo}, {colNo}")
		self.model().request_on_file_upload(rowNo, colNo)


	#### menu 관련
	def setup_menus(self):
		"""전체 메뉴 설정"""
		menus_dict = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_Menus', {})
		if not menus_dict:
			logger.warning(f"메뉴 설정을 찾을 수 없읍니다: {self.table_name}")
			return

		logger.debug(f"setup_menus : menus_dict : {type(menus_dict)}")
		logger.debug(f"setup_menus : menus_dict : {menus_dict}")
		for key,menu_list in menus_dict.items():
			setattr(self, f"{key}_menus", menu_list)


		if hasattr(self, 'cell_menu_by_coding'):
			self.cell_menus.extend(self.cell_menu_by_coding)
		if hasattr(self, 'v_header_menu_by_coding'):
			self.v_header_menus.extend(self.v_header_menu_by_coding)
		if hasattr(self, 'h_header_menu_by_coding'):
			self.h_header_menus.extend(self.h_header_menu_by_coding)
		logger.debug ( f"setup_menus : v_header_menus : {self.v_header_menus}")
		logger.debug ( f"setup_menus : h_header_menus : {self.h_header_menus}")
		logger.debug(f"setup_menus : cell_menus : {self.cell_menus}")
		if self.cell_menus:
			for menuObj in self.cell_menus:
				# display_headers = self.model()._headers
				display_headers = self.table_config['_headers']
				col_idx = display_headers.index( self.table_config['_mapping_display_to_attr'].get(menuObj['col_name'], menuObj['col_name']) )
				self.cell_menu_actions[col_idx] = menuObj['menus']
		### sorting 관련 view 설정
		_sorting_enable = False
		for menuObj in self.h_header_menus:
			if 'sort' in menuObj.get('h_header', {}).get('name', '') and menuObj.get('visible', False):
				_sorting_enable = True
				break
		logger.debug(f"setup_menus : _sorting_enable : {_sorting_enable}")
		self.menu_handler.enable_sorting(_sorting_enable)
		
	def create_action(self, 
					menu_item:dict, 
					object_name_prefix:str='v_header', 
					slot_prefix:str='slot_v_header',
					**kwargs
					):
		"""공통 QAction 생성 함수
			kwargs : rowNo, colNo 등 담아서 전달
		"""
		### {'id': 1, 'order': 1, 'visible': True, 'table': 1, 
		# 	'v_header': {'id': 1, 'name': 'add_row', 'title': '신규 Row 생성', 'tooltip': '현재 선택된 아래에 신규 Row를 생성합니다.'}}, 
		menu_obj = menu_item.get(object_name_prefix, {})
		if not menu_obj:
			logger.warning(f"menu_obj is None : {menu_item}")
			return
		title = menu_obj.get('title', '')
		# 구분선 추가 처리
		if title == 'seperator':
			action = QWidgetAction(self)  # QWidgetAction을 사용하여 구분선 추가
			action.setSeparator(True)
			return action      
		
		action = QAction(menu_obj['title'], self)
		action.setObjectName(f"{object_name_prefix}_{menu_obj['name']}")
		action.setToolTip(menu_obj['tooltip'])
		action.setEnabled(True)

		return self.on_menu_action(action, menu_obj, object_name_prefix, slot_prefix, **kwargs)

		raw_func = menu_obj.get('slot_func', None)
		slot_func = None

		if callable(raw_func):
			slot_func = raw_func  # e.g., self.on_user_select
			logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
		elif isinstance(raw_func, str):
			slot_name = f"{slot_prefix}__{raw_func}"
			slot_func = getattr(self.menu_handler, slot_name, self.menu_handler.default_slot)

		# kwargs에 row, col 등 담아서 전달
		if slot_func == self.menu_handler.default_slot:
			logger.warning(f"slot_func is default_slot : {slot_name}")
		action.triggered.connect(lambda: slot_func(**kwargs))
		return action

	def create_cell_action (self, 
					menu_item:dict, 
					object_name_prefix:str='v_header', 
					slot_prefix:str='slot_v_header',
					**kwargs ):
		"""셀 메뉴 생성"""
		menu_obj = menu_item
		if not menu_obj:
			logger.warning(f"menu_obj is None : {menu_item}")
			return
		title = menu_obj.get('title', '')
		# 구분선 추가 처리
		if title == 'seperator':
			action = QWidgetAction(self)  # QWidgetAction을 사용하여 구분선 추가
			action.setSeparator(True)
			return action      
		
		action = QAction(menu_obj['title'], self)
		action.setObjectName(f"{object_name_prefix}_{menu_obj['name']}")
		action.setToolTip(menu_obj['tooltip'])
		action.setEnabled(True)
		# callable 인지, 또한 menu_handler 에 있는지 확인
		raw_func = menu_item.get('slot_func')
		slot_func = None

		return self.on_menu_action(action, menu_item, object_name_prefix, slot_prefix, **kwargs)

		# 타입에 따라 처리
		if callable(raw_func):
			slot_func = raw_func  # e.g., self.on_user_select
			logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
		elif isinstance(raw_func, str):
			handler_func_name = f"{slot_prefix}__{raw_func}"
			slot_func = getattr(self.menu_handler, handler_func_name, None)
			if slot_func is None:
				logger.warning(f"[Menu] No such menu_handler slot_func: {handler_func_name}, fallback to default_slot")
				slot_func = self.menu_handler.default_slot
		else:
			logger.warning(f"[Menu] slot_func is invalid type: {type(raw_func)}")
			slot_func = self.menu_handler.default_slot

		action.triggered.connect(lambda: slot_func(**kwargs))
		return action

	def on_menu_action(self, action:QAction, menu_item:dict, object_name_prefix:str='v_header', slot_prefix:str='slot_v_header', **kwargs):
		""" 메뉴 액션 처리 """
		logger.info(f"on_menu_action : {action}, {menu_item}, {kwargs}")
		raw_func = menu_item.get('slot_func')
		slot_func = None

		# 타입에 따라 처리
		if callable(raw_func):
			slot_func = raw_func  # e.g., self.on_user_select
			logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
		else:
			raw_func = menu_item.get('name', None)
			logger.debug(f"[Menu] raw_func : {raw_func}")
			if raw_func and isinstance(raw_func, str):
				handler_func_name = f"{slot_prefix}__{raw_func}"
				slot_func = getattr(self.menu_handler, handler_func_name, None)
				logger.debug(f"[Menu] slot_func : {slot_func}")
				if slot_func is None:
					logger.warning(f"[Menu] No such menu_handler slot_func: {handler_func_name}, fallback to default_slot")
					slot_func = self.menu_handler.default_slot
			else:
				logger.warning(f"[Menu] slot_func is invalid type: {type(raw_func)}")
				slot_func = self.menu_handler.default_slot

		action.triggered.connect(lambda: slot_func(**kwargs))
		return action

	def show_v_header_context_menu(self, position):
		"""수직 헤더 컨텍스트 메뉴 표시"""
		### 현재 선택된 행 번호 가져오기
		selected_row = self.currentIndex().row()
		logger.debug(f"show_v_header_context_menu : {self.v_header_menus}, position : {position}")
		###DEBUG - show_v_header_context_menu : init_basic_config
		# [{'id': 1, 'order': 1, 'visible': True, 'table': 1, 
		# 	'v_header': {'id': 1, 'name': 'add_row', 'title': '신규 Row 생성', 'tooltip': '현재 선택된 아래에 신규 Row를 생성합니다.'}}, 
		# {'id': 2, 'order': 2, 'visible': True, 'table': 1, 
		# 	'v_header': {'id': 2, 'name': 'del_row', 'title': '선택 Row 삭제', 'tooltip': '현재 선택된  Row를 삭제(db에서) 삭제합니다.'}}]
		menu = QMenu(self)
		for menuObj in self.v_header_menus:
			action = self.create_action(menuObj, 'v_header', 'slot_v_header', rowNo=selected_row)
			menu.addAction(action)
		menu.exec(self.viewport().mapToGlobal(position))

	def show_h_header_context_menu(self, position):
		"""수평 헤더 컨텍스트 메뉴 표시"""
		### 현재 선택된 행 번호 가져오기
		selected_col = self.currentIndex().column()
		logger.debug(f"show_h_header_context_menu : {self.h_header_menus}, position : {position}")
		menu = QMenu(self)
		for menuObj in self.h_header_menus:
			action = self.create_action(menuObj, 'h_header', 'slot_h_header', colNo=selected_col)
			menu.addAction(action)
				
		menu.exec(self.viewport().mapToGlobal(position))

	def show_cell_context_menu(self, position):
		"""셀 컨텍스트 메뉴 표시"""
		### 현재 선택된 행 번호 가져오기
		selected_row = self.currentIndex().row()
		selected_col = self.currentIndex().column()
		logger.debug(f"show_cell_context_menu : {self.cell_menu_actions}, position : {position}, selected_col in self.cell_menu_actions : {selected_col in self.cell_menu_actions}")
		if selected_col in self.cell_menu_actions:
			menu = QMenu(self)
			for menuObj in self.cell_menu_actions[selected_col]:
				action = self.create_cell_action(menuObj, 'cell_menu', 'slot_cell_menu', rowNo=selected_row, colNo=selected_col)
				menu.addAction(action)
			menu.exec(self.viewport().mapToGlobal(position))

