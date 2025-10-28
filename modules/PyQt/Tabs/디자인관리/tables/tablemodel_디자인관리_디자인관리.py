from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import date, datetime
import concurrent.futures

import pathlib
import typing
import copy
import json

from modules.PyQt.User.table.My_Table_Model import My_TableModel

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableModel_디자인관리(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		
		self.parentWid = parent
	
	def setData(self, index:QModelIndex, value, role:Qt.ItemDataRole):
		if role == Qt.ItemDataRole.EditRole:
			row , col = index.row(), index.column()			
			### 😀😀 디자인관리는 copy 한 경우에 적용: 
			row_data:dict = self._get_row_data(row)			
			value, api_data  =  self._get_edit_data(row, col, value)
			
			match  self.header[col]:
				case '의뢰여부':
					if value:											
						dlg_res_button = Utils.generate_QMsg_question(self.parentWid, text = f" 의뢰 진행하시겠읍니까?\n(진행하시면 더이상 수정은 못하고, 이력조회에서 진행현황 조회가능합니다.)")
						if dlg_res_button == QMessageBox.StandardButton.Ok :
							api_data['의뢰일'] = datetime.now()
							self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
							return True
						else:
							return False
					else:
						self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
						return True
				case '접수여부':
					if value :
						dlg_res_button = Utils.generate_QMsg_question(self.parentWid, text = f" [디자이너 : {row_data.get('접수디자이너')} ] (으)로 진행하시겠읍니까?")
						if dlg_res_button == QMessageBox.StandardButton.Ok :
							api_data['접수일'] = datetime.now()
							api_data['designer_fk'] = [ user['id'] for user in INFO.ALL_USER if user['user_성명']== row_data.get('접수디자이너') ][0] if hasattr(self, '접수디자이너list') else -1
							self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
							return True
						else:
							return False
					else:
						self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
						return True
				case '완료여부':
					if value :
						res = Utils.generate_QMsg_question(self.parentWid, text = f"완료로 진행하시겠읍니까?")
						if res == QMessageBox.StandardButton.Ok :
							api_data['완료일'] = datetime.now()
							self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
							return True
						else:
							return False
					else:
						self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
						return True
				case _:
					self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
					return True
		return False
	
	def _proceed_update(self, **kwargs):
		row_data:dict = kwargs['row_data']
		api_data = kwargs['api_data']
		row = kwargs['row']
		col = kwargs['col']
		value = kwargs['value']

		if row_data.get('id', -1) == -1:
			row_data.update (api_data)
			api_data = copy.deepcopy(row_data)
			del api_data['의뢰일']
		#########################################
		api_data.update({'id': self._data[row][self.header.index('id')]})


		self.signal_data_changed.emit({
									'row' :row,
									'col' : col,
									'value' : value,
									'api_data' :api_data,
									})

	def user_defined_data(self, index:QModelIndex, role:int, value ) :
		colNo = index.column()
		rowNo = index.row()
		headerName = self.header[colNo] 

		if 'datetime' in self.header_type[headerName].lower()  : ### 'DateTimeField'
			if not isinstance(value, str) : 
				return '미정입니다....'
				return QDateTime.currentDateTime().addDays(3)
			else : 
				return value.split('.')[0].replace('T', '  ')
	
		return value

	def flags(self, index:QModelIndex):
		flags = super().flags( index)		
		rowNo, colNo = index.row(), index.column()

		if '접수여부' ==  self.header[colNo] :		
			colNo_접수디자이너 = self.header.index('접수디자이너')
			if self._data[rowNo][colNo_접수디자이너] :
				return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
			else: 
				return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled 
			
		return flags