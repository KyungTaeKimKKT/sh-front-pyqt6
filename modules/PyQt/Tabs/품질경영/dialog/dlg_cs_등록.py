from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.Tabs.품질경영.dialog.ui.Ui_dlg_cs등록form import Ui_Dialog
from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit
from modules.PyQt.User.object_value import Object_Set_Value, Object_ReadOnly

from copy import deepcopy
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils
from datetime import datetime
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

class Dlg_CS_등록(QDialog):
	signal_ok = pyqtSignal(dict)

	def __init__(self, parent=None, url:str='', **kwargs):
		super().__init__(parent)
		self.url = url
		self.dataObj = { 'id' : -1 }
		self.is_Edit = True
		self.Elevator사 = '현대'
		self.부적합유형 = '스크래치'
		self.Elevator사list :list[str] = kwargs.get('Elevator사list', [])
		self.부적합유형list :list[str] = kwargs.get('부적합유형list', [])

		for key, value in kwargs.items():
			setattr(self, key, value)

		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self._init_inputDict()	


		self.ui.label_title.setText( kwargs.get('title', 'CS 등록') )
		self.setWindowTitle( kwargs.get('title', 'CS 등록') )

		self._update_kwargs(**kwargs)
		self.triggerConnect()
		self.show()
		
	def _init_inputDict(self):
		self.inputDict = {
			'Elevator사' : self.ui.label_El_Company,
			# 'Elevator사' : self.ui.comboBox_El_company,
			# 'Elevator사_기타' : self.ui.lineEdit_El_Comapany,
			'현장명' : self.ui.lineEdit_Hyunjang,
			'현장주소' : self.ui.lineEdit_Address,
			'el수량' : self.ui.spinBox_el_qty,
			'운행층수' : self.ui.spinBox_floor_qty,
			'고객명' : self.ui.lineEdit_Gogaek,
			'부적합유형' : self.ui.label_NCR,
			'불만요청사항' : self.ui.plainTextEdit_claim,
			'고객연락처' : self.ui.lineEdit_contact,
			'차수' : self.ui.spinBox_chasu,
			'진행현황' : self.ui.label_Dungrok_result,
			'등록자' : self.ui.label_Dungrok,
			'등록일' : self.ui.dateTimeEdit_dungrok,
			'완료일' : self.ui.dateTimeEdit_close,
			'claim_files_ids' : self.ui.wid_fileupload, 	# 파일 업로드 위젯
		}
		self.hidden_wid = [
			self.ui.label_status, self.ui.label_status_result,
			self.ui.label_Dungrok,	self.ui.label_Dungrok_result,
			self.ui.label_date_dunrok, self.ui.label_date_close,
			self.ui.dateTimeEdit_dungrok, self.ui.dateTimeEdit_close,
		]

	def _hide_hidden_wid(self):
		for wid in self.hidden_wid:
			wid.hide()

	def _show_hidden_wid(self):
		for wid in self.hidden_wid:
			wid.show()

	def _set_data(self):
		""" edit 일때 사용 """
		self._hide_hidden_wid()
		for key, wid in self.inputDict.items():
			if key in ['Elevator사', '부적합유형']:
				_txt = self.dataObj.get(key, '')
				self.inputDict[key].setText(_txt if _txt and _txt != 'None' else getattr(self, key))				
				continue

			if key == 'claim_files_ids':
				if ( claim_files_ids := self.dataObj.get(key,[]) ):
					param = f"ids={','.join(map(str, claim_files_ids))}"
					is_ok, _json = APP.API.getlist(INFO.URL_CS_CLAIM_FILE + f"?{param}&page_size=0" )
					if is_ok:
						self.claim_files = _json
						self.ui.wid_fileupload.update_kwargs( files=_json )
					else:
						Utils.generate_QMsg_critical(self)
				continue

			Object_Set_Value(wid, self.dataObj.get(key))

	def _set_readonly(self):
		""" view 일때 사용 """
		self._show_hidden_wid()
		for key, wid in self.inputDict.items():
			Object_ReadOnly(wid, self.dataObj.get(key))

	def _get_data(self):
		data = {
			'Elevator사' :self.ui.label_El_Company.text().strip(),
			'현장명' : self.ui.lineEdit_Hyunjang.text(),
			'현장주소' : self.ui.lineEdit_Address.text(),
			'el수량' : self.ui.spinBox_el_qty.value(),
			'운행층수' : self.ui.spinBox_floor_qty.value(),
			'고객명' : self.ui.lineEdit_Gogaek.text(),
			'부적합유형' : self.ui.label_NCR.text().strip(),
			'불만요청사항' : self.ui.plainTextEdit_claim.toPlainText(),
			'고객연락처' : self.ui.lineEdit_contact.text(),
			'차수' : self.ui.spinBox_chasu.value(),
			'claim_files' : self.ui.wid_fileupload.getValue(),
			
		}
		return data 
	
	def _update_kwargs(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)
		if self.is_Edit:
			self._set_data()			
		else:
			self._set_readonly()

	def triggerConnect(self):
		self.ui.PB_Search_Hyunjang.clicked.connect(self.slot_btn_search)
		self.ui.buttonBox.accepted.connect(self.slot_btn_ok)
		self.ui.buttonBox.rejected.connect(self.slot_btn_cancel)

		self.ui.PB_El_Company.clicked.connect(self.slot_select_Elevator_Company)
		self.ui.PB_NCR.clicked.connect(self.slot_select_NCR)

	@pyqtSlot()
	def slot_select_NCR(self):
		""" PB_NCR 클릭시 호출 , dialog 호출 후 선택된 값을 _update_NCR 호출 """
		_isok, _list = APP.API.getlist(INFO.URL_CS_CLAIM_GET_부적합유형+'?page_size=0')
		if _isok:
			self.부적합유형list = _list
			dlg = Dialog_list_edit(self, title='부적합유형 선택', _list=self.부적합유형list, is_sorting=False)
			dlg.signal_ok.connect( self._update_NCR  )
		else:
			Utils.generate_QMsg_critical(self)
		
	@pyqtSlot(str)
	def _update_NCR(self, NCR:str):
		self.ui.label_NCR.setText( NCR )
		self.부적합유형 = NCR
		
	@pyqtSlot()
	def slot_select_Elevator_Company(self):
		""" PB_El_Company 클릭시 호출 , dialog 호출 후 선택된 값을 _update_El_company 호출 """
		_isok, _list = APP.API.getlist(INFO.URL_CS_CLAIM_GET_ELEVATOR사+'?page_size=0')
		if _isok:
			self.Elevator사list = _list
			dlg = Dialog_list_edit(self, title='Elevator사 선택', _list=self.Elevator사list, is_sorting=False)
			dlg.signal_ok.connect( self._update_El_company  )
		else:
			Utils.generate_QMsg_critical(self)

	@pyqtSlot(str)
	def _update_El_company(self, elevator_company:str):
		self.ui.label_El_Company.setText( elevator_company )
		self.Elevator사 = elevator_company

	@pyqtSlot()
	def slot_btn_ok(self):
		sendData = deepcopy(self.dataObj)
		sendData.pop('id')
		sendData.update( self._get_data() )
		sendData.update ( {'등록일':datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '진행현황':'작성'} )
		if ( claim_files := sendData.pop( 'claim_files', []) ):
			ic( claim_files )
			claim_files_existing_file_ids = []
			sendFi = []
			# 'type'이 'local'인 경우에만 API로 보낼 수 있도록 필터링
			for file in claim_files:
				if file['type'] == 'local':
					sendFi.append(('claim_files', (file['file'], open(file['file'], 'rb'))))
				elif file['type'] == 'server':
					claim_files_existing_file_ids.append( file['id'] )
			sendData['claim_files_ids'] = claim_files_existing_file_ids if claim_files_existing_file_ids else [-1]
			ic ( claim_files_existing_file_ids )
		else:
			sendFi = []
			sendData['claim_files_ids'] = [-1]

		_isOk, _json = APP.API.Send(self.url, self.dataObj, sendData, sendFi)
		if _isOk:
			self.signal_ok.emit(_json)
			Utils.generate_QMsg_Information(self, title='등록 완료', text='등록 완료', autoClose=1000 )
			self.accept()
		else:
			Utils.generate_QMsg_critical(self)		

	@pyqtSlot()
	def slot_btn_search(self):
		obj = self.dataObj
		현장명_txt = self.ui.lineEdit_Hyunjang.text()

		dlg = QDialog(self)
		hLayout = QVBoxLayout()
		from modules.PyQt.Tabs.Elevator_Info.Elevator_Info_한국정보 import 한국정보__for_Tab
	
		api_uri, api_url, db_field_url = INFO._get_URL_EL_INFO_한국정보(INFO)
		db_field_url = 'db-field-Elevator_Summary_WO설치일_선택menu_enable_View/'
		wid = 한국정보__for_Tab(
				dlg, 
				'', api_uri=api_uri, api_url=api_url, db_field_url=db_field_url, is_Auto_조회_Start=True, 
				param=f"search={현장명_txt}&page_size=25",
				search_str = 현장명_txt, 
				)
		hLayout.addWidget(wid)
		dlg.setLayout(hLayout)
		dlg.setWindowTitle( 'MOD 현장명 검색')
		dlg.setMinimumSize( 600, 800)
		dlg.show()
		### SEARCH CONDITION SET AND SEARCH ( BUTTON CLICK )
		wid._set_search_condition(현장명_txt)

		wid.signal_select_row.connect (lambda EL_INFO: self.slot_select_row(dlg, self.dataObj, EL_INFO))
	
	@pyqtSlot(QWidget, dict, dict)
	def slot_select_row(self, wid:QWidget, apiDict:dict, EL_INFO:dict) :
		""" apiDict : Elevator 한국정보 Model data로 \n
			apiDict.get('id') 로 fk 사용
		"""
		self.dataObj.update ( {'el_info_fk' : EL_INFO.get('id')} )


		#### el info render
		if EL_INFO:
			ic( EL_INFO)
			self.ui.lineEdit_Hyunjang.setText( EL_INFO.get('건물명') )
			self.el_info_fk = EL_INFO.get('id')
			self.ui.spinBox_el_qty.setValue( EL_INFO.get('수량') )
			self.ui.spinBox_floor_qty.setValue ( EL_INFO.get('운행층수')  )
			self.ui.lineEdit_Address.setText( EL_INFO.get('건물주소_찾기용') )
			# self.ui.label_Info_addr.setText ( str(EL_INFO.get('건물주소') ) )

		wid.close()

	@pyqtSlot()
	def slot_btn_cancel(self):
		self.reject()


