from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData_품질경영_부적합내용:
	header = None	#### none 이면 header_type keys 
	header_type = {
			'id' : '___',
			'품목': '___',
			'부적합수량': '___',
			'원인' : '___',
			'귀책부서': '___',
			'조치방안': '___',
			'조치일정':  '___',
			# '표시순서': '___'

		}
	no_Edit = []
	hidden_column = [] ###['id', '생산capa','등록자',]
	pageSize = 100
	suffix = f'?page_size={pageSize}'
	search_msg = {}	
	

	def __init__(self):
		super().__init__()	
		self.form_type = self._get_form_type()
		self.menu = Table_menu()
		
		self.table_Sorting = False
		
		self.h_header_context_menu = self.menu.generate(
			[ 'New','Delete',]
		)
		self.v_header_context_menu = self.menu.generate(
			[]
		)
	
	def _get_form_type(self):
		return {
			"제목"  : "QLineEdit(parent)",
			"구분": "QComboBox(parent)",
			"proj_No" : "QLineEdit(parent)",
			"수량": "QSpinBox(parent)",
			"납기일":  "QDateEdit(parent)",
			"고객사" : "Combo_LineEdit(parent)",
			"담당"  : "QLineEdit(parent)",
		}
	
	def _get_default_data(self) -> list:
		return [
			{
                'id' : -1,
                '품목': '',
                '부적합수량': '',
                '원인' : '',
                '귀책부서': '',
                '조치방안': '',
                '조치일정':  '',
			}, 

		]
