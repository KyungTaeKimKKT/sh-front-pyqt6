from modules.common_import_v2 import *

from modules.PyQt.Tabs.공지및요청사항.tables.Wid_table_요청사항_관리 import Wid_table_요청사항_관리 as Wid_Table
from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

class MainWidget(Base_MainWidget):	
	def update_mapping_name_to_widget(self):
		if self.lazy_config_mode:
			for name, cls_name in self.lazy_config.get('mapping_name_to_widget', {}).items():
				cls = globals().get(cls_name, None)
				if cls :
					kwargs = self.lazy_config.get('kwargs', {}).get(name, {})
					if name == 'Table':
						kwargs['권한_mode'] = '관리자'
					print ('name: ', name, 'kwargs: ', kwargs)
					instance = cls( self, **kwargs)
					if instance:
						self.mapping_name_to_widget[name] = instance
					else:
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = Wid_Table(self)

class 요청사항_관리__for_Tab( BaseTab_V2 ):
	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main