from config import Config as APP
from PyQt6.QtCore import QThread, pyqtSignal
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Background_API_Thread(QThread):
	""" API FETCH THREAD 
		EMIT 후 CLOSE 됨
	"""
	finished = pyqtSignal(bool, object)
	error = pyqtSignal(bool, object)

	def __init__(self, url, parent=None):
		super().__init__(parent)
		self.url = url

	def run(self):
		try:
			is_ok, api_datas = APP.API.getlist(self.url)
			self.finished.emit(is_ok, api_datas)			
		except Exception as e:
			self.error.emit(False, e)
		finally:
			self.quit()
			# self.wait()