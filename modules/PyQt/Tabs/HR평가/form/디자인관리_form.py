import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import urllib
import datetime
import json
from pathlib import Path

import copy

# import user_defined compoent
from modules.PyQt.Tabs.디자인관리.ui.Ui_디자인관리_의뢰 import Ui_Form
from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보

from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly


import modules.user.utils as Utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 디자인관리_의뢰_Form(  QDialog,Ui_Form,  Qwidget_Utils):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='' ):
		super().__init__(parent)
		self.url = url
		self.dataObj= {}
		self.현장명_fks =[]
		self.skip = []

		self.setupUi(self)		

		self.validator_list = ['현장명', '상세내용',  ]	
		self.updateList_el정보 = ['현장명', 'el수량', '운행층수']
		self.inputDict  = {
			'구분': self.wid_Gubun ,
			'고객사': self.wid_Gogaek,
			'현장명' : self.lineEdit_Huynjang ,
			'el수량': self.spinBox_El_surang ,
			'운행층수': self.spinBox_Unhaeng ,
			'비고':  self.plainTextEdit_Bigo ,
			'상세내용': self.plainTextEdit_Sangse ,
			'샘플의뢰여부':self.checkBox_Sample ,
			'완료요청일': self.dateTimeEdit_Complete ,
		}

		self.wid_FileUpload_File_keyName = '의뢰file_fks'
		self.file_uploadDict = {
			self.wid_FileUpload_File_keyName : self.wid_FileUpload,
		}
		### self.wid_FileUpload 초기화
		self.wid_FileUpload.newFiles_key = self.wid_FileUpload_File_keyName
		# self.Main_conversion_Dict = {
		# 	'제목' : 'job_name',
		# 	'proj_No' : 'proj_No',
		# 	'수량' : '총수량',
		# 	'구분' : '구분',
		# 	'고객사' : '고객사',
		# 	'생산형태' : '생산형태',
		# }
		

	def run(self):
		self.show()
		self.triggerConnect()
		if self.validator_list : self._enable_validator()

	def triggerConnect(self):
		super().triggerConnect()
		self.wid_Gubun.currentTextChanged.connect( self.handle_changed_Gubun)

	def handle_changed_Gubun(self):
		if 'MOD' in self.wid_Gubun.getValue().upper():
			self.elevator_info = Elevator_한국정보(self)
			self.elevator_info.run()
			self.elevator_info.signal.connect(self.slot_elevator_info_siganl)
		else :
			if getattr(self, 'elevator_info',None) : 
				self.elevator_info.close()

	def slot_elevator_info_siganl(self, msg:dict):
		self.display_el정보 ( msg.get('select') )

	# ### save 
	def func_save(self) -> None:
		api_send_data = self._get_value_from_InputDict()
		json_dict, api_send_files = self._get_value_from_fileUpload()

		api_send_data.update(json_dict)

		### api_send_data update
		api_send_data['등록일'] = datetime.datetime.now()

		if self.현장명_fks:
			api_send_data['현장명_fk_ids'] = json.dumps(self.현장명_fks)


		is_ok, _ = APP.API.Send( self.url, self.dataObj, api_send_data,  api_send_files)
		if is_ok:
			self.signal.emit({'action':'update'})
			self.close()

	def editMode(self):
		super().editMode()
		self.display_el정보(infoList=self.dataObj.get('현장명_fk') )

	def viewMode(self):
		super().viewMode()
		self.display_el정보(infoList=self.dataObj.get('현장명_fk') , is_ViewMode=True)

		self.PB_save.hide()
		self.PB_cancel.setText('확인')
	
	def display_el정보(self, infoList:list, is_ViewMode=False) -> None:
		if not infoList :
			self.lineEdit_Juso.setReadOnly(is_ViewMode)
			return 
		
		현장명_fks =[]
		주소txt =''
		value_dict = {
			'현장명' : '',
			'el수량' : 0,
			'운행층수' : 0,
		}
		for info in infoList:			
			for (key, value) in info.items():
				match key :
					case '건물명': 
						value_dict['현장명'] += value
					case '수량':
						value_dict['el수량'] += value						
					case '운행층수':
						value_dict['운행층수'] += value
					case '건물주소':
						주소txt += value
					case 'id':
						현장명_fks.append(value)
		if 현장명_fks : self.현장명_fks = 현장명_fks
		for name in self.updateList_el정보:
			Object_Set_Value(input=self.inputDict[name], value=value_dict[name])	
		self.lineEdit_Juso.setText(주소txt)
		self.lineEdit_Juso.setReadOnly(is_ViewMode)

