from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING, Protocol
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
import json, time, copy

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

### handlers plugin
from plugin_main.websocket.handlers.app권한_handler import AppAuthorityHandler, AppAuthorityHandler_V2
from plugin_main.websocket.handlers.ping_handler import PingHandler, PingHandler_V2
from plugin_main.websocket.handlers.users_handler import UsersHandler, UsersHandler_V2
from plugin_main.websocket.handlers.tabletotalconfig_handler import TableTotalConfigHandler, TableTotalConfigHandler_V2
# from plugin_main.websocket.handlers.tableconfig_handler import TableConfigHandler
from plugin_main.websocket.handlers.resources_handler import ResourcesHandler, ResourcesHandler_V2
# from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler
# from plugin_main.websocket.handlers.network_monitor import NetworkMonitorHandler
from plugin_main.websocket.handlers.gongji_handler import GongiHandler, GongiHandler_V2
from plugin_main.websocket.handlers.client_app_access_log import ClientAppAccessLogHandler, ClientAppAccessDashboardHandler


from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker
# from modules.PyQt.Qthreads.WS_AsyncWorker import WS_AsyncWorker

### v2 임
from plugin_main.websocket.handlers.pyro5_handler import Pyro5Handler

from info import Info_SW as INFO

import modules.user.utils as Utils

if TYPE_CHECKING:
    from main import MainWindow, Ui_MainWindow  # 순환 임포트 방지

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()


class WS_InitManager_V3:
    def __init__(self):
        self.init_url_names = INFO.get_WS_URLS_Init_Names()
        self.check_init_names()
        self.url_tasks  = [
            (INFO.get_WS_URL_by_name('app_권한'), AppAuthorityHandler_V2),
            (INFO.get_WS_URL_by_name('ping'), PingHandler_V2),
            (INFO.get_WS_URL_by_name('active_users'), UsersHandler_V2),
            (INFO.get_WS_URL_by_name('table_total_config'), TableTotalConfigHandler_V2),
            (INFO.get_WS_URL_by_name('resource'), ResourcesHandler_V2),
            (INFO.get_WS_URL_by_name('공지사항'), GongiHandler_V2),
            (INFO.get_WS_URL_by_name('client_app_access_log'), ClientAppAccessLogHandler),
            (INFO.get_WS_URL_by_name('client_app_access_dashboard'), ClientAppAccessDashboardHandler),
        ]
        self.initialize_workers()

    def initialize_workers(self):
        # 핸들러 객체 생성
        for url, handler in self.url_tasks:
            if url == INFO.get_WS_URL_by_name('client_app_access_log'):
                INFO.WS_TASKS[url] = handler(url,  is_send_connect_msg=False)
            else:
                INFO.WS_TASKS[url] = handler(url)
        print ( INFO.WS_TASKS )
    
    def check_init_names(self):
        print ( self.init_url_names )
        for name in self.init_url_names:
            if not self.check_connect_url(name):
                return False
        return True

    def check_connect_url(self, get_name:str) -> bool:
        if INFO.get_WS_URL_by_name(get_name) :
            return True
        print(f"check_connect_url: {get_name} 없음")    
        return False


# class WS_InitManager_V2:
#     def __init__(self):
#         self.url_tasks  = [
#             (WS_URLS.app_권한, AppAuthorityHandler_V2),
#             (WS_URLS.ping, PingHandler_V2),
#             (WS_URLS.active_users, UsersHandler_V2),
#             (WS_URLS.table_total_config, TableTotalConfigHandler_V2),
#             (WS_URLS.resources, ResourcesHandler_V2),
#             (WS_URLS.WS_공지사항, GongiHandler_V2),
#             (WS_URLS.client_app_access_log, ClientAppAccessLogHandler),
#             (WS_URLS.client_app_access_dashboard, ClientAppAccessDashboardHandler),
#         ]
#         self.initialize_workers()

#     def initialize_workers(self):
#         # 핸들러 객체 생성
#         for url, handler in self.url_tasks:
#             if url == WS_URLS.client_app_access_log:
#                 INFO.WS_TASKS[url] = handler(url,  is_send_connect_msg=False)
#             else:
#                 INFO.WS_TASKS[url] = handler(url)




