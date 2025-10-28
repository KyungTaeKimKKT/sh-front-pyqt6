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

from modules.PyQt.User.object_value import Object_Set_Value, Object_Diable_Edit, Object_ReadOnly, Object_Get_Value

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

TABLE_NAME = '샘플의뢰_의장'
HOVER_LIST = []

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class TableModel_샘플의뢰_의장(My_TableModel):
	signal_data_changed = pyqtSignal(dict)
	signal_isChamro_changed = pyqtSignal(dict)

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		
		self.parentWid = parent
		
	### 😀 No API SEND ==> ORIGINAL임
	def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
		if role == Qt.ItemDataRole.EditRole:
			# 유효한 인덱스인지 확인
			if not index.isValid():
				return False
			
			# 데이터 수정
			self._data[index.row()][index.column()] = value
			
			# 데이터가 변경되었음을 알림
			self.dataChanged.emit(index, index)
			return True
		return False
	
	def user_defined_BackgroundRole(self, index:QModelIndex, role):
		if hasattr(self, 'cell_menus_cols') and self.header[index.column()] in self.cell_menus_cols:
			return eval( self.cell_menus_cols_color) if hasattr(self, 'cell_menus_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkYellow))
		if hasattr(self, 'no_Edit_cols') and self.header[index.column()] in self.no_Edit_cols:
			return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
		if hasattr(self, 'no_Edit_rows') and index.row() in self.no_Edit_rows:
			return eval( self.no_Edit_rows_color) if hasattr(self, 'no_Edit_rows_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
			# return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))
		
		평가자_ID_cols = [ index   for index, head in enumerate(self.header) if '평가자_ID' in head and '0' not in head ]
		row , col = index.row(), index.column()
		if col in 평가자_ID_cols:
			if index.data() == -1:
				return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkRed))

class TableView_샘플의뢰_의장(My_TableView):
	signal_hover = pyqtSignal(bool, int, str, QPoint)
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)


