from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING, Protocol
from modules.global_event_bus import event_bus
import json, time, copy

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker

from info import Info_SW as INFO
import modules.user.utils as Utils

if TYPE_CHECKING:
    from main import MainWindow, Ui_MainWindow  # 순환 임포트 방지

from core.interfaces import Main_WS_Manager_Interface



class Main_WS_Manager_Interface(Protocol):
    """MainWindow와 Main_WS_Manager 간의 인터페이스 정의"""
    uiMainW: 'Ui_MainWindow'  # 구체적인 타입 지정
    
    def set_status_WS(self, status: bool, blink_interval: int = 0) -> None:
        """WebSocket 상태를 설정하는 메서드"""
        pass


class Main_WS_Manager:
	""" composion pattern 적용 . not MRO """


	def __init__(self, handler:Optional[QMainWindow]):
		self.handler = handler  # main 클래스의 참조
		self.ws_thread = None
		self.ws_urls = None

	
	def close(self):
		"""
		웹소켓 연결을 안전하게 종료합니다.
		"""
		try:

			if hasattr(self, 'ws_thread') and self.ws_thread is not None:
				# 웹소켓 스레드의 close 메서드 호출 (내부 리소스 정리)
				self.ws_thread.close()
				# 스레드가 완전히 종료될 때까지 대기
				self.ws_thread.wait()
				self.ws_thread = None

		except Exception as e:
			logger.error(f"웹소켓 종료 오류: {e}")
			logger.error(f"{traceback.format_exc()}")


	# WebSocket 관련 메서드들을 제거하고 ws_manager를 통해 처리
	def enable_ws(self):
		"""
			Async WebSocket 관리자 초기화			
		"""
		logger.info(f"enable_ws: {INFO.WS_MAIN_URLS}")
		self.ws_urls = [ INFO.URI_WS+ url for url in INFO.WS_MAIN_URLS ]
		# Async WebSocket 관리자 초기화
		self.ws_thread = WS_Thread_AsyncWorker(urls=self.ws_urls, parent=self.handler)
		self.ws_thread.received.connect(lambda url, msg: self.ws_on_message(url, msg))
		# self.ws_thread.reconnected.connect(self.handle_ws_status_changed)
		self.ws_thread.error.connect(lambda url, e: self.ws_on_error(url, e))
		self.ws_thread.start()

		self.event_bus = event_bus


	def ws_on_message(self, url:str, msg:dict): 
		""" 웹소켓 메시지 수신 핸들러
			url별로 분류, 분개 시켜 각자 handling 하도록 함.
			msg 는 {"type": "broadcast", "sender": "system", "id": 168, "message": "saving message", "send_time": "2024-12-19T14:29:21"}
			
		 """
		self.event_bus.publish(INFO.EVENT_BUS_TYPE_WS_STATUS, True)
		if msg.get('type') != 'ping'  :logger.info(f"ws_on_message: {url}")
		
		if isinstance(msg, dict):
			subject = msg.get('subject')
			match subject:
				case 'app_authority' | 'app_authority_changed':	
					app권한:list[dict] = msg.get('message')

					logger.info(f"app권한 : subject = {subject}")
					# self.handler.set_app권한( self.get_app권한_from_ws(app권한) )
					# self.handler.render_menu()
					### bakcground 처리
					if subject == 'app_authority':
						depapp = copy.deepcopy(app권한)
						logger.info(f"depapp : {len(depapp)}")
						send_app권한 = self.get_app권한_from_ws(depapp)
						logger.info(f"send_app권한 : {len(send_app권한)}")
						self.event_bus.publish(
							'broadcast:app_initialized', 
							send_app권한)
						self.handler.run_table_config_worker()
					elif subject == 'app_authority_changed':
						pass

				case 'users_active':
					users_active:list[dict] = msg.get('message')
					self.handler.set_users_active( users_active )

				
				case 'gongji':
					공자사항:list[dict] = msg.get('message')
					pass

				case _:
					### 디버깅 용도
					if msg.get('type') == 'ping'  : return 
					logger.info(f"웹소켓 메시지 Default : url {url} :  Subject: {msg}")

			# if msg.get('subject') :
			# 	Utils.generate_QMsg_Information( 
			# 		INFO.MAIN_WINDOW, 
			# 		title=f"WS 메시지 수신 : {url}", 
			# 		text=f"메시지 : {msg.get('subject')}", 
			# 		autoClose=1000
			# 	)			
		else:
			pass


	def ws_on_error(self, url:str, e:dict):
		"""
			WS 오류 발생 핸들러
		"""
		try:
			self.event_bus.publish(INFO.EVENT_BUS_TYPE_WS_STATUS, False)
			# Utils.generate_QMsg_Information( 
			# 	self.handler, 
			# 	title=f"WS 오류 발생 : {url}", 
			# 	text=f"오류 : {e}", 
			# 	autoClose=1000
			# )
		except Exception as e:
			logger.error(f"WS 오류 발생 오류: {e}")
			logger.error(f"{traceback.format_exc()}")


	# def handle_ws_status_changed(self, is_connected, blink_interval):
	# 	"""WebSocketManager에서 전달된 연결 상태와 깜빡임 간격을 처리합니다."""
	# 	if is_connected:
	# 		if blink_interval > 0:
	# 			# 일부 연결됨 - 깜빡이는 효과 (녹색과 검은색 사이)
	# 			self.handler.set_status_WS(True, blink_interval)
	# 			# blink_interval 후에 다시 idle로 설정하지 않고, 깜빡임 효과를 위해 타이머 설정
	# 			# QTimer.singleShot(blink_interval, lambda: self.handler.set_status_WS('idle'))
	# 		else:
	# 			# 모두 연결됨 - 녹색으로 유지
	# 			self.handler.set_status_WS(True)  # 0은 타이머 없음을 의미
	# 	else:
	# 		# 모두 연결 끊김 - 빨간색으로 유지
	# 		self.handler.set_status_WS(False)  # 타이머 없이 계속 빨간색 유지

	def get_app권한_from_ws(self, app권한:list[dict]):
		"""
			app권한 목록을 받아서 처리
		"""

		logger.info(f"info.userid : {INFO.USERID}, app권한 : {len(app권한)}")
		if not app권한:
			return []
		owner_app권한 = [ obj for obj in app권한 if INFO.USERID in obj.get('user_pks') ]
		if INFO.IS_DEV:
			pass
		
		else:
			owner_app권한 = [ obj for obj in owner_app권한 if  obj.get('is_Actvie') and obj.get('is_dev') == False ]

		return owner_app권한

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