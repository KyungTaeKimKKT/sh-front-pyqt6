from local_db.models import Table_Config
from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import concurrent.futures

import pathlib
import typing
import copy
import json
import time
from modules.PyQt.Tabs.영업수주.tables.Wid_Table_Builder import Wid_Table_Builder
from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model, TableModelBuilder
# from modules.PyQt.compoent_v2.table.Base_Table_Delegate import Base_Table_Delegate
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer

# from modules.PyQt.Tabs.생산지시서.dialog.list_edit.dlg_판금처선택 import 판금처선택다이얼로그

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()
ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableView_영업수주_관리(Base_Table_View):
	pass

	# signal_refresh = pyqtSignal()
	# signal_select_rows = pyqtSignal(list)
	# signal_select_row = pyqtSignal(dict)
	# def __init__(self, parent, **kwargs):
	# 	super().__init__(parent, **kwargs)
	# 	# 행 선택 모드 설정
	# 	self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
	# 	# cell 선택 모드 설정
	# 	# self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
	# 	# self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

	# def setModel(self, model):
	# 	""" select_row 시그널 연결 필수 """
	# 	super().setModel(model)
	# 	# model이 설정된 후에 selection changed 시그널 연결
	# 	self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        

class TableModel_영업수주_관리(Base_Table_Model):
	"""
		kwargs로 모델 속성을 초기화할 수 있는 생성자
	"""
	pass
	# def __init__(self, parent, **kwargs):
	# 	super().__init__(parent, **kwargs)

	# def user_defined_data( self, index, role, value):
	# 	value = super().user_defined_data(index, role, value)
	# 	if role == Qt.ItemDataRole.DisplayRole:
	# 		if isinstance(value, str) and 'T' in value and len(value) > 16:
	# 			try:
	# 				dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
	# 				return dt.strftime('%y-%m-%d %H:%M')  # 사용자 친화적 형식
	# 			except (ValueError, TypeError):
	# 				pass
	# 		return value 
	# 	return value

	# def user_defined_DecorationRule(self, index, value):
	# 	rowNo = index.row()
	# 	colNo = index.column()
	# 	if colNo == self.header.index('진행현황'):
	# 		value = self._data[rowNo][colNo]
	# 		if value == 'Close':
	# 			return QtGui.QIcon(f':/icons/true.jpg')
	# 		else:
	# 			return QtGui.QIcon(f':/icons/false.png')

	# def user_defined_BackgroundRole(self, index:QModelIndex, role):
	# 	rowNo = index.row()
	# 	colNo = index.column()
	# 	if colNo == self.header.index('진행현황'):
	# 		value = self._data[rowNo][colNo]
	# 		if value == 'Close':
	# 			return QBrush(QColor("green"))


	# 	if hasattr(self, 'cell_menus_cols') and self.header[index.column()] in self.cell_menus_cols:
	# 		return eval( self.cell_menus_cols_color) if hasattr(self, 'cell_menus_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkYellow))
	# 	if hasattr(self, 'no_Edit_cols') and self.header[index.column()] in self.no_Edit_cols:
	# 		return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
	# 	if hasattr(self, 'no_Edit_rows') and index.row() in self.no_Edit_rows:
	# 		return eval( self.no_Edit_rows_color) if hasattr(self, 'no_Edit_rows_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
	# 		# return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))

	# def user_defined_ForegroundRole(self, index, role):
	# 	rowNo = index.row()
	# 	colNo = index.column()
	# 	# if colNo == self.header.index('HTM_Sheet'):
	# 	# 	return QBrush(QColor("white"))
	# 	# if colNo == self.header.index('JAMB_Sheet'):
	# 	# 	return QBrush(QColor("white"))
		

class Delegate_영업수주_관리(My_Table_Delegate):
	pass
