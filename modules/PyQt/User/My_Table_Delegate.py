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

import modules.user.utils as utils
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



class My_Table_Delegate(QtWidgets.QItemDelegate):
	""" 필수 kwarg \n
		table_header= list[str], \n
		header_type = dict{str:str}, \n
		no_Edit_cols = list[str]
	"""
	def __init__(self, parent, **kwargs):

		super().__init__(parent)
		for key, value in kwargs.items():
			setattr(self, key, value)
			
		self.table_header : list[str]
		self.no_Edit_cols : list[str]
		self.header_type :  dict[str:str]
		# self.header_type = header_type		
		# self.header = header if header else list(header_type.keys()) if bool(header_type) else []
		# self.no_Edit_cols = no_Edit
		self.ST = StyleSheet

	def createEditor(self, parent, option, index):
		row = index.row()
		col = index.column()
		key = str(self.table_header[col] )
		value = str(self.header_type.get(key) )

		if not key in self.no_Edit_cols:
			match utils.get_dataType( value ):
				case 'Char':
					widget = QLineEdit(self)
				case 'Integer':
					widget = QSpinBox(self)
				case 'Float':
					widget = QDoubleSpinBox(self)
				case 'Text':
					widget = QPlainTextEdit(self)
				case 'DateTime':
					widget = QDateTimeEdit(self)
				case 'Date'	:
					widget = QDateEdit(self)
				case 'Time' :
					widget = QTimeEdit(self)
				case 'Boolean':
					widget = QCheckBox(self)
				case _:
					return super().createEditor(parent, option, index)
				
			return self.user_defined_creatorEditor_설정(key, widget)

		else:
			return None

	#😀 각 app마다 custome widget일 때 지정할 것..
	def user_defined_cratorEditor(self, key:str, widget:QWidget) ->QtWidgets.QWidget:
		return widget


	def setEditorData(self, editor:QWidget, index:QModelIndex) ->None:
		row = index.row()
		col = index.column()
		key = self.table_header[col]		
		value = (index.data(Qt.ItemDataRole.EditRole) or index.data(Qt.ItemDataRole.DisplayRole))			
		
		if not key in self.no_Edit_cols:		
			editor.setStyleSheet(self.ST.edit_)

			Object_Set_Value( editor, value )	

			### 😀😀 필요시 Hard-coding
			self.user_defined_setEditorData(editor, index)


	# def setModelData(self, editor, model, index) -> None:
	# 	if isinstance(editor,  Combo_LineEdit):
	# 		value = editor.getValue()
	# 		model.setData(index, value, Qt.EditRole)


	############ 아래 2개는 app마다 override 할 것😀😀 #####################
	def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex) -> None:
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