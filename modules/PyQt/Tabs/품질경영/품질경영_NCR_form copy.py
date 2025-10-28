import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import urllib
import datetime
import json
from pathlib import Path


# import user_defined compoent
from modules.PyQt.component.choice_combobox import Choice_ComboBox

from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly



from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget

import modules.user.utils as utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class NCR_Form(Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)
		self.no_Edit =[]
		self.validator_list = ['현장명']
		self.appData = parent.appData
		self.현장명_fks = []	
	
	def UI(self):
		if hasattr(self, 'formlayout') : utils.deleteLayout (self.formlayout)
		self.formlayout = QFormLayout()
		# self.formlayout.setSpacing(16)
		####
		self.title = QLabel(self)
		self.title.setText(self.title_text)
		self.title.setSizePolicy(QSizePolicy.Expanding, 0)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:32px;color:white;background-color:black;")
		self.formlayout.addRow(self.title)

		layout = QHBoxLayout()
		for index, (key, value) in enumerate(self.inputType.items()):
			if key in self.skip: continue

			match key:
				case '구분' |'고객사':
					(_txt, _input) = self._gen_element(key, value)
					if isinstance(_input, Choice_ComboBox):
						if key == '구분':
							_input.choices = self.appData._get_form_choices_구분()
							_input.currentTextChanged.connect(self.slot_changed_choices_GUBUN  )
						else:
							_input.choices = self.appData._get_form_choices_고객사()
						_input._render()
						if  _txt is not None  and _input is not None:
							self.formlayout.addRow(_txt, _input)
				case '의뢰파일':
					self.wid_fileUpload = File_Upload_ListWidget(self)
					self.wid_fileUpload.setObjectName("attchFile")
					self.formlayout.addRow(self.wid_fileUpload)
					self.inputDict['의뢰파일'] = self.wid_fileUpload
					
				case _:
					(_txt, _input) = self._gen_element(key, value)
					if  _txt is not None  and _input is not None:
						self.formlayout.addRow(_txt, _input)
						
			layout.addWidget(_txt)
			layout.addWidget(_input)
			layout.addStretch()
			if index % 2 == 0 :
				self.formlayout.addRow(layout)
				layout = QHBoxLayout()

		self.formlayout.addRow(layout)

		#😀
		self.user_defined_ui_setting()


		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_save = QPushButton('Save')
		self.PB_save.setEnabled(False)
		self.PB_cancel = QPushButton('Cancel')
		hbox.addWidget(self.PB_save)
		hbox.addWidget(self.PB_cancel)
		self.formlayout.addRow(hbox)
		

		self.setLayout(self.formlayout)
		self.setMinimumSize ( 320, 720)
		self.show()

	def user_defined_ui_setting(self):
		### 😀 QSpinbox default range setting ( defalult가 0,99 🤑)

		for (key, input) in self.inputDict.items():
			if isinstance(input, QDateEdit ):
				if not self.dataObj : input.setDate(QDate.currentDate() )
			if isinstance(input, QSpinBox ):
				if not self.dataObj : input.setRange(0, 10000)
			if key in ['완료요청일']:
				if isinstance( (input:= self.inputDict[key]), QDateTimeEdit ):
					input.setDateRange( QDate.currentDate(), QDate.currentDate().addMonths(1))
					input.setDate( QDate.currentDate().addDays(1))
		
		for key in self.no_Edit:
			inputObj = self.inputDict[key]
			Object_ReadOnly(input=inputObj, value = self.dataObj[key])
			

	def run(self):
		self.UI()        
		self.TriggerConnect()

		for key in self.validator_list:
			self.inputDict[key].textChanged.connect(self.check_validator)
	
	##### Trigger Func. #####
	#### 😀 구분 combo box change ==> gettext ==> if mod: elevator_info run()
	def slot_changed_choices_GUBUN(self):
		if 'mod' in self.sender().currentText().lower():
			self.elevator_info = Elevator_한국정보(self)
			self.elevator_info.run()
			self.elevator_info.signal.connect(self.slot_elevator_info_siganl)
		else :
			if getattr(self, 'elevator_info',None) : 
				self.elevator_info.close()

	def slot_elevator_info_siganl(self, msg:dict):

		self.현장명_fks =[]
		value_건물명 = ''
		value_수량 = 0
		value_운행층수 = 0
		for info in msg.get('select'):			
			for (key, value) in info.items():
				match key :
					case '건물명': 
						value_건물명 += value
					case '수량':
						value_수량 += value						
					case '운행층수':
						value_운행층수 += value
					case 'id':
						self.현장명_fks.append(value)

		Object_Set_Value(input=self.inputDict['현장명'], value=value_건물명)	
		Object_Set_Value(input=self.inputDict['el수량'], value=value_수량 )
		Object_Set_Value(input=self.inputDict['운행층수'], value=value_운행층수 )


	def func_save(self):
		for key in self.inputType.keys():
			if key == 'id' : continue
			if key == '의뢰파일': continue			
			self.result[key] = self._get_value(key)
		
		self.result['현장명_fk'] = self.현장명_fks if self.현장명_fks else []
		self.result['등록일'] = QDateTime.currentDateTime().toString(INFO.DateTimeFormat )
		self.result_files = []


		####😀 key는  API DATA에 따라서, 
		if (의뢰file := self.wid_fileUpload._getValue() ):
			exist_DB_ids:list = 의뢰file.get('exist_DB_id')
			if len(exist_DB_ids):
				self.result['의뢰file_fks_json'] = json.dumps( exist_DB_ids )
			else:
				self.result['의뢰file_삭제'] = True
				
			if ( 의뢰file_fks := 의뢰file.get('new_DB') ):
				#### 😀 change for api m2m field
				self.result_files.extend( self._conversion_to_api_field( 
											change_key ='의뢰file', original= 의뢰file_fks ) )
		# self.api_send()
	
	def _conversion_to_api_field(self, change_key:str, original:list) -> list:
		"""
			😀change tuple value 
			original : [('첨부file_fks', <_io.BufferedReader name='/home/kkt/Downloads.xlsx'>)]
		"""
		result = []
		for item in original:
			temp = list(item)
			temp[0]  = change_key
			result.append(tuple(temp) )
		return result

	## 😀 form 의 save method에서 기본적으로 get_value ==> set_value로..
	def editMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == 'id':continue
			if key == '의뢰파일': continue

			inputObj = self.inputDict[key]
			Object_Set_Value(input=inputObj, value = self.dataObj[key])
			# if isinstance(  inputObj, 고객사_Widget) :
			# 	inputObj.setValue(self.dataObj[key] )
		
		###😀 api data에 따라서.
		if (fNames := self.dataObj.get('의뢰file_fks', None) ) :
			self.wid_fileUpload._setValue(fNames)

	## 😀 form 의 edit method에서 기본적으로 set_value 에서 readonly로
	#  Object_Set_Valuee ==> Object_ReadOnly로.. button setVisible(False)
	def viewMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == 'id':continue
			if key == '의뢰파일':continue
			inputObj = self.inputDict[key]
			Object_ReadOnly(input=inputObj, value = self.dataObj[key])

		if (fNames := self.dataObj.get('의뢰file_fks', None) ) :
			self.wid_fileUpload._setValue(fNames)
		self.wid_fileUpload._setReadOnly()
		
		self.PB_save.setVisible(False)
		self.PB_cancel.setText('확인')

			

	def api_send(self):
		if bool(self.dataObj):
			ID = self.dataObj.get('id', None)
			if ID is not None and ID >0:
				is_ok, res_json = APP.API.patch(url= self.url+ str(self.dataObj.get('id')) +'/',
												data=self.result,
												files=self.result_files)
			else:
				is_ok, res_json = APP.API.post(url= self.url,
								data=self.result ,
								files= self.result_files)
		else:
			is_ok, res_json = APP.API.post(url= self.url,
											data=self.result ,
											files= self.result_files)
			
		if is_ok:
			self.signal.emit({'action':'update'})
			self.close()
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')

	### Hard-coding 😀😀
	def _gen_by_key(self, key:str='', value=None, label:object='', input:object=None):
		match key:
			case '현장명':
				if isinstance(input, QLineEdit ):
					input.setPlaceholderText("제목을 넣으세요(필수★)")
					# input.textChanged.connect(self.check_validator)
			# case '일자':
			# 	if isinstance(input, QtWidgets.QDateEdit ):
			# 		input.setDate(QDate.currentDate())
			
			case _:
				pass				
			
		self.inputDict[key] = input

		return (label, input)
	
	def check_validator(self) -> bool:
		for key in self.validator_list:
			if self._get_value( key ):
				self.inputDict[key].setStyleSheet(ST.edit_)
				self.PB_save.setEnabled(True)
				return True
		self.PB_save.setEnabled(False)
		return False
	


