from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtPrintSupport import *

import qrcode
import json

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
# from modules.PyQt.dialog.ui.Ui_qr_write import Ui_Form
from modules.PyQt.dialog.ui.Ui_qr_write_with_label import Ui_Form

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class QDialog_QR_Writing ( QDialog, Ui_Form , Qwidget_Utils):
	signal_prt_end = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.dataObj = {}
		self.receivedData = {}
		self.serialCode = ''
		self.setupUi(self)

		self.URL = INFO.URL_Serial_Generate_Bulk

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

		# self.printer = self._init_Printer()

		self.PB_print.clicked.connect(self.on_PB_print_clicked )

	def _init_Printer(self) -> QPrinter:
		printer = QPrinter()

		pageSize = QPageSize(  QSizeF(100,100), QPageSize.Unit.Millimeter, "QR_Label")
		printer.setPageSize( pageSize )

		printer.setFullPage(True)
		printer.setPageMargins( QMarginsF(0,0,0,0), QPageLayout.Unit.Millimeter )
		printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)

	def run(self) -> bool:
		if not self.receivedData: return

		sendData = {}
		sendData['생산계획_확정_Branch_fk'] = self.receivedData['id']
		sendData['수량_no'] = self.receivedData['수량_no']
		sendData['확정자'] = INFO.USERID
		sendData['serial'] ='임의코드'

		is_ok, _json = APP.API.Send( url=self.URL,
							  dataObj={},
							  sendData=sendData)
		if is_ok:
			self.serialCode = _json.get('serial', '')
			self.dataObj = _json
			self.dataObj['수량'] = f"{self.dataObj.get('수량_no')} / {self.dataObj.get('계획수량')}"

			self.viewMode()
			self.show()
			self.on_PB_print_clicked()

	def viewMode(self):
		if not self.dataObj: return
		#😀 inputDict에 해당하는 data만 setting
		for key, inputObj in self.inputDict.items():
			inputObj.setText ( self.dataObj.get(key, ''))

		# for key, value in self.dataObj.items():
		# 	self.inputDict[key].setText (value)

	@pyqtSlot()
	def on_PB_print_clicked(self):
		qr_img = Utils.generate_QR_Code( self.serialCode )
		self.set_image_from_pillowImage(qr_img )
		self.print_me()

	def set_image_from_pillowImage(self, pillowImage):
		"""https://stackoverflow.com/questions/63138735/how-to-insert-a-pil-image-in-a-pyqt-canvas-PyQt6"""
		from PIL.ImageQt import ImageQt
		imageQt = ImageQt(pillowImage).copy()
		self.img_QR.setPixmap(   QPixmap.fromImage(imageQt) )

	def print_me(self):
		printer = QPrinter()

		pageSize = QPageSize(  QSizeF(100,100), QPageSize.Unit.Millimeter, "QR_Label")
		printer.setPageSize( pageSize )

		printer.setFullPage(True)
		printer.setPageMargins( QMarginsF(0,0,0,0), QPageLayout.Unit.Millimeter )
		printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)
		# printer.setOutputFileName("Test.pdf")

		painter = QPainter(printer)
		painter.begin(printer)
		scale = self._get_printer_scale() 
		painter.scale( scale, scale )

		self.frame_printArea.render(painter)
		painter.end()
		
		self.signal_prt_end.emit()

	def _get_printer_scale(self) -> float:
		return self.doubleSpinBox_scale.value()
		unit = QPrinter.Unit.Millimeter
		# Establish scaling transform
		xscale = self.frame_printArea.width() / printer.pageRect(unit).width() 

		yscale = self.frame_printArea.height() / printer.pageRect(unit).height() 
