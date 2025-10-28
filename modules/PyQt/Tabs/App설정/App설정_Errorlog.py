from modules.common_import_v2 import *

from modules.PyQt.Tabs.App설정.tables.Wid_table_App설정_errorlog import Wid_table_App설정_errorlog as Wid_table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

			
class MainWidget(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_table(self)	


		
class Errorlog__for_Tab(BaseTab_V2):
	def _init_by_child(self):
		pass

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main

