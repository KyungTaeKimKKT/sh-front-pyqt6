from __future__ import annotations

from modules.common_import_v2 import *

from modules.PyQt.Tabs.home.baseappdashboard import BaseAppDashboard
from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler_V2

# class SemiCircleGauge(QWidget):
#     def __init__(self, parent=None, label:str = "Gauge", max_value:int=100, warning_threshold:int=90, **kwargs ):
#         super().__init__(parent)
#         self.kwargs = kwargs
#         self.value = 0
#         self.max_value = self.set_max_value(max_value)
#         self.warning_threshold = self.set_warning_threshold(warning_threshold)
#         self.label = self.set_label(label)
#         self.margin :int= 0
#         self.margin_percent :float= 0.1
#         # self.setStyleSheet("background-color:#ff0000;border:1px solid red;")
#         # self.setMinimumSize( self.kwargs.get('min_width', 200), self.kwargs.get('min_height', 200))

#     def set_warning_threshold(self, val:int):
#         self.warning_threshold = val
#         return self.warning_threshold
    
#     def set_max_value(self, val:int):
#         self.max_value = val
#         return self.max_value
    
#     def set_label(self, val:str):
#         self.label = val
#         return self.label
    
#     def set_value(self, val:float):
#         self.value = min(max(val, 0), self.max_value)
#         self.update()

#     def get_radius(self, margin_percent:float=0.1) -> int:
#         """ width()가 크다는 가정하에, """
#         min_value = min(self.width(), self.height())
#         self.margin = int(min_value * margin_percent)
#         return int(min_value - self.margin*2)
    
#     def paint_background(self, painter:QPainter):
#         # 배경색 칠하기
#         painter.fillRect(self.rect(), QColor("#ff0000"))
#         # 테두리 그리기
#         pen = QPen(Qt.red)
#         pen.setWidth(1)
#         painter.setPen(pen)
#         painter.drawRect(self.rect().adjusted(0, 0, -1, -1))  # 테두리가 안 잘리도록 조정

    


#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing)

#         # self.paint_background(painter)

#         # geometry : half-circle임. 즉, radius 전체 값이 실질적인 half-circle 반지름이 되어야 함.
#         self.radius = self.get_radius(margin_percent=self.margin_percent)  # 이 값은 'diameter' 역할
#         cx = self.width() / 2
#         x_circle_start = int(cx - self.radius )
#         x_circle_end = int( cx + self.radius)
#         y_circle_top = self.margin
#         center_y = y_circle_top + self.radius   # 원의 중심 y
#         circle_rect = QRectF(int(x_circle_start), int(y_circle_top), int(self.radius*2), int(self.radius*2))

#         # 전체 아크 각도(상수로 분리)
#         full_start_deg = 180
#         full_span_deg = -180  # 시계방향 180도

#         # 1) 배경 아크 (두껍게)
#         pen_bg = QPen(QColor(220, 220, 220), 15)
#         pen_bg.setCapStyle(Qt.PenCapStyle.FlatCap)
#         painter.setPen(pen_bg)
#         painter.drawArc(circle_rect, int(full_start_deg * 16), int(full_span_deg * 16))

#         # 2) 하단 베이스 라인
#         pen_line = QPen(QColor(120, 120, 120), 5)
#         painter.setPen(pen_line)
#         y_bottom = int( circle_rect.top() + self.radius )
#         painter.drawLine(int(x_circle_start - self.margin), y_bottom, int(x_circle_end + self.margin), y_bottom)

#         # 3) 눈금 (radial lines) — 10% 단위 블록 10개를 만들기 위해 9개의 내부 눈금(10%..90%)
#         tick_count = 9
#         tick_pen = QPen(QColor(180, 180, 180), 3)
#         tick_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
#         painter.setPen(tick_pen)

#         circle_r = self.radius   # 실제 반지름
#         tick_length = max(6, int(circle_r * 0.08))
#         # 안쪽/바깥쪽 반지름(아크 펜 너비를 고려)
#         bg_pen_half = pen_bg.width() / 2.0
#         r_inner = circle_r - bg_pen_half - 2
#         r_outer = circle_r + bg_pen_half + tick_length

