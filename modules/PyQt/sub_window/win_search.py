from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtCore import QDate
from PyQt6 import sip



import typing

from stylesheet import StyleSheet
from modules.PyQt.User.object_value import Object_Get_Value
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Win_Search(QDialog):

	signal = pyqtSignal(dict)
	
	def __init__(self, parent=None):
		super().__init__(parent=None)
		self.parent =parent
		self.header = ['검색어',]

		self.inputType = {
			'검색어': 'QLineEdit()',

		}
		self.inputDict = {}
		self.result = {}
		self.필수keys = [] ### parent의 Data class 의  search_필수kyes=['search'] 상속
		

		self.UI()

		self.render_default()
		self.triggerConnect()

		self.st = StyleSheet()


		# self.PB_search.defaultStyle = self.PB_search.styleSheet()
	
	def UI(self):
		if hasattr(self, 'formlayout') : 
			self.deleteLayout(self.formlayout)
		self.setMinimumSize(450,400)
		self.formlayout = QFormLayout()

		self.title = QLabel()
		self.title.setText('검색')
		self.title.setSizePolicy(QSizePolicy.Expanding, 0)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:64px;color:white;background-color:black;")
		self.formlayout.addRow(self.title)

		self.UI_for_search_type()
		# for key in self.header:
		# 	(_txt, _input) = self.__gen_element(key, None)
		# 	if  _txt is not None  and _input is not None:
		# 		self.inputDict[key] = _input
		# 		self.formlayout.addRow(_txt, _input)
		self.fileLabel= QLabel()
		self.formlayout.addRow(self.fileLabel)
		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_search = QPushButton('검색')
		self.PB_search.setEnabled(False)
		self.PB_cancel = QPushButton('취소')
		hbox.addWidget(self.PB_search)
		hbox.addWidget(self.PB_cancel)
		self.formlayout.addRow(hbox)
		

		self.setLayout(self.formlayout)
		self.show()
	
	def UI_for_search_type(self):
		if self.parent.search_type is None : return
		for ( key, value) in self.parent.search_type.items():
			(_label, _input) = self.__gen_element(key, value)
			if  _label is not None  and _input is not None:
				self.inputDict[key] = _input
				self.formlayout.addRow(_label, _input)

	def render_default(self):
		if  hasattr(self.parent, 'search_필수kyes'):	
			self.필수keys = self.parent.search_필수kyes[0]	
			value = len(self.필수keys) == 0
		else : value = False
		self.PB_search.setEnabled( value )



	
	#### 😀😀 경우에 따라서 editing
	def triggerConnect(self):
		self.PB_search.clicked.connect(self.slot_PB_search)
		self.PB_cancel.clicked.connect (lambda:self.close())

		if bool(self.inputDict):
			for (key, _) in self.parent.search_type.items():
				input = self.inputDict[key]
				if isinstance( input, QLineEdit ) :
					input.textChanged.connect(self.slot_textChanged)

				elif isinstance(input, QDateEdit):
					input.dateChanged.connect(self.slot_dateChanged)

			


	########################################
	def _get_value(self, key):
		value = Object_Get_Value(self.inputDict[key])
		return value.get()

	##### Data class에서 search_type, search_msg, search_gen_by_key에 의해 생성됨
	def __gen_element(self, key=str, value=None):
		setattr(self, key+'_label', QLabel() )
		label = getattr(self, key+'_label' )
		label.setText(key)
		setattr(self, key+'_input', eval(value) if len(value) >2 else QLineEdit() )
		input:QWidget = getattr(self, key+'_input' )
		input.setObjectName (key)

		return self.__gen_by_key(key, value, label, input)

	def __gen_by_key(self, key=str, value=None, label:object=None, input:object=None):
		if (eval_list :=self.parent.search_gen_by_key.get(key ) ) is not None : 
			for command in eval_list:
				eval(f"input.{command}")
			
		self.inputDict[key] = input
		return (label, input)


	##################
	#### slots######
	def slot_PB_search(self):		
		search_msg = {}
		for key , obj in self.inputDict.items():
			search_msg[key] = self._get_value(key)

		self.signal.emit(search_msg)
		self.close()

	def slot_textChanged(self):
		if ( txt:= self.sender().text() ) :
			self.PB_search.setStyleSheet(self.st.edit_)
			self.sender().setStyleSheet(self.st.edit_)
		else : 
			self.PB_search.setStyleSheet(self.st.edit_enable)
			self.sender().setStyleSheet(self.st.edit_enable)

		if self.필수keys : self.check_필수keys(self.sender(), txt)

	def slot_dateChanged(self):
		self.sender().setStyleSheet(self.st.edit_)

		self.user_defined_dateChanged_check(self.sender())
	
	def check_필수keys(self, obj:QWidget, txt:str):
		if obj.objectName() in self.필수keys and len(txt) > 0:
			self.PB_search.setEnabled(True)
		else: 
			self.PB_search.setEnabled(False)


	###😀😀
	def user_defined_dateChanged_check(self, obj:QWidget ):
		"""
		일일보고: from_일자, to_일자에 대해 진행함
		"""
		key = obj.objectName()
		input = self.inputDict[key]
		if not isinstance( input, QDateEdit ): return

		value = input.date()
		match key:
			case 'from_일자':
				self.inputDict['to_일자'].setMinimumDate(value)	
				# self.inputDict['to_일자'].setMaximumDate(value.addMonths(1))

			case 'to_일자':
				# self.inputDict['from_일자'].setMinimumDate(value.addMonths(-1))	
				self.inputDict['from_일자'].setMaximumDate(value)

		if self.inputDict['from_일자'].date() < self.inputDict['to_일자'].date().addMonths(-3):
			value_to = self.inputDict['from_일자'].date().addMonths(3)
			self.inputDict['to_일자'].setDate(value_to)

	def deleteLayout(self, cur_lay):
		# QtWidgets.QLayout(cur_lay)
		
		if cur_lay is not None:
			while cur_lay.count():
				item = cur_lay.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					self.deleteLayout(item.layout())
			sip.delete(cur_lay)