from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.custom_상속.custom_qstacked import Custom_QStackedWidget 


from config import Config as APP
from info import Info_SW as INFO
import modules.user.utils as Utils

import copy, time
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Empty_For_QStackedWidget(QLabel):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setText("조회된 데이터가 없읍니다.")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: gray;")
        self.setFont(QFont("Arial", 24))
        self.show()

    def hideEvent(self, a0: QHideEvent) -> None:
        self.hide()
        return super().hideEvent(a0)
    
    def showEvent(self, a0: QShowEvent) -> None:
        self.show()
        return super().showEvent(a0)




###✅ 25-7-16 생성
from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
class Base_MainWidget( QStackedWidget, LazyParentAttrMixin_V2):
	""" lazy_attrs를 이용한 클래스 """
	def __init__(self, parent:QWidget, **kwargs):
		super().__init__(parent)
		self.lazy_attr_names = ['APP_ID']
		self.lazy_ready_flags = {}
		self.lazy_attr_values = {}
		self.lazy_ws_names = []
		self.lazy_config:Optional[dict] = None
		self.lazy_config_mode:bool = False

		self.api_datas:Optional[list[dict]] = kwargs.get('api_datas', None)
			
		self.mapping_name_to_widget:dict[str, QWidget] = {}
		self.mapping_widget_to_name:dict[QWidget, str] = {}
		self.empty_widget = Empty_For_QStackedWidget(self)

		self.mapping_name_to_widget['empty'] = self.empty_widget
		self.current_name = None

		self.event_bus = event_bus
		self.kwargs = kwargs

		self.setup_ui()

		self.run_lazy_attr()
          
	def get_style_sheet(self):
		return """
            QStackedWidget {
                background-color: white;
                border: 5px solid black;
            }
        """

	def on_all_lazy_attrs_ready(self):
		try:
			if hasattr(self, 'lazy_attrs') and 'main_widget' in self.lazy_attrs:
				self.lazy_config = self.lazy_attrs['main_widget']
				if 'Default_view' in self.lazy_attrs:
					self.lazy_config['Default_view'] = self.lazy_attrs['Default_view']
				elif 'Default_view' not in self.lazy_config:
					self.lazy_config['Default_view'] = 'Table'

				self.current_name = self.lazy_config['Default_view']
				print(f"{self.__class__.__name__} : on_all_lazy_attrs_ready : current_name: {self.current_name}")

				self.lazy_config_mode = bool(self.lazy_config)
			else:
				logger.critical(f"{self.__class__.__name__} : on_all_lazy_attrs_ready : lazy_config 없음")
				logger.critical(f"{self.__class__.__name__} : on_all_lazy_attrs_ready : lazy_attrs: {self.lazy_attrs}")
				self.lazy_config = {
					'Default_view': 'Table',
					'mapping_name_to_widget': {
						'Table': "Wid_Table",
						'Chart': "Chart"
					}
				}

			APP_ID = self.lazy_attrs['APP_ID']
			print(f"self.lazy_attrs: {self.lazy_attrs}")
			self.table_name = Utils.get_table_name(APP_ID)
			self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
			if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
				self.url = Utils.get_api_url_from_appDict(self.appDict)
					
			self.update_mapping_name_to_widget()
			self.update_ui()
			self.subscribe_gbus()
               
		except Exception as e:
			logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")
			
	def update_mapping_name_to_widget(self):
		raise NotImplementedError("create_mapping_name_to_widget 메서드는 구현되어야 합니다.")
	
	def update_wid_select_main(self):
		try:
			self.wid_select_main = getattr( self._lazy_source_widget, 'wid_select_main', None)
			self.cb_select_main :QComboBox = getattr( self._lazy_source_widget, 'cb_select_main', None)
			#### self.valid_mapping_name_to_widet 이 하나인 경우는 self.wid_select_main  hide 함
			
			if len(self.valid_mapping_name_to_widget) <= 1:
				self.wid_select_main.hide()
				return 


			if self.cb_select_main is not None:
				current_items = [self.cb_select_main.itemText(i) for i in range(self.cb_select_main.count())]				
				if current_items != self.valid_mapping_name_to_widget:
					self.cb_select_main.currentTextChanged.disconnect()
					self.cb_select_main.clear()
					self.cb_select_main.addItems(self.valid_mapping_name_to_widget)
					self.cb_select_main.setCurrentText(self.lazy_config.get('Default_view', 'empty'))
					self.cb_select_main.currentTextChanged.connect(self._lazy_source_widget.on_select_main)
					self.cb_select_main.currentTextChanged.connect(lambda: self.set_current_name(self.cb_select_main.currentText()))
			else:
				print(f"{self.__class__.__name__} : update_wid_select_main : cb_select_main not found")

		except Exception as e:
			logger.error(f"update_wid_select_main 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"update_wid_select_main 오류: {e}")
		
	
	
	def update_ui(self):
		try:
			self.add_Widgets(self.mapping_name_to_widget)
			if self.lazy_config and 'Default_view' in self.lazy_config:
				current_wid_name = self.lazy_config.get('Default_view', 'empty')
			else:
				current_wid_name = 'empty'
			self.setCurrentWidget_with_name( current_wid_name if self.api_datas else 'empty')
		except Exception as e:
			print(f"setup_ui 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			raise ValueError(f"setup_ui 오류: {e}")
     
	def setup_ui(self):

		self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		self.setMinimumSize(400, 400)
		self.setContentsMargins(0, 0, 0, 0)
		self.setStyleSheet(self.get_style_sheet())
		self.update_ui()

	def subscribe_gbus(self):
		self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.on_api_datas )
		self.event_bus.subscribe( f"{self.table_name}:empty_data", self.on_empty_data )
            
	def unsubscribe_gbus(self):
		try:
			self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.on_api_datas )
			# self.event_bus.unsubscribe( f"{self.table_name}:table_config_mode", self.apply_table_config_mode )
			self.event_bus.unsubscribe( f"{self.table_name}:empty_data", self.on_empty_data )
		except Exception as e:
			logger.error(f"Error unsubscribing from gbus: {e}")

	def on_empty_data(self, is_ignore_empty:Optional[bool]=None):

		if is_ignore_empty:
			self.set_active_to_current()
		else:
			self.set_empty_to_current()

	def on_api_datas(self, api_datas:list[dict]):
		self.api_datas = copy.deepcopy(api_datas)	
		self.apply_api_datas(self.api_datas)

	def apply_api_datas(self, datas:Optional[list[dict]]=None):
		if datas:
			self.set_active_to_current()
		else:
			if self.lazy_config and self.lazy_config.get('ignore_empty', False):
				self.set_active_to_current()
			else:
				self.set_empty_to_current()

	def set_empty_to_current(self):
		wid = self.mapping_name_to_widget['empty']
		self.setCurrentWidget(wid)

	def set_active_to_current(self):
		if self.current_name :
			wid = self.mapping_name_to_widget[self.current_name]
		else:
			wid = self.mapping_name_to_widget[self.lazy_config.get('Default_view', 'Table')]
		self.setCurrentWidget(wid)

	def set_current_name(self, name:str):
		self.current_name = name
		wid = self.mapping_name_to_widget[name]
		self.setCurrentWidget(wid)


	def addWidget_with_name(self, name: str, widget: QWidget) -> None:
		"""name은 반드시 지정해야 한다."""
		if name not in self.mapping_name_to_widget :
			self.mapping_name_to_widget[name] = widget
		else:
			if widget != self.mapping_name_to_widget[name]:
				del_wid = self.mapping_name_to_widget.pop(name)
				del_wid.deleteLater()
				self.mapping_name_to_widget[name] = widget

		self.addWidget(widget)
		# self.setCurrentWidget(name)

	def removeWidget_with_name(self, name: str) -> None:
		widget = self.mapping_name_to_widget.pop(name, None)
		if widget:
			self.removeWidget(widget)

	def setCurrentWidget_with_name(self, name: str) -> None:
		widget = self.mapping_name_to_widget.get(name, None)
		if not widget:
			print(f"{self.__class__.__name__} : setCurrentWidget_with_name : {name} not found in mapping_name_to_widget")
		if widget:
			self.current_widget_name = name
			# for w in self.mapping_widgets.values():
			#     w.hide()
			# widget.show()
			self.setCurrentWidget(widget)
		else:
			if name != 'empty':
				self.setCurrentWidget_with_name('empty')
			else:
				logger.error(f"'empty' widget not found in mapping_name_to_widget")

	def add_Widgets(self, mapping_name_to_widget: dict[str, QWidget]) -> None:
		for name, widget in mapping_name_to_widget.items():
			self.addWidget_with_name(name, widget)

	def remove_Widgets(self, names: list[str]) -> None:
		for name in names:
			self.removeWidget_with_name(name)

	def clear_all_Widgets(self) -> None:
		for widget in self.mapping_name_to_widget.values():
			self.removeWidget(widget)
		self.mapping_name_to_widget.clear()

	def get_current_widget_name(self) -> str:
		return self.mapping_widget_to_name[self.currentWidget()]