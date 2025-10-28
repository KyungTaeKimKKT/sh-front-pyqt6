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

class DefaultUserInputDialog(QDialog):
    def __init__(self, parent=None, 
                 default_values: dict[str:list[str]]=None, 
                 on_complete_channelName: str=None,
                 selected_values: dict[str:str]=None,
                 **kwargs ):

        pre_default_values = {
            '고객사': ['현대EL', 'OTIS', 'TKE', '기타'],
            '구분': ['MOD', 'NE', '비정규'],
            '기여도': ['1', '2', '3', '4', '5']
        }

        super().__init__(parent)
        self.event_bus = event_bus
        self.on_complete_channelName = on_complete_channelName
        self.kwargs = kwargs
        self.setWindowTitle("기본 입력값 설정")
        self.resize(400, 200)

        self.default_values = default_values or pre_default_values
        self.selected_values = {}

        self.combo_boxes = {}
        self.init_ui()

        if selected_values:
            for key, value in selected_values.items():
                self.combo_boxes[key].setCurrentText(value)

    def init_ui(self):
        layout = QVBoxLayout(self)

        for label_text in ['고객사', '구분', '기여도']:
            h_layout = QHBoxLayout()
            label = QLabel(f"{label_text}:", self)
            combo = QComboBox(self)
            combo.addItems(self.default_values.get(label_text, []))
            self.combo_boxes[label_text] = combo

            h_layout.addWidget(label)
            h_layout.addWidget(combo)
            layout.addLayout(h_layout)

        # 버튼 영역
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("확인", self)
        cancel_btn = QPushButton("취소", self)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_selected_values(self):
        for key, combo in self.combo_boxes.items():
            self.selected_values[key] = combo.currentText()
        return self.selected_values
    
    def accept(self):
        self.selected_values = self.get_selected_values()
        if self.on_complete_channelName:
            self.event_bus.publish(self.on_complete_channelName, self.selected_values)
        super().accept()
