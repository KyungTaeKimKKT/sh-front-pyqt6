from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.component.combo_lineedit import Combo_LineEdit
from modules.PyQt.component.combo_lineedit_v2 import ComboLineEdit_V2
from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.imageViewer2 import ImageViewer2

from info import Info_SW as INFO
from datetime import datetime, date, time
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()



class Widget_Get_Value:
	"""
		get object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, obj:QWidget) ->None:
		self.obj = obj
		
	@staticmethod
	def getValue(obj:QWidget, key:str=''):
		"""
		위젯의 값을 가져오는 정적 메소드
		
		Args:
			obj: 값을 가져올 위젯
			key: 특정 위젯에서 사용하는 키 (예: ImageViewer)
			
		Returns:
			위젯의 값
		"""
		try:
			if obj is None:
				return None
				
			if isinstance(obj, QLineEdit):
				return obj.text()
				
			elif isinstance(obj, QComboBox):
				return obj.currentText()
				
			elif isinstance(obj, QSpinBox):
				return obj.value()
				
			elif isinstance(obj, QDoubleSpinBox):
				return obj.value()
				
			elif isinstance(obj, QCheckBox):
				return obj.isChecked()
				
			elif isinstance(obj, QTextEdit):
				return obj.toPlainText()
				
			elif isinstance(obj, QPlainTextEdit):
				return obj.toPlainText()
				
			elif isinstance(obj, QDateEdit):
				return obj.date().toPyDate()
				
			elif isinstance(obj, QDateTimeEdit):
				return obj.dateTime().toPyDateTime()
				
			elif isinstance(obj, Combo_LineEdit):
				return obj.getValue()
				
			elif isinstance(obj, ComboLineEdit_V2):
				return obj.getValue()
				
			elif isinstance(obj, ImageViewer):
				return obj._getValue(key)
				
			elif isinstance(obj, ImageViewer2):
				return obj._getValue(key)
				
			elif isinstance(obj, QTableWidget):
				# 테이블 위젯 데이터 추출
				rows = obj.rowCount()
				cols = obj.columnCount()
				data = []
				for row in range(rows):
					row_data = []
					for col in range(cols):
						item = obj.item(row, col)
						row_data.append(item.text() if item else "")
					data.append(row_data)
				return data
				
			elif isinstance(obj, QTableView):
				# 테이블 뷰 모델 데이터 추출
				model = obj.model()
				if model:
					rows = model.rowCount()
					cols = model.columnCount()
					data = []
					for row in range(rows):
						row_data = []
						for col in range(cols):
							index = model.index(row, col)
							row_data.append(model.data(index))
						data.append(row_data)
					return data
				return []
				
			else:
				logger.warning(f"지원하지 않는 위젯 타입입니다: {type(obj)}")
				return None
		except Exception as e:
			logger.error(f"위젯 값 가져오기 중 오류 발생: {e}")
			logger.error(traceback.format_exc())
			return None

	def get(self, key:str=''):
		return Widget_Get_Value.getValue(self.obj, key)


# class Widget_Get_Value :
# 	def __init__(self, obj:QWidget):
# 		super().__init__(obj)
# 		return self.get()
	

class Widget_Set_Value:
	"""
			Set object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QWidget, value:object=None) ->None:
		self.obj = input
		self.value = value
		self.set()

	@staticmethod
	def _get_Datetime_from_str(text:str) -> QDateTime:
		"""
		문자열에서 QDateTime 객체를 생성합니다.
		
		Args:
			text: 날짜시간 문자열
			
		Returns:
			QDateTime: 변환된 날짜시간 객체
		"""
		if text is None or not text: 
			return QDateTime.currentDateTime()
			
		try:
			# 밀리초 부분 제거
			wo_ms = text.split('.')[0].strip()
			
			# 지원하는 날짜 형식 목록
			formats = [
				('yyyy-MM-ddThh:mm:ss', lambda t: t),  # ISO 형식
				('yyyy-MM-dd hh:mm:ss', lambda t: t),  # 일반 형식
				('yyyy-MM-ddhh:mm:ss', lambda t: t.replace(' ','')),  # 공백 없는 형식
				('yyyy-MM-dd', lambda t: t),  # 날짜만 있는 형식
				('yy.MM.dd hh:mm', lambda t: t)  # 간략 형식
			]
			
			# 각 형식으로 변환 시도
			for fmt, preprocessor in formats:
				processed_text = preprocessor(wo_ms)
				dt = QDateTime.fromString(processed_text, fmt)
				if dt.isValid():
					return dt
			
			# 모든 형식 변환 실패 시 현재 날짜시간 반환
			logger.warning(f"지원하지 않는 날짜시간 형식: {text}")
			return QDateTime.currentDateTime()
		except Exception as e:
			logger.error(f"날짜시간 변환 오류: {e}")
			return QDateTime.currentDateTime()

	@staticmethod
	def _get_Date_from_str(text:str) -> QDate:
		"""
		문자열에서 QDate 객체를 생성합니다.
		
		Args:
			text: 날짜 문자열
			
		Returns:
			QDate: 변환된 날짜 객체
		"""
		if text is None or not text or len(text) < 4: 
			return QDate.currentDate()
			
		try:
			# 다양한 형식 처리
			if 'T' in text:
				text = text.split('T')[0]
			
			# 지원하는 날짜 형식 목록
			formats = [
				('yyyy-MM-dd', lambda t: t),  # ISO 형식
				('yy.MM.dd', lambda t: t),    # 간략 형식
				('MM/dd/yyyy', lambda t: t),  # 미국식 형식
				('dd.MM.yyyy', lambda t: t)   # 유럽식 형식
			]
			
			# 각 형식으로 변환 시도
			for fmt, preprocessor in formats:
				processed_text = preprocessor(text)
				dt = QDate.fromString(processed_text, fmt)
				if dt.isValid():
					return dt
			
			# 특수 형식 처리 (.으로 구분된 간략 형식)
			if '.' in text:
				try:
					return datetime.strptime(text, '%y.%m.%d').date()
				except ValueError:
					pass
			
			# 모든 형식 변환 실패 시 현재 날짜 반환
			logger.warning(f"지원하지 않는 날짜 형식: {text}")
			return QDate.currentDate()
		except Exception as e:
			logger.error(f"날짜 변환 오류: {e}")
			return QDate.currentDate()

	@staticmethod
	def setValue(obj:QWidget, value:object=None):
		"""
		위젯에 값을 설정하는 정적 메소드
		
		Args:
			obj: 값을 설정할 위젯
			value: 설정할 값
		"""
		try:
			if isinstance(obj, QLineEdit):
				obj.setText("" if value is None else str(value))
				
			elif isinstance(obj, QComboBox):
				if value is not None:
					# 콤보박스에 해당 항목이 있는지 확인
					index = obj.findText(str(value))
					if index >= 0:
						obj.setCurrentIndex(index)
					else:
						# 없으면 텍스트 직접 설정 시도
						obj.setCurrentText(str(value))
				
			elif isinstance(obj, QSpinBox):
				try:
					obj.setValue(int(value) if value is not None else 0)
				except (ValueError, TypeError):
					obj.setValue(0)
					
			elif isinstance(obj, QDoubleSpinBox):
				try:
					obj.setValue(float(value) if value is not None else 0.0)
				except (ValueError, TypeError):
					obj.setValue(0.0)
					
			elif isinstance(obj, QCheckBox):
				if value is None:
					obj.setChecked(False)
				else:
					# 다양한 불리언 표현 처리
					str_value = str(value).lower()
					obj.setChecked(str_value in ('true', 'yes', 'y', '1', 'on'))
					
			elif isinstance(obj, QTextEdit):
				obj.setText("" if value is None else str(value))
				
			elif isinstance(obj, QPlainTextEdit):
				obj.setPlainText("" if value is None else str(value))
				
			elif isinstance(obj, QDateEdit):
				if value is None:
					obj.setDate(QDate.currentDate())
				elif isinstance(value, QDate):
					obj.setDate(value)
				elif isinstance(value, date):
					obj.setDate(QDate(value.year, value.month, value.day))
				elif isinstance(value, str):
					obj.setDate(Widget_Set_Value._get_Date_from_str(value))
				else:
					# 알 수 없는 타입은 현재 날짜로 설정
					logger.warning(f"QDateEdit에 지원하지 않는 값 타입: {type(value)}")
					obj.setDate(QDate.currentDate())
					
			elif isinstance(obj, QDateTimeEdit):
				if value is None:
					obj.setDateTime(QDateTime.currentDateTime())
				elif isinstance(value, QDateTime):
					obj.setDateTime(value)
				elif isinstance(value, datetime):
					obj.setDateTime(QDateTime(value))
				elif isinstance(value, str):
					obj.setDateTime(Widget_Set_Value._get_Datetime_from_str(value))
				else:
					# 알 수 없는 타입은 현재 날짜시간으로 설정
					logger.warning(f"QDateTimeEdit에 지원하지 않는 값 타입: {type(value)}")
					obj.setDateTime(QDateTime.currentDateTime())
					
			elif isinstance(obj, Combo_LineEdit):
				obj.setValue(value)
				
			elif isinstance(obj, ComboLineEdit_V2):
				obj.setValue(value)
				
			elif isinstance(obj, QLabel):
				obj.setText("" if value is None else str(value))
				
			elif isinstance(obj, QProgressBar):
				try:
					obj.setValue(int(value) if value is not None else 0)
				except (ValueError, TypeError):
					obj.setValue(0)
					
			elif isinstance(obj, QTextBrowser):
				obj.setAcceptRichText(True)
				obj.setText("" if value is None else str(value))
				
			elif isinstance(obj, QTableWidget):
				# 테이블 위젯에 데이터 설정
				if value is None:
					obj.setRowCount(0)
					return
					
				if isinstance(value, list):
					obj.setRowCount(len(value))
					if len(value) > 0:
						obj.setColumnCount(len(value[0]) if isinstance(value[0], list) else 1)
						
					for row, row_data in enumerate(value):
						if isinstance(row_data, list):
							for col, cell_data in enumerate(row_data):
								item = QTableWidgetItem("" if cell_data is None else str(cell_data))
								obj.setItem(row, col, item)
						else:
							item = QTableWidgetItem("" if row_data is None else str(row_data))
							obj.setItem(row, 0, item)
			else:
				logger.warning(f"지원하지 않는 위젯 타입입니다: {type(obj)}")
		except Exception as e:
			logger.error(f"위젯 값 설정 중 오류 발생: {e}")
			logger.error(traceback.format_exc())

	def set(self):
		Widget_Set_Value.setValue(self.obj, self.value)

