from typing import Any
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
from datetime import datetime, timedelta, date, time
import copy

class GanttModel(QAbstractTableModel):
    def __init__(self, 
                 parent:QWidget|None=None,
                 api_datas:list[dict] = [], 
                 label_headers:list[str] = [], 
                 body_start:datetime|date|time = date.today(),  ##[datetime,date, time] 중 하나
                 body_end:datetime|date|time = date.today(),    ##[datetime,date, time] 중 하나
                 step_reference:str = 'day', #### 'hour', 'month', 'year' 등으로 확충
                 step:int = 1,
                 **kwargs
                 ):
        super().__init__(parent)
        self._label_widths: dict[int, int] = {}
        self.step_reference = step_reference
        self.step = step
        self.label_headers = label_headers  # ex: ['현장명']
        self.body_start = body_start
        self.body_end = body_end
        self.kwargs = kwargs
        self.api_datas = api_datas
        self._datas = api_datas
        self.original_datas = copy.deepcopy(api_datas)
        self.body_cell_width = kwargs.get('body_cell_width', 50)
        self.font_metrics = QFontMetrics(QFont())  # scene에서 쓰는 폰트 기준
        # self.body_headers = self._generate_date_headers(body_start_date, body_end_date)
        # self._headers = self.label_headers + self.body_headers
        if self.api_datas:
            self.on_api_datas_received(self.api_datas)
    
    @property
    def body_headers(self):        
        return self._generate_date_headers()

    @property
    def _headers(self):
        return self.label_headers + self.body_headers
    
    #### getters
    def get_label_headers(self) -> list[str]:
        return self.label_headers

    ##### setters
    def set_tasks(self, task_data:list[dict]):
        self._tasks = task_data

    def set_label_headers(self, label_headers:list[str]):
        self.label_headers = label_headers

    def set_body_start_date(self, body_start_date:datetime|date|time):
        self.body_start = body_start_date

    def set_body_end_date(self, body_end_date:datetime|date|time):
        self.body_end = body_end_date

    def set_step(self, step:int):
        self.step = step

    def set_step_reference(self, step_reference:str):
        if step_reference in ['day', 'hour', 'month', 'year']:
            self.step_reference = step_reference
        else:
            raise ValueError(f"Invalid step_reference: {step_reference}")

    def _generate_date_headers(self):
        """ ✅ 25-7-24: 추가적인 보완 필요 """
        start = self.body_start
        end = self.body_end
        step = self.step
        #### date 기준만 ==> 현재 적용
        if self.step_reference == 'day':
            if isinstance(start, date) and isinstance(end, date):
                days_range = (end - start).days + 1
                return [start + timedelta(days=i) for i in range(0, days_range, step)]
            elif isinstance(start, datetime) and isinstance(end, datetime):
                _start = start.date()
                _end = end.date()
                days_range = (_end - _start).days + 1
                return [_start + timedelta(days=i) for i in range(days_range, step)]

        #### datetime에서 시간 기준만
        elif isinstance(start, datetime) and isinstance(end, datetime):
            time_range = int(( (end - start).total_seconds() + 1)/3600 )
            return [start + timedelta(hours=i) for i in range(time_range, step)]
        else:
            return []

    def rowCount(self, parent=QModelIndex()):
        return len(self._datas)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        task = self._datas[index.row()]
        col = index.column()

        # LABEL 영역
        if col < len(self.label_headers):
            key = self.label_headers[col]
            if role == Qt.ItemDataRole.DisplayRole:
                if key == "현장주소":
                    _text = task.get(key, "").strip().split(' ')
                    return f"{_text[0]} {_text[1]}"                
                return task.get(key, "")
            elif role == Qt.ItemDataRole.DecorationRole and key == "현장명":
                return QIcon(":/icons/site.png")  # 예시 아이콘

        # BODY 영역
        else:
            col_date = self.body_headers[col - len(self.label_headers)]
            start = datetime.fromisoformat(task['등록일']).date()
            end = datetime.fromisoformat(task['완료요청일']).date()

            if role == Qt.ItemDataRole.DisplayRole:
                if start <= col_date <= end:
                    return "■"
                return ""
            elif role == Qt.ItemDataRole.BackgroundRole:
                if start <= col_date <= end:
                    return QBrush(QColor("skyblue"))

        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()

        if orientation == Qt.Orientation.Horizontal:
            if section < len(self.label_headers):
                return self.label_headers[section]
            else:
                return self.body_headers[section - len(self.label_headers)].strftime('%m-%d')
        else:
            return self._tasks[section].get("현장명", "")
        

    def on_api_datas_received(self, api_datas:list[dict]):
        self.api_datas = api_datas
        self._datas = self.api_datas
        self.original_datas = copy.deepcopy(api_datas)
        self.calculate_label_widths()

    def calculate_label_widths(self):
        self._label_widths.clear()
        for i, key in enumerate(self.get_label_headers() ):
            max_val = max((str(d.get(key, "")) for d in self.api_datas), key=len, default="")
            candidate = max([key, max_val], key=len)  # 💡 key 포함
            width = self.font_metrics.horizontalAdvance(candidate) + 20  # padding 포함
            self._label_widths[i] = width

    def get_column_width(self, col: int) -> int:
        """label col: 동적, body col: 고정"""
        if col < len(self.label_headers):
            return self._label_widths.get(col, self.body_cell_width)
        return self.body_cell_width



class GanttLabelCellItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model, index: QModelIndex):
        super().__init__(rect)
        self.model = model
        self.index = index
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.text = model.data(index, Qt.ItemDataRole.DisplayRole)
        self.tooltip = model.data(index, Qt.ItemDataRole.ToolTipRole)
        if self.tooltip and isinstance(self.tooltip, str):
            self.setToolTip(self.tooltip)

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.drawText(self.rect().adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter, self.text)

    def refresh(self):
        self.update()  # 자체 update()로 paint 재실행


class GanttBodyCellItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model, index: QModelIndex):
        super().__init__(rect)
        self.model = model
        self.index = index
        self.value = model.data(index, Qt.ItemDataRole.DisplayRole)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#d0f0ff")))

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(Qt.GlobalColor.white))

    def contextMenuEvent(self, event):
        menu = QMenu()
        action = menu.addAction("작업 세부 정보 보기")
        action.triggered.connect(lambda: print(f"Context clicked: {self.index.data()}"))
        menu.exec(event.screenPos())

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.value == "🔧":
            icon = QPixmap("wrench.png").scaled(16, 16)
            painter.drawPixmap(self.rect().center().toPoint() - QPointF(8, 8), icon)
        elif self.value:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.value))
    
    def refresh(self):
        self.update()  # 자체 update()로 paint 재실행

# class GanttCellItem(QGraphicsRectItem):
#     def __init__(self, rect: QRectF, model: QAbstractTableModel, index: QModelIndex):
#         super().__init__(rect)
#         self.model = model
#         self.index = index
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

#         self.model.layoutChanged.connect(self.refresh)
#         self.model.dataChanged.connect(self.refresh)

#     def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
#         role = Qt.ItemDataRole

#         # Background
#         bg = self.model.data(self.index, role.BackgroundRole)
#         if isinstance(bg, QBrush):
#             painter.fillRect(self.rect(), bg)

#         # Border
#         painter.setPen(QPen(Qt.GlobalColor.gray))
#         painter.drawRect(self.rect())

#         # Text
#         text = self.model.data(self.index, role.DisplayRole)
#         if text:
#             painter.drawText(self.rect().adjusted(3, 3, -3, -3), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, str(text))

#     def refresh(self):
#         self.update()  # 자체 update()로 paint 재실행

class GanttHeaderItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model: QAbstractTableModel, colNo:int):
        super().__init__(rect)
        self.model = model
        self.colNo = colNo
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        role = Qt.ItemDataRole

        # Background
        # bg = self.model.data(self.index, role.BackgroundRole)
        # if isinstance(bg, QBrush):
        #     painter.fillRect(self.rect(), bg)

        # Border
        painter.setPen(QPen(Qt.GlobalColor.gray))
        painter.drawRect(self.rect())

        # Text
        text = self.model.headerData(self.colNo, Qt.Orientation.Horizontal, role.DisplayRole)
        if text:
            painter.drawText(self.rect().adjusted(3, 3, -3, -3), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, str(text))

    def refresh(self):
        self.update()  # 자체 update()로 paint 재실행

