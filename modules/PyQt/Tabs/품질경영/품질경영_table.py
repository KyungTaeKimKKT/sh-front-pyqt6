
from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing
import pathlib
import pandas as pd
import urllib
from datetime import date, datetime

from modules.PyQt.User.toast import User_Toast
from config import Config as APP

from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.User.Tb_Model import Base_TableModel
from modules.PyQt.User.Tb_Delegate import Base_Delegate
from modules.PyQt.Tabs.Base import Base_App

import modules.user.utils as utils

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 품질경영_Base_TableView( My_TableView):
	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ...) -> None: 
		super().__init__(parent)


	def user_defined_slot_h_header_contextMenu(self, action:str, row:int):
		match action:
			case 'File첨부'|'활동현황_추가'|'활동현황_보기'|'활동종료'|'Select'|'select':
				self.signal.emit( {
					'action': action.lower(),
					'data' : {
						'row': row,
					}
				})
			case _:
				User_Toast( parent=self, title='지원하지 않는 Action 명령어입니다.', 
			   				text=f"action 명령어 {action}", style='WARNING')

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
			case '완료파일수'|'첨부파일수':
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
	
	def slot_download_첨부파일(self, row:int, col:int):
		match self.parent.header[col]:
			case '첨부파일수':
				self.func_download_multiple_files( self.parent.app_DB_data[row].get('file_fks') )
			# case '완료파일수':
			# 	self.func_download_multiple_files( self.parent.app_DB_data[row].get('완료file_fks') )


	def func_download_multiple_files(self, file_fks:list) -> None:
		for obj in file_fks:
			fName, contents = utils.download_file_from_url(obj.get('file'))

			if fName :
				options =  QtWidgets.QFileDialog.Options()
				options |=  QtWidgets.QFileDialog.DontUseNativeDialog
				User_fName, _ = QtWidgets.QFileDialog.getSaveFileName(parent=None, 
													caption="Save File", 
													directory=str(pathlib.Path.home()/ fName), 
													filter="*", 
													options = options)
			else:
				User_Toast( parent=self, title='File Download error',	text = 'File Download error', style='Error')
			 
			if User_fName:
				with open(User_fName, 'wb') as download:
					download.write(contents)