import sys, traceback, os
from PyQt6 import QtCore, QtGui, QtWidgets, QtPrintSupport, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebEngineCore import *

# from pyqtspinner.spinner import WaitingSpinner
# from WaitingSpinnerWidget import QtWaitingSpinner
from modules.PyQt.dialog.hover.dlg_hover import Dlg_Hover

import pandas as pd
import urllib
from datetime import date, datetime, timedelta
from pprint import pprint
import pathlib
import psutil
import info ,subprocess
import copy

import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class QCalendar_휴일(QCalendarWidget):
	signal_clicked = pyqtSignal(dict, str)
	signal_current_page_changed = pyqtSignal(int, int)
	signal_contextMenu = pyqtSignal( str, QDate )

	def __init__(self, parent=None, **kwargs):
		super().__init__(parent)
		### type  선언
		self.api_data :list[dict]

		for k,v in kwargs.items():
			setattr(self, k, v)

		self.events = {}

		self.setGridVisible(True)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.cell_default = QtGui.QTextCharFormat()
		self.cell_default.setBackground(QtGui.QColor("white"))

		self.cell_changed = QtGui.QTextCharFormat()
		self.cell_changed.setBackground(QtGui.QColor("yellow"))


		self.clicked.connect(self.slot_clicked)
		self.currentPageChanged.connect(self.slot_current_page_changed )


	def contextMenuEvent(self, event):
		return 
		# obj:QTableView = self.findChild ( QTableView, 'qt_calendar_calendarview')


		# index = obj.indexAt(event.globalPos() )


		# model = obj.model()
		select_qDate = self.selectedDate()
		now_day = datetime.today().date()
		if select_qDate :
			pyDate = select_qDate.toPyDate() 
			menu = QtWidgets.QMenu()
			if pyDate == (now_day - timedelta(days=1) ):
				uploadAction = menu.addAction('File Upload')
				uploadAction.triggered.connect (lambda: self.signal_contextMenu.emit ('File Upload', select_qDate ) )
				if self._is_file_exist(pyDate):
					downloadAction = menu.addAction('File Download')
					downloadAction.triggered.connect ( lambda: self.signal_contextMenu.emit ('File Download', select_qDate ))

				# res = menu.exec(event.globalPos())
				# if res == uploadAction:

			elif pyDate < (now_day - timedelta(days=1) ) and self._is_file_exist(pyDate):
				downloadAction = menu.addAction('File Download')
				downloadAction.triggered.connect ( lambda: self.signal_contextMenu.emit ('File Download', select_qDate ))
				# res = menu.exec(event.globalPos())
				# if res == downloadAction :

			else:
				return 
			menu.exec(event.globalPos())
			# menu.move(event.globalPos() )
			# menu.setVisible(True)
	

	def _update_data(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
		self.events = self._get_event_dates(self.api_data)
		

	def _get_event_dates(self, app_DB_data:list[dict]) -> dict:		
		events = {}
		for obj in app_DB_data:
			if ( date_str := obj.get('휴일') ) is None: continue
			
			_qDate = QtCore.QDate.fromString(date_str, Qt.DateFormat.ISODate)
			events[_qDate]  = obj.get('id', -1)
			# events.append( QtCore.QDate.fromString(date_str, self.date_format) )
		return events
	
	@pyqtSlot()
	def slot_contextMensu(self):
		self.signal_contextMenu.emit( self.sender().objectName(), )

	@pyqtSlot()
	def slot_current_page_changed( self ):
		self.signal_current_page_changed.emit ( self.yearShown(), self.monthShown() )

	@pyqtSlot()
	def slot_clicked(self):
		# self._gen_hover_dlg()
		휴일_str = self.selectedDate().toString( Qt.DateFormat.ISODate )
		originalDict = Utils.get_Obj_From_ListDict_by_subDict(self.api_data, {'휴일': 휴일_str})
		self.signal_clicked.emit(originalDict, 휴일_str )


	def paintCell(self, painter:QPainter, rect:QRect, date:QDate):
		super().paintCell(painter, rect, date)
		if date in self.events.keys():			
			### 등록표시
			painter.setBrush(Qt.GlobalColor.yellow)
			painter.drawEllipse(rect.topLeft() + QPoint(20, 20), 16, 16)
			painter.setPen ( QColor(0,0,0))
			rect_hi = QRect( rect.topLeft(),QSize(40,40))


			painter.drawText( rect_hi, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, str(self.events[date]) )

			######################
			painter.drawText(rect, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, str(date.day()) )
			self.setDateTextFormat( date, self.cell_changed )

			# [is_hi,is_po] , _ = _is_exist_file(self.app_DB_data, date )
			# if not is_hi and not is_po:
			# 	txt = 'X'
			# elif is_hi and is_po:
			# 	txt = '完' 
			# else:
			# 	txt = 'HI' if is_hi else 'PO'
			# painter.drawText( rect_hi, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, txt )

			# ######################
			# painter.drawText(rect, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, str(date.day()) )
			# self.setDateTextFormat( date, self.cell_changed )
		else:
			self.setDateTextFormat( date, self.cell_default)

	def _gen_hover_dlg(self):
		txt = ''
		dlgHover = Dlg_Hover(self)
		일자_str = self.selectedDate().toString( Qt.DateFormat.ISODate )
		dlgHover.setWindowTitle ( 일자_str )
		obj = Utils.get_Obj_From_ListDict_by_subDict(self.api_data, {'일자': 일자_str })
		for key, value in obj.items():
			txt += f" {key} : {value if not 'file' in key else Utils.get_fName_from_url(value)} \n"
		
		dlgHover.dlg_tb.setText ( txt )