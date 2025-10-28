from __future__ import annotations

from modules.common_import_v2 import *

from modules.PyQt.Tabs.home.baseappdashboard import BaseAppDashboard


from modules.PyQt.Tabs.monitor.charts.Dashboard_DB_status import PieChartWidget


class DashboardWidget_ServerDB_Status(BaseAppDashboard):

    def init_kwargs(self):
        return 

    def _create_dashboard_area(self) -> QFrame:
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        h_layout = QHBoxLayout(self.dashboard_area)
        self.dashboard_area.setLayout(h_layout)
        self.main_widget = PieChartWidget(self )
        h_layout.addWidget(self.main_widget)
        return self.dashboard_area


    def update_dashboard_area(self):
        """ 데이터 변경 시 화면 업데이트 
        Dashboard_DB_status 의 update_data 를 약간 변형해서 사용함.
        """
        self.ws_data = GlobalData.server_db_status[-1]   ### 전체 메세지이므로
        timestamp = self.ws_data.get('timestamp', datetime.now().isoformat() )
        message = self.ws_data.get('message', {})
        conn_data = {'idle':0, 'active':0}
        for c in message['connections']:
            key = c['state'] or 'idle'
            conn_data[key] = c['count']
        self.main_widget.update_data(conn_data, max_connections=message.get('max_connections'))