class GanttScene(QGraphicsScene):
    def __init__(self, model: QAbstractTableModel, cell_height=30, header_height=30, label_width=150, cell_width=80):
        super().__init__()
        self.model = model
        self.header_height = header_height
        self.cell_height = cell_height
        self.label_width = label_width
        self.cell_width = cell_width
        self.map_col_to_x_and_width: dict[int, tuple[float, int]] = {}

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

        self.refresh()

    def refresh(self):
        self.clear()
        self._draw()

    def _draw(self):
        self._get_map_col_to_x_and_width()
        if not self.map_col_to_x_and_width:
            return
        self._draw_headers()
        self._draw_grid()

    def _get_map_col_to_x_and_width(self):
        x = 0
        self.map_col_to_x_and_width = {}
        for col in range(self.model.columnCount()):
            w = self.model.get_column_width(col)
            self.map_col_to_x_and_width[col] = (x, w)
            x += w
        print(self.map_col_to_x_and_width)

    def _draw_headers(self):
        for col in range(self.model.columnCount()):
            rect = self._get_rect_header(col=col)
            item = self._create_header_item(rect, col)
            self.addItem(item)

    def _draw_grid(self):
        for row in range( self.model.rowCount()):
            for col in range(self.model.columnCount()):
                rect = self._get_rect_body(row=row, col=col)                
                index = self.model.index(row, col)
                if col < len(self.model.label_headers):
                    item = self._create_label_cell(rect, index)
                else:
                    item = self._create_body_cell(rect, index)

                self.addItem(item)
    
    def _get_rect_header(self, col:int=0) -> QRectF:
        x, w = self.map_col_to_x_and_width.get(col, (0, 0))
        height = self.header_height
        y = 0
        return QRectF(x, y, w, height)

    def _get_rect_body(self, row:int=0, col:int=0) -> QRectF:
        x, w = self.map_col_to_x_and_width.get(col, (0, 0))
        height = self.cell_height
        y = ( self.header_height ) + (row * self.cell_height)
        return QRectF(x, y, w, height)
    

    # ✅ 템플릿 메서드: override point
    def _create_header_item(self, rect, col):
        return GanttHeaderItem(rect, self.model, col)

    def _create_label_cell(self, rect, index):
        return GanttLabelCellItem(rect, self.model, index)

    def _create_body_cell(self, rect, index):
        return GanttBodyCellItem(rect, self.model, index)
    ######


# class GanttScene(QGraphicsScene):
#     def __init__(self, model: QAbstractTableModel, cell_width=100, cell_height=30, header_height=30, label_width=150):
#         super().__init__()
#         self.model = model
#         self.cell_width = cell_width
#         self.cell_height = cell_height
#         self.header_height = header_height
#         self.label_width = label_width

#         self._draw_headers()
#         self._draw_grid()

#         self.model.layoutChanged.connect(self.refresh)
#         self.model.dataChanged.connect(self.refresh)

#     def _draw_headers(self):
#         col_count = self.model.columnCount()
#         for col in range(col_count):
#             index = self.model.index(0, col)  # 헤더에는 row는 의미 없음
#             x = self.label_width + (col - len(self.model.label_headers)) * self.cell_width if col >= len(self.model.label_headers) else col * self.label_width
#             y = 0
#             rect = QRectF(x, y, self.cell_width if col >= len(self.model.label_headers) else self.label_width, self.header_height)

#             header_item = GanttHeaderItem(rect, self.model, col)
#             # header_item = QGraphicsRectItem(rect)
#             # header_item.setBrush(QBrush(QColor("#ddd")))
#             # header_item.setPen(QPen(Qt.GlobalColor.black))
#             self.addItem(header_item)

#             # label = QGraphicsTextItem(self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
#             # label.setPos(rect.x() + 3, rect.y() + 3)
#             # self.addItem(label)

#     def _draw_grid(self):
#         row_count = self.model.rowCount()
#         col_count = self.model.columnCount()

#         for row in range(row_count):
#             for col in range(col_count):
#                 index = self.model.index(row, col)
#                 if col < len(self.model.label_headers):
#                     # 왼쪽 label 영역
#                     x = 0
#                     width = self.label_width
#                 else:
#                     x = self.label_width + (col - len(self.model.label_headers)) * self.cell_width
#                     width = self.cell_width

#                 y = self.header_height + row * self.cell_height
#                 rect = QRectF(x, y, width, self.cell_height)

#                 item = GanttCellItem(rect, self.model, index)
#                 self.addItem(item)

#     def refresh(self):
#         self.clear()
#         self._draw_headers()
#         self._draw_grid()

class GanttView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def showEvent(self, event):
        super().showEvent(event)
        self.reset_view_to_top_left()

    def reset_view_to_top_left(self):
        # 스크롤바를 강제로 맨 앞(0,0)으로 이동
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)

