from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger


BASE_NCR_HEADER_TYPE = {
			'id' : 'QLineEdit(parent)',
			'is_배포':'QCheckBox(parent)',
			'발행번호' : 'QLineEdit(parent)',
			'제목' : '___',
			'분류':'___',
			'구분':'___',
			'QCost' : '___',
			'조치사항':'___',
			'귀책공정':'___',			
			'발생일자' : '___',
			'첨부파일수' :'___',
			'발견자' : '___',
			'고객사' : '___',
			'작성일자' : '___',
			'작성자_fk' : '___',
			'현장명': '___',
			'소재' : '___',
			'의장명' : '___',
			'OP'    : '___',
			'자재명' : '___',
			'수량' : '___',
			'단위' : '___',
			# '부적합내용' : '___',
			'부적합상세' : '___',
			'임시조치방안': '___',
			'일정사항' : '___',
			
}

BASE_품질비용_HEADER_TYPE = {
			'id' : 'QLineEdit(parent)',
			# 'NCR_fk'
			'소재비' : 'QSpinBox(parent)',
			'의장비' : 'QSpinBox(parent)',
			'판금' : 'QSpinBox(parent)',
			'설치비' : 'QSpinBox(parent)',		
			'출장비' : 'QSpinBox(parent)',
			'합계' : 'QSpinBox(parent)',

}


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData_품질경영_관리자:
	header = None	#### none 이면 header_type keys 
	header_type = BASE_NCR_HEADER_TYPE
	
	no_Edit = ['id',]
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
			'File첨부', 'seperator',
			'Delete','seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = {}
	
	def _get_form_type(self):
		key_list = list(BASE_NCR_HEADER_TYPE.keys() )
		key_delete_list = ['id', '발생원인','재발방지대책', '첨부파일수','is_배포']
		form_type = { key : BASE_NCR_HEADER_TYPE.get(key, None) for key in key_list if key not in key_delete_list }
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

	def _get_접수디자이너_selector(self) ->list:
		return  self.접수디자이너_selector
