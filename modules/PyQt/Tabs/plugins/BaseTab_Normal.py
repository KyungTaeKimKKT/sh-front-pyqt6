from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias
# from abc import ABC, abstractmethod
from typing import Callable

from config import Config as APP
from info import Info_SW as INFO
from modules.PyQt.Qthreads.background_api_thread import Background_API_Thread
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

module_postfix = __name__.split('.')[-1].split('__')[-1]

class BaseTab(QWidget):   ##2025-03-22 14:32:11,873 - ERROR - root - main - Error configuring logging: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
    """모든 탭의 기본 클래스
        
    
    """


    def __init__(self, parent, **kwargs):
        super().__init__(parent)        
        logger.info(f" : __INIT__: kwargs : {kwargs}")
        self.globals_dict :dict = {}
        self.module_postfix:str = ''
        self.is_Auto_조회_Start = kwargs.get('auto_start', False)
        self.selected_rows = []
        self.last_param = ""
        self.kwargs = kwargs        
        self.api_datas : list[dict]|dict|None = None
        self.기타조회조건 = {}
        self.기타조회조건_for_param = {}
        self.api_datas :list[dict]|dict|None = None
        self.table_name = None
        self.initialize_attributes(kwargs)
        logger.info(f" : __INIT__: 클래스 속성들: {self.url}")

    def initialize_attributes(self, kwargs:dict={}):
        logger.info(f" : __INIT__: kwargs : {kwargs}")
        self.set_kwargs(kwargs)

    def initialize_UI(self):
        """ ui 초기화"""
        # 초기화
        self.setup_ui()
        self.customize_ui()

    def initialize_handlers(self):
        """ 핸들러 초기화 """
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")


    def closeEvent(self, event):
        """위젯이 닫힐 때 호출되는 이벤트 핸들러"""
        
        # 모든 QThread, WS_Thread_Sync 속성 찾아서 종료
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, QThread):
                if hasattr(attr, 'quit'):
                    attr.quit()
                if hasattr(attr, 'wait'):
                    attr.wait(1000)  # 최대 1초 대기
            
            if isinstance(attr, WS_Thread_Sync):
                attr.close()

            # 시그널 연결 해제 (객체의 모든 시그널 속성 검사)
            if hasattr(attr, '__class__'):
                for signal_name in dir(attr.__class__):
                    try:
                        signal = getattr(attr.__class__, signal_name)
                        if isinstance(signal, pyqtBoundSignal) or hasattr(signal, 'connect'):
                            instance_signal = getattr(attr, signal_name, None)
                            if instance_signal and hasattr(instance_signal, 'disconnect'):
                                self.disconnect_signal(instance_signal)
                    except:
                        pass

        # 자신의 시그널 속성도 검사
        for signal_name in dir(self.__class__):
            try:
                signal = getattr(self.__class__, signal_name)
                if isinstance(signal, pyqtBoundSignal) or hasattr(signal, 'connect'):
                    instance_signal = getattr(self, signal_name, None)
                    if instance_signal and hasattr(instance_signal, 'disconnect'):
                        self.disconnect_signal(instance_signal)
            except:
                pass


            # 부모 클래스의 closeEvent 호출
        super().closeEvent(event)


    def setup_ui(self):
        """UI 설정 - 하위 클래스에서 구현"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    def customize_ui(self):
        """UI 커스터마이징 - 필요시 하위 클래스에서 오버라이드"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    def update_ui(self):
        """UI 업데이트 - 필요시 하위 클래스에서 오버라이드"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    def connect_signals(self):
        """시그널 연결 - 하위 클래스에서 구현"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")

    def disconnect_signal(self, signal:pyqtBoundSignal):
        """시그널 연결 해제"""
        try:
            signal.disconnect()
        except:
            pass

    def run(self):
        """테이블 구성 및 초기화"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    
    def get_search_url(self):
        """검색 URL 반환 - 하위 클래스에서 구현"""
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    def build_search_param(self, param):
        """검색 파라미터 생성 - 필요시 하위 클래스에서 오버라이드"""
        return f"?{param}" if param else ""
    
    def process_api_response(self, response):
        """API 응답 처리 - 하위 클래스에서 구현"""
        pass
        # raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")

    ### setter
    def set_slot_handler(self, slot_handler):
        self.slot_handler = slot_handler

    def set_kwargs(self, kwargs:dict={}):
        self.kwargs = kwargs or self.kwargs
        if kwargs:
            self.set_kwargs_to_attributes(kwargs)

    def set_kwargs_to_attributes(self, kwargs:dict ={}):
        """kwargs 를 객체의 속성으로 설정"""
        try:
            if not kwargs:            
                kwargs = self.kwargs 

            for key, value in kwargs.items():
                setattr(self, key, value)
            
            if hasattr(self, 'api_uri') and hasattr(self, 'api_url'):
                self.url = f"{self.api_uri}{self.api_url}"
            else:
                self.url = None

            if hasattr(self, 'div') and hasattr(self, 'name') and not hasattr(self, 'table_name'):
                setattr(self, 'table_name', f"{self.div}_{self.name}_appID_{self.id}")
                logger.info(f"table_name 설정 : {self.table_name}")
        except Exception as e:
            logger.error(f"set_kwargs_to_attributes 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def set_api_datas(self, api_datas:list[dict]|dict):
        self.api_datas = api_datas

    def set_fetch_flag(self, fetch_flag:bool):    
        self.fetch_flag = fetch_flag

    def set_table_name(self, table_name:str):
        self.table_name = table_name

    def make_table_name(self, div:str='', name:str='', id:str=''):
        """ table_name 생성 """    
        try: 
            if not div:
                div = self.div
            if not name:
                name = self.name
            if not id:
                id = self.id
            self.table_name = f"{div}_{name}_appID_{id}"
            if self.table_name is None:
                raise Exception("table_name 생성 실패")
            return self.table_name
        except Exception as e:
            logger.error(f"make_table_name 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return None

    #### getter
    def get_kwargs(self) -> dict:
        """ kwargs 반환 """
        return self.kwargs

    def get_attributes(self, attr_Name:str) -> dict:
        """ attributes 반환 """
        return getattr(self, attr_Name, None)

    def get_api_datas(self) -> list[dict]|dict:
        """ api_datas 반환 """
        return self.api_datas

    def get_param(self) -> str:
        """ param 반환 """
        return self.param

    def get_defaultParam(self) -> str:
        """ defaultParam 반환 """
        return self.defaultParam

    def get_기타조회조건_for_param(self) -> dict:
        """ 기타조회조건_for_param 반환 """
        return self.기타조회조건_for_param
    
    def get_url(self) -> str|None:        
        """ url 반환 """
        return self.url

    def get_param(self) -> str:
        """ param 반환 """
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다")
    
    ####  server commnunication
    def fetch_sync(self, url:str) -> list[dict]|dict:
        """ api_datas 반환 """
        is_ok, _json = APP.API.getlist( url )
        if is_ok:
            return _json
        else:
            return []
        
    def fetch_by_bg_thread(self, attrName:str,url:str, success_callback:Callable=None, error_callback:Callable=None) :
        """ 백그라운드 스레드 실행 , return 은 class attribute(thread 임) 반환 """
        setattr(self, attrName, Background_API_Thread(url))
        thread = getattr(self, attrName)
        thread.finished.connect(success_callback)
        thread.error.connect(error_callback)
        thread.start()
        return thread

    def post_sync(self, url:str, data:dict) -> bool:
        """ api_datas send """
        is_ok = APP.API.Send(url, data)
        return is_ok