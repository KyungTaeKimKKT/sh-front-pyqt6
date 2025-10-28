from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing
import copy

from info import Info_SW as INFO
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
####
from stylesheet import StyleSheet


class Dialog_Find(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("검색")
		self.setup_ui()

	def setup_ui(self):
		layout = QHBoxLayout()
		self.search_input = QLineEdit()
		self.search_button = QPushButton("찾기")
		self.reset_button = QPushButton("초기화")  # 리셋 버튼 추가
		
		layout.addWidget(self.search_input)
		layout.addWidget(self.search_button)
		layout.addWidget(self.reset_button)  # 리셋 버튼 추가
		self.setLayout(layout)

class My_TableView(QtWidgets.QTableView):
	""" kwargs
		hidden_columns : list[str]
	"""
	signal_vMenu = QtCore.pyqtSignal(dict)
	signal_hMenu = QtCore.pyqtSignal(dict)
	signal_cellMenu = QtCore.pyqtSignal(dict)
	signal_hover = pyqtSignal(bool, int, QPoint) ### show 여부, rowNo와 mouse QPoint를 줌
	signal_select_row = pyqtSignal(dict)
	signal_select_rows = pyqtSignal(list)


	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] , **kwargs) -> None: 
		super().__init__(parent)
		self.hidden_rows_by_dialog_find = set()  # 숨겨진 행들을 추적
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
		self.cell_menu_dict = {}

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
		# self.h_headers.setMinimumWidth(48)
		# self.h_headers.setMaximumWidth(64)
		self.h_headers.setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


		self.installEventFilter(self)

		self.setMouseTracking(True)

		self.setup_search_in_Tableview_Only()

	def setup_search_in_Tableview_Only(self):
	
		# 검색 다이얼로그 생성
		self.find_dialog = Dialog_Find(self)
		self.find_dialog.search_button.clicked.connect(self.find_text_in_Only_tableview)
		self.find_dialog.search_input.returnPressed.connect(self.find_text_in_Only_tableview)
		self.find_dialog.reset_button.clicked.connect(self.reset_search)  # 리셋 버튼 연결

		# Ctrl+F 단축키 설정
		self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
		self.find_shortcut.activated.connect(lambda: self.find_dialog.show() )

	def find_text_in_Only_tableview(self):
		search_text = self.find_dialog.search_input.text().lower()
		for row in range(self.model().rowCount(QModelIndex())):
			row_visible = False
			for col in range(self.model().columnCount(QModelIndex())):
				item = self.model().index(row, col)
				cell_text = str(self.model().data(item,  Qt.ItemDataRole.DisplayRole) ).lower()
				if search_text in cell_text:
					row_visible  = True
					break
			self.setRowHidden(row, not row_visible)

	def reset_search(self):
		self.find_dialog.search_input.clear()
		for row in range(self.model().rowCount(QModelIndex())):
			self.setRowHidden(row, False)

	def _enable_Mutl_Selection_Mode(self):
		# 다중 선택 모드 설정
		self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
		self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

	def setConfig (self, **kwargs) -> None:
		""" kwargs : table_config 사용
			ui를 사용하면 실질적인 main run 함수
		"""
		self.__init__Attribute()
		
		for key, value in kwargs.items():
			setattr(self, key, value)

		if hasattr(self, 'hidden_columns') : self._hide_hidden_cols()
		self._resizeTable()

		if hasattr(self, 'cols_width') :
			self.cols_width : dict[str:int]
			for theadName, width in self.cols_width.items():				
				self.setColumnWidth( self.table_header.index(theadName), width )

		#### set_Row_Span if self.row_span_list
		if hasattr(self, 'row_span_list') and len(self.row_span_list):
			for headerName in self.row_span_list:
				headerName:str|dict
				if isinstance(headerName, str):
					self._set_Row_Span(headerName=headerName)
				elif isinstance ( headerName, dict) :
					self._set_Row_Span( **headerName)
		

	def __init__Attribute(self):
		""" type 설정 개념."""
		self.table_header:list[str] = []
		self.no_Edit_cols : list[str] = []
		self.hidden_columns : list[str] = []
		self.no_vContextMenu : list[str] = []
		self.no_hContextMenu : list[str] = []
		self.no_vContextMenuCols : list[str] = self.hidden_columns
		self.no_hContextMenuRows : list[int|str]
		self.v_Menus : dict[str:dict[str:str]] = {}
		self.h_Menus : dict[str:dict[str:str]] = {}
		self.cell_Menus : dict[str:dict[str:str]] = {}
		
	def _hide_hidden_cols(self, hidden_columns:list[str] =[] ) -> None:
		"""
			hidden_columns: list[str]가 있으면 hide
			없으면 self.hidden_column : list[str] 이 있으면 해당 column을 hide
		"""

		self.hidden_columns : list[str]
		hidden_columns = hidden_columns if hidden_columns else self.hidden_columns
		
		for hidden_col_name in self.hidden_columns:
			self.hideColumn( self.table_header.index(hidden_col_name))
	
	def _resizeTable(self):
		for colNo, headName in enumerate(self.table_header):
			match self.model().header_type.get(headName, ''):
				case 'ManyToManyField'|'JSONField':
					self.setColumnWidth( colNo, 16*20)   ### px 단위임
				
				case _:
					self.resizeColumnToContents( colNo)
			# else:
			# 	if ( width:= self.table_col_width.get(headName, None) ) :
			# 		self.table.setColumnWidth( colNo, width)
			# 	else:
			# 		self.table.resizeColumnToContents( colNo)
		self.resizeRowsToContents()

		
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


	### 😀😀 menu Generation
	@pyqtSlot(QPoint)
	def v_header_contextMenu(self, point) -> QMenu|None:
		if len(list(self.v_Menus.keys())) == 0 or len(list(self.v_Menus.values())) == 0:

			return 
		col = self.v_headers.logicalIndexAt(point.x())
		colName = self.table_header[col]

		if colName in self.no_vContextMenuCols: 
			return None
		self.v_header_menu = self.gen_menu_items(menu_type='v', menu_config=self.v_Menus, point=point)

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

		self.h_header_menu = self.gen_menu_items(menu_type='h', menu_config=self.h_Menus, point=point)

	def contextMenuEvent(self, event:QtGui.QContextMenuEvent):	
		indexes = self.selectionModel().selectedIndexes()
		for index in sorted(indexes):
			row = index.row()
			col = index.column()
		
		self.gen_menu_items(menu_type='c', menu_config=self.cell_Menus, point=None, logical_pos=(col, row))


	def gen_menu_items(self, menu_type:str, menu_config:dict, point:QPoint, logical_pos:tuple[int,int]=(0,0) ) -> QMenu:
		""" 
			menu_type:str = 'h', 'v', 'c', 로 구분해서 생성
		"""
		menu = QtWidgets.QMenu(self)
		

		for (key, obj) in menu_config.items():
			match key :
				case 'section' : 
					menu.addSection('')
				case 'seperator' : 
					menu.addSeparator()
				case _:					
					if menu_type == 'v':						
						action = self._gen_menu_Action( menu,  obj, point, logical_pos )
						action.triggered.connect(lambda: self.slot_v_header_contextMenu( self.v_headers.logicalIndexAt(point.x()) ))
						self.v_header_menu_dict[key] = action
					elif menu_type == 'h':						
						action = self._gen_menu_Action( menu,  obj, point, logical_pos )
						action.triggered.connect(lambda: self.slot_h_header_contextMenu( self.h_headers.logicalIndexAt(point.y()) ))
						self.h_header_menu_dict[key] = action
					else :						
						pos:tuple[list[str],list[str|int] ] = obj.get('position')
						
						if self._check_cellMenu_x(x_headers=pos[0], logical_pos_x=logical_pos[0] ) and self._check_cellMenu_y(y_headers=pos[1], logical_pos_y=logical_pos[1]):
							action = self._gen_menu_Action( menu,  obj, point ,logical_pos)
							action.triggered.connect(lambda: self.slot_cell_contextMenu(logical_pos ))
							self.cell_menu_dict[key] = action
						

		menu.setToolTipsVisible(True)
		if point:
			menu.move( self.mapToGlobal(point) )
		else:
			menu.popup (QtGui.QCursor.pos() )
		menu.setVisible(True)
		return menu	

	def _gen_menu_Action( self, menu:QMenu, obj:dict, point:QPoint, logical_pos) ->QAction:
		action:QtGui.QAction = menu.addAction(eval(obj.get('icon')) ,obj.get('title'))
		action.setToolTip( obj.get('tooltip'))
		action.setObjectName( obj.get('objectName'))		

		return self.user_defined__Action(action, obj, point, logical_pos)
	
	def user_defined__Action( self, action:QAction, obj:dict, point:QPoint, logical_pos) ->QAction:
		match  (objectName := obj.get('objectName') ):

			case _:
				return action
			
	def _check_cellMenu_x(self, x_headers:list[str] , logical_pos_x:int) -> bool:
		""" x_headers : 해당 cell menu를 display 할 header name
			self.model().table_header 의 logical_pos[0] 이 포함되면 true, 
		"""
		for x_header in x_headers:	
			if x_header == self.model().table_header[logical_pos_x] :
				return True
		return False
			
	def _check_cellMenu_y(self, y_headers:list[str|int] , logical_pos_y:int) -> bool:
		""" x_headers : 해당 cell menu를 display 할 header name
			self.model().table_header 의 logical_pos[0] 이 포함되면 true, 
		"""
		if 'all' in y_headers : return True

		for y_header in y_headers:	
			if y_header == logical_pos_y :
				return True
		return False

	
	#### 😀😀😀 signal Emit
	@pyqtSlot(int)
	def slot_v_header_contextMenu(self, colNo:int):
		actionName = self.sender().objectName().lower().strip()
		self.signal_vMenu.emit ( {
			'action' : actionName,
			'col'  : colNo, 
		})

	@pyqtSlot(int)
	def slot_h_header_contextMenu(self, rowNo:int):
		actionName = self.sender().objectName().lower().strip()
		self.signal_hMenu.emit ( {
			'action' : actionName,
			'row'  : rowNo, 
		})

	@pyqtSlot(QPoint)
	def slot_cell_contextMenu(self, logical_pos:tuple[int,int]):
		actionName = self.sender().objectName().lower().strip()
		self.signal_cellMenu.emit ( {
			'action' : actionName,
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		})
		

	
	
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

	def on_selection_changed(self, selected, deselected):
		# 선택된 행들의 인덱스 가져오기
		selected_rows = set()
		for index in self.selectedIndexes():
			selected_rows.add(index.row())
			
		# 선택된 행들의 데이터를 딕셔너리 리스트로 만들어서 시그널 발생
		selected_data = []
		for row in selected_rows:
			row_data = {}
			for col, header in enumerate(self.model().header):
				row_data[header] = self.model()._data[row][col]
			selected_data.append(row_data)

		
		self.signal_select_rows.emit(selected_data)

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


	def _set_Row_Span(self, headerName:str='' , **kwargs):
		"""
		kwargs 에는 startRowNo, endRowNo, subHeader 가 있음
		subHeader 가 있으면 해당 컬럼을 기준으로 행 병합
		"""
		my_data = copy.deepcopy( self.model()._data )
		colNo = self.table_header.index(headerName)
		subHeader = subHeader if ( subHeader:= kwargs.get('subHeader', False) ) else ''

		startRowNo = kwargs['startRowNo'] if 'startRowNo' in kwargs else 0
		endRowNo = kwargs['endRowNo'] if 'endRowNo' in kwargs else None  # -1 대신 None 사용
		targetDatas = my_data[startRowNo:endRowNo]

		if not subHeader:
			row_span_cnt = 0
			for idx, row in enumerate(targetDatas):
				if idx < row_span_cnt: continue
				my_item_count = 0
				my_label = row[colNo]
				for row_rest in targetDatas[idx:]:
					if row_rest[colNo] == my_label:
						my_item_count += 1
					else: break
				if my_item_count != 1:
					self.setSpan( startRowNo+idx, colNo, my_item_count, 1)
					row_span_cnt += my_item_count
		
		else:
			sub_col_no = self.table_header.index(subHeader)
			row_span_cnt = 0
			for idx, row in enumerate(targetDatas):
				if idx < row_span_cnt: continue
				my_item_count = 0
				my_label = str( row[colNo] ) + str( row[sub_col_no] )
				for row_rest in targetDatas[idx:]:
					if (str(row_rest[colNo])+str(row_rest[sub_col_no])) == my_label:
						my_item_count += 1
					else: break
				if my_item_count != 1:
					self.setSpan( startRowNo+idx, colNo, my_item_count, 1)
					row_span_cnt += my_item_count

	# def mouseMoveEvent(self, event:QtGui.QMouseEvent):
	# 	""" hard coding으로 ..."""
	# 	super().mouseMoveEvent(event)
	# 	if not hasattr(self, 'tb') :
	# 		self.tb = QTextBrowser(self)
	# 	if not event.buttons():
	# 		index = self.indexAt(event.pos())
	# 		if  'app사용자수' == self.model().table_header [index.column()]:
	# 			self.setCursor(Qt.CursorShape.PointingHandCursor)

	# 			self.tb.setAcceptRichText(True)
	# 			self.tb.setOpenExternalLinks(True)
	# 			self.tb.append('test')

	# 			# self.tb.move(QtGui.QCursor.pos() )
	# 			# self.tb.move( self.mapToGlobal(event.pos()) )
	# 			self.tb.move( event.pos() )
	# 			self.tb.show()

	# 		else:
	# 			self.unsetCursor()
	# 			self.tb.hide()
	# 			self.tb.close()