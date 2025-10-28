from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from django.db import transaction

import time

from local_db.models import Table_Config

from info import Info_SW as INFO
from config import Config as APP

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class API_Worker_Send(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            start_time = time.time()

            ### 1. api data POST
            is_ok, _json = APP.API.post(
                url= INFO.URL_CONFIG_TABLENAME + 'get_table_list/',
                data=post_data
            )
            if not is_ok:
                raise Exception('API 호출 실패')

            ### 2. table_config 저장
            bulk_list = [
                Table_Config( **_dict ) for _dict in _json['result']
            ]
            with transaction.atomic():
                Table_Config.objects.all().delete()
                Table_Config.objects.bulk_create(bulk_list)
            
            ### ram 저장
            # for _dict in _json['result']:
            #     INFO.TABLE_CONFIG[_dict['table_name']] = _dict
            ### 3. 완료 시그널 발송
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def get_post_data_for_query(self):
        result = []
        for _dict in INFO.APP_권한:
            result.append ( f"{_dict['div']}_{_dict['name']}_appID_{_dict['id']}" )
        return result