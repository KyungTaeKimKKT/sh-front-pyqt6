from modules.common_import_v2 import *

# from modules.PyQt.Tabs.monitor.networkviewer.viewer import NetworkTopologyViewer as Chart

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
# from plugin_main.websocket.handlers.network_monitor	import  NetworkMonitorHandler_V2
from modules.PyQt.Tabs.monitor.charts.Dashboard_DB_status import DBMonitorWidget as Dashboard

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
			self.mapping_name_to_widget['Chart'] = None
			self.mapping_name_to_widget['Dashboard'] = Dashboard
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)

	### table이 없는 관계로, 현재는 바로 activate
	def subscribe_gbus(self):
		self.ws_url_name = INFO.get_WS_URL_by_name('db_live_dashboard')
		self.event_bus.subscribe( f"{self.ws_url_name}", self.on_ws_data_received )
	
	def on_ws_data_received(self, data:dict):
		if data:
			self.set_active_to_current()
		else:
			self.set_empty_to_current()



class Server_DB_Status__for_Tab(BaseTab_V2):

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main