# class WS_InitManager:
#     def __init__(self):
#         self.url_tasks  = [
#             (WS_URLS.app_권한, AppAuthorityHandler),
#             (WS_URLS.ping, PingHandler),
#             (WS_URLS.active_users, UsersHandler),
#             (WS_URLS.table_total_config, TableTotalConfigHandler),
#             (WS_URLS.resources, ResourcesHandler),
#             (WS_URLS.WS_공지사항, GongiHandler),
#             # (WS_URLS.server_monitor, ServerMonitorHandler),
#             # (WS_URLS.network_monitor, NetworkMonitorHandler),
#         ]
#         self.initialize_workers()
        
#         INFO.WS_TASKS[WS_URLS.WS_원격조정] = Pyro5Handler(WS_URLS.WS_원격조정)
#         # self.loop = asyncio.get_event_loop()
#         # if not self.loop.is_running():
#         #     self.loop.run_until_complete(self.initialize_workers())

#     # async def initialize_workers(self):
#     #     # 핸들러 객체 생성
#     #     for url, handler in self.url_tasks:
#     #         handler_instance = handler(url)
        
#     #     # 웹소켓 초기화 작업
#     #     for url, handler in self.url_tasks:
#     #         ws_async_worker = WS_Thread_AsyncWorker(url)
#     #         ws_async_worker.start()

#     def initialize_workers(self):
#         # 핸들러 객체 생성
#         for url, handler in self.url_tasks:
#             handler_instance = handler(url)

#         # 웹소켓 초기화 작업
#         for url, handler in self.url_tasks:			
#             ws_async_worker = WS_Thread_AsyncWorker(url)
#             INFO.WS_TASKS[url] = ws_async_worker
#             ws_async_worker.start()


class WS_Manager_by_each:
	def __init__(self, url:str, handler:Any):
		self.url = url
		self.handler = handler
		
		self.ws_async_worker = WS_Thread_AsyncWorker(self.url)
		INFO.WS_TASKS[self.url] = self.ws_async_worker	
		self.ws_async_worker.start()
          
		self.handler_instance = handler(self.url)

    # def add_url(self, url: str, max_retry=None, retry_delay=3):
    #     """새 URL에 대한 연결 시작"""
    #     if url not in INFO.URL_TASKS:
    #         worker = WS_AsyncWorker(url, max_retry, retry_delay)
    #         INFO.URL_TASKS[url] = worker
    #         worker.start()  # 작업 시작
    #         logger.info(f"[Manager] URL Added: {url}")
    #     else:
    #         logger.info(f"[Manager] URL already exists: {url}")

    # def remove_url(self, url: str):
    #     """URL 연결 종료"""
    #     worker = self.workers.pop(url, None)
    #     if worker:
    #         worker.stop()
    #         logger.info(f"[Manager] URL Removed: {url}")
    #     else:
    #         logger.info(f"[Manager] URL not found: {url}")

    # def stop_all(self):
    #     """모든 연결 종료"""
    #     for url, worker in self.workers.items():
    #         worker.stop()
    #     self.workers.clear()
    #     logger.info("[Manager] All URLs Removed")

# class Main_WS_Manager:
# 	""" composion pattern 적용 . not MRO """


# 	def __init__(self, handler:Optional[QMainWindow]):
# 		self.handler = handler  # main 클래스의 참조
# 		self.ws_thread = None
# 		self.ws_urls = None
# 		self.ws_thread_by_url = {}

# 		self.register_sub_handlers()


# 	def register_sub_handlers(self):
# 		""" 서브 핸들러 등록 """
# 		# URL과 핸들러 클래스 매핑 (동적 관리 가능)
# 		self.sub_handlers = {
# 			WS_URLS.get('app_권한'): AppAuthorityHandler,
# 			WS_URLS.get('ping'): PingHandler,
# 			WS_URLS.get('active_users'): UsersHandler,
# 			WS_URLS.get('table_total_config'): TableTotalConfigHandler,
# 			WS_URLS.get('resources'): ResourcesHandler,
# 			WS_URLS.get('server_monitor'): ServerMonitorHandler,
# 			WS_URLS.get('network_monitor'): NetworkMonitorHandler,
# 		}

# 	def register_sub_handler( self, url:str, handler:Any, parent:None):
# 		self.sub_handlers[url] = handler
# 		self.ws_thread_by_url[url] = WS_Thread_AsyncWorker(urls=[url], parent=parent)
# 		self.ws_thread_by_url[url].received.connect(lambda url, msg: self.ws_on_message(url, msg))
# 		self.ws_thread_by_url[url].error.connect(lambda url, e: self.ws_on_error(url, e))
# 		self.ws_thread_by_url[url].start()

