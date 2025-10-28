
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

class WS_Thread_Sync (QThread):
	signal_opened = pyqtSignal()
	signal_closed = pyqtSignal()
	signal_receive_message = pyqtSignal(dict)	
	signal_ping_received = pyqtSignal()
	signal_status = pyqtSignal(bool)
	""" SHORT PERIOD SYNC WS
		url을 받아서, runfoever 하는 스레드
		종료시 close() 호출
	"""

	def __init__(self, parent, url:str|None=None, **kwargs):
		super().__init__(parent)
		self.enableTrace = INFO.WS_EnableTrace
		self.URL = INFO.URI_WS + (url if url else 'message/')
		self.running = False

	def run(self):
		self.ws = websocket.WebSocketApp(
			self.URL,
			on_open   = self.on_open,
			on_message= self.on_message,
			on_error  = self.on_error,
			on_close  = self.on_close 
		)
		self.ws.run_forever()

	def stop(self):
		self.close()

	def close(self):
		if self.ws:
			self.ws.close()
			self.signal_closed.emit()

	def on_open(self, ws):
		self.signal_status.emit(True)
		self.running = True
		self.signal_opened.emit()


	
	def on_message(self, ws, msg):
		msg = json.loads(msg)
		# self.signal_ws_status.emit(True)


		if msg.get('type') == 'ping':
			self.signal_ping_received.emit()
			# 서버에서 보낸 ping 메시지를 수신했을 때의 처리
			self.last_ping_time = datetime.now()
		else:
			self.signal_receive_message.emit(msg)


	def send(self, msg):
		if self._is_in_receivers(msg):
			self.ws.send( msg )

	def on_error(self, ws, error ):
		# ic ( f'{self.URL} Error !!! : {error}')
		self.signal_ws_status.emit(False)
		return
		if not self.is_reconnecting:  # 재연결 중이 아닐 때만 재연결 시도
			self.reconnect()

	def on_close(self, ws, close_status_code, close_msg):
		# ic ( f'{self.URL} is Closed!!!\n {close_status_code}  {close_msg}')
		self.signal_status.emit(False)		
		self.running = False

	def is_running(self):
		return self.running

	def _is_in_receivers(self, msg:dict) -> bool:
		""" 수신자가 나인지 확인, 내가 수신자면 True """
		receivers = msg.get('receiver')
		if len(receivers) == 1 and isinstance(receivers[0], str) and receivers[0].lower() == 'all':
			return True
		return bool( INFO.USERID in receivers )