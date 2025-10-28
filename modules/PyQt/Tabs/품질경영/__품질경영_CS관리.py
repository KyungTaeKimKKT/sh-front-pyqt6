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



from modules.PyQt.Tabs.품질경영.품질경영_table import 품질경영_Base_TableView
from modules.PyQt.Tabs.품질경영.품질경영_delegate import 품질경영_Base_Delegate
from modules.PyQt.Tabs.품질경영.품질경영_table_model import 품질경영_Base_TableModel
from modules.PyQt.Tabs.품질경영.품질경영_CS_form import CS_Form
from modules.PyQt.Tabs.품질경영.CS_활동현황_form import CS_활동현황_Form, CS_활동현황_Form_View
# from modules.PyQt.Tabs.품질경영.품질경영_CS관리 import App__for_Tab as CS_Bast_Tab
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget
from modules.PyQt.Tabs.Base import Base_App

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as utils
# import sub window
from modules.PyQt.sub_window.win_search import Win_Search
from modules.PyQt.sub_window.win_form import Win_Form
from modules.PyQt.User.object_value import Object_Get_Value

# 😀😀😀😀😀
from modules.PyQt.Tabs.품질경영.Datas_CS관리 import AppData_CS_관리 as AppData
import traceback
from modules.logging_config import get_plugin_logger

# from modules.PyQt.Tabs.생산모니터링.일일업무_개인_table_view import 개인_TableView



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(품질경영_Base_TableModel):
	pass

class App_TableView ( 품질경영_Base_TableView):
	pass

class App_Delegate(품질경영_Base_Delegate):
	pass


