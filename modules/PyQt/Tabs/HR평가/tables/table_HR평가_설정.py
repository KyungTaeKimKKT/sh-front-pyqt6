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
from modules.PyQt.Tabs.HR평가.tables.tablemodel_HR평가_설정 import TableModel_HR평가_설정
from modules.PyQt.Tabs.HR평가.tables.tableview_HR평가_설정 import TableView_HR평가_설정
from modules.PyQt.Tabs.HR평가.tables.delegate_HR평가_설정 import Delegate_HR평가_설정
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

TABLE_NAME = 'HR평가_설정'
HOVER_LIST = []


class Wid_Table_for_HR평가_설정(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()
	signal_select_row = pyqtSignal(dict)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_HR평가_설정
		self.table_model : TableModel_HR평가_설정
		self.delegate : Delegate_HR평가_설정

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

		###😀😀
		self._modity_table_config()
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


	def _modity_table_config(self) -> None:
		""" 여기서 필요에 따라 table_config modify """
		t_config = self.table_config		
		t_config['no_Edit_rows'] = [  idx  for idx, api_data in enumerate(self.api_data) if api_data.get('is_완료') ]



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
	def slot_signal_model_data_changed(self, msg:dict) -> None:
		"""
		{
			'row' :row,
			'col' : col,
			'value' : value,
			'api_data' :api_data,
		}
		"""

		rowNo, colNo, headerName = self._get_datas_from_msg (msg)
		api_data = msg.get('api_data')	
		평가설정_Id = self._get_ID_from_Msg(msg)
		## 😀
		if 'is_시작' == headerName and msg.get('value'):
			is_ok, _json = APP.API.getlist( INFO.URL_HR평가_평가체계DB + f"?평가설정_fk={str(평가설정_Id)}"+"&is_참여=True&page_size=0" )
			if is_ok:
				차수별_평가자s :dict[int:list[int]] = {}
				for 차수 in range( self.api_data[rowNo].get('총평가차수') +1 ):
					# for obj in _json:

					차수별_평가자s[차수] = [ 평가자_id if (평가자_id:= obj.get('평가자')) is not None  else -1 for obj in _json if obj.get('차수') == 차수  ] 

				text = "\n 총대상자 \n"
				for 차수, 평가자s in 차수별_평가자s.items():
					unique = list(set(평가자s))
					if -1 in unique : unique.remove( -1 )
					text += f"{'본인평가' if 차수 == 0 else str(차수)+'차 평가'}  : {len(unique)} 명 \n"
				text += '\n\n 검증결과: \n'
				
				is_평가자할당_ok= True
				for 차수, 평가자s in 차수별_평가자s.items():
					if 차수 >= 0:
						text += f"{'본인평가' if 차수 == 0 else str(차수)+'차 평가'}  : 평가자 미할당수 ==> {평가자s.count(-1)} 명 \n"
						if 평가자s.count(-1) > 0: is_평가자할당_ok = False

				if not is_평가자할당_ok : 
					Utils.generate_QMsg_critical(self, title="평가자 할당 오류", text=text + "\n\n평가 대상자의 평가자 할당은 모두 되어야 합니다.\n")
					return 

				dlg_res_button =  Utils.generate_QMsg_question(self, title="확인", text = text + '\n\n 평가를 시작하시겠읍니까? \n')
				if dlg_res_button == QMessageBox.StandardButton.Ok :
					is_ok, _ = APP.API.Send ( INFO.URL_HR평가_평가설정DB, {'id':평가설정_Id}, {'is_시작':True})
					if is_ok:
						self._update_model_data_from_Msg ( msg )
						Utils.generate_QMsg_Information(self, title='평가 시작', text='😀😀😀평가가 시작되었읍니다. \n 해당 대상자는 MENU가 생성되었읍니다. \n')
					else:
						Utils.generate_QMsg_critical(self)

		elif 'is_종료' == headerName and msg.get('value'):
			dlg_res_button =  Utils.generate_QMsg_question(self, title="확인", text = '\n\n 평가를 종료 하시겠읍니까? \n 평가 MENU가 비활성화됩니다. \n')
			if dlg_res_button == QMessageBox.StandardButton.Ok :
				is_ok, _ = APP.API.Send ( INFO.URL_HR평가_평가설정DB, {'id':평가설정_Id}, {'is_종료':True})
				if is_ok:
					self._update_model_data_from_Msg ( msg )
					Utils.generate_QMsg_Information(self, title='평가 종료', text='😀😀😀평가가 종료되었읍니다. \n \n')
				else:
					Utils.generate_QMsg_critical(self)

		else :
			_isOk, _json = APP.API.Send( self.url, api_data , api_data)
			if _isOk:
				if api_data.get('id', -1) < 0:
					self.signal_refresh.emit()
				else:
					self._update_model_data_from_Msg ( msg )
			else:




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

	def menu__copy_create_row(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		obj:dict = self.api_data[msg.get('row')]
		dlg_res_button  = Utils.generate_QMsg_question( self, title='평가설정_copy_create', text= json.dumps(obj, ensure_ascii=False) + '\n\n 평가설정을 신규 생성합니다.')

		if dlg_res_button == QMessageBox.StandardButton.Ok :
			is_ok, _json = APP.API.Send( INFO.URL_HR평가_COPY_CREATE_평가설정, {}, {'id': obj.get('id')} )
			if is_ok:
				Utils.generate_QMsg_Information(self, 
									title='Copy and New 완료', 
									text='평가체계가 완료되었읍니다. \n  평가체계 확인 및 평가시스템을 구축하십시요.\n\n' + json.dumps(_json, ensure_ascii=False) )
				self.signal_refresh.emit()
			else:
				Utils.generate_QMsg_critical(self)


	def menu__평가체계_신규_row(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""

		rowNo = msg.get('row')
		dlg_res_button  = Utils.generate_QMsg_question( self, title='평가체계도 신규 생성', text='평가체게도 신규 생성합니다.')
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			is_ok, _json = APP.API.Send( INFO.URL_HR평가_CREATE_평가체계, {}, {'is_생성':True, '평가설정_fk': self.api_data[rowNo].get('id'), '총평가차수': int(self.api_data[rowNo].get('총평가차수'))})
			if is_ok:

			else:
				Utils.generate_QMsg_critical( self, title='DB 생성 실패', text='확인 후 다시 시도해 주시기 바랍니다.')

	def menu__평가체계_수정_row(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""

		rowNo = msg.get('row')
		dlg_res_button  = Utils.generate_QMsg_question( self, title='평가체계도 수정', text='평가체게도 수정합니다.')

		if dlg_res_button == QMessageBox.StandardButton.Ok :
			is_ok, _json = APP.API.Send( INFO.URL_HR평가_CREATE_평가체계, {}, {'is_수정':True, '평가설정_fk': self.api_data[rowNo].get('id'), '총평가차수': int(self.api_data[rowNo].get('총평가차수'))})
			if is_ok:
				results:list[dict] = _json.get('result')

				from modules.PyQt.Tabs.HR평가.dialog.dlg_평가체계 import Dialog_평가체계
				dlg_평가체계 = Dialog_평가체계( self,
								url= INFO.URL_HR평가_평가체계DB , 
								app_Dict=self.api_data[rowNo],
								api_datas = results
								  )


			else:
				Utils.generate_QMsg_critical( self, title='DB 생성 실패', text='확인 후 다시 시도해 주시기 바랍니다.')

	def menu__평가항목_설정_row(self, msg:dict) :
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""

		rowNo = msg.get('row')
		dlg_res_button  = Utils.generate_QMsg_question( self, title='평가항목', text='평가항목을 관리합니다.')

		if dlg_res_button == QMessageBox.StandardButton.Ok :
			from modules.PyQt.Tabs.HR평가.dialog.dlg_평가항목관리 import Dialog_HR평가_평가항목설정

			dlg = Dialog_HR평가_평가항목설정 ( self, 
							 	url='',
							 	app_Dict= self.api_data[rowNo], 
							 	dataObj = {} )
			

	def menu__평가시스템_구축_row(self, msg:dict) :
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""

		rowNo = msg.get('row')
		dlg_res_button  = Utils.generate_QMsg_question( self, title='평가시스템 구축', text='평가시스템 구축(DB생성) 합니다.')

		if dlg_res_button == QMessageBox.StandardButton.Ok :
			_isOk, _json = APP.API.Send(INFO.URL_HR평가_평가시스템_구축, {}, {'평가설정_fk':self.api_data[rowNo].get('id') , 'is_시작':True})
			if _isOk:

			else:
				Utils.generate_QMsg_critical(self)
			

	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, HR평가_설정은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_HR평가_설정
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
			copy msg.get('row') 하여 insert 함, HR평가_설정은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_HR평가_설정
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
				URL_파일_m2m  = '/HR평가_설정/완료file-viewSet/'
				URL_파일_m2m  = getattr( self, f"URL_{m2mField}")
			case _:
				URL_파일_m2m = ''
				m2mField = ''
		return (m2mField, URL_파일_m2m)
	
	def _get_headerName(self, idx:int) -> str:
		return self.table_header[idx]