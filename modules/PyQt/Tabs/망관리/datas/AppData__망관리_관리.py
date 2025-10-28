from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger


BASE_망관리_HEADER_TYPE = {
	'id'            : '___',
    '망번호'        : '___',
    '고객사'        : '___',
    '현장명'        : '___',
    '문양'          : '___',
    '의장종류'      : '___',
    '할부치수'      : '___',
    '품명'          : '___',
    '망사'          : '___',
    '사용구분'      : '___',
    '세부내용'      : '___',
    '비고'          : '___',
    'upload_path_1' : '___',
    'upload_path_2' : '___',
    '등록자'        : '___',
    '등록일'        : '___',

}



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData__망관리_관리:
	header = None	#### none 이면 header_type keys 
	header_type = BASE_망관리_HEADER_TYPE
	all_list = list(BASE_망관리_HEADER_TYPE.keys())
	no_Edit = [ name for name in all_list if '납기일' not in name]
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
			[ '작성완료','seperator', 'MRP','seperator', 
			'Form_New_현대','Form_New_OTIS','Form_New_TKE','Form_New_기타', 
			'seperator', 'Form_Edit','Form_View','seperator',
			'File첨부', 'seperator',
			'Delete','seperator','Search','seperator','Export_to_Excel',
				 ]
		)
		self.v_header_context_menu = {}
	
	def _get_form_type(self):
		key_list = list(BASE_망관리_HEADER_TYPE.keys() )
		key_delete_list = ['id', '작성일']
		form_type = { key : BASE_망관리_HEADER_TYPE.get(key, None) for key in key_list if key not in key_delete_list }
		return form_type
			