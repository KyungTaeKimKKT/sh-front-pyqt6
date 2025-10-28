
import sys, os
from PyQt6.QtWidgets import QApplication,  QFileDialog
from pathlib import Path
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class File_Download(QFileDialog):
	def __init__(self, parent=None, folder:str=str(Path.home() / "Downloads"), fType:str="Excel Files(*.xlxs)", url:str=None):
		super().__init__(parent)
 
		self.options = self.Options()
		self.options |= self.DontUseNativeDialog

		self.Name, _ = self.getSaveFileName(parent=None, 
											caption="Save File", 
											directory=folder, 
											filter="Excel Files(*.xlxs)", 
											options = self.options)



app = QApplication(sys.argv)
demo = File_Download()
demo.show()
sys.exit(app.exec_())