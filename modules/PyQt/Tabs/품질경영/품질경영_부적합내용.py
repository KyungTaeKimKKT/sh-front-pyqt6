from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing
from operator import itemgetter
import copy

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

from modules.PyQt.User.object_value import Object_Get_Value

from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit, Material_Widget

# 😀😀😀😀😀
from modules.PyQt.Tabs.품질경영.품질경영_부적합내용_Datas import AppData_품질경영_부적합내용 as AppData
import modules.user.utils as Utils

from info import Info_SW
INFO = Info_SW()
from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger

ST = StyleSheet()

no_Edit_Row = []



### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(Base_TableModel):
	signal = QtCore.pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = []):
		super().__init__( baseURL, data, header, header_type, no_Edit)

		
	### edit시 필수 😀😀: https://www.pythonguis.com/faq/qtableview-cell-edit/ ==> 에제는 pandas
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			row , col = index.row(), index.column()			
			data = self._get_edit_data(row, col, value)

			self._data[row][col] = value
			# ID = self._get_ID(row)
			# is_ok, res_json = self._api_send( ID=ID, data=data)
			# # Set the value into the frame.==>self._data.iloc[index.row(), index.column()] = value
			# if is_ok:
			# 	self._data[row]= self.get_data_from_response(res_json)
			# 	# self.signal.emit({'data':'changed'})
			# 	return True
			# else:
			# 	return False
			return True

		return False

	
	##########################################################################3
	def user_defined_data(self, index:QModelIndex, role, value) :
		return value
		# pass
		# col = index.column()	
		# if role == Qt.EditRole and self.header[col] == 'Material':
		# 	return ''
		# # print ( col, self.header[col], value)
		# return value

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
			# case '첨부file수':
			# 	if len(value):
			# 		if int(value) > 0:
			# 			return QtGui.QIcon(f':/table-decorator/files-exist')
				
			case '제목':
				col = self.header.index('수량')
				el수량 = self._data[row][col]
				if el수량 is None : return
				if int(el수량) > INFO._get_품질경영_중요도():
					return  QtGui.QIcon(f':/table-decorator/디자인의뢰-중요')


			# case 6:
			#     return str(value).split('T')[1]
			# case 7:
			#     return str(value).capitalize()
			
			case _:
				return value
	############################################################################

	def user_defined_BackgroundRole(self, index, role):
		global no_Edit_Row 
		if index.row() in no_Edit_Row:
			return QtGui.QColor(self.ST.COLOR_edit_disable )
		
		row = index.row()
		col = index.column()
		match self.header[col]:
			case '상세부적합내용':
				if not len( index.data() ): return 
				중요도index = self._get_column_중요도(col_key='상세부적합내용', data=index.data() )
				중요도_attr:dict = getattr(ST, f"작지_중요도{중요도index+1}", None)
				if 중요도_attr is None : return
				return QtGui.QColor(중요도_attr.get('bg'))
	
	def user_defined_ForegroundRole(self, index, role):
		row = index.row()
		col = index.column()
		match self.header[col]:
			case '상세부적합내용':
				if not len( index.data() ): return 
				중요도index = self._get_column_중요도(col_key='상세부적합내용', data=index.data() )
				중요도_attr:dict = getattr(ST, f"작지_중요도{중요도index+1}", None)
				if 중요도_attr is None : return
				return QtGui.QColor(중요도_attr.get('fg'))


	def _get_edit_data(self, row:int, column:int, value) ->dict:
		key =  self.header[column]
		ID = self._get_ID(row)
		data = {}
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
		elif row in no_Edit_Row and self.header[col] not in ['Material']:
			return flags

		else:
			return flags | Qt.ItemIsEditable

	def _get_column_중요도(self, col_key:str='상세부적합내용', data:str='' ) -> int:
		col_list={}
		col_datas_list=[]
		for row_idx, row_data in enumerate(self._data):
			col_datas_list.append(  row_data[self.header.index(col_key)].replace(' ','') )
		
		col_datas_unique = list(set(col_datas_list))
		self.col_len_sorted = sorted( col_datas_unique, key=len,  reverse=True)

		return self.col_len_sorted.index( data.replace(' ',''))



