from __future__ import annotations
from typing import TYPE_CHECKING

from modules.global_event_bus import event_bus

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import datetime, json

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class MessageTraceView_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus

        # 전체 메시지 저장용
        self.all_messages:list[tuple[str, str, int, str]] = []  # [(timestamp, channel, sub_count   , data)]
        self.paused_messages:list[tuple[str, str, int, str]] = []  # 중지된 동안 받은 메시지 저장
        self.is_paused = False  # 상태 변수 추가

        self.init_ui()

        self.subscribe_gbus()


    def init_ui(self):
        self.setWindowTitle("Gbus Publish Trace Viewer")
        self.setGeometry(100, 100, 800, 600)

        # 전체 layout
        self.layout = QVBoxLayout(self)

        # 상단 필터 및 버튼 영역
        self.top_layout = QHBoxLayout()
        self.channel_filter = QComboBox()
        self.channel_filter.addItem("All")
        self.channel_filter.currentIndexChanged.connect(self.apply_filter)

        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)

        # Pause/Resume 버튼 추가
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)

        self.top_layout.addWidget(self.channel_filter)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.clear_button)
        self.top_layout.addWidget(self.pause_resume_button)

        self.layout.addLayout(self.top_layout)

        # 메시지 table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Channel", "Sub수", "Data"])
        
        # 열 너비 고정
        self.table.setColumnWidth(0, 150)  # Timestamp 열 너비 고정
        self.table.setColumnWidth(2, 100)  # Sub수 열 너비 고정
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout.addWidget(self.table)

        
        self.setLayout(self.layout)
        # 버튼 연결
        # self.add_message_button.clicked.connect(self.add_random_message)
        self.clear_button.clicked.connect(self.clear_logs)

        self.hide()
    
    def subscribe_gbus(self):
        self.event_bus.subscribe(f"trace_gbus", self.handle)
    
    def handle(self, msg: any):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        channel, sub_count, data = self.parse_message(msg)

        # 메시지 저장
        if self.is_paused:
            self.paused_messages.insert(0, (timestamp, channel, sub_count, data))
        else:
            self.all_messages.insert(0, (timestamp, channel, sub_count, data))

            # 필터용 채널 추가
            if channel not in [self.channel_filter.itemText(i) for i in range(self.channel_filter.count())]:
                self.channel_filter.addItem(channel)

            # 현재 필터에 맞으면 테이블에 추가
            selected_channel = self.channel_filter.currentText()
            if selected_channel == "All" or selected_channel == channel:
                self.add_table_row(timestamp, channel, sub_count, data)

    def parse_message(self, msg: any) -> tuple[str, str, str]:
        if isinstance(msg, str):
            try:
                msg = json.loads(msg)
            except json.JSONDecodeError:
                return "Unknown", "Unknown", msg
        if isinstance(msg, dict):
            channel = msg.get("channel", "Unknown")
            sub_count = msg.get("sub수", "Unknown")
            data = msg.get("data", "None")
        else:
            return "Unknown", "Unknown", str(msg)

        return channel, sub_count, data

    def add_table_row(self, timestamp: str, channel: str, sub_count: str, data: any):
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.table.setItem(0, 1, QTableWidgetItem(channel))
        self.table.setItem(0, 2, QTableWidgetItem(str(sub_count)))

        # 데이터가 dict나 list일 경우 JSON 문자열로 변환
        try:
            if isinstance(data, (dict, list)):
                tooltip_data = json.dumps(data, ensure_ascii=False, indent=2)
                display_data = json.dumps(data, ensure_ascii=False)
            else:
                tooltip_data = display_data = str(data)

        except Exception as e:
            logger.error(f"Error adding table row: {e}")
            tooltip_data = display_data = str(e)
        finally:
            data_item = QTableWidgetItem(display_data[:50] + "..." if len(display_data) > 50 else display_data)
            data_item.setToolTip(tooltip_data)
            self.table.setItem(0, 3, data_item)

    def apply_filter(self):
        selected_channel = self.channel_filter.currentText()
        self.table.setRowCount(0)

        for timestamp, channel, sub_count, data in self.all_messages:
            if selected_channel == "All" or selected_channel == channel:
                self.add_table_row(timestamp, channel, sub_count, data)

    def clear_logs(self):
        self.all_messages.clear()
        self.table.setRowCount(0)
        self.channel_filter.clear()
        self.channel_filter.addItem("All")

    def toggle_pause_resume(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_resume_button.setText("Resume")
        else:
            self.pause_resume_button.setText("Pause")
            # 중지된 동안 받은 메시지 추가
            for message in self.paused_messages:
                self.all_messages.insert(0, message)
                timestamp, channel, sub_count, data = message
                selected_channel = self.channel_filter.currentText()
                if selected_channel == "All" or selected_channel == channel:
                    self.add_table_row(timestamp, channel, sub_count, data)
            self.paused_messages.clear()



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MessageTraceView_Dialog()
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