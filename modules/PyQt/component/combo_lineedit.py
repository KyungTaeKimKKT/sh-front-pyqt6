from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.User.validator import (
    Numeric_Validator,
    생산지시서_치수_Validator,
	샘플의뢰_size_Validator,
)
from modules.PyQt.component.ui.Ui_combo_lineedit import Ui_Form

import modules.user.utils as Utils
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Combo_LineEdit(QtWidgets.QWidget, Ui_Form):
	signal_manual_input =  QtCore.pyqtSignal()
	signal_combo_input =  QtCore.pyqtSignal()
	currentTextChanged = QtCore.pyqtSignal()

	def __init__(self, parent=None, **kwargs):
		super().__init__( parent)
		self.items = INFO.고객사_Widget_items
		self.input = None
		self.value = None
		for k, v in kwargs.items():
			setattr( self,  k, v)
		# self.UI()
		# self.triggerConnect()

	def _render(self):
		if hasattr( self, 'vLayout') : Utils.deleteLayout(self.vLayout)
		self.setupUi(self)
		self._setDefault()  
		self._setValidator()
		self.line.hide()
		self.triggerConnect()      

		# self.value = self.combo.currentText() if self.combo.isVisible() else self.line.text()

	def _setDefault(self):
		self.combo.clear()
		self.combo.addItems(self.items)
		self.setValue(self.items[0])


	def _setValidator(self):
		""" lineedit에 대해 validator 적용"""
		pass
	
	def triggerConnect(self):
		self.combo.currentTextChanged.connect(self.slot_combo_textChanged)
		self.line.textChanged.connect ( self.slot_line_changed )

	def slot_combo_textChanged(self):
		txt = self.sender().currentText()
		if txt == '기타':
			self.line.setVisible(True)
			self.signal_manual_input.emit()
			self.currentTextChanged.emit()

		else:
			self.line.setVisible(False)
			self.signal_combo_input.emit()
			self.currentTextChanged.emit()
			self.value = txt

	def slot_line_changed(self):
		txt = self.sender().text()
		self.value = txt 
	
	def getValue(self):
		return self.line.text() if self.line.isVisible() else self.combo.currentText()

	
	def setValue(self, value):
		if value in self.items:
			self.combo.setCurrentText(value)
			self.signal_combo_input.emit()
		else:
			self.combo.setCurrentText('기타')
			self.line.setText(str(value) )
			self.line.setVisible(True)
			self.line.textChanged.connect ( self.slot_line_changed )
			self.signal_manual_input.emit()

	def _setMaximumWidth(self, width:int) -> None:
		self.combo.setMaximumWidth(width)
		self.line.setMaximumWidth(width)

	def _setReadOnly(self):
		self.line.setReadOnly(True)
		self.combo.setEnabled(False)


class 고객사_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.고객사_Widget_items
		self._render()

class  구분_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.구분_Widget_items
		self._render()
		  
class  생산형태_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.생산형태_Widget_items
		self._render()
		  
class Material_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Material_Widget_itmes
		self._render()
		  
class Sample_소재Size_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Sample_소재Size_Widget_items
		self._render()

			
class 생산지시서_소재_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.생산지시서_소재_Widget_items
		self._render()

class 생산지시서_치수_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.생산지시서_치수_Widget_items
		self._render()

	def _setValidator(self):
		""" lineedit에 대해 validator 적용"""
		self.line.setValidator( 생산지시서_치수_Validator(qRegEx=None, wid=self.line) )
		self.line.setPlaceholderText("숫자,T,* 만 입력")
		# validator = Numeric_Validator(qRegEx=None, wid=self.line)

		# if isinstance( validator, QValidator):
		# 	self.line.setValidator( validator  )

class 생산지시서_판금출하처_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.생산지시서_판금출하처_Widget_items
		self._render()

class 생산지시서_JAMB발주사_Widget(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.생산지시서_JAMB발주사_Widget_items
		self._render()

class Widget_망관리_고객사( 고객사_Widget):
	pass
	# def __init__(self, parent=None, **kwargs):
	# 	super().__init__(parent, **kwargs)
	

class Widget_망관리_의장종류(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Widget_망관리_의장종료_items
		self._render()

class Widget_망관리_할부치수(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Widget_망관리_할부치수_items
		self._render()

class Widget_망관리_품명(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Widget_망관리_품명_items
		self._render()

class Widget_망관리_망사(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Widget_망관리_망사_items
		self._render()

class Widget_망관리_사용구분(Combo_LineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.items = INFO.Widget_망관리_사용구분_items
		self._render()