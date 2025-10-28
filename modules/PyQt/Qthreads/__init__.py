# https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
# import os
# for module in os.listdir(os.path.dirname(__file__)):
#     if module == '__init__.py' or module[-3:] != '.py':
#         continue
#     __import__(module[:-3], locals(), globals())
# del module

from .User_WS_Client import User_WS_Client
from .PlaySound import PlaySound
from .Clock import Clock
from .socket_server import ServerSocket
import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()


