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


from modules.PyQt.Tabs.monitor.monitor_network_monitor_설정 import network_monitor_설정__for_Tab
class network_monitor__for_Tab(network_monitor_설정__for_Tab):


	def get_pb_text(self) -> str:
		return '실시간 모니터링 시작' if self.get_running_status() else '실시간 모니터링 중지'
	
	def get_running_status(self) -> bool:
		""" running 상태 : True, 중지 상태 : False """
		return self.pb_query.text() == '실시간 모니터링 중지'
	
	@property
	def is_start_monitor(self) -> bool:
		return getattr(self, '_is_start_monitor', False)
	
	@is_start_monitor.setter
	def is_start_monitor(self, value:bool):
		setattr(self, '_is_start_monitor', value)

	@property
	def ws_url(self) -> str:
		return INFO.get_WS_URL_by_name('network_monitor')

	
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


		self.pb_start_stop = CustomPushButton(self, self.pb_text)
		h_layout.addWidget(self.pb_start_stop)

		self.pb_query.clicked.connect(lambda: self.slot_search_for(param={'page_size':0}))
		self.pb_start_stop.clicked.connect(lambda: self.on_off_monitoring(self.combo_selected_server.currentText()))

		return self.container_server_select

	def run(self):
		""" 설정을 상속받았기 때문에 run()시 config를 먼저 가져옴"""
		super().run()
		QTimer.singleShot( 200, lambda: self.pb_start_stop.click())

	def slot_fetch_finished(self, msg) -> tuple[bool, dict, list[dict]]:
		is_ok, pagination, api_datas = super().slot_fetch_finished(msg)
		if is_ok and getattr(self, 'ws_handler', None) is not None:
			self.ws_handler.rePublish_published_msg()
			




	def on_off_monitoring(self, server_id:Optional[str]=None) :

		try:
			self.is_start_monitor = not self.is_start_monitor
			self.pb_start_stop.setText(self.get_pb_text())
			
			if self.is_start_monitor:
				if self.ws_url not in INFO.WS_TASKS:
					self.ws_handler = NetworkMonitorHandler_V2(self.ws_url)
					INFO.WS_TASKS[self.ws_url] = self.ws_handler


			# if self.get_running_status():
			# 	#### 종료
			# 	self.stacked_table.set_empty_to_current()
			# 	if getattr(self, 'ws_handler', None):
			# 		self.ws_handler.stop()
			# 		self.viewer.unsubscribe()
			# 		self.ws_handler = None
			# 		INFO.WS_TASKS.pop(WS_URL_NAME, None)


			# else:
			# 	#### 시작
			# 	### 사내IP-DB 조회
			# 	_isok, _json = APP.API.getlist(f"/모니터링/사내IP-DB/?page_size=0")
			# 	print ( '사내IP-DB 조회 결과 : ', _json)
			# 	if _isok:
			# 		self.viewer = self.stacked_table.run()
			# 		self.viewer.load_data(_json)
			# 	else:
			# 		Utils.QMsg_Critical(self, 
			# 			 title="사내IP-DB 조회 실패", 
			# 			 text=f"사내IP-DB 조회 실패<br> {_json}")
			# 		raise Exception("사내IP-DB 조회 실패")

			# 	# 이전 인스턴스 제거 (있다면)
			# 	if WS_URL_NAME in INFO.WS_TASKS:
			# 		old_ws_handler: NetworkMonitorHandler_V2 = INFO.WS_TASKS.pop(WS_URL_NAME)
			# 		old_ws_handler.stop()
			# 		# old_worker.wait()  # 안전하게 종료 대기

			# 	# 새 인스턴스 생성 및 등록
			# 	self.ws_handler = NetworkMonitorHandler_V2(
			# 		url=WS_URL_NAME,
			# 	)
			# 	INFO.WS_TASKS[WS_URL_NAME] = self.ws_handler

			# 	self.viewer.subscribe()

			# self.pb_query.setText(self.get_pb_text())

		except Exception as e:
			Utils.QMsg_Critical(self, title="모니터링 ON/OFF 실패", text=f"모니터링 ON/OFF 실패 <br> 오류 메시지 : {str(e)}")
			logger.error(f"network_monitor_설정__for_Tab : on_off_monitoring : {e}")
			logger.error(f"{traceback.format_exc()}")