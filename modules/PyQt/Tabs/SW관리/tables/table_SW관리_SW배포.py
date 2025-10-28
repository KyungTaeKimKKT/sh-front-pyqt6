from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime
import concurrent.futures

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
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

TABLE_NAME = 'SW배포'
HOVER_LIST = []

class TableModel_SW배포(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		

	def setData(self, index, value, role):
		if role == Qt.ItemDataRole.EditRole:
			row , col = index.row(), index.column()
			
			### 😀😀 SW배포는 copy 한 경우에 적용: 
			row_data:dict = self._get_row_data(row)			
			value, api_data  =  self._get_edit_data(row, col, value)
			if row_data.get('id', -1) == -1:
				row_data.update (api_data)
				api_data = copy.deepcopy(row_data)
			#########################################
			api_data.update({'id': self._data[row][self.header.index('id')]})

			if '버젼' in api_data and isinstance( api_data['버젼'], (float)):
				api_data['버젼'] = round ( api_data['버젼'], 2)

			self.signal_data_changed.emit({
										'row' :row,
										'col' : col,
										'value' : value,
										'api_data' :api_data,
										})
			return True
		return False

	def user_defined_data(self, index:QModelIndex, role:int, value ) :
		colNo = index.column()
		rowNo = index.row()
		headerName = self.header[colNo] 
		match headerName:
			case '일자':
				if not isinstance(value, str) : return '...'
				# return '미리보기' if len(value) and not '내용이 없읍니다.'in value else '내용이 없읍니다.'		
		return value

class TableView_SW배포(My_TableView):
	signal_hover = pyqtSignal(bool, int, str, QPoint)
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
	
	def mouseMoveEvent(self, event:QtGui.QMouseEvent):
		""" hard coding으로 ..."""
		super().mouseMoveEvent(event)

		if not event.buttons():
			index = self.indexAt(event.pos())
			try:				
				id_idx = self.table_header.index('id')
				ID = self.model()._data[index.row()][id_idx]
			except:
				ID = -1

			hoverName = self.model().table_header [index.column()]
			if  hoverName in HOVER_LIST:
				self.setCursor(Qt.CursorShape.PointingHandCursor)
				if ID != -1:
					self.signal_hover.emit( True, ID, hoverName,QtGui.QCursor.pos() )
			else:
				self.unsetCursor()				
				self.signal_hover.emit( False, ID, hoverName, QtGui.QCursor.pos() )

class Delegate_SW배포(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	# def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex, **kwargs) -> None:
	# 	if '일' in kwargs['key'] and kwargs['value'] is None and isinstance(editor, QDateEdit):
	# 		editor.setDate( datetime.now().date() )



class Wid_Table_for_SW배포(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_SW배포
		self.table_model : TableModel_SW배포
		self.delegate : Delegate_SW배포

		self.dlg_hover_app사용자 = self._init_dlg_Hover()

	def _init_dlg_Hover(self) -> QDialog:
		dlg = QDialog(self)
		dlg.setFixedSize( 600, 600)
		vLayout = QVBoxLayout()
		self.dlg_tb = QTextBrowser(self)
		self.dlg_tb.setAcceptRichText(True)
		self.dlg_tb.setOpenExternalLinks(True)
		vLayout.addWidget(self.dlg_tb)
		dlg.setLayout(vLayout)
		dlg.hide()

		return dlg

	def UI(self):
		self.vLayout_main = QVBoxLayout()
		self.tableView = eval(f"TableView_{TABLE_NAME}(self)")
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
		self.tableView.signal_hover.connect(self.slot_signal_hover)

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

	### 😀😀 table 마다 hard coding
	@pyqtSlot(bool, int, str, QPoint) ### show 여부, rowNo와 mouse QPoint)
	def slot_signal_hover(self, is_show:bool, ID:int, hoverName:str, position:QPoint ):
		if ID <1 : return 
		if is_show:			
			if ( app_data_dict := self._get_apiDict_by_ID(ID) ):
				match hoverName:
					case '내용':
						self.dlg_hover_app사용자.setWindowTitle( f" {app_data_dict.get('제목')} ")
						self.dlg_tb.clear()
						self.dlg_tb.setText ( app_data_dict.get(hoverName))
					### m2m filed로 조회
					case 'file수':
						self.dlg_hover_app사용자.setWindowTitle( f" {app_data_dict.get('제목')} ")
						self.dlg_tb.clear()
						futures = []
						with concurrent.futures.ThreadPoolExecutor() as executor:
							for file_id in  app_data_dict.get('files'):
								futures.append( executor.submit (APP.API.getObj , INFO.URL_요청사항_FILE, file_id )  )
						for future in futures:
							self.dlg_tb.append ( future.result()[1].get('file'))

		self.dlg_hover_app사용자.move(position.x()+INFO.NO_CONTROL_POS, position.y() )
		self.dlg_hover_app사용자.setVisible(is_show)
		# if INFO.IS_DebugMode :

		

	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__공지내용_수정(self, msg:dict) -> None:
		return 
		row = msg.get('row')
		obj:dict = self.api_data[row]

		dlg = Dialog_공지내용_수정(self, obj=obj) ### parent 없이 별도 widget으로
		# dlg._update_Text(obj.get('공지내용',''))

		dlg.signal_accepted.connect (self.slot_dlg_text_changed  )

	@pyqtSlot(dict)
	def slot_dlg_text_changed(self, obj:dict) :		
		_isOk, _json = APP.API.Send( self.url, obj, obj )
		if _isOk:
			self.signal_refresh.emit()



	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, SW배포은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_SW배포
		model_datas:list[list] = self.tableView.model()._data

		new_data = self._create_new(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

	def _create_new(self, data:list) -> list:
		""" 
			app 마다 상이하므로, overwrite 할 것.
		"""
		copyed = []
		for index,value in enumerate(data):
			if index == self.table_header.index('id'):
				copyed.append(-1)
				continue

			if isinstance(value, str):
				copyed.append('')
			elif isinstance(value, bool):
				copyed.append(False)
			elif isinstance(value, (int,float)):
				copyed.append(0)
			else:
				copyed.append('')

		return copyed
	
	def menu__upgrade_row(self, msg:dict) ->None:
		"""
			copy msg.get('row') 하여 insert 함, SW배포은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_SW배포
		model_datas:list[list] = self.tableView.model()._data

		new_data = self._create_upgrade(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

	def _create_upgrade(self, data:list) -> list:
		""" 
			app 마다 상이하므로, overwrite 할 것.
		"""
		copyed = []
		for index,value in enumerate(data):
			
			if index == self.table_header.index('id'):
				copyed.append(-1)
				continue
			elif index == self.table_header.index('버젼'):
				copyed.append(float(value)+0.01)
				continue
			elif index == self.table_header.index('file'):
				copyed.append( '')
				continue
			elif index == self.table_header.index('변경사항'):
				copyed.append( '')
				continue


			if isinstance(value, str):
				copyed.append(value)
			elif isinstance(value, bool):
				copyed.append(False)
			elif isinstance(value, (int,float)):
				copyed.append(value)
			else:
				copyed.append('')

		return copyed
	
	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__file_upload(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		fName = Utils._getOpenFileName_only1( self, initialFilter = 'ZIP File(*.zip)' )
		if fName:
			modelDataDict = self.table_model._get_row_data(msg.get('row'))
			sendFile = [('file', open(fName, 'rb'))]


			is_ok, _json = APP.API.Send( self.url, modelDataDict, modelDataDict, sendFile )
			if is_ok:
				self.signal_refresh.emit()
			else:
				QMessageBox.critical(self, 'File Upload Fail', '다시 시도해 주십시요')


	def menu__file_download(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		obj:dict = self.api_data[msg.get('row')]
		fName = Utils.func_filedownload(url=obj.get('file'))

	def slot_signal_model_data_changed(self, msg:dict) -> None:
		"""
		{
			'row' :row,
			'col' : col,
			'value' : value,
			'api_data' :api_data,
		}
		"""


		obj = {}
		self.tableView : QTableView
		model_datas = self.tableView.model()._data
		api_data = msg.get('api_data')		
		obj['id'] = api_data.pop('id')
		if  model_datas[msg.get('row')][msg.get('col')] == msg.get('value'):
			return
		
		_isOk, _json = APP.API.Send( self.url, obj , api_data)
		if _isOk:
			self.signal_refresh.emit()
			# self.tableView.model().beginResetModel()
			# # print ( model_datas)
			# model_datas[msg.get('row')] =  self.get_table_row_data(_json)
			# self.tableView.model().endResetModel()
		else:
			pass
