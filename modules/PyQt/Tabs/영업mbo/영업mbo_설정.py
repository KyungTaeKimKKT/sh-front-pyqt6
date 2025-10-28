from __future__ import annotations
from modules.common_import_v2 import *

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_설정 import Wid_table_영업mbo_설정 as Wid_Table


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
						self.mapping_name_to_widget[name] = None
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = Wid_Table(self)
			self.mapping_name_to_widget['Chart'] = None
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)
	
from plugin_main.widgets.fileopen_single import FileOpenSingle

class 설정__for_Tab( BaseTab_V2 ):
	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main

	# def run(self):
	# 	"""필수 실행 루틴"""
	# 	if INFO.IS_DEV:
	# 		logger.info(f"{self.__class__.__name__} : run")
	# 		logger.info(f"self.table_name: {self.table_name if hasattr(self, 'table_name') else 'table_name not set'}")
	# 		logger.info(f"self.url: {self.url if hasattr(self, 'url') else 'url not set'}")
	# 	self.subscribe_gbus()
	# 	if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
	# 		QTimer.singleShot( 0, lambda: self.simulate_search_pb_click() )


	# no_edit_columns_by_coding = ["id", "매출_year", "매출_month", "id_made", "현재_입력자", "모든현장_금액_sum", "신규현장_금액_sum", "기존현장_금액_sum",
	# 								"모든현장_count", "기존현장_count", "신규현장_count", "is_검증", "is_master적용", "is_개인별할당", "is_관리자마감",
	# 								"등록자","등록일"
	# 								]
	# custom_editor_info = {
	# 	'file': FileOpenSingle,
	# }
	# edit_mode = 'row' ### 'row' | 'cell' | 'None'

	# def create_ui(self):
	# 	start_time = time.perf_counter()
	# 	self.ui = Ui_Tab_Common()
	# 	self.ui.setupUi(self)

	# 	self.stacked_table = 설정__for_stacked_Table(self)
	# 	self.create_table_config_button()
	# 	self.ui.v_table.addWidget(self.stacked_table)

	# 	self.custom_ui()
	# 	self.event_bus.publish_trace_time(
	# 				{ 'action': f"AppID:{self.id}_create_ui", 
	# 			'duration': time.perf_counter() - start_time })

	# def custom_ui(self):
	# 	return
	# 	self.PB_clear_tableconfig = QPushButton('테이블 초기화')
	# 	self.ui.h_search.addWidget(self.PB_clear_tableconfig)
	# 	self.PB_create_tableconfig = QPushButton('테이블 생성 및 update')
	# 	self.ui.h_search.addWidget(self.PB_create_tableconfig)

	# 	self.PB_clear_tableconfig.clicked.connect(self.slot_clear_tableconfig)
	# 	self.PB_create_tableconfig.clicked.connect(self.slot_create_tableconfig)

	# def subscribe_gbus(self):
	# 	super().subscribe_gbus()
	# 	self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	# def unsubscribe_gbus(self):
	# 	self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	# def on_selected_rows(self, selected_rows:list[dict]):
	# 	logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
	# 	self.selected_rows = selected_rows

	# def slot_clear_tableconfig(self):
	# 	dlg_res_button = Utils.generate_QMsg_question(self, title='테이블 초기화', text='테이블 초기화 하시겠습니까?')
	# 	if dlg_res_button != QMessageBox.StandardButton.Ok :
	# 		return
	# 	if hasattr(self, 'selected_rows') and self.selected_rows:
	# 		for row in self.selected_rows:
	# 			_is_ok = APP.API.delete( f"{self.url}{row['id']}/manage_table_config/")
	# 			if _is_ok:
	# 				Utils.generate_QMsg_Information(self, title='테이블 초기화', text='테이블 초기화 완료', autoClose= 1000)
	# 			else:
	# 				Utils.generate_QMsg_critical(self, title='테이블 초기화 실패', text='테이블 초기화 실패' )
	# 		self.selected_rows = []
	# 	else:
	# 		Utils.generate_QMsg_critical(self, title='Select Row error', text='먼저 행을 선택해주세요' )

	# def slot_create_tableconfig(self):
	# 	dlg_res_button = Utils.generate_QMsg_question(self, title='테이블 생성 및 update', text='테이블 생성 및 update 하시겠습니까?')
	# 	if dlg_res_button != QMessageBox.StandardButton.Ok :
	# 		return
	# 	if hasattr(self, 'selected_rows') and self.selected_rows:
	# 		for row in self.selected_rows:
	# 			_is_ok, _ = APP.API.getObj_byURL( f"{self.url}{row['id']}/manage_table_config/")
	# 			if _is_ok:
	# 				Utils.generate_QMsg_Information(self, title='테이블 생성 및 update', text='테이블 생성 및 update 완료', autoClose= 1000)
	# 			else:
	# 				Utils.generate_QMsg_critical(self, title='테이블 생성 및 update 실패', text='테이블 생성 및 update 실패' )
	# 			self.selected_rows = []
	# 	else:
	# 		Utils.generate_QMsg_critical(self, title='Select Row error', text='먼저 행을 선택해주세요' )


