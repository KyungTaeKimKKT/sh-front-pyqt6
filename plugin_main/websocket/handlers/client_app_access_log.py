from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy, json

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

import modules.user.utils as utils

class Mixin_ClientAppAccessLogHandler:
    def on_message_handle(self, msg:dict):
        logger.info(f"ClientAppAccessLogHandler : on_message_handle : {self.msg}")

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
                    logger.info(f"NetworkMonitorHandler : handle : {self.msg} 처리 안함")
                    return
        except Exception as e:
            logger.error(f"NetworkMonitorHandler : handle : {e}")
            logger.error(traceback.format_exc())

    def _handle_update(self):
        #### NetworkTopologyViewer.subscribe() 에서 처리함
        self.event_bus.publish(
                    self.event_name, 
                    copy.deepcopy(self._message)
        )

class ClientAppAccessLogHandler(Mixin_ClientAppAccessLogHandler, Base_WSMessageHandler_V2):
    pass

class ClientAppAccessLogHandler_No_Thread(Mixin_ClientAppAccessLogHandler, Base_WSMessageHandler_No_Thread):
    pass


class Mixin_ClientAppAccessDashboardHandler:
    def on_message_handle(self, msg:dict):
        logger.info(f"ClientAppAccessLogHandler : on_message_handle : {msg}")        

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
                    logger.info(f"NetworkMonitorHandler : handle : {self.msg} 처리 안함")
                    return
        except Exception as e:
            logger.error(f"NetworkMonitorHandler : handle : {e}")
            logger.error(traceback.format_exc())

    def _handle_update(self):
        #### NetworkTopologyViewer.subscribe() 에서 처리함
        self.set_latest_msg(self._message.copy())
        self.event_bus.publish(
                    self.event_name, 
                    self._message.copy()
        )

class ClientAppAccessDashboardHandler(Mixin_ClientAppAccessDashboardHandler, Base_WSMessageHandler_V2):
    pass

class ClientAppAccessDashboardHandler_No_Thread(Mixin_ClientAppAccessDashboardHandler, Base_WSMessageHandler_No_Thread):
    pass
