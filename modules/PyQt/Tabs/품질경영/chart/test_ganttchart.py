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



class GanttChartView(QGraphicsView):
    def __init__(self, api_datas, parent=None):
        super().__init__(parent)
        self.scene = GanttChartScene(api_datas)
        self.setScene(self.scene)
        self.init_view_settings()
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def init_view_settings(self):
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)


class GanttChartScene(QGraphicsScene):
    def __init__(self, api_datas, parent=None):
        super().__init__(parent)
        self.api_datas = api_datas
        self.cell_width = 40
        self.row_height = 60
        self.top_margin = 80
        self.left_margin = 150
        self.font = QFont("Arial", 10)

        self.start_date, self.end_date = self.calculate_date_range()
        self.total_days = (self.end_date.toPyDate() - self.start_date.toPyDate()).days + 1
        self.setSceneRect(0, 0, self.left_margin + self.cell_width * self.total_days, self.top_margin + len(self.api_datas) * self.row_height)

        self.draw_grid_and_labels()
        self.add_schedule_items()

    def calculate_date_range(self):
        dates = []
        for data in self.api_datas:
            for key in ['등록일', '완료요청일', '완료일']:
                if data.get(key):
                    dates.append(QDate.fromString(data[key][:10], 'yyyy-MM-dd'))
        if not dates:
            today = QDate.currentDate()
            return today, today.addDays(10)
        return min(dates), max(dates).addDays(5)

    def draw_grid_and_labels(self):
        self.draw_date_labels()
        self.draw_weekday_labels()
        self.draw_vertical_grid()
        self.draw_site_labels()

    def draw_date_labels(self):
        for i in range(self.total_days):
            x = self.left_margin + i * self.cell_width
            date = self.start_date.addDays(i)
            text = date.toString("MM/dd")
            item = QGraphicsSimpleTextItem(text)
            item.setFont(self.font)
            item.setPos(x + 5, 0)
            self.addItem(item)

    def draw_weekday_labels(self):
        for i in range(self.total_days):
            x = self.left_margin + i * self.cell_width
            date = self.start_date.addDays(i)
            weekday = date.toString("ddd")
            color = QColor('red') if date.dayOfWeek() == 7 else QColor('blue') if date.dayOfWeek() == 6 else QColor('black')
            item = QGraphicsSimpleTextItem(weekday)
            item.setFont(self.font)
            item.setBrush(color)
            item.setPos(x + 5, 20)
            self.addItem(item)

    def draw_vertical_grid(self):
        pen = QPen(QColor("gray"), 0.5)
        for i in range(self.total_days + 1):
            x = self.left_margin + i * self.cell_width
            self.addLine(x, 0, x, self.sceneRect().height(), pen)

    def draw_site_labels(self):
        for row, data in enumerate(self.api_datas):
            y = self.top_margin + row * self.row_height
            site_name = data.get("현장명", "N/A")
            item = QGraphicsSimpleTextItem(site_name)
            item.setFont(self.font)
            item.setPos(5, y)
            self.addItem(item)

    def add_schedule_items(self):
        for row, data in enumerate(self.api_datas):
            self.add_schedule_box(data, row)

    def add_schedule_box(self, data, row):
        y = self.top_margin + row * self.row_height
        color_map = {
            '등록일': QColor("skyblue"),
            '완료요청일': QColor("orange"),
            '완료일': QColor("green")
        }

        # 등록일 x 위치 기록
        min_x = None
        for label in ['등록일', '완료요청일', '완료일']:
            if not data.get(label):
                continue
            date = QDate.fromString(data[label][:10], 'yyyy-MM-dd')
            days = (date.toPyDate() - self.start_date.toPyDate()).days
            if days < 0 or days >= self.total_days:
                continue
            x = self.left_margin + days * self.cell_width

            if label == '등록일':
                min_x = x

            item = GanttItemBox(
                row, label, date, color_map[label], self.cell_width,
                self.left_margin, self.top_margin, self.row_height,
                self.total_days, self.start_date,
                min_x if label == '완료요청일' else None
            )
            item.setRect(0, 0, self.cell_width, 20)
            item.setPos(x, y + (self.row_height - 20) / 2)
            self.addItem(item)


