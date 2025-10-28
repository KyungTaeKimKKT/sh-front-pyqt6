from __future__ import annotations
from typing import TYPE_CHECKING

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import datetime, json

class TimeTraceView_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus

        self.all_traces: list[tuple[str, str, float, str]] = []  # [(timestamp, action, duration, description)]
        self.paused_traces: list[tuple[str, str, float, str]] = []
        self.is_paused = False

        self.init_ui()
        self.subscribe_gbus()

    def init_ui(self):
        self.setWindowTitle("Time Tracer Viewer")
        self.setGeometry(150, 150, 800, 600)

        self.layout = QVBoxLayout(self)

        # 상단 버튼
        self.top_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)

        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)

        self.top_layout.addStretch()
        self.top_layout.addWidget(self.clear_button)
        self.top_layout.addWidget(self.pause_resume_button)
        self.layout.addLayout(self.top_layout)

        # 테이블
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Action", "Duration (ms)", "Description"])
        
        self.table.setColumnWidth(0, 150)  # Timestamp
        self.table.setColumnWidth(2, 120)  # Duration
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout.addWidget(self.table)

        self.setLayout(self.layout)
        self.hide()

    def subscribe_gbus(self):
        self.event_bus.subscribe( GBus.TRACE_TIME, self.handle)

    def handle(self, msg: any):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action, duration, description = self.parse_message(msg)

        if self.is_paused:
            self.paused_traces.insert(0, (timestamp, action, duration, description))
        else:
            self.all_traces.insert(0, (timestamp, action, duration, description))
            self.add_table_row(timestamp, action, duration, description)

    def parse_message(self, msg: any) -> tuple[str, float, str]:
        if isinstance(msg, str):
            try:
                msg = json.loads(msg)
            except json.JSONDecodeError:
                return "Unknown", 0.0, msg
        if isinstance(msg, dict):
            action = msg.get("action", "Unknown")
            duration = msg.get("duration", 0.0) * 1000
            description = msg.get("description", "None")
        else:
            return "Unknown", 0.0, str(msg)

        return action, float(duration), description

    def add_table_row(self, timestamp: str, action: str, duration: float, description: str):
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.table.setItem(0, 1, QTableWidgetItem(action))
        self.table.setItem(0, 2, QTableWidgetItem(f"{duration:.2f}"))

        desc_item = QTableWidgetItem(description[:50] + "..." if len(description) > 50 else description)
        desc_item.setToolTip(description)
        self.table.setItem(0, 3, desc_item)

    def clear_logs(self):
        self.all_traces.clear()
        self.table.setRowCount(0)

    def toggle_pause_resume(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_resume_button.setText("Resume")
        else:
            self.pause_resume_button.setText("Pause")
            # 중지된 동안 받은 trace 추가
            for trace in self.paused_traces:
                self.all_traces.insert(0, trace)
                timestamp, action, duration, description = trace
                self.add_table_row(timestamp, action, duration, description)
            self.paused_traces.clear()



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = TimeTraceView_Dialog()
    window.show()

    # 테스트 메시지
    test_messages = [
        {"channel": "login_success", "data": {"login_info": "login_success"}},
        {"channel": "cpu_ram_monitor", "data": {"cpu_percent": 8, "ram_percent": 60}},
        {"channel": "login", "data": True},
        {"channel": "system/ping/|on_ws_message", "data": {"receiver": ["ALL"], "type": "ping"}},
        '{"channel": "invalid_json", "data": "string type"}',
        'not even json'
    ]

    def send_test_messages():
        if test_messages:
            msg = test_messages.pop(0)
            window.handle(msg)
        else:
            timer.stop()

    timer = QTimer()
    timer.timeout.connect(send_test_messages)
    timer.start(1000)

    sys.exit(app.exec())