class GanttMainWidget(QWidget):
    def __init__(self, task_data:list[dict]=[], **kwargs):
        super().__init__()

        self.api_datas = task_data

        self.setup_ui()

        QTimer.singleShot(1000, lambda: self.api_data_update())
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.view = self._create_widget()
        self.main_layout.addWidget(self.view)
        self.setLayout(self.main_layout)

    def _create_widget(self) -> QGraphicsView:
        self.model = self.setup_model()
        self.scene = GanttScene(self.model)
        self.view = GanttView(self.scene)
        return self.view
    
    def setup_model(self) -> GanttModel:
        self.model = GanttModel(self)
        self.model.set_label_headers(["현장명", "현장주소","Elevator사","부적합유형","등록일","완료요청일"])
        self.model.set_body_start_date(datetime(2025, 7, 1).date())
        self.model.set_body_end_date(datetime(2025, 7, 31).date())
        self.model.set_step_reference('day')
        return self.model

    def api_data_update(self, api_datas:list[dict] = None):        
        self.api_datas = api_datas or self.api_datas
        self.model.on_api_datas_received(self.api_datas)
        self.model.layoutChanged.emit()

def run_app(task_data):
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Gantt Chart Example (with Model)")
    widget = GanttMainWidget(task_data)
    window.setCentralWidget(widget)
    window.resize(1200, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    task_data = [
        {'id': 51, '현장명': '삼라마이다스빌', '현장주소': '광주광역시 북구 동운로 141', 'Elevator사': 'TKE',
         '부적합유형': '스크래치', '등록일': '2025-07-21T17:57:50', '완료요청일': '2025-07-26'},
        {'id': 37, '현장명': '한울3차아파트(K20240590)', '현장주소': '충청남도 아산시 어의정로183번길 14',
         'Elevator사': 'TKE', '부적합유형': '스크래치', '등록일': '2025-07-12T17:06:18.231341', '완료요청일': '2025-07-18'},
        {'id': 34, '현장명': '코오롱동신아파트', '현장주소': '충청북도 충주시 금릉로 14', 'Elevator사': '현대',
         '부적합유형': '스크래치', '등록일': '2025-07-09T08:21:45.446129', '완료요청일': '2025-07-21'}
    ]
    run_app(task_data)


#####✅ class GanttModel(QAbstractTableModel):
# class GanttModel(QAbstractTableModel):
#     def __init__(self, headers, task_data):
#         super().__init__()
#         self.unit = 'day'  # 기본 단위
#         self.gap = 1
#         self.start_date = date.today()
#         self.end_date = date.today() + timedelta(days=30)
#         self._raw_data = task_data  # api_data 원본
#         self._headers = headers
#         self._filter_fn = lambda row: True  # 기본 필터: 모두 통과
#         self._generate_date_headers()

#     def set_unit(self, unit: Literal["year", "month", "day", "hour"]):
#         self.unit = unit
#         self._generate_date_headers()
#         self.layoutChanged.emit()

#     def set_range(self, start: date, end: date):
#         self.start_date = start
#         self.end_date = end
#         self._generate_date_headers()
#         self.layoutChanged.emit()

#     def set_step(self, step: int):
#         self.gap = step
#         self._generate_date_headers()
#         self.layoutChanged.emit()

#     def set_filter(self, fn: Callable):
#         self._filter_fn = fn
#         self.layoutChanged.emit()

#     def _generate_date_headers(self):
#         self.body_headers = []
#         cur = self.start_date
#         while cur <= self.end_date:
#             self.body_headers.append(cur)
#             cur += timedelta(days=self.gap)  # 단위/간격에 따라 변경 가능

#     def rowCount(self, parent=None):
#         return len([r for r in self._raw_data if self._filter_fn(r)])

#     def data(self, index, role=Qt.DisplayRole):
#         if not index.isValid():
#             return QVariant()

#         row = index.row()
#         col = index.column()

#         filtered_rows = [r for r in self._raw_data if self._filter_fn(r)]
#         item = filtered_rows[row]

#         if role == Qt.DisplayRole:
#             if col == 0:  # label_headers 예시
#                 return item["현장명"]
#             else:
#                 날짜 = self.body_headers[col - 1]
#                 return item["스케줄"].get(str(날짜), "")  # 예시
#         elif role == Qt.ForegroundRole:
#             if self._is_weekend(self.body_headers[col - 1]):
#                 return QColor(Qt.gray)
#         return QVariant()