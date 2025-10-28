from __future__ import annotations
from modules.common_import_v2 import *

from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis
from collections import deque

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2

MAX_HISTORY = 300  # 5분 기준 가정, 1초 update 시 300개

# ======================== Pie Chart 위젯 ========================

class PieChartWidget(QWidget):
    def __init__(self, parent, title="Pie Chart"):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop)

        self.series = QPieSeries()
        self.chart.addSeries(self.series)

        chart_view = QChartView(self.chart)
        layout = QVBoxLayout(self)
        layout.addWidget(chart_view)
        self.setLayout(layout)

    def update_data(self, data_dict, max_connections=None):
        self.series.clear()
        total = sum(data_dict.values())
        for key, val in data_dict.items():
            if total > 0:
                label = f"{key}<br>({val}, {val*100/total:.1f}%)"  # ✅ HTML <br> 사용
            else:
                label = f"{key}<br>(0, 0%)"
            slice_ = self.series.append(label, val)
            slice_.setLabelVisible(True)

        if max_connections:
            self.chart.setTitle(f"Connections (max={max_connections})")

    

# ======================== Line Chart 위젯 ========================
class LineChartWidget(QWidget):
    def __init__(self, parent, title:str):
        super().__init__(parent)
        self.series = QLineSeries()
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(title)
        
        # X축: 5분 범위, 1분 단위
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("HH:mm")
        self.axis_x.setTickCount(6)  # 5분 범위라 1분 단위 간격
        self.axis_x.setTitleText("Time")
        
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText(title)
        
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)
        self.chart.legend().setVisible(False)
        self.chart_view = QChartView(self.chart)
        layout = QVBoxLayout(self)
        layout.addWidget(self.chart_view)

        self.data = deque(maxlen=MAX_HISTORY)

    # def update_data(self, value:int, timestamp:str):
    #     ts = datetime.fromisoformat(timestamp)
    #     self.data.append((ts, value))
    #     self.series.clear()
    #     print ( f"update_data: {len(self.data)}")
    #     for dt, val in self.data:
    #         self.series.append(dt.timestamp()*1000, val)  # QDateTimeAxis는 msec
    #     if self.data:
    #         max_val = max(v for _, v in self.data)
    #         self.axis_y.setRange(0, max_val*1.2)
    #         min_time = self.data[0][0]
    #         max_time = self.data[-1][0]
    #         self.axis_x.setRange(QDateTime(min_time), QDateTime(max_time))


    def update_data(self, value:int, timestamp:str):
        ts = datetime.fromisoformat(timestamp)
        self.data.append((ts, value))
        self.series.clear()

        # ✅ 5분 이내 데이터만 반영
        now = datetime.now()
        cutoff = now - timedelta(minutes=5)
        visible_data = [(dt, val) for dt, val in self.data if dt >= cutoff]

        for dt, val in visible_data:
            self.series.append(dt.timestamp() * 1000, val)

        if visible_data:
            max_val = max(v for _, v in visible_data)
            self.axis_y.setRange(0, max_val * 1.2)

        # ✅ X축: 현재시간 기준 -5분 ~ 현재시간
        min_time = QDateTime.fromSecsSinceEpoch(int(cutoff.timestamp()))
        max_time = QDateTime.fromSecsSinceEpoch(int(now.timestamp()))
        self.axis_x.setRange(min_time, max_time)

        # ✅ Tick: 1분 단위 (5분 범위라 총 6개 눈금)
        self.axis_x.setTickCount(6)

# ======================== INFO 위젯 ========================
class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(30)  # 고정 높이
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.label_timestamp = QLabel("Last update: --")
        layout.addWidget(self.label_timestamp)
        layout.addStretch()

# ======================== 전체 모니터 위젯 ========================