#         for i in range(1, tick_count + 1):  # 1..9 => 10%..90%
#             percent = i / 10.0
#             theta_deg = 180.0 - percent * 180.0
#             theta = math.radians(theta_deg)
#             x1 = cx + r_inner * math.cos(theta)
#             y1 = center_y - r_inner * math.sin(theta)
#             x2 = cx + r_outer * math.cos(theta)
#             y2 = center_y - r_outer * math.sin(theta)
#             painter.drawLine(int(x1), int(y1), int(x2), int(y2))

#         # 3) warning_threshold 선 (빨간색)
#         warn_percent = self.warning_threshold / self.max_value
#         warn_theta_deg = 180.0 - warn_percent * 180.0
#         warn_theta = math.radians(warn_theta_deg)
#         warn_pen = QPen(QColor(255, 0, 0), 4)
#         warn_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
#         painter.setPen(warn_pen)
#         wx1 = cx + r_inner * math.cos(warn_theta)
#         wy1 = center_y - r_inner * math.sin(warn_theta)
#         wx2 = cx + r_outer * math.cos(warn_theta)
#         wy2 = center_y - r_outer * math.sin(warn_theta)
#         painter.drawLine(int(wx1), int(wy1), int(wx2), int(wy2))

#         # 4) 값 아크 (사용률) — 변수명 독립적으로 계산
#         pen_val = QPen(QColor(50, 150, 255), 15)
#         if self.value >= self.warning_threshold:
#             pen_val.setColor(QColor(255, 60, 60))
#         pen_val.setCapStyle(Qt.PenCapStyle.FlatCap)
#         painter.setPen(pen_val)
#         angle_span_val = int((self.value / self.max_value) * (full_span_deg * 16))  # full_span_deg은 -180
#         painter.drawArc(circle_rect, int(full_start_deg * 16), angle_span_val)

#         # 5) 중앙 텍스트
#         painter.setPen(Qt.GlobalColor.black)
#         font = QFont('Arial', 12, QFont.Weight.Bold)
#         painter.setFont(font)
#         label_rect = QRectF(circle_rect)
#         label_rect.setBottom(int(label_rect.bottom() - self.radius / 2))
#         painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"{self.label}\n{self.value:.1f}%")


