from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
import copy, json

from plugin_main.websocket.handlers.base_handlers import Base_WSMessageHandler_V2

from info import Info_SW as INFO
import modules.user.utils as Utils
import datetime
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

import modules.user.utils as utils


class Pyro5Handler(Base_WSMessageHandler_V2):

    def set_is_request(self, is_request:bool):
        self.is_request = is_request
    

    def on_message_handle(self, msg: Union[dict,list, None]):
        """ app권한 message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)
        print(f"Pyro5Handler : handle : {type(self.msg)} : {self.msg}")

        try: 
            # logger.debug(f"ServerMonitorHandler : handle : {self.msg}")
            if 'action' in msg:
                self.action = msg.get('action').strip()
                self.event_name = f"{self.url}"
                self.datas = msg.get('message')
                print(f"Pyro5Handler : handle : {self.action} : {self.action == 'remote_control_request'}")
                # logger.info (f"Pyro5Handler : handle : {type(self.datas)}")
                # logger.info(f"Pyro5Handler : handle : {self.datas}")
            # self.app권한 = self.get_app권한_BY_Owner( msg.get('message') )
                match self.action:
                    case 'remote_control_request':
                        if INFO.USERID == 1:
                            self._handle_remote_control_request()
                        else:
                            logger.info(f"Pyro5Handler : handle : {self.action} 처리 안함")
                            return
                    case 'remote_control_accept':
                        self._handle_remote_control_accept()
                    case 'remote_control_reject':
                        self._handle_remote_control_reject()
                    case 'remote_control_ready':
                        self._handle_remote_control_ready()
                    # case 'create':
                    #     self._handle_create()
                    # case 'update':
                    #     self._handle_update()
                    # case 'delete':
                    #     self._handle_delete()
                    case _:
                        logger.info(f"NetworkMonitorHandler : handle : {self.action} 처리 안함")
                        return
                
                ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
                # logger.info(f"NetworkMonitorHandler : {type(self.datas)} : {self.datas}  처리 완료")
                self.event_bus.publish(
                    self.event_name, 
                    self.datas
                )

        except Exception as e:
            logger.error(f"NetworkMonitorHandler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_remote_control_request(self):
        """ 실행자 : 관리자
        요청자에서 송신한 remote_control_request 처리 : 요청자가 자신인 경우 처리 안함 """
        _txt = f"원격조정 요청을 수신하였읍니다.\n\n{self.msg}"
        from_id = self.msg.get('from_id')
        if from_id == INFO.USERID:
            return 
        replay_msg = {
            "to_id": self.msg.get('from_id'),
            "to_name": self.msg.get('from_name'),
            "from_id": INFO.USERID,
            "from_name": INFO.USERNAME,
            "timestamp": datetime.datetime.now().isoformat()
        }
        if Utils.QMsg_question(INFO.MAIN_WINDOW, title="원격조정 요청 수신", text=_txt):
            msg = replay_msg.copy()
            msg.update({
                "action": "remote_control_accept",
            })
            self.send_message(msg)
            self.is_remote_control_accept = True

        else:
            msg = replay_msg.copy()
            msg.update({
                "action": "remote_control_reject",
            })
            self.send_message(msg)

    def _handle_remote_control_accept(self):
        """ 실행자 : 요청자 
        관리자에서 송신한 remote_control_accept 처리 : 자기가 is_request =True인 경우 처리함"""
        to_id = self.msg.get('to_id')
        to_name = self.msg.get('to_name')
        from_id = self.msg.get('from_id')
        from_name = self.msg.get('from_name')
        if to_id != INFO.USERID or not getattr(self, 'is_request', False):
            return 
        print(f"Pyro5Handler : _handle_remote_control_accept : {self.msg}")

        ### 관리자에서 요청 수락하였으므로, 요청자는 ns 등록 및 원격 서버 실행
        from plugin_main.dialog.remote_control_request import RemoteServer_Request_Thread
        lookup_name = f"{Utils.get_local_ip()}:{INFO.USERID}"
        self.remote_control_client_thread = RemoteServer_Request_Thread(lookup_name=lookup_name)
        self.remote_control_client_thread.start()

        #### threading start 후, 관리자에게 ready msg 송부함. 관리자는 이 msg 받고 dialog 오픈
        msg = {
            "action": "remote_control_ready",
            "to_id": self.msg.get('from_id'),
            "to_name": self.msg.get('from_name'),
            "from_id": INFO.USERID,
            "from_name": INFO.USERNAME,
            "timestamp": datetime.datetime.now().isoformat(),
            "lookup_name": lookup_name
        }
        self.send_message(msg)

    def _handle_remote_control_ready(self):
        """ 실행자 : 관리자
        요청자에서 송신한 remote_control_ready 처리 """
        to_id = self.msg.get('to_id')
        to_name = self.msg.get('to_name')
        from_id = self.msg.get('from_id')
        from_name = self.msg.get('from_name')
        lookup_name = self.msg.get('lookup_name')
        if to_id != INFO.USERID:
            return 
        print(f"Pyro5Handler : _handle_remote_control_ready : {self.msg}")
        from plugin_main.dialog.remote_control_accept import RemoteViewerDialog, RemoteControlClient
        dlg = RemoteViewerDialog( lookup_name=lookup_name)
        ### 녹화는 dialog 안에서 pb_recording 버튼 클릭시 시작
        # dlg.start_recording( "./debug/remote_control_accept.mp4", size=(1600, 1200), fps= 4)
        dlg.exec()
        # dlg.stop_recording()

    

    def _handle_remote_control_reject(self):
        """ remote_control_reject 처리 """
        pass

    def _handle_init(self):
        """ init 처리 """
        pass
        # logger.info(f"ServerMonitorHandler : _handle_init : {self.datas}")


    
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