class App_TableView( My_TableView):
	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ...) -> None: 
		super().__init__(parent)


	def user_defined_slot_h_header_contextMenu(self, action:str, row:int):
		match action:
			case '완료처리':
				self.signal.emit( {
					'action': action.lower(),
					'data' : {
						'row': row,
					}
				})
			case _:
				User_Toast( parent=self, title='지원하지 않는 Action 명령어입니다.', 
			   				text=f"action 명령어 {action}", style='WARNING')


	####### 😀😀 contextMenu는 
	## 😀😀1. redner ==> super().method로 수정...
	##      2  trigger connect로 이루어져 있음
	def contextMenuEvent(self, event:QtGui.QContextMenuEvent):			
		indexes = self.selectionModel().selectedIndexes()
		for index in sorted(indexes):
			row = index.row()
			col = index.column()
		
		if ( menu:= self.contextMenu_Render_Connect(event, row, col) ) is not None:
			menu.popup(QtGui.QCursor.pos())

	#### Menu render and connect 
	def contextMenu_Render_Connect(self, event, row:int, col:int) ->QtWidgets.QMenu:
		menu : QtWidgets.QMenu = None
		match self.parent.header[col]:
			case '완료파일수':
				index = self.model().index(row, col)
				if int(index.data()) > 0:
					menu = QtWidgets.QMenu(self)
					self.action_download = menu.addAction(
												QtGui.QIcon(":/table-icons/file-download"),
												'File Download')
					self.action_download.setToolTip('App사용자를 추가,삭제 할 수 있읍니다.')
					menu.addSeparator()

					self.action_download.triggered.connect(lambda:self.slot_download_첨부파일(row, col))
	
			case _:
				pass
		return menu
	
	def slot_download_첨부파일(self, row, col):
		의뢰file_fks:list = self.parent.app_DB_data[row].get('의뢰file_fks')
		for obj in 의뢰file_fks:
			fName, contents = Utils.download_file_from_url(obj.get('file'))

			if fName :
				options =  QtWidgets.QFileDialog.Options()
				options |=  QtWidgets.QFileDialog.DontUseNativeDialog
				User_fName, _ = QtWidgets.QFileDialog.getSaveFileName(parent=None, 
													caption="Save File", 
													directory=str(pathlib.Path.home()), 
													filter="*", 
													options = options)
			else:
				User_Toast( parent=self, title='File Download error',	text = 'File Download error', style='Error')
			 
			if User_fName:
				with open(User_fName, 'wb') as download:
					download.write(contents)


### app 마다 hardcoding : 😀	
class App_Delegate(Base_Delegate):	
	### Material_Widget value가 '해당없음' 일 때 , siganl emit 하여 no_Edit_Row에 추가
	# signal_noEditRow = pyqtSignal(int)
	# signal_EditRow = pyqtSignal(int)

	def __init__(self, header:list=[], header_type:dict={} ,no_Edit:list = []):
		super().__init__(header, header_type, no_Edit)
		self.appData = AppData()
	QModelIndex
	#😀 custome widget일 때
	def setModelData(self, editor, model, index) -> None:
		super().setModelData(editor, model, index)

		if isinstance(editor,  Material_Widget):
			global no_Edit_Row
			row = index.row()
			value = editor.getValue()
			model.setData(index, value, Qt.EditRole)
			if value in ['해당없음'] and row not in no_Edit_Row:
				no_Edit_Row.append(row)
				for key in ['대표부적합내용', '상세부적합내용', '비고']:
					col = self.header.index(key)
					index = model.index(row,col)
					model.setData(index, '', Qt.EditRole)

			elif value not in ['해당없음'] and row in no_Edit_Row:
				no_Edit_Row.remove(row)
			model.layoutChanged.emit()
		# elif isnstance(editor, ):
		# 	model.setData(index, editor.text(), )
	
	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	#😀 각 app마다 custome widget일 때 지정할 것..
	def user_defined_cratorEditor(self, parent, value:str='') ->QtWidgets.QWidget|None:
		if value:
			return eval(value)
		else:
			return None

	def user_defined_setEditorData(self, widget, index):
		row, col = index.row(), index.column()
		text = (index.data(Qt.EditRole) or index.data(Qt.DisplayRole))	
		if isinstance(widget, Material_Widget ):
			widget.setValue(text)
		pass


	### modify widgets
	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:		
		match key:
			case 'Material':
				if isinstance(widget, Material_Widget):
					widget._render()

			
		return widget




