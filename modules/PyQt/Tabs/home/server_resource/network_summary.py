from __future__ import annotations

from modules.common_import_v2 import *

from modules.PyQt.Tabs.monitor.networkviewer.viewer import Widget_StatusSummary
from plugin_main.websocket.handlers.network_monitor import NetworkMonitorHandler_V2

from modules.PyQt.Tabs.home.baseappdashboard import BaseAppDashboard

class DashboardWidget_NetworkSummary(BaseAppDashboard):


    def init_kwargs(self):
        self.max_ping_count =  self.kwargs.get('max_ping_count', 6)
        self.map_ip_result = defaultdict(list)

    def _create_dashboard_area(self) -> QFrame:
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        h_layout = QHBoxLayout(self.dashboard_area)
        self.dashboard_area.setLayout(h_layout)
        self.main_widget = Widget_StatusSummary(self )
        h_layout.addWidget(self.main_widget)
        return self.dashboard_area
    
    def update_dashboard_area(self):
        self.set_ping_status(self._data['message'])
        self.main_widget.update_summary(self.get_ping_status_summary())

    # def setup_ui(self):
    #     self.main_layout = QVBoxLayout()

    #     ### 1. header 생성 : 제목, update 시간, goApp 버튼

    #     self.header_widget = QWidget(self)
    #     self.header_layout = QHBoxLayout()
    #     self.header_widget.setLayout(self.header_layout)

    #     self.lb_title = QLabel(self)
    #     self.lb_title.setText("네트워크 상태 모니터링")
    #     self.lb_title.setStyleSheet("font-weight:bold;background-color:yellow;")
    #     self.header_layout.addWidget(self.lb_title)
    #     self.header_layout.addSpacing(10)
    #     self.header_layout.addWidget ( QLabel( 'Update 시간:'))
    #     self.lb_update_time = QLabel(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    #     self.lb_update_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #     self.lb_update_time.setStyleSheet("background-color:yellow;")
    #     self.header_layout.addWidget(self.lb_update_time)

    #     self.header_layout.addStretch()
    #     self.PB_go_widget = QPushButton('해당 App 이동')
    #     self.PB_go_widget.clicked.connect(lambda: self.go_widget())
    #     self.header_layout.addWidget(self.PB_go_widget)

    #     self.main_layout.addWidget(self.header_widget)

    #     ### 2. 메모리, CPU 사용률 그래프 생성

    #     self.main_widget = Widget_StatusSummary(self )
    #     self.main_layout.addWidget(self.main_widget)

    #     self.setLayout(self.main_layout)

    # def go_widget(self):
    #     action = INFO.get_menu_to_action(div='monitor', name='network_monitor')
    #     if action and isinstance(action, QAction):
    #         action.trigger()
    
    # def set_ws_url(self, ws_url_name:str=None):
    #     self.ws_url_name = ws_url_name or self.ws_url_name
    #     self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)
    #     self.try_count +=1

    # def check_ws_handler(self):
    #     if not self.ws_url:
    #         self.set_ws_url(self.ws_url_name)

    #     if self.ws_url not in INFO.WS_TASKS:
    #         self.ws_handler = NetworkMonitorHandler_V2(self.ws_url)
    #         INFO.WS_TASKS[self.ws_url] = self.ws_handler

    # def subscribe_gbus(self):
    #     self.event_bus.subscribe( self.ws_url, self.on_data_changed)


    # def unsubscribe_gbus(self):
    #     self.event_bus.unsubscribe( self.ws_url, self.on_data_changed)

    # def on_data_changed(self, data: dict):
    #     try:
    #         # print (f"DashboardWidget_NetworkSummary : on_data_changed : {data}")
    #         timestamp = data.get('timestamp', 'Unknown')
    #         if timestamp:
    #             self.lb_update_time.setText( Utils.format_datetime_str_with_weekday(timestamp, with_year=True ) )
    #         self._data = data.copy()
    #         self.set_ping_status(self._data['message'])
    #         self.main_widget.update_summary(self.get_ping_status_summary())
    #     except Exception as e:
    #         logger.error(f"on_data_changed 오류: {e}")
    #         logger.error(traceback.format_exc())

    def get_ping_status_summary(self) -> dict:
        """전체 ping 상태에 대한 통계 요약"""
        statuses = [self.calculate_ping_status(pings) for pings in self.map_ip_result.values()]
        counts = Counter(statuses)

        summary = {
            "총 host": len(statuses),
            "정상": counts.get("정상", 0),
            "주의": counts.get("주의", 0),
            "경고": counts.get("경고", 0),
            "비정상": counts.get("비정상", 0),
            "N/A": counts.get("N/A", 0),
        }
        return summary
    

    def set_ping_status(self, status_list: List[Dict[str, list]]):
        """ 현재 노드들의 ping 상태 업데이트 """
        self.ping_status = status_list

        if isinstance(status_list, list):
            for resultDict in status_list:
                for ip, value in resultDict.items():
                    self.map_ip_result[ip].append(value[0])
                    if len(self.map_ip_result[ip]) > self.max_ping_count:
                        self.map_ip_result[ip].pop(0)

        else:
            logger.error(f"set_ping_status : {status_list} 형식 오류")
            logger.error( status_list )


    def calculate_ping_status(self, result_list:list[bool]) -> str:
        """ ping status를  str 으로 반환 """
        if not result_list:
            return "N/A"
        total = len(result_list)
        true_count = sum(1 for v in result_list if v is True)
        if total == true_count:
            return "정상"
        elif true_count == 0:
            return "비정상"
        elif true_count < 2:
            return "경고"
        else:
            return "주의"