class DBMonitorWidget(QWidget, LazyParentAttrMixin_V2):
    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.lazy_attrs = {}
        self.event_bus = event_bus
        self.ws_url_name = 'db_live_dashboard'
        self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)

        self.run_lazy_attr()



    def check_ws(self):
        ###BaseAppDashboard 와 동일한 방식으로 처리 : 25-8-22
        ### check 해서 없으면 생성함
        print ( f"check_ws: {self.ws_url}")
        if not self.ws_url:
            self.set_ws_url(self.ws_url_name)

        if not self.ws_url:
           raise ValueError(f"ws_url 이 없습니다. {self.ws_url}")
        print ( f"check_ws: {self.ws_url} in INFO.WS_TASKS: {self.ws_url in INFO.WS_TASKS}")
        if self.ws_url not in INFO.WS_TASKS:
            ws_manager = APP.get_WS_manager()
            connect_msg = self.kwargs.get('ws_handler_kwargs', {}).get('connect_msg', {})
            ws_manager.add(self.ws_url, connect_msg=connect_msg)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1️⃣ INFO 위젯
        self.info_widget = InfoWidget()
        main_layout.addWidget(self.info_widget)

        # 2️⃣ Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(6)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #999999;
            }
        """)
        main_layout.addWidget(self.splitter)

        # Connection widget: Pie + Line (내부 splitter)
        self.connection_widget = QSplitter(Qt.Orientation.Horizontal)
        self.conn_pie = PieChartWidget(self)
        self.conn_line = LineChartWidget(self, "Connections (history)")
        self.connection_widget.addWidget(self.conn_pie)
        self.connection_widget.addWidget(self.conn_line)
        self.connection_widget.setSizes([200, 400])  # 초기 비율 설정
        self.splitter.addWidget(self.connection_widget)

        # Transactions/sec widget
        self.tx_widget = LineChartWidget(self, "Transactions/sec")
        self.splitter.addWidget(self.tx_widget)

        # Block IO widget
        self.io_widget = LineChartWidget(self, "Block IO (reads/hits)")
        self.splitter.addWidget(self.io_widget)

        self.setMinimumSize(900, 450)

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.setup_ui()
            # super().mixin_on_all_lazy_attrs_ready(APP_ID=APP_ID )
            if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
                raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]

            ## 👍 25-8-22 의미는 없지만, 나중에 table이 생성되면 참조할 수 있도록
            self.table_name = Utils.get_table_name(APP_ID)
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)

            self.check_ws()
            self.initialize_with_history()
            self.subscribe_gbus()

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")


    def subscribe_gbus(self):        
        self.event_bus.subscribe( f"{self.ws_url}", self.on_ws_data_received )

    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe( f"{self.ws_url}", self.on_ws_data_received )

    def initialize_with_history(self):
        """App Tab 실행 시 기존 히스토리 데이터로 차트 초기화"""
        if hasattr(GlobalData, 'server_db_status') and GlobalData.server_db_status:
            print(f"히스토리 데이터 {len(GlobalData.server_db_status)}개로 차트 초기화")
            for _dict in GlobalData.server_db_status:
                self.update_by_argument(_dict)


    def on_ws_data_received(self, data:dict):
        #### 원래는 data 를 사용하지만, 현재는 GlobalData.server_db_status 를 사용 : 25-8-22
        if data:
            self.ws_data = GlobalData.server_db_status[-1]   ### 전체 메세지이므로
            self.update_by_argument(self.ws_data)
        else:
            logger.error(f"on_ws_data_received 오류: {data}")

    def update_by_argument( self, data:dict):
        timestamp = data.get('timestamp', datetime.now().isoformat() )
        message = data.get('message', {})
        self.update_monitor(message, timestamp)


    def update_monitor(self, message:dict, timestamp:str):
        # timestamp
        self.info_widget.label_timestamp.setText(f"Last update: {timestamp}")

        # Pie chart connections
        conn_data = {'idle':0, 'active':0}
        for c in message['connections']:
            key = c['state'] or 'idle'
            conn_data[key] = c['count']
        self.conn_pie.update_data(conn_data, max_connections=message.get('max_connections'))

        # Line chart connections
        total_conn = sum(conn_data.values())
        self.conn_line.update_data(total_conn, timestamp)

        # Transactions per sec
        self.tx_widget.update_data(int(message['total_tx']), timestamp)

        # Block IO: blks_hit + blks_read
        block_total = int(message['block_io']['blks_hit'] + message['block_io']['blks_read'])
        self.io_widget.update_data(block_total, timestamp)

# ======================== 실행 테스트 ========================
# if __name__ == "__main__":
#     import sys
#     app = QApplication(sys.argv)
#     w = DBMonitorWidget()
#     w.show()

#     import random
#     from PyQt6.QtCore import QTimer

#     def update_fake():
#         message = {
#             'connections':[{'state':'idle','count':random.randint(20,30)}, {'state':'active','count':random.randint(0,5)}],
#             'total_tx': random.randint(40000000, 40050000),
#             'block_io': {'blks_read': random.randint(10000000,12000000), 'blks_hit': random.randint(150000000,160000000)},
#             'max_connections': 100
#         }
#         w.update_monitor(message, datetime.now().strftime("%H:%M:%S"))

#     timer = QTimer()
#     timer.timeout.connect(update_fake)
#     timer.start(1000)

#     sys.exit(app.exec())