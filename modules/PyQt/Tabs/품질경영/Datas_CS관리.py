from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger


BASE_CS_HEADER_TYPE = {
			'id' : '___',
			'고객명':'QLineEdit(parent)',
			'Elevator사': 'Combo_LineEdit(parent)',
			'현장명':'QLineEdit(parent)',
			'진행현황': 'QLineEdit(parent)',
			'el수량': 'QSpinBox(parent)',
			'운행층수': 'QSpinBox(parent)',
			'불만요청사항' : 'QTextEdit(parent)',
			'claim_파일수': 'QSpinBox(parent)',
			'고객연락처':'QLineEdit(parent)',
			'등록자':'QLineEdit(parent)',
			'등록일':'QDateEdit(parent)',
			'차수' : 'QSpinBox(parent)',
			'품질비용':'QSpinBox(parent)',
			'대책활동수':'QSpinBox(parent)',
			'대책활동파일수': 'QSpinBox(parent)',
			# 'claim_파일수': 'QSpinBox(parent)',

			# 'actions'			
			# 'action_files'
			# 'clamin_files'
}

# BASE_CS_HEADER_TYPE = {
# 			'id' : 'QLineEdit(parent)',
# 			# 'NCR_fk'
# 			'소재비' : 'QSpinBox(parent)',
# 			'의장비' : 'QSpinBox(parent)',
# 			'판금' : 'QSpinBox(parent)',
# 			'설치비' : 'QSpinBox(parent)',		
# 			'출장비' : 'QSpinBox(parent)',
# 			'합계' : 'QSpinBox(parent)',

# }


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData_CS_관리:
	header = None	#### none 이면 header_type keys 
	header_type = BASE_CS_HEADER_TYPE
	
	no_Edit = list(BASE_CS_HEADER_TYPE.keys() ) #['id', 'claim_파일수','등록자','등록일','대책활동수','대책활동파일수' ]  #list(BASE_CS_HEADER_TYPE.keys() ) #['id','claim_파일수']
	hidden_column = [] ###['id', '생산capa','등록자',]
	pageSize = 25
	suffix = f'?page_size={pageSize}'

	search_필수kyes=['search'], ### 24.7.9 현재는 'search' textchange만 구현
	search_type = {
		'search' : 'QLineEdit()',
		# 'from_일자':'QDateEdit()',
		# 'to_일자': 'QDateEdit()',
	}
	search_msg = {}	
	search_gen_by_key = {
		'search' : [
			"setPlaceholderText('검색어를 넣으세요')",
			"setToolTip('검색어를 있어야 검 검색합니다')"
		],
	}

	def __init__(self):
		super().__init__()	
		self.form_type = self._get_form_type()
		self.menu = Table_menu()
		
		self.table_Sorting = False
		
		self.h_header_context_menu = self.menu.generate(
			[ '작성완료','seperator', 'Form_New','Form_Edit','Form_View','seperator',
			'활동현황_추가','활동현황_보기', 'seperator',
			'File첨부', 'seperator',
			'Delete','seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = {}
	
	def _get_form_type(self):
		key_list = list(BASE_CS_HEADER_TYPE.keys() )
		key_delete_list = ['id','진행현황','claim_파일수','대책활동수','대책활동파일수','등록자','등록일']
		form_type = { key : BASE_CS_HEADER_TYPE.get(key, None) for key in key_list if key not in key_delete_list }
		return form_type
			
		
		return {
			'일자': 'QDateEdit(parent)',
			'업무내용': 'QPlainTextEdit(parent)',
			'소요시간' : 'QDoubleSpinBox(parent)',
			'주요산출물': 'QPlainTextEdit(parent)',
			'비고':  'QPlainTextEdit(parent)',
		}

	def _get_form_choices_고객사(self):
		return {
			'현대' :'현대EL',
			'OTS' : 'OTIS',
			'TKE' : 'TKE',
			'기타' : '기타',

		}

	def _get_form_choices_구분(self):
		return {
			'NE' :'NE',
			'MOD' : 'MOD',
			'기타' : '기타',

		}


class AppData_CS_등록(AppData_CS_관리):
	def __init__(self):
		super().__init__()	
		self.h_header_context_menu = self.menu.generate(
			[ '작성완료','seperator', 'Form_New','Form_Edit','Form_View','seperator',
			 'seperator',
			'Delete','seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = {}

class AppData_CS_활동(AppData_CS_관리):
	def __init__(self):
		super().__init__()	
		self.h_header_context_menu = self.menu.generate(
			[ 
			'활동종료', 'seperator','활동현황_추가','활동현황_보기', 
			'seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = {}


class AppData_CS_이력조회(AppData_CS_관리):
	def __init__(self):
		super().__init__()	

		self.table_Sorting = True
		self.h_header_context_menu = self.menu.generate(
			[ 
			'seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = self.menu.generate(
			['Set_row_span', 'Reset_row_span','seperator',]
		)