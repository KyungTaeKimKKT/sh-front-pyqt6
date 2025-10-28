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
from modules.PyQt.Tabs.생산지시서.dialog.ui.Ui_생산지시서_form_main_현대 import Ui_Form_HY

from modules.PyQt.User.object_value import Object_Set_Value, Object_Diable_Edit, Object_ReadOnly, Object_Get_Value
from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보

# from modules.PyQt.User.upload_excel_table import Upload_Excel_생산지시서
# from modules.PyQt.User.save_excel_format import Save_Excel_format_생산지시서

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class Wid_생산지시서_main(QWidget, Qwidget_Utils):
	signal_textChanged = pyqtSignal(dict)
	signal_save = pyqtSignal(dict)
	signal_cancel = pyqtSignal()
	signal_PB_CreateTab_clicked = pyqtSignal()

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

		self.ui = Ui_Form_HY()
		self.ui.setupUi(self)
		self.init_InputDict()

		self.user_defined_ui_setting()

		
		if hasattr(self, 'dataObj') :
			if self.dataObj['id'] > 0:
				self._render_from_DataObj()
			elif hasattr(self, 'is_update_By_Jakji') and self.is_update_By_Jakji:
				self._render_from_작업지침_obj()
			else:
				self._render_from_DataObj()

		self.triggerConnect()


		# if not self.is_Edit:
		# 	self.ui.PB_save.hide()
		# 	self.ui.PB_cancel.setText(' 확인 ')
		# 	self.ui.PB_Info_search.hide()
		# 	self.ui.file_upload_wid.update_kwargs( is_Editable= False)
		# 	self.slot_conversion_to_pdf()




	def init_InputDict(self) -> None:
		""" 각 dict는 {key : DB Field ; widget } 으로 구성
			특히, imageView, file, table의 key는 serializer 참조 """

		self.inputDict = {
			'Job_Name' : self.ui.lineEdit_Job_name,
			'Proj_No' : self.ui.lineEdit_Proj_No,
			'총수량' : self.ui.spinBox_chongsurang,
			'지시수량' : self.ui.spinBox_Daesu,
			'차수' : self.ui.spinBox_Chasu,
			'작성자' : self.ui.lineEdit_Name,
			'생산지시일' : self.ui.dateEdit_Produce,
			'소재발주일' : self.ui.dateEdit_Order,
			'구분' : self.ui.combo_edit_Gubun,
			'고객사' : self.ui.combo_edit_Gogaek,
			'생산형태' : self.ui.combo_eidt_Prod_Div,
		}

		self.작지_to_생지_conversion_Dict = {
			'제목' : 'Job_Name',
			'Proj_No' : 'Proj_No',
			'수량' : '총수량',
			'구분' : '구분',
			'고객사' : '고객사',
			'생산형태' : '생산형태',
			'작성자' : '작성자',
		}

		# self.imageViewerDict = {
		# 	'Rendering_file' : self.ui.imageViewer_wid,
		# }

		# self.file_uploadDict = {
		# 	'첨부file_fks' : self.ui.file_upload_wid,
		# }

		# self.table_Dict = {
		# 	'process_fks' : self.ui.wid_table,
		# }
		
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
				# case '작성자':
				# 	if not self.dataObj or len(self.dataObj.get(key,'')) == 0: 
				# 		input.setText(INFO.USERNAME)

		# self.ui.comboBox_Yongji.addItems ( ['A4','A3'])
		# self.ui.comboBox_Banghyang.addItems ( ['가로','세로'])

		# self.ui.PB_conversion.hide()
		
		# ### eco 관련
		# self.ui.frame_ECO.setVisible ( self.is_ECO )

	def _find_obj_in_list(self, targetList, condition:tuple[str,str,str,str]) -> dict:
		부품 = condition[0].lower()
		패널 = condition[1].lower()
		적용 = condition[2]
		비고 = condition[3]
		for obj in targetList:
			if 부품 in obj.get('적용부품', '').lower() and  패널 in obj.get('적용패널','').lower():
				_obj = copy.deepcopy(obj)
				_obj['적용'] = 적용
				_obj['비고'] = 비고
				return _obj
			if 부품 == '상판' and  부품 in obj.get('비고','').lower():
				_obj = copy.deepcopy(obj)
				_obj['적용'] = 적용
				_obj['비고'] = 비고
				return _obj	
		return {}

	def _render_from_작업지침_obj(self):
		
		for 작지_key, 생지_key in self.작지_to_생지_conversion_Dict.items():
			try:
				match 작지_key:
					case '생산형태':
						Object_Set_Value( self.inputDict[생지_key], INFO.생산형태_Widget_items[0])
					case _:
						Object_Set_Value( self.inputDict[생지_key], self.작업지침_obj.get(작지_key))
			except:


		#### 😀 Process_fks : 즉, HTM_Table
		process_fks =  self.작업지침_obj.get('process_fks', []) 
		if len(process_fks) > 0:
			param = f"?ids={(',').join( [str(id) for id in process_fks] )}&page_size=0"
			is_ok, _json = APP.API.getlist(INFO.URL_작업지침_PROCESS_DB + param )
			if is_ok:
				ic(_json )
				for item in _json:
					# id 값을 old_id로 복사하고 id를 -1로 설정
					item['작지Process_fk'] = item.pop('id')
					item['id'] = -1
					item['소재'] = item.pop('Material')
					item['생산처'] = '음성'
				
				표시순서_maping = [
					('FRONT','FRONT','WALL','#1, #11번 (FRONT)'),('SIDE', 'SIDE','WALL','#2,10번 (SIDE/SIDE)'),( 'SIDE','SIDE','WALL','#4,8번 (SIDE/SIDE)'),
					('REAR','SIDE','WALL','#5,7번 (REAR SIDE)'),
					('SIDE','CENTER','WALL','#3,9번 (SIDE CENTER)'), ('REAR','CENTER','WALL','#6번 (REAR CENTER)'), ('상판','','상판','FIXING BRACKET'),('CAR DOOR','', 'CAR DOOR',''),
					('HATCH DOOR','기준층', 'HATCH DOOR\n(기준층)',''), ('HATCH DOOR','기타층','HATCH DOOR \n(기타층)',''), 
				    ('JAMB','기준층', 'JAMB\n(기준층)','발주서 접수후 진행예정!!'),('JAMB','기타층', 'JAMB\n(기타층)','발주서 접수후 진행예정!!')
				   ]

				변환된List = []
				for idx, tuple_str in enumerate(표시순서_maping) :
					obj = self._find_obj_in_list ( _json, tuple_str )
					obj['표시순서'] = idx
					변환된List.append( obj)
				ic( 변환된List)
				self.table_HTM_api_datas = 변환된List

				### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
				if self.is_ECO:
					for obj in self.table_HTM_api_datas:
						obj['id'] = -1 

			else:
				Utils.generate_QMsg_critical(self)
		else:
			self.table_HTM_api_datas = []

		_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_HTM_Table )
		if _isOk:
			if not self.is_Edit:
				db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
			self.ui.wid_table_HTM._update_data(
				api_data=self.table_HTM_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
				url = INFO.URL_생산지시_HTM_Table,
				**db_fields,
			)		
		else:
			Utils.generate_QMsg_critical(self)

		#### 😀 도면정보_fks : 즉, table_
		도면정보_fks = self.dataObj.get('도면정보_fks', []) 
		ic (도면정보_fks)
		if len(도면정보_fks) > 0:
			param = f"?ids={(',').join( [str(id) for id in 도면정보_fks] )}&page_size=0"
			is_ok, _json = APP.API.getlist(INFO.URL_생산지시_도면정보_Table + param )
			if is_ok:
				self.table_도면정보_api_datas = _json
				ic (self.table_도면정보_api_datas)
				### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
				if self.is_ECO:
					for obj in self.table_도면정보_api_datas:
						obj['id'] = -1 

			else:
				Utils.generate_QMsg_critical(self)
		else:
			self.table_도면정보_api_datas = []

		_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_도면정보_Table )
		if _isOk:
			if not self.is_Edit:
				db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
			self.ui.wid_table_Domyun._update_data(
				api_data=self.table_도면정보_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
				url = INFO.URL_생산지시_도면정보_Table,
				**db_fields,
			)		
		else:
			Utils.generate_QMsg_critical(self)


	def _render_from_DataObj(self):
		ic(self.dataObj)
		keysList = list (self.inputDict.keys() )
		if hasattr(self, 'dataObj') :
			for key, value in self.dataObj.items():
				try:
					if key in keysList:
						if self.is_Edit:
							Object_Set_Value( self.inputDict[key], value )
						else:
							Object_ReadOnly( self.inputDict[key], value  )
				except:
					pass

			#### 😀 Process_fks : 즉, HTM_Table
			process_fks = self.dataObj.get('process_fks', []) 
			if len(process_fks) > 0:
				param = f"?ids={(',').join( [str(id) for id in process_fks] )}&page_size=0"
				is_ok, _json = APP.API.getlist(INFO.URL_생산지시_HTM_Table + param )
				if is_ok:
					self.table_HTM_api_datas = _json
					# self.slot_update_LCD( self.ui.lcd_Total_HTM, sum([ obj['수량']  for obj in _json if isinstance(obj['수량'], int) and 'jamb' not in obj['적용'].lower() ]) )

					### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
					if self.is_ECO:
						for obj in self.table_HTM_api_datas:
							obj['id'] = -1 

				else:
					Utils.generate_QMsg_critical(self)
			else:
				self.table_HTM_api_datas = []

			_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_HTM_Table )
			if _isOk:
				if not self.is_Edit:
					db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
				self.ui.wid_table_HTM._update_data(
					api_data=self.table_HTM_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
					url = INFO.URL_생산지시_HTM_Table,
					**db_fields,
				)		
			else:
				Utils.generate_QMsg_critical(self)

			#### 😀 도면정보_fks : 즉, table_
			도면정보_fks = self.dataObj.get('도면정보_fks', []) 
			# ic (도면정보_fks)
			if len(도면정보_fks) > 0:
				param = f"?ids={(',').join( [str(id) for id in 도면정보_fks] )}&page_size=0"
				is_ok, _json = APP.API.getlist(INFO.URL_생산지시_도면정보_Table + param )
				if is_ok:
					self.table_도면정보_api_datas = _json

					# ic (self.table_도면정보_api_datas)
					### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
					if self.is_ECO:
						for obj in self.table_도면정보_api_datas:
							obj['id'] = -1 

				else:
					Utils.generate_QMsg_critical(self)
			else:
				self.table_도면정보_api_datas = []

			_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_도면정보_Table )
			if _isOk:
				if not self.is_Edit:
					db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
				self.ui.wid_table_Domyun._update_data(
					api_data=self.table_도면정보_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
					url = INFO.URL_생산지시_도면정보_Table,
					**db_fields,
				)		

				
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

		self.ui.wid_table_Domyun.signal_sum_changed.connect ( lambda _sum, _widLCD= self.ui.lcd_Total_Hogi : self.slot_update_LCD(_widLCD, _sum) )
		self.ui.wid_table_HTM.signal_sum_changed.connect ( lambda _sum, _widLCD= self.ui.lcd_Total_HTM : self.slot_update_LCD(_widLCD, _sum) )

		### 😀각 table의 sum signal and slot  define후, 해당 method 호출하여 update함
		self.ui.wid_table_HTM.table_model.calculateSum_byHeadName(headerName='수량')
		self.ui.wid_table_Domyun.table_model.calculateSum()
		# self.ui.PB_conversion.clicked.connect ( self.slot_conversion_to_pdf)
		# self.ui.PB_export_to_pdf.clicked.connect ( self.slot_export_to_pdf)

		self.ui.PB_save.clicked.connect(self.handle_PB_save)
		self.ui.PB_cancel.clicked.connect(lambda: self.signal_cancel.emit())	

		self.ui.PB_CreateTab.clicked.connect ( lambda: self.signal_PB_CreateTab_clicked.emit() )	

		# for name in self.connectDisplayNames:
		# 	input = self.inputDict[name]
		# 	if isinstance ( input, QLineEdit) :
		# 		input.textChanged.connect(self.handle_textChanged_connectDisplay)

	def slot_update_LCD ( self, _wid:QLCDNumber, _sum :int ):
		_wid.display ( _sum )
		style_dict = { False : """
								QLCDNumber {
									background-color: red;
									color: white;
								}
							""",
 						True: """
								QLCDNumber {
									background-color: yellow;
									color: black;
								}
							"""
		}
		is_same = self.ui.lcd_Total_Hogi.value() == self.ui.lcd_Total_HTM.value()
		self.ui.lcd_Total_Hogi.setStyleSheet( style_dict[is_same] )
		self.ui.lcd_Total_HTM.setStyleSheet( style_dict[is_same] )

 		
	@pyqtSlot()
	def handle_PB_save(self):				
		sendData = {}
		sendData['작성자_fk'] = INFO.USERID

		# if len(영업담당자:= self.ui.lineEdit_Yungyub.text() ) > 0:
		# 	if ( 영업담당자_info := INFO()._get_user_info_by_name(영업담당자) ):
		# 		sendData['영업담당자_fk'] = 영업담당자_info['id']
		# 	else:
		# 		Utils.generate_QMsg_critical(self, title="영업담당자 확인 오류", text="영업담당자를 확인 바랍니다.")
		# 		return 
			

		### 1. 의장TABLE
		의장_datas = self.ui.wid_table_HTM._get_Model_data()
		if Utils.compare_dict_lists( self.table_HTM_api_datas, 의장_datas, del_keys= []) :
			ic ( 'No change : 의장_datas')
		else :
			threadingTargets = [ {'url':INFO.URL_생산지시_HTM_Table, 'dataObj':{ 'id': 의장dict.pop('id')}, 'sendData': 의장dict } for 의장dict in 의장_datas ]
			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				process_fks = [ future.result()[1].get('id') for index,future in futures.items() ]
				sendData.update ( {'process_fks' : process_fks })
			else:
				Utils.generate_QMsg_critical(self)


		#### 2. 도면정보_fks : 즉, table_
		도면_datas = self.ui.wid_table_Domyun._get_Model_data()
		if Utils.compare_dict_lists( self.table_도면정보_api_datas, 도면_datas, del_keys= []) :
			ic ( 'No change : 도면_datas')
		else :
			threadingTargets = [ {'url': INFO.URL_생산지시_도면정보_Table, 'dataObj':{ 'id': 도면dict.pop('id')}, 'sendData': 도면dict } for 도면dict in 도면_datas ]
			# ic (threadingTargets)
			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )
			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				도면정보_fks = [ future.result()[1].get('id') for index,future in futures.items() ]
				sendData.update ( {'도면정보_fks' : 도면정보_fks })
			else:
				Utils.generate_QMsg_critical(self)


		###  4. inputDict  and el_info_fk update : signal emit ( sendData:dict )
		for key, wid in self.inputDict.items():
			sendData[key] = Object_Get_Value( wid ).get()

		# if self.el_info_fk > 0 : 
		# 	sendData['el_info_fk'] = self.el_info_fk
		self.signal_save.emit( sendData )
		

	### trigger functions
	@pyqtSlot()
	def handle_PB_Upload_Excel(self):
		""" 관리자용 table excel upload"""
		fName, _ = QFileDialog.getOpenFileName(self , 'Open file', str(Path.home()) )
		if fName:
			self.dataObj = Upload_Excel_생산지시서( fName )._getDataObj()
			self.dataObj['id'] = -1

			pilImage = self.dataObj.pop('pilImage',None)
			ic(pilImage )
			self.ui.imageViewer_wid.update_kwargs( pilImage = pilImage )
			

			self.table_HTM_api_datas = self.dataObj.pop('process_fks')
			cleaned_list = []
			for obj in self.table_HTM_api_datas:
				cleaned_dict = {}
				for key, value in obj.items():
					if isinstance( value, str) :
						cleaned_dict[key] = value.strip()
					else:
						cleaned_dict[key] = value
				cleaned_list.append( cleaned_dict )
			self.table_HTM_api_datas = cleaned_list
			self.ui.wid_table._update_data ( api_data = self.table_HTM_api_datas )

			keysList = list (self.inputDict.keys() )
			for key, value in self.dataObj.items():
				if key in keysList:
					Object_Set_Value( self.inputDict[key], value )
					if not self.is_Edit:
						Object_ReadOnly( self.inputDict[key], value  )


	@pyqtSlot()
	def handle_PB_Download_Excel(self) :
		excel = Save_Excel_format_생산지시서( dataObj=self.dataObj, process = self.table_HTM_api_datas, el_info_dict=self.el_info_dict )
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



