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

class TableModel_HR평가_설정(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		
		self.parentWid = parent
		

	def setData(self, index:QModelIndex, value, role:Qt.ItemDataRole):
		if role == Qt.ItemDataRole.EditRole:
			row , col = index.row(), index.column()			
			### 😀😀 HR평가_설정는 copy 한 경우에 적용: 
			row_data:dict = self._get_row_data(row)			
			value, api_data  =  self._get_edit_data(row, col, value)
			if self._data[row][col] == value : 
				return False
			self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
			return True
		return False
			
		# 	match  self.header[col]:
		# 		case 'is_검증':
		# 			if value:			
		# 				_isOk, _json = APP.API.patch( url= self.parentWid.url+  str( row_data.get('id')  ) + '/', data={'id':row_data.get('id'),  'request_검증':True}	)
		# 				if _isOk :
		# 					text = '\n'.join ( [ f" {key} : {value}" for key, value in _json.items()] )

		# 					dlg_res_button = Utils.generate_QMsg_question(self.parentWid, text = text + f"\n\nUpload한 file을 검증 완료하시겠읍니까?\n (자동으로 MASTER DB UPDATE 및 \n  개인별 할당이 진행됩니다.)")
		# 					if dlg_res_button == QMessageBox.StandardButton.Ok :
		# 						api_data.update( _json )
		# 						self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 						return True
		# 					else:
		# 						return False
		# 			else:
		# 				self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 				return True

		# 		case 'is_master적용':
		# 			if value:											
		# 				dlg_res_button = Utils.generate_QMsg_question(self.parentWid, text = f"Master DB에 적용하시겠읍니까?\n")
		# 				if dlg_res_button == QMessageBox.StandardButton.Ok :
		# 					self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 					return True
		# 				else:
		# 					return False
		# 			else:
		# 				self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 				return True
		# 		case 'is_개인별할당':
		# 			if value :
		# 				dlg_res_button = Utils.generate_QMsg_question(self.parentWid, text = f"개인별 할당 (새로운 db 생성) (으)로 진행하시겠읍니까?")
		# 				if dlg_res_button == QMessageBox.StandardButton.Ok :
		# 					self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 					return True
		# 				else:
		# 					return False
		# 			else:
		# 				self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 				return True
		# 		case 'is_시작':
		# 			if value :
		# 				res = Utils.generate_QMsg_question(self.parentWid, text = f"MBO OPEN 진행하시겠읍니까?")
		# 				if res == QMessageBox.StandardButton.Ok :
		# 					self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 					return True
		# 				else:
		# 					return False
		# 			else:
		# 				self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 				return True
		# 		case 'is_완료':
		# 			if value :
		# 				res = Utils.generate_QMsg_question(self.parentWid, text = f"MBO Close 진행하시겠읍니까?")
		# 				if res == QMessageBox.StandardButton.Ok :
		# 					self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 					return True
		# 				else:
		# 					return False
		# 			else:
		# 				self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 				return True
		# 		case _:
		# 			self._proceed_update( row_data=row_data,api_data=api_data,row=row,col=col,value=value)
		# 			return True
		# return False
	
	def _proceed_update(self, **kwargs):
		row_data:dict = kwargs['row_data']
		api_data = kwargs['api_data']
		row = kwargs['row']
		col = kwargs['col']
		value = kwargs['value']

		# if row_data.get('id', -1) == -1:
		# 	row_data.update (api_data)
		# 	api_data = copy.deepcopy(row_data)

		#########################################
		api_data.update({'id': self._data[row][self.header.index('id')]})


		self.signal_data_changed.emit({
									'row' :row,
									'col' : col,
									'value' : value,
									'api_data' :api_data,
									})

	# def user_defined_data(self, index:QModelIndex, role:int, value ) :
	# 	colNo = index.column()
	# 	rowNo = index.row()
	# 	headerName = self.header[colNo] 

	# 	if 'datetime' in self.header_type[headerName].lower()  : ### 'DateTimeField'
	# 		if not isinstance(value, str) : 
	# 			return '미정입니다....'
	# 			return QDateTime.currentDateTime().addDays(3)
	# 		else : 
	# 			return value.split('.')[0].replace('T', '  ')
	
	# 	return value
