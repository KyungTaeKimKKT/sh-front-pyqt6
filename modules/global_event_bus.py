from __future__ import annotations
from typing import Callable
from PyQt6.QtCore import QObject, pyqtSignal
from functools import partial

from modules.envs.global_bus_event_name import global_bus_event_name as GBus
import traceback
# from modules.logging_config import get_plugin_logger
# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()

class EventBusSignals(QObject):
    """이벤트 버스에서 사용할 시그널들을 정의하는 클래스"""
    
    # 기본 시그널 - 어떤 타입의 데이터든 전달 가능
    signal = pyqtSignal(str, object)
    
    # 특정 타입의 시그널을 추가로 정의할 수 있음
    # 예: int_signal = pyqtSignal(int)
    # 예: str_signal = pyqtSignal(str)
    # 예: custom_signal = pyqtSignal(str, int, list)


class GlobalEventBus(QObject):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalEventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._signals = EventBusSignals()
            self._event_handlers = {}  # {event_type: [callback]}
            self._connected_handlers = {}  # {event_type: {callback: bound_handler}}
            self._initialized = True

            self.no_debug_types = [
                GBus.WS_STATUS,
                GBus.API_STATUS,
                GBus.CPU_RAM_MONITOR,
                "broadcast/server_resource/",
                "broadcast/network_ping/",
            ]

    def _handle_event(self, expected_event_type: str, callback: Callable, actual_event_type: str, data: object):
        if expected_event_type == actual_event_type:
            callback(data)

    def get_event_handlers(self, event_type: str) -> list[Callable]:
        return self._event_handlers.get(event_type, [])

    def subscribe(self, event_type: str, callback: Callable[[object], None], from_class: str = None):
        try:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
                self._connected_handlers[event_type] = {}

            if callback not in self._event_handlers[event_type]:
                self._event_handlers[event_type].append(callback)

                handler = partial(self._handle_event, event_type, callback)
                self._connected_handlers[event_type][callback] = handler
                self._signals.signal.connect(handler)

                self.publish( GBus.TRACE_LOGGER, 
                              { 'action': f"이벤트 구독 추가: {from_class} : {event_type}, 콜백: {getattr(callback, '__name__', str(callback))}" })

        except Exception as e:
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "subscribe 오류", 
                            'data': f"{e}" })   
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "subscribe 오류", 
                            'data': f"{traceback.format_exc()}" })


    def unsubscribe(self, event_type: str, callback: Callable[[object], None]):
        try:
            if event_type in self._event_handlers and callback in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(callback)

                handler = self._connected_handlers.get(event_type, {}).pop(callback, None)
                if handler:
                    self._signals.signal.disconnect(handler)

                if not self._event_handlers[event_type]:
                    del self._event_handlers[event_type]
                    self._connected_handlers.pop(event_type, None)
                    self.publish( GBus.TRACE_LOGGER, 
                                  { 'action': f"{event_type} 구독 제거" , 
                                   'data':f"이벤트 타입 제거 (구독자 없음): {event_type}" })
        except Exception as e:
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "unsubscribe 오류", 
                            'data': f"{e}" })   
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "unsubscribe 오류", 
                            'data': f"{traceback.format_exc()}" })

    def publish_trace_time(self, data=None) : 
        self._signals.signal.emit(GBus.TRACE_TIME, data)

    def publish_trace_logger(self, data=None) :
        self._signals.signal.emit(GBus.TRACE_LOGGER, data)

    def publish(self, event_type: str, data=None) -> int:
        try:
            self._signals.signal.emit(event_type, data)
            sub_count = self.get_subscriber_count(event_type)
            self._signals.signal.emit(f"trace_gbus", 
                                      { 'channel':event_type, 
                                       'sub수': sub_count,
                                       'data':data })

            # if event_type not in self.no_debug_types:
            #     logger.debug(f"Publish: {event_type}, 데이터 타입: {type(data).__name__}, 구독자 수: {sub_count}")

            if sub_count == 0:
                pass
                # logger.warning(f"구독자가 없읍니다. event_type: {event_type}")
            return sub_count

        except Exception as e:
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "publish 오류", 
                            'data': f"{e}" })   
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "publish 오류", 
                            'data': f"{traceback.format_exc()}" })
            
    def unsubscribe_prefix(self, prefix: str):
        """
        prefix로 시작하는 event_type에 대해 모든 callback을 unsubscribe함
        """
        try:
            target_event_types = [et for et in self._event_handlers if et.startswith(prefix)]
            for event_type in target_event_types:
                callbacks = self._event_handlers.get(event_type, [])[:]
                for callback in callbacks:
                    self.unsubscribe(event_type, callback)

            self.publish(GBus.TRACE_LOGGER, {
                'action': f"{prefix} 구독 제거",
                'data': f"총 {len(target_event_types)}개의 이벤트 타입에 대해 제거 완료"
            })
        except Exception as e:
            self.publish(GBus.TRACE_LOGGER, {
                'action': "unsubscribe_prefix 오류",
                'data': f"{e}"
            })
            self.publish(GBus.TRACE_LOGGER, {
                'action': "unsubscribe_prefix 오류",
                'data': traceback.format_exc()
            })

    def clear(self):
        try:
            event_count = len(self._event_handlers)
            sub_count = self.get_subscriber_count()

            if hasattr(self._signals, "signal") :
                self._signals.signal.disconnect()

            self._event_handlers.clear()
            self._connected_handlers.clear()

            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "이벤트 버스 초기화 완료", 
                            'data': f"{event_count}개 이벤트 타입, {sub_count}개 구독 제거" })
        except Exception as e:
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "clear 오류", 
                            'data': f"{e}" })   
            self.publish( GBus.TRACE_LOGGER, 
                          { 'action': "clear 오류", 
                            'data': f"{traceback.format_exc()}" })

    def get_subscriber_count(self, event_type=None) -> int:
        if event_type:
            return len(self._event_handlers.get(event_type, []))
        return sum(len(callbacks) for callbacks in self._event_handlers.values())
    
    