# 	def close_by_url(self, url:str):
# 		if url in self.ws_thread_by_url:
# 			try:
# 				self.ws_thread_by_url[url].close()
# 				del self.ws_thread_by_url[url]

# 			except Exception as e:
# 				logger.error(f"close_by_url: {e}")

                  
# 	def close(self):
# 		"""
# 		웹소켓 연결을 안전하게 종료합니다.
# 		"""
# 		try:
# 			if hasattr(self, 'ws_thread') and self.ws_thread is not None:
# 				# 웹소켓 스레드의 close 메서드 호출 (내부 리소스 정리)
# 				self.ws_thread.close()
# 				# 스레드가 완전히 종료될 때까지 대기
# 				self.ws_thread.wait()
# 				self.ws_thread = None

# 		except Exception as e:
# 			logger.error(f"웹소켓 종료 오류: {e}")
# 			logger.error(f"{traceback.format_exc()}")


# 	# WebSocket 관련 메서드들을 제거하고 ws_manager를 통해 처리
# 	def enable_ws(self):
# 		"""
# 			Async WebSocket 관리자 초기화			
# 		"""
# 		logger.info(f"enable_ws: {WS_URLS.WS_MAIN_URLS}")
# 		self.ws_urls = [ INFO.URI_WS+ url for url in WS_URLS.WS_MAIN_URLS ]
# 		# Async WebSocket 관리자 초기화
# 		self.ws_thread = WS_Thread_AsyncWorker(urls=self.ws_urls, parent=self.handler)
# 		self.ws_thread.received.connect(lambda url, msg: self.ws_on_message(url, msg))
# 		# self.ws_thread.reconnected.connect(self.handle_ws_status_changed)
# 		self.ws_thread.error.connect(lambda url, e: self.ws_on_error(url, e))
# 		self.ws_thread.start()

# 		self.event_bus = event_bus

# 	def add_ws_url(self, new_url: str, handler:Any):
# 		"""
# 		Add a new WebSocket URL dynamically.
# 		"""
# 		self.ws_thread.add_url(new_url)
# 		self.ws_thread.received.connect(lambda url, msg: self.ws_on_message(url, msg))
# 		self.ws_thread.error.connect(lambda url, e: self.ws_on_error(url, e))

# 	def remove_ws_url(self, url_to_remove: str):
# 		"""
# 		Remove a WebSocket URL dynamically.
# 		"""
# 		self.ws_thread.remove_url(url_to_remove)


# 	def ws_on_message(self, url:str, msg:dict): 
# 		""" 웹소켓 메시지 수신 핸들러
# 			url별로 분류, 분개 시켜 각자 handling 하도록 함.
# 			msg 는 {"type": "broadcast", "sender": "system", "id": 168, "message": "saving message", "send_time": "2024-12-19T14:29:21"}
			
# 		 """
# 		self.event_bus.publish(GBus.WS_STATUS , True)
# 		# if msg.get('type') != 'ping' :
# 		# 	logger.info(f"ws_on_message: {url} {msg.get('type')}")

# 		_split = [ elm for elm in url.split('/') if elm ]
# 		conversion_url = _split[-2] + '/' + _split[-1] +'/'

# 		if isinstance(msg, dict):
# 			copyed_msg = copy.deepcopy(msg)
# 			subject = msg.get('subject')

# 			handler = self.sub_handlers.get(conversion_url, None )
# 			if handler:
# 				handler.handle(copyed_msg)
# 			else:
# 				logger.error( f" : ws_on_message : {conversion_url} 핸들러 없음")
			
# 		else:
# 			pass


# 	def ws_on_error(self, url:str, e:dict):
# 		"""
# 			WS 오류 발생 핸들러
# 		"""
# 		try:
# 			self.event_bus.publish(GBus.WS_STATUS, False)

