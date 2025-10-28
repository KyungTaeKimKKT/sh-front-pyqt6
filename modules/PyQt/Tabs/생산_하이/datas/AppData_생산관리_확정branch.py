from PyQt6.QtCore import QDate
from datetime import datetime, timedelta

from modules.PyQt.Tabs.TableVeiw_Menu_Generation import Table_menu
import traceback
from modules.logging_config import get_plugin_logger


BASE_생산관리_HEADER_TYPE = {
			'id' : 'QLineEdit(parent)',		
			"고객사": "QLineEdit(parent)",
			"job_name" : "QLineEdit(parent)",
			"proj_No": "QLineEdit(parent)",		
			"생산형태": "QLineEdit(parent)",	
			"작지유무" :"QCheckBox(parent)",
			"구분": "QLineEdit(parent)",	
			
            "제품분류" :'QLineEdit(parent)',	
			"최종납기일" : "My_DateEdit(parent)",
			"공정_완료계획일": "My_DateEdit(parent)",
			"공정" : 'QLineEdit(parent)',	
			"작업명" : 'QLineEdit(parent)',	
			"계획수량" : "My_SpinBox(parent)",
			
	

}



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData_생산관리_확정branch  :
	header = None	#### none 이면 header_type keys 
	header_type = BASE_생산관리_HEADER_TYPE
	all_list = list(BASE_생산관리_HEADER_TYPE.keys())
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
		key_list = list(BASE_생산관리_HEADER_TYPE.keys() )
		key_delete_list = ['id', '작성일']
		form_type = { key : BASE_생산관리_HEADER_TYPE.get(key, None) for key in key_list if key not in key_delete_list }
		return form_type
			