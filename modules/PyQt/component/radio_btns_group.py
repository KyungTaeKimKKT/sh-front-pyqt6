from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from modules.PyQt.component.ui.Ui_생산지시서_종류 import Ui_Form
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 생산지시서_종류_Selector(QWidget, Ui_Form):
	def __init__(self, parent):
		super().__init__(parent)
		self.defaultText = '생산지시서_Default'
		self.setupUi(self)
		self.inputDict = {
			'현대' : self.radio_HY,
			'OTIS' : self.radio_OTIS,
			'TKE' : self.radio_TKE,
			'기타' : self.radio_ETC,
		}
		self.default_set_Radio()

		self.installEventFilter(self)


	def default_set_Radio(self):
		if APP.CONFIG_개인 and (name:= APP.CONFIG_개인.get(self.defaultText, '') ):
			self.inputDict[name].setChecked(True)
		else:
			self.inputDict['현대'].setChecked(True)


	# https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
	def eventFilter(self, source, event:QEvent):
		if event.type() == QEvent.ContextMenu:
			menu = QMenu()
			action_save_Default = menu.addAction('Default로 저장')
 
			action = menu.exec_(event.globalPos())
  
			if action == action_save_Default:
				Utils.update_dict_to_json_file(self.get_value_Dict() )

		return super().eventFilter(source, event)
	
	def getValue(self) -> str:
		for key, value in self.get_value_Dict().items():
			return value

	def get_value_Dict(self) -> dict:
		for key, input in self.inputDict.items():
			input : QRadioButton
			if input.isChecked() :
				return {self.defaultText: key}