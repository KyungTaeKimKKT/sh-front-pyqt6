from modules.common_import import *

from modules.PyQt.Tabs.생산모니터링.tables.table_생산모니터링_당일생산계획 import Wid_Table_for_당일생산계획

class 당일생산계획__for_stacked_Table(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_Table_for_당일생산계획(self)	

class 당일생산계획__for_Tab( BaseTab):
	no_edit_columns_by_coding = ['id','sensor_id','line_no', 'job_qty', 'oper_yn','생성시간','등록자', 'ip_address','is_active','job_qty_time','생산capa' ]
	custom_editor_info = {
	}
	edit_mode = 'row'

	@property
	def is_auto_api_query(self) -> bool:
		return True

	# @property
	# def is_no_config_initial(self) -> bool:
	# 	""" api_datas 로 초기화 할 경우 True """
	# 	return True

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 당일생산계획__for_stacked_Table(self)
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		### 조회 pb 제외한 모두 숨기기
		self.ui.wid_search.hide_except_pb_search()
		

	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		self.selected_rows = selected_rows

	def run(self):
		if hasattr(self, 'url') and self.url and self.is_auto_api_query:
			param = f"?page_size=0"
			url = f"{self.url}{param}".replace('//', '/')
			QTimer.singleShot( 100, lambda: self.slot_search_for()) 
		else:
			Utils.generate_QMsg_critical( self, title="서버 조회 오류", text="url 또는 is_auto_api_query 가 없습니다." )
		super().run()

	def slot_search_for(self, param:Optional[str]=None) :
		#### 고정 시킴
		param = '?page_size=0'
		super().slot_search_for(param)

