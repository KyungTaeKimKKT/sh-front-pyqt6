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
from modules.PyQt.Tabs.Base import Base_App
from modules.PyQt.User.Tb_Model import Base_TableModel
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.User.Tb_Delegate import Base_Delegate

from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit

from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly



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



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData:
	header = None	#### none 이면 header_type keys 
	header_type = {
			'id' : '___',
			'소재': '___',
			'치수': '___',
			'두께': '___',
			'폭'  : '___',
			'길이': '___',
			'적용' : 'Material_Widget(parent)',
			'수량': '___',		

		}
	no_Edit = list( header_type.keys() )
	hidden_column = ['id'] ###['id', '생산capa','등록자',]
	pageSize = 100
	suffix = f'?page_size={pageSize}'
	search_msg = {}	

	def __init__(self):	
		self.table_Sorting = True
		self.h_header_context_menu = {}
		self.v_header_context_menu = {}
		# self.h_header_context_menu = self.menu.generate(
		# 	[ 'New','Delete','seperator','Search','seperator','Export_to_Excel',
		# 		 'seperator', 
		# 		'Form_New','Form_View']
		# )
		# self.v_header_context_menu = self.menu.generate(
		# 	['Set_row_span', 'Reset_row_span']
		# )

class App_TableModel(Base_TableModel):
	pass

class App_TableView ( My_TableView ):
	pass

class App_Delegate(Base_Delegate):
	pass

# [
# {'소재': 'GI', '치수': '1.6T*1000*2550', '적용': 'WALL', '수량': 24}, 
# {'소재': 'GI', '치수': '1.6T*1219*2240', '적용': 'CAR DOOR', '수량': 6}, 
# {'소재': 'GI', '치수': '1.6T*1219*2275', '적용': 'HATCH DOOR\n(기준층,지하층)\n(4면밴딩)', '수량': 6}, 
# {'소재': 'GI', '치수': '1.6T*1219*2275', '적용': 'HATCH DOOR\n(기타층)\n(4면밴딩)', '수량': 119}, 
# {'소재': 'GI', '치수': '1.6T*1219*2275', '적용': '상판', '수량': 2}, 
# {'소재': 'GI', '치수': '1.6T*1219*2550', '적용': 'WALL', '수량': 8}]


