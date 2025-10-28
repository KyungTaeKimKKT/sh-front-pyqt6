import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import openpyxl
import typing


# import user module
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.ui.Ui_tabs import Ui_Tabs

import modules.user.utils as utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP

from modules.PyQt.User.Tb_Model import Base_TableModel, Base_TableModel_Pandas
from modules.PyQt.User.Tb_Delegate import Base_Delegate, AlignDelegate
from modules.PyQt.Tabs.Base import Base_App
import traceback
from modules.logging_config import get_plugin_logger



### https://www.pythonguis.com/faq/editing-pyqt-tableview/

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App사용자관리_TableModel(Base_TableModel):
	signal = pyqtSignal(dict)

	def __init__(self,  baseURL:str, data:list, header:list, header_type:dict={}, no_Edit:list = [], user_pks:list=[]):
		super().__init__( baseURL, data, header, header_type, no_Edit)
		self.user_pks = user_pks

		##########################################################################3
	def _type_change(self, index, value):
		row = index.row()
		col = index.column()
		id = int (self._data[row][0])
		if id in self.user_pks:

			match self.header[col]:
				case 'user_성명'|'user_mailid':
					return QIcon(f':/icons/true.jpg')
	############################################################################

class App사용자관리_TableView(My_TableView):

	def __init__(self, parent: typing.Optional[QWidget] = ...) -> None: 
		super().__init__(parent)

	def _init_select_trigger(self):

		self.doubleClicked.connect(self.handle_doubleClicked)
		# self.clicked.connect (self.handle_clicked)

		
#### app 마다 hardcoding : 😀	
class App사용자관리_Delegate(Base_Delegate):
	def __init__(self, header_type:dict={} ,no_Edit:list = []):
		super().__init__(header_type, no_Edit)
			
	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor, index):
		pass

	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:
		match key:
			case '순서':
				
				widget.setRange(1, 99999)
				widget.setSingleStep(1)
		return widget
	

