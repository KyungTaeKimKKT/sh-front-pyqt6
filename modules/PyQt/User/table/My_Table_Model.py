from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import operator
import pandas as pd
import copy
import json
import datetime

# import user module
from config import Config as APP
from stylesheet import StyleSheet


import modules.user.utils as utils


import traceback
from modules.logging_config import get_plugin_logger




### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class My_TableModel(QtCore.QAbstractTableModel):
	""" kwargs
		header_type : dict ==> 'fields_model'
		header : list[str],
		_data : list[list],
		no_Edit : list[str] ==> 선택적으로 no_edit, 전체면 header 로, 없으면 null or []
	"""
	signal = pyqtSignal(dict)	
	signal_data_changed = pyqtSignal(dict)

	signal_sum_changed = pyqtSignal(int)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.parentWid = parent

		self.no_Edit_cols : list[str] = []
		self.no_Edit_rows : list[int] = []
		self.no_Menu_cols : list[str] = []
		self.no_Menu_rows : list[int] = []
		self.header: list[str]
		self.header_type : dict
		self._data : list[list]

		for (key, value) in kwargs.items():		
			setattr(self, key, value)

		if not hasattr(self, 'no_Edit'):
			self.no_Edit = []

	def headerData(self, p_int, Qt_Orientation, role=None):
		if role == Qt.ItemDataRole.DisplayRole and Qt_Orientation==Qt.Orientation.Horizontal:
			return self.header[p_int]
		else:
			return QtCore.QAbstractTableModel.headerData(self, p_int, Qt_Orientation, role)


