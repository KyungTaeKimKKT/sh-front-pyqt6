from modules.common_import_v2 import *

from modules.PyQt.Tabs.monitor.charts.wid_chart_resource import Wid_Chart_Resource as Chart

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler_V2

if TYPE_CHECKING:
	from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker

class MainWidget(Base_MainWidget):	
	def update_mapping_name_to_widget(self):
		if self.lazy_config_mode:
			for name, cls_name in self.lazy_config.get('mapping_name_to_widget', {}).items():
				cls = globals().get(cls_name, None)
				if cls :
					kwargs = self.lazy_config.get('kwargs', {}).get(name, {})
					instance = cls( self, **kwargs)
					if instance:
						self.mapping_name_to_widget[name] = instance
					else:
						self.mapping_name_to_widget[name] = None
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = None
			self.mapping_name_to_widget['Chart'] = Chart(self)
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)

	### table이 없는 관계로, 현재는 바로 activate
	def subscribe_gbus(self):
		self.ws_url_name = INFO.get_WS_URL_by_name('server_monitor')
		self.event_bus.subscribe( f"{self.ws_url_name}", self.on_ws_data_received )
	
	def on_ws_data_received(self, data:dict):
		if data:
			self.set_active_to_current()
		else:
			self.set_empty_to_current()

class server_monitor__for_Tab(BaseTab_V2):

	@property
	def pb_text(self) -> str:
		return '실시간 모니터링 중지' if self.is_start_monitor else '실시간 모니터링 시작'
	
	@property
	def is_start_monitor(self) -> bool:
		return getattr(self, '_is_start_monitor', False)
	
	@is_start_monitor.setter
	def is_start_monitor(self, value:bool):
		setattr(self, '_is_start_monitor', value)

	@property
	def ws_url(self) -> str:
		return INFO.get_WS_URL_by_name('server_monitor')
	
	def run(self):
		"""필수 실행 루틴"""
		if INFO.IS_DEV:
			logger.info(f"{self.__class__.__name__} : run")
			logger.info(f"self.table_name: {self.table_name if hasattr(self, 'table_name') else 'table_name not set'}")
			logger.info(f"self.url: {self.url if hasattr(self, 'url') else 'url not set'}")

		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
			self.pb_query.click()

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)
		
		### 서버 선택 추가함
		v_layout.addWidget(self._create_select_server_widget())

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main

	def _create_select_server_widget(self) -> QWidget:
		# 년도 선택 삽입
		self.container_server_select = QWidget()
		h_layout = QHBoxLayout(self.container_server_select)	
		self.label_server = QLabel('서버 선택 :  ', self)
		h_layout.addWidget(self.label_server)		
		self.combo_selected_server = Custom_Combo(self)
		self.combo_selected_server.addItems([f"{INFO.API_SERVER}"])
		h_layout.addWidget(self.combo_selected_server)

		h_layout.addStretch()

		### 조회 버튼 삽입
		self.pb_query = QPushButton(self.pb_text)
		h_layout.addWidget(self.pb_query)
		self.pb_query.clicked.connect(lambda: self.on_off_monitoring(self.combo_selected_server.currentText()))\

		return self.container_server_select


	def on_off_monitoring(self, server_id: Optional[str] = None):
		self.is_start_monitor = not self.is_start_monitor
		self.pb_query.setText(self.pb_text)

		WS_URL_NAME = self.ws_url

		if self.is_start_monitor:
			if WS_URL_NAME not in INFO.WS_TASKS:
				self.ws_handler = ServerMonitorHandler_V2(WS_URL_NAME)
				INFO.WS_TASKS[WS_URL_NAME] = self.ws_handler







