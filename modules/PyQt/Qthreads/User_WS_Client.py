
from PyQt6.QtCore import *
import websocket
import json

from info import Info_SW as INFO
from datetime import datetime
from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class User_WS_Client(QThread):
	signal_ws_opened = pyqtSignal()
	signal_ws_closed = pyqtSignal()
	signal_receive_message = pyqtSignal(dict)	
	signal_ping_received = pyqtSignal()
	signal_ws_status = pyqtSignal(bool)

	def __init__(self, parent, url:str|None=None, **kwargs):
		super().__init__(parent)
		self.max_ping_interval = kwargs.get('max_ping_interval', 10)
		self.max_not_ping_count = kwargs.get('max_not_ping_count', 3)
		self.count_ping_not_received = 0
		self.enableTrace = INFO.WS_EnableTrace
		self.URL = INFO.URI_WS + (url if url else 'message/')
		self.reconnect_attempts = 0
		self.max_reconnect_attempts = float('inf')  # 무한대
		self.reconnect_delay = 1  # 초기 지연 시간 (초)
		self.max_reconnect_delay = 60  # 최대 지연 시간 (초)

		self.is_reconnecting = False 

		# websocket.enableTrace(self.enableTrace)
		# https://pypi.org/project/websocket-client/
		self.ws = websocket.WebSocketApp(
			self.URL,
			on_open   = self.on_open,
			on_message= self.on_message,
			on_error  = self.on_error,
			on_close  = self.on_close 
		)
		self.count_ping_not_received = 0
		self.timer = QTimer()
		self.timer.timeout.connect(self.check_connection)
		self.timer.start(5000)  # 5초마다 연결 상태 확인

	def run(self):
		self.ws.run_forever()

	def stop(self):
		self.ws.close()
		self.timer.stop()

	def check_connection(self):

		if not self.ws.sock or not self.ws.sock.connected:
			self.signal_ws_status.emit(False)
			return 
			# self.reconnect()
		# else:
		# 	# 마지막 ping 메시지를 수신한 시간과 현재 시간의 차이를 계산
		# 	if (datetime.now() - self.last_ping_time).total_seconds() > self.max_ping_interval:
		# 		if self.count_ping_not_received > self.max_not_ping_count:
		# 			self.signal_ping_not_received.emit()

		# 		else:
		# 			self.count_ping_not_received += 1
		# 	else:
		# 		self.reconnect_attempts = 0  # Reset attempts on successful connection
		# 		self.reconnect_delay = 1  # Reset delay
		# 		ic(f"{self.URL} : check_connection : OK !!!")

	def reconnect(self):

		self.signal_ws_status.emit(False)
		if self.reconnect_attempts < self.max_reconnect_attempts:
			self.is_reconnecting = True  # 재연결 시작
			QMetaObject.invokeMethod(self.timer, "stop", Qt.QueuedConnection)  # 타이머 중지
			self.reconnect_attempts += 1


			# QTimer를 사용하여 지연 시간 후에 재연결 시도

			QTimer.singleShot(self.reconnect_delay * 1000, self.attempt_reconnect)
				
			self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)


		else:
			ic("Max reconnect attempts reached.")

	@pyqtSlot()
	def attempt_reconnect(self):

		self.is_reconnecting = False  # 재연결 시도 후 플래그 해제
		self.ws = websocket.WebSocketApp(
			self.URL,
			on_open=self.on_open,
			on_message=self.on_message,
			on_error=self.on_error,
			on_close=self.on_close
		)
		self.ws.run_forever()
	
	def close(self):
		if self.ws:
			self.ws.close()
			self.signal_ws_closed.emit()

	def on_open(self, ws):
		self.signal_ws_status.emit(True)
		return 
		self.reconnect_attempts = 0  # Reset attempts on successful connection
		self.reconnect_delay = 1  # Reset delay
		self.is_reconnecting = False  # 재연결 플래그 해제
		QMetaObject.invokeMethod(self.timer, "start", Qt.QueuedConnection, Q_ARG(int, 5000))  # 타이머 재시작
		self.signal_ws_opened.emit()
		ic(f'{self.URL} is opened !!!')
	
	def on_message(self, ws, msg):
		msg = json.loads(msg)
		# self.signal_ws_status.emit(True)
		# ic ( self.URL, msg )

		if msg.get('type') == 'ping':
			self.signal_ping_received.emit()
			# 서버에서 보낸 ping 메시지를 수신했을 때의 처리
			self.last_ping_time = datetime.now()
		else:
			self.signal_receive_message.emit(msg)



	def send(self, msg):
		self.ws.send( msg )

	def on_error(self, ws, error ):
		# ic ( f'{self.URL} Error !!! : {error}')
		self.signal_ws_status.emit(False)
		return
		if not self.is_reconnecting:  # 재연결 중이 아닐 때만 재연결 시도
			self.reconnect()

	def on_close(self, ws, close_status_code, close_msg):
		# ic ( f'{self.URL} is Closed!!!\n {close_status_code}  {close_msg}')
		self.signal_ws_status.emit(False)	
		return
		# if not self.is_reconnecting:  # 재연결 중이 아닐 때만 재연결 시도
		# 	self.reconnect()