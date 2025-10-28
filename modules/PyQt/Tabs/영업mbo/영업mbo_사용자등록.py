from modules.common_import import *

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_사용자등록 import Wid_table_영업mbo_사용자등록 as Wid_table


class 사용자등록__for_stacked_Table( Base_Stacked_Table ):
	def create_active_table(self):
		return Wid_table(self)	
	
from modules.PyQt.compoent_v2.custom_상속.custom_listwidget import Custom_ListWidget

class 사용자등록__for_Tab(BaseTab):
	no_edit_columns_by_coding = ['설정_fk', '매출_month', '매출_year', '현장명', 'id', '등록자_snapshot', 'by_admin', '신규현장_fk', '등록자' ]
	custom_editor_info = {
		'고객사': Custom_ListWidget,
		'구분': Custom_ListWidget,
		'기여도': Custom_ListWidget,
	}
	edit_mode = 'row' ### 'row' | 'cell' | 'None'
	is_no_config_initial = True		### table config 없음

	auto_api_query = True

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 사용자등록__for_stacked_Table(self)		
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })

	def custom_ui(self):
		#### default인 wid_search 숨기기 ==> 사용안함.
		self.ui.wid_search.hide()

		self.line_search = Custom_LineEdit()
		self.line_search.setPlaceholderText('현장명에 한해서 검색합니다.(대소문자 구분 없음)')
		self.ui.h_search.addWidget(self.line_search)
		self.ui.h_search.addStretch()

		### 검색 이벤트 연결
		self.line_search.textChanged.connect(
			lambda text: self.event_bus.publish(f"{self.table_name}:set_filter", text)
		)

		self.PB_API_QUERY = QPushButton('Refresh')
		self.PB_API_QUERY.clicked.connect(self.on_PB_API_QUERY_clicked)
		self.ui.h_search.addWidget(self.PB_API_QUERY)

	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		self.selected_rows = selected_rows

	def on_PB_API_QUERY_clicked(self):
		url = f"{self.url}?page_size=0"
		_isok, _json = APP.API.getlist(url=url)
		if _isok:
			self.event_bus.publish(f"{self.table_name}:datas_changed", _json)
		else:
			Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")

	def run(self):
		if self.auto_api_query:
			QTimer.singleShot(0, self.on_PB_API_QUERY_clicked)
		super().run()
