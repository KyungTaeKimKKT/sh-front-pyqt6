from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing
import copy
import json


# import user module
from modules.PyQt.User.table.My_Table_Model import My_TableModel
from modules.PyQt.User.table.My_tableview import My_TableView
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST


class Wid_Table_for_User관리(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_appData_Changed = pyqtSignal(dict)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		
		####  필수 : 😀 Data.py에서 class attr,value 읽어와 self attribut setting
		# self.appData = AppData()
		# self._init_Attributes_from_DataModule()
		# ####################################

		# self.첨부파일_Key = "첨부file_fks"
		self.tableView: My_TableView


	def UI(self):
		self.vLayout_main = QVBoxLayout()
		self.tableView = My_TableView(self)
		self.vLayout_main.addWidget(self.tableView)		
		self.setLayout(self.vLayout_main)
		
	def _update_data(self, **kwargs):
		""" kwargs : 
			#😀 db data
			api_data = list[dict]
			url = str
			#😀 DB_Field에서 가져온것
			fields_model = { name: type },
			fields_append = { name: type }, 
			fields_delete = { name: type },
			table_config = {
				'table_header' : list if not db_fields.keys(),
				'no_Edit_cols : list[str] => str은 table_header 의 element name,
				'hidden_columns' : list[str],
				....

			}
		"""
		self.api_data : list[dict]
		self.url : str
		self.fields_model :dict[str:str]
		self.fields_append :dict[str:str]
		self.fields_delete :dict[str:str]
		self.table_config :dict
		self.m2m_keyName : str

		for (key, value) in kwargs.items():
			setattr(self, key, value )
		self.api_data : list[dict]		

		### header_type 는 DB_FIELDS + SERIALIZER_APPEND
		self.header_type = copy.deepcopy(self.fields_model)
		self.header_type.update(self.fields_append)

		if  hasattr(self, 'table_config') and ( table_header:=self.table_config.get('table_header', None) ):			
			self.table_header =table_header
		else:
			self.table_header = list( self.header_type.keys() )

		self.run()



	
	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vLayout_main'):

			Utils.deleteLayout(self.vLayout_main)
		self.UI()
		self.model_data = self.gen_Model_data_from_API_data()

		self.table_model = My_TableModel(
					parent = self,
					header_type = self.header_type,
					header = self.table_header,
					_data = self.model_data,
					**self.table_config,
					# no_Edit_cols = self.no_Edit_cols if hasattr(self, 'no_Edit_cols') else [],
				)


		self.tableView.setModel ( self.table_model)
		self.tableView.setConfig ( **self.table_config  )
		self.delegate = My_Table_Delegate(self, header_type=self.header_type,  **self.table_config)
		self.tableView.setItemDelegate(self.delegate)

		#### table delegate signal handler
		self.delegate.closeEditor.connect(self.slot_delegate_closeEditor)

		### tableView signal handler
		self.tableView.signal_vMenu.connect(self.slot_signal_vMenu )
		self.tableView.signal_hMenu.connect(self.slot_signal_hMenu )
		self.tableView.signal_cellMenu.connect(self.slot_signal_cellMenu)

		### tableModel signal handler
		self.table_model.signal_data_changed.connect( self.slot_signal_model_data_changed )
	
	def gen_Model_data_from_API_data(self, api_DB_data:list[dict]=[] ) ->list[list]:  		
		api_DB_data = api_DB_data if api_DB_data else self.api_data
		
		_data = []
		for obj in api_DB_data:
			_data.append ( self.get_table_row_data(obj) )
		return _data
	
	def get_table_row_data(self, obj:dict) -> list:
		return [ self._get_table_cell_value(key, obj) for key in self.table_header ]
		
	def _get_table_cell_value(self, key:str, obj:dict) ->str:
		""" """
		value = obj.get(key , None)
		return value
###############################################################################################

	@pyqtSlot(dict)
	def slot_signal_model_data_changed(self, msg:dict):
		""" 
			override : 변화된 것을 받아서, m2m filed 처럼 만들어서  api send			
		"""
		model_datas = self.tableView.model()._data
		
		user_pks:list = self.app_Dict.get(self.m2m_keyName)
		ID = msg.get('api_data').get('id')
		사용유무 = msg.get('api_data').get('사용유무')
		if 사용유무 :
			if ID in user_pks:
				pass
			else:
				user_pks.append(ID)
		else:
			if ID in user_pks:
				user_pks.remove(ID)
			else:
				pass

		_isOK, _json = APP.API.Send ( url=self.url_APP설정, dataObj=self.app_Dict, sendData={self.m2m_keyName: user_pks} )
		if _isOK:
			self.tableView.model().beginResetModel()

			model_datas[msg.get('row')][msg.get('col')] =  사용유무
			self.tableView.model().endResetModel()
			self.signal_appData_Changed.emit(_json)
		else:



	### h_Menu : select all

	def menu__select_all(self, msg:dict) :
		model_datas = self.tableView.model()._data
		colNo = msg.get('col')
		headerName = self.table_header[colNo]
		user_pks:list = self.app_Dict.get(self.m2m_keyName)
		match headerName:
			case '사용유무':				
				ids = [ obj.get('id') for obj in self.api_data if obj.get('id') != 1 ]
				user_pks = list (set( user_pks + ids ) )
				_isOK, _json = APP.API.Send ( url=self.url_APP설정, dataObj=self.app_Dict, sendData={self.m2m_keyName: user_pks} )
				if _isOK:
					self.tableView.model().beginResetModel()
					for rowList in model_datas:
						rowList[colNo] = True
					self.tableView.model().endResetModel()
					self.app_Dict = _json
					# self.run()
					self.signal_appData_Changed.emit(_json)
				else:
					Utils.generate_QMsg_critical(self, title='DB error', text='확인후 다시 시도해 주십시요')
			case _:
				pass



	def menu__unselect_all(self, msg:dict) :
		model_datas = self.tableView.model()._data

		colNo = msg.get('col')
		headerName = self.table_header[colNo]
		user_pks:list = self.app_Dict.get(self.m2m_keyName)
		match headerName:
			case '사용유무':
				ids = [ obj.get('id') for obj in self.api_data if obj.get('id') != 1 ]
				user_pks = [  user_pk for user_pk in user_pks if user_pk not in ids  ] 
				if 1 not in user_pks: user_pks = [1] + user_pks

				_isOK, _json = APP.API.Send ( url=self.url_APP설정, dataObj=self.app_Dict, sendData={self.m2m_keyName: user_pks} )
				if _isOK:
					self.tableView.model().beginResetModel()
					for rowList in model_datas:
						rowList[colNo] = False
					self.tableView.model().endResetModel()
					self.app_Dict = _json
					# self.run()
					self.signal_appData_Changed.emit(_json)
				else:
					Utils.generate_QMsg_critical(self, title='DB error', text='확인후 다시 시도해 주십시요')

			case _:
				pass

	def _search_table(self, search:str):
		def _is_search ( rowData:list, search:str):
			for cellData in rowData:
				if search.lower() in str(cellData):
					return True
			return False
		
				
		model_data = self.tableView.model()._data
		
		if len(search) == 0:
			for row, _ in enumerate(model_data):
				self.tableView.showRow(row)
			return 

		showRows:list[int] = []
		hideRows:list[int] = []
		for index, rowData in enumerate(model_data):
			if _is_search ( rowData, search):
				showRows.append (index)
			else :
				hideRows.append ( index )
		
		if len(showRows) :
			for row in showRows:
				self.tableView.showRow(row)
		if len(hideRows):
			for row in hideRows:
				self.tableView.hideRow(row)

		