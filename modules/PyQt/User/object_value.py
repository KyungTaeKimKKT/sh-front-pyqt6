from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.component.combo_lineedit import Combo_LineEdit
from modules.PyQt.component.combo_lineedit_v2 import ComboLineEdit_V2
from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.imageViewer2 import ImageViewer2

from modules.PyQt.compoent_v2.Wid_label_and_pushbutton import Wid_label_and_pushbutton
from modules.PyQt.compoent_v2.Wid_lineedit_and_pushbutton import Wid_lineedit_and_pushbutton
from modules.PyQt.compoent_v2.FileListWidget.wid_fileUploadList import File_Upload_ListWidget

from info import Info_SW as INFO
from datetime import datetime, date, time
import traceback
from modules.logging_config import get_plugin_logger

CUSTOM_WIDGET_TYPE = (
	Wid_label_and_pushbutton, Wid_lineedit_and_pushbutton,
	File_Upload_ListWidget
)

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Widget_Get_Value :
	def __init__(self, obj:QWidget):
		super().__init__(obj)
		return self.get()

class Object_Get_Value:
	"""
		get object ( like, QlineEdit, QComboBox .... ) value
	"""
	custom_widget_type = CUSTOM_WIDGET_TYPE

	def __init__(self, obj:QWidget) ->None:
		self.obj = obj
		

	def get(self, key:str=''):
		obj = self.obj
		
		if isinstance( obj, QLineEdit ):
			return obj.text()
		elif isinstance ( obj, QComboBox ):
			return obj.currentText()
		elif isinstance ( obj, QSpinBox ):
			return obj.value()
		elif isinstance ( obj, QCheckBox ):
			return obj.isChecked()
		elif isinstance ( obj, QTextEdit):
			return obj.toPlainText()		
		elif isinstance (obj, QPlainTextEdit):
			return obj.toPlainText()
		elif isinstance (obj, QDoubleSpinBox):
			return obj.value()
		
		elif isinstance ( obj, QDateEdit ):
			return obj.date().toPyDate()
		
		elif isinstance ( obj, QDateTimeEdit ):
			return obj.dateTime().toPyDateTime()
		
		elif isinstance( obj, Combo_LineEdit):
			return obj.getValue()
		
		elif isinstance(obj, ImageViewer):
			return obj._getValue(key)
		
		elif isinstance(obj, ImageViewer2):
			return obj._getValue(key)
		
		elif isinstance( obj, QCheckBox):
			return obj.isChecked()
		
		elif isinstance ( obj, ComboLineEdit_V2):
			return obj.getValue()
		
		#### custom widget경우
		elif isinstance( obj, self.custom_widget_type):
			return obj.get_value()
		
		
		else:
			raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(obj)}")
			return None


# class Widget_Get_Value :
# 	def __init__(self, obj:QWidget):
# 		super().__init__(obj)
# 		return self.get()
	

