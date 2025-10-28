from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.global_event_bus import event_bus
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import copy, time, traceback

from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils

from modules.PyQt.Tabs.영업mbo.graph.pie_chart_개인별  import PieChartWidget
from modules.PyQt.Tabs.영업mbo.graph.combo_chart_개인별 import ComboChartWidget

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Wid_Chart_개인별(LazyParentAttrMixin, QWidget):
    def __init__(self, parent: QWidget=None):
        super().__init__(parent)
        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.datas: list[dict] = None
        self.init_ui()

        self.lazy_attr_names = INFO.Table_View_Lazy_Attr_Names
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.run_lazy_attr()


    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.table_name = Utils.get_table_name(APP_ID)
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)
            self.subscribe_event_bus()
            self.run()
        except Exception as e:
            logger.error(f"on_all_lazy_attr_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attr_ready 오류: {e}")


    def subscribe_event_bus(self):
        self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_apply_api_datas)

    
    def unsubscribe_event_bus(self):
        self.event_bus.unsubscribe(f"{self.table_name}:datas_changed", self.on_apply_api_datas)

    def run(self):
        self.pie_chart.run()
        self.combo_chart.run()

    def stop(self):
        pass

    def init_ui(self):
        self.h_layout = QHBoxLayout(self)
        self.pie_chart = PieChartWidget(self)
        self.combo_chart = ComboChartWidget(self)
        self.h_layout.addWidget(self.pie_chart , 1)
        self.h_layout.addWidget(self.combo_chart, 2)
        self.setLayout(self.h_layout)

    def connect_signals(self):
        pass

    def on_apply_api_datas(self, datas: list[dict]):
        self.datas = datas
        self.pie_chart.on_apply_api_datas(copy.deepcopy(datas))
        self.combo_chart.on_apply_api_datas(copy.deepcopy(datas))    