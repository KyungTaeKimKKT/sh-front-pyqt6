from modules.common_import import *
from modules.PyQt.Tabs.차량관리_V2.tables.wid_table_차량관리_V2_기준정보 import Wid_table_차량관리_V2_기준정보 as Wid_table

			
class 기준정보__for_stacked_Table(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_table(self)	


class 기준정보__for_Tab( BaseTab):
	no_edit_columns_by_coding = ['id',]
	custom_editor_info = {
	}
	edit_mode = 'row'
	@property
	def is_no_config_initial(self):
		return False
	
	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 기준정보__for_stacked_Table(self)
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		
	def custom_ui(self):
		pass
