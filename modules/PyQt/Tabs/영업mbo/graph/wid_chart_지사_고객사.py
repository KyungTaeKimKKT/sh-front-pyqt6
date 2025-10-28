from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v2 import *

from modules.PyQt.Tabs.영업mbo.graph.pie_chart_고객사 import PieChartWidget
from modules.PyQt.Tabs.영업mbo.graph.combo_chart_고객사 import ComboChartWidget

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class Wid_Chart_지사_고객사(QWidget, LazyParentAttrMixin_V2):
    def __init__(self, parent: QWidget=None, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.event_bus = event_bus
        self.datas: list[dict] = None
        self.first_data_applied = False
        self.lazy_attrs = {}

        self.run_lazy_attr()


    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.table_name = Utils.get_table_name(APP_ID)
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)
            self.init_ui()
            # self.run()
            self.subscribe_event_bus()

        except Exception as e:
            logger.error(f"on_all_lazy_attr_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attr_ready 오류: {e}")

    def subscribe_event_bus(self):
        self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_apply_api_datas)

    def unsubscribe_event_bus(self):
        self.event_bus.unsubscribe(f"{self.table_name}:datas_changed", self.on_apply_api_datas)


    def stop(self):
        pass

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        ### 1. splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        ### 2. 왼쪽  piechart
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.pie_chart = PieChartWidget(self)
        left_layout.addWidget(self.pie_chart)

        self.splitter.addWidget(left_widget)

        ### 3. 오른쪽  combo chart
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.combo_chart = ComboChartWidget(self)
        right_layout.addWidget(self.combo_chart)

        self.splitter.addWidget(right_widget)

        # 초기 사이즈 비율 설정 (왼쪽:오른쪽 = 1:2)

        QTimer.singleShot(0, lambda: self.adjust_splitter_ratio(1, 2))

        self.splitter.setHandleWidth(6)  # ✅ 이 줄 추가!
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #999999;
            }
        """)

    def connect_signals(self):
        pass

    def on_apply_api_datas(self, datas: list[dict]):
        self.datas = datas
        self.pie_chart.on_apply_api_datas(copy.deepcopy(datas))
        self.combo_chart.on_apply_api_datas(copy.deepcopy(datas))

        if not self.first_data_applied:
            self.first_data_applied = True
            QTimer.singleShot(0, lambda: self.adjust_splitter_ratio(1, 2))

    def adjust_splitter_ratio(self, left_ratio: int, right_ratio: int):
        total_weight = left_ratio + right_ratio
        sizes = []
        for i in range(self.splitter.count()):
            sizes.append(0)  # 일단 초기화
        total_width = sum(self.splitter.widget(i).sizeHint().width() for i in range(self.splitter.count()))
        
        # 비율 적용
        sizes[0] = total_width * left_ratio // total_weight
        sizes[1] = total_width * right_ratio // total_weight
        self.splitter.setSizes(sizes)