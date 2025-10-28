from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime
import concurrent.futures

import pathlib
import typing
import copy
import json

# import user module
from modules.PyQt.Tabs.디자인관리.tables.tablemodel_디자인관리_디자인관리 import TableModel_디자인관리
from modules.PyQt.Tabs.디자인관리.tables.tableview_디자인관리_디자인관리 import TableView_디자인관리
from modules.PyQt.Tabs.디자인관리.tables.delegate_디자인관리_디자인관리 import Delegate_디자인관리
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

TABLE_NAME = '디자인관리'
HOVER_LIST = []

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Table_for_디자인관리(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()
	signal_select_row = pyqtSignal(dict)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_디자인관리
		self.table_model : TableModel_디자인관리
		self.delegate : Delegate_디자인관리

		self.dlg_hover_app사용자 = self._init_dlg_Hover()

	def _init_dlg_Hover(self) -> QDialog:
		dlg = QDialog(self)
		dlg.setFixedSize( 600, 600)
		vLayout = QVBoxLayout()
		self.dlg_tb = QTextBrowser(self)
		self.dlg_tb.setAcceptRichText(True)
		self.dlg_tb.setOpenExternalLinks(True)
		vLayout.addWidget(self.dlg_tb)
		dlg.setLayout(vLayout)
		dlg.hide()

		return dlg

	def UI(self):
		self.vLayout_main = QVBoxLayout()
		self.tableView = eval(f"TableView_{TABLE_NAME}(self)")
		self.vLayout_main.addWidget(self.tableView)		
		self.setLayout(self.vLayout_main)
		
	def _update_data(self, **kwargs):
		""" kwargs : 
			#😀 db data
			api_data = list[dict]
			url = str
			#😀 DB_Field에서 가져온것
			fields_model = { name: type },
			fields_append = { name: type }, 
			fields_delete = { name: type },
			table_config = {
				'table_header' : list if not db_fields.keys(),
				'no_Edit_cols : list[str] => str은 table_header 의 element name,
				'hidden_columns' : list[str],
				....

			}
		"""
		self.api_data : list[dict]
		self.url : str
		self.fields_model :dict[str:str]
		self.fields_append :dict[str:str]
		self.fields_delete :dict[str:str]
		self.table_config :dict
		self.구분list : dict[str]
		self.고객사list :dict[str]

		for (key, value) in kwargs.items():
			setattr(self, key, value )
		self.api_data : list[dict]		

		### header_type 는 DB_FIELDS + SERIALIZER_APPEND
		self.header_type = copy.deepcopy(self.fields_model)
		self.header_type.update(self.fields_append)

		if  hasattr(self, 'table_config') and ( table_header:=self.table_config.get('table_header', None) ):			
			self.table_header =table_header
		else:
			self.table_header = list( self.header_type.keys() )

		self.run()



	
	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vLayout_main'):

			Utils.deleteLayout(self.vLayout_main)
		self.UI()
		self.model_data = self.gen_Model_data_from_API_data()

		self.table_model = eval ( f"""TableModel_{TABLE_NAME}(
					parent = self,
					header_type = self.header_type,
					header = self.table_header,
					_data = self.model_data,
					**self.table_config,					
				)""")


		self.tableView.setModel ( self.table_model)
		self.tableView.setConfig ( **self.table_config  )
		self.delegate = eval ( f"""Delegate_{TABLE_NAME}(
						self, 
						header_type=self.header_type,  
						**self.table_config
						)""")
		self.tableView.setItemDelegate(self.delegate)

		#### table delegate signal handler
		self.delegate.closeEditor.connect(self.slot_delegate_closeEditor)

		### tableView signal handler
		self.tableView.signal_vMenu.connect(self.slot_signal_vMenu )
		self.tableView.signal_hMenu.connect(self.slot_signal_hMenu )
		self.tableView.signal_cellMenu.connect(self.slot_signal_cellMenu)
		self.tableView.signal_hover.connect(self.slot_signal_hover)

		### tableModel signal handler
		self.table_model.signal_data_changed.connect( self.slot_signal_model_data_changed )


	def gen_Model_data_from_API_data(self, api_DB_data:list[dict]=[] ) ->list[list]:  		
		api_DB_data = api_DB_data if api_DB_data else self.api_data
		
		_data = []
		for obj in api_DB_data:
			_data.append ( self.get_table_row_data(obj) )
		return _data
	
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

		

	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__현장명_검색(self, msg:dict) -> None:
		row = msg.get('row')
		obj:dict = self.api_data[row]
		현장명_txt = obj.get('현장명')

		if 현장명_txt:
			dlg = QDialog(self)
			hLayout = QVBoxLayout()
			from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import 한국정보__for_Tab
		
			api_uri, api_url, db_field_url = INFO._get_URL_EL_INFO_한국정보(INFO)
			db_field_url = 'db-field-Elevator_Summary_WO설치일_선택menu_enable_View/'
			wid = 한국정보__for_Tab(
					dlg, ###😀관습적으로  self ㅜㅜ;;
					'', api_uri=api_uri, api_url=api_url, db_field_url=db_field_url, is_Auto_조회_Start=True, 
					param=f"search={현장명_txt}&page_size=25")
			hLayout.addWidget(wid)
			dlg.setLayout(hLayout)
			dlg.setWindowTitle( 'MOD 현장명 검색')
			dlg.setMinimumSize( 600, 800)
			dlg.show()

			wid.signal_select_row.connect (lambda EL_INFO: self.slot_select_row(dlg, obj, EL_INFO))
	
	def slot_select_row(self, wid:QWidget, 디자인관리_apiDict:dict, EL_INFO:dict) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		EL_한국정보_ID = EL_INFO.get('id')
		sendData = {
			'현장명_fk': EL_한국정보_ID,
			'현장명'  : EL_INFO.get('건물명'),
			'el수량' : EL_INFO. get('수량'),
			'운행층수' : EL_INFO.get('운행층수'),
		}
		_is_ok, _json = APP.API.Send( self.url, 디자인관리_apiDict,  sendData=sendData)
		if _is_ok:
			wid.close()
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(self, title='DB 저장 오류!')




	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, 디자인관리은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_디자인관리
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
			copy msg.get('row') 하여 insert 함, 디자인관리은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_디자인관리
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

		original_dict:dict = self.api_data[rowNo]
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
		if INFO.IS_DebugMode :	print ( formData , self.url )

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
			m2mList:list = self.api_data[rowNo].get(m2mField)
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
		""" msg dict를 바아서 tuple( m2mField, URL)을 RETURN, 없을 시 ('','')"""
		rowNo = msg.get('row')
		colNo = msg.get('col')

		match self._get_headerName(colNo):
			case '의뢰파일수':
				m2mField = '의뢰file_fks'
				URL_파일_m2m  = getattr( self, f"URL_{m2mField}")
			case '완료파일수':
				m2mField = '완료file_fks'
				URL_파일_m2m  = '/디자인관리/완료file-viewSet/'
				URL_파일_m2m  = getattr( self, f"URL_{m2mField}")
			case _:
				URL_파일_m2m = ''
				m2mField = ''
		return (m2mField, URL_파일_m2m)
	
	def _get_headerName(self, idx:int) -> str:
		return self.table_header[idx]
	
	### cell menu
	def menu__file_viewer(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		colNo = msg.get('col')
		rowNo = msg.get('row')
		(m2mField, URL_파일_m2m) = self._get_m2mField_info(msg)
		if not m2mField or not URL_파일_m2m : return 

		m2mList:list = self.api_data[rowNo].get(m2mField)
		threadingTargets = [ URL_파일_m2m  + str(ID)+'/' for ID in m2mList ]
		futures = Utils._concurrent_API_Job( APP.API.getObj_byURL, threadingTargets )

		result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		if all(result):
			path_List =  [ future.result()[1].get('file') for index,future in futures.items() ]
			from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer
			dlg = QDialog(self)
			vLayout = QVBoxLayout()
			vLayout.addWidget ( Wid_FileViewer( paths=path_List))
			dlg.setLayout(vLayout)
			dlg.show()
			ic ( path_List)
			
		else:
			Utils.generate_QMsg_critical(self)
