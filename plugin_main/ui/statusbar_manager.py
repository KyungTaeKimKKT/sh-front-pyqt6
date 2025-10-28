from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from datetime import datetime
from copy import deepcopy
import psutil

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

		# self.event_bus.subscribe(GBus.CPU_RAM_MONITOR, self.statusbar_manager.set_cpu_ram_status)
		# self.event_bus.subscribe(GBus.WS_STATUS, self.statusbar_manager.set_status_WS)
		# self.event_bus.subscribe(GBus.API_STATUS, self.statusbar_manager.set_status_API)


class StatusBarManager:
    def __init__(self, main_window: QMainWindow, duration_api_status: int = 3000, duration_ws_status: int = 500, **kwargs):
        self.kwargs = kwargs
        self.main_window = main_window
        self.statusbar = None
        self.event_bus = event_bus
        
        # 상태 플래그 초기화
        self.flag_status_WS = True
        self.flag_status_API = True
        self.flag_status_Network = True

        self.duration_api_status = duration_api_status ### msec 단위
        self.duration_ws_status = duration_ws_status ### msec 단위
        
        # 스타일 정의
        self.style_status_idle = "border-radius:8px;border:1px solid black;background-color:black;color:white;"
        self.style_status_success = "border-radius:8px;border:1px solid green;background-color:green;color:white;font-weight:bold;"
        self.style_status_fail = "border-radius:8px;border:1px solid red;background-color:red;color:white;font-weight:bold;"

        self.render_statusbar()
        self.main_window.setStatusBar(self.statusbar)

        ### single shot timer 로 5초 후에 상태 초기화
        self.timer_api_status = QTimer()
        self.timer_api_status.setSingleShot(True)
        self.timer_api_status.timeout.connect( self.reset_status_API)
        self.timer_api_status.start(self.duration_api_status)

        self.timer_ws_status = QTimer()
        self.timer_ws_status.setSingleShot(True)
        self.timer_ws_status.timeout.connect(self.reset_status_WS )
        self.timer_ws_status.start(self.duration_ws_status)

        self.map_name_to_timer = {
            'API': {'timer': self.timer_api_status, 'single_times': self.duration_api_status},
            'WS': {'timer': self.timer_ws_status, 'single_times': self.duration_ws_status},
        }

        self.subscribe_gbus()

        first_cpu_ram_data = {
            'cpu_percent': int(psutil.cpu_percent(interval=1)),
            'ram_percent': int(psutil.virtual_memory().percent),
        }
        self.set_cpu_ram_status(first_cpu_ram_data)

    def subscribe_gbus(self):
        self.event_bus.subscribe(GBus.CPU_RAM_MONITOR, self.set_cpu_ram_status)
        self.event_bus.subscribe(GBus.WS_STATUS, self.set_status_WS)
        self.event_bus.subscribe(GBus.API_STATUS, self.set_status_API)    

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(GBus.CPU_RAM_MONITOR, self.set_cpu_ram_status)
        self.event_bus.unsubscribe(GBus.WS_STATUS, self.set_status_WS)
        self.event_bus.unsubscribe(GBus.API_STATUS, self.set_status_API)

    def render_statusbar(self):
        self.statusbar = QStatusBar(self.main_window)
        self.statusbar.setObjectName("statusbar")
        self.main_window.setStatusBar(self.statusbar)
        self.statusbar.height = 20
        
        # 상태바 위젯 생성
        frame = QFrame(self.statusbar)
        h_layout = QHBoxLayout(frame)
        
        # 상태 라벨 생성
        self.lb_status_newtork = QLabel("Network")
        self.lb_status_API = QLabel("API")
        self.lb_status_WS = QLabel("WS")
        
        # 프로그레스바 생성
        self.pbar_status_CPU = QProgressBar()
        self.pbar_status_RAM = QProgressBar()
        
        # 위젯 크기 설정
        self.lb_status_newtork.resize(16, 16)
        self.lb_status_API.resize(16, 16)
        self.lb_status_WS.resize(16, 16)
        
        # 상태바에 위젯 추가
        self.statusbar.addPermanentWidget(self.pbar_status_CPU)
        self.statusbar.addPermanentWidget(self.pbar_status_RAM)
        self.statusbar.addPermanentWidget(self.lb_status_newtork)
        self.statusbar.addPermanentWidget(self.lb_status_API)
        self.statusbar.addPermanentWidget(self.lb_status_WS)
        
        # 프로그레스바 설정
        self.pbar_status_CPU.setFixedSize(100, 16)
        self.pbar_status_RAM.setFixedSize(100, 16)
        self.pbar_status_CPU.setValue(40)
        self.pbar_status_RAM.setValue(30)
        
        # 툴팁 설정
        self.pbar_status_CPU.setToolTip("CPU 사용률!")
        self.pbar_status_RAM.setToolTip("RAM 사용률")
        self.lb_status_newtork.setToolTip("Network 상태: RED시 불가능")
        self.lb_status_API.setToolTip("서버와 접속 상태 : RED시 불가능")
        self.lb_status_WS.setToolTip("서버와 실시간 접속 상태: RED시 불가능")
        
        self.statusbar.showMessage('Start')
        
        return self.statusbar
    

    
    def set_cpu_ram_status(self, data: dict[str, int]):
        """
        CPU 및 RAM 사용률 업데이트 이벤트 처리
        data : { 'cpu_percent': int, 'ram_percent': int }
        """
        self._set_progress_bar_style(self.pbar_status_CPU, data['cpu_percent'])
        self._set_progress_bar_style(self.pbar_status_RAM, data['ram_percent'])
    
    def _set_progress_bar_style(self, progress_bar: QProgressBar, value: int):
        """
        프로그레스바 값에 따라 스타일 설정
        """
        if value < 70:
            # 0~70: 녹색 배경, 검은색 글자
            style = """
                QProgressBar {
                    border: 1px solid #AAAAAA;
                    border-radius: 2px;
                    text-align: center;
                    color: black;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;  /* 녹색 */
                }
            """
        elif value < 90:
            # 70~90: 노란색 배경, 검은색 글자
            style = """
                QProgressBar {
                    border: 1px solid #AAAAAA;
                    border-radius: 2px;
                    text-align: center;
                    color: black;
                }
                QProgressBar::chunk {
                    background-color: #FFEB3B;  /* 노란색 */
                }
            """
        else:
            # 90 이상: 빨간색 배경, 검은색 글자
            style = """
                QProgressBar {
                    border: 1px solid #AAAAAA;
                    border-radius: 2px;
                    text-align: center;
                    color: black;
                }
                QProgressBar::chunk {
                    background-color: #F44336;  /* 빨간색 */
                }
            """
        
        progress_bar.setStyleSheet(style)
        progress_bar.setValue(int(value))
    
    def set_tooltip_last_check_time(self, widget: QLabel, time_str: str = None):
        """
        마지막 check 시간 설정
        """
        time_str = time_str or datetime.now().isoformat()
        widget.setToolTip(f"마지막 check 시간 :  {time_str}")
    
    def set_status_base(self, name:str, widget: QLabel, status: bool | str = None):
        """
        상태 설정 (base로 동작)
        single_times : -1 인 경우, 상태 유지
        """
        if status is True or status == 'success':
            if name in self.map_name_to_timer:
                timer = self.map_name_to_timer[name]['timer']
                timer.stop()
                timer.start(self.map_name_to_timer[name]['single_times'])
            widget.setStyleSheet(self.style_status_success)

        elif status is False or status == 'fail':
            if name in self.map_name_to_timer:
                timer = self.map_name_to_timer[name]['timer']
                timer.stop()
            widget.setStyleSheet(self.style_status_fail)
        else:
            widget.setStyleSheet(self.style_status_idle)
        
        self.set_tooltip_last_check_time(widget)
    
    def set_status_Network(self, status: bool | str = None):
        """
        네트워크 상태 표시를 설정합니다.
        """
        self.flag_status_Network = all ([ bool(self.flag_status_API), bool(self.flag_status_WS)])
        self.set_status_base(name='Network', widget=self.lb_status_newtork, status=self.flag_status_Network )
    
    def set_status_API(self, status: bool | str,):
        """
        API 상태 표시를 설정합니다.
        """
        self.flag_status_API = deepcopy(status)
        self.set_status_base(name='API', widget=self.lb_status_API, status=status)
        self.set_status_Network()       ### set_status_Network() 도  set_status_base() 를 호출하므로, recursion max 주의 ( 즉, set_status_base 에서 호출 금지)
    
    def set_status_WS(self, status: bool | str):
        """
        WebSocket 상태 표시를 설정합니다.
        """
        self.flag_status_WS = deepcopy(status)
        self.set_status_base(name='WS', widget=self.lb_status_WS, status=status)
        self.set_status_Network() ### set_status_Network() 도  set_status_base() 를 호출하므로, recursion max 주의 ( 즉, set_status_base 에서 호출 금지)

    def reset_status_API(self):
        self.lb_status_API.setStyleSheet(self.style_status_idle)

    def reset_status_WS(self):
        self.lb_status_WS.setStyleSheet(self.style_status_idle)