class GanttItemBox(QGraphicsRectItem):
    def __init__(self, row_index, label, date, color, width, left_margin, top_margin,
                 row_height, total_days, start_date, min_x=None):
        super().__init__(0, 0, width, 20)
        self.row_index = row_index
        self.label = label
        self.date = date
        self.color = color
        self.start_date = start_date
        self.left_margin = left_margin
        self.top_margin = top_margin
        self.row_height = row_height
        self.total_days = total_days
        self.cell_width = width
        self.min_x = min_x  # 등록일 X 위치

        self.setBrush(QBrush(self.color))

        # D&D 제한
        self.is_movable = self.label == "완료요청일"
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, self.is_movable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, self.is_movable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, self.is_movable)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton if self.is_movable else Qt.MouseButton.NoButton)

        # 위치
        days_offset = (self.date.toPyDate() - self.start_date.toPyDate()).days
        x_pos = self.left_margin + days_offset * self.cell_width
        box_height = self.rect().height()
        y_pos = self.top_margin + row_index * self.row_height + (self.row_height - box_height) / 2
        self.setPos(x_pos, y_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos: QPointF = value
            x = new_pos.x()

            min_x = self.min_x if self.min_x is not None else self.left_margin
            max_x = self.left_margin + self.cell_width * (self.total_days - 1)

            new_x = max(min_x, min(x, max_x))
            days_offset = int((new_x - self.left_margin) / self.cell_width)
            new_date = self.start_date.addDays(days_offset)

            fixed_y = self.top_margin + self.row_index * self.row_height + (self.row_height - self.rect().height()) / 2
            print(f"Row {self.row_index} {self.label} 변경됨: {new_date.toString('yyyy-MM-dd')}")
            return QPointF(new_x, fixed_y)

        return super().itemChange(change, value)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    sample_api_datas = [
        {
            '현장명': '한울3차아파트(K20240590)',
            '등록일': '2025-05-16T09:15:28',
            '완료요청일': '2025-05-23T00:00:00',
            '완료일': '2025-05-27T00:00:00'
        },
        {
            '현장명': '중앙하이츠빌',
            '등록일': '2025-05-10T10:00:00',
            '완료요청일': '2025-05-20T00:00:00',
            '완료일': None
        }
    ]

    view = GanttChartView(sample_api_datas)
    view.setWindowTitle("Gantt Chart Example")
    view.resize(1200, 600)
    view.show()

    sys.exit(app.exec())




# class DraggableDateItem(QGraphicsRectItem):
#     def __init__(self, date_index: int, row: int, color: QColor, callback=None):
#         super().__init__(date_index * 20, 50 + row * 40, 20, 30)
#         self.setBrush(QBrush(color))
#         self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
#         self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
#         self.setZValue(1)
#         self.row = row
#         self.callback = callback

#     def itemChange(self, change, value):
#         if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
#             new_x = round(value.x() / 20) * 20
#             self.setX(new_x)
#             if self.callback:
#                 self.callback(self.row, new_x // 20)
#         return super().itemChange(change, value)

# class GanttChartView(QGraphicsView):
#     def __init__(self, api_datas):
#         super().__init__()
#         self.api_datas = api_datas
#         self.scene = QGraphicsScene()
#         self.setScene(self.scene)

#         # self.setRenderHint(QPainter.RenderHint.Antialiasing)  # ✅ 수정된 부분

#         # self.setSceneRect(0, 0, 1600, 800)
#         # self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)


#         self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
#         self.setSceneRect(0, 0, 1600, 800)
#         self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)


#         self.left_column_width = 250
#         self.day_width = 80
#         self.top_margin = 100
#         self.row_height = 50

#         self.start_date, self.end_date = self.calculate_date_range()
#         self.dates = self.generate_dates(self.start_date, self.end_date)

#         self.draw_date_headers()
#         self.draw_rows()


#     def calculate_date_range(self):
#         min_date = QDate.currentDate()
#         max_date = QDate.currentDate()
#         for data in self.api_datas:
#             reg = QDate.fromString(data['등록일'][:10], "yyyy-MM-dd")
#             min_date = min(min_date, reg)
#             if data.get("완료요청일"):
#                 comp_req = QDate.fromString(data["완료요청일"][:10], "yyyy-MM-dd")
#                 max_date = max(max_date, comp_req)
#             if data.get("완료일"):
#                 comp = QDate.fromString(data["완료일"][:10], "yyyy-MM-dd")
#                 max_date = max(max_date, comp)
#         return min_date.addDays(-1), max_date.addDays(1)

#     def generate_dates(self, start: QDate, end: QDate):
#         dates = []
#         d = start
#         while d <= end:
#             dates.append(d)
#             d = d.addDays(1)
#         return dates

#     def draw_date_headers(self):
#         font = QFont("Arial", 8)
#         for i, d in enumerate(self.dates):
#             x = self.left_column_width + i * self.day_width

#             date_text = QGraphicsTextItem(d.toString("MM-dd"))
#             date_text.setFont(font)
#             date_text.setPos(x + 2, 0)
#             self.scene.addItem(date_text)

#             day_text = QGraphicsTextItem(d.toString("ddd"))
#             day_text.setFont(font)
#             day_text.setPos(x + 2, 18)
#             if d.dayOfWeek() in [6, 7]:
#                 day_text.setDefaultTextColor(Qt.GlobalColor.red)
#             self.scene.addItem(day_text)

#     def draw_rows(self):
#         for row, data in enumerate(self.api_datas):
#             self.draw_row_label(row, data)
#             self.draw_task_items(row, data)

#     def draw_row_label(self, row, data):
#         y = self.top_margin + row * self.row_height
#         label = QGraphicsTextItem(data["현장명"])
#         label.setTextWidth(self.left_column_width - 10)
#         label.setFont(QFont("Arial", 9))
#         label.setPos(0, y)
#         self.scene.addItem(label)

#     def draw_task_items(self, row, data):
#         def date_to_index(date_str):
#             date = QDate.fromString(date_str[:10], "yyyy-MM-dd")
#             return self.start_date.daysTo(date)

#         y = self.top_margin + row * self.row_height
#         h = 30

#         # 등록일
#         if data.get("등록일"):
#             i = date_to_index(data["등록일"])
#             self.add_box(i, y, h, QColor("blue"))

#         # 완료일
#         if data.get("완료일"):
#             i = date_to_index(data["완료일"])
#             self.add_box(i, y, h, QColor("green"))

#         # 완료요청일 (드래그 가능)
#         if data.get("완료요청일"):
#             i = date_to_index(data["완료요청일"])
#             item = DraggableDateItem(i, row, QColor("orange"), self.on_request_date_changed)
#             self.scene.addItem(item)

#     def add_box(self, day_index, y, height, color):
#         x = self.left_column_width + day_index * self.day_width
#         rect = QGraphicsRectItem(x, y, self.day_width, height)
#         rect.setBrush(QBrush(color))
#         rect.setPen(QPen(Qt.GlobalColor.black))
#         self.scene.addItem(rect)

#     def on_request_date_changed(self, row_index: int, new_day_index: int):
#         new_date = self.start_date.addDays(new_day_index)
#         print(f"Row {row_index} 완료요청일 변경됨: {new_date.toString('yyyy-MM-dd')}")
        

# class GanttChartWidget(QWidget):
#     def __init__(self, api_datas, parent=None):
#         super().__init__(parent)
#         layout = QVBoxLayout(self)
#         self.view = GanttChartView(api_datas)
#         layout.addWidget(self.view)
#         self.setLayout(layout)










# if __name__ == "__main__":
#     import sys
#     app = QApplication(sys.argv)
#     api_datas = [{
#         '현장명': '한울3차아파트(K20240590)',
#         '등록일': '2025-05-16T09:15:28.845602',
#         '완료요청일': '2025-05-20T00:00:00',
#         '완료일': '2025-05-22T00:00:00'
#     }]
#     window = GanttChartWidget(api_datas)
#     window.setWindowTitle("기본형 간트 차트")
#     window.show()
#     sys.exit(app.exec())