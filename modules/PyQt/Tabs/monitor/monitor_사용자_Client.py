from modules.common_import_v2 import *

from modules.PyQt.Tabs.monitor.tables.wid_table_monitor_사용자_client import Wid_table_monitor_사용자_Client as Wid_Table
from modules.PyQt.Tabs.monitor.charts.dashboard_client_app_access import Dashboard

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2


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
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = Wid_Table(self)
			self.mapping_name_to_widget['Dashboard'] = Dashboard(self)
		# print(f"{self.__class__.__name__} : create_mapping_name_to_widget : self.parent(): {self.parent()}")
		# self.mapping_name_to_widget['Table'] = Wid_Table(self.parent())
		print ( 'update_mapping_name_to_widget 완료: ', self.mapping_name_to_widget )
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)


class 사용자_Client__for_Tab(BaseTab_V2):

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main