class Win_app사용자관리(QMainWindow):
	signal = pyqtSignal(dict)

	def __init__(self, parent:QMainWindow=None):
		super().__init__(parent )
		
		self.app사용자obj :dict 
		#### gen header_type : Hardcodeing 😀
		self.header_type = {}	#['id', 'user_mailid', 'user_성명', 'user_직책', 'user_직급', '기본조직1', '기본조직2', '기본조직3', 'is_active', 'is_admin']
		self.header_type = {
			'id' : '___',
			'user_mailid': '___',
			'user_성명': '___',
			'user_직책' : '___',
			'user_직급': '___',
			'기본조직1': '___',
			'기본조직2' : '___',
			'기본조직3': '___',
			'is_active':'QCheckBox(parent)',
			'is_admin' : 'QCheckBox(parent)',
		}
		self.url = '/api/users/users/'
		self.url_pks_update = parent.url		
		self.no_Edit = ['id']	#'등록일',
		self.pageSize = 0
		self.suffix = f'?page_size={self.pageSize}'

		# 

		self.search_msg = {}

		self.UI()

		# 

	def UI(self):
		
		self.mainLayout = QVBoxLayout()
		widget = QWidget()

		self.tableView  = App사용자관리_TableView(self)
		self.mainLayout.addWidget(self.tableView)
		widget.setLayout(self.mainLayout)
		# widget.setLayout(self.mainLayout)
		self.setCentralWidget(widget)
		# self.centralwidget.setObjectName("centralwidget")

		self.show()



	def run(self):
		if self._check_api_Result():
			self.model_data = self.gen_Model_data_from_API_data()			
			if hasattr(self, 'app사용자obj'):
				if self.app사용자obj is not None and isinstance( self.app사용자obj, dict):
					self.user_pks:list = self.app사용자obj.get('user_pks',[])
				else:
					self.user_pks = []
			else:
				self.user_pks= [] 
			self.model = App사용자관리_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
										header_type=self.header_type, no_Edit=self.header, user_pks=self.user_pks)
			self.tableView = self._gen_table(self.tableView)
			### setting table delegate
			self.delegate = App사용자관리_Delegate(self.header_type, self.header)
			self.tableView.setItemDelegate(self.delegate)

			delegate_bg = AlignDelegate(self.tableView, self.user_pks)
			self.tableView.setItemDelegate(delegate_bg)

			self.tableView.signal.connect(self.slot_table_signal)
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')

	def slot_table_signal(self, msg:dict):
		actionName = msg.get('action')
		match actionName:
			case 'cell_doubleClicked':
				user_pks = self.user_pks
				row = msg.get('data').get('row')
				if ( ID := self._get_ID(row) ) in user_pks:
					user_pks.remove(ID)
				else: user_pks.append(ID)

				if ( self._update_user_pks_to_DB(user_pks) ):				
					delegate_bg = AlignDelegate(self.tableView, self.user_pks)
					self.tableView.setItemDelegate(delegate_bg)
					self.tableView.model().layoutChanged.emit()
				else:
					user_pks = self.user_pks
					delegate_bg = AlignDelegate(self.tableView, self.user_pks)
					self.tableView.setItemDelegate(delegate_bg)
					self.tableView.model().layoutChanged.emit()

	def _update_user_pks_to_DB(self , user_pks:list) -> bool:
		objID = self.app사용자obj.get('id')

		if 1 not in user_pks : user_pks.insert(0, 1)
		is_ok, res_json = APP.API.patch (self.url_pks_update + str(objID) + '/', 
											{"user_pks":user_pks}	)
		if is_ok:
			toast = User_Toast(self, text="사용자 변경이 DB에 저장되었읍니다.")
			self.signal.emit({'사용자변경': True})
		else:
			toast = User_Toast(self, text="사용자 변경이 DB에 저장되었읍니다.", style="ERROR")
		
		return is_ok
		# is_ok, res_json = APP.API.patch()


	def _get_app_DB_data(self, url):
		suffix = self.suffix
		return APP.API.getlist(url+suffix)

	def _check_api_Result(self) -> bool:
		if self.pageSize :
			is_ok, self.app_query_result = self._get_app_DB_data(self.url)
			self.app_DB_data = self.app_query_result.get('results')
			del self.app_query_result['results']
		else:
			is_ok, self.app_DB_data = self._get_app_DB_data(self.url)
		
		return is_ok
	
	def _gen_table(self, table:App사용자관리_TableView):
		table.setModel(self.model)
		table.resizeColumnsToContents()
		table.resizeRowsToContents()
		# https://stackoverflow.com/questions/38098763/pyside-pyqt-how-to-make-set-qtablewidget-column-width-as-proportion-of-the-a
		header = table.horizontalHeader()       
		# header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
		return table
	
	def _render_frame_MVC(self):
		pass

	
	def gen_Model_data_from_API_data(self) ->list:  
		self.header = self._get_header()
		_data = []
		for obj in self.app_DB_data:
			_data.append ( [ self._get_Name(key, obj) if key != 'file' else 'file' for key in self.header ] )
		return _data
	

	def _get_header(self) ->list:
		data = self.app_DB_data
		if bool(self.header_type):
			return list(self.header_type.keys() )
		else:
			return list(data[0].keys() ) if len(data) else [] #if len(data) else self.defaultDict.keys()


	def _get_Name(self, key, obj) ->str:
		value = obj[key]
		match key:
			# case 'OS':
			#     return self.OS_dict.get(value)
			# case '종류':
			#     return self.종류_dict.get(value)
			case _:
				return value
	
	def _get_ID(self, row:int) ->int:
		col = self.header.index('id')
		return int(self.model_data[row][col])
# def main():    

#     app=QApplication(sys.argv)
#     window= Win_app사용자관리()
#     window.show()
#     app.exec_()


# if __name__ == "__main__":
#     sys.exit( main())