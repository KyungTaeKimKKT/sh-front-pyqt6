from __future__ import annotations
from typing import TYPE_CHECKING

import json, csv
import datetime
import traceback
import logging

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.logging_config import get_plugin_logger

logger = get_plugin_logger()

# ===================================================
# Logger 전용 Trace Viewer (PyQt6)
# ===================================================

class LoggerTraceView_Dialog(QDialog):
    MAX_LOG_COUNT = 1000  # 최대 1000줄 유지

    LEVEL_COLORS = {
        "DEBUG": QColor(0, 191, 255),
        "INFO": QColor(0, 255, 0),
        "WARNING": QColor(255, 255, 0),
        "ERROR": QColor(255, 0, 0),
        "CRITICAL": QColor(255, 0, 255),
        "UNKNOWN": QColor(0, 191, 255),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus

        self.all_messages: list[tuple[str, str, str, str]] = []
        self.paused_messages: list[tuple[str, str, str, str]] = []
        self.is_paused = False

        self.init_ui()
        self.subscribe_log_events()

    def init_ui(self):
        self.setWindowTitle("Logger Trace Viewer")
        self.setGeometry(100, 100, 1000, 600)

        self.layout = QVBoxLayout(self)

        # 상단 필터 및 버튼
        self.top_layout = QHBoxLayout()

        self.level_filter = QComboBox()
        self.level_filter.addItem("All")
        self.level_filter.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentIndexChanged.connect(self.apply_filter)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Action / Data")
        self.search_box.textChanged.connect(self.apply_filter)

        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)

        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_logs)

        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)

        self.top_layout.addWidget(QLabel("Level Filter:"))
        self.top_layout.addWidget(self.level_filter)
        self.top_layout.addWidget(self.search_box)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.clear_button)
        self.top_layout.addWidget(self.export_button)
        self.top_layout.addWidget(self.pause_resume_button)

        self.layout.addLayout(self.top_layout)
        # 테이블
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Level", "Action", "Data"])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 150)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)  # 🔥 그리드 감추기
        self.table.setFont(QFont("Consolas", 10))  # 🔥 터미널 스타일 폰트
        self.table.verticalHeader().setDefaultSectionSize(24)  # 🔥 행 높이 줄이기
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.show_full_data)

        # ✨ 스타일 설정
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: black;
                color: white;
                gridline-color: black;
                selection-background-color: #444444;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: white;
                color: black;
                padding: 4px;
                border: 0px;
            }
        """)

        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.hide()

    def set_table_style(self):
        self.setStyleSheet("""
            QTableWidget {
                background-color: black;
                color: white;
                font-family: Consolas;
                font-size: 11pt;
                gridline-color: #333;
            }
            QHeaderView::section {
                background-color: white;
                color: black;
                font-weight: bold;
                padding: 4px;
            }
            QTableWidget::item:hover {
                background-color: #333333;
            }
        """)

    def subscribe_log_events(self):
        self.event_bus.subscribe(GBus.TRACE_LOGGER, self.handle)

    def handle(self, msg: dict):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = (msg.get("Level") or "UNKNOWN").upper()
        action = msg.get("Action") or ""
        data = msg.get("Data", "")

        new_log = (timestamp, level, action, data)

        if self.is_paused:
            self.paused_messages.insert(0, new_log)
        else:
            self.all_messages.insert(0, new_log)
            self.trim_logs()
            self.apply_filter()

    def trim_logs(self):
        if len(self.all_messages) > self.MAX_LOG_COUNT:
            self.all_messages = self.all_messages[:self.MAX_LOG_COUNT]

    def add_table_row(self, timestamp: str, level: str, action: str, data: str):
        self.table.insertRow(0)

        # 컬러 셋팅
        color_map = {
            "DEBUG": QColor("cyan"),
            "INFO": QColor("lime"),
            "WARNING": QColor("yellow"),
            "ERROR": QColor("red"),
            "CRITICAL": QColor("magenta"),
            "UNKNOWN": QColor("white")
        }
        color = color_map.get(level.upper(), QColor("white"))

        items = [
            QTableWidgetItem(timestamp),
            QTableWidgetItem(level),
            QTableWidgetItem(action if action else ""),
        ]

        # Data 길이 조정 + Tooltip
        try:
            tooltip_data = str(data)
            display_data = tooltip_data if len(tooltip_data) <= 100 else tooltip_data[:100] + "..."
        except Exception as e:
            display_data = tooltip_data = str(e)

        data_item = QTableWidgetItem(display_data)
        data_item.setToolTip(tooltip_data)

        items.append(data_item)

        for col, item in enumerate(items):
            item.setForeground(QBrush(color))
            self.table.setItem(0, col, item)

        # Fade-in 효과
        self.fade_in_row(0)

    def fade_in_row(self, row: int):
        # 처음 추가 시, 배경을 살짝 투명하게
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QBrush(QColor(30, 30, 30)))  # 약간 밝은 검정색

        # 0.2초 후에 원래 검정색으로 되돌리기
        QTimer.singleShot(200, lambda: self.restore_row_background(row))

    def restore_row_background(self, row: int):
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QBrush(QColor(0, 0, 0)))  # 완전 검정색

    def apply_filter(self):
        selected_level = self.level_filter.currentText()
        keyword = self.search_box.text().lower()

        self.table.setRowCount(0)

        # 최신순으로 거꾸로
        for timestamp, level, action, data in reversed(self.all_messages):
            if selected_level != "All" and level != selected_level:
                continue
            if keyword and keyword not in action.lower() and keyword not in str(data).lower():
                continue
            self.add_table_row(timestamp, level, action, data)

    def clear_logs(self):
        self.all_messages.clear()
        self.table.setRowCount(0)

    def toggle_pause_resume(self):
        self.is_paused = not self.is_paused
        self.pause_resume_button.setText("Resume" if self.is_paused else "Pause")

        if not self.is_paused:
            self.all_messages = self.paused_messages + self.all_messages
            self.paused_messages.clear()
            self.trim_logs()
            self.apply_filter()

    def export_logs(self):
        if not self.all_messages:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Logs", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "Level", "Action", "Data"])
                    for log in self.all_messages:
                        writer.writerow(log)
            except Exception as e:
                print(f"Failed to save CSV: {e}")

    def show_full_data(self, row, column):
        if column == 3:
            item = self.table.item(row, column)
            if item:
                full_text = item.toolTip()

                dlg = QDialog(self)
                dlg.setWindowTitle("Full Data View")
                dlg.resize(700, 500)
                layout = QVBoxLayout(dlg)

                text_browser = QTextBrowser()
                layout.addWidget(text_browser)

                try:
                    # \u 복호화
                    decoded_text = bytes(full_text, "utf-8").decode("unicode_escape")
                    parsed_json = json.loads(decoded_text)

                    # 예쁜 HTML로 변환
                    pretty_html = self.json_to_html(parsed_json)
                    text_browser.setHtml(f"<pre>{pretty_html}</pre>")  # <pre>로 들여쓰기 유지
                except Exception as e:
                    text_browser.setText(full_text)

                dlg.exec()

    def json_to_html(self, obj, indent=0):
        html = ""
        spacing = " " * (indent * 4)

        if isinstance(obj, dict):
            html += "{\n"
            for key, value in obj.items():
                html += spacing + "    "
                html += f"<b>\"{key}\"</b>: {self.json_to_html(value, indent + 1)},\n"
            html += spacing + "}"
        elif isinstance(obj, list):
            html += "[\n"
            for item in obj:
                html += spacing + "    "
                html += f"{self.json_to_html(item, indent + 1)},\n"
            html += spacing + "]"
        elif isinstance(obj, str):
            html += f"<span style='color:green'>\"{obj}\"</span>"
        elif isinstance(obj, bool):
            html += f"<span style='color:blue'>{str(obj).lower()}</span>"
        elif obj is None:
            html += "<span style='color:gray'>null</span>"
        else:  # numbers
            html += f"<span style='color:red'>{obj}</span>"

        return html