from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import datetime
from itertools import chain

from modules.PyQt.Tabs.샘플관리.dialog.ui.Ui_form_샘플제작의뢰서 import Ui_Form
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from modules.PyQt.User.object_value import Object_Set_Value, Object_Diable_Edit, Object_ReadOnly, Object_Get_Value

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_샘플의뢰_Form(QDialog,   Qwidget_Utils):
	""" kwargs \n
		url = str,\n
		dataObj = {}
	"""
	signal_data = pyqtSignal(list)
	signal_refresh = pyqtSignal()
	

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.app_Dict :dict
		self.DB_All :list[dict]
		self.DB_Selected : list[int] ### model m2m item_fks 임
		self.inputDict: dict[str:QWidget] = []
		self.dataObj:dict = { 'id': -1 } ####
		self.is_Edit = True
		for k, v in kwargs.items():
			setattr(self, k, v)

		self.ui =  Ui_Form()
		self.ui.setupUi(self)
		# self.ui.PB_Save.setEnabled(True)
		self._init_Input_Dict()
		self.__init__default_setting()

		self._render_from_DataObj()

		self.triggerConnect()
		
		self.show()


	def _init_Input_Dict(self):
		ui = self.ui
		self.inputDict = {
			'요청일' 	: ui.dateEdit_Jejak,
			'요청자' 	: ui.lineEdit_Name,
			'요청건명' 	: ui.lineEdit_Title,
			'고객사' 	: ui.lineEdit_El,
			'용도_현장명' : ui.lineEdit_Apt,
			'납기일' 	: ui.dateEdit_Napum,
			'납품차수' : ui.spinBox_Chasu,

			'시편' 	: ui.spinBox_Sipun,
			'NCT'	: ui.spinBox_Nct,
			'절곡' 	: ui.spinBox_Julgok,
			'조립' 	: ui.spinBox_Jorip,
			'설치'    : ui.spinBox_Sulchi,
			'불요' 	: ui.checkBox_Bulyo,
			'Book' 	: ui.spinBox_Book,
			'Board' : ui.spinBox_Board,

			'비고' 	: ui.plainTextEdit_Bigo,

			'현장명' : ui.lineEdit_W_hyunjang,
			'EL사' 	: ui.combo_edit_Gogak,
			'구분'	: ui.combo_edit_Gubun,
			'생산적용시점' 	: ui.dateEdit_W_date_production,

		}


	def __init__default_setting(self):      
		if self.is_Edit :
			return
		
		self.ui.PB_save.hide()
		self.ui.PB_cancel.setText('확인')


	def _render_from_DataObj(self):
		ic()
		keysList = list (self.inputDict.keys() )
		if hasattr(self, 'dataObj') :
			for key, value in self.dataObj.items():
				if key in keysList:
					Object_Set_Value( self.inputDict[key], value )
					if not self.is_Edit:
						Object_ReadOnly( self.inputDict[key], value  )

			process_fks = self.dataObj.get('process_fks', []) 
			ic ( process_fks, self.ui.wid_table)

			if len(process_fks) > 0:
				param = f"?ids={(',').join( [str(id) for id in process_fks] )}&page_size=0"
				is_ok, _json = APP.API.getlist(INFO.URL_샘플관리_PROCESS_DB + param )
				ic (_json )
				if is_ok:
					self.table_api_datas = _json
				else:
					Utils.generate_QMsg_critical(self)
			else:
				self.table_api_datas = []

			_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_샘플관리_PROCESS_DB)

			if _isOk:
				if not self.is_Edit:
					db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
				self.ui.wid_table._update_data(
					api_data=self.table_api_datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
					url = INFO.URL_샘플관리_PROCESS_DB,
					**db_fields,
				)		
			else:
				Utils.generate_QMsg_critical(self)


	def triggerConnect(self):
		self.ui.PB_save.clicked.connect( self.slot_PB_Save )
		self.ui.PB_cancel.clicked.connect( self.close )
		
		for key, widget in self.inputDict.items():
			widget : QWidget
			widget.focusInEvent = lambda e, w = widget: self.on_focus(e, w)
			widget.focusOutEvent = lambda e, w = widget: self.on_focus_lost(e, w)
		# self.ui.PB_Save.clicked.connect ( self.slot_PB_Save)

	@pyqtSlot()
	def slot_PB_Save(self):
		sendDatas =  self.ui.wid_table._get_Model_data()
		threadingTargets= [{ 'url': INFO.URL_샘플관리_PROCESS_DB,'dataObj': obj, 'sendData':obj } for obj in sendDatas ]
		futures = Utils._concurrent_Job( APP.API.Send,  threadingTargets)
		_isOk_result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
		if all(_isOk_result):
			IDs = [ future.result()[1].get('id') for index,future in futures.items() ]
			ic ( IDs )
			sendData = { key: Object_Get_Value(wid).get()   for key, wid in self.inputDict.items() }
			sendData.update ({'process_fks': IDs })
			ic ( sendData  )
			_isOk, _json = APP.API.Send(self.url, self.dataObj, sendData )
			if _isOk:
				self.signal_refresh.emit()
				self.close()
			else:
				Utils.generate_QMsg_critical(self)

		else:
			Utils.generate_QMsg_critical(self)




	def on_focus(self, event:QEvent, widget:QWidget):
		widget.setStyleSheet("background-color: yellow;")
		font = widget.font()
		font.setBold(True)
		widget.setFont(font)
		
	def on_focus_lost(self, event:QEvent, widget:QWidget):
		widget.setStyleSheet("")
		font = widget.font()
		font.setBold(False)
		widget.setFont(font)

	@pyqtSlot()
	def slot_PB_Select(self):
		sel_items = self.ui.listWidget_before.selectedItems() 
		if not sel_items : return


		self.ui.listWidget_after.addItems ( [qItem.text()  for qItem in sel_items] )
		for item in sel_items:
			self.ui.listWidget_before.takeItem( self.ui.listWidget_before.row(item))

	@pyqtSlot()
	def slot_PB_Unselect(self):
		sel_items = self.ui.listWidget_after.selectedItems() 
		if not sel_items : return

		# for qItem in sel_items:
		#     self.ui.listWidget_before.addItem(qItem)
		self.ui.listWidget_before.addItems ( [qItem.text()  for qItem in sel_items] )
		for item in sel_items:
			self.ui.listWidget_after.takeItem( self.ui.listWidget_after.row(item))


		# for obj in self.DB_All:



	