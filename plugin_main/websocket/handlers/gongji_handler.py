from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
from PyQt6.QtCore import QTimer
import copy, json

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

import modules.user.utils as utils

class Mixin_GongiHandler:
    def is_already_reading(self, msg:dict) -> bool:
        """ 이미 읽은 공지사항인지 체크 메서드 """
        reading_users = msg.get('reading_users', [])
        return INFO.USERID in reading_users
    
    def is_reading_target(self, msg:dict) -> bool:
        """ 읽을 대상인지 체크 메서드 """
        reading_target = msg.get('reading_target', [])
        if isinstance(reading_target, list):
            return INFO.USERID in reading_target
        elif isinstance(reading_target, str):
            return reading_target.lower() == 'all'
        else:
            return False
        
    def is_valid_for_popup(self, msg: dict) -> bool:
        return all( [ bool(msg), 
                     self.is_reading_target(msg), 
                     not self.is_already_reading(msg) 
                     ] )

    def on_message_handle(self, msg:dict):
        """ 공지사항 message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)
        if not self.check_is_available(msg):
            return 
        
        self._parse_message(msg)

        try: 
            match self._main_type:
                case 'init':
                    if self._sub_type == 'notify' and self._action == 'popup':
                        #### 실제 message는 list[dict] 형식이라, dict에서 한번더 검증(popup할건지 말건지)
                        #### self.is_reading_target(msg) , not self.is_already_reading(msg) 체크 후 popup 처리함
                        self._handle_popup()
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case 'popup':
                    self._handle_popup()
                case _:
                    logger.info(f"{self.__class__.__name__} : handle : {self._action} 처리 안함")
                    return
            

        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())

    def _handle_popup(self):
        """ popup 처리 : 공지사항 POPUP 처리 """
        contents = self._message
        if isinstance(contents, dict):
            if self.is_valid_for_popup(contents):
                self.on_open_popup(contents)
        elif isinstance(contents, list):
            for obj in contents:
                if self.is_valid_for_popup(obj):
                    self.on_open_popup(obj)


    def on_open_popup(self, obj:dict):
        """ popup 처리 : 공지사항 POPUP 처리 :  핵심은 qt event loop 처리  """
        QTimer.singleShot(0, lambda: self._show_popup(obj))
    
    def _show_popup(self, obj:dict):
        try:            
            from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지사항_popup import Dialog_공지사항_Popup
            dlg_gongi = Dialog_공지사항_Popup(INFO.MAIN_WINDOW, obj=obj, view_type='notice')
            dlg_gongi.exec()
        except Exception as e:
            logger.error(f"on_gongi_popup: {e}")
            traceback.print_exc()
    
    def _handle_init(self):
        """ init 처리 """

        pass

    
    def _handle_update(self):
        """ update 처리 """
        utils.generate_QMsg_Information(
            INFO.MAIN_WINDOW, 
            title="App권한 업데이트", 
            text="App권한 업데이트 완료", 
            autoClose=1000, 
            style='INFORMATION'
        )
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._update_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한:
                self._update_app권한(app권한_obj)
    
    def _handle_delete(self):
        """ delete 처리 """
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._delete_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한:
                self._delete_app권한(app권한_obj)

    def _handle_create(self):
        """ create 처리 """
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._create_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한: 
                self._create_app권한(app권한_obj)


    def _create_app권한(self, app권한_dict:dict):
        if INFO.USERID in app권한_dict.get('user_pks'):
            INFO.APP_권한.append(app권한_dict)
            INFO.APP_권한 = sorted(INFO.APP_권한, key=lambda x: x.get('순서'))

    def get_app권한_BY_Owner(self, app권한:Optional[list[dict]] = None ) -> list[dict]:
        """
            app권한 목록을 받아서 처리
        """
        try:
            app권한 = app권한 or self.msg.get('message')
            app권한 = self.pre_conversion(app권한)

            if not app권한:
                return []
            owner_app권한 = [ obj for obj in app권한 if INFO.USERID in obj.get('user_pks') ]
            if INFO.IS_DEV:
                pass
            else:
                owner_app권한 = [ obj for obj in owner_app권한 if  obj.get('is_Active') and not obj.get('is_dev') ]

            return owner_app권한
        
        except Exception as e:
            logger.error(f"get_app권한_BY_Owner 오류: {e}")
            logger.error(traceback.format_exc())
    
    def _update_app권한(self,  app권한_dict:dict):
        del_idx:Optional[int] = None
        for idx, app권한 in enumerate(INFO.APP_권한):
            if app권한.get('id') == app권한_dict.get('id'):
                if INFO.USERID in app권한_dict.get('user_pks') :
                    app권한.update(app권한_dict)
                else:
                    del_idx = idx
        if del_idx is not None:
            del INFO.APP_권한[del_idx]

    def _delete_app권한(self, app권한_dict:dict):
        del_idx:Optional[int] = None
        for idx, app권한 in enumerate(INFO.APP_권한):
            if app권한.get('id') == app권한_dict.get('id'):
                del_idx = idx
                break
        if del_idx is not None:
            del INFO.APP_권한[del_idx]

    def pre_conversion(self, app권한) -> dict:
        if isinstance(app권한, dict):
            return app권한
        elif isinstance(app권한, list):
            return app권한
        elif isinstance(app권한, str):
            return json.loads(app권한)
        
        else:
            raise ValueError(f"app권한 형식 오류: {type(app권한)}")


class GongiHandler_V2(Mixin_GongiHandler, Base_WSMessageHandler_V2):
    pass

class GongiHandler_No_Thread(Mixin_GongiHandler, Base_WSMessageHandler_No_Thread):
    pass

 
class GongiHandler(Base_WSMessageHandler):
    

    def handle(self, msg: Union[dict,list, None]):
        """ 공지사항 message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        if INFO.IS_DEV:
            logger.info(f"GongiHandler : handle : type :{type(msg)}: msg:{msg}")
        self.msg = copy.deepcopy(msg)

        try: 
            if not self.check_is_receiver(msg):
                return
            
            self.action = msg.get('action')
            self.event_name = f"{self.url}"
            if INFO.IS_DEV:
                print(f"GongiHandler : handle : {self.action} ")
            # self.app권한 = self.get_app권한_BY_Owner( msg.get('message') )
            match self.action:
                case 'init':
                    self._handle_init()
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case 'popup':
                    self._handle_popup()
                case _:
                    logger.info(f"{self.__class__.__name__} : handle : {self.action} 처리 안함")
                    return
            
            ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            # utils.generate_QMsg_Information(
            #     INFO.MAIN_WINDOW, 
            #     title="공지사항 업데이트", 
            #     text="공지사항 업데이트 완료", 
            #     autoClose=1000, 
            #     style='INFORMATION'
            # )
            # logger.info(f" : handle : {self.event_name} PUB 완료 : { len(INFO.APP_권한)}")
            # self.event_bus.publish(
            #     self.event_name, 
            #     self.action
            # )

        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())

    def _handle_popup(self):
        """ popup 처리 : 공지사항 POPUP 처리 """
        contents = self.msg.get('message')
        if isinstance(contents, dict):
            if contents:
                self.on_open_popup(contents)
        elif isinstance(contents, list):
            for obj in contents:
                if obj:
                    self.on_open_popup(obj)


    def on_open_popup(self, obj:dict):
        """ popup 처리 : 공지사항 POPUP 처리 """
        try:            
            from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지사항_popup import Dialog_공지사항_Popup
            dlg_gongi = Dialog_공지사항_Popup(INFO.MAIN_WINDOW, obj=obj, view_type='notice')
            dlg_gongi.exec()
        except Exception as e:
            logger.error(f"on_gongi_popup: {e}")
            traceback.print_exc()
    
    def _handle_init(self):
        """ init 처리 """

        pass

    
    def _handle_update(self):
        """ update 처리 """
        utils.generate_QMsg_Information(
            INFO.MAIN_WINDOW, 
            title="App권한 업데이트", 
            text="App권한 업데이트 완료", 
            autoClose=1000, 
            style='INFORMATION'
        )
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._update_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한:
                self._update_app권한(app권한_obj)
    
    def _handle_delete(self):
        """ delete 처리 """
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._delete_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한:
                self._delete_app권한(app권한_obj)

    def _handle_create(self):
        """ create 처리 """
        app권한 = self.msg.get('message')
        if isinstance(app권한, dict):
            self._create_app권한(app권한)
        elif isinstance(app권한, list):
            for app권한_obj in app권한: 
                self._create_app권한(app권한_obj)


    def _create_app권한(self, app권한_dict:dict):
        if INFO.USERID in app권한_dict.get('user_pks'):
            INFO.APP_권한.append(app권한_dict)
            INFO.APP_권한 = sorted(INFO.APP_권한, key=lambda x: x.get('순서'))

    def get_app권한_BY_Owner(self, app권한:Optional[list[dict]] = None ) -> list[dict]:
        """
            app권한 목록을 받아서 처리
        """
        try:
            app권한 = app권한 or self.msg.get('message')
            app권한 = self.pre_conversion(app권한)

            if not app권한:
                return []
            owner_app권한 = [ obj for obj in app권한 if INFO.USERID in obj.get('user_pks') ]
            if INFO.IS_DEV:
                pass
            else:
                owner_app권한 = [ obj for obj in owner_app권한 if  obj.get('is_Active') and not obj.get('is_dev') ]

            return owner_app권한
        
        except Exception as e:
            logger.error(f"get_app권한_BY_Owner 오류: {e}")
            logger.error(traceback.format_exc())
    
    def _update_app권한(self,  app권한_dict:dict):
        del_idx:Optional[int] = None
        for idx, app권한 in enumerate(INFO.APP_권한):
            if app권한.get('id') == app권한_dict.get('id'):
                if INFO.USERID in app권한_dict.get('user_pks') :
                    app권한.update(app권한_dict)
                else:
                    del_idx = idx
        if del_idx is not None:
            del INFO.APP_권한[del_idx]

    def _delete_app권한(self, app권한_dict:dict):
        del_idx:Optional[int] = None
        for idx, app권한 in enumerate(INFO.APP_권한):
            if app권한.get('id') == app권한_dict.get('id'):
                del_idx = idx
                break
        if del_idx is not None:
            del INFO.APP_권한[del_idx]

    def pre_conversion(self, app권한) -> dict:
        if isinstance(app권한, dict):
            return app권한
        elif isinstance(app권한, list):
            return app권한
        elif isinstance(app권한, str):
            return json.loads(app권한)
        
        else:
            raise ValueError(f"app권한 형식 오류: {type(app권한)}")