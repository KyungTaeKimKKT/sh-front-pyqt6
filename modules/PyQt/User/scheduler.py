import sys, traceback, os
from PyQt6 import QtCore, QtGui, QtWidgets, QtPrintSupport, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Scheduler(QCalendarWidget):
	date_format = "yyyy-MM-dd"
	def __init__(self, parent=None , **kwargs):
		super().__init__(parent)
		for k, v in kwargs.items():
			setattr(self, k, v)



		self.app_DB_data:list = parent.app_DB_data
		self.events = self._get_event_dates()

		self.url = parent.url
		# self.date_format ="yyyy-M-d"

		self.setGridVisible(True)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.cell_default = QtGui.QTextCharFormat()
		self.cell_default.setBackground(QtGui.QColor("white"))

		self.cell_changed = QtGui.QTextCharFormat()
		self.cell_changed.setBackground(QtGui.QColor("yellow"))


		self.clicked.connect(self.slot_clicked)

	def paintCell(self, painter, rect, date):
		super().paintCell(painter, rect, date)
		if date in self.events.keys():
			
			### 등록표시
			painter.setBrush(Qt.yellow)
			painter.drawEllipse(rect.topLeft() + QPoint(20, 20), 16, 16)
			painter.setPen ( QColor(0,0,0))
			rect_hi = QRect( rect.topLeft(),QSize(40,40))
			painter.drawText( rect_hi, Qt.TextSingleLine|Qt.AlignCenter, '完' )

			######################
			painter.drawText(rect, Qt.TextSingleLine|Qt.AlignCenter, str(date.day()) )
			self.setDateTextFormat( date, self.cell_changed )
		else:
			self.setDateTextFormat( date, self.cell_default)

	def _get_event_dates(self) -> dict:
		events = {}
		for obj in self.app_DB_data:
			if ( date_str := obj.get('휴일') ) is None: continue
			_qDate = QtCore.QDate.fromString(date_str, self.date_format)
			events[_qDate]  = obj.get('id')
			# events.append( QtCore.QDate.fromString(date_str, self.date_format) )
		
		return events
	
	@pyqtSlot()
	def slot_clicked(self):
		selectDate = self.selectedDate()
		if selectDate in self.events:
			is_ok = self.delete_date(selectDate)
		else:
			is_ok = self.add_date(selectDate)
		
		if is_ok : self.update()
		
			
	def add_date(self, date:QDate) -> bool:
		data = {
			'휴일': date.toString(self.date_format),
			'휴일내용': None
		}
		is_ok, _json = APP.API.post(self.url, data)
		if is_ok :
			self.events[date] = _json.get('id')
		return is_ok

	   
	def delete_date(self, date:QDate) -> bool:
		url = self.url + f'{self.events.get(date)}/'
		
		if (is_ok := APP.API.delete(url)) :
			self.events.pop(date)
		return is_ok