# 	def __init__(self, parent, **kwargs):
# 		super().__init__(parent, **kwargs)
# 		self.kwargs = kwargs

	# def user_defined_creatorEditor_설정(self, widget:object, **kwargs) -> object:
	# 	match kwargs['key']:
	# 		case 'claim_file_fks'|'claim_file_수':
	# 			if isinstance(kwargs['parent'], QTableView):
	# 				pos = kwargs['parent'].viewport().mapToGlobal(kwargs['option'].rect.topRight())
	# 			else:
	# 				pos = kwargs['parent'].mapToGlobal(kwargs['option'].rect.topRight())
				
	# 			판금처_list = [ _dict.get('판금처') for _dict in self.kwargs.get('판금처_list_dict', []) ]

	# 			dialog = 판금처선택다이얼로그(kwargs['parent'], 판금처_list=판금처_list, pos=pos)
                
	# 			if dialog.exec() == QDialog.DialogCode.Accepted:
	# 				value = dialog.get_value()
	# 				# 모델 데이터 직접 업데이트
	# 				kwargs['index'].model().setData(kwargs['index'], value, Qt.ItemDataRole.EditRole)
                
	# 			return None  # 셀 내에 에디터를 표시하지 않음
	# 		case 'action_fks' | 'action_수':
	# 			return None

	# 	return widget
	
	# def setModelData(self, editor, model:QAbstractItemModel, index:QModelIndex):		

	# 	if isinstance(editor, 판금처선택다이얼로그):
	# 		value = editor.get_value()
	# 	else:
	# 		value = Object_Get_Value(editor).get()
	# 	ic(value)

	# 	prevValue = model.data(index, Qt.ItemDataRole.DisplayRole)		
	# 	model.setData(index, value, Qt.ItemDataRole.EditRole)



TABLE_NAME = '영업수주_관리'

HOVER_LIST = []

# # 빌더 패턴을 사용한 테이블 모델 생성
# model = Base_TableModel.builder(parent_widget) \
#     .with_header(['id', '이름', '나이', '성별']) \
#     .with_data(data_list) \
#     .with_header_type({'id': 'BigAutoField', '나이': 'IntegerField', '성별': 'BooleanField'}) \
#     .with_non_editable_columns(['id']) \
#     .with_formatter('나이', lambda value, index, model: f"{value}세") \
#     .with_background_rule(lambda index, value, model: QtGui.QColor('lightblue') if index.row() % 2 == 0 else None) \
#     .build()

# # 런타임에 규칙 추가
# model.add_formatter('이름', lambda value, index, model: f"[VIP] {value}" if value in vip_list else value)


