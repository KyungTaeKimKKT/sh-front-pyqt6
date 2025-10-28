from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy

from plugin_main.websocket.handlers.base_handlers import Base_WSMessageHandler

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TableConfigHandler(Base_WSMessageHandler):
    

    def handle(self, msg: Union[dict,list, None]):
        """ tableconfig message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)

        try: 
            self.action = msg.get('action')
            self.event_name = f"{self.url}"
            match self.action:
                case 'init':
                    self._handle_init()
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case _:
                    logger.info(f"TableConfigHandler : handle : {self.action} 처리 안함")
                    return
            
            ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            logger.info(f" : handle : {self.event_name} PUB 완료 : { len(INFO.ALL_TABLE_CONFIG)}")
            self.event_bus.publish(
                self.event_name, 
                True
            )

        except Exception as e:
            logger.error(f"TableConfig Handler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_init(self):
        """ init 처리 """
        INFO.ALL_TABLE_CONFIG = self.msg.get('message')
        logger.info(f" : _handle_init : INFO.ALL_TABLE_CONFIG : {len(INFO.ALL_TABLE_CONFIG)}")

    
    def _handle_update(self):
        """ update 처리 """
        _obj = self.msg.get('message')
        if isinstance(_obj, dict):
            self._update_(_obj)
        elif isinstance( _obj, list):
            for _dict in _obj:
                self._update_(_dict)
    
    def _handle_delete(self):
        """ delete 처리 """
        _obj = self.msg.get('message')
        if isinstance(_obj, dict):
            self._delete_(_obj)
        elif isinstance(_obj, list):
            for _dict in _obj:
                self._delete_(_dict)

    def _handle_create(self):
        """ create 처리 """
        _obj = self.msg.get('message')
        if isinstance(_obj, dict):
            self._create_(_obj)
        elif isinstance( _obj, list):
            for _dict in _obj: 
                self._create_(  _dict)


    def _create_(self, _dict:dict):
        INFO.ALL_TABLE_CONFIG.append(_dict)


   
    def _update_(self,  _dict:dict):
        for idx, _obj in enumerate(INFO.ALL_TABLE_CONFIG):
            if _obj.get('id') == _dict.get('id'):
                _obj.update(_dict)
                break

    def _delete_(self, _dict:dict):
        del_idx:Optional[int] = None
        for idx, _obj in enumerate(INFO.ALL_TABLE_CONFIG):
            if _obj.get('id') == _dict.get('id'):
                del_idx = idx
                break
        if del_idx is not None:
            del INFO.ALL_TABLE_CONFIG[del_idx]