from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing
import copy
import json


# import user module

from modules.PyQt.Tabs.생산지시.생산지시용_작업지침서_조회 import 작지_배포_Tab
from modules.PyQt.Tabs.생산지시.생산지시용_NCR_조회 import NCR배포_Tab

# from modules.PyQt.Tabs.생산지시.ui.Ui_생산지시서_관리 import Ui_Form as Ui_생산지지서_관리

from modules.PyQt.Tabs.생산지시.components.tables.생산지시_tableview import 생산지시_Base_TableView
from modules.PyQt.Tabs.생산지시.components.tables.생산지시_delegate import 생산지시_Base_Delegate
from modules.PyQt.Tabs.생산지시.components.tables.생산지시_table_model import 생산지시_Base_TableModel
from modules.PyQt.Tabs.생산지시.components.forms.생산지시_form import 생산지시_Form
from modules.PyQt.Tabs.생산지시.components.forms.생산지시_form_OTIS import 생산지시_Form_OTIS
from modules.PyQt.Tabs.생산지시.components.forms.생산지시_form_TKE import 생산지시_Form_TKE

# from modules.PyQt.Tabs.생산지시.도면정보_form import 도면정보_Form
from modules.PyQt.component.search_for_tab_생지 import Search_for_tab_생지

from modules.PyQt.Tabs.구매.MRP.MRP_main import MRP_Main
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget
from modules.PyQt.Tabs.Base_table_for_tab import Base_Wid_Table


from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.sub_window.win_search import Win_Search
from modules.PyQt.sub_window.win_form import Win_Form
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


# 😀😀😀😀😀
from modules.PyQt.Tabs.생산지시.Datas.Datas import AppData_생산지시_관리 as AppData

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(생산지시_Base_TableModel):
	def setData(self, index, value, role):
		if role == Qt.EditRole:
			self._data[index.row()][index.column()] = value
			return True
		return False
	
	def user_defined_BackgroundRole(self, index, role):
		rowNo, colNo = index.row(), index.column()

		if '납기일' in self.header[colNo]:
			if self._check_date_different( self._original_data[rowNo][colNo] , self._data[rowNo][colNo] ):
				return QtGui.QColor("yellow" )
			else:
				return QtGui.QColor('white')
		return super().user_defined_BackgroundRole(index, role)

	def _check_date_different( self, date1, date2) -> bool:
		if isinstance(date2, QDate):
			date2 = QDate.toString(date2, Qt.DateFormat.ISODate )
		return date1 != date2


class App_TableView(생산지시_Base_TableView):
	pass

class App_Delegate(생산지시_Base_Delegate):
	pass


