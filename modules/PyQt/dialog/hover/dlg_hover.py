from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dlg_Hover(QDialog):
	"""
		View Only => dlg_tb : QTextBrowser 에 사용\n

	"""

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		for k, v in kwargs.items():
			setattr(self, k, v )
			
		self.UI()
		self.show()

	def UI(self):
		vLayout = QVBoxLayout()
		self.dlg_tb = QTextBrowser(self)
		self.dlg_tb.setAcceptRichText(True)
		self.dlg_tb.setOpenExternalLinks(True)
		vLayout.addWidget(self.dlg_tb)
		self.setLayout(vLayout)
