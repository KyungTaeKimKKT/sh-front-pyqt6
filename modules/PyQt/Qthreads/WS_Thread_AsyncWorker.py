import asyncio
import websockets  # websocket-client 대신 websockets 사용
import json
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from PyQt6.QtCore import QThread, pyqtSignal

from info import Info_SW as INFO
from datetime import datetime
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class  WS_Thread_AsyncWorker_V2(QThread):
	on_message = pyqtSignal(dict)  # url과 msg
	reconnected = pyqtSignal(str)       # url (재접속시 원래 url)
	error = pyqtSignal(dict )          # 예외 발생시 예외 객체

	def __init__(self, url:str, parent=None, **kwargs):
		"""
		urls : 웹소켓 연결할 url 리스트
		parent : QThread 부모
		kwargs : max_retry, retry_delay

		"""
		super().__init__(parent)
		self.kwargs = kwargs
		self.event_bus = event_bus
		self.url = url
		self.running = True
		self.max_retry = kwargs.get('max_retry', 100)  # 최대 재접속 횟수   5
		self.retry_delay = kwargs.get('retry_delay', 3)  # 재접속 delay 3

		self.default_connect_msg = {
			"action": "init_request",		#### 25-7 초기 연결 요청 : init ==> init_request로 변경
			"user_id": INFO.USERID,
			"timestamp": datetime.now().isoformat()
		}
		self.connect_msg = kwargs.get('connect_msg', self.default_connect_msg)
		self.is_send_connect_msg:bool = kwargs.get('is_send_connect_msg', True)
    
	async def ws_handler(self):
		"""
		비동기 웹소켓 연결 핸들러 :연결 유지 및 msg 처리
		"""
		retry_count = 0
		while self.running and retry_count < self.max_retry:
			try:
				# websockets 라이브러리 사용
				async with websockets.connect(INFO.URI_WS+self.url) as ws:
					self.ws = ws
					retry_count = 0
					# 연결 직후 서버에 접속 정보 전송
					try:
						logger.info(f"{self.url} connect_msg: {self.connect_msg}")
						if self.is_send_connect_msg:
							await ws.send(json.dumps(self.connect_msg, ensure_ascii=False))

					except Exception as e:
						logger.error(f"웹소켓 연결 오류: {e}")
						logger.error(f"{traceback.format_exc()}")

					while self.running:
						try:
							msg = await asyncio.wait_for(ws.recv(), timeout=30)  # 타임아웃 추가
							self.on_message.emit( json.loads(msg))
							# self.event_bus.publish(f"{self.url}|on_ws_message", json.loads(msg))
							self.event_bus.publish(GBus.WS_STATUS , True)
							
						except asyncio.TimeoutError:
								# 핑/퐁 메시지 전송 또는 연결 상태 확인
							# try:
							# 	# 연결 상태 확인을 위한 ping 전송
							# 	pong = await ws.ping()
							# 	await asyncio.wait_for(pong, timeout=10)
							# except:
							# 	# ping 실패 시 연결이 끊어진 것으로 간주

							# 	break
							if not self.running:
								break
							continue



			except websockets.exceptions.ConnectionClosedError as e:
				retry_count += 1
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]
				if self.running:  # 종료 중이 아닐 때만 재연결 시도
					await asyncio.sleep(self.retry_delay)

				else:
					break

			except websockets.exceptions.ConnectionClosedOK:
				# 정상적인 연결 종료 처리
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]

				break

			# except websockets.exceptions.ConnectionClosedError as e:
			except Exception as e:
				retry_count += 1
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]
				if self.running:  # 종료 중이 아닐 때만 재연결 시도
					await asyncio.sleep(self.retry_delay)

				else:
					break
			if not self.running:
				break

		if retry_count >= self.max_retry:
			logger.error(f"{self.url} 최대 재연결 시도 횟수({self.max_retry})를 초과했읍니다.")


	async def main(self):
		"""
		메인 함수 : 모든 URL에 대한 웹소켓 연결 시작
		"""
		await self.ws_handler()


	def run(self):
		"""
		QThread 실행 함수 : 내부에서 asyncio.run() 호출
		"""

		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)
		# ⭐ Task로 별도 생성
		self.task = self.loop.create_task(self.ws_handler())

		try:
			self.loop.run_forever()
		except Exception as e:
			print(f"[run_forever] 예외: {e}")
		finally:
			self.loop.run_until_complete(self._shutdown_loop())
			self.loop.close()

	async def _shutdown_loop(self):
		if self.ws:
			try:
				await self.ws.close()
			except:
				pass
		if self.task and not self.task.done():
			self.task.cancel()
			try:
				await self.task
			except asyncio.CancelledError:
				pass

	async def send_message_async(self, message:dict):
		"""
		웹소켓 메시지 비동기 전송 함수
		"""

		message_str = json.dumps(message, ensure_ascii=False)
		try:
			print ( 'send_message_async : ', message_str )
			await self.ws.send(message_str)
		except Exception as e:
			logger.error(f"웹소켓 메시지 전송 오류: {e}")
			logger.error(f"{traceback.format_exc()}")


	def send_message(self, message:dict):
		"""
		웹소켓 메시지 전송 , message는 dict 타입
		"""
		if not self.running:
			return False			

		try:
			# loop = asyncio.get_event_loop()
			loop = getattr(self, 'loop', None)
			if loop is not None and loop.is_running():
				# 비동기 함수를 Future로 변환하여 실행
				future = asyncio.run_coroutine_threadsafe(
					self.send_message_async( message), loop
				)
				return True  # 메시지 전송 요청 성공
			else:
				error_msg = f'이벤트 루프가 실행 중이 아닙니다: {self.url}'
				logger.error(f"이벤트 루프가 실행 중이 아닙니다: {self.url}")
				self.error.emit({'url': self.url, 'error_msg': error_msg})
				return False
		except Exception as e:
			error_msg = f"메시지 전송 중 예외 발생: {str(e)}"
			logger.error(f"메시지 전송 중 예외 발생: {str(e)}")
			logger.error(f"{traceback.format_exc()}")
			self.error.emit({'url': self.url, 'error_msg': error_msg})
			return False


	def _is_in_receivers(self, msg:dict) -> bool:
		""" 수신자가 나인지 확인, 내가 수신자면 True """
		if  isinstance(msg, (dict, list)) is False:
			# logger.info(f" :_is_in_receivers : msg:  {type(msg)} {msg[:100]}")
			return False
		receivers = msg.get('receiver', [])
		if len(receivers) == 1 and isinstance(receivers[0], str) and receivers[0].lower() == 'all':
			return True
		# logger.info(f"receivers: {receivers}, INFO.USERID: {INFO.USERID}")
		return bool(INFO.USERID in receivers if isinstance(receivers, list) else False)
	

	def stop(self):
		"""웹소켓 연결 종료 요청"""
		self.running = False

		if hasattr(self, 'ws') and self.ws is not None:
			try:
				if self.loop and self.loop.is_running():
					asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
			except Exception as e:
				logger.error(f"웹소켓 종료 중 오류: {e}")
			finally:
				self.ws = None

		if self.loop and self.loop.is_running():
			self.loop.call_soon_threadsafe(self.loop.stop)

		self.quit()
		if self.isRunning():
			if not self.wait(3000):
				self.terminate()


	def close(self):
		"""
		웹소켓 연결 종료
		"""
		self.stop()



