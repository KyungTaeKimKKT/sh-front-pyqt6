from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Custom_ListWidget(QDialog):
    def __init__(self, parent=None, 
                 _list=None, 
                 on_complete_channelName:Optional[str]=None, 
                 index:Optional[QModelIndex]=None, 
                 **kwargs):
        super().__init__(parent)
        self._list = _list or []
        self.selected_list_item = None  # 리스트에서 선택된 아이템 저장
        self.validator = kwargs.get('validator', None)  # validator를 kwargs에서 가져옴
        self.is_validation = kwargs.get('is_validation', False)  # is_validation을 kwargs에서 가져옴
        self.on_complete_channelName = on_complete_channelName
        self.index = index

        self.setup_ui(**kwargs)

    def setup_ui(self, **kwargs):
        layout = QVBoxLayout()
        self.setWindowTitle(kwargs.get('title', '선택'))

        self.list_widget = QListWidget()
        self.list_widget.addItems(self._list)

        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def on_item_double_clicked(self, item):
        self.selected_list_item = item.text()
        if self.on_complete_channelName:
            구독자수 = event_bus.publish( self.on_complete_channelName, {
                'index': self.index,
                'value': self.selected_list_item
            })
            logger.debug(f"Custom_ListWidget: self.on_complete_channelName: {self.on_complete_channelName}, 구독자수: {구독자수}")
        self.close()
