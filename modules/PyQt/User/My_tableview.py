from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
####
from stylesheet import StyleSheet

import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class My_TableView(QtWidgets.QTableView):
	""" kwargs
		hidden_columns : list[str]
	"""
	signal_vMenu = QtCore.pyqtSignal(dict)


	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] , **kwargs) -> None: 
		super().__init__(parent)

		if kwargs : 
			self.setConfig(**kwargs)

		self.parent=parent
		self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers |
							QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
		
		####
		self._init__v_header_contextMenu()
		self._init__h_header_contextMenu()
		self.v_header_menu:QtWidgets.QMenu 
		self.h_header_menu:QtWidgets.QMenu 
		self.v_header_menu_dict ={}
		self.h_header_menu_dict ={}

		if hasattr(self.parent, 'appData') :		
			if hasattr(self.parent.appData, 'table_Sorting'):
				self.setSortingEnabled(self.parent.appData.table_Sorting)
		else: 
			self.setSortingEnabled(False)

		self.st = StyleSheet()
		self.setStyleSheet( self.st.tb_header_stylesheet)
	
		self._init_select_trigger()
		##### attributes
		### rowSpan 된 column index 저장
		self._rowSpanList = []
		self._hidden_cols = []

		self.no_Menu_Cols = []
		self.no_Menu_Rows = []




		#### setting h_headers width
		self.h_headers.setMinimumWidth(48)
		self.h_headers.setMaximumWidth(64)
		self.h_headers.setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

		#### setting v_header width
		# 😀 동작안함
		# self._set_column_width()

		self.resizeColumnsToContents()  
		self.installEventFilter(self)

	def setConfig (self, **kwargs) -> None:
		""" kwargs : table_config 사용
			ui를 사용하면 실질적인 main run 함수
		"""
		self.__init__Attribute()
		
		for key, value in kwargs.items():
			setattr(self, key, value)

		self._hide_hidden_cols()

	def __init__Attribute(self):
		self.table_header:list[str] = []
		self.no_Edit_cols : list[str] = []
		self.hidden_columns : list[str] = []
		self.no_vContextMenu : list[str] = []
		self.no_hContextMenu : list[str] = []
		self.no_vContextMenuCols : list[str] = self.hidden_columns
		self.v_Menus : dict[str:dict[str:str]] = {}

		# attribute_names =[ 'hidden_columns', ]

		# for attrName in attribute_names:
		# 	self.hidden_columns = [] if not hasattr(self, attrName) else getattr(self, attrName)

		
	def _hide_hidden_cols(self, hidden_columns:list[str] =[] ) -> None:
		"""
			hidden_columns: list[str]가 있으면 hide
			없으면 self.hidden_column : list[str] 이 있으면 해당 column을 hide
		"""

		self.hidden_columns : list[str]
		hidden_columns = hidden_columns if hidden_columns else self.hidden_columns
		

		for hidden_col_name in self.hidden_columns:
			self.hideColumn( self.table_header.index(hidden_col_name))


	
		
	def _init__v_header_contextMenu(self):
		self.v_headers = self.horizontalHeader()
		self.v_headers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self._enable_v_header_contextmenus()
	
	def _enable_v_header_contextmenus(self):

		self.v_headers.customContextMenuRequested.connect(self.v_header_contextMenu)

	def _disable_v_header_contextmenus(self):

		try:
			self.v_headers.customContextMenuRequested.disconnect(self.v_header_contextMenu)	
		except:
			pass
	
	def _init__h_header_contextMenu(self):
		self.h_headers = self.verticalHeader()
		self.h_headers.setContextMenuPolicy(Qt.CustomContextMenu)
		self._enable_h_header_contextmenus()

	def _enable_h_header_contextmenus(self):
		self.h_headers.customContextMenuRequested.connect(self.h_header_contextMenu)
	def _disable_h_header_contextmenus(self):
		self.h_headers.customContextMenuRequested.disconnect(self.h_header_contextMenu)	
	
	def _init_select_trigger(self):
		pass
		# self.clicked.connect (self.handle_clicked)
		# self.doubleClicked.connect(self.handle_doubleClicked)

	def _set_column_width(self):
		if hasattr( self.parent.appData, "header_width"):
			header_width:dict = self.parent.appData.header_width
		else:
			return 
		for (index, (key, value) ) in enumerate( header_width.items() ):
			if value is None: continue
			self.setColumnWidth(index, value)

	def eventFilter(self, obj, event:QtCore.QEvent):
		if obj is self and event.type() == QtCore.QEvent.KeyPress:
			if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
				indexes = self.selectedIndexes()
				if indexes:
					self.edit_mode(indexes[0])
		

		return super().eventFilter(obj, event)
	
	##### Trigger functions  ####
	def edit_mode(self, index:QtCore.QAbstractTableModel.index):
		row, column, cell_value = index.row(), index.column(), index.data()

		# self.lineEdit.setText("%s" % cell_value)


	####### 😀😀 contextMenu는 
	# 1. render ==> parent.appData.v_header_context_menu ==> Data.py 의 v_header_context_menu
	# 2. render 하면서, slot에 connect 함.
	@pyqtSlot(QPoint)
	def v_header_contextMenu(self, point) -> QMenu|None:
		col = self.v_headers.logicalIndexAt(point.x())
		colName = self.table_header[col]

		if colName in self.no_vContextMenuCols: 
			return None
		self.v_header_menu = self.v_header_contextMenu_Render(point)

	def v_header_contextMenu_Render(self, point:QPoint) ->QtWidgets.QMenu:
		col = self.v_headers.logicalIndexAt(point.x())
		menu = QtWidgets.QMenu(self)

		# 😀😀😀 : generate action
		for ( key, obj ) in self.v_Menus.items() :
			match key :
				case 'section' : menu.addSection('')
				case 'seperator' : menu.addSeparator()
				case _:
					action = self._gen_element_v_header_contextMenu_Action( menu,  obj, col )
					action.triggered.connect(lambda: self.slot_v_header_contextMenu(col))
					self.v_header_menu_dict[key] = action
		
		menu.setToolTipsVisible(True)
		menu.move( self.mapToGlobal(point) )
		menu.setVisible(True)
		return menu

	
	def _gen_element_v_header_contextMenu_Action(self, menu:QtWidgets.QMenu, obj:dict ,col:int ) -> QtGui.QAction:
		action:QtGui.QAction = menu.addAction(eval(obj.get('icon')) ,obj.get('title'))
		action.setToolTip( obj.get('tooltip'))
		action.setObjectName( obj.get('objectName'))

		return self.user_defined_gen_elm_vHeader_CM_Action(action, obj, col)

	def user_defined_gen_elm_vHeader_CM_Action(self, action:QtGui.QAction=None, obj:dict={}, col:int=0) ->QtGui.QAction:
		match  (title := obj.get('title') ):
			###😀 row span은 setting value 와 현재 상태( self._rowSpanList )와 and 조건으로 동작
			case 'Set_row_span':
				if col in self._rowSpanList : 
					action.setEnabled( obj.get('enabled') & False )
				else : 
					action.setEnabled( obj.get('enabled') & True )
			case 'Reset_row_span':
				if col in self._rowSpanList : 
					action.setEnabled( obj.get('enabled') & True )
				else : 
					action.setEnabled( obj.get('enabled') & False )
			case _:
				action.setEnabled( obj.get('enabled') )
		
		return action

	@pyqtSlot(int)
	def slot_v_header_contextMenu(self, col:int):
		action = self.sender().objectName().capitalize().strip()
		self.signal_vMenu.emit ( {
			'action' : col
		})
	# 	match action:
	# 		case 'Set_row_span'| 'Reset_row_span'  :
	# 			self.signal.emit( {
	# 				'action': action.lower(),
	# 				'data' : {
	# 					'col': col,
	# 				}
	# 			})
	# 			if action == 'Set_row_span' :
	# 				self._rowSpanList.append(col)
	# 			elif action == 'Reset_row_span':
	# 				self._rowSpanList.remove(col)

	# 		case 'Hide_column':
	# 			self.hideColumn(col)

	# 		case 'Show_column':
	# 			self.handle_show_column()

	# 		case _:
	# 			self.user_defined_slot_v_header_contextMenu(action, col)

	# def user_defined_slot_v_header_contextMenu(self, action:str, col:int):
	# 	match action:
	# 		case _:
	# 			User_Toast( parent=self, title='지원하지 않는 Action 명령어입니다.', 
	# 		   				text=f"action 명령어 {action}", style='WARNING')
				


	####### 😀😀 contextMenu는 
	# 1. render ==> parent.appData.h_header_context_menu ==> Data.py 의 h_header_context_menu
	# 2. render 하면서, slot에 connect 함.
	def h_header_contextMenu(self, point):
		row = self.h_headers.logicalIndexAt(point.y())
		if row in self.no_Menu_Rows : return 
		self.h_header_menu = self.h_header_contextMenu_Render(point)

	### ####😀😀😀
	def h_header_contextMenu_Render(self, point) ->QtWidgets.QMenu:
		row = self.h_headers.logicalIndexAt(point.y())

		# 😀😀😀 : generate action		
		menu = QtWidgets.QMenu(self)
		for ( key, obj ) in self.parent.appData.h_header_context_menu.items() :
			match key :
				case 'section' : menu.addSection()
				case key if 'seperator' in key : menu.addSeparator()
				case _:
					action = self._gen_element_h_header_contextMenu_Action( menu,  obj, row)
					action.triggered.connect(lambda: self.slot_h_header_contextMenu(row))
					self.h_header_menu_dict[key] = action
		
		menu.setToolTipsVisible(True)
		menu.move( self.mapToGlobal(point) )
		menu.setVisible(True)
		return menu
	
	def _gen_element_h_header_contextMenu_Action(self, menu:QtWidgets.QMenu, obj:dict ,row:int) -> QtGui.QAction:

		action:QtGui.QAction = menu.addAction(eval(obj.get('icon')) ,obj.get('title'))
		action.setToolTip( obj.get('tooltip'))
		action.setObjectName( obj.get('objectName'))
		action.setEnabled( obj.get('enabled') )
	
		return self.user_defined_gen_elm_hHeader_CM_Action(action, obj, row)

	def user_defined_gen_elm_hHeader_CM_Action(self, action:QtGui.QAction=None, obj:dict={}, row:int=0) ->QtGui.QAction:
		match  (title := obj.get('title') ):
			###😀 row span은 setting value 와 현재 상태( self._rowSpanList )와 and 조건으로 동작
			case _:
				action.setEnabled( obj.get('enabled') )
		
		return action

	def slot_h_header_contextMenu(self, row:int):
		action = self.sender().objectName().strip()
		match action:
			case 'New'|'Upgrade'| 'Edit' | 'View' | 'Delete' |'Form_Edit'|'Form_View' |'작성완료' :
				self.signal.emit( {
					'action': action.lower(),
					'data' : {
						'row': row,
					}
				})
			case 'Export_to_excel'| 'Preview' | 'Print' |'Form_New'|'Search':
				self.signal.emit( {'action': f'handle_{action.lower()}'})
			case _:
				self.user_defined_slot_h_header_contextMenu(action, row)

	def user_defined_slot_h_header_contextMenu(self, action:str, row:int):
		match action:			
			case _:
				self.signal.emit( {
					'action': action.lower(),
					'data' : {
						'row': row,
					}
				})
				

	####### 😀😀 contextMenu는 
	## 😀😀1. redner ==> super().method로 수정...
	##      2  trigger connect로 이루어져 있음
	def contextMenuEvent(self, event:QtGui.QContextMenuEvent):	
		indexes = self.selectionModel().selectedIndexes()
		for index in sorted(indexes):
			row = index.row()
			col = index.column()
		
		if ( menu:= self.contextMenu_Render_Connect(event, row, col) ) is not None:
			menu.popup(QtGui.QCursor.pos())
				

	#### Menu render and connect 
	def contextMenu_Render_Connect(self, event, row:int, col:int) ->QtWidgets.QMenu:
		menu : QtWidgets.QMenu = None
		# match self.parent.header[col]:
		# 	case 'app사용자수':
		# 		menu = QtWidgets.QMenu(self)
		# 		self.action_download = menu.addAction(QtGui.QIcon(":/table-icons/tb-insert_row.svg"),'App사용자 관리')
		# 		self.action_download.setToolTip('App사용자를 추가,삭제 할 수 있읍니다.')
		# 		menu.addSeparator()

		# 		self.action_download.triggered.connect(lambda:self.slot_app사용자관리(row))
	
		# 	case _:
		# 		pass
		return menu
	
	
	################## slots#########
	def slot_selected_row(self):
		index = self.selectedIndexes()[0]
		row, col = index.row(), index.column()


	def handle_clicked(self):
		index = self.selectedIndexes()[0]
		row, col = index.row(), index.column()

		

	def handle_doubleClicked(self):
		index = self.selectedIndexes()[0]
		row, col = index.row(), index.column()


		self.signal.emit({
			'action':'cell_doubleClicked',
			'data' :{
				'row':row,
				'col':col,
			}
		})

	def handle_show_column(self):
		for col in self._hidden_cols:
			self.showColumn(col)

	def on_selectionChanged(self, selected, deselected):

		for ix in selected.indexes():
			pass


		for ix in deselected.indexes():
			pass



	def exist_hidden_colums(self) ->bool:
		result = False
		
		cols = self.model().columnCount(self)
		for col in range(cols):
			if self.isColumnHidden(col) and col not in self._hidden_cols:
				self._hidden_cols.append(col)
		return bool(self._hidden_cols)
	

	def _get_selected_rows(self) -> list[int]:
		""" selected rows return list """
		selectedRows =[]
		indexes = self.selectionModel().selectedRows()
		for index in sorted(indexes):
			selectedRows.append( index.row() )
		
		return list(set(selectedRows))