class SemiCircleGauge(QWidget):
    def __init__(self, parent=None, label: str = "Gauge", max_value: int = 100, warning_threshold: int = 90, **kwargs):
        super().__init__(parent)
        self.value = 0
        self.max_value = max_value
        self.warning_threshold = warning_threshold
        self.label = label

        # 스타일, 크기 등 조절용 kwargs
        self.margin_percent = kwargs.get('margin_percent', 0.1)

        self.qColor_bg = kwargs.get('qColor_bg', QColor(220, 220, 220))
        self.qColor_normal = kwargs.get('qColor_normal', QColor(80, 80, 80))
        self.qColor_warning = kwargs.get('qColor_warning', QColor(255, 60, 60))

        self.bg_arc_width = kwargs.get('bg_arc_width', 15)
        self.baseline_width = kwargs.get('baseline_width', 5)
        self.tick_count = kwargs.get('tick_count', 9)
        self.tick_width = kwargs.get('tick_width', 3)
        self.warning_line_width = kwargs.get('warning_line_width', 4)
        self.value_arc_width = kwargs.get('value_arc_width', 15)
        self.needle_width = kwargs.get('needle_width', 3)
        self.needle_length_percent = kwargs.get('needle_length_percent', 0.85)
        self.needle_tip_radius = kwargs.get('needle_tip_radius', 6)

        # 기타
        self.font_family = kwargs.get('font_family', 'Arial')
        self.font_size = kwargs.get('font_size', 12)
        self.font_weight = kwargs.get('font_weight', QFont.Weight.Bold)

    def set_value(self, val: float):
        self.value = min(max(val, 0), self.max_value)
        self.update()

    def get_radius_and_margin(self) -> tuple[int, int]:
        min_side = min(self.width(), self.height())
        margin = int(min_side * self.margin_percent)
        radius = int(min_side - 2 * margin)
        return radius, margin

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius, margin = self.get_radius_and_margin()
        cx = self.width() / 2
        y_top = margin
        center_y = y_top + radius
        circle_rect = QRectF(cx - radius, y_top, 2 * radius, 2 * radius)

        self.draw_background_arc(painter, circle_rect)
        self.draw_baseline(painter, circle_rect, margin)
        self.draw_ticks(painter, cx, center_y, radius)
        self.draw_warning_line(painter, cx, center_y, radius)
        self.draw_value_arc(painter, circle_rect)
        # 필요 시 바늘 그리기
        # self.draw_needle(painter, cx, center_y, radius)
        self.draw_label_text(painter, circle_rect, radius)
        return painter, cx, center_y, radius

    def draw_background_arc(self, painter: QPainter, rect: QRectF):
        pen = QPen(self.qColor_bg, self.bg_arc_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawArc(rect, 180 * 16, -180 * 16)

    def draw_baseline(self, painter: QPainter, rect: QRectF, margin: int):
        pen = QPen(QColor(120, 120, 120), self.baseline_width)
        painter.setPen(pen)
        y_bottom = rect.top() + rect.height() / 2
        painter.drawLine(int(rect.left() - margin), int(y_bottom), int(rect.right() + margin), int(y_bottom))

    def draw_ticks(self, painter: QPainter, cx: float, center_y: float, radius: int):
        pen = QPen(QColor(180, 180, 180), self.tick_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)

        bg_pen_half = self.bg_arc_width / 2
        tick_length = max(6, int(radius * 0.08))
        r_inner = radius - bg_pen_half - 2
        r_outer = radius + bg_pen_half + tick_length

        for i in range(1, self.tick_count + 1):
            percent = i / (self.tick_count + 1)
            theta_deg = 180.0 - percent * 180.0
            theta = math.radians(theta_deg)
            x1 = cx + r_inner * math.cos(theta)
            y1 = center_y - r_inner * math.sin(theta)
            x2 = cx + r_outer * math.cos(theta)
            y2 = center_y - r_outer * math.sin(theta)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def draw_warning_line(self, painter: QPainter, cx: float, center_y: float, radius: int):
        warn_percent = self.warning_threshold / self.max_value
        warn_theta_deg = 180.0 - warn_percent * 180.0
        warn_theta = math.radians(warn_theta_deg)
        pen = QPen(self.qColor_warning, self.warning_line_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)

        bg_pen_half = self.bg_arc_width / 2
        tick_length = max(6, int(radius * 0.08))
        r_inner = radius - bg_pen_half - 2
        r_outer = radius + bg_pen_half + tick_length

        wx1 = cx + r_inner * math.cos(warn_theta)
        wy1 = center_y - r_inner * math.sin(warn_theta)
        wx2 = cx + r_outer * math.cos(warn_theta)
        wy2 = center_y - r_outer * math.sin(warn_theta)
        painter.drawLine(int(wx1), int(wy1), int(wx2), int(wy2))

    def draw_value_arc(self, painter: QPainter, rect: QRectF):
        color = self.qColor_warning if self.value >= self.warning_threshold else QColor(50, 150, 255)
        pen = QPen(color, self.value_arc_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        angle_span_val = int((self.value / self.max_value) * (-180 * 16))
        painter.drawArc(rect, 180 * 16, angle_span_val)

    def _get_qColor(self, value: Optional[float] = None) -> QColor:
        value = value if value is not None else self.value
        return self.qColor_warning if value >= self.warning_threshold else self.qColor_normal

    def _get_pen_needle(self, value: Optional[float] = None) -> QPen:
        pen = QPen(self._get_qColor(value), self.needle_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        return pen

    def draw_needle(self, painter: QPainter, cx: float, center_y: float, radius: int):
        needle_length = radius * self.needle_length_percent
        angle_deg = 180.0 - (self.value / self.max_value) * 180.0
        angle_rad = math.radians(angle_deg)
        x = cx + needle_length * math.cos(angle_rad)
        y = center_y - needle_length * math.sin(angle_rad)
        pen = self._get_pen_needle()
        painter.setPen(pen)
        painter.drawLine(QPointF(cx, center_y), QPointF(x, y))

        brush_color = self._get_qColor()
        painter.setBrush(brush_color)
        painter.drawEllipse(QPointF(cx, center_y), self.needle_tip_radius, self.needle_tip_radius)

    def draw_label_text(self, painter: QPainter, rect: QRectF, radius: int):
        painter.setPen(Qt.GlobalColor.black)
        font = QFont(self.font_family, self.font_size, self.font_weight)
        painter.setFont(font)
        label_rect = QRectF(rect)
        label_rect.setBottom(int(label_rect.bottom() - radius / 2))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"{self.label}\n{self.value:.1f}%")

class SpeedGauge(SemiCircleGauge):
    def __init__(self, parent=None, label:str = "Gauge", max_value:int=100, warning_threshold:int=90, **kwargs ):
        super().__init__(parent, label, max_value, warning_threshold, **kwargs)

    def paintEvent(self, event):
        painter, cx, center_y, radius = super().paintEvent(event)
        self.draw_needle(painter, cx, center_y, radius)

class DashboardWidget_ServerResource(BaseAppDashboard):

    def init_kwargs(self):
        self.cpu_config = self.kwargs.get('cpu_config', {})
        self.mem_config = self.kwargs.get('mem_config', {})

    def _create_dashboard_area(self) -> QFrame:
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        v_layout = QVBoxLayout(self.dashboard_area)
        # h_layout = QHBoxLayout(self.dashboard_area)
        self.dashboard_area.setLayout(v_layout)
        self.cpu_gauge = SpeedGauge( self, 
                                         label= self.cpu_config.get('label', "CPU 사용률"), 
                                         max_value= self.cpu_config.get('max_value', 100), 
                                         warning_threshold= self.cpu_config.get('warning_threshold', 80)
                                         )
        self.mem_gauge = SpeedGauge( self, 
                                         label= self.mem_config.get('label', "메모리 사용률"), 
                                         max_value= self.mem_config.get('max_value', 100), 
                                         warning_threshold= self.mem_config.get('warning_threshold', 85)
                                         )
        # self.cpu_gauge = SemiCircleGauge( self, 
        #                                  label= self.cpu_config.get('label', "CPU 사용률"), 
        #                                  max_value= self.cpu_config.get('max_value', 100), 
        #                                  warning_threshold= self.cpu_config.get('warning_threshold', 80)
        #                                  )
        # self.mem_gauge = SemiCircleGauge( self, 
        #                                  label= self.mem_config.get('label', "메모리 사용률"), 
        #                                  max_value= self.mem_config.get('max_value', 100), 
        #                                  warning_threshold= self.mem_config.get('warning_threshold', 85)
        #                                  )

        # h_layout.addWidget(self.cpu_gauge)
        # h_layout.addWidget(self.mem_gauge)
        v_layout.addWidget(self.cpu_gauge)
        v_layout.addWidget(self.mem_gauge)

        return self.dashboard_area


    def update_dashboard_area(self):
        """ 데이터 변경 시 화면 업데이트 
         {'cpu': {'percent': 7.0, 'count': 12, 
         'cores': {'core_0': 3.0, 'core_1': 3.0, 'core_2': 3.0, 'core_3': 0.0, 'core_4': 3.0, 'core_5': 12.7, 'core_6': 5.0, 'core_7': 4.0, 'core_8': 7.1, 'core_9': 2.0, 'core_10': 3.0, 'core_11': 38.4}}, 
         'memory': {'total': 31.16, 'used': 27.54, 'percent': 91.0}, 
         'network': {'sent': 0.04, 'received': 0.04}, 
         'timestamp': '2025-08-11 11:15:57'}
        """
        cpu_percent = self._data.get('cpu', {}).get('percent', 0)
        mem_percent = self._data.get('memory', {}).get('percent', 0)
        self.cpu_gauge.set_value(cpu_percent)
        self.mem_gauge.set_value(mem_percent)





# def main():
#     app = QApplication(sys.argv)
#     widget = HomeDashboardWidget(on_open_detail_callback=open_app_detail)
#     widget.on_data_changed({
#         'cpu': {'percent': 10.6},
#         'memory': {'percent': 91.1},
#         'timestamp': '2025-08-11 11:17:08'
#     })
#     widget.show()
#     app.exec()

# if __name__ == "__main__":
#     main()