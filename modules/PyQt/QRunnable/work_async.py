from PyQt6 import QtCore, QtGui, QtWidgets, QtPrintSupport, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebEngineCore import *

import time

from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class WorkerSignals(QtCore.QObject):
	signal = QtCore.pyqtSignal(bool, bool, object)
	signal_post_get_websocket =  QtCore.pyqtSignal(bool, object)


class Worker(QRunnable):
	""" defulat GET """
	signal_worker_finished = WorkerSignals()

	def __init__(self, url, parent=None):
		super().__init__()
		
		self.parentWidget = parent
		self.async_api = Async_API_SH()
		self.url = url
		self.setAutoDelete(True)  # 작업 완료 후 자동 삭제 설정


		
	def run(self):
		start_time = time.time()

		is_Pagenation = bool (  not 'page_size=0' in self.url )
		is_ok, api_datas = self.async_api.Get(self.url)
		if is_ok :
			self.signal_worker_finished.signal.emit( is_Pagenation, is_ok, api_datas)
		else :
			self.signal_worker_finished.signal.emit( is_Pagenation, is_ok, api_datas)

		


class Worker_Post(QRunnable):
	""" defulat GET """
	signal_worker_finished = WorkerSignals()

	def __init__(self, url:str, data:dict):
		super().__init__()
		
		
		self.async_api = Async_API_SH()
		self.url = url
		self.data = data 
		
	def run(self):

		is_ok, api_datas = self.async_api.Post(self.url, self.data)

		self.signal_worker_finished.signal.emit( False, is_ok, api_datas)
		self.signal_worker_finished.signal_post_get_websocket.emit( is_ok, api_datas)

		