from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData_생산계획입력:
	header = None	#### none 이면 header_type keys 
	header_type = {
			'id' : '___',
			'line_no': '___',
			'생산capa': '___',
			'start_time' : 'QTimeEdit(parent)',
			'end_time': 'QTimeEdit(parent)',
			'plan_qty':  'QSpinBox(parent)',
			'등록자': '___',

		}
	no_Edit = ['id','line_no','생산capa','등록자']
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
			[ 'seperator','Export_to_Excel',
				 'seperator', 
				'Form_New']
		)
		self.v_header_context_menu = {}
	
	def _get_form_type(self):
		return {
			'일자': 'QDateEdit(parent)',
			'업무내용': 'QPlainTextEdit(parent)',
			'소요시간' : 'QDoubleSpinBox(parent)',
			'주요산출물': 'QPlainTextEdit(parent)',
			'비고':  'QPlainTextEdit(parent)',
		}

