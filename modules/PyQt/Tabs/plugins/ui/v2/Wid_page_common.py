from __future__ import annotations
from typing import Optional, Any

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import time, traceback, copy

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo


class Wid_Page_Common(QWidget, LazyParentAttrMixin):


    def __init__(self, parent=None):
        super().__init__(parent)

        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self._text_총검색건수 = "총검색건수 : "
        self._text_현재페이지 = "현재페이지 : "
        self._text_전체페이지 = "전체페이지 : "

        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.current_page = 1
        self.total_page = 1
        self.prev_total_page = None

        self.setup_ui()

        self.hide()

        self.run_lazy_attr()

    def setup_ui(self):
        self.resize(1378, 61)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(9, 0, -1, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName("main_layout")

        #### 2. 검색건수
        self.lb_countTotal = QLabel(parent=self)
        self.lb_countTotal.setText(self._text_총검색건수)
        self.main_layout.addWidget(self.lb_countTotal)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)

        #### 3. 현재페이지 / 전체페이지
        self.lb_현재페이지 = QLabel(parent=self )
        self.lb_현재페이지.setText("현재페이지 : ")
        self.main_layout.addWidget(self.lb_현재페이지)

        self.comboBox_current_Page = Custom_Combo(parent=self)
        self.main_layout.addWidget(self.comboBox_current_Page)

        self.lb_total_Page = QLabel(parent=self)
        self.lb_total_Page.setText(self._text_전체페이지)
        self.main_layout.addWidget(self.lb_total_Page)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem1)        

        self.setLayout(self.main_layout)


    def closeEvent(self, event):
        self.disconnect_signals()
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)

    
    def on_all_lazy_attrs_ready(self):
        APP_ID = self.lazy_attr_values['APP_ID']
        self.table_name = Utils.get_table_name(APP_ID)
        self.appDict = copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
        if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
            self.url = Utils.get_api_url_from_appDict(self.appDict)
			
        self.channel_name = f"AppID:{APP_ID}_"
        self.event_bus.subscribe(self.channel_name+GBus.PAGINATION_INFO, self.on_pagination_changed)
        self.connect_signals()


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(self.channel_name+GBus.PAGINATION_INFO, self.on_pagination_changed)

    def connect_signals(self):
        self.comboBox_current_Page.currentIndexChanged.connect( self.on_comboBox_current_Page_changed )


    def disconnect_signals(self):
        try:
            self.comboBox_current_Page.currentIndexChanged.disconnect()
        except Exception as e:
            pass

    def on_comboBox_current_Page_changed(self):
        pageNo = self.comboBox_current_Page.currentText()
        self.event_bus.publish(self.channel_name+GBus.PAGINATION_CHANGED, pageNo)

    def on_pagination_changed(self, pagination:dict):
        self.disconnect_signals()
        if pagination is None or pagination == {}:
            return
        self.lb_countTotal.setText(f"{self._text_총검색건수} {pagination['countTotal']} 건")

        if self.prev_total_page != self.total_page:
            self.comboBox_current_Page.clear()
            self.comboBox_current_Page.addItems( [ f"{i}" for i in range(1, pagination['total_Page']+1) ] )
        self.comboBox_current_Page.setCurrentText(f"{pagination['current_Page']}")
        self.lb_total_Page.setText(f"{self._text_전체페이지} {pagination['total_Page']}")
        if not self.isVisible():
            self.show()
        self.connect_signals()
        
    def run(self):
        pass

    def set_pagination(self, pagination:dict):
        self.current_page = pagination['current_Page']
        self.prev_total_page = self.total_page
        self.total_page = pagination['total_Page']
        