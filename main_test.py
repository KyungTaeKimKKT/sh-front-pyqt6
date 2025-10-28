from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import sys, traceback, os, logging
from copy import deepcopy
from modules.logging_config import configure_app_logging, setup_exception_handlers
import db_setting  # Django 설정 초기화
from PyQt6 import QtCore, QtGui, QtWidgets, QtPrintSupport, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebEngineCore import *


import asyncio
import qasync
import pandas as pd

from datetime import date, datetime
import subprocess
from collections import deque
import ffmpeg

# from modules.PyQt.ui.Ui_toolbar import Ui_Toolbar

### 플러그인 모듈
from modules.global_event_bus import event_bus
from modules.utils.api_fetch_worker import Api_Fetch_Worker
from plugin_main.timer_handler import Timer_Handler

from plugin_main import logging_loki as loki
from plugin_main.dialog.trace_gbus_dialog import MessageTraceView_Dialog
from plugin_main.dialog.trace_time_dialog import TimeTraceView_Dialog
from plugin_main.dialog.trace_logger_dialog import LoggerTraceView_Dialog

# from modules.PyQt.dialog.loading.dlg_loading import LoadingDialog
from modules.PyQt.Qthreads.screenrecorder import ScreenRecorder

from plugin_main.win_login import Login, Face_Recognition_Login
from plugin_main.preload_app import AppPreloader
from plugin_main.local_pc_resource import Local_PC_Resource
from plugin_main.api_server_check import Api_Server_Check
from plugin_main.dialog.loading_dialog import LoadingDialog


# from modules.PyQt.ui.Ui_login import Login
# from modules.PyQt.sub_window.win_login import Login

from modules.PyQt.User.toast import User_Toast

### SingleTone (보통 설정) 
from config import Config as APP
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

# from Ui_main_circular_bar_v1 import Ui_MainWindow_byDesigner
from stylesheet import StyleSheet

import importlib
import modules.user.utils as utils
import modules.user.utils as Utils
from update import Update

import json

from info import Info_SW as INFO
from stylesheet import StyleSheet

ST = StyleSheet()

# 프로젝트 최상위 경로를 전역 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INFO.set_base_dir(BASE_DIR)


#### crash용 파일 생성
CRASH_VIDEO_FILE = 'crash_video.mp4'
# 예외 처리기 설정
setup_exception_handlers()


import traceback


from plugin_main.ui.toolbar_manager import ToolbarManager
from plugin_main.ui.menu_manager import MenuManager
from plugin_main.ui.statusbar_manager import StatusBarManager
from plugin_main.ui.tab_manager import TabManager

from modules.PyQt.Tabs.home.wid_home import HomeDashboardWidget

from plugin_main.websocket.ws_msg_handler import WS_Message_Handler

# ws_client_qasync.py
import asyncio, json, contextlib
from PyQt6.QtCore import QObject, pyqtSignal
import websockets
from qasync import asyncSlot

class WSClient(QObject):
	message = pyqtSignal(str, dict)          # (url, data)
	connection_changed = pyqtSignal(str, bool)  # (url, connected)
	error = pyqtSignal(str, str)             # (url, err)

	def __init__(self, url: str, *,
					connect_msg: dict | None = None,
					retry_delay: float = 3.0,
					max_retry: int = -1,           # -1: 무제한
					ws_base: str = "",
					parent=None):
		super().__init__(parent)
		self.url = url
		self.ws_base = ws_base  # 예: INFO.URI_WS
		self.connect_msg = connect_msg
		self.retry_delay = retry_delay
		self.max_retry = max_retry

		self._ws = None
		self._closing = False
		self._runner_task: asyncio.Task | None = None
		self._writer_task: asyncio.Task | None = None
		self._send_q: asyncio.Queue[str] = asyncio.Queue()

		self._latest_message = {}



	async def start(self):
		"""이벤트 루프에서 호출: 연결 루프 시작"""
		if self._runner_task and not self._runner_task.done():
			return
		self._closing = False
		self._runner_task = asyncio.create_task(self._run())

	async def stop(self):
		"""이벤트 루프에서 호출: 정상 종료"""
		self._closing = True
		if self._writer_task:
			self._writer_task.cancel()
			with contextlib.suppress(asyncio.CancelledError):
				await self._writer_task
			self._writer_task = None

		if self._ws and not self._ws.closed:
			with contextlib.suppress(Exception):
				await self._ws.close()
		self._ws = None

		if self._runner_task:
			self._runner_task.cancel()
			with contextlib.suppress(asyncio.CancelledError):
				await self._runner_task
			self._runner_task = None

	async def _run(self):
		retries = 0
		full_url = f"{self.ws_base}{self.url}"

		while not self._closing and (self.max_retry < 0 or retries < self.max_retry):
			try:
				async with websockets.connect(
					full_url,
					ping_interval=20,
					ping_timeout=10
				) as ws:
					self._ws = ws
					retries = 0
					self.connection_changed.emit(self.url, True)

					# 초기 메시지
					if self.connect_msg:
						await ws.send(json.dumps(self.connect_msg, ensure_ascii=False))

					# writer Task 안전하게 생성
					if self._writer_task is None or self._writer_task.done():
						self._writer_task = asyncio.create_task(self._writer())

					try:
						async for msg in ws:
							try:
								data = json.loads(msg)
							except Exception:
								data = {"raw": msg}
							self._latest_message = data
							# emit을 안전하게 task로 실행
							asyncio.create_task(self._emit_message_safe(data))

					except websockets.ConnectionClosed as e:
						# 서버에서 연결 끊겼을 때
						self.connection_changed.emit(self.url, False)
						loki.warning(f"WebSocket connection closed: {e}")
						retries += 1
						await asyncio.sleep(self.retry_delay)

			except Exception as e:
				# 서버 죽음, 네트워크 문제 등
				self.error.emit(self.url, str(e))
				self.connection_changed.emit(self.url, False)
				self._ws = None

				if self._writer_task:
					self._writer_task.cancel()
					with contextlib.suppress(asyncio.CancelledError):
						await self._writer_task
					self._writer_task = None

				if self._closing:
					break
				retries += 1
				await asyncio.sleep(self.retry_delay)

		# 최대 재시도 초과
		if self.max_retry >= 0 and retries >= self.max_retry:
			self.error.emit(self.url, f"max_retry {self.max_retry} exceeded")

	async def _emit_message_safe(self, data):
		# PyQt 시그널 emit을 즉시 이벤트 큐에 넣어 호출되도록 qasync.loop.call_soon_threadsafe 사용
		loop = asyncio.get_running_loop()
		loop.call_soon_threadsafe(self.message.emit, self.url, data)

	async def _writer(self):
		while True:
			payload = await self._send_q.get()
			if self._ws is None or self._ws.closed:
				continue
			await self._ws.send(payload)

	@asyncSlot(dict)
	async def send(self, message: dict):
		"""Qt 슬롯에서 바로 호출 가능"""
		await self._send_q.put(json.dumps(message, ensure_ascii=False))

	def send_message(self, message: dict):
		"""기존 코드 호환용 (동기처럼 호출 가능)"""
		asyncio.ensure_future(self.send(message))

	def get_latest_msg(self):
		return self._latest_message


