from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

from Ui_date_time import Ui_Dialog
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Date_Time(QDialog):

	def __init__(self, parent=None , **kwargs):
		super().__init__(parent)

		self.ui = Ui_Dialog()
		self.ui.setupUi(self)


		self.show()



def main():    
	import sys
	app=QtWidgets.QApplication(sys.argv)

	dlg = Wid_Date_Time()
	
	app.exec()


if __name__ == "__main__":
	import sys
	sys.exit( main())