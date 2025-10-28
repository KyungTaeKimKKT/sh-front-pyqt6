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


from modules.PyQt.User.table.My_tableview import My_TableView
from modules.PyQt.User.table.My_Table_Model import My_TableModel
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu


from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

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

class TableView_생산_하이_생산완료(My_TableView):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		# 행 선택 모드 설정
		self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
		self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        
	def setModel(self, model):
		super().setModel(model)
		# model이 설정된 후에 selection changed 시그널 연결
		self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        


class TableModel_생산_하이_생산완료(My_TableModel):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	def user_defined_BackgroundRole(self, index:QModelIndex, role):
		rowNo = index.row()
		colNo = index.column()
		# if colNo == self.header.index('HTM_Sheet'):
		# 	if self._data[rowNo][self.header.index('is_HTM_확정')] :
		# 		return QBrush(QColor("blue"))
		# 	else:
		# 		return QBrush(QColor("red"))
		
		# if colNo == self.header.index('JAMB_Sheet'):
		# 	if self._data[rowNo][self.header.index('is_JAMB_확정')] :
		# 		return QBrush(QColor("blue"))
		# 	else:
		# 		return QBrush(QColor("red"))

		if hasattr(self, 'cell_menus_cols') and self.header[index.column()] in self.cell_menus_cols:
			return eval( self.cell_menus_cols_color) if hasattr(self, 'cell_menus_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkYellow))
		if hasattr(self, 'no_Edit_cols') and self.header[index.column()] in self.no_Edit_cols:
			return eval( self.no_Edit_cols_color) if hasattr(self, 'no_Edit_cols_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
		if hasattr(self, 'no_Edit_rows') and index.row() in self.no_Edit_rows:
			return eval( self.no_Edit_rows_color) if hasattr(self, 'no_Edit_rows_color') else QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.gray))
			# return QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))

	def user_defined_ForegroundRole(self, index, role):
		rowNo = index.row()
		colNo = index.column()
		# if colNo == self.header.index('HTM_Sheet'):
		# 	return QBrush(QColor("white"))
		# if colNo == self.header.index('JAMB_Sheet'):
		# 	return QBrush(QColor("white"))
		

class Delegate_생산_하이_생산완료(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)


TABLE_NAME = '생산_하이_생산완료'

HOVER_LIST = []


