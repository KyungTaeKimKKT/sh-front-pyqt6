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

from modules.PyQt.Tabs.생산관리.ui.Ui_생산관리_공정_작업별__for_Tab import Ui_Form
from modules.PyQt.Tabs.Base import Base_App
from modules.PyQt.Tabs.생산관리.datas.AppData_생산관리_확정branch import AppData_생산관리_확정branch as AppData

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 공정별_작업별_관리__for_Tab(Base_App, Ui_Form):
	def __init__(self, parent:QtWidgets.QMainWindow,   url:str ):
		super().__init__( parent,  url  )
		self.url = url
		# ####  😀 Data.py에서 class attr,value 읽어와 self attribut setting
		self.appData = AppData()
		self._init_Attributes_from_DataModule()
		# ####################################

		# self.첨부파일_Key = "첨부file_fks"
	
	def UI_Wid_run(self):
		""" sub Wid setting 수정 및 run"""
		# 생지에서 사용하는 frame hide()
		# self.frame.hide()

		# ### parent.url로 초기화 되어 있으나, overwrite
		self.Wid_Search_for.url =  self.url
		self.Wid_Search_for.run()		

		self.Wid_Table.url = self.url
		self.Wid_Table.appData = self.appData
		self.Wid_Table._init_Attributes_from_DataModule()
		self.Wid_Table.run()

	def 초기setting(self):
		self.PB_apply_plan.setEnabled ( hasattr( self.Wid_Table, 'table') )

	def triggerConnect(self):
		self.PB_apply_plan.clicked.connect ( self.on_PB_apply_plan_clicked)
		if hasattr(self, 'PB_QR_Gen' ) :self.PB_QR_Gen.clicked.connect ( self.on_PB_QR_Gen_clicked )
		if hasattr(self, 'PB_QR_Scan') :self.PB_QR_Scan.clicked.connect ( self.on_PB_QR_Scan_clicked)

		self.Wid_Search_for.signal_search.connect( self.slot_wid_search)


	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		self.setupUi(self)
		self.UI_Wid_run()

		self.triggerConnect()

		self.초기setting()
	
	@pyqtSlot()
	def on_PB_apply_plan_clicked(self):
		results = self.Wid_Table.get_Selected_Datas()
		if results: 
			replay = QMessageBox.question( self, '생산계획 반영', f"총 {len(results)} 건을 확정하시겠습니까?\n", 
						QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
			if replay == QMessageBox.StandardButton.Yes:
				for result in results:	
					sendData = self._update_By_계획변경_flag( copy.deepcopy(result) )
					is_ok, _json = APP.API.Send(
						url=self.url, dataObj=result, sendData=sendData)					
					if is_ok:
						history_obj = {'변경자':INFO.USERID, '변경내용':sendData.pop('history', '')}
						history_obj['생산계획관리_fk'] = _json.get('id')
						is_ok, _json = APP.API.Send( 
							url = INFO.URL_생산계획_History, dataObj={}, sendData=history_obj)
						if is_ok:
							self.run()
			else:
				logger.error(f"계획변경 취소")


	@pyqtSlot()
	def on_PB_QR_Gen_clicked(self):
		from modules.PyQt.dialog.wid_qr_write import QDialog_QR_Writing
		wid =  QDialog_QR_Writing(self)	

		selected_row_for_serial = self.Wid_Table._get_Selected_Datas_for_Serial()
		for row in selected_row_for_serial:
			wid.receivedData = row
			for cnt in range( row.get('계획수량')):
				wid.receivedData['수량'] = f"{cnt+1} / {row.get('계획수량')}"
				wid.receivedData['수량_no'] = cnt+1
				wid.run()

		# wid.dataObj = {
		# 	"고객사" : "현대",
		# 	"job_name" : "SM스튜디오 단지 신축공사",
		# 	"생산형태" : "정규양산",
		# 	"공정" : "HI",
		# 	"작업명" : "Maskant(Lozenge02 패턴 / LH 2안 잉크)",
		# 	"수량" : " 1/ 10 ",
		# }	
			# wid.serialCode = 'HI240906HY00001'
			# wid.viewMode()
			# wid.show()


	@pyqtSlot()
	def on_PB_QR_Scan_clicked(self):		
		from modules.PyQt.dialog.wid_qr_read import QDialog_QR_Reading
		wid = QDialog_QR_Reading(self)
		wid.show()

	def slot_wid_search(self, search_result:dict, app_DB_data:list) -> None:		
		self.wid_pagination._setValue(search_result)		
		self.Wid_Table.run_by_parent(app_DB_data)


	def _update_By_계획변경_flag(self, target:dict) -> dict:
		""" 계획변경  attribute 가 있으면 해당 timestamp에 now 보냄"""
		if target.get( 'is_계획반영_htm', None) :
			target['계획반영_htm_timestamp'] = datetime.now()
		if target.get('is_계획반영_jamb', None) :
			target['계획반영_jamb_timestamp'] = datetime.now()
		return target