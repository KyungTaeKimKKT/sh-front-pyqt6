from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from config import Config as APP
from info import Info_SW as INFO
from modules.PyQt.Qthreads.background_api_thread import Background_API_Thread
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync

from modules.utils.api_response_분석 import handle_api_response

class BaseTab_Slot_Handler(QObject):

    def __init__(self, handler : QWidget):
        super().__init__(handler)
        self.handler = handler
        self.event_bus = event_bus

    def slot_search_for(self, url:str=None, param:str=None):
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