from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


from modules.PyQt.User.Tb_Delegate import Base_Delegate

from modules.PyQt.component.choice_combobox import Choice_ComboBox

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger


### app 마다 hardcoding : 😀	

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 품질경영_Base_Delegate(Base_Delegate):
	def __init__(self, header:list=[], header_type:dict={} ,no_Edit:list = []):
		super().__init__(header, header_type, no_Edit)
		self.appData = None

	
	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor, index):
		row, col = index.row(), index.column()
		
		match self.header[col]:
			case '구분'|'고객사':
				if isinstance(editor, Choice_ComboBox):
					editor.setCurrentText( index.data() )
			case '접수디자이너':
				if isinstance(editor, QtWidgets.QComboBox ):
					editor.setCurrentText( index.data() )

		return editor

	### modify widgets
	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:
		match key:
			case '구분'|'고객사':
				if isinstance(widget, Choice_ComboBox):
					if key == '구분': widget.choices = self.appData._get_form_choices_구분()
					if key == '고객사': widget.choices = self.appData._get_form_choices_고객사()
					widget._render()
			case '접수디자이너':
				if isinstance(widget, QtWidgets.QComboBox ):					
					widget.addItems(self.appData._get_접수디자이너_selector())
		return widget