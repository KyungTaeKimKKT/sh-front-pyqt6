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

### 😀😀 user : ui...
from modules.PyQt.Tabs.망관리.ui.Ui_tab_망관리_album import Ui_Tab_App as Ui_Tab
from modules.PyQt.Tabs.망관리.widget.Wid_album_망단위 import Wid_album_망단위 ### 😀typing 위해서

# from modules.PyQt.Tabs.망관리.dialog.Dialog_망등록 import Dialog_망등록

###################
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine

from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils



from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

class Album__for_Tab(QWidget, Utils_QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow,   **kwargs ):
		super().__init__( parent )
		self.is_Auto_조회_Start = True
		
		self.param = ''
		self.defaultParam = f"page_size=15"	###😀 현재 5 *3 으로 고정함.

		#### appDict를 받아서 설정.
		self._init_kwargs(**kwargs)

		self.ui = Ui_Tab()
		self.ui.setupUi(self)

		self.triggerConnect()

		if hasattr(self, 'url_db_fields'):
			self._get_DB_Field(self.url_db_fields  )	

		self._init_AutoStart()

			
	def triggerConnect(self):
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		self.ui.Wid_Search_for.signal_download.connect(self.slot_download)

		self.ui.pb_info.clicked.connect (lambda: Dlg_Pdf_Viewer_by_webengine(self, url=self.help_page))
		
		self.ui.PB_Form_New.hide()
		# self.ui.PB_Form_New.clicked.connect(self.slot_PB_Form_New)

	#### app마다 update 할 것.😄
	def run(self):
		return 

	@pyqtSlot(QDialog, dict)
	def slot_form_save(self, dlg:QDialog, formData:dict) -> None:
		""" """
		formData['등록자'] = INFO.USERID
		m2mField = 'files'
		fileNames:dict[int:str] = formData.pop('fileNames', {}) ### fileupload list widget에서 fix 시킴

		futures = []
		with concurrent.futures.ThreadPoolExecutor() as executor:
			for ID, fName in fileNames.items():
				if 'http://' in fName or ID>0:
					pass
				else:
					futures.append( executor.submit (APP.API.Send , INFO.URL_요청사항_FILE,{}, {},[('file', open(fName,'rb'))] ) )
		### future result()는 bool, json 이므로, json의 id로 보냄
		formData[m2mField] = [ future.result()[1].get('id') for future in futures ]

		if INFO.IS_DebugMode :

		is_ok, _json = APP.API.Send( self.url, formData, formData )
		if is_ok:
			dlg.close()
			self.slot_search_for (param= self.param if self.param else self.defaultParam)
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
		""" 여기서는 tabel이 아니라,  album을 update 함. \n
			slot(method 이름은 그대로)
		"""
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

		# if hasattr( self.ui, 'gridLayout'): Utils.deleteLayout(self.ui.gridLayout )
		for idx in range(15):
			wid_album_망단위 : Wid_album_망단위   = getattr(self.ui, f'Wid_album_{idx}' )
			if idx < len(self.api_datas):
				wid_album_망단위._update_data( dataObj = self.api_datas[idx] )
			else:
				wid_album_망단위.hide()
		# for idx, api_data in enumerate(self.api_datas):
		# 	wid_album_망단위 : Wid_album_망단위   = getattr(self.ui, f'Wid_album_{idx}' )
		# 	wid_album_망단위._update_data( dataObj = api_data )



		# self.ui.Wid_Table._update_data(
		# 	api_data=self.api_datas, 
		# 	url = self.url,
		# 	**self.db_fields,			
		# )

		self._disconnect_signal (self.work.signal_worker_finished)
		self.loading_stop_animation()




