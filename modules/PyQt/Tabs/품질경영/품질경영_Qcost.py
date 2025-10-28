from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing
from operator import itemgetter
import copy

# import user module



from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.User.Tb_Model import Base_TableModel
from modules.PyQt.User.Tb_Delegate import Base_Delegate
from modules.PyQt.Tabs.Base import Base_App

from stylesheet import StyleSheet

from modules.PyQt.User.toast import User_Toast
from config import Config as APP

# import sub window
from modules.PyQt.sub_window.win_search import Win_Search

from modules.PyQt.User.object_value import Object_Get_Value

from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit,  Material_Widget

# 😀😀😀😀😀
from modules.PyQt.Tabs.작업지침서.Datas.Datas import AppData_작업지침서_Process as AppData
import modules.user.utils as Utils

from info import Info_SW
INFO = Info_SW()
from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger

ST = StyleSheet()

no_Edit_Row = [ 0 ]

DEFAULT_QCOST_DATA = {
	'id' : -1,
	'합계' : 0,
	'소재비' : 0,
	'의장비' : 0,
	'코팅비' : 0,
	'판금비' : 0,
	'운송비' : 0,
	'설치비' : 0,
}
	

### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(Base_TableModel):
	signal = QtCore.pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = []):
		super().__init__( baseURL, data, header, header_type, no_Edit)
		self.h_header = None
		

	def headerData(self, p_int, Qt_Orientation, role=None):

		if role == Qt.DisplayRole and Qt_Orientation==Qt.Horizontal:
			return self.header[p_int]
		elif role == Qt.DisplayRole and Qt_Orientation==Qt.Vertical:
			if self.h_header is not None: 	
				return self.h_header[p_int]
		# 	else : 
		# else:
		# 	return QtCore.QAbstractTableModel.headerData(self, p_int, Qt_Orientation, role)
		return QtCore.QAbstractTableModel.headerData(self, p_int, Qt_Orientation, role)

	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			row , col = index.row(), index.column()			
			# data = self._get_edit_data(row, col, value)
			self._data[row][col] = value

			self.user_change_합계()
			return True

		return False

	
	##########################################################################3
	def user_change_합계(self):
		합계 = 0
		for row in range( len(self._data) ):
			if row == 0 : continue
			합계 += int (self._data[row][0])
		self._data[0][0] =  합계


	def user_defined_data(self, index:QModelIndex, role, value) :
		return value
		
	def user_defined_DecorationRule(self, index, value):
		
		row = index.row()
		col = index.column()

		match self.header_type.get(self.header[col]):
			case 'QCheckBox(parent)':
				if value :
					return QtGui.QIcon(f':/icons/true.jpg')
				else:
					return QtGui.QIcon(f':/icons/false.png')

		
		match self.header[col]:
			case '제목':
				col = self.header.index('수량')
				el수량 = self._data[row][col]
				if el수량 is None : return
				if int(el수량) > INFO._get_작업지침서_중요도():
					return  QtGui.QIcon(f':/table-decorator/디자인의뢰-중요')
			
			case _:
				return value
	############################################################################

	def user_defined_BackgroundRole(self, index, role):
		global no_Edit_Row 
		if index.row() in no_Edit_Row:
			return QtGui.QColor("yellow" )

	def user_defined_ForegroundRole(self, index, role):
		row = index.row()
		col = index.column()
		match self.header[col]:
			case '상세Process':
				if not len( index.data() ): return 
				중요도index = self._get_column_중요도(col_key='상세Process', data=index.data() )
				중요도_attr:dict = getattr(ST, f"작지_중요도{중요도index+1}", None)
				if 중요도_attr is None : return
				return QtGui.QColor(중요도_attr.get('fg'))


	def _get_edit_data(self, row:int, column:int, value) ->dict:
		key =  self.header[column]
		ID = self._get_ID(row)
		data = {}
		if isinstance(value, QtCore.QDate) :
			result = value.toString('yyyy-MM-dd')
		else:
			result = value
		data.update( { key : result} )
		return data

	def flags(self, index):
		global no_Edit_Row
		col = index.column()
		row = index.row()
		flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled 
		if self.header[col] in self.no_Edit:
			return flags
		elif row in no_Edit_Row and self.header[col] not in ['Material']:
			return flags

		else:
			return flags | Qt.ItemIsEditable



