from modules.common_import_v2 import *

from modules.PyQt.Tabs.일일업무.tables.Wid_table_일일업무_조직_전사 import Wid_table_일일업무_조직_전사 as Wid_Table
from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

from modules.PyQt.Tabs.plugins.ui.v2.Wid_search_common import Wid_Search_Only_Refresh

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

class 조직_전사__for_Tab( BaseTab_V2):

	def _create_wid_search(self) -> Wid_Search_Only_Refresh:
		""" 필요시 오버라이드"""
		self.wid_search = Wid_Search_Only_Refresh(self)
		return self.wid_search

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main
	


	# no_edit_columns_by_coding = ['All']
	# edit_mode = 'None' ### 'row' | 'cell' | 'None'
	# custom_editor_info = {}
	# is_no_config_initial = False	### table config 없음
	# is_auto_api_query = True

	# def create_ui(self):
	# 	start_time = time.perf_counter()
	# 	self.ui = Ui_Tab_Common()
	# 	self.ui.setupUi(self)

	# 	self.stacked_table = 조직_전사__for_stacked_Table(self)
	# 	self.create_table_config_button()
	# 	self.ui.v_table.addWidget(self.stacked_table)

	# 	self.custom_ui()
	# 	self.event_bus.publish_trace_time(
	# 				{ 'action': f"AppID:{self.id}_create_ui", 
	# 			'duration': time.perf_counter() - start_time })

	# def custom_ui(self):
	# 	#### search edit hide, pagesize 'ALL'로 변경 및  hide
	# 	self.ui.wid_search.hide_except_pb_search()
	# 	self.PB_download = QPushButton('전사 다운로드')
	# 	self.ui.wid_search.ui.horizontalLayout.addWidget(self.PB_download)


	# def subscribe_gbus(self):
	# 	super().subscribe_gbus()
	# 	self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
	# 	self.PB_download.clicked.connect(
	# 		lambda: self.event_bus.publish(f"{self.table_name}:request_excel_export", True)
	# 	)
	# 	logger.debug(f"{self.__class__.__name__} : subscribe_gbus: {self.table_name}; event_bus_name: {self.table_name}:request_excel_export")

	# def unsubscribe_gbus(self):
	# 	self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
	# 	logger.debug(f"{self.__class__.__name__} : unsubscribe_gbus: {self.table_name}; event_bus_name: {self.table_name}:selected_rows")

	# def on_selected_rows(self, selected_rows:list[dict]):
	# 	logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
	# 	self.selected_rows = selected_rows

	# def run(self):
	# 	super().run()
	# 	if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
	# 		QTimer.singleShot( 100, lambda: self.ui.wid_search.ui.PB_Search.click())
	# 		# self.ui.wid_search.ui.PB_Search.click()