class Wid_Table_for_생산관리_공정_작업별(Base_Wid_Table ):
	def __init__(self, parent:QtWidgets.QMainWindow,  **kwargs ):
		super().__init__( parent, **kwargs )
		
		####  필수 : 😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		####################################

		self.첨부파일_Key = "첨부file_fks"

	def UI(self):
		self.vLayout_main = QVBoxLayout()
		self.tableView = App_TableView(self)
		self.vLayout_main.addWidget(self.tableView)		
		self.setLayout(self.vLayout_main)

	def get_api_and_model_table_generate(self) -> bool:
		if (is_api_ok := self._check_api_Result() ) :
			self.is_api_ok = is_api_ok

			if self.app_DB_data:
				self.model_data = self.gen_Model_data_from_API_data()
				self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
											header_type=self.header_type, no_Edit=self.no_Edit)
				self.table:App_TableView = self._gen_table(self.tableView )

				### setting table delegate
				self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
				self.table.setItemDelegate(self.delegate)
				
				self._hide_hidden_column()

				return True
			else:
				return False
		else: 
			return False

	
	#### app마다 update 할 것.😄
	def run(self):
		super().run()		


	def get_Selected_Datas(self) -> list[dict] :
		""" """
		result = []
		for rowNo in self.table._get_selected_rows():
			obj = {}
			history_txt = '초도확정'
			model_data:list = self.model_data[rowNo]
			for index, key in enumerate(self.header):
				value = model_data[index]
				match key:
					case 'id':
						obj[key] = value
					case '납기일_Door':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_Door 변경'
						obj[key] = value 
					case '납기일_Cage':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_Cage 변경'
						obj[key] = value
					case '납기일_JAMB':
						if not isinstance( value, str) and isinstance(value, QDate):
							value = value.toString(Qt.DateFormat.ISODate )
							history_txt += f',납기일_JAMB 변경'
						obj[key] = value
					case 'is_계획반영_htm':
						if not value and model_data[self.header.index('진행현황_htm')] == '배포':
							obj[key] = not value
					case 'is_계획반영_jamb':
						if not value and model_data[self.header.index('진행현황_jamb')] == '배포':
							obj[key] = not value

			obj['history'] = history_txt

			result.append(obj)
		return result
	

	def _get_Selected_Datas_for_Serial(self) -> list[dict] :
		""" serial 발행을 위한 selected row  datas return """
		result = []
		for rowNo in self.table._get_selected_rows():
			obj = {}
			model_data:list = self.model_data[rowNo]
			for index, key in enumerate(self.header):
				value = model_data[index]
				match key:

					case _:
						obj[key] = value
			result.append(obj)
		return result


	### 😀base app method override:
	def _get_Name(self, key:str, obj:dict) ->str:
		value = obj.get(key , None)
		match key:
			case '작지유무':
				return True if obj.get('작지유무', None) else False
			case _:
				return value
		
		db_fileds = ["제품분류", "최종납기일", "공정_완료계획일", "공정", "작업명","계획수량", 'id' ]

		if key in db_fileds:
			match key:
				case _:
					return value
		
		###😀 fk or fks fileds		
		if ( 생지_fk_obj := obj.get('생산계획관리_fk_contents').get('생산지시_fk_contents') ):
			match key:
				case '작지유무':
					return True if 생지_fk_obj.get('작업지침_fk', None) else False
				case _:
					return 생지_fk_obj.get(key)

				# case "고객사":
				# 	try:
				# 		sheets = Utils.getList_From_dictList( targetList=생지_fk_obj.get('process_fks') , keyName='수량' , delCondition={'적용':'jamb'} )
				# 		return sum([ x if isinstance(x, int) else 0 for x in sheets])
				# 	except:
				# 		pass
				# case "job_name":
				# 	try:
				# 		sheets = Utils.getList_From_dictList( targetList=생지_fk_obj.get('process_fks') , keyName='수량' , addCondition={'적용':'jamb'} )
				# 		return sum([ x if isinstance(x, int) else 0 for x in sheets])
				# 	except:
				# 		pass
				# case 'proj_No':
				# 	try:
				# 		sheets = Utils.getList_From_dictList( targetList=생지_fk_obj.get('도면정보_fks') , keyName='발주일'  )
				# 		return sheets[0]
				# 	except:
				# 		pass
				# case _:
				# 	return 생지_fk_obj.get(key)


	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def slot_search_for_tab(self, msg:dict):
		match msg.get('구분') :
			case '작업지침서':
				self.tableView_search_result = 작지_배포_Tab(self , api=self.api,appFullName='', url = msg.get('url'))
				self.tableView_search_result.signal.connect(self.slot_Work_Guide_Select)			
			case 'NCR':
				self.tableView_search_result = NCR배포_Tab(self , api=self.api,appFullName='', url = msg.get('url'))
				self.tableView_search_result.signal.connect(self.slot_NCR_Select)	

		self.vlayout_searchResult.addWidget(self.tableView_search_result)	
		self.tableView_search_result.run()
		self.tableView_search_result.show()
		

	def slot_Work_Guide_Select(self, msg:dict):
		form = 생산지시_Form (
						parent=self, 
						
						url = self.url,
						# win_title='NCR',
						# inputType=self.appData._get_form_type(),
						# title= 'NCR',
		)
		form.작지_data_Obj = msg 
		form.작지_data_Obj['생산형태'] = INFO.생산형태_Widget_items[0]
		form.is_작지_data_적용 = True
		form.run()
		form.signal.connect(self.slot_form_signal)	
	
	def slot_NCR_Select(self, msg:dict):
		form = 생산지시_Form (
						parent=self, 
						
						url = self.url,
						# win_title='NCR',
						# inputType=self.appData._get_form_type(),
						# title= 'NCR',
		)
		# form.작지_data_Obj = msg 

		# form.is_작지_data_적용 = True
		form.run()
		Object_Set_Value ( form.inputDict['생산형태'] ,  INFO.생산형태_Widget_items[1] )
		form.signal.connect(self.slot_form_signal)	


	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()
		if ( data := msg.get('data', None) ):
			row = data.get('row', -1)
		match actionName:

			case _:
				eval(f"self.{actionName}()")
	
	def handle_MRP(self, datas:list) -> None:
		mrp_main_wid = 	MRP_Main(self)
		mrp_main_wid.datas = datas
		mrp_main_wid.run()


	def handle_file첨부(self, dataObj:dict) :
		self.dialog = QDialog(self)
		vlayout = QVBoxLayout()
		self.dialog.setFixedSize (500,300)
		fileupload = File_Upload_ListWidget(
						newFiles_key=self.첨부파일_Key, 
						initialData=dataObj.get(self.첨부파일_Key, []))
		vlayout.addWidget(fileupload)
		vlayout.addStretch()
		saveBtn = QPushButton()
		saveBtn.setText('저장')
		vlayout.addWidget(saveBtn)
		self.dialog.setLayout(vlayout)
		self.dialog.show()
		saveBtn.clicked.connect(lambda:self.slot_file첨부( fileupload._getValue()))

	def slot_file첨부(self, files:dict) -> None:
		####😀 key는  API DATA에 따라서, 
		result, result_files = {}, []
		if files:
			exist_DB_ids:list = files.get('exist_DB_id')
			if len(exist_DB_ids):
				result[f'{self.첨부파일_Key}_json'] = json.dumps( exist_DB_ids )
			else:
				result[f'{self.첨부파일_Key}_삭제'] = True
				
			if ( files_fks := files.get('new_DB') ):
				#### 😀 change for api m2m field
				result_files.extend ( files_fks )

		is_ok, _ = APP.API.Send(self.url, self.selectedDataObj , result, result_files)
		if is_ok:
			self.dialog.close()
			self.run()

	
	def handle_form_view(self, row:int):
		form = 생산지시_Form (
						parent=self, 
						
						url = self.url,
						# win_title='NCR',
						# inputType=self.appData._get_form_type(),
						# title= 'NCR',
		)
		form.run()
		form.signal.connect(self.slot_form_signal)
		form.title_text='NCR'
		form.dataObj = copy.deepcopy(self.app_DB_data[row])
		form.run()
		form.viewMode()
		form.signal.connect(self.slot_form_signal)	


	def slot_form_signal(self, msg:dict):
		self.run()


