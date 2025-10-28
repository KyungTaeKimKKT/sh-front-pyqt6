from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Search_for_tab(QWidget):
	"""
		kwargs : search_msg , pb_text, placeholder, pageSize
	"""
	signal = pyqtSignal(dict)

	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.search_msg = kwargs.pop ('search_msg', {} )
		self.pb_text = kwargs.pop('pb_text', '한국Elevator 검색')
		self.placeholder = kwargs.pop('placeholder', '검색어를 입력하세요' )
		self.pageSize = kwargs.pop('pageSize', 25)

		self.default_Rows = ['25','50','75','100']

		self.UI()

	def UI(self) -> None:
		self.vlayout = QtWidgets.QVBoxLayout()
		self.no_data_hlayout = QtWidgets.QHBoxLayout()

		self.pb_form_New = QtWidgets.QPushButton(self.pb_text)
		self.pb_form_New.clicked.connect(self.slot_pb_Search_design)
		self.검색_lineEdit = QtWidgets.QLineEdit( self )
		self.검색_lineEdit.setPlaceholderText(self.placeholder)
		self.검색_lineEdit.textChanged.connect(self.slot_textChanged_search)
		if ( search_txt := self.search_msg.get('search', None) ):
			self.검색_lineEdit.setText(search_txt)

		self.no_data_hlayout.addStretch()
		self.no_data_hlayout.addWidget(self.검색_lineEdit)
		self.no_data_hlayout.addStretch()
		self.no_data_hlayout.addWidget(self.pb_form_New)
		self.vlayout.addLayout(self.no_data_hlayout)

		self.검색결과_frame = QFrame(self)
		검색결과layout = QHBoxLayout()
		self.검색결과label = QLabel(self)
		검색결과layout.addWidget(self.검색결과label)
		검색결과layout.addStretch()
		label_pageNo = QLabel(self)
		label_pageNo.setText('현재 Page')
		검색결과layout.addWidget(label_pageNo)
		self.Combo_pageNo = QComboBox(self)
		self.Combo_pageNo.currentTextChanged.connect(self.slot_Page_no_chagned)
		검색결과layout.addWidget(self.Combo_pageNo)
		self.label_total_page = QLabel(self)
		검색결과layout.addWidget(self.label_total_page)

		검색결과layout.addStretch()
		label_pageSize = QLabel(self)
		label_pageSize.setText('Row 수')
		검색결과layout.addWidget(label_pageSize)
		self.Combo_pageSize = QComboBox(self)
		self.Combo_pageSize.addItems(self.default_Rows)

		self.Combo_pageSize.setCurrentText(str(self.pageSize ) ) 
		self.Combo_pageSize.setStyleSheet(ST.edit_)
		self.Combo_pageSize.currentTextChanged.connect(self.slot_Page_size_changed )
		검색결과layout.addWidget(self.Combo_pageSize)
		self.검색결과_frame.setLayout(검색결과layout)

		self.vlayout.addWidget(self.검색결과_frame)

		self.setLayout(self.vlayout)
		
		self.검색결과_frame.hide()
	
	def display_검색결과(self, 검색결과:str, total_Page:int, current_Page:int|None)->None:
		""" 검색결과를 표시함 """
		self.검색결과label.setText(검색결과)
		self.Combo_pageNo.addItems( [ str(i) for i in range(1, total_Page+1)])
		if current_Page :
			self.Combo_pageNo.setCurrentText(str(current_Page))
		else:
			self.Combo_pageNo.setCurrentText('1')
		self.Combo_pageNo.setStyleSheet(ST.edit_)
		self.label_total_page.setText( f"/전체 {total_Page}Page")

		self.검색결과_frame.show()

	def slot_pb_Search_design(self):		
		self.search_msg['search'] = self.검색_lineEdit.text()

		self.signal.emit(self.search_msg)
		# self.run()

	def slot_textChanged_search(self):	
		"""
			deepcopy본을 보내는 것으로
		"""	
		if ( is_editing := bool(self.검색_lineEdit.text()) ):
			self.검색_lineEdit.setStyleSheet( ST.edit_)
		else:
			self.검색_lineEdit.setStyleSheet( ST.edit_enable)

		self.pb_form_New.setEnabled(is_editing)
		
	def slot_Page_no_chagned(self):
		self.search_msg['page'] = self.Combo_pageNo.currentText() 

	def slot_Page_size_changed(self):
		self.pageSize = int(self.Combo_pageSize.currentText() )