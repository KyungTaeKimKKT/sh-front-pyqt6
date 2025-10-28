from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.User.table.My_tableview import My_TableView
import traceback
from modules.logging_config import get_plugin_logger


HOVER_LIST = []


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableView_디자인관리(My_TableView):
	signal_hover = pyqtSignal(bool, int, str, QPoint)
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
	
	def mouseMoveEvent(self, event:QtGui.QMouseEvent):
		""" hard coding으로 ..."""
		super().mouseMoveEvent(event)

		if not event.buttons():
			index = self.indexAt(event.pos())
			try:				
				id_idx = self.table_header.index('id')
				ID = self.model()._data[index.row()][id_idx]
			except:
				ID = -1

			hoverName = self.model().table_header [index.column()]
			if  hoverName in HOVER_LIST:
				self.setCursor(Qt.CursorShape.PointingHandCursor)
				if ID != -1:
					self.signal_hover.emit( True, ID, hoverName,QtGui.QCursor.pos() )
			else:
				self.unsetCursor()				
				self.signal_hover.emit( False, ID, hoverName, QtGui.QCursor.pos() )
