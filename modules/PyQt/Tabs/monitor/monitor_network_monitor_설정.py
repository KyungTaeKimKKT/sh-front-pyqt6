from modules.common_import_v2 import *

from modules.PyQt.Tabs.monitor.networkviewer.viewer import NetworkTopologyViewer as Chart

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
from plugin_main.websocket.handlers.network_monitor	import  NetworkMonitorHandler_V2

if TYPE_CHECKING:
	from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker


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
			self.mapping_name_to_widget['Table'] = None
			self.mapping_name_to_widget['Chart'] = Chart(self)
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)

	### table이 없는 관계로, 현재는 바로 activate
	def subscribe_gbus(self):
		self.ws_url_name = INFO.get_WS_URL_by_name('server_monitor')
		self.event_bus.subscribe( f"{self.ws_url_name}", self.on_ws_data_received )
	
	def on_ws_data_received(self, data:dict):
		if data:
			self.set_active_to_current()
		else:
			self.set_empty_to_current()

class network_monitor_설정__for_Tab(BaseTab_V2):

	@property
	def pb_text(self) -> str:
		return '실시간 모니터링 중지' if self.is_start_monitor else '실시간 모니터링 시작'
	
	@property
	def is_start_monitor(self) -> bool:
		return getattr(self, '_is_start_monitor', False)
	
	@is_start_monitor.setter
	def is_start_monitor(self, value:bool):
		setattr(self, '_is_start_monitor', value)

	def _create_wid_search(self) :
		return None
	
	def _create_wid_pagination(self):
		return None

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)
		
		### 서버 선택 추가함
		v_layout.addWidget(self._create_select_server_widget())

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main

	
	def _create_select_server_widget(self) -> QWidget:
		# 년도 선택 삽입
		self.container_server_select = QWidget()
		h_layout = QHBoxLayout(self.container_server_select)	
		self.label_server = QLabel('서버 선택 :  ', self)
		h_layout.addWidget(self.label_server)		
		self.combo_selected_server = Custom_Combo(self)
		self.combo_selected_server.addItems([f"{INFO.API_SERVER}"])
		h_layout.addWidget(self.combo_selected_server)

		h_layout.addStretch()


		self.pb_query = CustomPushButton(self, 'DB 조회(Refresh)')
		h_layout.addWidget(self.pb_query)

		self.pb_save = CustomPushButton(self, 'DB 저장')
		h_layout.addWidget(self.pb_save)

		self.pb_query.clicked.connect(lambda: self.slot_search_for(param={'page_size':0}))
		self.pb_save.clicked.connect(lambda: self.slot_save())

		return self.container_server_select

	def run(self):
		"""필수 실행 루틴"""
		if INFO.IS_DEV:
			logger.info(f"{self.__class__.__name__} : run")
			logger.info(f"self.table_name: {self.table_name if hasattr(self, 'table_name') else 'table_name not set'}")
			logger.info(f"self.url: {self.url if hasattr(self, 'url') else 'url not set'}")
		self.subscribe_gbus()
		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
			QTimer.singleShot( 0, lambda: self.pb_query.click() )


	
	def slot_save(self, server_id:Optional[str]=None) :
		try:
			self.viewer = self.mainWidget.mapping_name_to_widget['Chart']
			# if not (hasattr(self, 'viewer') and isinstance(self.viewer, Chart) ):
			# 	self.viewer = self.stacked_table.run()

			send_datas =self.viewer.get_current_topology_data()
			print ( 'send_datas', send_datas)

			### 데이터 전송 : bulk mode : 
			# url = self.url + 'bulk_create_or_update/'
			url = self.url + 'batch_create_or_update/'
			print ( 'url', url)
			_is_ok, _json = APP.API.post ( url, data={'datas':json.dumps(send_datas, ensure_ascii=False) })
			if _is_ok:
				self.viewer.load_data(_json)
				Utils.generate_QMsg_Information(self, title="저장 완료", text="저장 완료", autoClose= 1000)
			else:
				Utils.generate_QMsg_critical(self, title="저장 실패", text=f"저장 실패<br>오류 메시지 : {_json}")
		except Exception as e:
			Utils.generate_QMsg_critical(self, title="저장 실패", text=f"저장 실패<br>오류 메시지 : {str(e)}")
			logger.error(f"slot_save 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	def slot_fetch_finished(self, msg) -> tuple[bool, dict, list[dict]]:
		is_ok, pagination, api_datas = super().slot_fetch_finished(msg)
		if is_ok :
			if api_datas:
				self.viewer:Chart = self.mainWidget.mapping_name_to_widget['Chart']
				self.viewer.load_plot_data(api_datas)
			else:
				Utils.QMsg_Critical(self, title="API 조회 자료가 없읍니다.", text="API 조회 자료가 없읍니다.")
		else:
			Utils.QMsg_Critical(self, title="API 조회 실패", text=f"API 조회 실패 <br> 오류 메시지 : {msg}")

		return is_ok, pagination, api_datas








	


