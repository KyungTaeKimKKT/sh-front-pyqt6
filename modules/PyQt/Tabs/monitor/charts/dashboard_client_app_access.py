from __future__ import annotations
from modules.common_import_v2 import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys
import random, platform


def get_font_family():
    return 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic' if platform.system() == 'macOS' else 'NanumGothic'

import matplotlib
matplotlib.rcParams['font.family'] = get_font_family()
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
# 대시보드 위젯
class Dashboard(QWidget, LazyParentAttrMixin_V2 ):
    def __init__(self, parent:QWidget=None, ws_url_name:str='client_app_access_dashboard', **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.event_bus = event_bus
        self.ws_url_name = ws_url_name
        self.event_name = INFO.get_WS_URL_by_name(self.ws_url_name)
        self.max_app_best = kwargs.get('max_app_best', -1)

        self.run_lazy_attr()

    def init_test_timer(self):
        """ 테스트용 타이머 (WS 수신 시 호출될 메서드 대체) """
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_fake_data)
        self.timer.start(3000)

    def setup_ui(self):        
        self.setWindowTitle( self.kwargs.get('title', "Dashboard (Live WS)") )
        self.resize( self.kwargs.get('width', 1200), self.kwargs.get('height', 800) )
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        #### 1. label
        self.label = QLabel("🔄 WebSocket Data Loading...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.label.setFixedHeight(30)
        self.main_layout.addWidget(self.label)

        # charts 전체를 QSplitter로 구성 (수평 방향)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- 좌측 레이아웃 (라벨 + PieChart) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.total_fig = Figure(figsize=(4, 4))
        self.total_canvas = FigureCanvas(self.total_fig)
        left_layout.addWidget(self.total_canvas)

        self.splitter.addWidget(left_widget)

        # --- 우측 레이아웃 (BarChart 2개 세로) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.dept_fig = Figure(figsize=(6, 3))
        self.dept_canvas = FigureCanvas(self.dept_fig)
        right_layout.addWidget(self.dept_canvas)

        self.app_fig = Figure(figsize=(6, 3))
        self.app_canvas = FigureCanvas(self.app_fig)
        right_layout.addWidget(self.app_canvas)

        self.splitter.addWidget(right_widget)

        # 초기 사이즈 비율 설정 (왼쪽:오른쪽 = 1:2)
        self.splitter.setSizes([400, 800])

        self.splitter.setHandleWidth(6)  # ✅ 이 줄 추가!
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #999999;
            }
        """)

        # self.init_charts()


    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.APP_ID = APP_ID
            self.app_dict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            self.setup_ui()
            self.subscribe_gbus()

            if self.event_name in INFO.WS_TASKS:
                self.on_data_changed(INFO.WS_TASKS[self.event_name].get_latest_msg())

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")
  
    def subscribe_gbus(self):
        self.event_bus.subscribe( self.event_name, self.on_data_changed)

    def on_data_changed(self, data:dict):
        self.data = copy.deepcopy(data)
        self.update_data(self.data)


    def init_charts(self):
        # Pie chart (전체)
        self.total_fig = Figure(figsize=(4, 4))
        self.total_canvas = FigureCanvas(self.total_fig)
        self.main_layout.addWidget(self.total_canvas)

        # 조직별 stacked bar
        self.dept_fig = Figure(figsize=(6, 4))
        self.dept_canvas = FigureCanvas(self.dept_fig)
        self.main_layout.addWidget(self.dept_canvas)

        # 앱별 bar
        self.app_fig = Figure(figsize=(6, 4))
        self.app_canvas = FigureCanvas(self.app_fig)
        self.main_layout.addWidget(self.app_canvas)

    def update_data(self, data):
        self.label.setText(f"✅ Last Updated: {Utils.format_datetime_str_with_weekday( data['timestamp'], with_year=True, with_weekday=True)}")

        self.update_pie_chart(data)
        self.update_dept_chart(data)
        self.update_app_chart(data)

    def update_pie_chart(self, data):
        self.total_fig.clear()
        ax = self.total_fig.add_subplot(111)

        labels = ['Online', 'Running', 'Offline']
        values = [
            data.get("online_users", 0),
            data.get("running_users", 0),
            data.get("offline_users", 0)
        ]
        total_users = sum(values)

        # 사용자 수와 퍼센트 함께 표시
        def make_label(pct, all_vals):
            count = int(round(pct * total_users / 100.0))
            return f'{pct:.1f}%\n({count})'

        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels,
            autopct=lambda pct: make_label(pct, values),
            startangle=140,
            textprops=dict(color="black")
        )

        # 가운데 흰 원 + 텍스트
        centre_circle = plt.Circle((0, 0), 0.35, fc='white')
        ax.add_artist(centre_circle)

        ax.text(0, 0, f'총 사용자\n{total_users}명',
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=12,
                fontweight='bold')

        ax.set_title("전체 사용자 현황")
        self.total_canvas.draw()

    def update_dept_chart(self, data):
        self.dept_fig.clear()
        ax = self.dept_fig.add_subplot(111)
        by_dept = data.get("by_department", {})

        labels = list(by_dept.keys())
        online = [by_dept[d]['online'] for d in labels]
        running = [by_dept[d]['running'] for d in labels]
        offline = [by_dept[d]['offline'] for d in labels]

        x = range(len(labels))
        ax.bar(x, offline, label='Offline')
        ax.bar(x, online, bottom=offline, label='Online')
        bottom_running = [offline[i] + online[i] for i in range(len(labels))]
        ax.bar(x, running, bottom=bottom_running, label='Running')

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0)
        ax.set_title("조직별 사용자 상태")
        ax.legend()
        self.dept_canvas.draw()

    def update_app_chart(self, data):
        """ y-scale 조정 : 기본 10, 필요시 10 단위로 올림 """
        self.app_fig.clear()
        ax = self.app_fig.add_subplot(111)

        app_data = data.get("by_app_running", {})
        app_data = self.select_best_app(app_data)

        labels = list(app_data.keys())
        values = list(app_data.values())

        ax.bar(labels, values)
        ax.set_title("앱별 실행 사용자 수")
        ax.tick_params(axis='x', rotation=0)

        # Y축 범위 설정
        if values:
            max_val = max(values)
        else:
            max_val = 0

        # 기본 10, 필요시 10 단위로 올림
        y_max = max(10, int(math.ceil(max_val / 10.0) * 10))
        ax.set_ylim(0, y_max)

        self.app_canvas.draw()

    def update_fake_data(self):
        # 실제 WebSocket 수신 시 이 메서드가 호출된다고 가정
        fake_data = {
            "timestamp": "2025-08-07T12:45:00",
            "total_users": 117,
            "online_users": random.randint(0, 30),
            "running_users": random.randint(0, 50),
            "offline_users": random.randint(30, 117),
            "by_department": {
                "개발팀": {"online": 3, "running": 7, "offline": 5},
                "영업팀": {"online": 5, "running": 2, "offline": 10},
                "관리팀": {"online": 0, "running": 1, "offline": 8},
            },
            "by_app_running": {
                "ERP": 5,
                "메일": 3,
                "App설정_개발자": 1
            }
        }
        self.update_data(fake_data)

    def select_best_app(self, app_data: dict):
        """app_data에서 사용자 수가 많은 상위 N개 앱만 반환"""
        if not isinstance(app_data, dict):
            return {}

        # (app_id, count) 튜플 리스트로 변환 후 사용자 수 기준 내림차순 정렬
        sorted_apps = sorted(app_data.items(), key=lambda x: x[1], reverse=True)

        # 상위 self.max_app_best개만 선택
        if self.max_app_best == -1:
            return dict(sorted_apps)
        elif self.max_app_best > 0 :
            top_apps = dict(sorted_apps[:self.max_app_best])
            return top_apps
        else:
            return {}

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())