class Widget_Diable_Edit(Widget_Set_Value):
	"""
			Set and disable object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QWidget, value:object=None) ->None:
		super().__init__(input, value)
		self.disable()

	@staticmethod
	def disableWidget(obj:QWidget):
		"""
		위젯을 비활성화하는 정적 메소드
		"""
		if isinstance(obj, (QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit, QDateEdit)):
			obj.setEnabled(False)

	def disable(self):
		Widget_Diable_Edit.disableWidget(self.obj)

class Widget_ReadOnly(Widget_Set_Value):
	"""
			Set and disable object ( like, QlineEdit, QComboBox .... ) value
	"""

	def __init__(self, input:QWidget, value:object=None) ->None:
		super().__init__(input, value)
		self.readOnly()

	@staticmethod
	def setReadOnly(obj:QWidget, value:object=None):
		"""
		위젯을 읽기 전용으로 설정하는 정적 메소드
		"""
		if isinstance(obj, QLineEdit):
			obj.setReadOnly(True)
		elif isinstance(obj, QComboBox):
			obj.setDisabled(True)
		elif isinstance(obj, QSpinBox):
			obj.setReadOnly(True)
		elif isinstance(obj, QCheckBox):
			obj.setDisabled(True)
		elif isinstance(obj, QTextEdit):
			obj.setReadOnly(True)
		elif isinstance(obj, QDateEdit):
			obj.clearMinimumDateTime() 
			Widget_Set_Value.setValue(obj, value)
			obj.setReadOnly(True)
		elif isinstance(obj, QDateTimeEdit):
			obj.clearMinimumDateTime() 
			Widget_Set_Value.setValue(obj, value)
			obj.setReadOnly(True)
		elif isinstance(obj, QPlainTextEdit):
			obj.setReadOnly(True)
		elif isinstance(obj, Combo_LineEdit):
			obj.setValue(value)
			obj._setReadOnly()
		elif isinstance(obj, (QLabel, QProgressBar)):
			return
		elif isinstance(obj, ComboLineEdit_V2):
			obj.setValue(value)
			obj._setReadOnly()
		else:
			try:
				obj.setReadOnly(True)
			except:
				pass

	def readOnly(self):
		Widget_ReadOnly.setReadOnly(self.obj, self.value)
	
	