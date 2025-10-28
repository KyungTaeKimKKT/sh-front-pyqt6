import os
import django
from django.conf import settings
import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()



# BASE_DIR 설정 (현재 파일의 디렉토리를 기준으로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Django 설정
settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'local_db.sqlite3'),
        }
    },
    INSTALLED_APPS=[
        'local_db'
    ],
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    TIME_ZONE='Asia/Seoul',  # 한국 시간대로 설정
    USE_TZ=False,  # 시간대 인식 비활성화 (로컬 시간 사용)
)

django.setup()

# 이제 DB_PATH 정의 (settings.configure() 호출 후에)
DB_PATH = os.path.join(BASE_DIR, 'local_db.sqlite3')