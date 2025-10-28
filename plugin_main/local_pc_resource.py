from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.global_event_bus import event_bus  
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import psutil

from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Local_PC_Resource(QObject):
    """
    PC 자원 사용률 업데이트 이벤트 처리
    timer_interval : 업데이트 주기 (ms) , default : 10000ms
    """
    def __init__(self, timer_interval:int=10000):
        super().__init__()
        self.event_bus_type:str = INFO.EVENT_BUS_TYPE_CPU_RAM_MONITOR
        self.event_bus = event_bus
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cpu_ram_monitor)
        self.timer.setInterval(timer_interval)

    def start(self):
        self.update_cpu_ram_monitor()
        self.timer.start()

    def close(self):
        self.timer.stop()
        self.timer.deleteLater()

    def set_timer_interval(self, timer_interval:int):
        self.timer.setInterval(timer_interval)
    
    def get_timer_interval(self):
        return self.timer.interval()

    def stop(self):
        self.timer.stop()

    def update_cpu_ram_monitor(self):
        """
        CPU 및 RAM 사용률 업데이트 이벤트 처리
        """
        
        cpu_percent = int(psutil.cpu_percent(interval=1))
        ram_percent = int(psutil.virtual_memory().percent)
        # logger.info(f"update_cpu_ram_monitor : {cpu_percent}, {ram_percent}")
        self.event_bus.publish(
            GBus.CPU_RAM_MONITOR, 
            { 'cpu_percent': cpu_percent, 'ram_percent': ram_percent }
        )