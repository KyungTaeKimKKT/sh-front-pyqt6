from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy, json

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

from modules.envs.globaldata import GlobalData

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

import modules.user.utils as utils

import platform
def get_font_family():
    return 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic' if platform.system() == 'macOS' else 'NanumGothic'

import matplotlib
matplotlib.rcParams['font.family'] = get_font_family()
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

class Mixin_ServerDB_Status_Handler:
    def on_message_handle(self, msg: dict):
        # print(f"NetworkMonitorHandler_V2 : on_message_handle : {msg}")
        if not self.check_is_receiver(msg):
            return
        
        self.msg = copy.deepcopy(msg)
        self._parse_message(self.msg)

        try:
            match self._main_type:
                case 'celery-notice':
                    if self._sub_type == 'broadcast' and self._action == 'update':
                        self._handle_update()
                
                case _:
                    logger.info(f"{self.__class__.__name__} : handle : {self.msg} 처리 안함")
                    return
        except Exception as e:
            logger.error(f"{self.__class__.__name__} : error : {e}")
            logger.error(traceback.format_exc())

    def _handle_update(self):
        #### .subscribe() 에서 처리함
        # print ( f"ServerDB_Status_Handler_No_Thread : _handle_update :{self.event_name} {self.msg}")
        GlobalData.append_server_db_status(self.msg.copy())
        self.event_bus.publish(
                    self.event_name, 
                    self.msg.copy()
                )
        


class ServerDB_Status_Handler_No_Thread(Mixin_ServerDB_Status_Handler, Base_WSMessageHandler_No_Thread):
    pass

