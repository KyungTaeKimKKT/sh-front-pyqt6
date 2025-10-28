import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import typing

from modules.user.class_utils import Class_Utils
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Numeric_Validator( QRegularExpressionValidator, Class_Utils):
	def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
		self.reg_ex = qRegEx if qRegEx else QRegularExpression("^[0-9]*$")
		self.wid = wid
		super().__init__(self.reg_ex, self.wid)

class YearMonth_Validator( QRegularExpressionValidator, Class_Utils):
	"""YYYY-MM 형태"""
	def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
		self.reg_ex = qRegEx if qRegEx else QRegularExpression("^[0-9]{4}-[0-9]{2}$")
		self.wid = wid
		super().__init__(self.reg_ex, self.wid)


class 샘플의뢰_size_Validator( QRegularExpressionValidator, Class_Utils):
	""" 1.5T*150*150 형태"""
	def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
		exp_str = "^[0-9.]+T\\*[0-9.]+\\*[0-9.]+$"
		self.reg_ex = qRegEx if qRegEx else QRegularExpression(exp_str)
		self.wid = wid
		super().__init__(self.reg_ex, self.wid)

class 생산지시서_치수_Validator( QRegularExpressionValidator, Class_Utils):
	""" 1.5T*1219*2750 형태"""
	def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
		exp_str = "^[0-9.]+T\\*[0-9.]+\\*[0-9.]+$"
		self.reg_ex = qRegEx if qRegEx else QRegularExpression(exp_str)
		self.wid = wid
		super().__init__(self.reg_ex, self.wid)

    # def validate(self, input_str, pos):
    #     if input_str == "":
    #         return (QValidator.State.Intermediate, input_str, pos)
        
    #     match = self.regex.match(input_str)
    #     if match.hasMatch():
    #         return (QValidator.State.Acceptable, input_str, pos)
        
    #     # T, * 문자가 포함되어 있거나 숫자와 소수점만 있는 경우 Intermediate
    #     if any(c in input_str for c in ['T', '*']) or all(c.isdigit() or c == '.' for c in input_str):
    #         return (QValidator.State.Intermediate, input_str, pos)
            
    #     return (QValidator.State.Invalid, input_str, pos)

class 망등록_망번호_Validator( QRegularExpressionValidator, Class_Utils):	
	""" 22-001 형태"""
	def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
		self.reg_ex = qRegEx if qRegEx else QRegularExpression("^[0-9]{2}[-][0-9]{3}$")
		self.wid = wid
		super().__init__(self.reg_ex, self.wid)


	# 	self.run()
	
	# def run(self):


	# 	return QRegularExpressionValidator( self.reg_ex, self.wid )
		




# class NumericDelegate(QStyledItemDelegate):
# 	def createEditor(self, parent, option, index):
# 		# if index.row() == 0 : return 
# 		editor = super(NumericDelegate, self).createEditor(parent, option, index)
# 		if isinstance(editor, QLineEdit):
# 			reg_ex = QRegExp("^[0-9]*$")
# 			validator = QRegularExpressionValidator(reg_ex, editor)
# 			editor.setValidator(validator)
# 		return editor

class Serial번호_Validator(QRegularExpressionValidator, Class_Utils):
    """ HI250211HY-00001 형태 검증
    - 앞 2글자: 문자
    - 가운데 6글자: 숫자(년월일)
    - 뒤 2글자: 문자
    - 하이픈(-)
    - 마지막 5글자: 숫자
    """
    def __init__(self, qRegEx:QRegularExpression=None, wid:QWidget=None):
        exp_str = "^[A-Z]{2}[0-9]{6}[A-Z]{2}-[0-9]{5}$"
        self.reg_ex = qRegEx if qRegEx else QRegularExpression(exp_str)
        self.wid = wid
        super().__init__(self.reg_ex, self.wid)