class Wid_Table_for_생산_하이_생산완료(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_refresh = pyqtSignal()
	signal_select_rows = pyqtSignal(list)
	
	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )
		self.tableView:  TableView_생산_하이_생산완료
		self.table_model : TableModel_생산_하이_생산완료
		self.delegate : Delegate_생산_하이_생산완료

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
			# ic ( 'delete self.vlayout_main')
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
		# ic( 'run ... table model: ', self.table_model)

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
		self.tableView.signal_select_rows.connect(lambda _selectList: self.signal_select_rows.emit(_selectList) )
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
		# 	ic ('hover : ', is_show, ID,  self.dlg_hover_app사용자.isVisible() )
		

	### 😀 h_Menu : new ==> 선택시 copy, model create까지 하고, index는 위에
	def menu__form_new_row(self, msg:dict) -> None:
		today = datetime.today().date()
		newObj = {'id':-1, '작성일': today, '작성자':INFO.USERNAME, '납기일' :today+timedelta(days=30),  }
		dlg =Dialog_생산지시서_Form(self, url=self.url,  dataObj = newObj )
		dlg.signal_refresh.connect ( lambda: self.signal_refresh.emit() )

	def menu__form_update_row(self, msg:dict) -> None:
		dataObj = self.api_data[msg.get('row')]
		dlg =Dialog_생산지시서_Form(self, url=self.url,  dataObj = dataObj )		
		dlg.signal_refresh.connect ( lambda: self.signal_refresh.emit() )

	def menu__form_view_row(self, msg:dict) -> None:
		dataObj = self.api_data[msg.get('row')]
		dlg =Dialog_생산지시서_Form(self, url=self.url,  dataObj = dataObj , is_Edit=False )

	def menu__file_upload_multiple(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		original_dict:dict = self.api_data[msg.get('row')]
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
		rowNo, colNo, headName =	self._get_datas_from_msg(msg)
		m2mField, m2mURL, URL_파일_m2m = self._get_m2mField_info(msg)

		dlg_res_button = Utils.generate_QMsg_question(self, text = "파일 다운로드  진행하시겠읍니까?")
		if dlg_res_button == QMessageBox.StandardButton.Ok :
			m2mList:list = self.api_data[rowNo].get(m2mField)
			threadingTargets = [ URL_파일_m2m  + str(ID)+'/' for ID in m2mList ]
			futures = Utils._concurrent_API_Job( APP.API.getObj_byURL, threadingTargets )

			ic ( threadingTargets )
			다운로드fileName :list[str] =[]
			for _, future in futures.items():
				ic ( future.result()[1])
				fName = Utils.func_filedownload(url=future.result()[1].get('file'))
				if fName:
					다운로드fileName.append ( fName +'\n')
			Utils.generate_QMsg_Information( self, title="파일다운로드 결과" ,
						text=f"{len(다운로드fileName)} 개 파일을 다운받았읍니다. \n {''.join(다운로드fileName)}")

			return 
		else:
			return 

	# def menu__file_preview_multiple(self, msg:dict):
	# 	rowNo, colNo, headName =	self._get_datas_from_msg(msg)
	# 	m2mField, m2mURL, URL_파일_m2m = self._get_m2mField_info(msg)

	# 	url_list = self.api_data[rowNo].get(m2mURL)
	# 	dlg = Dialog_ImageViewer(self, url_list= [ INFO.URI+url for url in url_list ] )


	def menu__update_의장도( self, msg ):
		rowNo, colNo, headName =	self._get_datas_from_msg(msg)
		dataObj= self.api_data[rowNo]
		from modules.PyQt.Tabs.생산지시서.dialog.widget.Wid_생산지시서_의장도  import Wid_작지_의장도

		dlg = QDialog(self)
		dlg.setWindowTitle( f"의장도_Update: {dataObj.get('제목')} ")
		vLayout = QVBoxLayout()
		PB_Save = QPushButton('저장', dlg)
		vLayout.addWidget(PB_Save)
		wid_의장도 = Wid_작지_의장도 ( self, dataObj= dataObj)
		vLayout.addWidget( wid_의장도 )
		setattr( dlg, 'wid_의장도', wid_의장도 )
		dlg.setLayout ( vLayout )
		dlg.show()
		
		PB_Save.clicked.connect ( lambda :  self.slot_menu_update_의장도_save( dlg , dataObj ))

	def slot_menu_update_의장도_save ( self, dlg:QDialog , dataObj:dict):
		의장도list = dlg.wid_의장도._get_의장도_datas()
		ic ( 의장도list )

		의장도_IDs = []
		if 의장도list:
			threadingTargets = []
			for 의장도 in 의장도list:					
				if 'id' in 의장도 :
					threadingTargets.append( {'url':INFO.URL_작업지침_의장도 , 'dataObj':{ 'id': 의장도.pop('id')}, 'sendData':의장도,  }  )
				else:
					sendFiles = 의장도.pop('files')
					threadingTargets.append ( {'url':INFO.URL_작업지침_의장도 , 'dataObj':{ 'id': -1}, 'sendData':의장도, 'sendFiles': sendFiles }  )

			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )

			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				의장도_IDs = [ future.result()[1].get('id') for index,future in futures.items() ]
			else:
				Utils.generate_QMsg_critical(self)

		sendData = { '의장도_fks' : 의장도_IDs }
		### 😀 clear 경우 즉, {'의장도_fks' : [] } 경우에도 적용가능하도록 변경
		# is_ok, _json = APP.API.Send ( self.url, dataObj, sendData= {'의장도_fks' : 의장도_IDs } )
		is_ok, _json = APP.API.Send ( self.url, dataObj, sendData= json.dumps(sendData, ensure_ascii=False) ,headers= { 'Content-Type': 'application/json' } )
		if is_ok:
			self.signal_refresh.emit()
			dlg.close()
		else :
			Utils.generate_QMsg_critical(self)

	def menu__eco_row(self , msg:dict ):
		# rowNo, colNo, headName =	self._get_datas_from_msg(msg)
		dataObj= self.api_data[msg.get('row')]

		today = datetime.today().date()
		newObj = copy.deepcopy( dataObj )
		newObj.update ( { '작성일': today, '작성자':INFO.USERNAME, '납기일' :today+timedelta(days=30), 'Rev':dataObj['Rev']+1 , '변경사유_내용':''} )

		dlg =Dialog_생산지시서_Form(self, url=self.url,  dataObj = newObj , is_ECO=True )
		dlg.signal_refresh.connect ( lambda: self.signal_refresh.emit() )


	# def menu__is_배포_cell(self , msg:dict ):
	# 	ic(msg)
	# 	rowNo, colNo, headName = self._get_datas_from_msg(msg)
	# 	dataObj= self.api_data[rowNo]
	# 	text = '\n\n'
	# 	for key in ['고객사', '제목', 'Proj_No', 'Rev', '납기일']:
	# 		if key == 'Rev':
	# 			text += f" {key} : {dataObj[key]}({'초도발행' if dataObj[key] == 1 else 'ECO'}) \n"
	# 		else :
	# 			text += f" {key} : {dataObj[key]}\n"

	# 	dlg_res_button =  Utils.generate_QMsg_question(self, title="배포확인", text= text + '\n\n 배포를 하시겠읍니까? \n')
	# 	if dlg_res_button == QMessageBox.StandardButton.Ok :
	# 		is_ok, _json = APP.API.Send ( self.url, dataObj, {'is_배포': msg['value']})
	# 		if is_ok:
	# 			self.signal_refresh.emit()
	# 		else:
	# 			Utils.generate_QMsg_critical(self)


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
		self.tableView : TableView_생산_하이_생산완료
		model_datas = self.tableView.model()._data
		api_data = msg.get('api_data')		
		send_data = copy.deepcopy(api_data)

		if  model_datas[msg.get('row')][msg.get('col')] == msg.get('value'):
			return
		

	
		ID = send_data.pop('id')
		ic ( self, ID, send_data )
		dataObj = {} if ID < 1 else {'id': ID}
		ic (headerName, msg.get('value'))

		_list = ['납기일_Door', '납기일_Cage', '납기일_JAMB']
		headerName_to_fk = {
			'납기일_Door' : self.table_header.index('schedule_door_fk'),
			'납기일_Cage' : self.table_header.index('schedule_cage_fk'),
			'납기일_JAMB' : self.table_header.index('schedule_jamb_fk'),
		}
		if headerName in list( headerName_to_fk.keys() ):				
			colIdx = headerName_to_fk[headerName]
			_dict = { 'url' : INFO.URL_생산계획_Schedule_By_Type,
						'dataObj' : {'id':  model_datas[msg.get('row')][colIdx] },
						'sendData' : { '출하일': msg.get('value').toPyDate() }}

			ic ( _dict )
			_isOk, _ = APP.API.Send ( **_dict )
			if _isOk :
				self.signal_refresh.emit()
			else:
				Utils.generate_QMsg_critical(self)





	def slot_Sample_completed( self, dlg:QDialog, compledtedDict:dict, msg:dict) :
		URL_파일_m2m = INFO.URL_생산_하이_생산완료FILE
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


	
	def slot_select_row(self, wid:QWidget, 생산_하이_생산완료_apiDict:dict, EL_한국정보_ID:int) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		_is_ok, _json = APP.API.Send( self.url, 생산_하이_생산완료_apiDict, {'현장명_fk': EL_한국정보_ID})
		if _is_ok:
			wid.close()
			self.signal_refresh.emit()
		else:
			Utils.generate_QMsg_critical(self, title='DB 저장 오류!')




	### 😀😀  Handle_Table_Menu 의 method new override
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, 생산_하이_생산완료은 일자만 복사하여 유지		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_생산_하이_생산완료
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
			copy msg.get('row') 하여 insert 함, 생산_하이_생산완료은 버젼만 default 0.01 up함		
		"""
		row :int = msg.get('row')
		self.tableView : TableView_생산_하이_생산완료
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
			return self.api_data[row]
		return None