from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing
from datetime import date

#### import Custom StyleSheet
from stylesheet import StyleSheet
### import custom widgets 😀😀
from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.my_spinbox import My_SpinBox
from modules.PyQt.component.my_dateedit import My_DateEdit

from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_ReadOnly
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AlignDelegate(QtWidgets.QStyledItemDelegate):
	def __init__(self, parent: typing.Optional[QtCore.QObject], user_pks:list):
		super().__init__()
		self.user_pks = user_pks
		self.selected_row = -1
	
	def initStyleOption(self, option, index):
		super(AlignDelegate, self).initStyleOption(option, index)
		option.displayAlignment = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
		value = index.data()
		if (value:=index.data()) in self.user_pks:
			self.selected_row = index.row()
		
		if self.selected_row  == index.row():
			option.palette.setBrush(
				QtGui.QPalette.Text, QtGui.QBrush(QtGui.QColor("black"))
			)
			option.backgroundBrush = QtGui.QBrush(QtGui.QColor("yellow"))
		else:
			option.backgroundBrush = QtGui.QBrush(QtGui.QColor("white"))



class Base_Delegate(QtWidgets.QItemDelegate):
	def __init__(self, header:list=[], header_type:dict={} ,no_Edit:list = []):
		super().__init__()
		self.header_type = header_type		
		self.header = header if header else list(header_type.keys()) if bool(header_type) else []
		self.no_Edit = no_Edit
		self.ST = StyleSheet

	def createEditor(self, parent, option, index):
		row = index.row()
		col = index.column()
		if not col in self.no_Edit:
			key = self.header[col]
			value = self.header_type.get(key)
			match value:
				case '___':
					return super().createEditor(parent, option, index)
				case _:
					attrName = value.split('(')[0]
					#### QtWidets 내에 
					if hasattr( QtWidgets, attrName) :
						widget = eval(f"QtWidgets.{value}")
					#### QtWidets 외에 ==> custom widget 경우 😀😀
					else:
						try:
							widget = eval(value)
						except:
							widget = self.user_defined_cratorEditor(parent, value)
					### app마다,  key에 따라서 widget을 정의
					return self.user_defined_creatorEditor_설정(key, widget)
		

		else:
			return None

	#😀 각 app마다 custome widget일 때 지정할 것..
	def user_defined_cratorEditor(self, parent, value:str='') ->QtWidgets.QWidget:
		if value:
			return eval(value)
		else:
			return None

	def setEditorData(self, editor, index):
		row = index.row()
		col = index.column()
		key = self.header[col]		
		text = (index.data(Qt.EditRole) or index.data(Qt.DisplayRole))			
		
		if not key in self.no_Edit:		
			editor.setStyleSheet(self.ST.edit_)

			text = (index.data(Qt.EditRole) or index.data(Qt.DisplayRole))		


			Object_Set_Value( editor, text )	


			# if isinstance(editor, QtWidgets.QLineEdit ):
			# 	editor.setText(text)
			# elif isinstance(editor, QtWidgets.QPlainTextEdit):
			# 	editor.setPlainText(text)
			# elif isinstance(editor, QtWidgets.QCheckBox ):
			# 	editor.setChecked( True if 'true' in str(text).lower() else False)
			# elif isinstance(editor, QtWidgets.QSpinBox ):
			# 	try:
			# 		editor.setValue(int(text))
			# 	except:
			# 		editor.setValue(0)
			# 	editor.setRange(0, 100000)
			
			# #### 😀😀😀 DateEdit , DateTimeEdit true, but DateTimeEdit is NOT DateEdit
			# elif isinstance(editor, QtWidgets.QDateEdit ):
			# 	if isinstance( text , QDate ):
			# 		editor.setDate(text)
			# 	elif isinstance(text, str):
			# 		qDate = self._get_Date_from_str(text)
			# 		editor.setDate(qDate)

			# elif isinstance(editor, QtWidgets.QDateTimeEdit) :
			# 	if isinstance (text , QDateTime ):
			# 		editor.setDateTime(text)
			# 	elif isinstance(text, str):
			# 		qtDatetime = self._get_Datetime_from_str(text)
			# 		editor.setDateTime(qtDatetime)
					
			# elif isinstance(editor, QtWidgets.QTextEdit):
			# 	editor.setText(text)
			# 	editor.setAcceptRichText(True)

			# elif isinstance(editor, QtWidgets.QDoubleSpinBox):
			# 	try:
			# 		editor.setValue(float(text)) 
			# 	except:
			# 		editor.setValue(0.0) 
			# 	editor.setRange(0, 10000)
			# 	# editor.setAcceptRichText(True)

			# elif isinstance(editor, QtWidgets.QComboBox):
			# 	editor.setCurrentText(text ) 
			# else:
			# 	pass

			### 😀😀 필요시 Hard-coding
			self.user_defined_setEditorData(editor, index)
		
		else:
			return None

	# def setModelData(self, editor, model, index) -> None:
	# 	if isinstance(editor,  Combo_LineEdit):
	# 		value = editor.getValue()
	# 		model.setData(index, value, Qt.EditRole)


	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor, index):
		pass 

	def user_defined_creatorEditor_설정(self, key:str, widget:object) -> object:
		match key:
			case '소요시간':
				if isinstance(widget, QtWidgets.QDoubleSpinBox):
					widget.setRange(0.01, 20.00)
					widget.setSingleStep(0.01)
		return widget

	
	def _get_Datetime_from_str(self, text:str) -> QtCore.QDateTime:
		wo_ms = text.split('.')[0]
		if 'T' in wo_ms :
			return  QtCore.QDateTime.fromString( wo_ms, 'yyyy-MM-ddThh:mm:ss')
		else : return QtCore.QDateTime.fromString( wo_ms, 'yyyy-MM-dd hh:mm:ss')

	def _get_Date_from_str(self, text:str) -> QtCore.QDate:
		"""
			string format이 yyyy-MM-dd가 아니면
			현재 날짜 return			
		"""
		if text is None :  return QtCore.QDate.currentDate()
		
		if len(text := text.strip() ) < 10 :
			return QtCore.QDate.currentDate()
		
		try:
			date.fromisoformat(text)
		except:
			return QtCore.QDate.currentDate()
		
		return QtCore.QDate.fromString(text, 'yyyy-MM-dd')