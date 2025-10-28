from __future__ import annotations
from typing import Optional, Any

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

from modules.PyQt.Tabs.plugins.ui.Ui_search_common import Ui_Search
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import time, traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from local_db.models import Search_History

class Wid_Search_Common(QWidget, LazyParentAttrMixin):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.search_history:list[str] = []
        self.is_ui_initialized = False

        if not self.is_ui_initialized:
            self.UI()
        self.run_lazy_attr()

    def UI(self):
        self.ui = Ui_Search()
        self.ui.setupUi(self)

        self.is_ui_initialized = True

    def closeEvent(self, event):
        self.disconnect_signals()
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)
    
    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.set_focus_to_search()
            self.set_completer( APP_ID )
            self.channel_name = f"AppID:{APP_ID}_"
            self.connect_signals()
        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")
    

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(self.channel_name)

    def connect_signals(self):
        self.ui.PB_Search.clicked.connect( self.on_search ) #lambda: self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, self.get_search_keyword()) )
        self.ui.le_search.returnPressed.connect( self.on_search ) #lambda: self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, self.get_search_keyword()) )
    
    def on_search(self):
        self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, self.get_search_keyword())

    def disconnect_signals(self):
        try:
            self.ui.PB_Search.clicked.disconnect()
            self.ui.le_search.returnPressed.disconnect()
        except Exception as e:
            pass

    def hide_search_edit(self):
        self.ui.label.hide()
        self.ui.le_search.hide()
    
    def hide_pagesize_combo(self):
        self.ui.comboBox_pageSize.setCurrentText('ALL')
        self.ui.comboBox_pageSize.hide()
        self.ui.label_6.hide()

    def hide_pb_option(self):
        self.ui.PB_Option.hide()

    def hide_except_pb_search(self):
        self.hide_search_edit()
        self.hide_pagesize_combo()
        self.hide_pb_option()


    def set_completer(self, id:int):
        self.ui.le_search.set_completer(id)
    
    def db_save_search_history(self):
        self.ui.le_search.db_save_search_history()

    def set_focus_to_search(self):
        # 이 메서드를 통해 검색창에 포커스 설정 가능
        self.ui.le_search.setFocus()

    def showEvent(self, event):
        # 위젯이 표시될 때마다 포커스 설정
        super().showEvent(event)
        if hasattr(self, 'ui'):
            self.ui.le_search.setFocus()

    def get_search_keyword(self) -> str:
        param = []
        if ( search_keyword := self.ui.le_search.text() ):
            self.db_save_search_history()
            param.append( f"search={search_keyword}" )
        page = self.ui.comboBox_pageSize.currentText()
        if page.upper() == 'ALL':
            param.append( f"page_size=0" )
        else:
            param.append( f"page_size={page}" )
        if INFO.IS_DEV:
            logger.debug(f"param: {param}")
        return '&'.join(param)
    

