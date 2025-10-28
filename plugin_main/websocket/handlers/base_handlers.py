from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Union

from threading import Lock
from info import Info_SW as INFO

from modules.global_event_bus import event_bus
import copy

from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker, WS_Thread_AsyncWorker_V2

# if TYPE_CHECKING:
#     from plugin_main.websocket.main_ws_manager import Main_WS_Manager


class Base_WSMessageHandler:
    """ 웹소켓 메시지 처리 기본 클래스 
        url 에 따라 처리 방법이 다름
        url: event_bus에 등록할 이름 
             -> 예) f"{url}:{action}" 형태임.
        manager: 웹소켓 매니저 (없어도 무방)
    """
    def __init__(self, url:str, manager=None):
        print(f"{self.__class__.__name__} : __init__ : {url} : subscribe : {f'{url}|on_ws_message'}")
        self.manager = manager
        self.url = url
        self.event_bus = event_bus

        self.event_bus.subscribe(f"{self.url}|on_ws_message", self.handle)


    def handle(self, msg):
        """메시지 처리 기본 메서드"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    

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



class Base_WSMessageHandler_No_Thread:
    """ 웹소켓 메시지 처리 기본 클래스 
        url 에 따라 처리 방법이 다름
        url: event_bus에 등록할 이름 
             -> 예) f"{url}:{action}" 형태임.
    """
    def __init__(self, event_name:str, **kwargs):
        self.kwargs = kwargs
        self.event_bus = event_bus
        self.event_name = event_name

        self.latest_msg = None
        self._lock = Lock()

        ### message 파싱 변수
        self._main_type:None|str = None
        self._sub_type:None|str = None
        self._action:None|str = None
        self._subject:None|str = None
        self._message:None|dict|list|str = None
        self._receiver:None|str|list[int] = None
        self._sender:None|str|int = None

        self.is_first = True


    def set_latest_msg(self, msg:dict):
        with self._lock:
            self.latest_msg = msg

    def get_latest_msg(self) -> dict:
        with self._lock:
            return copy.deepcopy(self.latest_msg)  # 안전하게 사본 반환
        
    def set_published_msg(self, msg:dict):
        with self._lock:
            self.published_msg = msg

    def get_published_msg(self) -> dict:
        with self._lock:
            return self.published_msg
        
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

    def close(self):
        """웹소켓 연결 종료 메서드"""
        self.ws_async_worker.close()

    def stop(self):
        """웹소켓 연결 종료 메서드"""
        self.ws_async_worker.stop()


    def on_message_handle(self, msg:dict):
        """메시지 처리 기본 메서드"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
    
    
    

    def send_message(self, msg:dict):
        """메시지 전송 메서드"""
        self.ws_async_worker.send_message(msg)

    def check_is_available(self, msg:dict) -> bool:
        """ 사용 가능 여부 체크 메서드
            수신자가 있고, 요청이 아닌 경우 사용 가능
        """
        return self.check_is_receiver(msg) and not self.check_is_request(msg)

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
        self._main_type = msg.get('main_type', None)
        self._sub_type = msg.get('sub_type', None)
        self._action = msg.get('action', None)
        self._subject = msg.get('subject', None)
        self._message = msg.get('message', None)
        self._receiver = msg.get('receiver', None)
        self._sender = msg.get('sender', None)



class Base_WSMessageHandler_V2:
    """ 웹소켓 메시지 처리 기본 클래스 
        url 에 따라 처리 방법이 다름
        url: event_bus에 등록할 이름 
             -> 예) f"{url}:{action}" 형태임.
        manager: 웹소켓 매니저 (없어도 무방)
    """
    def __init__(self, url:str, **kwargs):
        self.kwargs = kwargs
        self.url = url
        self.event_bus = event_bus
        self.event_name = f"{self.url}"

        self.latest_msg = None
        self._lock = Lock()

        ### message 파싱 변수
        self._main_type:None|str = None
        self._sub_type:None|str = None
        self._action:None|str = None
        self._subject:None|str = None
        self._message:None|dict|list|str = None
        self._receiver:None|str|list[int] = None
        self._sender:None|str|int = None

        self.ws_async_worker = WS_Thread_AsyncWorker_V2(url, parent=None, **kwargs)

        self.ws_async_worker.on_message.connect(self.on_message_handle)    ### subscribe 대신 연결: self.event_bus.subscribe(f"{self.url}|on_ws_message", self.handle)
        self.ws_async_worker.start()

    def set_latest_msg(self, msg:dict):
        with self._lock:
            self.latest_msg = msg

    def get_latest_msg(self) -> dict:
        with self._lock:
            return copy.deepcopy(self.latest_msg)  # 안전하게 사본 반환
        
    def set_published_msg(self, msg:dict):
        with self._lock:
            self.published_msg = msg

    def get_published_msg(self) -> dict:
        with self._lock:
            return self.published_msg
        
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

    def close(self):
        """웹소켓 연결 종료 메서드"""
        self.ws_async_worker.close()

    def stop(self):
        """웹소켓 연결 종료 메서드"""
        self.ws_async_worker.stop()


    def on_message_handle(self, msg:dict):
        """메시지 처리 기본 메서드"""
        raise NotImplementedError(f"{self.__class__.__name__} : 서브클래스에서 구현해야 합니다")
    
    
    

    def send_message(self, msg:dict):
        """메시지 전송 메서드"""
        self.ws_async_worker.send_message(msg)

    def check_is_available(self, msg:dict) -> bool:
        """ 사용 가능 여부 체크 메서드
            수신자가 있고, 요청이 아닌 경우 사용 가능
        """
        return self.check_is_receiver(msg) and not self.check_is_request(msg)

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
        self._main_type = msg.get('main_type', None)
        self._sub_type = msg.get('sub_type', None)
        self._action = msg.get('action', None)
        self._subject = msg.get('subject', None)
        self._message = msg.get('message', None)
        self._receiver = msg.get('receiver', None)
        self._sender = msg.get('sender', None)
