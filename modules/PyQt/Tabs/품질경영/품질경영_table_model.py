from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing

from modules.user.api import Api_SH

from modules.PyQt.User.Tb_Model import Base_TableModel

from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger


### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 품질경영_Base_TableModel(Base_TableModel):
	signal = QtCore.pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = []):
		super().__init__( baseURL, data, header, header_type, no_Edit)

	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			row , col = index.row(), index.column()
			data = self._get_edit_data(row, col, value)
			ID = self._get_ID(row)

			match col:
				case self.header.index('의뢰여부'):
					msgBox_replay = QtWidgets.QMessageBox.question(None,
												'디자인의뢰',
												'디자인의뢰를 진행하시겠습니까?',
												QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
												QtWidgets.QMessageBox.Cancel											
												)
					if msgBox_replay != QtWidgets.QMessageBox.Ok : return False
					else:
						is_ok, res_json = self._api_send( ID=ID, data=data)
				
					if is_ok:
						self._data.pop(row)
						return True
					else:
						return False					


				case self.header.index('접수여부') :
					접수디자이너 = self._data[row][self.header.index('접수디자이너')]
					if 접수디자이너 is None : return
					msgBox_replay = QtWidgets.QMessageBox.question(None,
												'디자인접수',
												f'담당디자이너: {접수디자이너} 로 접수 진행하시겠습니까?',
												QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
												QtWidgets.QMessageBox.Cancel											
												)
					if msgBox_replay != QtWidgets.QMessageBox.Ok : return False
					else:
						data['접수디자이너']=접수디자이너
						is_ok, res_json = self._api_send( ID=ID, data=data)
				
					if is_ok:
						self._data.pop(row)
						return True
					else:
						return False	

				case self.header.index('완료여부'):
					msgBox_replay = QtWidgets.QMessageBox.question(None,
												'디자인완료',
												'디자인완료를 진행하시겠습니까?',
												QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
												QtWidgets.QMessageBox.Cancel											
												)
					if msgBox_replay != QtWidgets.QMessageBox.Ok : return False
					else:
						is_ok, res_json = self._api_send( ID=ID, data=data)
					
					if is_ok:
						self._data.pop(row)

					# self.signal.emit({'data':'changed'})
						return True
					else:
						return False


				case _:
					is_ok, res_json = self._api_send( ID=ID, data=data)
								# Set the value into the frame.==>self._data.iloc[index.row(), index.column()] = value
					if is_ok:
						self._data[row]= self.get_data_from_response(res_json)
						# self.signal.emit({'data':'changed'})
						return True
					else:
						return False

		return False



	##########################################################################3
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
			case '첨부파일수'|'완료파일수':
				if value is not None:
					if int(value) > 0:
						return QtGui.QIcon(f':/table-decorator/files-exist')
				
			case '현장명':
				pass



			# case 6:
			#     return str(value).split('T')[1]
			# case 7:
			#     return str(value).capitalize()
			
			case _:
				return value
	############################################################################

	def user_defined_BackgroundRole(self, index, role):
		pass
		# global no_Edit_Row 
		# if index.row() in no_Edit_Row:
		# 	return QtGui.QColor(self.ST.COLOR_edit_disable )
	

	def _get_edit_data(self, row:int, column:int, value) ->dict:
		key =  self.header[column]
		ID = self._get_ID(row)
		data = {}

		if  ID  < 0:				
			data.update ( {'일자':self._data[row][self.header.index('일자')] } )
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
	
		else:
			return flags | Qt.ItemIsEditable