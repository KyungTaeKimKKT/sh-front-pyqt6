from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing


# import user module



from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.User.Tb_Model import Base_TableModel
from modules.PyQt.User.Tb_Delegate import Base_Delegate
from modules.PyQt.Tabs.Base import Base_App

from stylesheet import StyleSheet

from modules.PyQt.User.toast import User_Toast
from config import Config as APP

# import sub window
from modules.PyQt.sub_window.win_search import Win_Search
from modules.PyQt.sub_window.win_form import Win_Form
from modules.PyQt.User.object_value import Object_Get_Value

# 😀😀😀😀😀
from modules.PyQt.Tabs.Base import Base_App
from modules.PyQt.Tabs.생산모니터링.Datas import AppData_생산계획입력 as AppData
import traceback
from modules.logging_config import get_plugin_logger

# from modules.PyQt.Tabs.생산모니터링.일일업무_개인_table_view import 개인_TableView


### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(Base_TableModel):
	signal = QtCore.pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = []):
		super().__init__( baseURL, data, header, header_type, no_Edit)


	### 😀😀😀type에 따라서 변경해야 함. hard-coding ###
	### 😀start_time, end_time
	def user_defined_data(self, index:QModelIndex, role, value) :
		col = index.column()	
		if  self.header[col] in ['start_time','end_time']:
			value = str(value).split('T')[1]

		return value

	def user_defined_BackgroundRole(self, index, role):
		pass
		# global no_Edit_Row 
		# if index.row() in no_Edit_Row:
		# 	return QtGui.QColor(self.ST.COLOR_edit_disable )
	
	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			row , col = index.row(), index.column()
			data = self._get_edit_data(row, col, value)
			ID = self._get_ID(row)
				
			is_ok, res_json = self._api_send( ID=ID, data=data)

			# Set the value into the frame.==>self._data.iloc[index.row(), index.column()] = value
			if is_ok:
				self._data[row]= self.get_data_from_response(res_json)
				# self.signal.emit({'data':'changed'})
				return True
			else:
				return False

		return False

	def _get_edit_data(self, row:int, column:int, value) ->dict:
		key =  self.header[column]
		ID = self._get_ID(row)
		data = {}
		if  ID  < 0:				
			data.update ( {'일자':self._data[row][self.header.index('일자')] } )
			
		### 😀start_time, end_time 은 실제 QDateTimeEdit 이나, 표시는 QTimeEdit로 하였기 때문에
		### 당일을 포함시켜서 return
		if isinstance(value, QtCore.QTime) :			
			value = QDateTime( QDate.currentDate(), value )
			result = value.toString('yyyy-MM-ddThh:mm:ss')

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



class App_TableView( My_TableView):
	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ...) -> None: 
		super().__init__(parent)

		self.setColumnWidth(5,50)
		# self._set_column_width()


### app 마다 hardcoding : 😀	
class App_Delegate(Base_Delegate):
	def __init__(self, header:list=[], header_type:dict={} ,no_Edit:list = []):
		super().__init__(header, header_type, no_Edit)

	
	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor, index):
		row , col = index.row(), index.column()
		text = (index.data(Qt.EditRole) or index.data(Qt.DisplayRole))		
		if  self.header[col] in ['start_time','end_time']:
			if isinstance(editor, QtWidgets.QTimeEdit) :
				editor.setTime( QTime.fromString(text, 'hh:mm:ss')) 

	### modify widgets
	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:
		match key:
			case 'plan_qty':
				if isinstance(widget, QtWidgets.QSpinBox):
					widget.setRange(0, 1000)
					widget.setSingleStep(1)
		return widget

class Form_일일업무_개인(Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', inputType:dict={}, title:str='', dataObj:dict={} ):
		super().__init__(parent, url, win_title, inputType, title, dataObj )
		self.validator_list = ['업무내용']
		self.ST = StyleSheet()
		self.title_text ='일일업무'
		
	def run(self):
		self.UI()        
		self.TriggerConnect()

		self.inputDict['업무내용'].textChanged.connect(self.check_validator)
	
	##### Trigger Func. #####
	def func_save(self):
		for key in self.inputType.keys():
			if key == 'id' : continue
			self.result[key] = self._get_value(key)
		
		self.api_send()
		

	def api_send(self):
		if bool(self.dataObj):
			is_ok, res_json = APP.API.patch(url= self.url+ str(self.dataObj.get('id')) +'/',
											data=self.result )
		else:
			is_ok, res_json = APP.API.post(url= self.url,
											data=self.result )
			
		if is_ok:
			self.signal.emit({'action':'update'})
			self.close()
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')

	### Hard-coding 😀😀
	def _gen_by_key(self, key:str='', value=None, label:object='', input:object=None):
		match key:
			case '업무내용':
				if isinstance(input, QtWidgets.QLineEdit ):
					input.setPlaceholderText("제목을 넣으세요(필수★)")
					input.textChanged.connect(self.check_validator)
			case '일자':
				if isinstance(input, QtWidgets.QDateEdit ):
					input.setDate(QDate.currentDate())
			
			case _:
				pass				
			
		self.inputDict[key] = input

		return (label, input)
	
	def check_validator(self) -> bool:
		for key in self.validator_list:
			if self._get_value( key ):
				self.inputDict[key].setStyleSheet(self.ST.edit_)
				self.PB_save.setEnabled(True)
				return True
		self.PB_save.setEnabled(False)
		return False





class App__for_Tab(Base_App):
	def __init__(self, parent:QtWidgets.QMainWindow,   url:str ):
		super().__init__( parent,  appFullName, url  )
			
		####  😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################

		self.form = Form_일일업무_개인( 	parent=self, 
								
								url = self.url,
								win_title='공지사항' + '--' + '신규',
								inputType=self.header_type,
								title= '공지사항' + '--' + '신규',														
								)
		
	
	#### app마다 update 할 것.😄
	def run(self):
		self.deleteLayout(self.vlayout)
		if self.get_api_and_model_table_generate():
			self.table.signal.connect (self.slot_table_siganl)
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')
		
	

	def get_api_and_model_table_generate(self) -> bool:
		if self._check_api_Result():
			self.model_data = self.gen_Model_data_from_API_data()

			self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
										header_type=self.header_type, no_Edit=self.no_Edit)
			tableView, vlayout = self._render_frame_MVC(App_TableView(self))
			self.table:App_TableView = self._gen_table(tableView )

			### setting table delegate
			self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
			self.table.setItemDelegate(self.delegate)
			
			self._hide_hidden_column()

			return True
		else: return False

		


	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def slot_table_siganl(self,msg:dict):
		### 😀😀😀lower로 해서 보냄
		actionName = msg.get('action')
		match actionName:
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
				eval(f"self.{actionName}()")


	#### 😀 : form_new 만 추가
	def handle_form_new(self):
		self.form = Form_일일업무_개인( 	parent=self, 
								
								url = self.url,
					   			win_title='일일업무' + '--' + '신규',
					   			inputType=self.appData.form_type,
								title= '일일업무' + '--' + '신규',								
								)
		self.form.run()
		
		self.form.signal.connect(self.slot_form_signal)

	def slot_form_signal(self, msg:dict):
		if self._check_api_Result():
			self.model_data = self.gen_Model_data_from_API_data()
			self.model._data  = self.model_data
			self.table.model().layoutChanged.emit()
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')



