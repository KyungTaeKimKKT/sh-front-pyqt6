from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import time
import pandas as pd
import urllib
from datetime import date, datetime
import copy
from pathlib import Path
###################
from modules.PyQt.dialog.loading.dlg_loading import LoadingDialog

from config import Config as APP
from info import Info_SW as INFO

from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

from modules.PyQt.User.toast import User_Toast
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Utils_QWidget:

	def _update_page_info(self, url:str):
		self.help_page = url
		self._init_helpPage()

	def _update_page_info_title(self, info_title:str):
		self.ui.label_target.setText(info_title)

	def _update_update_time(self, _text:str|None=None):
		""" 업데이트 시간을 업데이트 합니다. """
		_time = datetime.now().strftime('%H시 %M분 %S초')
		if _text :
			self.ui.label_update_time.setText(f"{_time} : {_text}")
		else:
			self.ui.label_update_time.setText(f"{_time}")
	
	def _set_info_title(self, info_title:str):
		self.ui.label_target.setText(info_title)

	def _disconnect_signal(self, signal:pyqtSignal, slot=None):
		""" signal과 slot을 연결 해제합니다. 
			slot이 없으면, 모든 slot을 연결 해제합니다.
		"""
		try:
			if slot is not None:
				signal.disconnect(slot)
			else:
				signal.disconnect()

		except:
			pass

	def _init_kwargs(self, **kwargs):
		""" main 함수에서 kwargs로 넘긴, Api_App권한 MODEL DATA DICT를 초기화함."""
		self.div :str
		self.name : str
		self.url : str
		self.api_uri : str
		self.api_url : str
		self.user_pks : list[int] ### m2m field
		self.비고 : str
		self.is_Active : bool
		self.is_Run : bool
		self.순서 :int
		self.is_dev :bool
		self.help_page : str

		for key, value in kwargs.items():
			setattr(self, key, value)
		if hasattr(self, 'api_uri') and self.api_uri and hasattr(self, 'api_url') and self.api_url:
			if isinstance(self.api_uri, str) and isinstance(self.api_url, str):
				self.url = self.api_uri+self.api_url
		if hasattr(self, 'api_uri') and self.api_uri and hasattr(self, 'db_field_url') and self.db_field_url:
			if isinstance(self.api_uri, str) and isinstance(self.db_field_url, str):
				self.url_db_fields = self.api_uri + self.db_field_url
		
		self.table_name = f"{self.div}_{self.name}_appID_{self.id}"


	def _init_AutoStart(self):
		if self.is_Auto_조회_Start:
			### 자동 조회 BY DEFAULT_parameter
			self.ui.Wid_Search_for.param = self.param if self.param else self.defaultParam 
			self.slot_search_for(self.param if self.param else self.defaultParam )
	
	def _init_helpPage ( self ) -> None:
		""" 여러 조건들로 ui.pb_info enable or disable"""
		if hasattr(self.ui, 'pb_info'):
			pb_info : QPushButton = self.ui.pb_info
			if hasattr(self, 'help_page') and self.help_page is not None  :
				            # URL 유효성 검사
				try:
					if 'http' not in self.help_page:
						url = INFO.URI + self.help_page
					else:
						url = self.help_page
					request = urllib.request.Request(
						url, 
						headers={'User-Agent': 'Mozilla/5.0'}
					)
					urllib.request.urlopen(request, timeout=3)
					pb_info.setEnabled(True)
					pb_info.setToolTip("유효한 도움말 페이지가 있읍니다")
					self.help_page = url
				except Exception as e:
					pb_info.setEnabled(False)
					pb_info.setToolTip(f"URL이 유효하지 않읍니다: {str(e)}")
					self.help_page = None
			else:
				pb_info.setEnabled(False)		


	def _init_dialog(self) -> QDialog:
		dlg = QDialog(self)
		vLayout = QVBoxLayout()
		self.dlg_tb = QTextBrowser(self)
		self.dlg_tb.setAcceptRichText(True)
		self.dlg_tb.setOpenExternalLinks(True)
		vLayout.addWidget(self.dlg_tb)
		dlg.setLayout(vLayout)
		dlg.hide()

		return dlg

	def _get_DB_Field(self, url:str=INFO.URL_DB_Field_Api_App권한_View) ->None:
		""" server에서 DB_Field를 get 하여 , setattr 함
			server 에서 다음곽 같은 형태, 
		   { 
				'fields_model' : model_field, =>{fieldName:type}
				'fields_serializer' : serializer_field, -=> {fieldname:type}
				'fields_append' : {'app사용자수' : 'IntegerField'} ==> model과 serializer차이점으로 serializer에 추가(보통, ㅡmethodfield)
															==> sendData 에서 보통 제외되니 매우 중요.
				'fields_delete' : {name: type} ==> 형태로 serializer에서 model field가 빠진 내용... 하지만 front는 serializer 된 내용만 받으니 별로 중요치 않음.
				'table_config' : {
					'table_header' :['id', 'div', 'name','url','api_url','순서','비고','app사용자수', 'is_Active','is_Run','등록일'],
					'no_Edit_cols' :['id', 'app사용자수','등록일'],
					'hidden_columns' [ 'id',...],
				}
			}

		"""
		_is_ok, self.db_fields = APP.API.getAPI_View(url=url)

		if _is_ok:
			for (key, value) in self.db_fields.items():
				setattr( self, key, value )
			# {'id': 'BigAutoField', 'div': 'CharField', 'name': 'CharField', 'url': 'CharField', 'api_url': 'CharField', '비고': 'CharField', '등록일': 'DateTimeField', 'is_Active': 'BooleanField', 'is_Run': 'BooleanField', '순서': 'IntegerField', 'user_pks': 'ManyToManyField'}

	def _render_activate(self, sender:QWidget ):
		sender.setStyleSheet('background-color:yellow;color:black;font-weight:bold;')
		

	def loading_start_animation(self, movie=":/movies/loading.gif", timer_after:int= 1000):
		self.is_api_finished = False
		self.__start_animation = time.time()
		QTimer.singleShot( timer_after,  lambda:self._create_dlg_loading(movie, timer_after) )

	def _create_dlg_loading(self, movie=":/movies/loading.gif", start_time:int=1000):
		if not self.is_api_finished and (time.time() - self.__start_animation) > 1:
			if INFO.MAIN_WINDOW:
				INFO.MAIN_WINDOW.show_loading_dialog( movie=movie, start_time=start_time)
			else:
				self.window().show_loading_dialog( movie=movie, start_time=start_time)
			# self.dlg_loading = LoadingDialog(self, movie=":/movies/loading.gif", start_time=start_time)
		
	def loading_stop_animation(self):
		self.is_api_finished = True
		
		if INFO.MAIN_WINDOW:
			INFO.MAIN_WINDOW.hide_loading_dialog()
		else:
			self.window().hide_loading_dialog()
		# if hasattr( self, 'dlg_loading') and isinstance(self.dlg_loading, LoadingDialog):
		# 	self.dlg_loading.close()
		
	@pyqtSlot()
	def slot_download(self):
		if not self.api_datas: return

		if 'page_size=0' in self.param:
			self.save_data_to_file ( False, True, self.api_datas)
		else:
			try:
				param = param if param else self.param
			except:
				param = self.param

					###😀 GUI FREEZE 방지 ㅜㅜ;;
			pool = QThreadPool.globalInstance()
			self.work_download_util = Worker(self.url +'?'+ self._get_param_to_get_all_datas(param))
			self.work_download_util.signal_worker_finished.signal.connect ( self.save_data_to_file )
			pool.start( self.work_download_util )
			self.loading_start_animation()

	@pyqtSlot(bool, bool, object)
	def save_data_to_file(self, is_Pagenation:bool, _isOk:bool, api_datas:object) ->None:
		self.loading_stop_animation()

		fName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
			"Save File", str(Path.home() / "Downloads"), 
			"Excel Files(*.xlsx)" )

		if fName:
			self._save_api_datas_to_excel(fName=fName+'.xlsx', _type={'API':api_datas})
		try:
			self.work_download_util.signal_worker_finished.signal.disconnect()
		except:
			pass

	def _get_param_to_get_all_datas(self, param) -> str:
		import copy
		queryList = copy.deepcopy(param).replace('?','').split('&')

		for index, query in enumerate(copy.deepcopy(queryList) ):
			if 'page_size' in query:
				queryList[index] = 'page_size=0'

		return '&'.join(queryList)
	
	def _save_api_datas_to_excel(self, fName:str, _type:dict ) -> None:
		""" kwargs 
			_type : { 'API' : api_datas, 'TABLEVIEW' : tableView }
			API : api_datas 를 엑셀로 저장
			TABLEVIEW : tableView 보이는 data 를 엑셀로 저장
			
		"""
		key = list(_type.keys())[0]
		match key:
			case 'API':
				df = pd.DataFrame(_type[key], columns=self.table_config.get('table_header'))
				df = df.drop(columns=self.table_config.get('hidden_columns') )

			case 'TABLEVIEW':
				tableView = _type[key]	
				model = tableView.model()
				visible_rows = model.rowCount(QModelIndex())
				visible_columns = 0
				visible_headers = []
				
				### 보이는 컬럼 수와 헤더 가져오기
				for col in range(model.columnCount(QModelIndex())):
					if not tableView.isColumnHidden(col):
						visible_columns += 1
						header = model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
						visible_headers.append(header)
				
				### 보이는 데이터만 추출
				visible_data = []
				for row in range(visible_rows):
					row_data = []
					for col in range(model.columnCount(QModelIndex())):
						if not tableView.isColumnHidden(col):
							index = model.index(row, col)
							value = model.data(index, Qt.ItemDataRole.DisplayRole)
							row_data.append(value)
					visible_data.append(row_data)
				
				# 보이는 데이터로 DataFrame 생성
				df = pd.DataFrame(visible_data, columns=visible_headers)

			case _:
				raise ValueError(f"Invalid type: {type}")
		
		# 엑셀로 저장		else:

		with pd.ExcelWriter(fName, engine='xlsxwriter') as writer:
			df.to_excel(writer, sheet_name='download', index=False)
			workbook = writer.book
			worksheet = writer.sheets['download']
			cell_format = workbook.add_format({'text_wrap':True})
			worksheet.set_column('A:Z', cell_format=cell_format)

		User_Toast(parent=INFO.MAIN_WINDOW, duration=2000, title="엑셀 저장", text=f"엑셀 저장 완료", style='SUCCESS')
