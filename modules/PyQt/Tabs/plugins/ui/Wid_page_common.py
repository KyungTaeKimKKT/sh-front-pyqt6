from __future__ import annotations
from typing import Optional, Any

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.PyQt.Tabs.plugins.ui.Ui_pagination_common import Ui_Pagination
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import time, traceback

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Wid_Page_Common(QWidget, LazyParentAttrMixin):


    def __init__(self, parent=None):
        super().__init__(parent)

        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.current_page = 1
        self.total_page = 1
        self.prev_total_page = None
        self.ui = Ui_Pagination()
        self.ui.setupUi(self)

        self.hide()

        self.run_lazy_attr()

    def closeEvent(self, event):
        self.disconnect_signals()
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)
        # match attr_name:
        #     case 'id':
        #         self.lazy_ready_flags[attr_name] = True
        #         self.channel_name = f"AppID:{attr_value}_"
        #         self.event_bus.subscribe(self.channel_name+GBus.PAGINATION_INFO, self.on_pagination_changed)
        #         self.connect_signals()
        #     case 'table_name':
        #         self.lazy_ready_flags[attr_name] = True
        #         self.table_name = attr_value
        #         self.ui.PB_DownloadAll.clicked.connect(
        #             lambda: self.event_bus.publish(f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", True)
        #         )
        #     case _:
        #         logger.warning(f"Unknown attribute: {attr_name}")
        
        # if all(self.lazy_ready_flags.get(name, False) for name in self.lazy_attr_names):
        #     self.on_all_lazy_attrs_ready()
    
    def on_all_lazy_attrs_ready(self):
        logger.info("All lazy attributes are ready!")
        APP_ID = self.lazy_attr_values['APP_ID']
        self.table_name = Utils.get_table_name(APP_ID)
        self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
        if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
            self.url = Utils.get_api_url_from_appDict(self.appDict)
			
        self.channel_name = f"AppID:{APP_ID}_"
        self.event_bus.subscribe(self.channel_name+GBus.PAGINATION_INFO, self.on_pagination_changed)
        self.connect_signals()
        self.ui.PB_DownloadAll.clicked.connect(
                    lambda: self.event_bus.publish(f"{self.table_name}:{GBus.PAGINATION_DOWNLOAD}", True)
                )


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(self.channel_name+GBus.PAGINATION_INFO)

    def connect_signals(self):
        self.ui.comboBox_current_Page.currentIndexChanged.connect(
            lambda: self.event_bus.publish(self.channel_name+GBus.PAGINATION_CHANGED, self.ui.comboBox_current_Page.currentText()) 
        )


    def disconnect_signals(self):
        try:
            self.ui.comboBox_current_Page.currentIndexChanged.disconnect()
        except Exception as e:
            pass



    def on_pagination_changed(self, pagination:dict):
        self.disconnect_signals()
        logger.info(f"update_page_info: {pagination}")
        if pagination is None or pagination == {}:
            return
        self.ui.label_countTotal.setText(f"{pagination['countTotal']} 건")

        if self.prev_total_page != self.total_page:
            self.ui.comboBox_current_Page.clear()
            self.ui.comboBox_current_Page.addItems( [ f"{i}" for i in range(1, pagination['total_Page']+1) ] )
        self.ui.comboBox_current_Page.setCurrentText(f"{pagination['current_Page']}")
        self.ui.label_total_Page.setText(f"{pagination['total_Page']}")
        self.show()
        self.connect_signals()
        
    def run(self):
        pass

    def set_pagination(self, pagination:dict):
        self.current_page = pagination['current_Page']
        self.prev_total_page = self.total_page
        self.total_page = pagination['total_Page']
        