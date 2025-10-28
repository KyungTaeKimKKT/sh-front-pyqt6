import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import json
import copy
from pathlib import Path
import pandas as pd
from datetime import datetime

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.Tabs.작업지침서.dialog.ui.Ui_작업지침서_main_tab import Ui_Form_main as Ui_작업지침서_main

from modules.PyQt.User.object_value import Object_Set_Value, Object_Diable_Edit, Object_ReadOnly, Object_Get_Value
from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보

from modules.PyQt.User.upload_excel_table import Upload_Excel_작지
from modules.PyQt.User.save_excel_format import Save_Excel_format_작지

from config import Config as APP
import modules.user.utils as Utils
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


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_작지_main(QWidget, Qwidget_Utils):
	signal_textChanged = pyqtSignal(dict)
	signal_save = pyqtSignal(dict)
	signal_cancel = pyqtSignal()

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.is_ECO = False
		self.is_Edit = True
		self.url = ''
		self.dataObj = {}
		self.api_send_data_dict = {}
		self.api_send_datas_files = []
		self.el_info_fk = -1
		self.skip = []
		self.validator_list = ['제목']
		self.첨부files:list[dict] = []

		self.connectDisplayNames =  ['제목', 'Proj_No']

		for k, v in kwargs.items():
			setattr(self, k, v)

		self.ui = Ui_작업지침서_main()
		self.ui.setupUi(self)
		self.init_InputDict()

		self.user_defined_ui_setting()
		
		self._render_from_DataObj()

		self.triggerConnect()

		# if hasattr(self, 'dataObj') and self.is_Edit:
		# 	self._mode_for_inputDict(self.is_Edit)
		# 	ic ( kwargs)
		if not self.is_Edit:
			self.ui.PB_save.hide()
			self.ui.PB_cancel.setText(' 확인 ')
			self.ui.PB_Info_search.hide()
			self.ui.file_upload_wid.update_kwargs( is_Editable= False)
			self.slot_conversion_to_pdf()




	def init_InputDict(self) -> None:
		""" 각 dict는 {key : DB Field ; widget } 으로 구성
			특히, imageView, file, table의 key는 serializer 참조 """
		self.inputDict = {
			"제목"  : self.ui.lineEdit_Jemok,
			"Proj_No" :  self.ui.lineEdit_ProjNo,
			"고객사" : self.ui.combo_line_Gogaek,
			"구분"  : self.ui.combo_line_Gubun,

			"수량": self.ui.spinBox_ELSU,
			"납기일":  self.ui.dateEdit_Nabgi,
			
			"담당"  : self.ui.lineEdit_Damdang,
			"영업담당자"  : self.ui.lineEdit_Yungyub,
			"작성일" : self.ui.dateEdit_Jaksung,
			"작성자" : self.ui.lineEdit_Jaksungja,
			"고객요청사항" : self.ui.lineEdit_gogak_yochung,
			"고객성향" : self.ui.lineEdit_gogaek_sunghang,
			"특이사항" : self.ui.lineEdit_toiki,
			"집중점검항목" : self.ui.lineEdit_Jumgum,
			"검사요청사항" : self.ui.lineEdit_gumsa,
			### eco관련
			"변경사유_내용": self.ui.lineEdit_ECO_Contents,
			"Rev" : self.ui.spinBox_ECO_Rev,
		}


		self.imageViewerDict = {
			'Rendering_file' : self.ui.imageViewer_wid,
		}

		self.file_uploadDict = {
			'첨부file_fks' : self.ui.file_upload_wid,
		}

		self.table_Dict = {
			'process_fks' : self.ui.wid_table,
		}
		
	def user_defined_ui_setting(self):
		### 😀 QSpinbox default range setting ( defalult가 0,99 🤑)
		if INFO.IS_DEV :
			self.ui.frame_admin.show()
		else:
			self.ui.frame_admin.hide()

		for (key, input) in self.inputDict.items():
			match key :
				case '납기일':
					if isinstance( input, QDateTimeEdit ):						
						if not self.dataObj or not self.dataObj.get(key): 
							input.setDateRange( QDate.currentDate(), QDate.currentDate().addYears(1))
							input.setDate( QDate.currentDate().addMonths(1))
				case '작성일':
					input.setDate (QDate.currentDate() )
				case '작성자':
					if not self.dataObj or len(self.dataObj.get(key,'')) == 0: 
						input.setText(INFO.USERNAME)

		self.ui.comboBox_Yongji.addItems ( ['A4','A3'])
		self.ui.comboBox_Banghyang.addItems ( ['가로','세로'])

		self.ui.PB_conversion.hide()
		
		### eco 관련
		self.ui.frame_ECO.setVisible ( self.is_ECO )

	def _render_from_DataObj(self):
		# ic(self.dataObj)
		keysList = list (self.inputDict.keys() )
		if hasattr(self, 'dataObj') :
			for key, value in self.dataObj.items():
				if key in keysList:
					Object_Set_Value( self.inputDict[key], value )
					if not self.is_Edit:
						Object_ReadOnly( self.inputDict[key], value  )

			process_fks = self.dataObj.get('process_fks', []) 
			# ic ( process_fks, )

			if len(process_fks) > 0:
				param = f"?ids={(',').join( [str(id) for id in process_fks] )}&page_size=0"
				is_ok, _json = APP.API.getlist(INFO.URL_작업지침_PROCESS_DB + param )
				if is_ok:
					self.table_api_datas = _json
					### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
					if self.is_ECO:
						for obj in self.table_api_datas:
							obj['id'] = -1 

				else:
					Utils.generate_QMsg_critical(self)
			else:
				self.table_api_datas = []

			_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_작업지침_PROCESS_DB)
			if _isOk:
				if not self.is_Edit:
					db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
				self.ui.wid_table._update_data(
					api_data=self.table_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
					url = INFO.URL_작업지침_PROCESS_DB,
					**db_fields,
				)		
			else:
				Utils.generate_QMsg_critical(self)

			
			### 대표 rendering 표시
			if 'Rendering_URL' in self.dataObj and len( Rendering_URL :=self.dataObj.get('Rendering_URL', '') ) > 0:
				self.ui.imageViewer_wid.update_kwargs( url= INFO.URI+Rendering_URL )

			### 첨부file 표시
			if '첨부file_fks' in self.dataObj and '첨부파일_URL' in self.dataObj:
				ic ( self.첨부files )
				self.첨부files = [ { 'id':id, 'file':INFO.URI+url }  for id, url in zip(self.dataObj.get('첨부file_fks'), self.dataObj.get('첨부파일_URL'))]
				self.ui.file_upload_wid.update_kwargs( files=self.첨부files )
		
			### EL INFO
			if 'el_info_fk' in self.dataObj and ( ID:= self.dataObj.get('el_info_fk') ) :
				self.el_info_fk = ID
				if ID  is not None and ID >0 :
					is_ok, _json = APP.API.getObj( INFO.Elevator_한국정보_URL, ID)
					if is_ok:
						self.el_info_dict = _json
						self.ui.label_Info_EL_SU.setText( str( _json.get('수량') ))
						self.ui.label_Info_floor_su.setText ( str( _json.get('운행층수') ) )
						self.ui.label_Info_addr.setText ( str(_json.get('건물주소_찾기용') ) )
					else:
						Utils.generate_QMsg_critical(self)



	def run(self):
		if hasattr(self.ui, 'vLayout_main') : Utils.deleteLayout(self.ui.vLayout_main)
		self.ui.setupUi(self)
		self.init_InputDict()
		self.user_defined_ui_setting()	
		self.show()
		
		self.triggerConnect()
		self._enable_validator()

	def _enable_validator(self):
		self.ui.PB_save.setEnabled(False)
		for key in self.validator_list:
			self.inputDict[key].textChanged.connect(self.check_validator)

	def triggerConnect(self) ->None:
		### 관리자용 process table upload용 ###
		if hasattr(self.ui, 'PB_Upload_Excel') :
			self.ui.PB_Upload_Excel.clicked.connect(self.handle_PB_Upload_Excel)
		if hasattr(self.ui, 'PB_Download_Excel') :
			self.ui.PB_Download_Excel.clicked.connect(self.handle_PB_Download_Excel)
		#######################################
		self.ui.PB_Info_search.clicked.connect(self.slot_Info_search)
		self.ui.PB_ViewMap.clicked.connect(self.slot_map_view )

		self.ui.PB_conversion.clicked.connect ( self.slot_conversion_to_pdf)
		self.ui.PB_export_to_pdf.clicked.connect ( self.slot_export_to_pdf)

		self.ui.PB_save.clicked.connect(self.handle_PB_save)
		self.ui.PB_cancel.clicked.connect(lambda: self.signal_cancel.emit())		

		for name in self.connectDisplayNames:
			input = self.inputDict[name]
			if isinstance ( input, QLineEdit) :
				input.textChanged.connect(self.handle_textChanged_connectDisplay)

 		
	@pyqtSlot()
	def handle_PB_save(self):				
		sendData = {}
		sendData['작성자_fk'] = INFO.USERID

		if len(영업담당자:= self.ui.lineEdit_Yungyub.text() ) > 0:
			if ( 영업담당자_info := INFO()._get_user_info_by_name(영업담당자) ):
				sendData['영업담당자_fk'] = 영업담당자_info['id']
			else:
				Utils.generate_QMsg_critical(self, title="영업담당자 확인 오류", text="영업담당자를 확인 바랍니다.")
				return 
			

		### 1. 의장TABLE
		의장_datas = self.ui.wid_table._get_Model_data()
		if Utils.compare_dict_lists( self.table_api_datas, 의장_datas, del_keys= ['대표Process_Text','상세Process_Text']) :
			ic ( 'No change : 의장_datas')
		else :
			threadingTargets = [ ]
			threadingTargets = [ {'url':INFO.URL_작업지침_PROCESS_DB, 'dataObj':{ 'id': 의장dict.pop('id')}, 'sendData': 의장dict } for 의장dict in 의장_datas ]
			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				process_fks = [ future.result()[1].get('id') for index,future in futures.items() ]
				sendData.update ( {'process_fks' : process_fks })
			else:
				Utils.generate_QMsg_critical(self)


		### 2. imageViewer : rendering
		rendering = self.ui.imageViewer_wid.getValue() 
		if rendering and 'type' in rendering:
			files ={}
			match rendering.get('type', ''):
				case 'file':
					files = { 'file': open(rendering['source'], 'rb') }
				case 'clipboar'|'pilImage':
					# 클립보드나 PIL 이미지인 경우
					# QPixmap을 바이트로 변환
					byte_array = QByteArray()
					buffer = QBuffer(byte_array)
					buffer.open(QBuffer.OpenModeFlag.WriteOnly)
					rendering['image'].save(buffer, 'PNG')
					fName = title if len(title:= self.ui.lineEdit_Jemok.text() ) > 0 else 'rendering'
					files = {'file': (f"{fName}.png", byte_array.data(), 'image/png')}
				case __:
					pass
		
			if files:
				_isOk, _json = APP.API.Send (INFO.URL_작업지침_RENDERING_FILE , {'id':-1}, {}, sendFiles=files )
				if _isOk :
					sendData.update ( {'Rendering': _json.get('id')})
					ic ( sendData )
				else:
					Utils.generate_QMsg_critical(self)


		### 3. file_upload 		
		list_files = self.ui.file_upload_wid.getValue()
		new_list_files = [ { 'file': open( fileDict.get('file'), 'rb') } for fileDict in list_files if fileDict.get('type') == 'local' ]
		기존_ids = [ Utils.get_Obj_From_ListDict_by_subDict( self.첨부files, {'file': fileDict.get('file')}).get('id') for fileDict in list_files if fileDict.get('type') == 'server' ]

		if new_list_files:
			threadingTargets = [ {'url':INFO.URL_작업지침_첨부_FILE , 'dataObj':{ 'id': -1}, 'sendData':{}, 'sendFiles':files } for files in new_list_files ]
			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )

			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				new_IDS = [ future.result()[1].get('id') for index,future in futures.items() ]
				sendData.update ( {'첨부file_fks' : 기존_ids+ new_IDS })
			else:
				Utils.generate_QMsg_critical(self)
		
		else :
			if 기존_ids == self.dataObj.get('첨부file_fks') :
				pass
			else :
				sendData.update (  {'첨부file_fks' : 기존_ids })


		###  4. inputDict  and el_info_fk update : signal emit ( sendData:dict )
		for key, wid in self.inputDict.items():
			sendData[key] = Object_Get_Value( wid ).get()

		if self.el_info_fk > 0 : 
			sendData['el_info_fk'] = self.el_info_fk
		self.signal_save.emit( sendData )
		

	### trigger functions
	@pyqtSlot()
	def handle_PB_Upload_Excel(self):
		""" 관리자용 table excel upload"""
		fName, _ = QFileDialog.getOpenFileName(self , 'Open file', str(Path.home()) )
		if fName:
			self.dataObj = Upload_Excel_작지( fName )._getDataObj()
			self.dataObj['id'] = -1

			pilImage = self.dataObj.pop('pilImage',None)
			ic(pilImage )
			self.ui.imageViewer_wid.update_kwargs( pilImage = pilImage )
			

			self.table_api_datas = self.dataObj.pop('process_fks')
			cleaned_list = []
			for obj in self.table_api_datas:
				cleaned_dict = {}
				for key, value in obj.items():
					if isinstance( value, str) :
						cleaned_dict[key] = value.strip()
					else:
						cleaned_dict[key] = value
				cleaned_list.append( cleaned_dict )
			self.table_api_datas = cleaned_list
			self.ui.wid_table._update_data ( api_data = self.table_api_datas )

			keysList = list (self.inputDict.keys() )
			for key, value in self.dataObj.items():
				if key in keysList:
					Object_Set_Value( self.inputDict[key], value )
					if not self.is_Edit:
						Object_ReadOnly( self.inputDict[key], value  )


	@pyqtSlot()
	def handle_PB_Download_Excel(self) :
		excel = Save_Excel_format_작지( dataObj=self.dataObj, process = self.table_api_datas, el_info_dict=self.el_info_dict )
		# 	fks_list = ['process_fks','첨부file_fks']
		# )
		fName = excel.save_to_excel_from_dict()
		if fName:
			msgBox = QMessageBox.information(self, "저장 성공", f"{fName} 으로 저장되었읍니다.", QMessageBox.Yes, QMessageBox.Yes )
		else:
			msgBox = QMessageBox.warning (self, "저장 실패", "File 저장에 실패하였읍니다.",  QMessageBox.Yes , QMessageBox.Yes)
										# self, 'DB에서 삭제', "DB에서 영구히 삭제됩니다.", QMessageBox.Yes 
										# QtWidgets.QMessageBox.Yes |  QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
										# )
	@pyqtSlot()
	def slot_conversion_to_pdf(self):

		for headName in ['적용부품', 'Material', '대표Process', '상세Process', '비고']:
			self.ui.wid_table._set_Row_Span(headName)

		# 화면 크기의 최대 높이로 설정
		screen = QApplication.primaryScreen()
		screen_size = screen.availableGeometry()
		self.resize(  self.width(), screen_size.height())

		self.ui.wid_table._resize_to_contents()


	@pyqtSlot()
	def slot_export_to_pdf(self):
		self.ui.frame_admin.hide()
		self.ui.frame_export.hide()
		self.export_to_pdf( self )

		# self.ui.wid_table._reset_Row_Span_All()
		# self.ui.wid_table._resize_to_contents()
		self.ui.frame_admin.setVisible(INFO.IS_DEV)
		self.ui.frame_export.show()

	def export_to_pdf(self , wid:QWidget, **kwargs ) :
		제목 = Object_Get_Value(self.inputDict['제목']).get()
		projNo= Object_Get_Value(self.inputDict['Proj_No']).get()
		고객사 = Object_Get_Value(self.inputDict['고객사']).get()
		defaultFName = f"{제목}_{고객사}_{projNo}.pdf"

		file_name, _ = QFileDialog.getSaveFileName(
			self,
			"PDF 저장",
			str(Path.home() / defaultFName),
			"PDF 파일 (*.pdf)"
		)
		
		if file_name:
			writer = QPdfWriter(file_name)
			
		# 용지 크기 설정
			page_size = self.ui.comboBox_Yongji.currentText()
			if page_size == "A4":
				writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
			elif page_size == "A3":
				writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
			# elif page_size == "Legal":
			# 	writer.setPageSize(QPageSize(QPageSize.PageSizeId.Legal))
				
			# 용지 방향 설정
			if self.ui.comboBox_Banghyang.currentText() == "가로":
				writer.setPageOrientation(QPageLayout.Orientation.Landscape)
			else:
				writer.setPageOrientation(QPageLayout.Orientation.Portrait)
				
		
			# 페이지 여백 설정
			writer.setPageMargins(QMarginsF(5, 5, 5, 5))
			
			painter = QPainter()
			painter.begin(writer)
			
			# 내용을 페이지 크기에 맞게 조정
			rect = painter.viewport()
			size = wid.size()
			scale = min(rect.width() / size.width(), rect.height() / size.height())
			painter.scale(scale, scale)
			
			wid.render(painter)
			painter.end()

			Utils.generate_QMsg_Information(self, title = 'Export to PDF 완료', text= f"\n\n{file_name} 으로 저장되었읍니다. \n\n")
	

	@pyqtSlot()
	def slot_map_view(self):
		from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
		address = self.ui.label_Info_addr.text()
		dlg = Dialog_Folium_Map(self, address= address )

	@pyqtSlot()
	def handle_textChanged_connectDisplay(self):
		msg = {}
		for name in self.connectDisplayNames:
			input = self.inputDict[name]
			msg[name] = input.text()
		self.signal_textChanged.emit (msg)


	@pyqtSlot()
	def slot_Info_search(self) -> None:
		obj = self.dataObj
		현장명_txt = Object_Get_Value( self.inputDict['제목'] ).get()

		dlg = QDialog(self)
		hLayout = QVBoxLayout()
		from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import 한국정보__for_Tab
	
		api_uri, api_url, db_field_url = INFO._get_URL_EL_INFO_한국정보(INFO)
		db_field_url = 'db-field-Elevator_Summary_WO설치일_선택menu_enable_View/'
		wid = 한국정보__for_Tab(
				dlg, ###😀관습적으로  self ㅜㅜ;;
				'', api_uri=api_uri, api_url=api_url, db_field_url=db_field_url, is_Auto_조회_Start=True, 
				param=f"search={현장명_txt}&page_size=25",
				search_str = 현장명_txt, 
				)
		hLayout.addWidget(wid)
		dlg.setLayout(hLayout)
		dlg.setWindowTitle( 'MOD 현장명 검색')
		dlg.setMinimumSize( 600, 800)
		dlg.show()

		wid.signal_select_row.connect (lambda EL_INFO: self.slot_select_row(dlg, obj, EL_INFO))
	
	def slot_select_row(self, wid:QWidget, apiDict:dict, EL_INFO:dict) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		ic ( apiDict, EL_INFO )

		#### el info render
		if EL_INFO:
			self.el_info_fk = EL_INFO.get('id')
			self.ui.label_Info_EL_SU.setText( str( EL_INFO.get('수량') ))
			self.ui.label_Info_floor_su.setText ( str( EL_INFO.get('운행층수') ) )
			self.ui.label_Info_addr.setText ( str(EL_INFO.get('건물주소') ) )

		wid.close()



