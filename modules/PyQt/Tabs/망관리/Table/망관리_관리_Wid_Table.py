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

from modules.PyQt.Tabs.망관리.dialog.Dialog_망등록 import Dialog_망등록
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.User.Tb_Model import Base_TableModel
from modules.PyQt.User.Tb_Delegate import Base_Delegate

from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget
from modules.PyQt.Tabs.Base_table_for_tab import Base_Wid_Table


from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.sub_window.win_search import Win_Search
from modules.PyQt.sub_window.win_form import Win_Form
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


# 😀😀😀😀😀
from modules.PyQt.Tabs.망관리.datas.AppData__망관리_관리 import AppData__망관리_관리 as AppData

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel( Base_TableModel):
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			self._data[index.row()][index.column()] = value
			return True
		return False
	
	def user_defined_DecorationRule(self, index, value):		
		row = index.row()
		col = index.column()

		match self.header[col]:
			case 'upload_path_1'|'upload_path_2':
				if isinstance(value, bool) :
					if value :
						return QtGui.QIcon(f':/table-decorator/files-exist')



class App_TableView( My_TableView ):

	def contextMenu_Render_Connect(self, event, row:int, col:int) ->QtWidgets.QMenu:
		menu : QtWidgets.QMenu = None
		match self.parent.header[col]:
			case 'upload_path_1'|'upload_path_2':
				if self.model()._data[row][col]:
					menu = QtWidgets.QMenu(self)
					self.action_view = menu.addAction('View')
					menu.addSeparator()

					self.action_view.triggered.connect(lambda:self.slot_FileView(row, col))
	
			case _:
				pass
		return menu
	
	def slot_FileView(self, row,col) :
		from modules.PyQt.component.imageViewer2 import ImageViewer_확대보기
		viewer_dialog = QDialog(self)
		vLayout = QVBoxLayout()
		viewer = ImageViewer_확대보기()

		vLayout.addWidget( viewer )
		viewer_dialog.setLayout(vLayout)
		

		url = self.parent.app_DB_data[row].get( self.parent.header[col])
		# url = url.replace('192.168.7.108:9999', '192.168.10.240:10000')		
		viewer.set_image_from_URL ( url )
		viewer_dialog.show()


class App_Delegate( Base_Delegate):
	pass


class Wid_Table_for__망관리_관리(Base_Wid_Table ):
	def __init__(self, parent:QtWidgets.QMainWindow,  **kwargs ):
		super().__init__( parent, **kwargs )
		
		####  필수 : 😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################

		self.첨부파일_Key = "첨부file_fks"

	def UI(self):
		self.vLayout_main = QVBoxLayout()
		self.tableView = App_TableView(self)
		self.vLayout_main.addWidget(self.tableView)		
		self.setLayout(self.vLayout_main)

	def get_api_and_model_table_generate(self) -> bool:
		if (is_api_ok := self._check_api_Result() ) :
			self.is_api_ok = is_api_ok

			if self.app_DB_data:
				self.model_data = self.gen_Model_data_from_API_data()
				self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
											header_type=self.header_type, no_Edit=self.no_Edit)
				self.table:App_TableView = self._gen_table(self.tableView )

				### setting table delegate
				self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
				self.table.setItemDelegate(self.delegate)
				
				self._hide_hidden_column()

				return True
			else:
				return False
		else: 
			return False

	
	#### app마다 update 할 것.😄
	def run(self):
		super().run()		


	def get_Selected_Datas(self) -> list[dict] :
		""" """
		result = []
		for rowNo in self.table._get_selected_rows():
			obj = {}
			history_txt = '초도확정'
			model_data:list = self.model_data[rowNo]
			for index, key in enumerate(self.header):
				value = model_data[index]
				match key:
					case 'id':
						obj[key] = value
					case '납기일_Door':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_Door 변경'
						obj[key] = value 
					case '납기일_Cage':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_Cage 변경'
						obj[key] = value
					case '납기일_JAMB':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_JAMB 변경'
						obj[key] = value
					case 'is_계획반영_htm':
						if not value and model_data[self.header.index('진행현황_htm')] == '배포':
							obj[key] = not value
					case 'is_계획반영_jamb':
						if not value and model_data[self.header.index('진행현황_jamb')] == '배포':
							obj[key] = not value
			obj['history'] = history_txt
			result.append(obj)
		return result
	### 😀base app method override:
	def _get_Name(self, key:str, obj:dict) ->str:
		value = obj.get(key , None)
		match key:
			case 'upload_path_1'|'upload_path_2':
				if not value : return False
				return True if 'http' in value else False
			case _:
				return obj.get(key, '')


	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def handle_form_view(self, row:int)	-> None:
		dialog = Dialog_망등록(self)
		dialog.dataObj = self.app_DB_data[row]
		### 망사가 db:int 형이라
		dialog.dataObj['망사'] = str ( dialog.dataObj['망사'] )
		dialog.viewMode()
		dialog.show()


	def slot_search_for_tab(self, msg:dict):
		pass

	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()
		if ( data := msg.get('data', None) ):
			row = data.get('row', -1)
		match actionName:
			
			case _:
				eval(f"self.{actionName}()")


	def handle_file첨부(self, dataObj:dict) :
		self.dialog = QDialog(self)
		vlayout = QVBoxLayout()
		self.dialog.setFixedSize (500,300)
		fileupload = File_Upload_ListWidget(
						newFiles_key=self.첨부파일_Key, 
						initialData=dataObj.get(self.첨부파일_Key, []))
		vlayout.addWidget(fileupload)
		vlayout.addStretch()
		saveBtn = QPushButton()
		saveBtn.setText('저장')
		vlayout.addWidget(saveBtn)
		self.dialog.setLayout(vlayout)
		self.dialog.show()
		saveBtn.clicked.connect(lambda:self.slot_file첨부( fileupload._getValue()))

	def slot_file첨부(self, files:dict) -> None:
		####😀 key는  API DATA에 따라서, 
		result, result_files = {}, []
		if files:
			exist_DB_ids:list = files.get('exist_DB_id')
			if len(exist_DB_ids):
				result[f'{self.첨부파일_Key}_json'] = json.dumps( exist_DB_ids )
			else:
				result[f'{self.첨부파일_Key}_삭제'] = True
				
			if ( files_fks := files.get('new_DB') ):
				#### 😀 change for api m2m field
				result_files.extend ( files_fks )

		is_ok, _ = APP.API.Send(self.url, self.selectedDataObj , result, result_files)
		if is_ok:
			self.dialog.close()
			self.run()

	def slot_form_signal(self, msg:dict):
		self.run()