from modules.PyQt.component.combo_lineedit_v2 import 샘플의뢰_Table_소재종류, 샘플의뢰_Table_소재Size
from modules.PyQt.component.textedit.textedit_with_contextmenu import TextEdit_ContextMenu
class Delegate_샘플의뢰_의장(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		self._items = {
			'작업형태' :  ['A 시편','B ~NCT', 'C ~절곡', 'D ~조립', 'E ~설치'] ,
			'제작형태' :  ['F 불요','G Book', 'H Board'],
			'소재종류' :  ['GI', 'POSMAC', 'SUS', '기타'], 
			'소재Size' :  ['1.5T*150*150', '1.5T*300*300', '기타'] ,
			'단위'     :  ['장', 'set', '대'] ,
		}

	def user_defined_creatorEditor_설정(self, widget:object, **kwargs) -> object:
		match kwargs['key']:
			case '작업형태'|'제작형태'|'단위':
				widget = QComboBox( kwargs['parent'])
				widget.addItems ( self._items[ kwargs['key'] ])
			case '소재종류':
				widget = 샘플의뢰_Table_소재종류( kwargs['parent'], items= self._items[ kwargs['key'] ])
			case '소재Size':
				widget = 샘플의뢰_Table_소재Size( kwargs['parent'], items= self._items[ kwargs['key'] ])
			case '상세Process' :
				widget = TextEdit_ContextMenu( kwargs['parent'] )

		return widget
	
	def setModelData(self, editor, model, index):
		value = Object_Get_Value(editor).get()
		model.setData(index, value, Qt.ItemDataRole.EditRole)


class Wid_Table_for_샘플의뢰_의장(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_appData_Changed = pyqtSignal(dict)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )		
		self.tableView:  TableView_샘플의뢰_의장
		self.table_model : TableModel_샘플의뢰_의장
		self.delegate : Delegate_샘플의뢰_의장


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

		for (key, value) in kwargs.items():
			setattr(self, key, value )
		self.api_data : list[dict]		

		self.info = INFO()

		### header_type 는 DB_FIELDS + SERIALIZER_APPEND
		self.header_type = copy.deepcopy(self.fields_model)
		self.header_type.update(self.fields_append)

		if  hasattr(self, 'table_config') and ( table_header:=self.table_config.get('table_header', None) ):			
			self.table_header =table_header
		else:
			self.table_header = list( self.header_type.keys() )

		self.run()


	def _search_in_model_data(self, search:str):
		if len(search) == 0 : 
			for rowNo, rowData in enumerate(self.model_data) :
				self.tableView.showRow(rowNo)

		search_rows:list[int] = []
		for rowNo, rowData in enumerate(self.model_data) :
			rowData : list
			for data in rowData:
				if search in str(data) and rowNo not in search_rows:
					search_rows.append ( rowNo )

		for rowNo, _ in enumerate(self.model_data):
			if rowNo in search_rows:
				self.tableView.showRow(rowNo)
			else:
				self.tableView.hideRow(rowNo)

	def _get_Model_data(self) -> list[dict]:
		sendData = []
		for rowNo, rowData in enumerate( self.model_data ):
			data = { headerName: rowData[index] for index, headerName in enumerate(self.table_header) }
			data['표시순서'] = rowNo
			sendData.append ( data )
		return sendData

	
	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vLayout_main'):

			Utils.deleteLayout(self.vLayout_main)
		self.UI()
		if len(self.api_data) == 0:
			self.api_data = self._generate_default_api_datas()
		self.model_data = self.gen_Model_data_from_API_data()

		###😀😀
		# self._modity_table_config()
		self.table_model = eval ( f"""TableModel_{TABLE_NAME}(
					parent = self,
					header_type = self.header_type,
					header = self.table_header,
					_data = self.model_data,
					**self.table_config,					
				)""")


		self.tableView.setModel ( self.table_model)
		self.tableView.setConfig ( **self.table_config  )
		self.delegate = eval ( f"""Delegate_{TABLE_NAME}(
						self, 
						header_type=self.header_type,  
						**self.table_config
						)""")
		self.tableView.setItemDelegate(self.delegate)

		#### table delegate signal handler
		self.delegate.closeEditor.connect(self.slot_delegate_closeEditor)

		### tableView signal handler
		self.tableView.signal_vMenu.connect(self.slot_signal_vMenu )
		self.tableView.signal_hMenu.connect(self.slot_signal_hMenu )
		self.tableView.signal_cellMenu.connect(self.slot_signal_cellMenu)

		### tableModel signal handler
		self.table_model.signal_data_changed.connect( self.slot_signal_model_data_changed )
		self.table_model.signal_isChamro_changed.connect ( self.slot_model_isChamro_changed )
	
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
	def slot_model_isChamro_changed(self, msg:dict):
		"""
			msg {'row': 111, 'col': 5, 'value': False, 'api_data': {'is_참여': False, 'id': 1644}}
		"""

		sendData :dict = msg['api_data']
		ID =sendData.pop('id')
		_isOK, _json = APP.API.Send ( url=self.url, dataObj={'id': ID}, sendData = sendData )
		if _isOK:
			model_datas = self.tableView.model()._data	
			model_datas[msg.get('row')][msg.get('col')] =  msg.get('value')
			self.tableView.model().endResetModel()
		else:
			Utils.generate_QMsg_critical(self)
	

	@pyqtSlot(dict)
	def slot_signal_model_data_changed(self, msg:dict):
		""" 
			msg = {'row': 0, 'col': 10, 'value': '20', 'api_data': {'1_평가자_ID': '20', 'id': 40}} 형태
			override : 변화된 것을 받아서, m2m filed 처럼 만들어서  api send			
		"""
		api_data = msg.get('api_data')
		평가자_ID:int = self._get_평가자ID(api_data)

		user_info = self.info._get_user_info( pk = 평가자_ID )	
		if not len(list(user_info.keys() )) > 0:
			Utils.generate_QMsg_critical( self, title='평가자 ID 오류', text =f'평가자 ID {str(평가자_ID)}는 존재하지 않읍니다' )
			return 

		model_datas = self.tableView.model()._data	
		성명_col_name = str( self.table_header[msg.get('col')] ).replace('_ID', '_성명')
		성명_col = self.table_header.index (성명_col_name)

		_isOK, _json = APP.API.Send ( url=self.url, dataObj=api_data, sendData={'평가자': 평가자_ID} )
		if _isOK:
			self.tableView.model().beginResetModel()

			model_datas[msg.get('row')][msg.get('col')] =  평가자_ID
			model_datas[msg.get('row')][성명_col] = user_info.get('user_성명')
			self.tableView.model().endResetModel()
			# self.signal_appData_Changed.emit(_json)
		else:





	def _generate_default_api_datas(self) ->list[dict]:		
		table_header:list[str] = self.table_config['table_header']
		obj = {}
		for header in table_header:
			if header == 'id' : obj[header] = -1
			else:
				match self.fields_model.get(header, '').lower():
					case 'charfield'|'textfield':
						obj[header] = ''
					case 'integerfield'|'floatfield':
						obj[header] = 0
					case 'datetimefield':
						# return QDateTime.currentDateTime().addDays(3)
						obj[header] =  datetime.now()
					case 'datefield':
						# return QDate.currentDate().addDays(3)
						obj[header] =  datetime.now().date()
					case 'timefield':
						# return QTime.currentTime()
						obj[header] = datetime.now().time()
					case _:
						obj[header] = ''
		return [ obj ]