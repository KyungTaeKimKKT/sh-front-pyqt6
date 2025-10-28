from modules.common_import import *
from modules.PyQt.Tabs.차량관리_V2.tables.wid_table_차량관리_V2_운행관리_사용자	import Wid_table_차량관리_V2_운행관리_사용자 as Wid_table
from modules.PyQt.Tabs.차량관리_V2.차량관리_V2_운행관리_관리자 import 운행관리_관리자__for_stacked_Table, 운행관리_관리자__for_Tab

			
class 운행관리_사용자__for_stacked_Table( 운행관리_관리자__for_stacked_Table):
	def create_active_table(self):
		return Wid_table(self)	


class 운행관리_사용자__for_Tab( 운행관리_관리자__for_Tab ):
	no_edit_columns_by_coding = ['id','차량번호_fk','담당자_fk','차량번호','일자', '담당자','차량번호_data']
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

		self.stacked_table = 운행관리_사용자__for_stacked_Table(self)
		self.create_table_config_button()
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		
		###✅  table selcect widget생성, 추가
		self.ui.h_search.insertWidget( 0, self.create_table_select_widget() )
		self.ui.wid_search.hide()
		self.ui.wid_pagination.hide()


	# def create_table_select_widget(self) -> QWidget:
	# 	widget = QWidget()
	# 	h_layout = QHBoxLayout()
	# 	widget.setLayout( h_layout )

	# 	lb_title = QLabel('관리대상 차량번호 선택')
	# 	h_layout.addWidget( lb_title )

	# 	self.lb_result = QLabel('')
	# 	self.lb_result.setAlignment(Qt.AlignCenter)
	# 	self.lb_result.setFixedWidth ( 16*8 )
	# 	self.lb_result.setStyleSheet('color:yellow;background-color:black;font-weight:bold;')
	# 	h_layout.addWidget( self.lb_result )

	# 	self.pb_select = CustomPushButton(widget, '선택')
	# 	self.pb_select.clicked.connect(self.on_table_select)
	# 	h_layout.addWidget( self.pb_select )
	# 	h_layout.addStretch()
	# 	self.pb_input = CustomPushButton(widget, '신규입력')
	# 	self.pb_input.clicked.connect(self.on_pb_input_clicked)
	# 	h_layout.addWidget( self.pb_input )
	# 	self.pb_input.hide()

	# 	self.pb_refresh = CustomPushButton(widget, 'Refresh')
	# 	self.pb_refresh.clicked.connect(self.api_fetch)
	# 	self.pb_refresh.setEnabled(False)
	# 	h_layout.addWidget( self.pb_refresh )
	# 	return widget

	# def on_table_select(self):
	# 	dlg = Dialog_차량번호_선택(self, 
	# 					url=f"{self.url}사용자별_차량_리스트" , 
	# 					title='관리대상 차량번호 선택',
	# 					search_placeholder='차량번호 검색...',
	# 					list_name_key = '차량번호',
	# 					base_auto_fetch=False
	# 					)
	# 	if dlg.exec():
	# 		selected_dict = dlg.get_selected_name()
	# 		if selected_dict:
	# 			self.lb_result.setText(f'{selected_dict["차량번호"]}')
	# 			self.차량번호_fk = selected_dict['차량번호_fk']
	# 			self.api_fetch()
	# 			self.pb_refresh.setEnabled(True)

	# def api_fetch(self):
	# 	self.slot_search_for(param=f'차량번호_fk={self.차량번호_fk}&page_size=0')
		
	# def custom_ui(self):
	# 	pass

	
	# def slot_fetch_finished(self, msg)->tuple[bool, dict, list[dict]]:
	# 	""" 만약 data가 없으면, 신규입력 버튼 활성화"""
	# 	is_ok, pagination, api_datas = super().slot_fetch_finished(msg)
	# 	if is_ok:
	# 		if len(api_datas) == 0:
	# 			self.pb_input.show()
	# 		else:
	# 			self.pb_input.hide()
	# 	return is_ok, pagination, api_datas

	# def on_pb_input_clicked(self):
	# 	""" 신규입력 버튼 클릭 시, 활성화된 테이블을 활성화( 빈 table이지만 메뉴가 있음 )"""
	# 	self.slot_search_for(
	# 		param=f'차량번호_fk={self.차량번호_fk}&page_size=0', 
	# 		_additional_url='템플릿/')