# ws_client_qasync.py
class WSManager(QObject):
	message = pyqtSignal(str, dict)
	connection_changed = pyqtSignal(str, bool)
	error = pyqtSignal(str, str)

	def __init__(self, ws_base: str, parent=None):
		super().__init__(parent)
		self.ws_base = ws_base
		self.clients: dict[str, WSClient] = {}
		self.pending = []

	def add(self, url: str, *, connect_msg: dict | None = None, message_slot_func: callable | None = None, error_slot_func: callable | None = None):
		if url in self.clients:
			return self.clients[url]
		c = WSClient(url, ws_base=self.ws_base, connect_msg=connect_msg)
		print (f"c : {c}")
		print (f"message_slot_func : {message_slot_func}{callable(message_slot_func)}")
		print (f"error_slot_func : {error_slot_func}{callable(error_slot_func)}")
		c.message.connect(self.message if message_slot_func is None else message_slot_func)
		c.connection_changed.connect(self.connection_changed)
		c.error.connect(self.error if error_slot_func is None else error_slot_func)
		self.clients[url] = c

		# ✅ 기존 코드 호환용 (INFO.WS_TASKS에도 등록)
		INFO.WS_TASKS[url] = c
		try:
			loop = asyncio.get_running_loop()
			loop.create_task(c.start())
		except RuntimeError:
			print (f"RuntimeError: {url}")
			# 아직 loop 없음 → pending 에 넣기
			self.pending.append(c)
		return c

	async def start_all(self):
		await asyncio.gather(*(c.start() for c in self.clients.values()))
		# pending 비우기
		self.pending.clear()

	async def stop_all(self):
		await asyncio.gather(*(c.stop() for c in self.clients.values()))

	def remove(self, url: str):
		if url in self.clients:
			self.clients[url].stop()
			del self.clients[url]
			del INFO.WS_TASKS[url]