class Object_Set_Value:
	"""
			Set object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QObject, value:object=None) ->None:
		self.obj = input
		self.value = value
		self.set()

	def set(self):
		obj = self.obj
		value = self.value
		
		if isinstance( obj, QLineEdit ):
			if value is None:
				value = ''
			if value :
				obj.setText(str(value))
		elif isinstance ( obj, QComboBox ):
			obj.setCurrentText(str(value))
		elif isinstance ( obj, QSpinBox ):
			try:
				obj.setValue(int(value))
			except:
				obj.setValue(0)
		elif isinstance ( obj, QCheckBox ):
			obj.setChecked( True if 'true' in str(value).lower() else False)
		elif isinstance ( obj, QTextEdit):
			obj.setText(value)
		
		elif isinstance (obj, QPlainTextEdit):
			obj.setPlainText(value)
		elif isinstance (obj, QDoubleSpinBox):
			try:
				obj.setValue(float(value))
			except:
				obj.setValue(0)
		
		elif isinstance ( obj, QDateEdit ):
			if isinstance( value, QDate):
				obj.setDate( value)
			elif isinstance ( value, date):
				obj.setDate( value )
			elif isinstance( value, str ):
				value = self._get_Date_from_str(value)

				obj.setDate(value)
		
		elif isinstance ( obj, QDateTimeEdit ):
			if isinstance( value, QDateTime):
				obj.setDateTime( value)
			elif isinstance ( value, datetime):
				obj.setDateTime( value )
			elif isinstance( value, str ):


				obj.setDateTime(self._get_Datetime_from_str(value))
		
		elif isinstance( obj, Combo_LineEdit):
			return obj.setValue(value)
		
		elif isinstance ( obj, QLabel):
			obj.setText( str(value) )
		
		elif isinstance ( obj, QProgressBar):
			obj.setValue( int(value))

		elif isinstance ( obj, QTextBrowser):
			obj.setAcceptRichText(True)
			# obj.setText ('<p style="background-color:black;color:yellow')
			obj.setText(value)

		elif isinstance ( obj, ComboLineEdit_V2):
			return obj.setValue()
		
		elif isinstance( obj, Wid_label_and_pushbutton):
			return obj.set_label_text(value)

	def _get_Datetime_from_str(self, text:str) -> QDateTime:
		if text is None : 
			return QDateTime.currentDateTime()
		wo_ms = text.split('.')[0].strip()
		if 'T' in wo_ms :
			return  QDateTime.fromString( wo_ms, 'yyyy-MM-ddThh:mm:ss')
		else : 
			wo_ms = wo_ms.replace(' ','')
			return QDateTime.fromString( wo_ms, 'yyyy-MM-ddhh:mm:ss')

	def _get_Date_from_str(self, text:str) -> date:

		if text is None or len(text)<4: 
			return date.today()
		if 'T' in text:

			text = text.split('T')[0]
		elif '.' in text  : #and ( len(text) == 8 or len(text) ==  10 ) :
			return  datetime.strptime( text, '%y.%m.%d').date()

		else:
			pass
		return QDate.fromString(text, 'yyyy-MM-dd')
	
class Object_Diable_Edit(Object_Set_Value):
	"""
			Set and disable object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QObject, value:object=None) ->None:
		super().__init__(input, value)
		self.disable()

	def disable(self):
		obj = self.obj
		value = self.value
		
		if isinstance( obj, QLineEdit ):
			obj.setEnabled(False)
		elif isinstance ( obj, QComboBox ):
			obj.setEnabled(False)
		elif isinstance ( obj, QSpinBox ):
			obj.setEnabled(False)
		elif isinstance ( obj, QCheckBox ):
			obj.setEnabled(False)
		elif isinstance ( obj, QTextEdit):
			obj.setEnabled(False)
		
		elif isinstance ( obj, QDateEdit ):
			obj.setEnabled(False)
	

class Object_ReadOnly(Object_Set_Value):
	"""
			Set and disable object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QObject, value:object=None) ->None:
		super().__init__(input, value)
		self.readOnly()

	def readOnly(self):
		obj = self.obj
		value = self.value
		
		if isinstance( obj, QLineEdit ):
			obj.setReadOnly(True)
		elif isinstance ( obj, QComboBox ):
			obj.setDisabled(True)
		elif isinstance ( obj, QSpinBox ):
			obj.setReadOnly(True)
		elif isinstance ( obj, QCheckBox ):
			obj.setDisabled(True)
		elif isinstance ( obj, QTextEdit):
			obj.setReadOnly(True)
		
		elif isinstance ( obj, QDateEdit ):
			obj.clearMinimumDateTime() 
			self.set()
			obj.setReadOnly(True)
		
		elif isinstance ( obj, QDateTimeEdit ):
			obj.clearMinimumDateTime() 
			self.set()
			obj.setReadOnly(True)
		elif isinstance ( obj, QPlainTextEdit ):
			obj.setReadOnly(True)
		
		elif isinstance( obj, Combo_LineEdit):
			obj._setReadOnly()
		
		elif isinstance ( obj, QLabel):
			return 
		
		elif isinstance ( obj, QProgressBar):
			return
		
		elif isinstance( obj, Combo_LineEdit):
			obj.setValue(value)
			obj._setReadOnly()
			return 
		
		elif isinstance ( obj, ComboLineEdit_V2):
			obj.setValue(value)
			obj._setReadOnly()
			return 
		
		else:
			obj.setReadOnly
	
	