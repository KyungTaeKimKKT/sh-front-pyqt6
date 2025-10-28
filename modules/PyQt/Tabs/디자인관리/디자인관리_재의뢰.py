from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime
import copy

import pathlib
import openpyxl
import typing

import concurrent.futures
import asyncio
import time

### 😀😀 user : ui...
from modules.PyQt.Tabs.디자인관리.ui.Ui_tab_디자인관리_재의뢰 import Ui_Tab_App as Ui_Tab

###################
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

class 재의뢰__for_Tab( QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )

		
		self.is_Auto_조회_Start = True

		self.param = ''		
		self.defaultParam = f"page_size=25"

		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)
		### wid_search hide
		self.label_header = QLabel('재의뢰는 기존의뢰찾기를 클릭하여 기존 의뢰를 검색하여 작성하기 바랍니다')
		self.label_header.setStyleSheet ( "background-color:black;color:yellow;font-weight:bold;")		
		self.ui.horizontalLayout.addWidget(self.label_header)
		self.ui.Wid_Search_for.hide()

		self.triggerConnect()
		
		if hasattr(self, 'url_db_fields'):
			self._get_DB_Field(self.url_db_fields  )		
			ui_search_config_dict = {}
			if hasattr( self, '구분list') :
				ui_search_config_dict['구분list'] = self.구분list
			if hasattr( self, '고객사list'):
				ui_search_config_dict['고객사list'] = self.고객사list
			if ui_search_config_dict and hasattr( self.ui.Wid_Search_for, '_update_config'):
				self.ui.Wid_Search_for._update_config( **ui_search_config_dict )
			
		

		self._init_helpPage()

		self._init_AutoStart()


	def triggerConnect(self):
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect ( self.slot_download)
		self.ui.Wid_Table.signal_refresh.connect(lambda:self.slot_search_for(self.param) )

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))

		### 😀 추가
		self.ui.PB_search_exist.clicked.connect ( self.slot_PB_search_exist)

	#### app마다 update 할 것.😄
	def run(self):
		
		return 
	
	############
	@pyqtSlot()
	def slot_PB_search_exist(self):
		from modules.PyQt.Tabs.디자인관리.디자인관리_이력조회 import 이력조회__for_Tab, 이력조회__for_Tab_선택_Enabled
		dialog = QDialog(self)
		dialog.setMinimumSize ( 600,800)
		dialog.setWindowTitle ('이력조회')
		vLayout = QVBoxLayout()
		appDict = Utils.get_Obj_From_ListDict_by_subDict ( INFO.APP_권한, {'div':'디자인관리', 'name':'이력조회'})

		wid_이력조회 = 이력조회__for_Tab_선택_Enabled(self, '', is_Auto_조회_Start= False, **appDict )
		wid_이력조회.signal_select_row.connect ( lambda msg: self.slot_signal_row_select(msg, dialog ))
		vLayout.addWidget (wid_이력조회)
		dialog.setLayout( vLayout)
		dialog.show()

	@pyqtSlot(dict)
	def slot_signal_row_select(self, msg:dict, dialog:QDialog):
		""" 
			select된 apiDict를 {'id': -1, '의뢰차수' : +1 } 로 하여, post 하고, 다시 refresh

		"""
		def _sendData_정리( sendData:dict, 유지할key:list):
			copyed = copy.deepcopy(sendData)
			for key, value in sendData.items():
				if not key in 유지할key:
					del copyed[key]

			copyed['의뢰여부']=False
			copyed['의뢰차수'] = copyed['의뢰차수']+1

			del copyed['id']
			return copyed
		
		dialog.close()
		# text = ''
		# for key, value in msg.items():
		# 	if key == '현장명' :
		# 		text += f" {key} : {value} \n"
		# 	if key == '의뢰차수':
		# 		text += f" {key} : {value+1}"

		text_list = [ f"{key} : {value if key == '현장명' else value+1} " for key, value in msg.items() if  key in ['현장명', '의뢰차수']]
		text =('\n').join( text_list)
		dlg_res_button = Utils.generate_QMsg_question(self, title="재의뢰 확인", text = f" {text} (으)로 진행하시겠읍니까?\n (선택된 내용을 복사하므로,  \n 꼭 내용 확인 후 의뢰하시기 바랍니다.)")
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			유지할keys :list[str]= self.table_config['table_header'] +['의뢰여부','현장명_fk','의뢰파일수','의뢰file_fks']
			sendData = _sendData_정리( msg, 유지할keys )

			_isOk, _json = APP.API.Send ( self.url, {'id':-1}, sendData )
			if _isOk:
				self.slot_search_for( self.param)
			else:


		



	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""
		self.loading_start_animation()	

		self.param = param 
		
		url = self.url + '?' + param

		###😀 GUI FREEZE 방지 ㅜㅜ;;
		pool = QThreadPool.globalInstance()
		self.work = Worker(url)
		self.work.signal_worker_finished.signal.connect ( self.table_update )
		pool.start( self.work )



	@pyqtSlot(bool, bool, object)
	def table_update(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
		if not _isOk:
			self._disconnect_signal (self.work.signal_worker_finished)
			self.loading_stop_animation()
			Utils.generate_QMsg_critical(self)
			return 

		if is_Pagenation :
			search_result_info:dict = copy.deepcopy(api_datas)
			self.api_datas = search_result_info.pop('results')
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, **search_result_info )
		else:
			self.api_datas = api_datas
			self.ui.Wid_Search_for._update_Pagination( is_Pagenation, countTotal=len(api_datas) )

		self.ui.Wid_Table._update_data(
			api_data=self.api_datas, 
			url = self.url,
			**self.db_fields,
			# table_header = 
		)	
		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()

	@pyqtSlot()
	def slot_pb_info(self):
		tb_text = [ 
			'<p style="background-color:black;color:yellow;"> 사용법</p>',
			'<p> 1.목적 : USER별로 APP사용권한을 설정합니다.  </p>',
			'<p> 2.특이사항 : admin은 is_Active, 순서 및 사용자에 한합니다. (그외는 개발자 영역으로 변경시 프로그램 실행 안됨 ) </p>',
			'<p>   -. is_Active : True가 APP활성화 </p>',
			'<p>   -. 순서 : 표시순서로 1~ 100,000 까지 (표시순서가 우선하므로  같은 DIV 그룹이더라도 표시순서에 따라 표시)</p>',
			'<p>   -. 사용자 : 사용자수에 마우스를 HOVER하면 현재 사용자가 나오고, 마우스 우클릭하면 변경 메뉴 표시</p>',		
			'<p> 3.menu : 해당 지점에서 마우스 우클릭 시 </p>',	
			'<p>   3-1. Horizontal Menu : 해당 row(줄)의 header</p>',	
			'<p>      -. New : 선택한 row의 아래로 신규 row 생성 </p>',	
			'<p>      -. Delete : 선택한 row를 <span style="background-color:yellow;color:red;">DB 에서 삭제</span> </p>',	
			'<p>   3-2. Vertical Menu:  없음 </p>',
			'<p>   3-3. Table Cell Menu:   </p>',	
			'<p>      -. App사용자 수: 신규 user table이 생성되어 사용자 변경   </p>',	
			'<p> 4.Table data 변경 : 해당 cell을  double click  </p>',	
			'<p>   4-1.변경 불가능 : ["id","app사용자수" ]   </p>',	
			'<p>   4-2.수정 후, 다른 CELL 로 이동하면 DB 저장됨  </p>',	
		]
		self.dlg_page_info.setWindowTitle('Page Info(사용법)')
		self.dlg_tb.setText( ''.join(tb_text))
		self.dlg_tb.setTextBackgroundColor( QColor('yellow'))
		self.dlg_page_info.show()
