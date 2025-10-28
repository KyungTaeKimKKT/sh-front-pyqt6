from modules.common_import_v2 import *

from modules.PyQt.Tabs.일일업무.calendar.calendar_전기사용량 import QCalendar_전기사용량

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
			self.mapping_name_to_widget['Calendar'] = QCalendar_전기사용량(self)


class 전기사용량__for_Tab( BaseTab_V2 ):

	def _create_wid_search(self) -> Wid_Search_Only_Refresh:
		""" 필요시 오버라이드"""
		self.wid_search = Wid_Search_Only_Refresh(self)
		return self.wid_search

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main


	# def create_ui(self):
	# 	start_time = time.perf_counter()
	# 	self.ui = Ui_Tab_Common()
	# 	self.ui.setupUi(self)

	# 	self.stacked_table = 전기사용량__for_stacked_Table(self)
	# 	self.ui.v_table.addWidget(self.stacked_table)

	# 	self.custom_ui()
	# 	self.event_bus.publish_trace_time(
	# 				{ 'action': f"AppID:{self.id}_create_ui", 
	# 			'duration': time.perf_counter() - start_time })
		
	
	# def custom_ui(self):
	# 	#### search edit hide, pagesize 'ALL'로 변경 및  hide
	# 	self.ui.wid_search.hide_except_pb_search()


	# def subscribe_gbus(self):
	# 	super().subscribe_gbus()
	# 	self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
	# 	# self.PB_download.clicked.connect(
	# 	# 	lambda: self.event_bus.publish(f"{self.table_name}:request_excel_export", True)
	# 	# )
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

	# def slot_search_for(self, param:Optional[str]=None) :
	# 	"""
	# 	결론적으로 main 함수임.
	# 	Wid_Search_for에서 query param를 받아서, api get list 후,
	# 	table에 _update함.	
	# 	"""		
	# 	self.start_time = time.perf_counter()
	# 	self.prev_param = copy.deepcopy(self.param)
	# 	#### 분기점 : direct로 pub 하니,  page=xx 만 들어옴.
	# 	if param and 'page=' in param:
	# 		parts = self.prev_param.split('&')
	# 		parts = [p for p in parts if not p.startswith('page=')]
	# 		parts.append(param)
	# 		self.param = '&'.join(parts)
	# 	else:
	# 		self.param = param

	# 	default_param = f"year={datetime.today().year}&month={datetime.today().month}" + f"&page_size=0"
	# 	url = self.url + '?' + default_param
	# 	self.api_channel_name = f"fetch_{url}"
	# 	self.on_fetch_start(url, self.api_channel_name, self.slot_fetch_finished)