class 부적합내용(Base_App):
	def __init__(self, parent:QtWidgets.QMainWindow,  appFullName:str=None, url:str=None ,  app_DB_data:list=[]):
		super().__init__( parent,  appFullName, url )

		####  😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################

		self.app_DB_data = app_DB_data if app_DB_data else self.appData._get_default_data()
		self.original_model_data = []
		# self.is_api_ok=False
	
	def UI(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.tableView = App_TableView(self)
		self.vlayout.addWidget(self.tableView)		
		self.setLayout(self.vlayout)

	#### app마다 update 할 것.😄
	def run(self):
		if hasattr( self, 'vlayout') : Utils.deleteLayout(self.vlayout)

		self.UI()
		if self.get_api_and_model_table_generate():
			self.table._disable_v_header_contextmenus()
			self.table.signal.connect (self.slot_table_siganl)
		else:
			User_Toast(self, text='server not connected', style='ERROR')

	def get_Api_data(self) -> list:
		if Utils.compare_list(self.original_model_data, self.model_data) : return []

		부적합내용_fks = []
		for 표시순서, 부적합내용 in enumerate(self.model_data):
			obj = {}
			for index, key in enumerate(self.header):
				obj[key] = 부적합내용[index]
			### 😀 저장할 때 순서대로 다시 보이기 위해 사용 
			# ==> table data 생성에서 이 filed '표시순서'로 sort된 data로  model data 생성
			obj['표시순서'] = 표시순서
			부적합내용_fks.append(obj)
		return 부적합내용_fks
	

	def _setReadOnly(self):
		"""
			table을  ReadOnly로
		"""
		self.no_Edit = self.header

	def get_api_and_model_table_generate(self) -> bool:

		if self.app_DB_data:
			### 😀 self.app_DB_data sorting
			### https://stackoverflow.com/questions/72899/how-to-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary-in-python
			try:
				self.app_DB_data = sorted(self.app_DB_data, key=itemgetter('표시순서'), reverse=False)
			except:
				pass

			self.model_data = self.gen_Model_data_from_API_data()
			self.original_model_data = copy.deepcopy(self.model_data)

			self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
										header_type=self.header_type, no_Edit=self.no_Edit)
			# tableView, vlayout = self._render_frame_MVC(App_TableView(self))
			self.table:App_TableView = self._gen_table(self.tableView)

			### setting table delegate
			self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
			self.table.setItemDelegate(self.delegate)
			# self.delegate.signal_noEditRow.connect(self.slot_no_EditRow)
			# self.delegate.signal_EditRow.connect(self.slot_EditRow)
			
			self._hide_hidden_column()

			return True
		else:
			return False



	def _render_Null_data(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		hlayout = QtWidgets.QHBoxLayout()

		self.label = QtWidgets.QLabel('접수할 자료가 없읍니다.')
		hlayout.addStretch()
		hlayout.addWidget(self.label)
		hlayout.addStretch()
		self.vlayout.addLayout(hlayout)
		self.vlayout.addStretch()
		
		# self.tabWidget.setLayout(self.vlayout)		
		self.setLayout(self.vlayout)	


	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def slot_table_siganl(self,msg:dict):
		### 😀😀😀lower로 해서 보냄
		actionName = msg.get('action')
		match actionName:
			case '완료처리':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.handle_form_완료(row)					

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

	def slot_no_EditRow(self, row:int):
		global no_Edit_Row
		no_Edit_Row.append(row)
	
	def slot_EditRow(self, row:int):
		global no_Edit_Row
		no_Edit_Row.remove(row)





