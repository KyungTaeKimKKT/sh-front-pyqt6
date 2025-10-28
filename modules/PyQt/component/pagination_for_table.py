from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.component.ui.Ui_pagination_for_table import Ui_Form
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value,Object_ReadOnly

import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Pagination_for_table(QWidget, Ui_Form , Qwidget_Utils):
	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.init_attributes(**kwargs)
		self.setupUi(self)
		self.init_inputDict()
		self.trigger_style_inputDict_textChanged()
		self.hide()

	def init_inputDict(self):
		self.inputDict = {
			'countOnPage' : self.comboBox_table_row,
			'current_Page' : self.comboBox_curPage,
		}
	
	# def run(self):
	# 	self.setupUi()
	# 	self.init_inputDict()
	# 	self.trigger_style_inputDict_textChanged()

	def _setValue(self, valueDict:dict):
		"""  valueDict = {'links': {'next': None, 'previous': None}, 'countTotal': 2, 'countOnPage': 25, 'current_Page': 1, 'total_Page': 1} 형태"""
		if not valueDict : return 
		self.comboBox_curPage.addItems ( [ str(i) for i in range(1, valueDict['total_Page'] + 1) ] )

		for key, value in valueDict.items():
			match key:
				case 'countOnPage' | 'current_Page' :
					Object_Set_Value( self.inputDict[key], str(value))
				case  'countTotal' :
					self.label_search_result.setText( f" {value}건" )
				case 'total_Page':
					self.label_totalPage.setText( f"전체 {value} Page")
		self.show()

	