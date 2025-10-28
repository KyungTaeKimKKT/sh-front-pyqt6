import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Class_Utils:
	def init_attributes(self, **kwargs) ->None:
		for key, value in kwargs.items():
			setattr( self, key, value)