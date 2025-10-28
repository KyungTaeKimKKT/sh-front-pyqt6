from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import operator
import pandas as pd
import copy

# import user module
from config import Config as APP
from stylesheet import StyleSheet


import modules.user.utils as utils


import traceback
from modules.logging_config import get_plugin_logger




### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Base_TableModel(QtCore.QAbstractTableModel):
	signal = pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = []):
		super().__init__()
		 
		self.url = baseURL
		
		self.header_type = header_type
		self.no_Edit = no_Edit
		self.header = header
		self._data = data if data else [['' for _ in self.header]]
		self._original_data = copy.deepcopy(self._data)


		self.ST = StyleSheet()


	def headerData(self, p_int, Qt_Orientation, role=None):

		if role == Qt.DisplayRole and Qt_Orientation==Qt.Horizontal:
			return self.header[p_int]
		else:
			return QtCore.QAbstractTableModel.headerData(self, p_int, Qt_Orientation, role)


### display 결정 : Hard-coding이 필요한 부분 ****😀😀
##################################################################################
	def data(self, index, role):
		if index.isValid():
			col = index.column()
			value = self._data[index.row()][index.column()]
			if role == Qt.DisplayRole or role == Qt.EditRole :	
				return self.user_defined_data(index, role, value)

			if role == Qt.DecorationRole:
				col = index.column()
				match self.header_type.get(self.header[col]):
					case 'QCheckBox(parent)':
						if value :
							return QtGui.QIcon(f':/icons/true.jpg')
						else:
							return QtGui.QIcon(f':/icons/false.png')
						
				match self.header[col]:
					case '첨부파일수'|'완료파일수':
						if value is not None :
							try:
								if int(value) > 0:
									return QtGui.QIcon(f':/table-decorator/files-exist')
							except:
								return value		
					
				return self.user_defined_DecorationRule( index, value)
			
			if role == Qt.TextAlignmentRole :
				return self.user_defined_TextAlignmentRole( index, value)
					
			if role == Qt.BackgroundRole:
				return self.user_defined_BackgroundRole(index, role)
			
			if role == Qt.ForegroundRole:
				return self.user_defined_ForegroundRole(index,role)

	### 😀😀😀type에 따라서 변경해야 함. hard-coding ###
	def user_defined_data(self, index:QModelIndex, role, value) :
		# col = index.column()	

		return value
	
	def user_defined_TextAlignmentRole(self, index, role) :
		col = index.column()
		match self.header_type.get(self.header[col]):
			case '___':	### QLineEdit
				return Qt.AlignVCenter | Qt.AlignCenter
			case 'QSpinBox(parent)' | 'QDoubleSpinBox(parent)':
				return Qt.AlignVCenter| Qt.AlignRight
			case 'QPlainTextEdit(parent)' | 'QTextEdit(parent)':
				return Qt.AlignVCenter| Qt.AlignLeft
			case 'QCheckBox(parent)':
				return Qt.AlignVCenter | Qt.AlignLeft
			case _:
				return  Qt.AlignVCenter | Qt.AlignCenter

	def user_defined_ForegroundRole(self, index, role):
		pass

	def user_defined_BackgroundRole(self, index, role):
		pass

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
	
	def flags(self, index):
		# col = index.column()
		# flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled 
		# if self.header[col] in self.no_Edit:
		# 	return flags
		# else:
		# 	return flags | Qt.ItemIsEditable
		global no_Edit_Row
		col = index.column()
		row = index.row()
		flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled 
		if self.header[col] in self.no_Edit:
			return flags
	
		else:
			return flags | Qt.ItemIsEditable
	
	
	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			row , col = index.row(), index.column()
			is_ok, res_json = self._api_send( ID=self._get_ID(row), data=self._get_edit_data(row, col, value))

			# Set the value into the frame.==>self._data.iloc[index.row(), index.column()] = value
			if is_ok:
				self._data[row]= self.get_data_from_response(res_json)
				# self.signal.emit({'data':'changed'})
				return True
			else:
				return False

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
	


	def _get_edit_data(self, row:int, column:int, value) ->dict:
		key =  self.header[column]

		if isinstance(value, QtCore.QDate) :
			result = value.toString('yyyy-MM-dd')
		else:
			result = value
		return { key : result}
	
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