# 		except Exception as e:
# 			logger.error(f"WS 오류 발생 오류: {e}")
# 			logger.error(f"{traceback.format_exc()}")

	# @pyqtSlot(dict)
	# def slot_ws_sales_order_amount_changed(self, msg:dict):		
	# 	"""영업수주 금액 변경 메시지 처리"""
	# 	app_ids = msg.get('app_ids')

	# 	sub_type = msg.get('sub_type')

	# 	match sub_type:
	# 		case "영업수주_금액_DB_변경_자재내역_의장_변경":
	# 			message = json.loads(msg.get('message'))
	# 			no_의장_fk = [ obj for obj in message if obj.get('의장_fk') is None ]
	# 			utils.generate_QMsg_Information(self, text= f" 의장 미확정 {len(no_의장_fk)}건 / {len(message)}건 중", title='영업수주 금액 변경', autoClose=2000)

	# 			for app_id in app_ids:
	# 				key = utils.get_Obj_From_ListDict_by_subDict(self.app권한, {'id': int(app_id)}).get('표시명_구분')

	# 				if key in self.tabs:
	# 					tabWidget = self.tabs[key]
	# 					tabObj = tabWidget.findChild(QWidget, f'appid_{app_id}')
	# 					if tabObj :
	# 						if hasattr(tabObj, 'app') and tabObj.app:
	# 							if hasattr(tabObj.app, '자재내역_to_의장_Datas'):
	# 								tabObj.app._render_PB_Mapping(message)
	# 							if hasattr(tabObj.app, 'dlg_자재내역_to_의장') and (dlg := tabObj.app.dlg_자재내역_to_의장):
	# 								try :	


	# 									dlg.wid_table._update_data(api_data=message)										
	# 								except Exception as e:



	# @pyqtSlot(dict)
	# def slot_ws_appChanged(self, msg:dict):
	# 	"""
	# 		msg 는 {"type": "broadcast", "sender": "system", "id": 168, "message": "saving message", "send_time": "2024-12-19T14:29:21"}
	# 	"""
	# 	changed_app권한_dict =json.loads(msg.get('message'))
	# 	if not isinstance(changed_app권한_dict, dict):
	# 		return 
	# 	import copy
	# 	self.prev_app권한 = copy.deepcopy(self.app권한)

	# 	기존app권한dict = utils.get_Obj_From_ListDict_by_subDict(self.app권한, {'id': changed_app권한_dict.get('id')}) 

	# 	### 개발 모드는 skip
	# 	if changed_app권한_dict.get('is_dev') and  INFO.USERID != 1:
	# 		self.handle_개발자모드(changed_app권한_dict)
	# 		return


	# 	### app 자체가 삭제 : is_Active = False
	# 	if not changed_app권한_dict.get('is_Active'):
	# 		try :
	# 			self.app권한.remove(기존app권한dict)
	# 			self._update_toolbar()
	# 			self._update_tabs(changed_app권한_dict, 'remove')
	# 		except Exception as e:

	# 		return

	# 	if 기존app권한dict:
	# 		#### 기존 app권한에서 클라이언트가 삭제된 경우
	# 		if INFO.USERID in changed_app권한_dict.get('user_pks', []):
	# 			### 변경 or 변경사항 없음
	# 			changes_dict = self.check_specific_changes(기존app권한dict, changed_app권한_dict)
	# 			if changes_dict:
	# 				idx = self.app권한.index(기존app권한dict)
	# 				self.app권한[idx] = changed_app권한_dict
	# 				if 'is_Active' in changes_dict and not changes_dict.get('is_Active'):
	# 					#### 삭제된 경우
	# 					self.app권한.remove(기존app권한dict)
	# 					self._update_tabs(changed_app권한_dict, _type='remove')
						
	# 				else:
	# 					self._update_tabs(changed_app권한_dict, _type='change', changes_dict = changes_dict)

	# 			else:
	# 				return ###  변경사항 없음				
				
	# 		else:
	# 			### user가 삭제됨
	# 			self.app권한.remove(기존app권한dict)
	# 			self._update_tabs(changed_app권한_dict, _type='remove')

	# 	#### 기존 app권한에서 클라이언트가 추가된 경우
	# 	if not 기존app권한dict:
	# 		if INFO.USERID in changed_app권한_dict.get('user_pks', []):

	# 			self.app권한.append(changed_app권한_dict)
	# 			self.app권한.sort(key=lambda x: x.get('순서'))
	# 			self._update_tabs(changed_app권한_dict, _type='add')
	# 		else:
	# 			return            #### 해당사항 없음
			
	# 	self._update_toolbar()

	# # 