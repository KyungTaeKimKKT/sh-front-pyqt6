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

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget
from modules.PyQt.dialog.imageView.dialog_imageview import Dialog_ImageView


from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value

from modules.PyQt.component.combo_lineedit import Combo_LineEdit, Widget_망관리_망사, Widget_망관리_사용구분, Widget_망관리_의장종류, Widget_망관리_품명, Widget_망관리_할부치수, Widget_망관리_고객사

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger


TABLE_NAME = '관리'
HOVER_LIST = ['file수']


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableModel_관리(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		

	def setData(self, index, value, role):
		if role == Qt.ItemDataRole.EditRole:
			row , col = index.row(), index.column()
			value, api_data  =  self._get_edit_data(row, col, value)
			#### 😀is_등록일 때, confirm
			if col == self.header.index('is_등록') and value == True:
				dlg_res_button =  Utils.generate_QMsg_question(self.parentWid, title="확인", text='등록처리합니까? \n( 등록처리하면 더 이상 수정할 수 없읍니다.)\n')
				if dlg_res_button == QMessageBox.StandardButton.Ok :
					emit_data = self.__generate_emit_data(value, api_data, index )
					self.signal_data_changed.emit(emit_data)
			else:
				emit_data = self.__generate_emit_data(value, api_data, index )
				self.signal_data_changed.emit(emit_data)

			return True
		return False
	
	def __generate_emit_data(self, value, api_data:dict, index:QModelIndex) -> dict:
		row , col = index.row(), index.column()
		api_data.update({'id': self._data[row][self.header.index('id')]})

		emit_data = {
					'row' :row,
					'col' : col,
					'value' : value,
					'api_data' :api_data,
					}
		return emit_data

	def user_defined_data(self, index:QModelIndex, role:int, value ) :
		colNo = index.column()
		rowNo = index.row()
		headerName = self.header[colNo] 
		match headerName:
			case '일자':
				if not isinstance(value, str) : return '...'
				# return '미리보기' if len(value) and not '내용이 없읍니다.'in value else '내용이 없읍니다.'		
		return value

class TableView_관리(My_TableView):
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

class Delegate_관리(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	def user_defined_creatorEditor_설정(self, editor:QWidget, **kwargs) ->QtWidgets.QWidget:

		key = kwargs['key']
		### Widget_망관리_망사, Widget_망관리_사용구분, Widget_망관리_의장종료, Widget_망관리_품명, Widget_망관리_할부치수, 고객사_Widget
		if key in ['망사', '사용구분','의장종류', '품명','할부치수','고객사']:
			editor = eval(f"Widget_망관리_{key}( kwargs['parent'])")
			
		elif key in ['망번호']:
			### 😀 validator 적용
			from modules.PyQt.User.validator import 망등록_망번호_Validator
			editor.setValidator( 망등록_망번호_Validator(qRegEx=None, wid=editor) )
			editor.setPlaceholderText("xx-xxx 형태(x는 숫자)만 입력가능")
			editor.setToolTip ("xx-xxx 형태(x는 숫자)만 입력가능")

		return editor	
		
	#😀 custome widget일 때
	def setModelData(self, editor, model, index) -> None:
		super().setModelData(editor, model, index)
		if isinstance(editor,  Combo_LineEdit):
			global no_Edit_Row
			row = index.row()
			value = editor.getValue()
			model.setData(index, value, Qt.EditRole)
			model.layoutChanged.emit()
		# elif isnstance(editor, ):
		# 	model.setData(index, editor.text(), )

	# def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex, **kwargs) -> None:
	# 	if '일' in kwargs['key'] and kwargs['value'] is None and isinstance(editor, QDateEdit):
	# 		editor.setDate( datetime.now().date() )



class Wid_Table_for_관리(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_관리
		self.table_model : TableModel_관리
		self.delegate : Delegate_관리

		self.dlg_hover_file수 = self._init_dlg_Hover()

	def _init_dlg_Hover(self) -> QDialog:
		""" dlg만 초기화 함. image가 확정되면 wid을 insert함. """
		
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
		if ID <1 : 
			if hasattr(self, 'dlg_hover_file수') : self.dlg_hover_file수.close()	
			return 
		if is_show:			
			if ( app_data_dict := self._get_apiDict_by_ID(ID) ):
				match hoverName:
					case 'file수':
						if hasattr(self, 'dlg_hover_file수') : self.dlg_hover_file수.close()						
						if app_data_dict.get('file수', False):
							displayList =  [ {'_url':fileURL.replace('192.168.7.108', 'mes.swgroup.co.kr') } if (fileURL := app_data_dict.get(file,'') ) else ''  for file in ['file1', 'file2']  ]
							self.dlg_hover_file수 = Dialog_ImageView( self, 
											   displayList=displayList , 
											   _windowTitle=app_data_dict.get('망번호') + '--' + app_data_dict.get('현장명'),
											   _fixedSize = QSize( 400, 650 ),
											   )
							self.dlg_hover_file수.move(position.x()+INFO.NO_CONTROL_POS, position.y() )
		else:
			self.dlg_hover_file수.close()
		# if INFO.IS_DebugMode :

		

	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__파일_다운로드(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		colNo = msg.get('col')
		rowNo = msg.get('row')

		dlg_res_button = Utils.generate_QMsg_question(self, text = "파일 다운로드  진행하시겠읍니까?")
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			api_data:dict = self.api_data[rowNo]

			threadingTargets = [ fileURL.replace('192.168.7.108', 'mes.swgroup.co.kr') if (fileURL := api_data.get(file,'') ) else '' for file in ['file1', 'file2']  ]


			다운로드fileName :list[str] =[]
			for url in threadingTargets:

				다운로드fileName.append( Utils.func_filedownload(url))

			_txt = '\n'.join(다운로드fileName)
			Utils.generate_QMsg_Information( self, title="파일다운로드 결과" ,
									text=f"{len(다운로드fileName)} 개 파일을 다운받았읍니다. \n {_txt}")


	def menu__파일_업로드(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		rowNo = msg.get('row')
		original_dict:dict = self.api_data[rowNo]
		display_dict = {}
		if ( file1 := original_dict.get('file1','') ):
			display_dict[1] = file1
		if (file2 := original_dict.get('file2', '') ):
			display_dict[2] = file2

		dlg = Dialog_file_upload_with_listwidget(self , 
										   original_dict= original_dict, 
										   display_dict= display_dict, 
										   )
		### fileField 임
		dlg.signal_save.connect( lambda wid, original, sendData, m2mField: self._file_upload(wid, original,sendData  ) )

	def _file_upload( self, widget:QDialog, original:dict, sendData:dict[str:dict[int:str]] ):
		""" sendData는  {'fileNames': {-1: '/home/kkt/24-079_2.png', -2: '/home/kkt/24-079_1.png'}}"""
		
		fileNames = sendData.get('fileNames', False)
		if fileNames:
			sendFiles = []
			for idx, (id, fName) in enumerate(fileNames.items()):
				sendFiles.append( ( f"file{idx+1}" , open( fName, 'rb') ) )
			
			is_ok, _json = APP.API.Send( self.url, original, {}, sendFiles=sendFiles )
			if is_ok:
				widget.close()
				self.signal_refresh.emit()
			else:
				Utils.generate_QMsg_critical( self, title='File Upload Fail', text='FILE Upload가 실패하였읍니다. \n 다시 시도해 주십시요 \n')


	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, 관리은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_관리
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