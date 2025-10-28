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
from modules.PyQt.User.table.My_tableview import My_TableView
from modules.PyQt.User.table.My_Table_Model import My_TableModel
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

from modules.PyQt.Tabs.HR평가.tables.table_HR평가_역량평가 import Wid_Table_for_HR평가_역량평가
from modules.PyQt.Tabs.HR평가.tables.table_HR평가_성과평가 import Wid_Table_for_HR평가_성과평가
from modules.PyQt.Tabs.HR평가.tables.table_HR평가_특별평가 import Wid_Table_for_HR평가_특별평가

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

class TableView_HR평가_상급자평가_종합(My_TableView):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

class TableModel_HR평가_상급자평가_종합(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	def user_defined_BackgroundRole(self, index:QModelIndex, role):
		if hasattr(self, 'cell_menus_cols') and self.header[index.column()] in self.cell_menus_cols:
			return eval( self.cell_menus_cols_color) if hasattr(self, 'cell_menus_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkYellow))
		if hasattr(self, 'no_Edit_cols') and self.header[index.column()] in self.no_Edit_cols:
			return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
		if hasattr(self, 'no_Edit_rows') and index.row() in self.no_Edit_rows:
			return eval( self.no_Edit_rows_color) if hasattr(self, 'no_Edit_rows_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
			# return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))

		rowNo, colNo = index.row(), index.column()
		if self.header[colNo] == '평가점수' and int(index.data() ) == 0:
			return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkRed))


class Delegate_HR평가_상급자평가_종합(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	def user_defined_creatorEditor_설정(self, widget:object, **kwargs) -> object:
		match kwargs['key']:
			case '역량점수'|'성과점수'|'특별점수':
				if isinstance(widget, QtWidgets.QDoubleSpinBox):
					widget.setRange(0, 5.00)
					widget.setSingleStep(0.01)
		return widget
	


TABLE_NAME = 'HR평가_상급자평가_종합'

HOVER_LIST = []


class Wid_Table_for_HR평가_상급자평가_종합(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()
	signal_select_row = pyqtSignal(dict)
	signal_new_m2m = pyqtSignal(int)
	signal_del_m2m = pyqtSignal(int)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_HR평가_상급자평가_종합
		self.table_model : TableModel_HR평가_상급자평가_종합
		self.delegate : Delegate_HR평가_상급자평가_종합

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
		# self.tableView.signal_hover.connect(self.slot_signal_hover)

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

		

	### 😀 h_Menu : new ==> 선택시 copy, model create까지 하고, index는 위에
	def menu__update_row(self, msg:dict) -> None:
		row = msg.get('row')
		obj:dict = self.api_data[row]
		newObj = {}
		매출month = obj.get('매출_month', -1)
		매출year = obj.get('매출_year', -1)
		if 매출month >0:
			if 매출month == 12:
				매출year += 1
				매출month =1
			else:
				매출month +=1
		
		newObj['매출_year'] = 매출year
		newObj['매출_month'] = 매출month
		newObj['등록자'] = INFO.USERNAME

		_isOk, _json = APP.API.Send( self.url, {}, newObj )		
		if _isOk:
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical( self, title='DB 생성 Error', text="확인 후 재시도해 주십시요.")

	def menu__db_초기화(self, msg:dict) -> None:
		""" patch로 {'request_db_init':True, id:id } 를 보내서 설정된 db 초기화 요청"""
		row = msg.get('row')
		obj:dict = self.api_data[row]

		dlg_res_button = Utils.generate_QMsg_question(self, text = "db 초기화 하시겠읍니까? \n ( 검증부터 다시 시작해야 합니다.)")
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			_isOk, _json = APP.API.Send( self.url, obj, {'request_db_init':True, 'id': obj.get('id') }  )		
			if _isOk:
				Utils.generate_QMsg_Information( self, title='DB초기화', text='DB 초기화가 되었읍니다. ')
				self.signal_refresh.emit()
			else:
				Utils.generate_QMsg_critical( self, title='DB초기화 Error', text="확인 후 재시도해 주십시요.")


	def menu__file_upload(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		fName = Utils._getOpenFileName_only1( self, initialFilter = 'EXCEL FIle(*.xlsx)' )
		if fName:
			modelDataDict = self.table_model._get_row_data(msg.get('row'))
			sendFile = [('file', open(fName, 'rb'))]


			is_ok, _json = APP.API.Send( self.url, modelDataDict, modelDataDict, sendFile )
			if is_ok:
				self.signal_refresh.emit()
			else:
				Utils.generate_QMsg_critical (self, 'File Upload Fail', '다시 시도해 주십시요')


	def menu__file_download(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		obj:dict = self.api_data[msg.get('row')]
		fName = Utils.func_filedownload(url=obj.get('file'))
		# if fName:



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

		self.tableView : QTableView
		model_datas = self.tableView.model()._data
		api_data = msg.get('api_data')		
		send_data = copy.deepcopy(api_data)
		send_data['등록자_fk'] = INFO.USERID

		if  model_datas[msg.get('row')][msg.get('col')] == msg.get('value'):
			return
		

		ID = send_data.pop('id')

		dataObj = {} if ID < 1 else {'id': ID}
		_isOk, _json = APP.API.Send( url=self.url, dataObj=dataObj, sendData=send_data )
		if _isOk:
			NEW_ID = _json.get('id') if ID <1 else ID
			self.tableView.model().beginResetModel()
			model_datas[msg.get('row')][msg.get('col')] =  msg.get('value')
			if ID< 0:
				model_datas[msg.get('row')][self.table_header.index('id')] = NEW_ID
				self.signal_new_m2m.emit(NEW_ID)
			self.tableView.model().endResetModel()				
			
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(self, title='DB 저장 실패', text ='확인 후 다시 시도해 주십시요')


	def menu__delete_row(self, msg:dict) -> None:
		""" override """
		model =  self.tableView.model()
		model_datas:list[list] = model._data

		def delete_model_data(model, model_datas, row : int):
			model.beginResetModel()
			model_datas.pop( row  )
			model.endResetModel()

		row :int = msg.get('row')
		ID = self._get_ID( model_datas[row] )
		if ID <= 0 :
			delete_model_data(model, model_datas, row)
			return
		
		dlg_kwargs = {
			'title' : '삭제 확인',
			'msgText' : '삭제하시겠읍니까? \n(db에서 복구할 수 없읍니다.)'
		}
		from modules.PyQt.dialog.confirm.confirm import Dialog_Confirm
		dlg =  Dialog_Confirm( self, **dlg_kwargs)
		if dlg.exec():
			# self.signal_refresh.emit()
			if APP.API.delete(self.url+ str(ID) ):
				### 😀😀 OVERRIDE 된 부분
				delete_model_data(model, model_datas, row)
				self.signal_del_m2m.emit( ID )


			else:




	### cell_Menus 관련
	### cell Menus는 보통 app에 특화되어 있으므로 Utils_QWidget 에 넣지말고...
	### table main 에 
	def menu__인사평가(self, msg:dict) -> None:
		m2m_dict = {
			'역량점수' : 'ability_m2m',
			'성과점수' : 'perform_m2m',
			'특별점수' : 'special_m2m',
		}
		m2m_url = {
			'역량점수' : INFO.URL_HR평가_역량_평가_DB,
			'성과점수' : INFO.URL_HR평가_성과_평가_DB,
			'특별점수' : INFO.URL_HR평가_특별_평가_DB,
		}
		m2m_db_field_url = {
			'역량점수' : INFO.URL_DB_Field_역량_평가_DB,
			'성과점수' : INFO.URL_DB_Field_성과_평가_DB,
			'특별점수' : INFO.URL_DB_Field_특별_평가_DB,
		}

		row = msg.get('row')
		headerName = self.table_header[msg.get('col')]
		# obj:dict = self.api_data[row]

		# _isOK, _json = APP.API.getObj(INFO.URL_HR평가_평가결과_DB, obj.get('본인평가_id') )
		# if _isOK:		
		# 	m2m:list[int] = _json.get( m2m_dict[headerName] )
		# else:
		# 	Utils.generate_QMsg_critical(self)
		obj:dict = self.api_data[row]
		m2m :list[int] = obj.get( m2m_dict[headerName])
		param = f"?ids={ ','.join( [str(id) for id in m2m ] ) }&page_size=0"

		_isOk1, _json = APP.API.getlist( m2m_url[headerName] + param )
		_isOk2, _db_field = APP.API.getlist( m2m_db_field_url[headerName])
		if _isOk1 and _isOk2 :

			dlg = QDialog(self)
			vlayout = QVBoxLayout()
			
			wid_table, url_wid = self._get_wid_table( dlg, headerName )
			wid_table._update_data (
				api_data=_json, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
				url = url_wid,
				**_db_field,
			)
			vlayout.addWidget( wid_table )
			dlg.setLayout( vlayout)
			dlg.setWindowTitle ( f" {obj.get('피평가자_성명')} - {headerName} 평가")
			dlg.setMinimumSize ( 1000, 800 )
			dlg.show()
			dlg.closeEvent = self._dlg_close_signal_emit

		else:
			Utils.generate_QMsg_critical(self )


	
	def _dlg_close_signal_emit(self, event):

		self.signal_refresh.emit()
	
	def _get_wid_table(self, dlg:QDialog, headerName:str ) ->tuple[QWidget, str]:
		match headerName:
			case '역량점수':
				return ( Wid_Table_for_HR평가_역량평가(dlg), INFO.URL_HR평가_역량_평가_DB )
			case '성과점수':
				return ( Wid_Table_for_HR평가_성과평가(dlg), INFO.URL_HR평가_성과_평가_DB )
			case '특별점수':
				return ( Wid_Table_for_HR평가_특별평가(dlg), INFO.URL_HR평가_특별_평가_DB )



	
	def slot_select_row(self, wid:QWidget, HR평가_상급자평가_종합_apiDict:dict, EL_한국정보_ID:int) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		_is_ok, _json = APP.API.Send( self.url, HR평가_상급자평가_종합_apiDict, {'현장명_fk': EL_한국정보_ID})
		if _is_ok:
			wid.close()
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(self, title='DB 저장 오류!')




	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, HR평가_상급자평가_종합은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_HR평가_상급자평가_종합
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
			copy msg.get('row') 하여 insert 함, HR평가_상급자평가_종합은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_HR평가_상급자평가_종합
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
				URL_파일_m2m  = '/HR평가_상급자평가_종합/완료file-viewSet/'
				URL_파일_m2m  = getattr( self, f"URL_{m2mField}")
			case _:
				URL_파일_m2m = ''
				m2mField = ''
		return (m2mField, URL_파일_m2m)
	
	def _get_headerName(self, idx:int) -> str:
		return self.table_header[idx]