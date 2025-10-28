import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import urllib
import datetime
import json
from pathlib import Path


# import user_defined compoent
# from modules.PyQt.Tabs.품질경영.품질경영_Qcost import QCost
# from modules.PyQt.Tabs.품질경영.품질경영_부적합내용 import 부적합내용
# from modules.PyQt.component.choice_combobox import Choice_ComboBox
# from modules.PyQt.component.combo_lineedit import Combo_LineEdit

from modules.user.api import Api_SH
# from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly



from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget

import modules.user.utils as Utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

# class NumericDelegate(QStyledItemDelegate):
# 	def createEditor(self, parent, option, index):
# 		# if index.row() == 0 : return 
# 		editor = super(NumericDelegate, self).createEditor(parent, option, index)
# 		if isinstance(editor, QLineEdit):
# 			reg_ex = QRegExp("^[0-9]*$")
# 			validator = QRegExpValidator(reg_ex, editor)
# 			editor.setValidator(validator)
# 		return editor


class CS_Form( Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)
		self.no_Edit =[]
		self.validator_list = []
		self.현장명_fks = []	

		self.run()


	def UI(self):
		self.formlayout = QFormLayout()
		####
		self.title = QLabel(self)
		self.title.setText(self.title_text)
		self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:32px;color:white;background-color:black;")
		self.formlayout.addRow(self.title)

		for (key, value) in self.inputType.items():
			if key in self.skip: continue
   
			match key:
				case '현장명':
					(_txt, _input) = self._gen_element(key, value)
					self.PB_검색 = QPushButton('검색')
					self.formlayout.addRow(_txt, _input )	
					hbox = QHBoxLayout()
					hbox.addStretch()			
					self.PB_검색 = QPushButton('검색')
					hbox.addWidget(self.PB_검색)
					self.formlayout.addRow( hbox )

				case _:
					(_txt, _input) = self._gen_element(key, value)
					if  _txt is not None  and _input is not None:
						self.formlayout.addRow(_txt, _input)
		
		### file upload 추가###
		self.wid_fileUpload = File_Upload_ListWidget(newFiles_key='claim_files')
		self.formlayout.addWidget(self.wid_fileUpload)
		#######################

		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_save = QPushButton('Save')
		# self.PB_save.setEnabled(False)
		self.PB_cancel = QPushButton('Cancel')
		hbox.addWidget(self.PB_save)
		hbox.addWidget(self.PB_cancel)
		self.formlayout.addRow(hbox)
		
		self.setLayout(self.formlayout)
		self.show()

		self.inputDict['el수량'].setRange(0, 1000)
		self.inputDict['운행층수'].setRange(0, 10000)
		self.inputDict['Elevator사']._render()


	def run(self):
		self.UI() 
		self.TriggerConnect()

	def TriggerConnect(self):
		super().TriggerConnect()
		self.PB_검색.clicked.connect(self.func_search_elevator)

	### save 
	def func_save(self):
		for key in self.inputType.keys():
			if key == 'id' : continue
			self.result[key] = self._get_value(key)
		
		### 😀 manual get : custom widget
		self.result['등록일'] = datetime.date.today()
		self.result['등록자'] = INFO.USERNAME
		self.result['진행현황'] = '작성중'

		# if (rendering_file := self.imageViewer._getValue() ) != () :
		# 	self.result_files.extend ( [rendering_file] )


		if (첨부파일 := self.wid_fileUpload._getValue() ):
			self.result['claim_files_json'] = json.dumps( 첨부파일.get('exist_DB_id') )
			if ( 첨부file_fks := 첨부파일.get('new_DB') ):
				self.result_files.extend( 첨부file_fks )

		if Utils.compare_dict(self.dataObj, self.result) :
			reply = QMessageBox.warning(self, "저장확인", "변경사항이 없읍니다.", QMessageBox.Yes, QMessageBox.Yes )
			return

		else:
			# self.result['품질비용_fk'] = json.dumps( self.result['품질비용_fk'] )
			# self.result['부적합내용_fks'] = json.dumps ( self.tableWidget_Bujek.get_Api_data() )
			is_ok, _ = APP.API.Send( self.url, self.dataObj, self.result, self.result_files)
			if is_ok:
				self.signal.emit({'action':'update'})
				self.close()

	def func_search_elevator(self):
		self.elevator_info = Elevator_한국정보(self)
		self.elevator_info.run()
		### Elevator_한국정보 자체 있는 input 제거
		# self.elevator_info.wid_search_for_tab.검색_lineEdit.setVisible(False)
		# self.elevator_info.pb_search.setVisible(False)
		self.elevator_info.wid_search_for_tab.검색_lineEdit.setText( self.inputDict['현장명'].text())
		self.elevator_info.slot_search_for_tab({'search':self.inputDict['현장명'].text()})

		self.elevator_info.signal.connect(self.slot_elevator_info_siganl)

	###
	def slot_elevator_info_siganl(self, msg:dict):
		# msg: {'select': [{'id': 148830, '건물명': '삼라마이다스빌', '건물주소': '경기도 성남시 분당구 정자일로 21 (금곡동)', '건물주소_찾기용': '경기도 성남시 분당구 정자일로 21 ', 'loc_x': 0.0, 'loc_y': 0.0, '시도': '경기', '시도_ISO': None, '시군구': '성남시 분당구', '최초설치일자': '2004-03-29', '수량': 3, 'timestamp': '2024-02-29T09:20:52.337516', '운행층수': 54}]}
		if ( select := msg.get('select', []) ):
			self.inputDict['현장명'].setText( select[0].get('건물명', ''))
			self.inputDict['el수량'].setValue( select[0].get('수량', 0) )
			self.inputDict['운행층수'].setValue( select[0].get('운행층수', 0))
			self.result['el_info_fk'] = select[0].get('id' )

	def editMode(self):
		super().editMode()
		self.wid_fileUpload._setValue( self.dataObj.get('claim_files'))

	def viewMode(self):
		super().viewMode()
		self.wid_fileUpload._setValue( self.dataObj.get('claim_files'))
		self.wid_fileUpload._setReadOnly()