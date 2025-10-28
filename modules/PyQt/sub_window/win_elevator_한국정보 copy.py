import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from pathlib import Path

import typing

from modules.PyQt.Tabs.Elevator_Info.Datas import AppData_Elevator_Info as AppData
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import (
    한국정보__for_Tab, 
    # App_TableView,
    App_TableModel,
    App_Delegate
)

from modules.PyQt.User.toast import User_Toast
from info import Info_SW as INFO

from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableView( My_TableView):
	def __init__(self, parent: typing.Optional[QWidget|None] = ...) -> None: 
		super().__init__(parent)

	def user_defined_slot_h_header_contextMenu(self, action:str, row:int):
		row_list = []
		indexes = self.selectionModel().selectedIndexes()
		for index in sorted(indexes):
			row = index.row()
			col = index.column()
			row_list.append(row)
		
		row_list = list(set(row_list))
		if len(row_list) == 0 : return

		match action:
			case 'Select'|'select':
				self.signal.emit( {
					'action': action.lower(),
					'data' : {
						'rows': row_list,
					}
				})
			case _:
				User_Toast( parent=self, title='지원하지 않는 Action 명령어입니다.', 
			   				text=f"action 명령어 {action}", style='WARNING')



class Elevator_한국정보( QMainWindow, 한국정보__for_Tab ):
	signal = pyqtSignal(dict)

	def __init__(self, parent=None,  appFullName='',url=''):
		super().__init__( parent, appFullName, url)		
		self.api = APP.API
		self.url = INFO.Elevator_한국정보_URL
		
		self.appData.v_header_context_menu = {}
		self.appData.h_header_context_menu = {
			'Select' : {
				"icon" : "QtGui.QIcon(':/table-icons/tb-upgrade_row')",
				"title": "Select",
				"tooltip" :"Select합니다.",
				"objectName" : 'Select',
				"enabled" : True,
			}
		}


	def run(self):
		if hasattr(self, 'vlayout'): self.deleteLayout(self.vlayout)
		self.UI()

	def UI(self):
		wid = QWidget()
		self.vlayout =  QVBoxLayout()
		form = QHBoxLayout()

		self.input_현장명 = QLineEdit()
		self.input_현장명.setPlaceholderText('MOD경우 현장명을 넣으세요')
		self.input_현장명.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self.pb_search = QPushButton('검색')
		form.addWidget(self.input_현장명)
		form.addWidget(self.pb_search)
		self.vlayout.addLayout(form)
		# self.setLayout(self.vlayout)
		wid.setLayout(self.vlayout)
		self.setCentralWidget(wid)
		self.show()
		self.pb_search.clicked.connect(self.slot_search)

		self.setMinimumSize( 480,240)

	def get_api_and_model_table_generate(self) -> bool:
		if (is_api_ok := self._check_api_Result() ) :
			self.is_api_ok = is_api_ok

			if self.app_DB_data:
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
			else:
				return False
		else: 
			return False


	def _render_frame_MVC(self, tableView):
		if hasattr(self, 'table') :
			self.table.deleteLater()

		self.vlayout.addWidget(tableView)	

		self.show()
		return (tableView,self.vlayout)
	

	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()

		match actionName:
			case 'Select'|'select':
				rows_list = msg.get('data').get('rows')
				self.signal.emit( {
					'select': [self.app_DB_data[row] for row in rows_list ]
				} )

				# eval(f"self.{actionName}()")


	def slot_search(self):
		self.search_msg = {
			'search' :self.input_현장명.text()			
		}
		self.pageSize = 0
		self.suffix =  f'?page_size={self.pageSize}'
		self.search_and_display()


	def search_and_display(self):
		if self.get_api_and_model_table_generate():
			self.setMinimumSize( 900, 600)
			self.table.signal.connect (self.slot_table_siganl)
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')

