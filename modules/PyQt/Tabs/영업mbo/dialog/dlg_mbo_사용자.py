from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()






class MBO_UserSelectDialog(QDialog):
    """
    data 예시 = [
        {"id": 1, "user_성명": "홍길동", "MBO_표시명_부서": "영업팀"},
        {"id": 2, "user_성명": "김철수", "MBO_표시명_부서": "기획팀"},
        {"id": 3, "user_성명": "이영희", "MBO_표시명_부서": "영업팀"},
    ]
    """
    def __init__(self, parent, 
                 data: list[dict]=[], 
                 on_complete_channelName: str=None,
                 index: QModelIndex=None,
                 **kwargs ):
        super().__init__(parent)
        self.data = data
        self.on_complete_channelName = on_complete_channelName
        self.index = index
        self.kwargs = kwargs
        self.selected_user = None
        
        if self.data:
            # self.sorted_data = self.sort_data()
            self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("사용자 선택")
        self.resize(400, 300) 

        layout = QVBoxLayout(self)

        label = QLabel("사용자를 선택하세요:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        for item in self.data:
            display_text = f"{item['MBO_표시명_부서']} - {item['user_성명']}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

            # 더블클릭 시 확인 처리
        self.list_widget.itemDoubleClicked.connect(lambda item: self.accept())

        self.show()

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def sort_data(self):
        # 정렬: 부서 → 성명
        sorted_data = sorted(self.data, key=lambda x: (x["MBO_표시명_부서"], x["user_성명"]))
        return sorted_data

    def get_selected_user(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None
    
    def accept(self):
        self.selected_user = self.get_selected_user()
        logger.debug(f"self.selected_user: {self.selected_user}")
        event_bus.publish(self.on_complete_channelName, {
            'index': self.index,
            'value': self.selected_user
        })
        self.close()
