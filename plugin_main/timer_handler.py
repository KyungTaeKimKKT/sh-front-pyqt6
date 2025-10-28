from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from PyQt6.QtCore import QTimer, QObject

from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow

class Timer_Handler(QObject):
    def __init__(self, parent:Optional[QMainWindow]=None):
        super().__init__(parent)
        self.event_bus = event_bus

        self.timer_1sec = QTimer()
        self.timer_1sec.timeout.connect(self.update_timer_1sec)
        self.timer_1sec.setInterval(1000)
        self.timer_1sec.start()

    def update_timer_1sec(self):
        """ timer에 맞춰서 self.event_bus에 이벤트 발생 """
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        if now.second == 0:
            self.event_bus.publish(GBus.TIMER_1MIN, now_str)
