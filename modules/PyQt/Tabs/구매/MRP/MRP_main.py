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
import pandas as pd

# import user_defined compoent

from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit, 고객사_Widget, 구분_Widget,생산형태_Widget

from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly


from modules.PyQt.Tabs.구매.MRP.종합_Wid import 종합_Wid
from modules.PyQt.Tabs.구매.MRP.개별_Wid import 개별_Wid


from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget

import modules.user.utils as Utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

class MRP_Main( QMainWindow , Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', datas:list=[], skip:list=['id'],
				 ):
		super().__init__(parent)
		self.no_Edit =[]
		self.validator_list = []
		self.appData = parent.appData
		self.현장명_fks = []	
		self.datas = datas
		self.SPG_dict = {}
		self.skip = skip
		self.title = title
		self.inputType = inputType
		self.win_title = win_title
		self.wid_tabs = {}
		
		self.url = url
		self.작지_data_Obj = {}
		self.is_작지_data_적용 = False
		self.tabName_summary = "tab_Summary"
		self.api_to_sendDatas = {}
		self.api_to_sendDatas_files = []

		self.Main_conversion_Dict = {
			'제목' : 'job_name',
			'proj_No' : 'proj_No',
			'수량' : '총수량',
			'구분' : '구분',
			'고객사' : '고객사',
			'생산형태' : '생산형태',
		}


	def UI(self):
		self.setObjectName("MRP")
		self.resize(1740, 1215)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(1)
		sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.setSizePolicy(sizePolicy)
		self.centralwidget = QtWidgets.QWidget(self)
		self.centralwidget.setObjectName("centralwidget")
		self.vLayout_Main = QVBoxLayout(self.centralwidget)
		self.centralwidget.setLayout(self.vLayout_Main)

		# self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.centralwidget)
		# self.horizontalLayout_7.setObjectName("horizontalLayout_7")
		self.tabWidget = QtWidgets.QTabWidget(self)
		self.tabWidget.setObjectName("tabWidget")
		self.tab_Summary = 종합_Wid()
		self.tab_Summary.setObjectName(self.tabName_summary )
		self.wid_tabs[self.tabName_summary] = self.tab_Summary
		
		self.tabWidget.addTab(self.tab_Summary,'Summary')

		self.vLayout_Main.addWidget(self.tabWidget)

		# self.horizontalLayout_7.addWidget(self.tabWidget)

		self.setCentralWidget(self.centralwidget)
		
		self.menubar = QtWidgets.QMenuBar(self)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 1740, 28))
		self.menubar.setObjectName("menubar")
		self.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(self)
		self.statusbar.setObjectName("statusbar")
		self.setStatusBar(self.statusbar)

		self.retranslateUi()
		self.tabWidget.setCurrentIndex(0)

	def retranslateUi(self):
		self.setWindowTitle("MRP Main")

		# self.PB_save.setText("저장")
		# self.PB_cancel.setText("취소")
		# self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "HTM 생산지시서")



	def _init_Input_Dict(self):
		""" UI 완료 후 초기화 진행 """
		self.inputDict = {
			### HTM
			'job_name' : self.lineEdit_Job_name,
			'proj_No' : self.lineEdit_Proj_No,
			'총수량' : self.spinBox_chongsurang,
			'지시수량' : self.spinBox_Daesu,
			'차수' : self.spinBox_Chasu,
			'작성자' : self.lineEdit_Name,
			'생산지시일' : self.dateEdit_Produce,
			'소재발주일' : self.dateEdit_Order,
			'구분' : self.comboBox_line_Gubun,
			'고객사' : self.comboBox_Line_Gogaek,
			'생산형태' : self.comboBox_Prod_Div,
			### SPG
			# '현장명': self.lineEdit_SPG_hyunjang,
			# '공사번호' : self.lineEdit_SPG_proj_No,
			# 'SPG_호기' : self.plainTextEdit_Hogi,
			# 'SPG_도면번호'    : self.lineEdit_Domyun,
			# 'SPG_비고' : self.plainTextEdit_SPG_Bigo,
		}
		self.m2m_field = {
			'도면정보_fks' : self.tableView_Domyun,
			'process_fks' : self.tableView_HTM,
		}
		self.inputType = self.inputDict

	def user_defined_ui_setting(self):
		for (key, input) in self.inputDict.items():
			if isinstance(input, QDateEdit ):
				if not self.dataObj : input.setDate(QDate.currentDate() )
			if isinstance(input, QSpinBox ):
				if not self.dataObj : input.setRange(1, 100000)
			if isinstance(input , Combo_LineEdit) :
				input._render()
				input._setDefault()
				match key :
					case '고객사' : input._setMaximumWidth(120)
					case '생산형태' : input._setMaximumWidth(240)
					case _:  input._setMaximumWidth(60)

			if key in ['작성자', '작성일자']:
				if isinstance( input, QLineEdit ):
					input.setText(INFO.USERNAME)
				input.setReadOnly(True)
			if key in ['생산지시일','소재발주일']:
				if isinstance ( input, QDateEdit):
					input.setMinimumDate (QDate.currentDate() )

	def render_작지_data_Obj(self):

		for 작지_key, 생지_key in self.Main_conversion_Dict.items():
			try:
				Object_Set_Value( self.inputDict[생지_key], self.작지_data_Obj.get(작지_key))
			except:


	def gen_ProcessData_from_작지_data_Obj(self):
		wall_conversion_dict = {
			'Front_Front Panel' : 'FRONT',
			'Side_Side Panel' : 'SIDE/SIDE',
			'Side_Center Panel' : 'SIDE CENTER',
			'Rear_Side Panel' : 'REAR SIDE',
			'Rear_Center Panel' : 'REAR CENTER',	
		}
		for 작지obj in self.작지_data_Obj.get('process_fks'):			
			key1 = str(작지obj.get('적용부품'))
			key2 = str(작지obj.get('적용패널'))
			if ( findString := f"{key1}_{key2}" )in list(wall_conversion_dict.keys()):
				for dataObj in self.tableView_HTM.app_DB_data:
					if wall_conversion_dict.get(findString) in dataObj['비고'] :
						self._change_ProcessData( dataObj, 작지obj)

			else :
				match key1:
					case 'Car Door':
						for dataObj in self.tableView_HTM.app_DB_data:
							if key1.upper() in dataObj['적용'] :
								self._change_ProcessData( dataObj, 작지obj)
					case 'Hatch Door'| 'Jamb':
						for dataObj in self.tableView_HTM.app_DB_data:
							key2 = '기준층' if '기준층' in key2 else '기타층'
							if key1.upper() in dataObj['적용']  and key2 in dataObj['적용']:
								self._change_ProcessData( dataObj, 작지obj)
					
			
			if '상판동일' in str(작지obj.get('비고')).replace(' ', ''):
				self._change_ProcessData_상판(작지obj)

		self.tableView_HTM.run()

	def _change_ProcessData(self, dataObj:dict, 작지obj:dict ) -> None:
		for key in ['대표Process', '상세Process', '소재']:
			dataObj[key] = 작지obj.get('Material') if key == '소재' else 작지obj.get(key)

	def _change_ProcessData_상판(self, 작지obj:dict ) -> None:
		for dataObj in self.tableView_HTM.app_DB_data:
			if '상판' in dataObj['적용']:
				for key in ['대표Process', '상세Process', '소재']:
					dataObj[key] = 작지obj.get('Material') if key == '소재' else 작지obj.get(key)

	def run(self):


		self.UI()  
		self.retranslateUi()      
		
		if self.datas:
			self.calucrate_pivot()
		self.tab_Summary.run()
		# self._init_Input_Dict()
		# self.user_defined_ui_setting()
		##😀
		# self.tableView_Domyun.run()
		# self.tableView_HTM.run()
		###
		self.show()
		# self.TriggerConnect()

		# if self.is_작지_data_적용 :
		# 	self.render_작지_data_Obj()
		# 	self.gen_ProcessData_from_작지_data_Obj()
		
	def calucrate_pivot(self) :

		for dataObj in self.datas:
			df = pd.DataFrame(dataObj.get('process_fks') )
			df['확정'] = df['확정'].astype(str)
			확정_df = df[ (df['확정'] == 'True') & (df['수량'] >0) ]
			pivot_df = 확정_df.pivot_table(
							 index=['소재','치수','적용'],
							 columns=[],
							 values='수량',
							 aggfunc='sum'
							 )
			resultDF = pivot_df.reset_index()
			개별wid_table_datas:list = resultDF.to_dict(orient='records')
			tabName =  dataObj.get('job_name')
			wid = self.gen_개별_wid( dataObj, 개별wid_table_datas, dataObj.get('job_name', '개별'))
			self.wid_tabs[tabName] = wid
			self.tabWidget.setCurrentWidget(wid)
		self.tabWidget.setCurrentWidget(self.wid_tabs[self.tabName_summary ])
	
	def gen_개별_wid(self, dataObj:dict, table_datas:list, title:str) ->QWidget:
		wid = 개별_Wid()
		self.tabWidget.addTab(wid, title)
		wid.dataObj = dataObj
		wid.tableView_Wid_appDBdatas = table_datas
		wid.run()
		return wid


	def TriggerConnect(self):
		self.PB_save.clicked.connect(self.func_save)
		# self.PB_save_SPG.clicked.connect(self.func_save)
		self.PB_cancel.clicked.connect(self.close)
		# self.PB_cancel_3.clicked.connect(self.close)