class App__for_Tab(Base_App):
	def __init__(self, parent:QtWidgets.QMainWindow,   url:str ):
		super().__init__( parent,  appFullName, url  )
			
		####  😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################

	def UI(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.no_data_hlayout = QtWidgets.QHBoxLayout()

		self.pb_form_New = QtWidgets.QPushButton('고객요청/불만사항 등록')
		self.pb_form_New.clicked.connect(self.handle_form_new)
		self.label = QtWidgets.QLabel('신규 고객요청 및 불만사항을 생성합니다.')
		self.no_data_hlayout.addStretch()
		self.no_data_hlayout.addWidget(self.label)
		self.no_data_hlayout.addStretch()
		self.no_data_hlayout.addWidget(self.pb_form_New)
		self.vlayout.addLayout(self.no_data_hlayout)
		self.tableView = App_TableView(self)
		self.vlayout.addWidget(self.tableView)		
		self.setLayout(self.vlayout)
	
	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vlayout'): utils.deleteLayout(self.vlayout)
		self.UI()
		if self.get_api_and_model_table_generate():

			self.table.signal.connect (self.slot_table_siganl)
		else:
			if self.is_api_ok:
				pass
				# self._render_Null_data()
			else:
				User_Toast(self, text='server not connected', style='ERROR')	
		
	

	def get_api_and_model_table_generate(self) -> bool:
		self.is_api_ok = self._check_api_Result()
		if self.is_api_ok:
			if self.app_DB_data:

				self.model_data = self.gen_Model_data_from_API_data()

				self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
											header_type=self.header_type, no_Edit=self.no_Edit)

				# tableView, vlayout = self._render_frame_MVC(App_TableView(self))

				self.table:App_TableView = self._gen_table(self.tableView )

				### setting table delegate
				self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit ) #, appData=AppData())
				self.delegate.appData = self.appData
				self.table.setItemDelegate(self.delegate)
				
				self._hide_hidden_column()

				return True
		else: return False


	def _get_Name(self, key:str, obj:dict) ->str|int|None:
		value = obj.get(key , None)
		match key:
			case 'claim_파일수':
				return len(obj.get('claim_files', []))
			case '대책활동수':
				return len( obj.get('actions', []))
			case '대책활동파일수':
				count = 0
				for action in obj.get('actions', [] ):
					count += len( action.get('action_files', []))

				return count
			# case 'OS':
			#     return self.OS_dict.get(value)
			# case '종류':
			#     return self.종류_dict.get(value)
			case _:
				return value

	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def slot_table_siganl(self,msg:dict):
		### 😀😀😀lower로 해서 보냄
		actionName = msg.get('action')
		match actionName:
			case 'form_edit'|'Form_Edit':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.handle_form_edit(row)	

			case 'form_view'|'Form_View':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.handle_form_view(row)				

			case 'new':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.insert_app_DB_data(row)					
					self.table.model().layoutChanged.emit()

			case 'delete':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					if ( ID := self._get_ID(row) ) >0:
						msgBox = QtWidgets.QMessageBox.warning(
										self, 'DB에서 삭제', "DB에서 영구히 삭제됩니다.", 
										QtWidgets.QMessageBox.Yes |  QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
										)
						if msgBox == QtWidgets.QMessageBox.Yes:
							is_ok = APP.API.delete(self.url+str(ID)+'/')		
							if is_ok:
								self.model_data.pop(row)
								self.table.model().layoutChanged.emit()
							else:
								pass						
						else:
							return
					else:
						self.model_data.pop(row)
						self.table.model().layoutChanged.emit()

			case 'set_row_span':
				if isinstance( (col := msg.get('data').get('col') ) , int) :					
					self.handle_row_span('set', col)			
			
			case 'reset_row_span':
				if isinstance( (col := msg.get('data').get('col') ) , int) :					
					self.handle_row_span('reset', col)

			case _:
				self.user_defined_table_signal_handler( msg )

	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()
		if ( data := msg.get('data', None) ):
			row = data.get('row', -1)
		match actionName:
			case '작성완료':
				if self.handle_진행현황 (row=row, msgTitle=actionName, msgText="배포하시겠습니까?", 진행현황 = 'Open'):
					self.run()
				else:
					return 
						
			case '활동종료':
				if self.handle_진행현황 (row=row, msgTitle=actionName, msgText="활동종료(Close) 하시겠습니까?", 진행현황 = 'Close'):
					self.run()
				else:
					return 

			case 'File첨부'|'file첨부':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_file첨부(self.selectedDataObj )

			case '활동현황_추가':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_활동현황추가(self.selectedDataObj )
			
			case '활동현황_보기':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_활동현황보기(self.selectedDataObj )
					
			case '활동종료':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_활동현황보기(self.selectedDataObj )
					
			case _:
				eval(f"self.{actionName}()")
	
	def handle_진행현황(self, row:int, msgTitle:str, msgText:str, 진행현황:str) -> bool:
		if isinstance( row , int) and row > -1 :
			if ( ID := self._get_ID(row) ) >0:
				reply = QMessageBox.question(
					self, msgTitle, msgText, QMessageBox.Yes |  QMessageBox.Cancel, QMessageBox.Cancel
				)
				if reply == QMessageBox.Yes:
					is_ok = APP.API.patch(
									url = self.url+str(ID)+'/', 
									data= { '진행현황':진행현황,				  									
											})		
				return True
			else:
				return False
		return False


	def handle_활동현황추가(self, dataObj):
		form = CS_활동현황_Form(
						parent=self, 
						
						url = self.url,
						win_title='고객불만_활동추가',
						inputType={},
						title= '고객불만_활동추가',		
		)
		form.dataObj = dataObj
		form.run()

	def handle_활동현황보기(self, dataObj): 
		form =CS_활동현황_Form_View(
						parent=self, 
						
						url = self.url,
						win_title='고객불만_활동보기',
						inputType={},
						title= '고객불만_활동보기',		
		)
		form.dataObj = dataObj
		form.run()


	def handle_file첨부(self, dataObj:dict) :
		self.dialog = QDialog(self)
		vlayout = QVBoxLayout()
		self.dialog.setFixedSize (500,300)
		fileupload = File_Upload_ListWidget(
						newFiles_key='file_fks', 
						initialData=dataObj.get('file_fks', []))
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
				result['file_fks_json'] = json.dumps( exist_DB_ids )
			else:
				result['file_fks_삭제'] = True
				
			if ( files_fks := files.get('new_DB') ):
				#### 😀 change for api m2m field
				result_files.extend ( files_fks )

		is_ok, _ = APP.API.Send(self.url, self.selectedDataObj , result, result_files)
		if is_ok:
			self.dialog.close()
			self.run()


	#### 😀 : form_new 만 추가
	def handle_form_new(self):
		form = CS_Form( 	parent=self, 
						
						url = self.url,
						win_title='고객불만_요청_관리',
						inputType=self.appData._get_form_type(),
						title= '고객불만_요청_관리',														
						)

		# form.process_app_DB_data = self.app_DB_data[2].get('process_fks')
		# form.dataObj = self.app_DB_data[row]
		form.run()	
		form.signal.connect(self.slot_form_signal)	

	def handle_form_edit(self, row:int):
		form = CS_Form( 	parent=self, 
						
						url = self.url,
						win_title='고객불만_요청_관리',
						inputType=self.appData._get_form_type(),
						title= '고객불만_요청_관리',														
						)

		# form.process_app_DB_data = self.app_DB_data[2].get('process_fks')
		form.dataObj = copy.deepcopy(self.app_DB_data[row])
		form.run()	
		form.editMode()
		form.signal.connect(self.slot_form_signal)	
	
	def handle_form_view(self, row:int):
		form = CS_Form( 	parent=self, 
						
						url = self.url,
						win_title='고객불만_요청_관리',	
						inputType=self.appData._get_form_type(),
						title= '고객불만_요청_관리,',														
						)
		form.title_text='고객불만_요청_관리'
		form.dataObj = copy.deepcopy(self.app_DB_data[row])
		form.run()
		form.viewMode()
		form.signal.connect(self.slot_form_signal)	


	def slot_form_signal(self, msg:dict):
		self.run()