from modules.mixin.recording_mixin import RecordingMixin
class MainWindow(QtWidgets.QMainWindow ):
	def __init__(self):
		super().__init__()
		#### 로그인은 초기화에 선언
		self.event_bus = event_bus
		self.event_bus.subscribe(GBus.LOGIN, self.handle_Login)
		self.event_bus.subscribe(GBus.LOGIN, self.render_title)

		### attribute 설정
		self.app권한 :list[dict] = []
		self._is_WS_status_setting = False
		self._is_WS_RETRYING = False
		# self._init_toolbar_setting_attribute()
		self.processed_urls = set()
		self.processing_urls_targets = [] 
		self.dlg_loading = None   # 로딩중 다이얼로그
		# self.uiMainW =  Ui_MainWindow( self)
		# self.uiMainW.MainWindow = self
		# self.uiMainW.setupUi(self)

		self.cpuAlarmCount = 0
		self.tabs:dict[str, QTabWidget] = {}	### 표시명_구분 : QtWidgets.QTabWidget
		self.curTabs : QTabWidget|None = None
		self.cur_appDict : dict|None = None

		self.debug_recording_fps = 10
		self.debug_recording_size = (1600, 1200)
		self.debug_recording_path = os.path.join(utils.makeDir("debug"), CRASH_VIDEO_FILE)
		self.debug_recording_method = 'ffmpeg'
		self.debug_recording_max_duration = 30 ### 초단위
		self.debug_recording_max_frames = deque (maxlen=self.debug_recording_fps * self.debug_recording_max_duration)
		self._ffmpeg_path = utils.get_ffmpeg_path()
		
		### 관계형. (composition 주입형 handler)
		# self.slot_handler = Main_Slot_Handler(self)
		
		INFO.MAIN_WINDOW = self

		self.ws_message_handler = WS_Message_Handler()

		# self.uiMainW.run()

		if INFO.IS_DEV:
			self.trace_gbus_dialog = MessageTraceView_Dialog(self)
			self.trace_time_dialog = TimeTraceView_Dialog(self)
			self.trace_logger_dialog = LoggerTraceView_Dialog(self)
			self.trace_gbus_dialog.show()
			self.trace_time_dialog.show()
			self.trace_logger_dialog.show()

		self.handle_Login(True)

	def UI(self):
		self.setObjectName("MainWindow")
		self.resize(1700, 1150)
		self.setMinimumSize(QSize(1200, 800))
		self.centralwidget = QWidget(self)
		self.centralwidget.setObjectName("centralwidget")

		self.setCentralWidget(self.centralwidget)

		self.vLayout_Main = QVBoxLayout(self.centralwidget)
		self.vLayout_Main.setObjectName("vLayout_Main")

		self.vLayout_Main.addWidget(self.create_home_widget())
		
		# 윈도우 타이틀과 아이콘 설정
		# self.__render_Window_Title_Icon()

		self.menubar = QMenuBar(self)
		self.setMenuBar(self.menubar)

		# self.toolbar = QToolBar(self)
		# self.addToolBar(self.toolbar)
		
        # 컴포넌트 관리자 초기화
		self.menu_manager = MenuManager(self.menubar)
		self.toolbar_manager = ToolbarManager(self)
		self.statusbar_manager = StatusBarManager(self)
		self.tab_manager = TabManager(self)

		# 상태바 렌더링
		# self.statusbar = self.statusbar_manager.render_statusbar()
		# # 상태바를 메인 윈도우에 설정
		# self.MainWindow.setStatusBar(self.statusbar)

	def create_home_widget(self) -> QWidget:
		self.home_widget = HomeDashboardWidget(self)
		print(f"self.home_widget : {self.home_widget}")
		return self.home_widget



	def init_recording_by_timer(self):
		self.timer_recording = QTimer()
		self.timer_recording.timeout.connect(self.update_frames)
		self.timer_recording.start( int(1000 / self.debug_recording_fps) )

	def update_frames(self):
		self.debug_recording_max_frames.append(self.capture_mainWindow())

	def save_recording(self):
		def normalize_frames_by_largest(frames: list[QPixmap]) -> tuple[list[QPixmap], int, int]:
			# 가장 큰 해상도 기준
			max_w = max(f.width() for f in frames)
			max_h = max(f.height() for f in frames)
			target_size = QSize(max_w, max_h)

			result_frames = []
			for f in frames:
				if f.size() == target_size:
					result_frames.append(f)
				else:
					padded = QPixmap(target_size)
					padded.fill(Qt.GlobalColor.black)  # 또는 white

					painter = QPainter(padded)
					painter.drawPixmap(0, 0, f)  # 좌측 상단에 원본 유지
					painter.end()

					result_frames.append(padded)

			return result_frames, max_w, max_h

		frames = self.debug_recording_max_frames		
		if not frames:
			loki.warning("녹화된 프레임이 없습니다.")
			return
		
		target_frames, w, h = normalize_frames_by_largest(frames)
		process = (
			ffmpeg
			.input('pipe:', format='rawvideo', pix_fmt='rgb24', s=f'{w}x{h}', framerate=self.debug_recording_fps)
			.output(self.debug_recording_path, pix_fmt='yuv420p', vcodec='libx264', crf=23)
			.overwrite_output()
			.run_async(pipe_stdin=True, cmd=self._ffmpeg_path if self._ffmpeg_path else None)
		)
		for frame in target_frames:
			try:
				pil_img = utils.pixmap_to_pil(frame)
				process.stdin.write(pil_img.tobytes())
			except Exception as e:
				loki.warning(f"프레임 변환 중 오류 발생: {e}")
				continue
		process.stdin.close()
		process.wait()

	def send_app_access_log(self, status:str):
		if INFO.get_is_send_app_access_log():
			ws  = INFO.WS_TASKS.get(INFO.get_WS_URL_by_name('client_app_access_log'))
			if ws:  
				ws.send_message( { 'status': status, 
								'user_id': INFO.USERID, 
								'app_fk_id' : -1 } )
				print (f"send_app_access_log : ws{ws} ==> status : {status}")
			else:
				loki.error(f"ws: {ws} 없음")

	def closeEvent(self, event):
		"""
		애플리케이션이 종료될 때 실행 중인 모든 스레드를 정리합니다.
		"""
		try:
			self.send_app_access_log('logout')

			# 진행 상황 다이얼로그 표시
			progress_dialog = QProgressDialog("애플리케이션 종료 중...(잠시 기다려주세요)", None, 0, 100, self)
			progress_dialog.setWindowTitle("종료 진행 상황")
			progress_dialog.setWindowModality(Qt.WindowModal)
			progress_dialog.setCancelButton(None)  # 취소 버튼 제거
			progress_dialog.setMinimumDuration(0)  # 즉시 표시되도록 설정
			progress_dialog.setAutoClose(False)    # 자동으로 닫히지 않도록 설정
			progress_dialog.show()
			QApplication.processEvents()  # UI 업데이트 처리
			
			# 진행 상황 업데이트 함수
			def update_progress(value, text):
				progress_dialog.setValue(value)
				progress_dialog.setLabelText(text)
				QApplication.processEvents()  # UI 업데이트 처리
			
			update_progress(10, "로컬 PC 리소스 정리 중...")
			if hasattr(self, 'local_pc_resource'):
				self.local_pc_resource.close()
			
			# 약간의 지연 추가
			QThread.msleep(100)
			
			update_progress(20, "로컬 PC 리소스 정리 중...")
			# 스크린 레코더 정리
			if hasattr(self, 'screen_recorder') and self.screen_recorder is not None:
				self.screen_recorder.stop()
				self.screen_recorder.wait()
			
			QThread.msleep(100)
			
			update_progress(30, "데이터 스레드 정리 중...")
			# DataFetchThread 정리
			if getattr(self, 'threads', None):
				for thread in self.threads:
					if thread.isRunning():
						thread.quit()
						thread.wait()

			QThread.msleep(100)
			
			update_progress(40, "타이머 정리 중...")
			# 타이머 정리
			if getattr(self, 'Minute_timer', None):
				self.Minute_timer.stop()

			if getattr(self, 'Sec_10_Timer', None):
				self.Sec_10_Timer.stop()

			QThread.msleep(100)
			

			QThread.msleep(100)
			
			update_progress(70, "웹소켓 매니저 정리 중...")
			# 웹소켓 정리
			for url, task in INFO.WS_TASKS.items():
				if task is not None:
					task.stop()


			QThread.msleep(100)

			update_progress(80, "event_bus 정리 중...")				
			event_bus.clear()
			
			update_progress(90, "앱 정리 중...")
			# 현재 열려있는 모든 탭의 앱 정리
			for key, tab_widget in self.tabs.items():    
				for i in range(tab_widget.count()):
					tab = tab_widget.widget(i)
					if hasattr(tab, 'app') and tab.app is not None:
						try:
							if not sip.isdeleted(tab.app):
								tab.app.deleteLater()
						except:
							pass


			QThread.msleep(100)
			
			update_progress(100, "종료 완료")
			progress_dialog.close()

		except Exception as e:
			logging.error(f"애플리케이션 종료 중 오류 발생: {e}")
			logging.error(f"상세 오류: {traceback.format_exc()}")
		
		# 재시작 플래그가 설정되어 있지 않으면 이벤트 수락
		event.accept()

	def subscribe_gbus(self):
		return 
		### System  메뉴 중  restart_application_requested 이벤트 만, 구독
		self.event_bus.subscribe(GBus.CPU_RAM_MONITOR, self.statusbar_manager.set_cpu_ram_status)
		self.event_bus.subscribe(GBus.WS_STATUS, self.statusbar_manager.set_status_WS)
		self.event_bus.subscribe(GBus.API_STATUS, self.statusbar_manager.set_status_API)

	def test_ws_without_qthread(self):
		self.ws = WSManager(ws_base= INFO.URI_WS)

		APP.set_WS_manager(self.ws)

		self.WS_urls  = [
			INFO.get_WS_URL_by_name('app_권한'), 
			INFO.get_WS_URL_by_name('ping'), 
			INFO.get_WS_URL_by_name('active_users'), 
            INFO.get_WS_URL_by_name('table_total_config'), 
			INFO.get_WS_URL_by_name('resource'),
			INFO.get_WS_URL_by_name('공지사항'), 
			INFO.get_WS_URL_by_name('client_app_access_log'),
            INFO.get_WS_URL_by_name('client_app_access_dashboard'),
        ]
		default_connect_msg = {
					"action": "init_request",		#### 25-7 초기 연결 요청 : init ==> init_request로 변경
					"user_id": INFO.USERID,
					"timestamp": datetime.now().isoformat()
				}
		map_url_to_connect_msg = {
			INFO.get_WS_URL_by_name('client_app_access_log'): 
			{ 'status': 'login', 
				'user_id': INFO.USERID, 
				'app_fk_id' : -1 }
		}

		for url in self.WS_urls:
			self.ws.add (url, connect_msg=map_url_to_connect_msg.get(url, default_connect_msg))

		self.ws.message.connect(self.on_message)
		self.ws.connection_changed.connect(self.on_conn)
		self.ws.error.connect(self.on_err)

	async def start_ws(self):
		await self.ws.start_all()

	async def stop_ws(self):
		await self.ws.stop_all()

	def on_message(self, url: str, data: dict):
		self.event_bus.publish(GBus.WS_STATUS , True)
		self.ws_message_handler:WS_Message_Handler = getattr( self, 'ws_message_handler', WS_Message_Handler() )
		self.ws_message_handler.on_message(url, data )


	def on_conn(self, url: str, ok: bool):
		print (f"[{url}] connected={ok}")
		# self.view.append(f"[{url}] connected={ok}")

	def on_err(self, url: str, err: str):
		print (f"[{url}] ERROR: {err}")
		# self.view.append(f"[{url}] ERROR: {err}")

	def closeEvent(self, e):
		# 종료 시 비동기 정리
		asyncio.create_task(self.stop_ws())
		super().closeEvent(e)

	def initialize_after_login(self):
		""" 로그인 후 초기화 함수 """

		self.test_ws_without_qthread()
		#### 1. ui 생성.
		self.UI()
		### 프로젝트 최상위 경로를 전역 설정
		INFO.set_base_dir(BASE_DIR)

		self.timer_handler = Timer_Handler(self)

		# from plugin_main.websocket.main_ws_init import  WS_InitManager_V3
		# self.ws_init_manager = WS_InitManager_V3()

		### 25-8-18 순서 변경 :  먼저 
		# from plugin_main.dialog.dlg_app_loading import Dialog_App_Loading
		# self.app_loading_dialog = Dialog_App_Loading(gif_path='./plugin_main/dialog/dlg_app_loading.gif')
		# # self.app_loading_dialog.exec()
		# self.app_loading_dialog.show()


		# self.test_ws_without_qthread()

		# self.app_preloader = AppPreloader()

		self.event_bus.publish('login_success', {'login_info': 'login_success'})

		self.subscribe_gbus()
		### local pc resource 초기화
		self.local_pc_resource = Local_PC_Resource(timer_interval=10000)
		self.local_pc_resource.start()

		### api server check 초기화, ws는 ws manger 에서 발행.
		self.api_server_check = Api_Server_Check()
		self.api_server_check.start()

		self.load_plugins()


		self.TriggerConnect()

		self.loading_dialog = LoadingDialog(self)
		APP.set_DLG_LOADING(self.loading_dialog)



	
	# def _render_Menu(self):
	# 	self.menubar = QtWidgets.QMenuBar(self )
	# 	# self.menubar.setGeometry(QtCore.QRect(0, 0, 1353, 28))
	# 	self.menubar.setObjectName("menubar")
		
	# 	#😀 appMenu : print_preview, print 
	# 	self.action_Print_preview = QAction( QIcon(':/app-menu-icons/print-preview'),
	# 								  'Print Preview', self )
	# 	self.action_Print_preview.setShortcut('Ctlr+P')
	# 	self.action_Print_preview.setStatusTip('현재 App화면을 프린트합니다.')

	# 	self.action_Print = QAction( QIcon(':/app-menu-icons/print'),
	# 								  'Print', self )
	# 	# self.action_print.setShortcut('Ctlr+P')
	# 	self.action_Print.setStatusTip('현재 App화면을 프린트합니다.')
		
	# 	appMenu = self.menubar.addMenu('&App')
	# 	appMenu.addAction(self.action_Print_preview)
	# 	appMenu.addAction(self.action_Print)



	# 	### 😀 setting menu
	# 	settings_menu = self.menubar.addMenu('Settings')
	# 	# 툴바 설정 서브메뉴 생성
	# 	toolbar_menu = settings_menu.addMenu('Toolbar Settings')
		
	# 	# 툴바 폰트 설정 액션
	# 	toolbar_font_action = QAction('Toolbar Font', self)
	# 	toolbar_font_action.triggered.connect(self.change_toolbar_font)
		
	# 	# 툴바 색상 설정 액션
	# 	toolbar_color_action = QAction('Toolbar Color', self)
	# 	toolbar_color_action.triggered.connect(self.change_toolbar_color)
		
	# 	# 툴바 배경색 설정 액션
	# 	toolbar_bg_action = QAction('Toolbar Background', self)
	# 	toolbar_bg_action.triggered.connect(self.change_toolbar_bg)
		
	# 	# 설정 저장 메뉴 추가
	# 	save_settings_action = QAction('Save Settings', self)
	# 	save_settings_action.triggered.connect(self.save_settings)
	# 	# 메뉴에 액션 추가
	# 	toolbar_menu.addAction(toolbar_font_action)
	# 	toolbar_menu.addAction(toolbar_color_action)
	# 	toolbar_menu.addAction(toolbar_bg_action)
	# 	settings_menu.addSeparator()
	# 	settings_menu.addAction(save_settings_action)

	# 	# 시스템 메뉴 추가 (맨 오른쪽에 위치)
	# 	system_menu = self.menubar.addMenu('System')
	# 	self.action_restart = QAction(QIcon(':/app-menu-icons/restart'), '앱 재시작', self)
	# 	self.action_restart.setStatusTip('애플리케이션을 재시작합니다.')
	# 	self.action_restart.triggered.connect(self.restart_application)
	# 	system_menu.addAction(self.action_restart)
		
	# 	self.setMenuBar(self.menubar)


	def load_plugins(self):		
		""" system menu manager, api_fetch_worker??, loading_dialog"""

		return 
		self.api_fetch_worker = Api_Fetch_Worker(self)
		self.loading_dialog = LoadingDialog(self)

	def show_loading_dialog(self, **kwargs):
		return 

	def TriggerConnect(self):
		return 
		self.action_Print_preview.triggered.connect(self.handle_print_preview)
		self.action_Print.triggered.connect(self.handle_print)

	# 앱 리로드를 위한 키보드 이벤트 핸들러 추가
	def keyPressEvent(self, event):
		# Ctrl+R 키 조합 감지
		if (event.key() == Qt.Key_R or  event.key() == Qt.Key_F5)  \
			and event.modifiers() == Qt.ControlModifier:
			if INFO.IS_DEV:
				print ('app reload sequence start:')
				removed = utils.clear_all_proj_modules()
				print(f"Removed {len(removed)} modules:")
				print(removed[:20])  # 처음 20개만 출력 
				### 공용 모듈 reload
				importlib.reload (utils)
				importlib.reload (Utils)
			### TAB MANAGER 에서 처리
			self.event_bus.publish(GBus.APP_RELOAD, True)
			# self.reload_current_app()
		elif event.key() == Qt.Key_G and event.modifiers() == Qt.ControlModifier and hasattr(self, 'trace_gbus_dialog'):
			self.trace_gbus_dialog.show()
			self.trace_time_dialog.show()

		else:
			super().keyPressEvent(event)


	# 애플리케이션 재시작 메서드 추가
	def restart_application(self, data:dict={}):
		"""애플리케이션을 재시작합니다."""
		try:
			# 현재 실행 중인 프로세스 정보 저장
			python_executable = sys.executable
			script_file = sys.argv[0]
			args = sys.argv[1:]
			
			# 사용자에게 재시작 확인 메시지 표시
			if utils.QMsg_question(self, title='애플리케이션 재시작', text='애플리케이션을 재시작하시겠습니까?<br>현재 실행중인 프로세스를 종료하고 재시작합니다.<br>'):
				# 재시작 플래그 설정 (새 프로세스 시작을 위한 정보 저장)
				self._restart_info = {
					'executable': python_executable,
					'script': script_file,
					'args': args
				}
				
				# closeEvent가 호출되도록 창을 닫음
				self.close()

				if INFO.OS == 'Windows':
					# Windows에서는 subprocess.Popen 사용
					subprocess.Popen([self._restart_info['executable'], self._restart_info['script']] + self._restart_info['args'])
				else:
					# Unix 계열에서는 os.execv 사용
					os.execv(self._restart_info['executable'], [self._restart_info['executable'], self._restart_info['script']] + self._restart_info['args'])
				
				# 현재 프로세스 종료
				QApplication.instance().quit()
		except Exception as e:
			logging.error(f"애플리케이션 재시작 중 오류 발생: {e}")
			QMessageBox.critical(self, "재시작 오류", f"애플리케이션을 재시작하는 중 오류가 발생했읍니다:\n{e}")






	def handle_print(self):
		dialog = QtPrintSupport.QPrintDialog()
		if dialog.exec_() == QtWidgets.QDialog.Accepted:
			pass

			# self.editor.document().print_(dialog.printer())

	def handle_print_preview(self):
		dialog = QtPrintSupport.QPrintPreviewDialog()
		dialog.paintRequested.connect(self.show_print_preview)
		dialog.exec_()

	def show_print_preview(self, printer):
		painter = QtGui.QPainter()
		painter.begin(printer)
		painter.setPen(Qt.red)
		painter.drawPixmap(0, 0, self.capture_mainWindow() )
		painter.end()
	
	# https://stackoverflow.com/questions/51361674/is-there-a-way-to-take-screenshot-of-a-window-in-PyQt6-or-qt5
	# windows Ok???😀😀
	def capture_mainWindow(self) ->QPixmap:
		# 현재 QMainWindow가 위치한 화면 (screen) 가져오기
		screen = self.window().screen()		
		# 해당 screen 전체 화면 캡처
		screenshot = screen.grabWindow(0)		
		return screenshot
		#### 현재 윈도우 캡쳐 : 여러 동작이 빠지므로 제외함
		# return QWidget.grab(self)

	# @pyqtSlot(bool, dict)
	def handle_Login(self, _is_login:bool):
		"""
			main function에서 login moudle에서 GBUS.LOGIN 이벤트 발생함.
		"""
		if _is_login : 	
			self.initialize_after_login()
			self.init_recording_by_timer()

			# self.send_app_access_log('login')

			self.show()
		else: 
			self.hide()
			self.close()

	def handle_개발자모드(self, changed_app권한_dict:dict):

		self.app권한.append(changed_app권한_dict)
		self.app권한.sort(key=lambda x: x.get('순서'))

	# def _update_render_toolbar(self):

	# 	### 1. toolbar 변경
	# 	self.removeToolBar(self.tb.tb)
	# 	self.tb = Ui_Toolbar(self, self.app권한)
	# 	User_Toast( INFO.MAIN_WINDOW, duration=5000, title='App Changed', text=f'{INFO.USERNAME} 님의 Menu를 변경하였읍니다.', style='SUCCESS')

	def _update_tabs(self, changed_app권한_dict:dict, _type:str='add', changes_dict:dict=None):
		is_toast = True
		cur_tab_wid, appID, cur_idx = self.__get_cur_tab_info()
		changed_표시명_구분 = changed_app권한_dict.get('표시명_구분')
		_idx_tab_obj = self._getTabIndexByObjectName(f"appid_{changed_app권한_dict.get('id')}")

		if not appID or not cur_tab_wid or self.curTabs.objectName() != changed_표시명_구분:

			return
		
		same_표시명_구분_list = [ app for app in self.app권한 if app.get('표시명_구분') == changed_표시명_구분 ]
		match _type:
			case 'add':
				added_tab_wid = self._create_tab_widget(changed_app권한_dict)
				self.curTabs.insertTab(same_표시명_구분_list.index(changed_app권한_dict), added_tab_wid, changed_app권한_dict.get('표시명_항목'))				
			case 'remove':
				self.curTabs.removeTab( _idx_tab_obj )
			case 'change':
				is_toast = False
				self._update_tabs_change(changed_app권한_dict, changes_dict)
				
			case _:

				return
		self.tabs[changed_표시명_구분] = self.curTabs
		if is_toast:
			User_Toast( INFO.MAIN_WINDOW, duration=5000, title='App Changed', text=f'{INFO.USERNAME} 님의 Tab를 변경하였읍니다.', style='SUCCESS')

	def _update_tabs_change(self, changed_app권한_dict:dict, changes_dict:dict):
		is_toast = True
		changed_표시명_구분 = changed_app권한_dict.get('표시명_구분')
		_idx = self._getTabIndexByObjectName(f"appid_{changed_app권한_dict.get('id')}")
		tab_obj = self.tabs[changed_표시명_구분].widget(_idx)

		changed_key = list(changes_dict.keys())[0]
		value = changes_dict.get(changed_key).get('new')
		match changed_key:
			case 'is_Active':
				pass
			case 'is_Run':
				self.tabs[changed_표시명_구분].tabBar().setTabEnabled(_idx, value)
				self.tabs[changed_표시명_구분].setTabEnabled(_idx, value)
			case 'help_page':
				is_toast = False
				if tab_obj.app:
					tab_obj.app._init_kwargs( **changed_app권한_dict )
					tab_obj.app._update_page_info(value)
			case 'info_title':
				is_toast = False
				if tab_obj.app:			
					tab_obj.app._init_kwargs( **changed_app권한_dict )		
					tab_obj.app._set_info_title(value)
			case _:
				pass
		if is_toast:
			User_Toast( INFO.MAIN_WINDOW, duration=5000, title='App Changed', text=f'{INFO.USERNAME} 님의 Tab를 변경하였읍니다.', style='SUCCESS')
	

	def check_specific_changes(self, prev_item:dict, new_item:dict) -> dict:
		"""특정 속성의 변경 여부를 확인합니다."""
		changes = {}
		
		# 확인할 중요 속성 목록
		important_attrs = ['is_Active', 'is_Run', 'is_dev', '표시명_항목', '표시명_구분', 'help_page', 'info_title']
		
		for attr in important_attrs:
			if prev_item.get(attr) != new_item.get(attr):
				changes[attr] = {
					'prev': prev_item.get(attr),
					'new': new_item.get(attr)
				}
		
		return changes

	def _create_tab_widget(self, appDict:dict):
		divName , appName = appDict.get('div'), appDict.get('name')    
		tabObj = QtWidgets.QWidget()
		tabObj.setObjectName(f'appid_{appDict.get("id")}')
		return tabObj

	def __get_cur_tab_info (self) -> tuple[ QWidget, int, int] :
		""" 현재 선택된 tab의 정보를 반환하는 함수 
			return 으로 current tab내의 widget, appID"""
		try :
			cur_tab_wid = self.curTabs.widget(self.curTabs.currentIndex())	
			appID = cur_tab_wid.objectName().split('_')[-1]
			return cur_tab_wid, int(appID), self.curTabs.currentIndex()
		except Exception as e:
			loki.error(f"MainWindow : __get_cur_tab_info : {e}")
			loki.error(f"MainWindow : __get_cur_tab_info : {traceback.format_exc()}")
			return None, None, None
		
	def _getTabIndexByObjectName(self, object_name: str) -> int:
		"""
		self.curTabs(QTabWidget)에 등록된 각 탭 위젯들의 objectName을 확인하여,
		주어진 object_name과 일치하는 탭의 index를 반환합니다.
		일치하는 위젯이 없으면 -1을 반환합니다.
		"""
		for idx in range(self.curTabs.count()):
			widget = self.curTabs.widget(idx)
			if widget.objectName() == object_name:
				return idx
		return -1



	def reload_current_app(self):
		"""현재 선택된 앱을 강제로 다시 로드합니다."""
		if self.curTabs and self.cur_appDict:
			cur_widget, appID, cur_idx = self.__get_cur_tab_info()
			if cur_widget:
				# 앱 참조 초기화
				if hasattr(cur_widget, 'app') and cur_widget.app:
					try:
						if not sip.isdeleted(cur_widget.app):
							cur_widget.app.hide()
							cur_widget.app.deleteLater()
					except:
						pass
					cur_widget.app = None
					
				# 앱 다시 로드
				self.trigger_Branch(appDict=self.cur_appDict, tabWidget=cur_widget)
				User_Toast(parent=self, duration=2000, title="앱 리로드", text=f"{self.cur_appDict.get('표시명_구분')} - {self.cur_appDict.get('표시명_항목')}", style='INFORMATION')


	### tab clicked from Ui_tabs.py
	def slot_tabBarClicked(self, index):
		if not self.curTabs.widget(index) or not self.curTabs.widget(index).isEnabled():
			return

		self._set_cur_tab_style()

		self.appName = self.curTabs.tabText(index)
		appid = self.curTabs.widget(index).objectName().split('_')[-1]

		self.trigger_Branch(
			appDict = utils.get_Obj_From_ListDict_by_subDict(self.app권한, {'id': int(appid)}), 
			tabWidget=self.curTabs.widget(index)
		)

	

	def render_title(self, is_login:bool):
		if not is_login: return 
		_title_text = f" 접속서버 : {INFO.API_SERVER}-{INFO.HTTP_PORT} - {INFO.APP_Name} (Version: {INFO.Version}  {INFO.종류} ) - 사용자 :{INFO.USERNAME }"
		if INFO.IS_DEV:
			_title_text += f" - 개발자 모드 : {INFO.USERNAME }"
		self.setWindowTitle(_title_text)

	def _toast_hellow_login(self):
		text = f'{INFO.MAIL_ID} ({INFO.USERNAME}) 님  환영합니다.'
		toast = User_Toast(self, duration=3000,title='Login Success', 
				text= text, style='SUCCESS')

