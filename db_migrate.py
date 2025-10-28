from django.core.management import call_command

# ORM 초기화
import db_setting
import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()



call_command('makemigrations', 'local_db')
call_command('migrate', 'local_db')

