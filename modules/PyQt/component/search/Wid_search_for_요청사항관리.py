from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.component.search.Wid_search_for import Wid_Search_for_망관리 as Base_Search
from modules.PyQt.component.search.Ui_search_compenet_요청사항 import Ui_Form 

import pathlib
import pandas as pd

from info import Info_SW as INFO
import modules.user.utils as Utils
from stylesheet import StyleSheet as ST
from config import Config as APP
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Search_for_요청사항( Base_Search):
	signal_search = pyqtSignal(dict, list)

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		self.ui = Ui_Form()

		# self.URL_ExportDBtoExcel =INFO.URL_Elevator_한국정보_DOWNLOAD

		
	def init_InputDict(self) ->None:
		self.inputDict = {
			'search' : self.ui.lineEdit_Search,
			'요청구분' : self.ui.comboBox_Gubun,
			'is_완료' : self.ui.comboBox_Yanro,
			'From일자' : self.ui.dateEdit_From,
			'To일자' : self.ui.dateEdit_To,
		}
		self.page_InputDict = {
			'countOnPage' : self.ui.comboBox_table_row,
			'current_Page' : self.ui.comboBox_curPage,
		}

	def user_defined_ui_setting(self):
		self.ui.frame_Pagenation.hide()
		self.ui.PB_DownloadAll.hide()
		now = QDate.currentDate()
		self.ui.dateEdit_From.setDate( now.addMonths(-1))
		self.ui.dateEdit_To.setDate( now )

		self.ui.comboBox_Gubun.addItems(['All']+INFO.Combo_요청사항_구분_Items)
		self.ui.comboBox_Yanro.addItems( ['All','완료','미완료' ])
		self.handle_checkBox_Date_enabled()

	
	def triggerConnect(self):
		super().triggerConnect()

	def run(self):
		super().run()
		# self.ui.PB_DownloadAll.clicked.connect(self.exportDBtoExcel)

	@pyqtSlot()
	def exportDBtoExcel(self):
		if not self.app_DB_data: return
		
		fName = self._getFName_fromDialog_excelFormat()
		if fName:
			response = APP.API.post_raw_return( 
				self.URL_ExportDBtoExcel, self._get_PostSendData()  )


			if response.ok:
				fName = fName+'.xlsx'
				with open( fName, 'wb') as file:
					file.write(response.content )
				fSize = int(response.headers.get('Content-Length')) / 1000000 
				QMessageBox.information(self, 'File Download 완료',  f"{fName} 으로 저장되었읍니다.({fSize:.1f}Mbytes) ",
							QMessageBox.StandardButton.Ok , QMessageBox.StandardButton.Ok  )


	def _get_api_query_params(self, search_dict:dict, is_pageSize:bool=True) -> str:
		self.pageSize = self._get_curTableRow()

		self.search = search_dict.pop('search')
		query_params = f'?search={self.search}&'
		if search_dict:
			for (key, value ) in search_dict.items():
				if value == 'All' : continue
				match key:
					case 'is_완료':
						query_params += f"{key}={True if '완료'==value else False}&"
					case 'From일자'|'To일자':
						if not self._is_enabled_등록일조회(): continue
						else: query_params += f"{key}={value}&"
					case _:
						query_params += f"{key}={value}&"

			query_params += f'page_size={self.pageSize if is_pageSize else 0}'

		self.query_params = query_params
		return query_params


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