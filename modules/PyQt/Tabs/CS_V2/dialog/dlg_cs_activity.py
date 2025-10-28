from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.Tabs.품질경영.dialog.ui.Ui_dlg_cs활동form import Ui_Dialog
from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit
from modules.PyQt.User.object_value import Object_Set_Value, Object_ReadOnly

from copy import deepcopy
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils
from datetime import datetime, timedelta

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

class Dlg_CS_Activity(QDialog):
	signal_ok = pyqtSignal(dict)

	def __init__(self, parent=None, url:str='', **kwargs):
		super().__init__(parent)
		self.url = url
		self.dataObj = { 'id' : -1 }
		self.is_Edit = True

		for key, value in kwargs.items():
			setattr(self, key, value)

		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self._init_inputDict()	


		self.ui.label_title.setText( kwargs.get('title', 'CS Activity 등록') )
		self.setWindowTitle( kwargs.get('title', 'CS Activity 등록') )

		self._update_kwargs(**kwargs)
		self.triggerConnect()
		self.show()
		
	def _init_inputDict(self):
		self.inputDict = {
			'예정_시작일' : self.ui.dateEdit_start,
			'예정_완료일' : self.ui.dateEdit_end,
			'활동현황' : self.ui.plainTextEdit_activity,
			'activity_files_ids' : self.ui.wid_activity_files_upload,

		}

	def _set_data(self):
		""" edit 일때 사용 """

		for key, wid in self.inputDict.items():
			if key == 'activity_files_ids':
				if ( activity_files_ids := self.dataObj.get(key,[]) ):
					param = f"ids={','.join(map(str, activity_files_ids))}"
					is_ok, _json = APP.API.getlist(INFO.URL_CS_ACTIVITY_FILE + f"?{param}&page_size=0" )
					if is_ok:
						self.activity_files = _json
						self.ui.wid_activity_files_upload.update_kwargs( files=_json )
					else:
						Utils.generate_QMsg_critical(self)
				continue
			if key == '예정_시작일':
				if self.dataObj.get(key, None):
					self.ui.dateEdit_start.setDate( datetime.strptime(self.dataObj.get(key), '%Y-%m-%d') )
				else:
					self.ui.dateEdit_start.setDate( datetime.now() )
			elif key == '예정_완료일':
				if self.dataObj.get(key, None):
					self.ui.dateEdit_end.setDate( datetime.strptime(self.dataObj.get(key), '%Y-%m-%d') )
				else:
					self.ui.dateEdit_end.setDate( datetime.now()+timedelta(days=3) )
			else:
				Object_Set_Value(wid, self.dataObj.get(key))

	def _set_readonly(self):
		""" view 일때 사용 """

		for key, wid in self.inputDict.items():
			Object_ReadOnly(wid, self.dataObj.get(key))

	def _get_data(self):
		data = {
			'활동현황' : self.ui.plainTextEdit_activity.toPlainText(),
			'activity_files' :	 self.ui.wid_activity_files_upload.getValue(),
			'예정_시작일' :self.ui.dateEdit_start.date().toString("yyyy-MM-dd"),
			'예정_완료일' : self.ui.dateEdit_end.date().toString("yyyy-MM-dd"),
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
		self.ui.buttonBox.accepted.connect(self.slot_btn_ok)
		self.ui.buttonBox.rejected.connect(self.slot_btn_cancel)


	@pyqtSlot()
	def slot_btn_ok(self):
		sendData = deepcopy(self.dataObj)
		sendData.pop('id')
		sendData.update( self._get_data() )
		sendData.update ( {'등록일':datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
					 '활동일':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					 '등록자_fk':INFO.USERID,					 
					 } )
		ic( sendData )

		if ( activity_files := sendData.pop( 'activity_files', []) ):

			activity_files_existing_file_ids = []
			sendFi = []
			# 'type'이 'local'인 경우에만 API로 보낼 수 있도록 필터링
			for file in activity_files:
				if file['type'] == 'local':
					sendFi.append(('activity_files', (file['file'], open(file['file'], 'rb'))))
				elif file['type'] == 'server':
					activity_files_existing_file_ids.append( file['id'] )
			sendData['activity_files_ids'] = activity_files_existing_file_ids

		else:
			sendFi = []

		_isOk, _json = APP.API.Send(self.url, self.dataObj, sendData, sendFi)
		if _isOk:
			ic( _json )
			self.signal_ok.emit(_json)
			Utils.generate_QMsg_Information(self, title='Activity 등록 완료', text='Activity 등록 완료', autoClose=1000 )
			self.accept()
		else:
			Utils.generate_QMsg_critical(self)		

	@pyqtSlot()
	def slot_btn_cancel(self):
		self.reject()


