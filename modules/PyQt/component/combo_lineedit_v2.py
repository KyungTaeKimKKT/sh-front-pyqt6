from PyQt6.QtWidgets import QWidget, QComboBox, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QValidator, QFont

from modules.PyQt.User.validator import (
    Numeric_Validator,
    생산지시서_치수_Validator,
	샘플의뢰_size_Validator,
)

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ComboLineEdit_V2(QWidget):
	def __init__(self, parent=None, **kwargs):
		super().__init__(parent)
		self.items:list = []
		self.value = None
		
		for k, v in kwargs.items():
			setattr ( self, k, v)
		# 레이아웃 설정
		self.vlayout = QVBoxLayout(self)
		self.vlayout.setContentsMargins(0, 0, 0, 0)
		self.vlayout.setSpacing(0)
		
		# 콤보박스 생성
		self.combo = QComboBox()
		self.combo.addItems(self.items)
		
		# 라인에딧 생성
		self.lineEdit = QLineEdit()
		self.lineEdit.hide()  # 초기에는 숨김
		
		# 스타일 설정
		self.lineEdit.setStyleSheet("""
			QLineEdit:focus {
				background-color: yellow;
				font-weight: bold;
			}
		""")
		
		
		# 위젯 추가
		self.vlayout.addWidget(self.combo)
		self.vlayout.addWidget(self.lineEdit)
		
		# 콤보박스 변경 이벤트 연결
		self.combo.currentTextChanged.connect(self.onComboChanged)

		if hasattr(self, 'value') :
			self.setValue(self.value)
		
	def onComboChanged(self, text):
		if text == '기타':
			self.lineEdit.show()
			self.lineEdit.setFocus()
		else:
			self.lineEdit.hide()
			
	def getValue(self):
		if self.combo.currentText() == '기타':
			return self.lineEdit.text()
		return self.combo.currentText()
		
	def setValue(self, value=None):
		if value is None :
			if self.value is None:
				self.combo.setCurrentIndex(0)
				return 
			else:
				value = self.value

		if value in [self.combo.itemText(i) for i in range(self.combo.count())]:
			self.combo.setCurrentText(value)
			return 
		else:
			self.combo.setCurrentText('기타')
			self.lineEdit.setText(value)
			self.lineEdit.show()


	
	def _setReadOnly(self):
		self.lineEdit.setReadOnly(True)
		self.combo.setEnabled(False)

	
	def _setValidator(self):
		""" lineedit에 대해 validator 적용"""
		self.lineEdit.setValidator( 샘플의뢰_size_Validator(qRegEx=None, wid=self.lineEdit) )
		self.lineEdit.setPlaceholderText("숫자,T 만 입력")


class 샘플의뢰_Table_소재종류 ( ComboLineEdit_V2 ):
	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)


class 샘플의뢰_Table_소재Size ( ComboLineEdit_V2 ):
	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)

	def _setValidator(self):
		""" lineedit에 대해 validator 적용"""
		self.lineEdit.setValidator( 샘플의뢰_size_Validator(qRegEx=None, wid=self.lineEdit) )
		self.lineEdit.setPlaceholderText("숫자,T 만 입력")