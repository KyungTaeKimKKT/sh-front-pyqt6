import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from pathlib import Path

import typing

from modules.PyQt.component.search_for_tab import Search_for_tab
# from modules.PyQt.Tabs.Elevator_Info.Datas import AppData_Elevator_Info as AppData
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import (
    한국정보__for_Tab, 
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


	def UI(self):
		wid = QWidget()
		self.vlayout = QVBoxLayout()
		self.wid_search_for_tab = Search_for_tab (
			parent=self, 
			search_msg = self.search_msg, 
			pb_text='한국Elevator 검색', 
			placeholder="'건물명', '건물주소','시도','시군구' 에 대해 검색합니다.",
			pageSize = self.pageSize
		)
		self.wid_search_for_tab.signal.connect(self.slot_search_for_tab)
		self.vlayout.addWidget(self.wid_search_for_tab)

		self.tableView = App_TableView(self)
		self.vlayout.addWidget(self.tableView)	
		wid.setLayout(self.vlayout)
		self.setCentralWidget(wid)
		self.show()

		self.setMinimumSize( 480,240)

	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()

		match actionName:
			case 'Select'|'select':
				rows_list = msg.get('data').get('rows')
				self.signal.emit( {
					'select': [self.app_DB_data[row] for row in rows_list ]
				} )


