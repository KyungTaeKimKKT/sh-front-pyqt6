from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtPrintSupport import *

import qrcode
import json
import cv2

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.dialog.ui.Ui_qr_read import Ui_Form

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class QDialog_QR_Reading ( QDialog, Ui_Form , Qwidget_Utils):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.dataObj = {}
		self.URL = INFO.URL_Serial조회_by_Serial
		self.prevSerial = ''

		self.setupUi(self)
		self.is_scan_start = False

		self.inputDict = {
			"고객사" : self.label_Gogak,
			"job_name" : self.label_Hyunjang,
			"생산형태" : self.label_Hyungtae,
			"제품분류" : self.label_Jepumbunru,
			"공정" : self.label_Gongjung,
			"작업명" : self.label_Jakup,
			"수량" : self.label_Count,
			'소재' : self.label_SoJae,
			'치수' : self.label_Chisu,
		}

		# self.PB_print.clicked.connect(self.on_PB_print_clicked )

	def run(self):
		pass

	def viewMode(self):
		if not self.dataObj: return
		#😀 inputDict에 해당하는 data만 setting
		for key, inputObj in self.inputDict.items():
			inputObj.setText ( self.dataObj.get(key, ''))

		# for key, value in self.dataObj.items():
		# 	self.inputDict[key].setText (value)

	@pyqtSlot()
	def on_PB_scan_clicked(self):
		self.is_scan_start = not self.is_scan_start
		pb_txt = 'Scan Stop' if self.is_scan_start else 'Scan Start'
		self.PB_scan.setText(pb_txt)

		if APP.CAM  is not None:
			if not APP.CAM.get_run_state() : APP.CAM.start()

			if self.is_scan_start:
				APP.CAM.signal_scan.connect( self.slot_signal_camera)
			else:
				self.widget.label_ImageView.setText('Scan Stopped !!')
				APP.CAM.signal_scan.disconnect( self.slot_signal_camera)


	@pyqtSlot( object)
	def slot_signal_camera(self, frame) -> None:
		""" camera로 부터 frame 영상이 들어오면, 처리"""
		self.render_live_image(frame)
		
		barcode = Utils.read_QR_Code( frame )
		if barcode:			
			self.curSerial = barcode.data.decode('utf-8')
			if self.prevSerial == self.curSerial:
				return
			self.render_barcode_image(frame, barcode)  
			self.prevSerial = self.curSerial
			self.dataObj = self._get_serialDB(self.curSerial)
			self.dataObj['수량'] = f"{self.dataObj.get('수량_no')} / {self.dataObj.get('계획수량')}"
			self.viewMode()

	def _get_serialDB(self, serial) -> dict:
		suffix = f'?serial={serial}&page_size=0'
		is_ok, _json = APP.API.getlist( url=self.URL+suffix )
		if is_ok:
			return _json[0]
		else:
			return {}		

	def render_live_image(self, frame):
		rgb_image = cv2.cvtColor( frame, cv2.COLOR_BGR2RGB)
		qImg = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
		self.widget_live.set_image_from_QImage(qImg)

	def render_barcode_image(self, frame, barcode) :
		if barcode :
			(x, y, w, h) = barcode.rect 
			cv2.rectangle( frame, (x-10, y-10), (x + w+10, y + h+10), (255, 0, 0), 2) 
		rgb_image = cv2.cvtColor( frame, cv2.COLOR_BGR2RGB)
		qImg = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
		self.widget.set_image_from_QImage(qImg)