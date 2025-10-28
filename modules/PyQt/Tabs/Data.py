import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class AppData:
    header = None
    header_type = {
			'id' : '___',
			'div': '___',
			'name': '___',
			'url' : '___',
			'api_url': '___',
			'비고':  'QPlainTextEdit(parent)',
			'등록일': 'QDateTimeEdit(parent)',
			'is_Active':'QCheckBox(parent)',
			'is_Run' : 'QCheckBox(parent)',
			'순서' : 'QSpinBox(parent)',
			'user_pks':'___',
			'current_user': '___',
			'app사용자수' : '___',
	}
    no_Edit = ['id','current_user','app사용자수','user_pks','등록일']