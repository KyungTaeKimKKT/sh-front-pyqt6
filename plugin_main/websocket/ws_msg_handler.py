from modules.common_import_v2 import *

from plugin_main.websocket.handlers.app권한_handler import App_권한_Handler_No_Thread
from plugin_main.websocket.handlers.ping_handler import PingHandler_No_Thread
from plugin_main.websocket.handlers.tabletotalconfig_handler import TableTotalConfigHandler_No_Thread
from plugin_main.websocket.handlers.resources_handler import ResourcesHandler_No_Thread
from plugin_main.websocket.handlers.gongji_handler import GongiHandler_No_Thread
from plugin_main.websocket.handlers.client_app_access_log import ClientAppAccessLogHandler_No_Thread, ClientAppAccessDashboardHandler_No_Thread
from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler_No_Thread
from plugin_main.websocket.handlers.network_monitor import NetworkMonitorHandler_No_Thread
from plugin_main.websocket.handlers.apps_handler import  AppsHandler_No_Thread
from plugin_main.websocket.handlers.users_handler import  UsersHandler_No_Thread
from plugin_main.websocket.handlers.server_db_status_handler import ServerDB_Status_Handler_No_Thread

class WS_Message_Handler:

    def __init__(self):
        self.url : str = ''
        self.map_url_to_msg : dict[str,dict] = {}
        self.event_bus = event_bus

        ### message 파싱 변수
        self._main_type:None|str = None
        self._sub_type:None|str = None
        self._action:None|str = None
        self._subject:None|str = None
        self._message:None|dict|list|str = None
        self._receiver:None|str|list[int] = None
        self._sender:None|str|int = None

        self.names = []
        self.map_urlName_to_cls = {
            'app_권한': App_권한_Handler_No_Thread, 
            'ping': PingHandler_No_Thread,
            'table_total_config': TableTotalConfigHandler_No_Thread,
            'resource': ResourcesHandler_No_Thread,
            '공지사항': GongiHandler_No_Thread,
            'client_app_access_log': ClientAppAccessLogHandler_No_Thread,
            'client_app_access_dashboard': ClientAppAccessDashboardHandler_No_Thread,
            'server_monitor': ServerMonitorHandler_No_Thread,
            'network_monitor': NetworkMonitorHandler_No_Thread,
            'mbo_report:지사_구분': AppsHandler_No_Thread,
            'mbo_report:지사_고객사': AppsHandler_No_Thread,
            'hi_rtsp:건조로분석': AppsHandler_No_Thread,
            'active_users': UsersHandler_No_Thread,
            'db_live_dashboard': ServerDB_Status_Handler_No_Thread,
        }

        self.map_url_to_handler: dict[str, callable] = self._create_handler()
        # print (f"WS_Message_Handler : map_url_to_handler : {self.map_url_to_handler}")

    def get_url(self, name:str) -> str:
        url =  INFO.get_WS_URL_by_name(name)
        if url is None:
            raise ValueError (f" name: {name} is not defined by URL name !!!!")
        return url

    def get_handler(self, name: str) -> Callable:
        cls = self.map_urlName_to_cls.get(name, None)
        if cls is None:
            raise ValueError(f"name: {name} is not defined by handler class !!!!")
        _instance = cls(event_name=self.get_event_name(url=self.get_url(name)))
        if Utils.is_valid_method(  _instance, 'on_message_handle'):
            return _instance.on_message_handle
        else:
            raise ValueError(f"name: {name} is not defined by handler class !!!!")

    def get_event_name(self, url:str) -> str:
        match url:
            case _:
                return f"{url}"


    def _create_handler(self):
        self.names = list(self.map_urlName_to_cls.keys())   
        return { self.get_url(name): self.get_handler(name) for name in self.names }


    def on_message(self, url:str, msg:dict ):

        # print ( 'ws on_message: [url] : ', url)
        if not self.check_is_receiver(msg):
            return 
        self.url = url
        self.msg = copy.deepcopy(msg)
        self.map_url_to_msg[url] = self.msg
        
        self._parse_message(self.msg)

        if url in self.map_url_to_handler.keys():
            handler = self.map_url_to_handler.get( url, None)
            if handler is None:
                raise ValueError (f" url : {url} 에 대한 handler가 없읍니다.")
            handler(self.msg)
        else:
            logger.error(f" url : {url} 에 대한 handler가 없읍니다.")

                  



    def add_name(self, name:str):
        if name is not self.names:
            self.names.append(name)

    def set_names(self, names:list[str]):
        self.names = names


    def rePublish_latest_msg(self):
        self.event_bus.publish(
                    self.event_name, 
                    self.get_latest_msg().copy()
        )
        
    def rePublish_published_msg(self):
        self.event_bus.publish(
                    self.event_name, 
                    self.get_published_msg().copy()
        )

    def check_is_receiver(self, msg:dict) -> bool:
        """ 수신자 체크 메서드 """
        receiver = msg.get('receiver', None)
        if receiver is None:
            return False
        
        if isinstance(receiver, list):
            return INFO.USERID in receiver
        elif isinstance(receiver, str):
            return receiver.lower() == 'all'
        else:
            return False
        
        
    def check_is_request(self, msg:dict) -> bool:
        """ msg sub_type 이 request 인지 체크 메서드 : echo server라서 request 면 처리안함  """
        sub_type = msg.get('sub_type', None)
        return sub_type == 'request'
    
    def _parse_message(self, msg:dict):
        """메시지 파싱 메서드"""
        try:
            self.msg = copy.deepcopy(msg)
            self._main_type = self.msg.get('main_type', None)
            self._sub_type = self.msg.get('sub_type', None)
            self._action =  self.msg.get('action', None)
            self._subject = self.msg.get('subject', None)
            self._message = self.msg.get('message', None)
            self._receiver = self.msg.get('receiver', None)
            self._sender = self.msg.get('sender', None)
        except Exception as e:
            print ( f'{self.url}')

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

    def pre_conversion(self, app권한) -> dict:
        if isinstance(app권한, dict):
            return app권한
        elif isinstance(app권한, list):
            return app권한
        elif isinstance(app권한, str):
            return json.loads(app권한)
        
        else:
            raise ValueError(f"app권한 형식 오류: {type(app권한)}")