### display 결정 : Hard-coding이 필요한 부분 ****😀😀
##################################################################################
	def data(self, index, role):
		if index.isValid():
			col = index.column()
			value = self._data[index.row()][index.column()]
			if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole :	
				return self.user_defined_data(index, role, value)

			if role == Qt.ItemDataRole.DecorationRole:
				col = index.column()
				db_type =  self.header_type.get(self.header[col], 'default')

				if 'Boolean' in db_type:
					return QtGui.QIcon(f':/icons/true.jpg') if value else QtGui.QIcon(f':/icons/false.png')

				return self.user_defined_DecorationRule( index, value)

			
			if role == Qt.ItemDataRole.TextAlignmentRole :
				return self.user_defined_TextAlignmentRole( index, role, value)
					
			if role == Qt.ItemDataRole.BackgroundRole:
				return self.user_defined_BackgroundRole(index, role)
			
			if role == Qt.ItemDataRole.ForegroundRole:
				return self.user_defined_ForegroundRole(index,role)

	### 😀😀😀type에 따라서 변경해야 함. hard-coding ###
	def user_defined_data(self, index:QModelIndex, role, value) :
		"""
			self.header_type 예.. \n
			{'id': 'BigAutoField', '평가체계_fk': 'ForeignKey', '피평가자_평가체계_fk': 'ForeignKey', \n
			'is_submit': 'BooleanField', 'ability_m2m': 'ManyToManyField', 'perform_m2m': 'ManyToManyField', 'special_m2m': 'ManyToManyField',
			'차수별_점유': 'JSONField' } \n
		"""
		colNo = index.column()
		headerName = self.header[colNo] 

		match self.header_type.get(headerName, ''):
			case 'ManyToManyField':
				return str(value)
			case 'JSONField':
				return json.dumps(value, ensure_ascii=False)
			case 'DateTimeField':
				if isinstance( value, datetime.datetime) :
					return value 
				if  isinstance( value, str) and '.' in value:
					return value.split('.')[0]
				return value

			case _:
				return value
			
	
	def user_defined_TextAlignmentRole(self, index, role, value) :
		col = index.column()
		db_type =  self.header_type.get(self.header[col], 'default_center')

		match utils.get_dataType( db_type):
			case 'char':
				return  Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
			case 'integer':
				return Qt.AlignmentFlag.AlignVCenter| Qt.AlignmentFlag.AlignRight 
			case 'text' :
				return Qt.AlignmentFlag.AlignVCenter| Qt.AlignmentFlag.AlignLeft 
			case _:
				return  Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter


	def user_defined_ForegroundRole(self, index, role):
		pass

	def user_defined_BackgroundRole(self, index:QModelIndex, role):
		if hasattr(self, 'cell_menus_cols') and self.header[index.column()] in self.cell_menus_cols:
			return eval( self.cell_menus_cols_color) if hasattr(self, 'cell_menus_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkYellow))
		if hasattr(self, 'no_Edit_cols') and self.header[index.column()] in self.no_Edit_cols:
			return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
		if hasattr(self, 'no_Edit_rows') and index.row() in self.no_Edit_rows:
			return eval( self.no_Edit_rows_color) if hasattr(self, 'no_Edit_rows_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
			# return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))
		
		flags = self.flags(index)
		if not flags & Qt.ItemFlag.ItemIsEditable:
			return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))


	def user_defined_DecorationRule(self, index, value):
		pass
	############################################################################

	def rowCount(self, index):		
		# The length of the outer list.
		return len(self._data)

	def columnCount(self, index):
		if not len(self._data): return 0
		# The following takes the first sub-list, and returns
		# the length (only works if all rows are an equal length)
		return len(self._data[0])
	
	def flags(self, index:QModelIndex):
		col = index.column()
		row = index.row()
		flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled 

		if row in self.no_Edit_rows:
			return flags

		if self.header[col] in self.no_Edit_cols:
			return flags
	
		else:
			return flags | Qt.ItemFlag.ItemIsEditable
	
	def setData_QAbstractItemModel(self, index, value, role):
		return super().setData(index, value, role)

	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.ItemDataRole.EditRole:
			row , col = index.row(), index.column()
			value, api_data  =  self._get_edit_data(row, col, value)
			if self._data[row][col] == value : 
				return False
			api_data.update({'id': self._data[row][self.header.index('id')]})
			self.signal_data_changed.emit({
										'row' :row,
										'col' : col,
										'value' : value,
										'api_data' :api_data,
										})
			return True
		return False
	
		
	def sort(self, Ncol, order):
		self.layoutAboutToBeChanged.emit()
		try:
			self._data = sorted(self._data, key=operator.itemgetter(Ncol))   
		except:
			pass

		if order == Qt.DescendingOrder:
			self._data.reverse()
		self.layoutChanged.emit()

	# https://stackoverflow.com/questions/24961383/how-to-see-the-value-of-pyside-qtcore-qt-itemflag
	def is_Editable(self, flags:Qt.ItemFlags) -> bool:
		return int( Qt.ItemIsEditable ) & int(flags) == int( Qt.ItemIsEditable )


	def _api_send( self, ID:int, data:dict):
		if  ID < 0:
			return APP.API.post(self.url, data )
		else:
			return APP.API.patch(self.url+str(ID)+'/', data )
	

	def _get_row_data(self, row:int) -> dict:
		return { key : self._data[row][idx] for idx, key in enumerate(self.header)}


	def _get_edit_data(self, row:int, column:int, value) ->tuple[str, dict[str:str]]:
		key =  self.header[column]

		if isinstance(value, QtCore.QDate) :
			result = value.toString('yyyy-MM-dd')
		elif isinstance(value, QtCore.QDateTime) :
			result = value.toPyDateTime()
		else:
			result = value
		return ( value, { key : result} )
	
	def _get_ID(self, row:int) ->int:
		col = self.header.index('id')
		try :
			return int(self._data[row][col])
		except:
			return -1
	
	def get_data_from_response(self, res_json:dict) ->list:
		result = []
		for key in self.header:
			result.append( res_json.get(key))
		return result
	
	
	def is_float(self, txt:str='') -> bool:
		"""
			parameter 를 변환 try 하여 True, except False return
		"""
		try :
			a = float(txt)
			return True
		except: 
			return False

	def is_bool(self, txt:str='') -> bool:
		"""
			parameter 를 str 변환하여 글자 비교
		"""
		l_txt = txt.lower()
		if l_txt in ['true', 'false']: return True
		else: return False
		

	def calculateSum_byHeadName(self, headerName:str, **kwargs):
		""" headerName에 대한 합계"""
		# 4번째부터 마지막 -2 까지 포함하는 slicing
		startRowNo = kwargs['startRowNo'] if 'startRowNo' in kwargs else 0
		endRowNo = kwargs['endRowNo'] if 'endRowNo' in kwargs else len(self._data)
		self._calucrated_data = self._data[startRowNo:endRowNo]
		
		colNo = self.header.index(headerName)
		value_sum = sum(row[colNo] for row in self._calucrated_data if isinstance(row[colNo], (int, float)))

		self.layoutChanged.emit()

		self.signal_sum_changed.emit(value_sum)



class Base_TableModel_Pandas(QtCore.QAbstractTableModel):
	sig_update = pyqtSignal()

	def __init__(self,  baseURL:str, data:pd.DataFrame, header_type:dict={}, no_Edit:list = []):
		super().__init__()
		 
		self.url = baseURL
		self.originalData = data
		self.header_type = header_type
		self.no_Edit = no_Edit

		# self.header = self._get_header()
		self._data = data

	def _init__data(self) -> pd.DataFrame:
		return pd.DataFrame(self.originalData)
	
	def data(self, index, role):
		if role == Qt.DisplayRole:
			value = self._data.iloc[index.row(), index.column()]
			return str(value)

	def rowCount(self, index):
		return self._data.shape[0]

	def columnCount(self, index):
		return self._data.shape[1]

	def headerData(self, section, orientation, role):
		# section is the index of the column/row.
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return str(self._data.columns[section])

			if orientation == Qt.Vertical:
				return str(self._data.index[section])

