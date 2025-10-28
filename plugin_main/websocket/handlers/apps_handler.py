from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy, json

from plugin_main.websocket.handlers.base_handlers import  (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

import modules.user.utils as utils


class Mixin_AppsHandler:

    def get_event_name(self) -> str:
        return self.event_name
        # return f"{self.url}:{self._subject}".strip()
        

    def on_message_handle(self, msg:dict):
        self.msg = copy.deepcopy(msg)
        # print (f"AppsHandler_V2 : on_message_handle : {self.msg}")
        if not self.check_is_available(msg):
            return 
        
        self._parse_message(msg)

        try: 
            match self._main_type:
                case 'init':
                    if self._sub_type == 'response' and self._action == 'init':
                        self._handle_init()
                ### 밑에 case 는 reserver 상태임:
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case 'create':
                    self._handle_create()

                case _:
                    logger.info(f"AppAuthorityHandler : handle : {self.action} 처리 안함")
                    return
            
        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_init(self):
        """ init 처리 """
        print (f"AppsHandler_V2 : _handle_init : {self._message}")

        #### ✅ 처리 완료 이벤트 발송: toolbar_manager.render_toolbar(action)에서 수신
        self.event_bus.publish(
            self.get_event_name(), 
            copy.deepcopy(self.msg)
        )

    def _handle_update(self):
        """ update 처리 """
        # print (f"AppsHandler_V2 : _handle_update : {self._message}")
        self.event_bus.publish(
            self.get_event_name(), 
            copy.deepcopy(self.msg)
        )

class AppsHandler_V2(Mixin_AppsHandler, Base_WSMessageHandler_V2):
    pass

class AppsHandler_No_Thread(Mixin_AppsHandler, Base_WSMessageHandler_No_Thread):
    pass