class Wid_Table_for_영업수주_관리(QWidget , Handle_Table_Menu, Wid_Table_Builder):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()
	signal_select_row = pyqtSignal(dict)
	signal_select_rows = pyqtSignal(list)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_영업수주_관리
		self.table_model : TableModel_영업수주_관리
		self.delegate : Delegate_영업수주_관리

		self.table_config_api_datas : list[dict] = []
		self.table_config = {}
		self.prev_table_config = {}
		self.api_datas : list[dict] = []
		self.prev_api_data : list[dict] = []
		self.url : str = ''
		self.fields_model :dict[str:str] = {}
		self.fields_append :dict[str:str] = {}
		self.fields_delete :dict[str:str] = {}
		self.table_config :dict = {}
		self.구분list : dict[str] = {}
		self.고객사list :dict[str]

		self.model_data : list[list[any]] = []


	def UI_no_data(self):
		""" 데이터가 없는 경우 표시할 위젯 """
		self.wid_no_data = QLabel('데이터가 없읍니다.')
		self.wid_no_data.setStyleSheet('font-size: 20px; font-weight: bold; color: gray;')
		self.wid_no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.vLayout_main.addWidget(self.wid_no_data)
		self.wid_no_data.hide()
		return self.wid_no_data
	
	def show_table_hide_no_data(self, is_show:bool=True):
		""" table_view 위젯과 no_data 위젯 배타적 표시 """
		if not hasattr(self, 'wid_no_data'): return
		if not hasattr(self, 'table_view'): return
		self.wid_no_data.setVisible(not is_show)
		self.table_view.setVisible(is_show)


	def UI(self):
		self.vLayout_main = QVBoxLayout()
		# self.tableView = eval(f"TableView_{TABLE_NAME}(self)")
		# self.vLayout_main.addWidget(self.tableView)		
		self.vLayout_main.addWidget(self.UI_no_data())
		self.setLayout(self.vLayout_main)

	def fetch_table_config_from_api(self) -> list[dict]:
		"""API에서 받은 테이블 설정을 반환"""
		if self.table_name:
			url = INFO.URL_CONFIG_TABLENAME + f"?table_name={self.table_name}&page_size= 0"
			_isOk, _json = APP.API.getlist( url)
			if _isOk:
				return _json
		return []


	def process_table_config_from_api(self, _json:list[dict]):
		"""API에서 받은 테이블 설정을 처리하여 테이블 구성에 적용"""
		self.table_config_api_datas = _json or self.table_config_api_datas
		if not hasattr(self, 'table_config_from_api') or not self.table_config_api_datas:
			return
		
		# 테이블 설정이 없으면 초기화
		if not hasattr(self, 'table_config'):
			self.table_config = {}
		
		self.create_table_config_api_datas()
		self.run()

	def create_table_config_api_datas(self, api_datas:list[dict]=[]) -> dict:
		"""
			api_datas : list[dict]
		"""
		self.prev_table_config = self.table_config if self.table_config else {}
		# 테이블 설정 업데이트
		DBs = api_datas or self.table_config_api_datas
		self.table_name = DBs[0].get('table_name') 
		표시명 = 'display_name'
		self.table_config['_table_name'] = self.table_name
		self.table_config['_table_config_api_datas'] = DBs
		self.table_config['_headers'] = [ _obj.get(표시명) for _obj in DBs ]
		self.table_config['표시명vs컬럼명'] = { _obj.get(표시명): _obj.get('column_name') for _obj in DBs }
		self.table_config['_hidden_columns'] = [_idx for _idx, _obj in enumerate(DBs) if _obj.get('is_hidden', False) ]
		self.table_config['_no_edit_cols'] = [ _obj.get(표시명) for _obj in DBs if not _obj.get('is_editable', True) ]
		self.table_config['_column_types'] = { _obj.get(표시명): _obj.get('column_type') for _obj in DBs }
		self.table_config['_column_styles'] = { _obj.get(표시명): _obj.get('cell_style') for _obj in DBs }
		self.table_config['_column_widths'] = { _obj.get(표시명): _obj.get('column_width',0) for _obj in DBs }
		self.table_config['_table_style'] = None #DBs[0].get('table_style')

		return self.table_config

	def _set_api_datas(self, api_datas:list[dict]=[]):
		"""
			build method.
			api_datas : list[dict]
		"""
		self.api_datas = api_datas or self.api_datas
		return self

	def _set_table_config_datas(self, table_config_datas:list[dict]=[]):
		self.table_config_datas = table_config_datas or self.table_config_datas
		return self
		

	def _initialize_ui(self):
		"""UI 컴포넌트 초기화"""
		self.UI()
		_isShow = bool(self.api_datas and self.table_config)
		# 데이터가 있고 테이블 헤더가 있는 경우에만 테이블 뷰 생성
		if _isShow:
			self.model_data = self._create_model_data()
			if self.model_data:
				self._create_table_view()
		self.show_table_hide_no_data(_isShow)

	def _create_table_view(self):
		"""테이블 뷰 생성 및 설정"""
		self.table_model = (
			TableModelBuilder()
			.with_data(self.model_data)
			.with_table_config(self.table_config)
			.build()
		)
		self.table_view = TableView_영업수주_관리(self)
		self.table_model.configure_table_view(self.table_view)
		self.vLayout_main.addWidget(self.table_view)

		# 시그널 연결
		self.table_view.signal_table_config_api_datas.connect(self.slot_signal_table_config_api_datas)

	def _update_table_with_data(self):
		"""데이터 변경에 따른 테이블 업데이트"""
		is_show = bool(self.api_datas and self.table_config)
		# 데이터가 있는 경우
		if is_show:
			# API 데이터가 변경된 경우
			if self.prev_api_data != self.api_datas:
				self.model_data = self._create_model_data()
				if hasattr(self, 'table_model'):
					self.table_model.set_data(self.model_data)
			
			# 테이블 설정이 변경된 경우
			if self.prev_table_config != self.table_config:
				if hasattr(self, 'table_model'):
					self.table_model.set_table_config(self.table_config)
		else:
			self._create_table_view()
		
		self.show_table_hide_no_data(is_show)


	def run(self):

		if not self.table_config or not self.table_config_api_datas:
			### 1. table_config_api_datas 가져오기
			if ( qs := Table_Config.objects.filter(table_name=self.table_name) ): #### 0.00초 걸림
				self.table_config_api_datas = qs.values()
			else:
				self.table_config_api_datas = self.fetch_table_config_from_api()
			### 2. table_config 생성
			self.table_config = self.create_table_config_api_datas(self.table_config_api_datas)


		# UI가 아직 초기화되지 않은 경우 ### 0.01초 걸림
		if not hasattr(self, 'vLayout_main'):
			self._initialize_ui()

		else:
			self._update_table_with_data()
		return self
	


	@pyqtSlot(list)
	def slot_signal_table_config_api_datas(self, api_datas:list[dict]):
		"""
			table_config_api_datas 시그널 에 연결될 슬롯 함수 ==> api datas send
		"""

		is_ok, _json = APP.API.post(INFO.URL_CONFIG_TABLE_BULK_UPDATE, {'datas':json.dumps(api_datas,ensure_ascii=False)} )
		if is_ok:
			self.process_table_config_from_api( _json )
			User_Toast(INFO.MAIN_WINDOW, title="테이블 설정", text="테이블 설정이 Server에 저장 및 적용합니다.", duration=3000, style='INFORMATION')
		else:
			User_Toast(INFO.MAIN_WINDOW, title="테이블 설정", text="테이블 설정 저장 실패", duration=3000, style='ERROR')

	def slot_delegate_closeEditor(self, editor: QWidget, hint: QAbstractItemDelegate.EndEditHint):
		"""
		delegate의 closeEditor 시그널에 연결될 슬롯 함수
		
		Args:
			editor: 편집이 완료된 위젯
			hint: 편집 종료 힌트
		"""
		# 필요한 처리 로직 구현
		pass
	
	def _create_model_data(self, api_data:list[dict]=[], table_header:list[str]=[] ) ->list[list]:
		"""
			api_data : list[dict]
			table_header : list[str]
		"""
		api_data = api_data or self.api_datas
		table_header = table_header or self.table_config.get('_headers', [])
		model_data = []
		표시명vs컬럼명_dict:dict[str:str] = self.table_config['표시명vs컬럼명']
		for _obj in api_data:			
			model_data.append ( [ _obj.get(표시명vs컬럼명_dict.get(headName), '') for headName in table_header ] )

		return model_data

	def get_table_row_data(self, obj:dict) -> list:		
		return [ self._get_table_cell_value(key, obj) for key in self.table_header ]
	
	def _get_table_cell_value(self, key:str, obj:dict) ->str:
		""" """
		value = obj.get(key , None)
		return value

	### 😀😀 table 마다 hard coding
	@pyqtSlot(bool, int, str, QPoint) ### show 여부, rowNo와 mouse QPoint)
	def slot_signal_hover(self, is_show:bool, ID:int, hoverName:str, position:QPoint ):
		if ID <1 : return 
		if is_show:			
			if ( app_data_dict := self._get_apiDict_by_ID(ID) ):
				match hoverName:
					case '현장명':
						self.dlg_hover_app사용자.setWindowTitle( f" {app_data_dict.get('제목')} ")
						self.dlg_tb.clear()
						self.dlg_tb.setText ( app_data_dict.get(hoverName))
					### m2m filed로 조회
					case 'file수':
						self.dlg_hover_app사용자.setWindowTitle( f" {app_data_dict.get('제목')} ")
						self.dlg_tb.clear()
						futures = []
						with concurrent.futures.ThreadPoolExecutor() as executor:
							for file_id in  app_data_dict.get('files'):
								futures.append( executor.submit (APP.API.getObj , INFO.URL_요청사항_FILE, file_id )  )
						for future in futures:
							self.dlg_tb.append ( future.result()[1].get('file'))

		self.dlg_hover_app사용자.move(position.x()+INFO.NO_CONTROL_POS, position.y() )
		self.dlg_hover_app사용자.setVisible(is_show)
		# if INFO.IS_DebugMode :
		# 	ic ('hover : ', is_show, ID,  self.dlg_hover_app사용자.isVisible() )
		



	def menu__file_upload_multiple(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		original_dict:dict = self.api_datas[msg.get('row')]
		m2mField = '첨부file_fks'
		URL_파일_m2m = INFO.URL_샘플관리_첨부FILE
		dlg = Dialog_file_upload_with_listwidget(self , 
										   original_dict= original_dict, 
										   m2mField=m2mField, 
										   display_dict= self._get_dlg_display_data( original_dict.get(m2mField,[]), URL_파일_m2m ), 
										   )
		dlg.signal_save.connect( lambda wid, original, sendData, m2mField: self._file_upload(wid, original,sendData,m2mField, URL_파일_m2m ) )

	def _file_upload(self, wid:QDialog, originalDict:dict, files:dict,  m2mField:str,  URL_파일_m2m:str ) -> None:
		"""
			1. file Upload URL에 files : { 'fileNames': list[str]} 에서 fileNames:list[str]을 가져옴 \n
			2. fileNames 에서 기존것과 신규를 분리하여, 신규 ids를 가져와서 다시 합쳐서,
			3. m2mField로 update 하고, 성공하면 wid.close()
		"""
		formData = {}
		fileNames:dict[int:str] = files.pop('fileNames') ### fileupload list widget에서 fix 시킴		

		기존_ids = [ ID for ID, _ in fileNames.items() if ID>0 ]
		targetThreading = [ fName for ID, fName in fileNames.items() if ID<0 ]

		futures = []
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = [  executor.submit (APP.API.Send ,  URL_파일_m2m, {}, {},[('file', open(fName,'rb'))] ) for fName in targetThreading ]

		신규_files_ids = [ future.result()[1].get('id') for future in futures ]

		formData[m2mField] = 기존_ids + 신규_files_ids
		if INFO.IS_DebugMode :	ic ( formData , self.url )

		is_ok, _json = APP.API.Send( self.url, originalDict, formData )
		if is_ok:			
			wid.close()
			self.signal_refresh.emit()
		else:
			QMessageBox.critical(self, 'DB 저장 오류', '다시 시도해 주십시요')

	def menu__file_download_multiple(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		def _show_download_result ( _url_list:list[str]  ) -> None:
			"""
				API 결과 파일 다운로드 결과 표시
			"""
			다운로드fileName :list[str] =[]
			for url in _url_list:
				fName = Utils.func_filedownload(url=url)
				if fName:
					다운로드fileName .append ( fName +'\n')

			Utils.generate_QMsg_Information( 
				self, 
				title="파일다운로드 결과" ,
				text=f"{len(다운로드fileName )} 개 파일을 다운받았읍니다. \n" + '\n'.join(다운로드fileName ) +'\n\n'
				)
			
		colNo = msg.get('col')
		rowNo = msg.get('row')
		tableHeaderName = self.table_header[colNo]

		dlg_res_button = Utils.generate_QMsg_question(self, text = "파일 다운로드  진행하시겠읍니까?")
		if dlg_res_button != QMessageBox.StandardButton.Ok :
			return 
		match tableHeaderName:
			case 'claim_file_수':
				claim_files_url = [ url if url.startswith('http') else INFO.URI + url 
					   for url in self.model_data[rowNo][self.table_header.index('claim_files_url')] ]
				_show_download_result( claim_files_url )

			case 'activity_file_수':
				activity_files_url = [ url if url.startswith('http') else INFO.URI + url 
					   for url in self.model_data[rowNo][self.table_header.index('activity_files_url')] ]
				_show_download_result( activity_files_url )

		
	### cell menu
	def menu__file_preview_multiple(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		def _show_dlg( _files_url:list[str] ) -> None:
			dlg = QDialog(self)
			vLayout = QVBoxLayout()
			wid = Wid_FileViewer( paths=_files_url)
			vLayout.addWidget ( wid )
			dlg.setLayout(vLayout)
			dlg.show()

		colNo = msg.get('col')
		rowNo = msg.get('row')
		tableHeaderName = self.table_header[colNo]

		match tableHeaderName:
			case 'claim_file_수':
				claim_files_url = [ url if url.startswith('http') else INFO.URI + url 
					   for url in self.model_data[rowNo][self.table_header.index('claim_files_url')] ]
				_show_dlg( claim_files_url )
				
			case 'activity_file_수':
				activity_files_url = [ url if url.startswith('http') else INFO.URI + url 
					   for url in self.model_data[rowNo][self.table_header.index('activity_files_url')] ]
				_show_dlg( activity_files_url )

	

	@pyqtSlot(dict)
	def slot_signal_model_data_changed(self, msg:dict) -> None:
		"""
		{
			'row' :row,
			'col' : col,
			'value' : value,
			'api_data' :api_data,
		}
		"""
		# ic ('model data chagend:', msg)
		rowNo, colNo, headerName  = self._get_datas_from_msg(msg)
		self.tableView : TableView_영업수주_관리
		model_datas = self.tableView.model()._data
		api_data = msg.get('api_data')		
		send_data = copy.deepcopy(api_data)

		if  model_datas[msg.get('row')][msg.get('col')] == msg.get('value'):
			return
		

		self.tableView.model().beginResetModel()
		model_datas[msg.get('row')][msg.get('col')] =  msg.get('value')
		self.tableView.model().endResetModel()


	def slot_Sample_completed( self, dlg:QDialog, compledtedDict:dict, msg:dict) :
		URL_파일_m2m = INFO.URL_영업수주_관리FILE
		futures = []
		m2m_field = '완료file_fks'
		targetThreading = compledtedDict.get(m2m_field, [])
		if targetThreading:
			with concurrent.futures.ThreadPoolExecutor() as executor:
				futures = [  executor.submit (APP.API.Send ,  URL_파일_m2m, {}, {},[('file', open(fName,'rb'))] ) for fName in targetThreading ]
			신규_files_ids = [ future.result()[1].get('id') for future in futures ]

		originalDict =  {'id': msg.get('api_data').pop('id')}
		sendData:dict = msg.get('api_data')
		sendData.update({'완료의견':compledtedDict.get('완료의견', '')})
		if 신규_files_ids :
			sendData.update ({m2m_field:신규_files_ids})
		ic ( originalDict, sendData )
		is_ok, _json = APP.API.Send( self.url, originalDict , sendData )
		if is_ok:			
			dlg.close()
			self.signal_refresh.emit()
		else:
			QMessageBox.critical(self, 'DB 저장 오류', '다시 시도해 주십시요')


	def slot_등록자선택(self, dlg:QDialog, originalDict:dict, sales_selected :dict) :
		ic ( self, sales_selected )
		is_Ok, _json = APP.API.Send( self.url, originalDict, sendData={ 'admin_input_fk' : sales_selected.get('id') } )
		if is_Ok:
			dlg.close()
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(title='DB 저장 ERROR', text='확인 후 다시 시도해 주십시요')


	
	def slot_select_row(self, wid:QWidget, 영업수주_관리_apiDict:dict, EL_한국정보_ID:int) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		_is_ok, _json = APP.API.Send( self.url, 영업수주_관리_apiDict, {'현장명_fk': EL_한국정보_ID})
		if _is_ok:
			wid.close()
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(self, title='DB 저장 오류!')




	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, 영업수주_관리은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_영업수주_관리
		model_datas:list[list] = self.tableView.model()._data

		new_data = self._create_new(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

	def _create_new(self, data:list) -> list:
		""" 
			app 마다 상이하므로, overwrite 할 것.
		"""
		copyed = []
		for index,value in enumerate(data):
			if index == self.table_header.index('id'):
				copyed.append(-1)
				continue

			if isinstance(value, str):
				copyed.append('')
			elif isinstance(value, bool):
				copyed.append(False)
			elif isinstance(value, (int,float)):
				copyed.append(0)
			else:
				copyed.append('')

		return copyed
	
	def menu__upgrade_row(self, msg:dict) ->None:
		"""
			copy msg.get('row') 하여 insert 함, 영업수주_관리은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_영업수주_관리
		model_datas:list[list] = self.tableView.model()._data

		new_data = self._create_upgrade(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

	def _create_upgrade(self, data:list) -> list:
		""" 
			app 마다 상이하므로, overwrite 할 것.
		"""
		copyed = []
		for index,value in enumerate(data):
			
			if index == self.table_header.index('id'):
				copyed.append(-1)
				continue
			elif index == self.table_header.index('버젼'):
				copyed.append(float(value)+0.01)
				continue
			elif index == self.table_header.index('file'):
				copyed.append( '')
				continue
			elif index == self.table_header.index('변경사항'):
				copyed.append( '')
				continue


			if isinstance(value, str):
				copyed.append(value)
			elif isinstance(value, bool):
				copyed.append(False)
			elif isinstance(value, (int,float)):
				copyed.append(value)
			else:
				copyed.append('')

		return copyed
	
	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__파일_업로드(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		rowNo = msg.get('row')
		(m2mField, URL_파일_m2m) = self._get_m2mField_info(msg)
		if not m2mField or not URL_파일_m2m : return 

		original_dict:dict = self.api_datas[rowNo]
		dlg = Dialog_file_upload_with_listwidget(self , 
										   original_dict= original_dict, 
										   m2mField=m2mField, 
										   display_dict= self._get_dlg_display_data( original_dict.get(m2mField,[]), URL_파일_m2m ), 
										   )
		dlg.signal_save.connect( lambda wid, original, sendData, m2mField: self._file_upload(wid, original,sendData,m2mField, URL_파일_m2m ) )

	def _file_upload(self, wid:QDialog, originalDict:dict, files:dict,  m2mField:str,  URL_파일_m2m:str ) -> None:
		"""
			1. file Upload URL에 files : { 'fileNames': list[str]} 에서 fileNames:list[str]을 가져옴 \n
			2. fileNames 에서 기존것과 신규를 분리하여, 신규 ids를 가져와서 다시 합쳐서,
			3. m2mField로 update 하고, 성공하면 wid.close()
		"""
		formData = {}
		fileNames:dict[int:str] = files.pop('fileNames') ### fileupload list widget에서 fix 시킴		

		기존_ids = [ ID for ID, _ in fileNames.items() if ID>0 ]
		targetThreading = [ fName for ID, fName in fileNames.items() if ID<0 ]

		futures = []
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = [  executor.submit (APP.API.Send ,  URL_파일_m2m,{}, {},[('file', open(fName,'rb'))] ) for fName in targetThreading ]

		신규_files_ids = [ future.result()[1].get('id') for future in futures ]

		formData[m2mField] = 기존_ids + 신규_files_ids
		if INFO.IS_DebugMode :	ic ( formData , self.url )

		is_ok, _json = APP.API.Send( self.url, originalDict, formData )
		if is_ok:			
			wid.close()
			self.signal_refresh.emit()
		else:
			QMessageBox.critical(self, 'DB 저장 오류', '다시 시도해 주십시요')

	def _get_dlg_display_data(self, ids:list[int], url:str) ->dict[ int:str]:
		futures = []
		with concurrent.futures.ThreadPoolExecutor() as executor:
			for id in ids:
				futures.append( executor.submit (APP.API.getObj ,  url, id ) )

		fileName = { future.result()[1].get('id'):future.result()[1].get('file') for future in futures }
		return fileName
	

	def menu__파일_다운로드(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		colNo = msg.get('col')
		rowNo = msg.get('row')
		(m2mField, URL_파일_m2m) = self._get_m2mField_info(msg)
		if not m2mField or not URL_파일_m2m : return 

		dlg_res_button = Utils.generate_QMsg_question(self, text = "파일 다운로드  진행하시겠읍니까?")
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			m2mList:list = self.api_datas[rowNo].get(m2mField)
			threadingTargets = [ URL_파일_m2m  + str(ID)+'/' for ID in m2mList ]
			futures = Utils._concurrent_API_Job( APP.API.getObj_byURL, threadingTargets )

			다운로드fileName :list[str] =[]
			for _, future in futures.items():
				다운로드fileName.append ( Utils.func_filedownload(url=future.result()[1].get('file')) +'\n')
			Utils.generate_QMsg_Information( self, title="파일다운로드 결과" ,
						text=f"{len(다운로드fileName)} 개 파일을 다운받았읍니다. \n {''.join(다운로드fileName)}")

			return 
		else:
			return 
		
	def _get_m2mField_info (self, msg:dict) ->tuple[str,str] :
		""" msg dict를 바아서 tuple( m2mField, m2mURL, URL)을 RETURN, 없을 시 ('','')"""
		rowNo = msg.get('row')
		colNo = msg.get('col')

		match self._get_headerName(colNo):
			case '첨부파일':
				m2mField = '첨부file_fks'
				m2mURL = '첨부파일_URL'
				URL_파일_m2m  = INFO.URL_작업지침_첨부_FILE
			case '완료파일':
				m2mField = '완료file_fks'
				m2mURL = '완료파일_URL'
				URL_파일_m2m  = INFO.URL_샘플관리_완료FILE
			case _:
				URL_파일_m2m = ''
				m2mURL = ''
				m2mField = ''
		return (m2mField, m2mURL, URL_파일_m2m)
	
	def _get_headerName(self, idx:int) -> str:
		return self.table_header[idx]
	

	def _get_selected_row_Dict(self) -> dict:
		# 선택된 행 정보 가져오기
		indexes = self.tableView.selectedIndexes()
		if indexes:
			row = indexes[0].row()			
			return self.api_datas[row]
		return None