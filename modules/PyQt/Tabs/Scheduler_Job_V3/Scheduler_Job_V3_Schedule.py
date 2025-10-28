from modules.common_import_v2 import *

from modules.PyQt.Tabs.Scheduler_Job_V3.tables.wid_table_job_schedule import Wid_table_job_schedule
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

class MainWidget(Base_Stacked_Table):
	
	def create_active_table(self):
		return Wid_table_job_schedule(self)

class Schedule__for_Tab(BaseTab_V2):

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main
