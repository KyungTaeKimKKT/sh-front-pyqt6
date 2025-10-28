from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Table_Builder:
    def __init__(self):
        self.api_datas = []
        self.table_name = ''

    def with_api_datas(self, api_datas:list[dict]):
        """ api_datas 설정 """
        self.api_datas = api_datas
        return self


    def with_table_name(self, table_name:str):
        """ table_name 설정 """
        self.table_name = table_name
        return self

