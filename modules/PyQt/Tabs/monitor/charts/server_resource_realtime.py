from __future__ import annotations

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCharts import *
from PyQt6.QtCore import *

from collections import deque
import datetime




class BaseChart(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 상하 마진 최소화
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

    def add_series(self, series: QAbstractSeries, axis_x: QAbstractAxis, axis_y: QAbstractAxis):
        self.chart.addSeries(series)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

class NetworkMonitorChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__("네트워크 실시간 모니터링", parent)
        self.sent_history = deque(maxlen=300)
        self.received_history = deque(maxlen=300)

        self.sent_series = QLineSeries()
        self.received_series = QLineSeries()

        self.axis_x = QValueAxis()
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("초 전")
        self.axis_x.setRange(-299, 0)

        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("%.2f")
        self.axis_y.setTitleText("데이터 전송/수신 (MB)")
        self.axis_y.setRange(0, 1)  # 초기 범위 설정, 필요에 따라 조정 가능

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.add_series(self.sent_series, self.axis_x, self.axis_y)
        self.add_series(self.received_series, self.axis_x, self.axis_y)

        self.sent_series.setColor(Qt.GlobalColor.red)  # SENT를 빨간색으로 설정
        self.received_series.setColor(Qt.GlobalColor.blue)  # RECEIVED를 파란색으로 설정

        self.sent_series.setName("SENT")  # SENT 라벨 추가
        self.received_series.setName("RECEIVED")  # RECEIVED 라벨 추가

        # Show the legend and set its alignment to top-right
        # self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.chart.legend().show()

    def apply_data(self, network_dict: dict):
        self.update_data(network_dict)
        self.update_chart()

    def update_data(self, network_dict: dict):
        self.sent_history.append(network_dict["sent"])
        self.received_history.append(network_dict["received"])

    def update_chart(self):
        self.sent_series.clear()
        self.received_series.clear()
        count = len(self.sent_history)
        for i in range(count):
            self.sent_series.append(QPointF(-count + i, self.sent_history[i]))
            self.received_series.append(QPointF(-count + i, self.received_history[i]))

        # Set the range of the x-axis based on the number of data points
        self.axis_x.setRange(-count + 1, 0)

        # Set the range of the y-axis based on the maximum value in the data
        max_value = max(max(self.sent_history, default=0), max(self.received_history, default=0))
        self.axis_y.setRange(0, max_value * 1.1)  # Add a 10% margin

class CoreUsageBarChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__("코어별 실시간 사용률", parent)
        self.bar_series = QBarSeries()

        self.axis_x = QBarCategoryAxis()
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.add_series(self.bar_series, self.axis_x, self.axis_y)

        # Hide the legend
        self.chart.legend().hide()

    def apply_data(self, core_usage: dict):
        self.bar_series.clear()
        barset = QBarSet("코어별 사용률")
        labels = []

        for core, usage in core_usage.items():
            barset << usage
            labels.append(core)

        self.bar_series.append(barset)
        self.axis_x.clear()
        self.axis_x.append(labels)

class CPUMonitorChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__("CPU 실시간 모니터링", parent)
        self.history = deque(maxlen=300)
        self.timestamps = deque(maxlen=300)
        self.core_usage = {}

        self.line_series = QLineSeries()
        self.limit_line = QLineSeries()

        self.axis_x = QValueAxis()
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("초 전")
        self.axis_x.setRange(-299, 0)

        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("%.0f")
        self.axis_y.setTitleText("CPU %")
        self.axis_y.setRange(0, 100)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.add_series(self.line_series, self.axis_x, self.axis_y)
        self.add_series(self.limit_line, self.axis_x, self.axis_y)

        self.limit_line.setColor(Qt.GlobalColor.red)  # 한계선을 빨간색으로 설정
        self.limit_line.append(QPointF(-299, 90))
        self.limit_line.append(QPointF(0, 90))
        self.limit_line.setName("90%")  # 한계선 라벨 추가

        # Hide the legend
        self.chart.legend().hide()

        self.set_limit_text()
        self.set_title_text()

    def set_limit_text(self, limit: str = "한계선: 90%"):
        self.chart.setTitle(f"CPU 실시간 모니터링 ({limit})")

    def set_title_text(self, title: str = "CPU 실시간 모니터링"):
        self.chart.setTitle(f"{title} (한계선: 90%)")

    def apply_data(self, cpu_dict: dict):
        self.update_data(cpu_dict)
        self.update_chart()

    def update_data(self, cpu_dict: dict):
        self.history.append(cpu_dict["percent"])
        # self.timestamps.append(datetime.datetime.fromisoformat(data["timestamp"]))
        # self.core_usage = cpu_dict["cores"]

    def update_chart(self):
        self.line_series.clear()
        count = len(self.history)
        for i in range(count):
            self.line_series.append(QPointF(-count + i, self.history[i]))

        # Set the range of the x-axis based on the number of data points
        self.axis_x.setRange(-count + 1, 0)

class MemoryMonitorChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__("메모리 실시간 모니터링", parent)
        self.memory_history = deque(maxlen=300)

        self.memory_series = QLineSeries()
        self.limit_line = QLineSeries()

        self.axis_x = QValueAxis()
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("초 전")
        self.axis_x.setRange(-299, 0)

        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("%.2f")
        self.axis_y.setTitleText("메모리 사용량 (GB)")
        self.axis_y.setRange(0, 32)  # 초기 범위 설정, 필요에 따라 조정 가능

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.add_series(self.memory_series, self.axis_x, self.axis_y)
        self.add_series(self.limit_line, self.axis_x, self.axis_y)

        self.limit_line.setColor(Qt.GlobalColor.red)  # 한계선을 빨간색으로 설정
        self.limit_line.append(QPointF(-299, 0.9 * 32))  # 90% 메모리 용량
        self.limit_line.append(QPointF(0, 0.9 * 32))
        self.limit_line.setName("90%")  # 한계선 라벨 추가

        # Hide the legend
        self.chart.legend().hide()

        self.set_limit_text()
        self.set_title_text()

    def set_limit_text(self, limit: str = "한계선: 90%"):
        self.chart.setTitle(f"메모리 실시간 모니터링 ({limit})")

    def set_title_text(self, title: str = "메모리 실시간 모니터링"):
        self.chart.setTitle(f"{title} (한계선: 90%)")

    def apply_data(self, memory_dict: dict):
        self.update_data(memory_dict)
        self.update_chart()

    def update_data(self, memory_dict: dict):
        self.memory_history.append(memory_dict["used"])

    def update_chart(self):
        self.memory_series.clear()
        count = len(self.memory_history)
        for i in range(count):
            self.memory_series.append(QPointF(-count + i, self.memory_history[i]))

        # Set the range of the x-axis based on the number of data points
        self.axis_x.setRange(-count + 1, 0)

count = 0
if __name__ == "__main__":
    import sys, time
    app = QApplication(sys.argv)
    from datas import datas
    window = CPUMonitorChart()
    core_window = CoreUsageBarChart()
    network_window = NetworkMonitorChart()
    memory_window = MemoryMonitorChart()  # 메모리 모니터링 창 추가
    window.show()
    core_window.show()
    network_window.show()
    memory_window.show()  # 메모리 모니터링 창 표시

    timer = QTimer()
    timer.timeout.connect(lambda: slot_apply_data())
    timer.start(1000)

    def slot_apply_data():
        global count
        start_time = time.time()
        window.apply_data(datas[count]["message"])
        core_window.apply_data(datas[count]["message"]["cpu"]["cores"])
        network_window.apply_data(datas[count]["message"])
        memory_window.apply_data(datas[count]["message"])  # 메모리 데이터 적용
        end_time = time.time()
        print(f"apply_data 실행 시간: {(end_time - start_time)*1000:.2f}msec ")

        count += 1
        if count >= len(datas):
            count = 0

    sys.exit(app.exec())