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
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly



from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget
from modules.PyQt.component.file_download_listwidget import File_Download_ListWidget

import modules.user.utils as Utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class CS_활동현황_Form( Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)
		self.no_Edit =[]
		self.validator_list = []
		self.현장명_fks = []	

		self.dataList = []

		self.inputType = {
			'활동일'  : 'QDateEdit(parent)',
			'활동현황' : 'QTextEdit(parent)',
		}
		#### action을 먼저 저장하고, 받은 id로
		#### fks =[] 로 넣어서 보냄
		self.action_url = '품질경영/CS관리-action/'

		self.run()

	def UI(self):
		self.setMinimumSize( 300, 800)
		self.mainLayout = QVBoxLayout()
		####
		self.title = QLabel(self)
		self.title.setText(self.title_text)
		self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:32px;color:white;background-color:black;")
		self.mainLayout.addWidget(self.title)

		hbox = QHBoxLayout()
		hbox.addStretch()
		self.PB_save = QPushButton('Save')
		# self.PB_save.setEnabled(False)
		self.PB_cancel = QPushButton('Cancel')
		hbox.addWidget(self.PB_save)
		hbox.addWidget(self.PB_cancel)
		self.mainLayout.addLayout(hbox)
		

		self.setLayout(self.mainLayout)
		self.show()



	def _gen_by_inputType(self, dataObj:dict={}) -> QWidget:
		wid = QWidget()
		layout = QFormLayout()
		for (key, value) in self.inputType.items():
			if key in self.skip: continue   
			match key:
				case _:
					(_txt, _input) = self._gen_element(key, value)
					if  _txt is not None  and _input is not None:
						layout.addRow(_txt, _input)
						if dataObj:
							# Object_Set_Value(_input, dataObj.get(key, ''))
							Object_ReadOnly( _input, dataObj.get(key, ''))
					if isinstance( _input, QDateEdit):
						if not dataObj:
							_input.setDate(QDate.currentDate())
		self.wid_fileUpload = File_Upload_ListWidget(newFiles_key='files_fks')
		layout.addWidget(self.wid_fileUpload)
		wid.setLayout(layout)		
		return wid

	def run(self):				

		self.UI() 
		self.mainLayout.addWidget( self._gen_by_inputType() )

		for data in self.dataList :
			pass
		self.TriggerConnect()

	def TriggerConnect(self):
		super().TriggerConnect()
		# self.PB_검색.clicked.connect(self.func_search_elevator)

	### save 
	def func_save(self):
		for key in self.inputType.keys():
			if key == 'id' : continue
			self.result[key] = self._get_value(key)
		
		### 😀 manual get : custom widget
		self.result['등록일'] = datetime.date.today()
		self.result['등록자'] = INFO.USERNAME

		if ( 첨부파일들 := self.wid_fileUpload._getValue() ):
			self.result['files_fks_json'] = json.dumps( 첨부파일들.get('exist_DB_id') )
			if ( files_fks := 첨부파일들.get('new_DB') ):
				self.result_files.extend( files_fks )

		if Utils.compare_dict(self.dataObj, self.result) :
			reply = QMessageBox.warning(self, "저장확인", "변경사항이 없읍니다.", QMessageBox.Yes, QMessageBox.Yes )
			return

		else:
			is_ok, _json = APP.API.post( self.action_url, self.result, self.result_files )
			if is_ok:		
				actions = [ obj.get('id') for obj in self.dataObj.get('actions', [] ) ]	
				actions.append( _json.get('id'))
				is_ok, _ = APP.API.Send( self.url, 
										self.dataObj, 
										{'actions': json.dumps(actions)}, )
				if is_ok:
					self.signal.emit({'action':'update'})
					self.close()

	def func_search_elevator(self):
		self.elevator_info = Elevator_한국정보(self)
		self.elevator_info.run()
		### Elevator_한국정보 자체 있는 input 제거
		self.elevator_info.input_현장명.setVisible(False)
		self.elevator_info.pb_search.setVisible(False)
		self.elevator_info.input_현장명.setText( self.inputDict['현장명'].text())
		self.elevator_info.slot_search()

		self.elevator_info.signal.connect(self.slot_elevator_info_siganl)

	###
	def slot_elevator_info_siganl(self, msg:dict):
		# msg: {'select': [{'id': 148830, '건물명': '삼라마이다스빌', '건물주소': '경기도 성남시 분당구 정자일로 21 (금곡동)', '건물주소_찾기용': '경기도 성남시 분당구 정자일로 21 ', 'loc_x': 0.0, 'loc_y': 0.0, '시도': '경기', '시도_ISO': None, '시군구': '성남시 분당구', '최초설치일자': '2004-03-29', '수량': 3, 'timestamp': '2024-02-29T09:20:52.337516', '운행층수': 54}]}
		if ( select := msg.get('select', []) ):
			self.inputDict['현장명'].setText( select[0].get('건물명', ''))
			self.inputDict['el수량'].setValue( select[0].get('수량', 0) )
			self.inputDict['운행층수'].setValue( select[0].get('운행층수', 0))
			self.result['el_info_fk'] = select[0].get('id' )


class CS_활동현황_Form_View( CS_활동현황_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)


	def UI(self):
		super().UI()
		#### PB_save visible false, PB_cancel rename
		self.PB_save.setVisible(False)
		self.PB_cancel.setText('확인')
	

	def _gen_by_inputType(self, dataObj:dict={}) -> QWidget:
		wid = QWidget()
		layout = QFormLayout()
		for (key, value) in self.inputType.items():
			if key in self.skip: continue   
			match key:
				case _:
					(_txt, _input) = self._gen_element(key, value)
					if  _txt is not None  and _input is not None:
						layout.addRow(_txt, _input)
						if key == '활동일':
							label_등록자 = QLabel('등록자', self)
							label_등록자이름 = QLabel(dataObj.get('등록자'), self)
							layout.addRow(label_등록자, label_등록자이름)

						if dataObj:
							# Object_Set_Value(_input, dataObj.get(key, ''))
							Object_ReadOnly( _input, dataObj.get(key, ''))
					if isinstance( _input, QDateEdit):
						if not dataObj:
							_input.setDate(QDate.currentDate())
		if (initialData := dataObj.get('action_files', [])) :
			self.wid_fileDownload = File_Download_ListWidget(self, initialData=initialData)
		layout.addWidget(self.wid_fileDownload)
		wid.setLayout(layout)		
		return wid


	def run(self):				

		self.UI() 
		for action in self.dataObj.get('actions', []):
			self.mainLayout.addWidget(self._gen_by_inputType(action) )

		self.TriggerConnect()