# class GlobalEventBus(QObject):
#     """
#     PyQt6 시그널을 활용한 글로벌 이벤트 버스 클래스
#     애플리케이션 전체에서 이벤트를 발행하고 구독할 수 있는 중앙 집중식 이벤트 시스템

#     event_type 등록된 예시:
#     'update_cpu_ram_monitor', 'ws_status'
#     """
    
#     _instance = None
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(GlobalEventBus, cls).__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance
    
#     def __init__(self):
#         if not self._initialized:
#             super().__init__()
#             self._signals = EventBusSignals()
#             self._event_handlers = {}
#             self._initialized = True

#             self.no_debug_types = [GBus.WS_STATUS, GBus.API_STATUS, GBus.CPU_RAM_MONITOR, "broadcast/server_resource/",'broadcast/network_ping/']
    
#     def subscribe(self, event_type: str, callback: Callable[[object], None], from_class:str=None):
#         """
#         특정 이벤트 타입에 콜백 함수를 구독합니다.
        
#         Args:
#             event_type (str): 구독할 이벤트 타입
#             callback (callable): 이벤트 발생 시 호출될 콜백 함수
#         """
#         try:
#             if event_type not in self._event_handlers:
#                 self._event_handlers[event_type] = []
#                 # logger.debug(f"새 이벤트 타입 등록: {event_type}")
        
#             if callback not in self._event_handlers[event_type]:
#                 self._event_handlers[event_type].append(callback)
#                 logger.debug(f"이벤트 구독 추가: {from_class} : {event_type}, 콜백: {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")
                
#                 # 시그널에 슬롯 연결
#                 # 람다를 사용하여 이벤트 타입 필터링
#                 self._signals.signal.connect(
#                     lambda evt_type, data: callback(data) if evt_type == event_type else None
#                 )
#         except Exception as e:
#             logger.error(f"subscribe 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")
    
#     def unsubscribe(self, event_type: str, callback: Callable[[object], None]):
#         """
#         특정 이벤트 타입에서 콜백 함수의 구독을 취소합니다.
        
#         Args:
#             event_type (str): 구독 취소할 이벤트 타입
#             callback (callable): 구독 취소할 콜백 함수
#         """
#         try:
#             if event_type in self._event_handlers and callback in self._event_handlers[event_type]:
#                 self._event_handlers[event_type].remove(callback)
                
#                 # 모든 연결 해제 후 남은 핸들러만 다시 연결
#                 # (PyQt에서는 특정 람다 연결만 해제하기 어려움)
#                 self._signals.signal.disconnect()
                
#                 # 모든 이벤트 타입에 대해 핸들러 다시 연결
#                 for evt_type, handlers in self._event_handlers.items():
#                     for handler in handlers:
#                         self._signals.signal.connect(
#                             lambda e_type, data: handler(data) if e_type == evt_type else None
#                         )
                
#                 # 구독자가 없으면 해당 이벤트 타입 키 제거
#                 if not self._event_handlers[event_type]:
#                     del self._event_handlers[event_type]
#                     logger.debug(f"이벤트 타입 제거 (구독자 없음): {event_type}")
#         except Exception as e:
#             logger.error(f"unsubscribe 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")
    
#     def publish(self, event_type, data=None) -> int:
#         """
#         특정 이벤트 타입을 발행하고 모든 구독자에게 알립니다.
#         return : 구독자 수 ( 만약 0 이면 error 하도록 )
        
#         Args:
#             event_type (str): 발행할 이벤트 타입
#             data (object, optional): 이벤트와 함께 전달할 데이터
#         """
#         try:
#             self._signals.signal.emit(event_type, data)
#             sub_count = self.get_subscriber_count(event_type)
#             # no_debug_types에 포함되지 않은 이벤트 타입만 로깅
#             # if event_type not in self.no_debug_types:
#             #      logger.debug(f"Publish: {event_type}, 데이터 타입: {type(data).__name__}, 구독자 수: {sub_count}")

#             if sub_count == 0:
#                 pass
#                 # logger.warning(f"구독자가 없읍니다. event_type: {event_type}")
#             return sub_count
            
#         except Exception as e:
#             logger.error(f"publish 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")
    
#     def clear(self):
#         """모든 구독 정보를 초기화합니다."""
#         try:
#             event_count = len(self._event_handlers)
#             sub_count = self.get_subscriber_count()

#             if hasattr(self._signals, 'signal') and self._signals.signal.receivers() > 0:
#                 self._signals.signal.disconnect()
#             self._event_handlers = {}
#             logger.debug(f"이벤트 버스 초기화 완료: {event_count}개 이벤트 타입, {sub_count}개 구독 제거")
#         except Exception as e:
#             logger.error(f"clear 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")
    
#     def get_subscriber_count(self, event_type=None):
#         """
#         특정 이벤트 타입 또는 전체 구독자 수를 반환합니다.
        
#         Args:
#             event_type (str, optional): 구독자 수를 확인할 이벤트 타입
            
#         Returns:
#             int: 구독자 수
#         """
#         if event_type:
#             return len(self._event_handlers.get(event_type, []))
        
#         # 전체 구독자 수 계산
#         total = 0
#         for handlers in self._event_handlers.values():
#             total += len(handlers)
#         return total


# 글로벌 인스턴스 생성 - 애플리케이션 전체에서 사용할 수 있는 싱글톤 인스턴스
event_bus = GlobalEventBus()