class  WS_Thread_AsyncWorker(QThread):
	received = pyqtSignal(str, dict)  # url과 msg
	reconnected = pyqtSignal(str)       # url (재접속시 원래 url)
	error = pyqtSignal(str, dict )          # 예외 발생시 예외 객체

	def __init__(self, url:str, parent=None, **kwargs):
		"""
		urls : 웹소켓 연결할 url 리스트
		parent : QThread 부모
		kwargs : max_retry, retry_delay

		"""
		super().__init__(parent)
		self.event_bus = event_bus
		self.url = url
		self.running = True
		self.max_retry = kwargs.get('max_retry', 100)  # 최대 재접속 횟수   5
		self.retry_delay = kwargs.get('retry_delay', 3)  # 재접속 delay 3
		self.connections = {}  # URL별 연결정보 추적
    
	async def ws_handler(self):
		"""
		비동기 웹소켓 연결 핸들러 :연결 유지 및 msg 처리
		"""
		retry_count = 0
		while self.running and retry_count < self.max_retry:
			try:
				# websockets 라이브러리 사용
				async with websockets.connect(INFO.URI_WS+self.url) as ws:

					retry_count = 0
					# INFO.WS_TASKS[self.url] = self

					# 연결 직후 서버에 접속 정보 전송
					try:
						connect_msg = {
							"action": "init_request",		#### 25-7 초기 연결 요청 : init ==> init_request로 변경
							"user_id": INFO.USERID,
							"timestamp": asyncio.get_event_loop().time()
						}
						logger.info(f"{self.url} connect_msg: {connect_msg}")
						await ws.send(json.dumps(connect_msg, ensure_ascii=False))

					except Exception as e:
						logger.error(f"웹소켓 연결 오류: {e}")
						logger.error(f"{traceback.format_exc()}")

					while self.running:
						try:
							msg = await asyncio.wait_for(ws.recv(), timeout=30)  # 타임아웃 추가
							self.event_bus.publish(f"{self.url}|on_ws_message", json.loads(msg))
							self.event_bus.publish(GBus.WS_STATUS , True)
							
						except asyncio.TimeoutError:
								# 핑/퐁 메시지 전송 또는 연결 상태 확인
							try:
								# 연결 상태 확인을 위한 ping 전송
								pong = await ws.ping()
								await asyncio.wait_for(pong, timeout=10)
							except:
								# ping 실패 시 연결이 끊어진 것으로 간주

								break
							if not self.running:
								break
							continue

			except websockets.exceptions.ConnectionClosedError as e:
				retry_count += 1
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]
				if self.running:  # 종료 중이 아닐 때만 재연결 시도
					await asyncio.sleep(self.retry_delay)

				else:
					break

			except websockets.exceptions.ConnectionClosedOK:
				# 정상적인 연결 종료 처리
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]

				break

			# except websockets.exceptions.ConnectionClosedError as e:
			except Exception as e:
				retry_count += 1
				if self.url in INFO.WS_TASKS:
					del INFO.WS_TASKS[self.url]
				if self.running:  # 종료 중이 아닐 때만 재연결 시도
					await asyncio.sleep(self.retry_delay)

				else:
					break


	
		if retry_count >= self.max_retry:
			logger.error(f"{self.url} 최대 재연결 시도 횟수({self.max_retry})를 초과했읍니다.")


	async def main(self):
		"""
		메인 함수 : 모든 URL에 대한 웹소켓 연결 시작
		"""
		await self.ws_handler()


	def add_url(self, url: str):
		"""
		Dynamically adds a new URL to the worker and starts a WebSocket handler for it.
		"""
		if url not in self.urls:
			self.urls.append(url)
			# Start a new handler for the new URL
			asyncio.ensure_future(self.ws_handler(url))
			logger.info(f"Added new URL: {url}")

	def remove_url(self, url: str):
		"""
		Dynamically removes a URL from the worker and closes the WebSocket connection for it.
		"""
		if url in self.urls:
			self.urls.remove(url)
			if url in self.connections:
				ws = self.connections[url]
				asyncio.ensure_future(ws.close())  # Gracefully close the WebSocket connection
				del self.connections[url]
				logger.info(f"Removed URL: {url}")
		else:
			logger.warning(f"URL not found: {url}")

	def run(self):
		"""
		QThread 실행 함수 : 내부에서 asyncio.run() 호출
		"""
		print(f"WS_Thread_AsyncWorker : run : {self.url}")
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(self.main())

	def on_message(self, url:str, msg:str):
		"""
		웹소켓 메시지 수신 핸들러
		"""
		try:
			print(f"WS_Thread_AsyncWorker : on_message : {msg}")
			msg_dict = json.loads(msg)
			if self._is_in_receivers(msg_dict):
				self.received.emit(url, msg_dict)  # 여기서만 시그널 발생
		except json.JSONDecodeError:
			logger.error(f"JSON 파싱 오류: {msg}")
			logger.error(f"{traceback.format_exc()}")
			self.error.emit(url, f"JSON 파싱 오류: {msg}")
		except Exception as e:
			logger.error(f"웹소켓 메시지 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			self.error.emit(url, e)  # 기타 예외 처리 추가


	async def send_message_async(self, url:str, message:dict):
		"""
		웹소켓 메시지 비동기 전송 함수
		"""
		if url in self.connections:
			ws = self.connections[url]
			message_str = json.dumps(message, ensure_ascii=False)
			try:
				await ws.send(message_str)
				return True
			except Exception as e:
				logger.error(f"웹소켓 메시지 전송 오류: {e}")
				logger.error(f"{traceback.format_exc()}")
				self.error.emit(url, e)

				return False
		else:
			self.error.emit(url, f"웹소켓 연결이 없읍니다: {url}")
			logger.error(f"웹소켓 연결이 없읍니다: {url}")

			return False

	def send_message(self, url:str, message:dict):
		"""
		웹소켓 메시지 전송 , message는 dict 타입
		"""
		if not self.running:

			return False
			
		if url in self.connections:
			# 현재 실행 중인 이벤트 루프 가져오기
			try:
				loop = asyncio.get_event_loop()
				if loop.is_running():
					# 비동기 함수를 Future로 변환하여 실행
					future = asyncio.run_coroutine_threadsafe(
						self.send_message_async(url, message), loop
					)
					return True  # 메시지 전송 요청 성공
				else:
					error_msg = f'이벤트 루프가 실행 중이 아닙니다: {url}'
					logger.error(f"이벤트 루프가 실행 중이 아닙니다: {url}")
					self.error.emit(url, error_msg)
					return False
			except Exception as e:
				error_msg = f"메시지 전송 중 예외 발생: {str(e)}"
				logger.error(f"메시지 전송 중 예외 발생: {str(e)}")
				logger.error(f"{traceback.format_exc()}")
				self.error.emit(url, e)
				return False
		else:
			error_msg = f'웹소켓 연결이 없읍니다: {url}'

			self.error.emit(url, error_msg)
			return False

	def _is_in_receivers(self, msg:dict) -> bool:
		""" 수신자가 나인지 확인, 내가 수신자면 True """
		if  isinstance(msg, (dict, list)) is False:
			# logger.info(f" :_is_in_receivers : msg:  {type(msg)} {msg[:100]}")
			return False
		receivers = msg.get('receiver', [])
		if len(receivers) == 1 and isinstance(receivers[0], str) and receivers[0].lower() == 'all':
			return True
		# logger.info(f"receivers: {receivers}, INFO.USERID: {INFO.USERID}")
		return bool(INFO.USERID in receivers if isinstance(receivers, list) else False)
	

	def stop(self):
		"""
		웹소켓 연결 종료
		"""
		self.running = False
		
		# 이벤트 루프 가져오기 시도
		try:
			loop = asyncio.get_event_loop()
		except RuntimeError:
			# 이벤트 루프가 없는 경우 새로 생성
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
		
		# 연결 정보 복사 (반복 중 딕셔너리 변경 방지)
		connections_copy = dict(self.connections)
		
		# 모든 연결 명시적으로 닫기
		for url, connection in connections_copy.items():
			try:
				# 연결이 생성된 원래 이벤트 루프에서 종료 처리
				if hasattr(connection, '_loop'):
					original_loop = connection._loop
					if original_loop.is_running():
						asyncio.run_coroutine_threadsafe(connection.close(), original_loop)
					else:
						# 이미 종료된 루프라면 무시
						pass
				else:
					# 안전하게 연결 정보만 삭제
					pass
			except Exception as e:
				logger.error(f"웹소켓 연결 종료 오류: {e}")
				logger.error(f"{traceback.format_exc()}")
			finally:
				if url in self.connections:
					del self.connections[url]
			
			# 스레드 종료
			self.quit()
		
		# 스레드가 실행 중인지 확인하고 종료 대기
		if self.isRunning():
			if not self.wait(3000):  # 3초 동안 스레드 종료 대기
				
				self.terminate()
			else:
				pass




	def close(self):
		"""
		웹소켓 연결 종료
		"""
		self.stop()