import asyncio
class AsyncEventLoop(QEventLoop):
    def __init__(self):
        super().__init__()

    def processEvents(self, flags=None):
        super().processEvents(flags)
        # asyncio 작업을 처리하려면 asyncio 이벤트 루프를 진행시킴
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))


def main():    
	# ✅ 이벤트 루프 설정 추가 (Windows aiodns 문제 해결용)
	import asyncio
	import platform
	if platform.system().lower() == "windows":
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

	from plugin_main.style.stylesheet import StyleSheet as AppStyleSheet
	INFO.PID_Main = os.getpid()
	# 로깅 설정 초기화 - 애플리케이션 시작 시 한 번만 호출
	configure_app_logging(INFO.IS_DEV)

	# 환경 변수 및 OpenGL 설정 → 반드시 QApplication 전에!
	# GPU 및 샌드박스 비활성화
	os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu --disable-software-rasterizer"
	os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
	os.environ["QT_QUICK_BACKEND"] = "software"  # 중요: QtQuick 강제 software fallback
	#  OpenGL을 완전히 소프트웨어로 강제
	QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

	app=QtWidgets.QApplication(sys.argv)
	loop = qasync.QEventLoop(app)   # ✅ asyncio 호환 루프
	asyncio.set_event_loop(loop)    # ✅ 여기서 AssertionError 안남

	style = AppStyleSheet()
	style.apply_to_app(app)

	# 예외 처리 함수가 제대로 작동하는지 테스트
	# try:
	# 	# 의도적으로 예외 발생

	# 	1/0  # ZeroDivisionError 발생
	# except Exception as e:

	# 	# 여기서 예외를 다시 발생시켜 sys.excepthook이 호출되도록 함
	# 	raise
	from update_v2 import Update_V2
	# update = Update()
	updateManager = Update_V2()
	if len( fName:= updateManager.update_routine()) :
		match INFO.OS:
			case 'Windows':
				exeName = fName[2:].replace('/', '\\')
				subprocess.Popen(exeName)
				return 0

	res = None
	if INFO.IS_FACELOGIN:
		login_face = Face_Recognition_Login(			
			verify_url='ai-face/user-face/facelogin_via_rpc/',
			is_hidden=False,
		)

		if login_face.exec():
			print (f"login_face success")
			res = login_face.get_result()
		else:
			print (f"login_face failed")


	if res :
		login = Login(face_recognition_login_data=res)    
		window=MainWindow()

		with loop:
			loop.create_task(window.start_ws())
			loop.run_forever()
	else:
		login = Login()    
		if login.exec():
			loki.info( msg=f"{INFO.USERNAME} login success" )
			window=MainWindow()
			with loop:
				# WS 시작을 태스크로 걸고, Qt 앱을 돌리면 끝.
				loop.create_task(window.start_ws())
				loop.run_forever()
		else:
			return -1