class Table_Main( Base_App ):
	signal = pyqtSignal(dict)

	def __init__(self, parent:QtWidgets.QMainWindow=None,  appFullName:str='', url:str='' ):
		super().__init__( parent,  appFullName, url  )
			
		####  😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################


	def UI(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.tableView = App_TableView(self)
		self.vlayout.addWidget(self.tableView)		
		self.setLayout(self.vlayout)

	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vlayout'): Utils.deleteLayout(self.vlayout)
		# self.UI()
		if self.get_api_and_model_table_generate():
			self.table.signal.connect (self.slot_table_siganl)
		else:
			if self.is_api_ok:
				pass
			else:
				toast = User_Toast(self, text='server not connected', style='ERROR')
		
	def _check_api_Result(self, search_msg:dict=None) -> bool:
		return len(self.app_DB_data) > 0 
	
	def _get_Name(self, key:str, obj:dict) ->str:
		""" key는 self.header , obj는 app_DB_data dict"""
		value = obj.get(key , None)
		치수list = str(obj.get( '치수')).split('*')
		match key:
			case '두께':
				return 치수list[0].replace('T','').strip()
			case '폭':
				return 치수list[1].strip()
			case '길이':
				return 치수list[2].strip()

			case _:
				return value

	def TriggerConnect(self):
		self.PB_Save.clicked.connect(self.func_save)
		self.PB_Save_SPG.clicked.connect(self.func_save)
		self.PB_cancel.clicked.connect(self.close)
		self.PB_cancel_3.clicked.connect(self.close)

		self.lineEdit_Job_name.textChanged.connect(self.slot_update_Domyun_contents)
		self.lineEdit_Proj_No.textChanged.connect(self.slot_update_Domyun_contents)
		self.spinBox_Daesu.textChanged.connect(self.slot_update_Domyun_rows)

		self.tableView_Domyun.signal.connect( self.slot_tableView_Domyun_No)


	def slot_tableView_Domyun_No(self, msg:dict):
		self.lineEdit_Domyun.setText( msg.get('도면No'))
		self.lineEdit_Domyun.setStyleSheet(ST. edit_)

	def slot_update_Domyun_rows(self) -> None:
		obj:QWidget = self.sender()
		obj.setStyleSheet(ST.edit_)
		row수 = int( self._get_value(key='지시수량') )
		model_datas = self.tableView_Domyun.model_data
		deleted_row수 = len(model_datas) - 5
		### row 추가/삭제
		self.tableView_Domyun.model.beginResetModel()
		if row수 > deleted_row수 : 
			copyed_Row = copy.deepcopy( model_datas[-2] )
			for _ in range( row수 -  deleted_row수 ):
				model_datas.insert( -2, copyed_Row )
		elif row수 < deleted_row수 :
			for _ in range ( deleted_row수 - row수 ):
				model_datas.pop(-2)
		self.tableView_Domyun._calcurate_합계_All()
		self.tableView_Domyun.model.endResetModel()
		self.tableView_Domyun.render_span_head()
	
	def slot_update_Domyun_contents(self) -> None :
		obj:QWidget = self.sender()
		obj.setStyleSheet(ST.edit_)
		keyName = self._get_keyName_도면정보_model(obj.objectName() )
		for key, input in self.inputDict.items():
			if obj == input:
				value = self._get_value(key)
				model_datas = self.tableView_Domyun.model_data
				for index, row in enumerate(model_datas):
					if index in [0,1,2,3, len(model_datas)-1 ]: continue
					# 😀 https://stackoverflow.com/questions/76603422/update-a-qtableview-entirely-when-data-has-changed
					self.tableView_Domyun.model.beginResetModel()
					row[self._get_colNo_도면정보_header(keyName)] = value 
					self.tableView_Domyun.model.endResetModel()

		### spg Update		
		match keyName :
			case '현장명':
				self.lineEdit_SPG_hyunjang.setText(value)
				self.lineEdit_SPG_hyunjang.setStyleSheet(ST.edit_)
			case '공사번호':
				self.lineEdit_SPG_proj_No.setText(value)
				self.lineEdit_SPG_proj_No.setStyleSheet(ST.edit_)

	def _get_colNo_도면정보_header(self, key:str) ->int:
		return self.tableView_Domyun.header.index(key)
	
	def _get_keyName_도면정보_model(self, objName:str) ->str:
		ref_dict = {
			'lineEdit_Job_name' : '현장명',
			'lineEdit_Proj_No'  : '공사번호',
		}
		return ref_dict.get(objName)


	### save 
	def func_save(self) -> None:
		for key in self.inputType.keys():
			if key == 'id' : continue
			self.api_to_sendDatas[key] = self._get_value(key)
		### 😀 manual get : custom widget
		self.api_to_sendDatas['등록일'] = datetime.date.today()
		self.api_to_sendDatas['등록자'] = INFO.USERNAME
		self.api_to_sendDatas['진행현황'] = '작성중'

		### m2m field
		for key , inputObj in self.m2m_field.items():
			self.api_to_sendDatas[key] = inputObj.get_Api_data()


		# if (첨부파일 := self.wid_fileUpload._getValue() ):
		# 	self.api_to_sendDatas['claim_files_json'] = json.dumps( 첨부파일.get('exist_DB_id') )
		# 	if ( 첨부file_fks := 첨부파일.get('new_DB') ):
		# 		self.api_to_sendDatas_files.extend( 첨부file_fks )

		if Utils.compare_dict(self.dataObj, self.api_to_sendDatas) :
			reply = QMessageBox.warning(self, "저장확인", "변경사항이 없읍니다.", QMessageBox.Yes, QMessageBox.Yes )
			return

		else:
			for key , inputObj in self.m2m_field.items():
				# https://stackoverflow.com/questions/11875770/how-can-i-overcome-datetime-datetime-not-json-serializable
				self.api_to_sendDatas[key] = json.dumps( self.api_to_sendDatas[key] , indent=4, sort_keys=True, default=str)

			is_ok, _ = APP.API.Send( self.url, self.dataObj, self.api_to_sendDatas, self.api_to_sendDatas_files)
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
			self.api_to_sendDatas['el_info_fk'] = select[0].get('id' )

	def editMode(self):
		super().editMode()
		self.tableView_Domyun.app_DB_data = self.dataObj.get('도면정보_fks')
		self.tableView_Domyun.run()
		self.tableView_HTM.app_DB_data = self.dataObj.get('process_fks')
		self.tableView_HTM.run()
		# self.wid_fileUpload._setValue( self.dataObj.get('claim_files'))

	def viewMode(self):
		super().viewMode()
		# self.wid_fileUpload._setValue( self.dataObj.get('claim_files'))
		# self.wid_fileUpload._setReadOnly()