from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Mixin_PingHandler:
    def handle(self, msg: Union[dict,list, None]):
        """ app권한 message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)

        try: 
            self.type = msg.get('type')
            # logger.info(f" : handle : {self.type} 수신")
            # self.event_name = f"{self.url}"
            # match self.action:
            #     case 'init':
            #         self._handle_init()
            #     case 'create':
            #         self._handle_create()
            #     case 'update':
            #         self._handle_update()
            #     case 'delete':
            #         self._handle_delete()
            #     case _:
            #         logger.info(f"AppAuthorityHandler : handle : {self.action} 처리 안함")
            #         return
            
            ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            # logger.info(f" : handle : {self.event_name} PUB 완료")
            # self.event_bus.publish(
            #     self.event_name, 
            #     True
            # )

        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())


class PingHandler_No_Thread(Mixin_PingHandler, Base_WSMessageHandler_No_Thread):
    pass

class PingHandler_V2(Base_WSMessageHandler_V2):
    def on_message_handle(self, msg:dict):
        """ ping 패킷 수신 처리 
            현재, ws 연결 상태 확인 용도로 사용되므로 ws_async_worker 에서 publish 함. 여기선 pass
        """
        pass

class PingHandler(Base_WSMessageHandler):
    

    def handle(self, msg: Union[dict,list, None]):
        """ app권한 message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)

        try: 
            self.type = msg.get('type')
            # logger.info(f" : handle : {self.type} 수신")
            # self.event_name = f"{self.url}"
            # match self.action:
            #     case 'init':
            #         self._handle_init()
            #     case 'create':
            #         self._handle_create()
            #     case 'update':
            #         self._handle_update()
            #     case 'delete':
            #         self._handle_delete()
            #     case _:
            #         logger.info(f"AppAuthorityHandler : handle : {self.action} 처리 안함")
            #         return
            
            ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            # logger.info(f" : handle : {self.event_name} PUB 완료")
            # self.event_bus.publish(
            #     self.event_name, 
            #     True
            # )

        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())
 