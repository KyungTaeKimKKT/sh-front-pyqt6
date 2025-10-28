from modules.common_import import *


if TYPE_CHECKING:
    from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler

import modules.PyQt.Tabs.monitor.charts.server_resource_realtime as ServerResourceRealtime

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
class Wid_Chart_Resource(QWidget, LazyParentAttrMixin_V2):
    def __init__(self, parent: QWidget=None):
        super().__init__(parent)
        self.data: dict = None
        self.event_bus = event_bus

        self.ws_url_name = INFO.get_WS_URL_by_name('server_monitor')            

        self.ui_initialized = False

        self.run_lazy_attr()

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.APP_ID = APP_ID
            self.app_dict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            self.setup_ui()
            self.subscribe_gbus()

            if hasattr(self, 'data') and self.data:
                self.on_data_changed(self.data)

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")
  
    def subscribe_gbus(self):
        self.event_bus.subscribe(f'{self.ws_url_name}', self.on_data_changed)

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(f'{self.ws_url_name}', self.on_data_changed)

    def on_data_changed(self, api_data: dict):
        try:
            if getattr ( self, '_lazy_source_widget', None) and not getattr(self._lazy_source_widget, 'is_start_monitor', False):
                기존_timestamp = self.timestamp_label.text()
                if "중지된 상태" not in 기존_timestamp:
                    now = datetime.now()
                    add_text = f"  중지된 상태입니다. 중지 시간 : {now.strftime('%Y-%m-%d %H:%M:%S')}"
                    self.timestamp_label.setText(f"{기존_timestamp}  ==> {add_text}")
                return  # 중지 상태면 더 이상 업데이트하지 않음
                
            self.data = api_data.copy()
            ### 1. timestamp 처리
            timestamp = self.data.get("timestamp", "No TimeStamp")
            if timestamp == "No TimeStamp":
                self.timestamp_label.setText(timestamp)
            else:
                timestamp = Utils.format_datetime_str_with_weekday( timestamp, with_year=True, with_weekday=True)
                self.timestamp_label.setText(timestamp)

            ### 2. cpu 처리
            self.cpu_usage_chart.apply_data(copy.deepcopy(self.data["cpu"]))
            ### 3. cpu core 처리
            core_data = {str(k.split('_')[-1]): v for k, v in copy.deepcopy(self.data["cpu"]["cores"]).items()}
            self.cpu_core_chart.apply_data(core_data)
            ### 4. memory 처리
            self.memory_chart.apply_data(copy.deepcopy(self.data["memory"]))
            ### 5. network 처리
            self.network_chart.apply_data(copy.deepcopy(self.data["network"]))
        except Exception as e:
            logger.error(f"Wid_Chart_Resource : slot_apply_resource : {e}")
            logger.error(f"Wid_Chart_Resource : slot_apply_resource : {traceback.format_exc()}")



    def closeEvent(self, event):
        self.stop()

    def stop(self):
        self.unsubscribe_gbus()

    def setup_ui(self):
        logger.debug(f"Wid_Chart_Resource : setup_ui : {self.ui_initialized}")
        if self.ui_initialized:
            return
        if self.layout() is not None:
            return  # 이미 레이아웃이 설정되어 있으면 종료
        logger.debug(f"Wid_Chart_Resource : setup_ui : {self.layout()}")
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setSpacing(5)  # 레이아웃 간의 간격을 최소화

        #### 서버 TimeStamp 표시
        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)  # 위아래 여백 최소화
        self.label = QLabel("서버 TimeStamp : ")
        self.h_layout.addWidget(self.label)
        self.timestamp_label = QLabel("")
        self.h_layout.addWidget(self.timestamp_label)
        self.h_layout.addStretch()
        self.v_layout.addLayout(self.h_layout)

        # CPU 레이아웃
        self.h_layout_cpu = QHBoxLayout()
        self.h_layout_cpu.setContentsMargins(0, 0, 0, 0)  # 위아래 여백 최소화
        self.cpu_frame = QFrame(self)
        self.cpu_frame.setLayout(self.h_layout_cpu)
        self.cpu_frame.setFrameShape(QFrame.Shape.Box)
        self.cpu_frame.setStyleSheet("border: 1px solid gray;")

        # Memory 레이아웃
        self.h_layout_memory = QHBoxLayout()
        self.h_layout_memory.setContentsMargins(0, 0, 0, 0)  # 위아래 여백 최소화
        self.memory_frame = QFrame(self)
        self.memory_frame.setLayout(self.h_layout_memory)
        self.memory_frame.setFrameShape(QFrame.Shape.Box)
        self.memory_frame.setStyleSheet("border: 1px solid gray;")

        # Network 레이아웃
        self.h_layout_network = QHBoxLayout()
        self.h_layout_network.setContentsMargins(0, 0, 0, 0)  # 위아래 여백 최소화
        self.network_frame = QFrame(self)
        self.network_frame.setLayout(self.h_layout_network)
        self.network_frame.setFrameShape(QFrame.Shape.Box)
        self.network_frame.setStyleSheet("border: 1px solid gray;")

        self.cpu_usage_chart = ServerResourceRealtime.CPUMonitorChart(self)
        self.cpu_core_chart = ServerResourceRealtime.CoreUsageBarChart(self)
        self.memory_chart = ServerResourceRealtime.MemoryMonitorChart(self)
        self.network_chart = ServerResourceRealtime.NetworkMonitorChart(self)

        self.h_layout_cpu.addWidget(self.cpu_usage_chart, 3)
        self.h_layout_cpu.addWidget(self.cpu_core_chart, 2)
        self.h_layout_memory.addWidget(self.memory_chart)
        self.h_layout_network.addWidget(self.network_chart)

        self.v_layout.addWidget(self.cpu_frame, 1)
        self.v_layout.addWidget(self.memory_frame, 1)
        self.v_layout.addWidget(self.network_frame, 1)
        self.setLayout(self.v_layout)

        self.ui_initialized = True

