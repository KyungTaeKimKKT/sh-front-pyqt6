from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Main_WS_Manager_Interface(ABC):
    """
    WebSocket 메시지 처리를 위한 인터페이스
    이 인터페이스를 구현하는 클래스는 WebSocket 관련 이벤트를 처리할 수 있어야 함
    """
    

    @abstractmethod
    def enable_ws(self) -> None:
        """
        WebSocket 연결을 활성화하는 메서드
        LOGIN 후 호출되는 메서드
        """
        pass

    @abstractmethod
    def ws_on_message(self, url: str, msg: object) -> None:
        """
        WebSocket으로부터 메시지를 수신했을 때 호출되는 메서드
        
        Args:
            url: 메시지를 보낸 WebSocket 엔드포인트 URL
            msg: 수신된 메시지 객체 (일반적으로 JSON에서 변환된 dict)
        """
        pass
    
    @abstractmethod
    def ws_on_error(self, url: str, e: object) -> None:
        """
        WebSocket 연결 중 오류가 발생했을 때 호출되는 메서드
        
        Args:
            url: 오류가 발생한 WebSocket 엔드포인트 URL
            error: 발생한 예외 객체
        """
        pass
    
    # @abstractmethod
    # def on_ws_connected(self, url: str) -> None:
    #     """
    #     WebSocket 연결이 성공적으로 수립되었을 때 호출되는 메서드
        
    #     Args:
    #         url: 연결된 WebSocket 엔드포인트 URL
    #     """
    #     pass
    
    # @abstractmethod
    # def on_ws_disconnected(self, url: str, code: int, reason: str) -> None:
    #     """
    #     WebSocket 연결이 종료되었을 때 호출되는 메서드
        
    #     Args:
    #         url: 연결이 종료된 WebSocket 엔드포인트 URL
    #         code: 종료 코드
    #         reason: 종료 이유
    #     """
    #     pass

    @abstractmethod
    def handle_ws_status_changed(self, is_connected: bool, blink_interval: int) -> None:
        """
        WebSocket 연결 상태가 변경되었을 때 호출되는 메서드
        
        Args:
            is_connected: 연결 상태 (True: 연결됨, False: 연결 끊김)
            blink_interval: 깜빡임 간격 (0 이상일 때 깜빡임 효과)
        """
        pass
