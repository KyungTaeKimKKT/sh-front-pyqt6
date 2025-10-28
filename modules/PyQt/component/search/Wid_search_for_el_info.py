from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.component.search.Wid_search_for import Wid_Search_for_망관리 as Base_Search
from modules.PyQt.component.search.Ui_search_compenet_elevator_info import Ui_Form

import pathlib
import pandas as pd
import time, os

from info import Info_SW as INFO
import modules.user.utils as Utils
from stylesheet import StyleSheet as ST
from config import Config as APP
from modules.user.async_api import Async_API_SH
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Search_for_EL_Info( Base_Search):
	signal_search = pyqtSignal(dict, list)
	signal_download = pyqtSignal()

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		self.ui = Ui_Form()

		self.URL_ExportDBtoExcel =INFO.URL_Elevator_한국정보_DOWNLOAD

	def init_InputDict(self) ->None:
		self.inputDict = {
			'search' : self.ui.lineEdit_Search,
			'시도' : self.ui.lineEdit_SiDo,
			'From수량' : self.ui.spinBox_From_Surang,
			'To수량'	: self.ui.spinBox_To_Surang,
			'From일자' : self.ui.dateEdit_From,
			'To일자' : self.ui.dateEdit_To,
		}
		self.page_InputDict = {
			'countOnPage' : self.ui.comboBox_table_row,
			'current_Page' : self.ui.comboBox_curPage,
		}

	def user_defined_ui_setting(self):
		self.ui.frame_Pagenation.hide()
		now = QDate.currentDate()
		self.ui.dateEdit_From.setDate( now.addYears(-21))
		self.ui.dateEdit_To.setDate( now.addYears(-10) )

		self.handle_checkBox_Date_enabled()
		self.handle_checkBox_Kumo_enabled()

	def triggerConnect(self):
		super().triggerConnect()
		self.ui.checkBox_Kumo.clicked.connect(self.handle_checkBox_Kumo_enabled )

	def run(self):
		super().run()

		self.ui.PB_DownloadAll.clicked.connect(self.exportDBtoExcel)

	@pyqtSlot()
	def exportDBtoExcel(self):

		if not self.app_DB_data: return

		self.fName = self._getFName_fromDialog_excelFormat()
		if self.fName:

			self.progressTimer = QTimer(self)
			# self.progressTimer.setInterval(500)
			self.progressTimer.timeout.connect(self.display_progressDialog )
			self.progressTimer.start(1000)
			self.progressTimerCount = 0

			self.progressDialog = QProgressDialog('Server에서 다운로드 준비 중입니다...', '', 0, 100, self)
			self.progressDialog.setCancelButton(None)
			self.progressDialog.setWindowModality(Qt.WindowModality.WindowModal)
			self.progressDialog.setMinimumDuration(0)

			async_API = Async_API_SH()
			async_API.signal_Response.connect(self.post_Response )

			# https://realpython.com/python-pyqt-qthread/
			pool = QThreadPool.globalInstance()
			pool.start( lambda: async_API.Post ( self.URL_ExportDBtoExcel, self._get_PostSendData() )  )





	@pyqtSlot(object)
	def post_Response(self, res:object):
		if res is None : return

		from modules.PyQt.Qthreads.socket_client import Socket_client
		sock_client = Socket_client( INFO.IP_SOCKET_SERVER, INFO.PORT_SOCKET_SERVER, res)
		sock_client.signal_received.connect(self.file_download_by_socket)

		sock_client.run()

	@pyqtSlot(bytes)
	def file_download_by_socket(self, datas:bytes) :
		self.progressTimer.stop()
		self.progressDialog.close()

		fName = self.fName+'.xlsx'
		with open(fName, 'wb') as fp:
			fp.write(datas)
		fSize = os.path.getsize(fName) / 1000000
		QMessageBox.information(self, 'File Download 완료',  f"{fName} 으로 저장되었읍니다.({fSize:.1f}Mbytes) ",
					QMessageBox.StandardButton.Ok , QMessageBox.StandardButton.Ok  )

	@pyqtSlot()
	def display_progressDialog (self):
		if self.progressTimerCount is None: return 

		self.progressDialog.show()
		self.progressTimerCount += 1
		self.progressDialog.setLabelText(f'Server에서 다운로드 준비 중입니다...(경과시간:{self.progressTimerCount*0.5}초))')
		self.progressDialog.setValue ( self.progressTimerCount  )

	@pyqtSlot(int, int)
	def handle_progress(self, progress:int, filesize:int ):
		fileSize = str(int(filesize/1000)) +' KBytes'
		소요시간 =  str( time.time()-self.start ) +' 초'

		self.progressDialog.setLabelText(f"Downloading... ( {fileSize if filesize else ''} , {소요시간 })")
		self.progressDialog.setValue (progress)

	@pyqtSlot(dict)
	def finished_download(self, res:dict):
		fName = self.fName
		self.progressDialog.close()
		headers = res.get('headers')
		contents = res.get('contents')
		if headers and contents:
			fName = fName+'.xlsx'
			with open( fName, 'wb') as file:
				file.write(contents )
			fSize = int( headers.get('Content-Length')) / 1000000
			QMessageBox.information(self, 'File Download 완료',  f"{fName} 으로 저장되었읍니다.({fSize:.1f}Mbytes) ",
						QMessageBox.StandardButton.Ok , QMessageBox.StandardButton.Ok  )

	@pyqtSlot()
	def handle_checkBox_Kumo_enabled(self):
		self.ui.frame_Kumo.setVisible( self._is_enabled_규모() )


	def _get_api_query_params(self, search_dict:dict, is_pageSize:bool=True) -> str:
		self.pageSize = self._get_curTableRow()

		self.search = search_dict.pop('search')
		query_params = f'?search={self.search}&'
		if search_dict:
			for (key, value ) in search_dict.items():
				if value == 'All' : continue
				match key:
					case 'From일자'|'To일자':
						if not self._is_enabled_등록일조회(): continue
						else: query_params += f"{key}={value}&"
					case 'From수량'|'To수량':
						if not self._is_enabled_규모(): continue
						else: query_params += f"{key}={value}&"
					case _:
						query_params += f"{key}={value}&"

			query_params += f'page_size={self.pageSize if is_pageSize else 0}'

		self.query_params = query_params
		return query_params

	def _is_enabled_규모(self) -> bool:
		return self.ui.checkBox_Kumo.isChecked()

	def _getFName_fromDialog_excelFormat(self) -> str:
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fName, _ = QFileDialog.getSaveFileName(self,
			"Save File", str(pathlib.Path.home() / "Downloads"),
			"Excel Files(*.xlsx)", options = options)

		if fName:
			return fName
			self.save_to_excel(fName=fName+'.xlsx')

	def _get_query_for_all_data(self) -> str:
		query_list = self.query_params.split('&')
		del query_list[self._get_index_for_pageSize() ]
		return  '&'.join(query_list)+'&page_size=0'

	def _get_index_for_pageSize(self) -> int:
		for index, query in enumerate(self.query_params.split('&') ):
			if 'page_size' in query:
				return index

	def _get_PostSendData(self) -> dict:
		import copy
		queryList = copy.deepcopy(self.query_params).replace('?','').split('&')
		sendDict = {}
		for query in queryList:
			split = query.split('=')
			if split[1] :
				sendDict[split[0]] = split[1]
		return sendDict