def handle_login_face(login_face:Face_Recognition_Login, data:dict):

	if data.get('status', 'fail')== 'success':
		import requests
		# 클라이언트 예제 (Python requests)
		refresh_token = data['refresh']
		access_token = data['access']
		headers = {'Authorization': f'JWT {access_token}'}
		resp = requests.post( "http://192.168.7.108:9999/api/users/facelogin/", 
							json={'refresh':refresh_token}, 
							headers=headers
							)
		if resp.ok:
			login_data = resp.json()  # 일반 로그인과 동일한 구조
			print (f"login_data: {login_data}")
			login_face.set_result(login_data)
			login_face.accept()

		else:
			print (f"login_data failed: {resp.status_code} {resp.text}")
			login_face.reject()


	else:

		login_face.reject()

	# 종료 직후, 한번더  cv2 종료
	if hasattr(login_face, 'cap') and login_face.cap is not None:
		login_face.cap.release()
		login_face.cap = None


if __name__ == "__main__":
	from plugin_main.preload_lib import PreloadLib
	import threading
	preloader = PreloadLib()
	preloader.start()
	# 별도 스레드에서 wait_all 실행
	threading.Thread(target=lambda: preloader.wait_all(), daemon=True).start()
	match INFO.OS:
		case 'Windows':
			import pyuac
			if not pyuac.isUserAdmin():
				pyuac.runAsAdmin()
			else:
				try:
					sys.exit(main())
				finally:
					# 애플리케이션 종료 시 preloader 정리
					if 'preloader' in locals() and preloader is not None:
						preloader.stop()

		case _:
			try:
				sys.exit(main())
			finally:
				# 애플리케이션 종료 시 preloader 정리
				if 'preloader' in locals() and preloader is not None:
					preloader.stop()