class App_TableView( My_TableView):
	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ...) -> None: 
		super().__init__(parent)


### app 마다 hardcoding : 😀	
class App_Delegate(Base_Delegate):	
	def __init__(self, header:list=[], header_type:dict={} ,no_Edit:list = []):
		super().__init__(header, header_type, no_Edit)
		self.appData = AppData()

	#😀 custome widget일 때
	def setModelData(self, editor, model, index) -> None:
		super().setModelData(editor, model, index)

	
	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	#😀 각 app마다 custome widget일 때 지정할 것..
	def user_defined_cratorEditor(self, parent, value:str='') ->QtWidgets.QWidget|None:
		if value:
			return eval(value)
		else:
			return None

	def user_defined_setEditorData(self, widget, index):
		row, col = index.row(), index.column()
		text = (index.data(Qt.EditRole) or index.data(Qt.DisplayRole))	
		if isinstance(widget, QSpinBox ):
			widget.setRange(0,1000000000)
		pass


	### modify widgets
	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:		
		return widget




class QCost(QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,  app_DB_data:list=[]):
		super().__init__( parent )
		
		self.no_Edit =[]
		self.app_DB_data = app_DB_data if app_DB_data else DEFAULT_QCOST_DATA
		self.header_type = { '금액':'QSpinBox(parent)'}
		
		self.url = ''
		self.h_header = self.get_h_header()
		self.original_model_data = []
	
	def UI(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.tableView = App_TableView(self)
		self.vlayout.addWidget(self.tableView)		
		self.setLayout(self.vlayout)

	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vlayout') : Utils.deleteLayout(self.vlayout)

		self.UI()
		if self.get_api_and_model_table_generate():
			pass
		else:
			User_Toast(self, text='server not connected', style='ERROR')

	def _setReadOnly(self):
		"""
			table을  ReadOnly로
		"""
		self.no_Edit = self.header

	def get_Api_data(self) -> dict:
		if Utils.compare_list (self.original_model_data, self.model._data) :
			return {}
		result = self.app_DB_data
		for row, key in enumerate(self.model.h_header):
			result[key] = self.model._data[row][0]
		return result
	
	def get_h_header(self) ->list:
		""" DEFAULT_QCOST_DATA KEY로 순서를 만듬"""
		h_header = list(DEFAULT_QCOST_DATA.keys() )
		h_header.remove('id')
		return h_header

	def get_api_and_model_table_generate(self) -> bool:
		if self.app_DB_data:
			### 😀 self.app_DB_data sorting
			### https://stackoverflow.com/questions/72899/how-to-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary-in-python
			# try:
			# 	self.app_DB_data = sorted(self.app_DB_data, key=itemgetter('표시순서'), reverse=False)
			# except:
			# 	pass
			self.original_model_data = self.gen_Model_data_from_API_data()
			self.model_data = copy.deepcopy(self.original_model_data)

			self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
										header_type=self.header_type, no_Edit=self.no_Edit)
			# h_header = list(self.app_DB_data.keys())
			# h_header.remove('id')
			# h_header.remove('NCR_fk')
			self.model.h_header = self.h_header
			
			# tableView, vlayout = self._render_frame_MVC(App_TableView(self))
			self.table:App_TableView = self._gen_table(self.tableView)

			### setting table delegate
			self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
			self.table.setItemDelegate(self.delegate)
			

			return True
		else:
			return False

	def gen_Model_data_from_API_data(self) ->list[list[str]]:  	
		""" h_header 순서대로 model data생성"""	
		self.header = ['금액']
		_data = [
			[self.app_DB_data.get(h_headerName)] for h_headerName in self.h_header
		]
		return _data
			
	def _gen_table(self, table:App_TableView):
		table.setModel(self.model)
		table.resizeColumnsToContents()
		table.resizeRowsToContents()
		# https://stackoverflow.com/questions/38098763/pyside-pyqt-how-to-make-set-qtablewidget-column-width-as-proportion-of-the-a
		header = table.horizontalHeader()    
		header.setDefaultAlignment( Qt.AlignCenter)   
		# header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
		return table





