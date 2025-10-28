import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime
from itertools import chain

import pathlib
import openpyxl
import typing

from modules.user.utils_qwidget import Utils_QWidget

from modules.PyQt.Tabs.HR평가.dialog.ui.Ui_tab_HR평가_평가체계_사용자 import Ui_Tab

# import user module
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.ui.Ui_tabs import Ui_Tabs

import modules.user.utils as utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO

from modules.PyQt.User.Tb_Model import Base_TableModel, Base_TableModel_Pandas
from modules.PyQt.User.Tb_Delegate import Base_Delegate, AlignDelegate
from modules.PyQt.Tabs.Base import Base_App
import traceback
from modules.logging_config import get_plugin_logger





# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_평가체계(QDialog, Utils_QWidget):
	signal = pyqtSignal(dict)
	signal_appDataChanged = pyqtSignal()

	def __init__(self, parent=None, url:str='', **kwargs):
		super().__init__(parent )
		self.isAppDataChanged = False
		self.app_Dict : dict
		# self.url_APP설정 = url
		# self.url = url if len(url) > 5 else INFO.URL_User_ALL
		self.url = url
		for key, value in kwargs.items():			
			setattr(self, key, value )

		self.app_Dict : dict
		self._get_DB_Field(url=INFO.URL_DB_Field_User_View )

		self.ui = Ui_Tab()
		self.ui.setupUi(self)

		self.triggerConnect()

		self._update_table( self.api_datas)

		self.show()

	def _update_table(self, api_datas:list[dict]=[] ):
		def add_사용자_User_table(app_Dict:dict, user_datas:list[dict]):
			api_datas:list[dict] = []
			for 차수 in range( app_Dict.get('총평가차수') +1):
				for user in user_datas:
					obj = {}					
					obj['차수'] = 차수
					obj['피평가자'] = user.get('id')
					obj['평가자'] = user.get('id') if 차수 == 0 else -1
					api_datas.append(obj)
		
			return api_datas
					
		if len(api_datas) == 0 :
			info = INFO()			
			api_datas = info._get_all_user()

		self.api_datas = self._conversion_api_datas(api_datas=api_datas)

		
		TABLE_HEADER = ['피평가자_ID','피평가자_성명','피평가자_조직1','피평가자_조직2','피평가자_조직3','is_참여'] \
					+ list( chain.from_iterable( ( f"{차수}_id" , f"{차수}_평가자_ID", f"{차수}_평가자_성명" ) for 차수 in range( self.app_Dict.get('총평가차수') +1)  ))      # [ f"{차수}_id" for 차수 in range( self.app_Dict.get('총평가차수') +1)]
		fields_model_차수 = { 차수:'Ingeger' for 차수 in range( self.app_Dict.get('총평가차수') +1)}
		fields_model = fields_model_차수
		fields_model.update ( {'is_참여':'BooleanField'} )

		self.db_fields = {
			'fields_model' : fields_model ,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				#############
				'table_header' : TABLE_HEADER,
				'no_Edit_cols' :['id', '피평가자_ID','피평가자_성명','피평가자_조직1','피평가자_조직2','피평가자_조직3', ] + [ head for head in TABLE_HEADER  if  '0' in head or 'id' in head  or '성명' in head ] , 
					#  + list( chain.from_iterable( ( head ) for head in TABLE_HEADER  if  '0' in head or 'id' in head  or '성명' in head ) ),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
			},
		}

		self.ui.Wid_Table._update_data(
			api_data = self.api_datas, 			
			url = self.url,
			# url_APP설정 = self.url_APP설정,
			**self.db_fields,
			app_Dict = self.app_Dict,
			# table_header = 
		)

	def _conversion_api_datas(self, api_datas:list[dict]=[] ) -> list[dict]:
		""" table 표시를 위한 data conversion \n
			api_datas =  [{'0': 1, '1': -1, '2': -1, '0_id': 39, '1_id': 40, '2_id': 41 },...\n

		"""
		info = INFO()
		for obj in api_datas:
			#😀 0차는 본인평가로, 0차 id 는 피평가자
			피평가자_ID:int = obj.get('0')
			user_info = info._get_user_info( pk= 피평가자_ID )

			obj['피평가자_ID'] = 피평가자_ID
			obj['피평가자_성명'] = user_info.get('user_성명')
			obj['피평가자_조직1'] = user_info.get('기본조직1')
			obj['피평가자_조직2'] = user_info.get('기본조직2')
			obj['피평가자_조직3'] = user_info.get('기본조직3')
			# obj['is_참여'] = True			
		return api_datas

	def triggerConnect(self):
		self.ui.Wid_Search_for.signal_search.connect(self.slot_search_for)
		### table에서 data가 바뀌면 signaling
		self.ui.Wid_Table.signal_appData_Changed.connect(self.slot_appData_changed )

	def run(self):
		return 


	@pyqtSlot(str)
	def slot_search_for(self, param:str) :
		"""
		결론적으로 main 함수임.
		Wid_Search_for에서 query param를 받아서, api get list 후,
		table에 _update함.	
		"""

		if param:
			self.ui.Wid_Table._search_in_model_data(param)



		# if param :
		# 	url = self.url + '?' + param + '&page_size=0'
		# else:
		# 	url = self.url+ '?' + 'page_size=0'
		# is_ok, api_datas = APP.API.getlist ( url=url )

		# if is_ok:

		# 	self._update_table(api_datas=api_datas)




	@pyqtSlot(dict)
	def slot_appData_changed(self, msg:dict) -> None:
		self.isAppDataChanged = True
		

	def closeEvent(self, a0):
		if self.isAppDataChanged:
			self.signal_appDataChanged.emit()
		return super().closeEvent(a0)

	

	
	


# def main():    

#     app=QApplication(sys.argv)
#     window= Win_app사용자관리()
#     window.show()
#     app.exec_()


# if __name__ == "__main__":
#     sys.exit( main())