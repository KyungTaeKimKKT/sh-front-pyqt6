from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy, json

from plugin_main.websocket.handlers.base_handlers import  (
    Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

import modules.user.utils as utils

class Mixin_ServerMonitorHandler:
    def on_message_handle(self, msg: dict):
        if not self.check_is_receiver(msg):
            return        
        self.msg = copy.deepcopy(msg)
        self.set_latest_msg(self.msg.copy())
        self._parse_message(self.msg)
        # print(f"ServerMonitorHandler : handle : {self.msg}")
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
        self.set_published_msg( self._message.copy())
        self.event_bus.publish(
                    self.event_name, 
                    self._message.copy()
        )


class ServerMonitorHandler_V2(Mixin_ServerMonitorHandler, Base_WSMessageHandler_V2):
    pass


class ServerMonitorHandler_No_Thread(Mixin_ServerMonitorHandler, Base_WSMessageHandler_No_Thread):
    pass


# class ServerMonitorHandler(Base_WSMessageHandler):
    

#     def handle(self, msg: Union[dict,list, None]):
#         """ 서버 모니터링 message 처리 by action
#             action : init, update, delete, create, ... 그외는 필요시
#         """
#         self.msg = copy.deepcopy(msg)
#         print(f"ServerMonitorHandler : handle : {self.msg}")

#         try: 
#             # logger.debug(f"ServerMonitorHandler : handle : {self.msg}")
#             self.action = msg.get('action')
#             self.event_name = f"{self.url}"
#             self.datas = msg.get('message')
#             logger.info(f"ServerMonitorHandler : handle : {self.datas}")
#             # self.app권한 = self.get_app권한_BY_Owner( msg.get('message') )
#             match self.action:
#                 case 'init':
#                     self._handle_init()
#                 # case 'create':
#                 #     self._handle_create()
#                 # case 'update':
#                 #     self._handle_update()
#                 # case 'delete':
#                 #     self._handle_delete()
#                 case _:
#                     logger.info(f"AppAuthorityHandler : handle : {self.action} 처리 안함")
#                     return
            
#             ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
#             print(f"ServerMonitorHandler : handle : {self.event_name}")
#             print(f"ServerMonitorHandler : handle : {self.datas}")
#             self.event_bus.publish(
#                 self.event_name, 
#                 self.datas
#             )

#         except Exception as e:
#             logger.error(f"AppAuthorityHandler : handle : {e}")
#             logger.error(traceback.format_exc())
    
#     def _handle_init(self):
#         """ init 처리 """
#         pass
#         # logger.info(f"ServerMonitorHandler : _handle_init : {self.datas}")


    
#     def _handle_update(self):
#         """ update 처리 """
#         utils.generate_QMsg_Information(
#             INFO.MAIN_WINDOW, 
#             title="App권한 업데이트", 
#             text="App권한 업데이트 완료", 
#             autoClose=1000, 
#             style='INFORMATION'
#         )
#         app권한 = self.msg.get('message')
#         if isinstance(app권한, dict):
#             self._update_app권한(app권한)
#         elif isinstance(app권한, list):
#             for app권한_obj in app권한:
#                 self._update_app권한(app권한_obj)
    
#     def _handle_delete(self):
#         """ delete 처리 """
#         app권한 = self.msg.get('message')
#         if isinstance(app권한, dict):
#             self._delete_app권한(app권한)
#         elif isinstance(app권한, list):
#             for app권한_obj in app권한:
#                 self._delete_app권한(app권한_obj)

#     def _handle_create(self):
#         """ create 처리 """
#         app권한 = self.msg.get('message')
#         if isinstance(app권한, dict):
#             self._create_app권한(app권한)
#         elif isinstance(app권한, list):
#             for app권한_obj in app권한: 
#                 self._create_app권한(app권한_obj)


#     def _create_app권한(self, app권한_dict:dict):
#         if INFO.USERID in app권한_dict.get('user_pks'):
#             INFO.APP_권한.append(app권한_dict)
#             INFO.APP_권한 = sorted(INFO.APP_권한, key=lambda x: x.get('순서'))

#     def get_app권한_BY_Owner(self, app권한:Optional[list[dict]] = None ) -> list[dict]:
#         """
#             app권한 목록을 받아서 처리
#         """
#         try:
#             app권한 = app권한 or self.msg.get('message')
#             app권한 = self.pre_conversion(app권한)

#             if not app권한:
#                 return []
#             owner_app권한 = [ obj for obj in app권한 if INFO.USERID in obj.get('user_pks') ]
#             if INFO.IS_DEV:
#                 pass
#             else:
#                 owner_app권한 = [ obj for obj in owner_app권한 if  obj.get('is_Active') and not obj.get('is_dev') ]

#             return owner_app권한
        
#         except Exception as e:
#             logger.error(f"get_app권한_BY_Owner 오류: {e}")
#             logger.error(traceback.format_exc())
    
#     def _update_app권한(self,  app권한_dict:dict):
#         del_idx:Optional[int] = None
#         for idx, app권한 in enumerate(INFO.APP_권한):
#             if app권한.get('id') == app권한_dict.get('id'):
#                 if INFO.USERID in app권한_dict.get('user_pks') :
#                     app권한.update(app권한_dict)
#                 else:
#                     del_idx = idx
#         if del_idx is not None:
#             del INFO.APP_권한[del_idx]

#     def _delete_app권한(self, app권한_dict:dict):
#         del_idx:Optional[int] = None
#         for idx, app권한 in enumerate(INFO.APP_권한):
#             if app권한.get('id') == app권한_dict.get('id'):
#                 del_idx = idx
#                 break
#         if del_idx is not None:
#             del INFO.APP_권한[del_idx]

#     def pre_conversion(self, app권한) -> dict:
#         if isinstance(app권한, dict):
#             return app권한
#         elif isinstance(app권한, list):
#             return app권한
#         elif isinstance(app권한, str):
#             return json.loads(app권한)
        
#         else:
#             raise ValueError(f"app권한 형식 오류: {type(app권한)}")