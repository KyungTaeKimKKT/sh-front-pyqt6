from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy

from modules.PyQt.User.table.My_tableview import My_TableView
import traceback
from modules.logging_config import get_plugin_logger


HOVER_LIST = []


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableView_HR평가_설정(My_TableView):
	signal_hover = pyqtSignal(bool, int, str, QPoint)
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	@pyqtSlot(QPoint)
	def h_header_contextMenu(self, point) -> QMenu|None:
		if len(list(self.h_Menus.keys())) == 0 or len(list(self.h_Menus.values())) == 0:

			return 
		row = self.h_headers.logicalIndexAt(point.y())

		### Model 에서 생성한 것을 가져와서 update함.
		try:
			self.no_Menu_Rows +=self.model().no_Menu_rows 
		except Exception as e:
			pass
		if hasattr(self, 'no_Menu_Rows') and row in self.no_Menu_Rows : return 
		if hasattr(self, 'no_hContextMenuRows') :
			if 'all' in self.no_hContextMenuRows  or row in self.no_hContextMenuRows: return
		
		### 😀추가됨
		### 즉, row 0 에 대해서만  h_Menu 생성하고,
		### if is_완료 면,  update menu만.
		### 아니면 전부다 ( update, db초기화, delete )
		if row == 0:
			self.h_header_menu = self.gen_menu_items(menu_type='h', menu_config=self.h_Menus, point=point)
			# modelData:list = self.model()._data[row]
			# if  modelData[self.table_header.index('is_완료')] :
			# 	coped_menu_config = copy.deepcopy ( self.h_Menus )
			# 	del coped_menu_config['DB_초기화']
			# 	del coped_menu_config['Delete']			
			# 	self.h_header_menu = self.gen_menu_items(menu_type='h', menu_config=self.h_Menus, point=point)
			# else : 
			# 	self.h_header_menu = self.gen_menu_items(menu_type='h', menu_config=self.h_Menus, point=point)
	
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
