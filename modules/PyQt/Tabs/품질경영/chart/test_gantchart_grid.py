# from __future__ import annotations
# from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
# from modules.global_event_bus import event_bus
# from modules.envs.global_bus_event_name import global_bus_event_name as GBus
# from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# from datetime import date, datetime
import copy, sys

### 😀😀 user : ui...
# from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
# from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
# from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table

# from modules.PyQt.Tabs.품질경영.tables.Wid_table_품질경영_CS관리 import Wid_table_품질경영_CS관리 as Wid_table

# from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
# ###################
# from modules.utils.api_response_분석 import handle_api_response
# from modules.PyQt.Tabs.plugins.BaseTab_Slot_Handler import BaseTab_Slot_Handler

# import modules.user.utils as Utils
# from config import Config as APP
# from info import Info_SW as INFO

# import traceback, time
# from modules.logging_config import get_plugin_logger
# logger = get_plugin_logger()

from datetime import datetime, timedelta

class GanttChartScene(QGraphicsScene):
    def __init__(self, start_date: QDate, total_days: int, schedules: list):
        super().__init__()
        self.start_date = start_date
        self.total_days = total_days
        self.schedules = schedules
        self.cell_width = 20
        self.row_height = 20
        self.draw_schedule_boxes()

    def draw_schedule_boxes(self):
        for sched in self.schedules:
            label = sched['label']
            color = QColor(sched['color'])
            date = QDate.fromString(sched['date'], 'yyyy-MM-dd')
            days_offset = self.start_date.daysTo(date)
            if 0 <= days_offset < self.total_days:
                x = days_offset * self.cell_width
                rect = self.addRect(x, 0, self.cell_width, self.row_height)
                rect.setBrush(QBrush(color))


class SingleGanttChartView(QGraphicsView):
    def __init__(self, start_date: QDate, total_days: int, schedules: list):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene = GanttChartScene(start_date, total_days, schedules)
        self.setScene(self.scene)
        self.setFixedHeight(30)
        self.setMinimumWidth(total_days * 20)


class GanttChartMainWidget(QWidget):
    def __init__(self, start_date: QDate, total_days: int, site_data: list):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # 날짜 헤더
        date_header = QWidget()
        date_layout = QHBoxLayout(date_header)
        for d in range(total_days):
            label = QLabel(start_date.addDays(d).toString("MM-dd"))
            label.setFixedWidth(20)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_layout.addWidget(label)
        main_layout.addWidget(date_header)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        grid_layout = QGridLayout(scroll_widget)

        for row, site in enumerate(site_data):
            grid_layout.addWidget(QLabel(site['name']), row, 0)
            view = SingleGanttChartView(start_date, total_days, site['schedules'])
            grid_layout.addWidget(view, row, 1)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    start_date = QDate(2025, 5, 1)
    total_days = 31
    site_data = [
        {
            'name': '현장A',
            'schedules': [
                {'label': '등록일', 'color': 'skyblue', 'date': '2025-05-03'},
                {'label': '완료요청일', 'color': 'orange', 'date': '2025-05-10'},
            ]
        },
        {
            'name': '현장B',
            'schedules': [
                {'label': '등록일', 'color': 'skyblue', 'date': '2025-05-06'},
                {'label': '완료요청일', 'color': 'orange', 'date': '2025-05-15'},
            ]
        },
    ]

    window = GanttChartMainWidget(start_date, total_days, site_data)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())