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

        # 예시값들 (필요에 따라 조정하세요)
        start_date = QDate.currentDate()  # 또는 api_datas에서 추출
        total_days = 30
        left_margin = 100
        top_margin = 40
        row_height = 40
        cell_width = 40
        data_list = api_datas  # 데이터 리스트

        self.scene = GanttChartScene(
            start_date,
            total_days,
            left_margin,
            top_margin,
            row_height,
            cell_width,
            data_list
        )
        self.setScene(self.scene)
        self.init_view_settings()
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def init_view_settings(self):
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)


class GanttChartScene(QGraphicsScene):
    def __init__(self, start_date, total_days, left_margin, top_margin, row_height, cell_width, data_list):
        super().__init__()
        self.start_date = start_date
        self.total_days = total_days
        self.left_margin = left_margin
        self.top_margin = top_margin
        self.row_height = row_height
        self.cell_width = cell_width
        self.data_list = data_list
        self.box_height = 20

        self.draw_all_rows()

    def draw_all_rows(self):
        for row_index, data in enumerate(self.data_list):
            self.draw_row(row_index, data)

    def draw_row(self, row_index, data):
        y = self.top_margin + row_index * self.row_height

        # 1. 현장명 텍스트 (좌측 영역)
        site_name = data.get("현장명", f"현장{row_index}")
        text_item = QGraphicsTextItem(site_name)
        text_item.setFont(QFont("Arial", 10))
        # Y는 row 중앙 정렬 (텍스트 높이 20 가정)
        text_item.setPos(5, y + (self.row_height - 20) / 2)
        self.addItem(text_item)

        # 2. 날짜별 Gantt 박스 (우측 영역)
        color_map = {
            '등록일': QColor("skyblue"),
            '완료요청일': QColor("orange"),
            '완료일': QColor("green")
        }

        # 등록일 박스 x 위치 기억 (드래그 제한용)
        reg_x = None

        for label in ['등록일', '완료요청일', '완료일']:
            date_str = data.get(label)
            if not date_str:
                continue
            date = QDate.fromString(date_str[:10], 'yyyy-MM-dd')
            days_offset = (date.toPyDate() - self.start_date.toPyDate()).days
            if days_offset < 0 or days_offset >= self.total_days:
                continue

            x = self.left_margin + days_offset * self.cell_width

            if label == '등록일':
                reg_x = x

            box = GanttItemBox(
                row_index=row_index,
                label=label,
                date=date,
                color=color_map[label],
                width=self.cell_width,
                left_margin=self.left_margin,
                top_margin=self.top_margin,
                row_height=self.row_height,
                total_days=self.total_days,
                start_date=self.start_date,
                min_x=reg_x  # 등록일 위치를 min_x 제한으로 전달
            )
            box.setRect(0, 0, self.cell_width, self.box_height)
            # Y도 중앙 정렬
            box.setPos(x, y + (self.row_height - self.box_height) / 2)
            self.addItem(box)


class GanttItemBox(QGraphicsRectItem):
    def __init__(self, row_index, label, date, color, width, left_margin, top_margin, row_height, total_days, start_date, min_x=None):
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
        self.min_x = min_x if min_x is not None else left_margin

        self.setBrush(QBrush(self.color))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        # 초기 위치
        days_offset = (self.date.toPyDate() - self.start_date.toPyDate()).days
        x_pos = self.left_margin + days_offset * self.cell_width
        y_pos = self.top_margin + self.row_index * self.row_height + (self.row_height - 20) / 2
        self.setPos(x_pos, y_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos: QPointF = value
            x = new_pos.x()
            fixed_y = self.top_margin + self.row_index * self.row_height + (self.row_height - 20) / 2

            # 좌우 제한: min_x(등록일 박스) ≤ x ≤ max_right
            new_x = max(self.min_x, x)
            max_right = self.left_margin + self.cell_width * self.total_days - self.cell_width
            new_x = min(new_x, max_right)

            # 날짜 업데이트 (필요하면)
            days_offset = int((new_x - self.left_margin) / self.cell_width)
            new_date = self.start_date.addDays(days_offset)
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