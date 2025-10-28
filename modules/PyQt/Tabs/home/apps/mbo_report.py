from __future__ import annotations
from modules.common_import_v2 import *
from modules.common_graphic_import import *
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# import sys
# import random, platform


# def get_font_family():
#     return 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic' if platform.system() == 'macOS' else 'NanumGothic'

# import matplotlib
# matplotlib.rcParams['font.family'] = get_font_family()
# matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

from modules.PyQt.Tabs.home.baseappdashboard import BaseAppDashboard

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
from modules.PyQt.Tabs.monitor.charts.dashboard_client_app_access import Dashboard

from modules.PyQt.Tabs.영업mbo.graph.pie_chart_지사_구분 import PieChartWidget as PieChartWidget_MBO_Report_지사구분
from modules.PyQt.Tabs.영업mbo.graph.pie_chart_고객사 import PieChartWidget as PieChartWidget_MBO_Report_지사고객사

class Main_ClientUsage(Dashboard):
    """ 상속받아서, home-dashboard 에서 활용 : 전체 사용자 현황 및 앱별 실행 사용자 수 best-5 만"""

    def run_lazy_attr(self):
        """ override 해서 바로 ui 및 각종 초기화, 설정 처리 """
        self.setup_ui()
        # self.subscribe_gbus()
        if self.event_name in INFO.WS_TASKS:
            self.on_data_changed(INFO.WS_TASKS[self.event_name].get_latest_msg())

    def setup_ui(self):        
        # self.setWindowTitle( self.kwargs.get('title', "Dashboard (Live WS)") )
        # self.setMinimumSize ( self.kwargs.get('min_width', 800), self.kwargs.get('min_height', 400) )
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # #### 1. label
        # self.label = QLabel("🔄 WebSocket Data Loading...", self)
        # self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.label.setStyleSheet("font-size: 16px; font-weight: bold;")
        # self.label.setFixedHeight(30)
        # self.main_layout.addWidget(self.label)

        # charts 전체를 QSplitter로 구성 (수평 방향)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- 좌측 레이아웃 (라벨 + PieChart) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.pie_chart_widget = self.create_pie_chart()
        ### old라서, 
        # self.pie_chart_widget_지사구분.run()

        left_layout.addWidget(self.pie_chart_widget)

        self.splitter.addWidget(left_widget)

        # --- 우측 레이아웃 (BarChart 2개 세로) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # self.dept_fig = Figure(figsize=(6, 3))
        # self.dept_canvas = FigureCanvas(self.dept_fig)
        # right_layout.addWidget(self.dept_canvas)

        self.wid_dummy = QWidget()
        right_layout.addWidget(self.wid_dummy)

        self.splitter.addWidget(right_widget)

        # 초기 사이즈 비율 설정 (왼쪽:오른쪽 = 1:1)
        self.splitter.setSizes([self.size().width()//2, self.size().width()//2])

        self.splitter.setHandleWidth(6)  # ✅ 이 줄 추가!
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #999999;
            }
        """)

    def update_data(self, data):
        """ on_data_changed 에서 호출됨 """
        if not data:
            return 
        # self.label.setText(f"✅ Last Updated: {Utils.format_datetime_str_with_weekday( data['timestamp'], with_year=True, with_weekday=True)}")
        print (f"Main_ClientUsage : update_data : {type(data)} : {data}")
        if Utils.is_valid_method(self.pie_chart_widget, 'set_data'):
            self.pie_chart_widget.set_data(data.get('message', [])) # 전체 사용자 현황 => 그대로 사용
        elif Utils.is_valid_method(self.pie_chart_widget, 'on_apply_api_datas'):
            self.pie_chart_widget.on_apply_api_datas(data.get('message', [])) # 전체 사용자 현황 => 그대로 사용
        else:
            raise ValueError(f"pie_chart_widget 에 set_data 또는 on_apply_api_datas 메서드가 없습니다.")
        # self.update_dept_chart(data) # 부서별 사용자 현황
        # self.update_app_chart(data) # 앱별 사용자 현황 => best-5 만 사용

    def create_pie_chart(self):
        raise NotImplementedError("create_pie_chart() 함수는 child 에서 구현해야 함")
        return PieChartWidget_MBO_Report_지사구분(self, **self.kwargs)


class Main_ClientUsage_지사구분(Main_ClientUsage):
    def create_pie_chart(self):
        return PieChartWidget_MBO_Report_지사구분(self, **self.kwargs)
    
class Main_ClientUsage_지사고객사(Main_ClientUsage):
    def create_pie_chart(self):
        return PieChartWidget_MBO_Report_지사고객사(self, **self.kwargs)


class DashboardWidget_MBO_Report_지사구분(BaseAppDashboard):

    def init_kwargs(self):
        pass

    def _create_dashboard_area(self) -> QFrame:
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        h_layout = QHBoxLayout(self.dashboard_area)
        self.dashboard_area.setLayout(h_layout)

        self.main_widget = Main_ClientUsage_지사구분(self, **self.kwargs)
        h_layout.addWidget(self.main_widget)

        return self.dashboard_area
    
    def update_dashboard_area(self):
        print (f"DashboardWidget_MBO_Report_지사구분 : update_dashboard_area : {self._data}")
        self.main_widget.update_data(self._data)


class DashboardWidget_MBO_Report_지사고객사(BaseAppDashboard):

    def init_kwargs(self):
        pass

    def _create_dashboard_area(self) -> QFrame:
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        h_layout = QHBoxLayout(self.dashboard_area)
        self.dashboard_area.setLayout(h_layout)

        self.main_widget = Main_ClientUsage_지사고객사(self, **self.kwargs)
        h_layout.addWidget(self.main_widget)

        return self.dashboard_area
    
    def update_dashboard_area(self):
        print (f"DashboardWidget_MBO_Report_지사고객사 : update_dashboard_area : {self._data}")
        self.main_widget.update_data(self._data)