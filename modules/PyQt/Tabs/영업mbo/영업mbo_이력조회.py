from modules.common_import import *
from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_이력조회 import Wid_table_영업mbo_이력조회 as Wid_table


class 이력조회__for_stacked_Table( Base_Stacked_Table ):
	def create_active_table(self):
		return Wid_table(self)	

from modules.PyQt.Tabs.영업mbo.dialog.dlg_mbo_사용자 import MBO_UserSelectDialog
class 이력조회__for_Tab( BaseTab):
	no_edit_columns_by_coding = ['All']
	custom_editor_info = {
		'고객사': Custom_ListWidget,
		'구분': Custom_ListWidget,
		'기여도': Custom_ListWidget,
		'담당자': MBO_UserSelectDialog,
	}

	edit_mode = 'None'
	is_auto_api_query = False
	is_no_config_initial = False

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 이력조회__for_stacked_Table(self)
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		return
		self.PB_clear_tableconfig = QPushButton('테이블 초기화')
		self.ui.h_search.addWidget(self.PB_clear_tableconfig)
		self.PB_create_tableconfig = QPushButton('테이블 생성 및 update')
		self.ui.h_search.addWidget(self.PB_create_tableconfig)

		self.PB_clear_tableconfig.clicked.connect(self.slot_clear_tableconfig)
		self.PB_create_tableconfig.clicked.connect(self.slot_create_tableconfig)

	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		self.selected_rows = selected_rows

