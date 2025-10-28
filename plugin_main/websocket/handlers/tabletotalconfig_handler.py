from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO
import modules.user.utils as utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class Mixin_TableTotalConfigHandler:
    def on_message_handle(self, msg:dict):
        self.msg = copy.deepcopy(msg)
        if not self.check_is_available(msg):
            return 
        self._parse_message(msg)
        try: 
            match self._main_type:
                case 'init':
                    if self._sub_type == 'response' and self._action == 'init':
                        self._handle_init()
                ### 밑에 case 는 reserver 상태임:
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case _:
                    logger.info(f"TableConfigHandler : handle : {self.action} 처리 안함")
                    return
            
        except Exception as e:
            logger.error(f"TableConfig Handler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_init(self):
        """ init 처리 """
        prev = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG)
        INFO.ALL_TABLE_TOTAL_CONFIG = copy.deepcopy(self._message )
        print ( 'tabletotal change: ', prev == INFO.ALL_TABLE_TOTAL_CONFIG )
        self.event_bus.publish(f"{GBus.TABLE_TOTAL_REFRESH}", True)

        if self.is_first:
            self.is_first = False
            return
        else:
            if INFO._get_is_app_admin():
                _text = """
                            <div style="
                                font-weight: bold; 
                                color: darkgreen; 
                                background-color: #f0fff0; 
                                border: 1px solid #a0d0a0; 
                                border-radius: 5px; 
                                padding: 8px; 
                                font-size: 12pt;
                                line-height: 1.4;
                            ">
                            Table 설정 INIT 완료:<br>
                            app 운영중에 INIT 될 때만 발생됩니다.<br>
                            이 메세지는 app관리자에게만 보입니다.<br>
                            </div>
                            """
                utils.generate_QMsg_Information(
                        INFO.MAIN_WINDOW, 
                        title=" Table 설정 INIT", 
                        text=_text, 
                        autoClose=2000, 
                        style='INFORMATION'
                    )

        # if INFO.IS_DEV and  INFO._get_is_table_config_admin():
        #     utils.generate_QMsg_Information(
        #         INFO.MAIN_WINDOW, 
        #         title="TABLE_TOTAL_CONFIG INIT", 
        #         text="TABLE_TOTAL_CONFIG INIT 완료", 
        #         autoClose=1000, 
        #         style='INFORMATION'
        #     )

    
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

class TableTotalConfigHandler_V2(Mixin_TableTotalConfigHandler, Base_WSMessageHandler_V2):
    pass


class TableTotalConfigHandler_No_Thread(Mixin_TableTotalConfigHandler, Base_WSMessageHandler_No_Thread):
    pass


class TableTotalConfigHandler(Base_WSMessageHandler):
    

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
            
            # ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            # logger.info(f" : handle : {self.event_name} PUB 완료 : { len(INFO.ALL_TABLE_TOTAL_CONFIG)}")
            self.event_bus.publish(
                self.event_name, 
                True
            )

        except Exception as e:
            logger.error(f"TableConfig Handler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_init(self):
        """ init 처리 """
        INFO.ALL_TABLE_TOTAL_CONFIG = self.msg.get('message')   
        # logger.info(f"INFO.ALL_TABLE_TOTAL_CONFIG : {INFO.ALL_TABLE_TOTAL_CONFIG}")
        # logger.warning(f"INFO.ALL_TABLE_TOTAL_CONFIG : {type(INFO.ALL_TABLE_TOTAL_CONFIG)}")
        # config_list = []
        # # import time
        # # s = time.perf_counter()
        # ### 호환성을 위해 INFO.ALL_TABLE_CONFIG 유지함.
        # for _dict in INFO.ALL_TABLE_TOTAL_CONFIG:
        #     config_list.extend(_dict.get('config'))
        # INFO.ALL_TABLE_CONFIG = config_list     
        # # e = time.perf_counter()
        # # logger.warning (f"ALL_TABLE_CONFIG : handle_init:  publish : 1000*(e-s) : {1000*(e-s)} msec")


        # # logger.debug(f"INFO.ALL_TABLE_CONFIG : handle_init:  publish : {GBus.TABLE_TOTAL_REFRESH}")
        # # s = time.perf_counter()
        # INFO.MAP_TableName_To_TableConfigApiDatas = {_dict.get('table_name'):_dict.get('config', []) for _dict in INFO.ALL_TABLE_TOTAL_CONFIG}
        # for table_name, config_api_datas in INFO.MAP_TableName_To_TableConfigApiDatas.items():
        # INFO.MAP_TableName_To_Menus = {_dict.get('table_name'):_dict.get('menus', []) for _dict in INFO.ALL_TABLE_TOTAL_CONFIG}
        # e = time.perf_counter()
        # logger.warning (f"ALL_TABLE_CONFIG :MAPPING TIME : 1000*(e-s) : {1000*(e-s)} msec")
        self.event_bus.publish(f"{GBus.TABLE_TOTAL_REFRESH}", True)
        if INFO._get_is_table_config_admin():
            utils.generate_QMsg_Information(
                INFO.MAIN_WINDOW, 
                title="TABLE_TOTAL_CONFIG INIT", 
                text="TABLE_TOTAL_CONFIG INIT 완료", 
                autoClose=1000, 
                style='INFORMATION'
            )

    
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