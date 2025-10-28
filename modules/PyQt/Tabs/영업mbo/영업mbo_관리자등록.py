from modules.common_import import *

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_관리자등록 import Wid_table_영업mbo_관리자등록 as Wid_table

class 관리자등록__for_stacked_Table( Base_Stacked_Table ):
	""" override"""
	
	def init_ui(self):
		self.mapping_tables = {
            "none": Wid_table (self,  filter_field="사용자등록수", filter_value=0),
            "normal": Wid_table (self,  filter_field="사용자등록수", filter_value=1),
            "duplicate": Wid_table (self, filter_field="사용자등록수", filter_value=2),
        }
		self.add_Widgets(self.mapping_tables )
		if INFO._get_is_table_config_admin():
			self.addWidget('config table', self.create_config_table() )

	# def create_active_table(self):
	# 	return Wid_table(self)


from modules.PyQt.Tabs.영업mbo.dialog.dlg_mbo_사용자 import MBO_UserSelectDialog
# 😄
class 관리자등록__for_Tab(BaseTab):
	no_edit_columns_by_coding = ['설정_fk', '매출_month', '매출_year', '현장명', 'id', 'by_admin', '신규현장_fk', '금액', 
									'사용자등록수','등록자_snapshot','등록자','등록일','check_admin','부서', '담당자' ]
	custom_editor_info = {
		'고객사': Custom_ListWidget,
		'구분': Custom_ListWidget,
		'기여도': Custom_ListWidget,
		'담당자_fk': MBO_UserSelectDialog,
	}
	edit_mode = 'row' ### 'row' | 'cell' | 'None'

	is_auto_api_query = True
	is_no_config_initial = True		### table config 없음
	
	map_button_text = {
		'없음': '없음 보기',
		'정상': '정상 보기',
		'중복': '중복 보기',
	}
	map_button_to_widgetName = {
		'없음': 'none',
		'정상': 'normal',
		'중복': 'duplicate',
	}
	map_widgetName_to_buttonName = {
		'none': '없음',
		'normal': '정상',
		'duplicate': '중복',
	}

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		### stacked_table switching 을 위한 btn container 및 button 생성
		self.btn_container = QWidget()
		self.btn_container_layout = QHBoxLayout()
		# 버튼으로 페이지 전환
		self.btn_none = CustomPushButton(self, self.map_button_text['없음'])
		self.btn_normal = CustomPushButton(self, self.map_button_text['정상'])
		self.btn_duplicate = CustomPushButton(self, self.map_button_text['중복'])

		self.btn_container_layout.addWidget(self.btn_none)
		self.btn_container_layout.addWidget(self.btn_normal)
		self.btn_container_layout.addWidget(self.btn_duplicate)


		self.btn_container.setLayout(self.btn_container_layout)
		self.ui.v_table.addWidget(self.btn_container)

		self.stacked_table = 관리자등록__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		
		self.btn_none.clicked.connect(lambda: self.stacked_table.setCurrentWidget(self.map_button_to_widgetName['없음']))
		self.btn_normal.clicked.connect(lambda: self.stacked_table.setCurrentWidget(self.map_button_to_widgetName['정상']))
		self.btn_duplicate.clicked.connect(lambda: self.stacked_table.setCurrentWidget(self.map_button_to_widgetName['중복']))

		self.map_button = {
			'없음': self.btn_none,
			'정상': self.btn_normal,
			'중복': self.btn_duplicate,
		}

		for _, btn in self.map_button.items():
			btn.setEnabled(False)
		

	def custom_ui(self):
		self.ui.wid_search.hide()

		self.ui.h_search.addStretch()
		self.PB_API_QUERY = QPushButton('Refresh')
		self.PB_API_QUERY.clicked.connect(self.on_PB_API_QUERY_clicked)
		self.ui.h_search.addWidget(self.PB_API_QUERY)

		self.PB_sum_userInput = QPushButton('사용자 입력 마감')
		self.PB_sum_userInput.setToolTip('사용자 입력 마감(기존 관리자 입력을 초기화합니다.)')
		self.ui.h_search.addWidget(self.PB_sum_userInput)
		self.PB_close_admin_input = QPushButton('관리자 입력 마감')
		self.ui.h_search.addWidget(self.PB_close_admin_input)

		self.PB_sum_userInput.clicked.connect(self.slot_sum_userInput)
		self.PB_close_admin_input.clicked.connect(self.slot_close_admin_input)
		self.PB_close_admin_input.setEnabled(False)

	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows")
		self.event_bus.unsubscribe(f"{self.table_name}:datas_changed")

	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		self.selected_rows = selected_rows

	def on_PB_API_QUERY_clicked(self):
		self.slot_search_for(param=f"page_size=0")

	def on_datas_changed(self, api_datas:list[dict]):
		""" data변경시 button 업데이트 """

		분석_dict = {'없음':0, '정상':0, '중복':0 , }
		정상_id수, 비정상_id수 = 0, 0
		total_count = len(api_datas)
		for _dict in api_datas:
			if _dict['사용자등록수'] == 0:
				분석_dict['없음'] += 1
			elif _dict['사용자등록수'] == 1:
				분석_dict['정상'] += 1
				id = _dict['id'] 
				if id is not None and id > 0:
					정상_id수 += 1
				else:
					비정상_id수 += 1
			elif _dict['사용자등록수'] >= 2:
				분석_dict['중복'] += 1
		
		for key, value in 분석_dict.items():
			if key == '정상':
				text = f"( {value} / {total_count} ) => 저장:{정상_id수} / 비저장:{비정상_id수}"
			else:
				text = f"( {value} / {total_count} )"
			self.map_button[key].setText( self.map_button_text[key] + text )
			self.map_button[key].setEnabled( bool(value) )

		self.PB_close_admin_input.setEnabled( all( not self.map_button[key].isEnabled() for key in ['중복', '없음']) )

		current_widget_name = self.stacked_table.get_current_widget_name()
		if current_widget_name != 'empty' and not self.map_button[self.map_widgetName_to_buttonName[current_widget_name]].isEnabled():
			for key in ['정상', '중복', '없음']:
				if self.map_button[key].isEnabled():
					self.map_button[key].click()
					break
			# self.map_button[key].setStyleSheet(f"background-color: {self.map_button_color[key]};")

	def slot_sum_userInput(self):
		""" 사용자 입력 마감 
		"""
		dlg_res_button = Utils.generate_QMsg_question(None, title="사용자 입력 마감", text="사용자 입력 마감(기존 관리자 입력을 초기화합니다.)")
		if dlg_res_button != QMessageBox.StandardButton.Ok :
			return
		
		_isok, _json = APP.API.getlist( url= self.url+f"request-to-sum-user-input/")
		if _isok:
			Utils.generate_QMsg_Information(None, title="사용자 입력 마감", text="사용자 입력 마감 요청 완료", autoClose=1000)
			self.event_bus.publish(f"{self.table_name}:datas_changed", _json)
		else:
			Utils.generate_QMsg_critical(None, title="사용자 입력 마감 요청 실패", text="사용자 입력 마감 요청 실패")
		

	def slot_close_admin_input(self):
		""" 관리자 입력 마감 
		"""
		dlg_res_button = Utils.generate_QMsg_question(None, title="관리자 입력 마감", text="관리자 입력 마감 <br> 1.자동으로 설정이 close 됩니다. <br> 2. 비정규 는 일괄적으로 변경됩니다.<br> 3. 부서 및 담당자는 일괄적으로 적용됩니다. <br>")
		if dlg_res_button != QMessageBox.StandardButton.Ok :
			return
		
		_isok, _json = APP.API.getlist( url= self.url+f"request-to-close-admin-input/")
		if _isok:
			Utils.generate_QMsg_Information(None, title="관리자 입력 마감", text="관리자 입력 마감 요청 완료", autoClose=1000)
			self.PB_close_admin_input.setEnabled(False)
		else:
			Utils.generate_QMsg_critical(None, title="관리자 입력 마감 요청 실패", text="관리자 입력 마감 요청 실패")

	def run(self):
		super().run()
		if self.is_auto_api_query:
			QTimer.singleShot( 0, lambda: self.on_PB_API_QUERY_clicked())
