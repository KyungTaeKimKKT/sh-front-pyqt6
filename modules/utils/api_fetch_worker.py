from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from copy import deepcopy
from modules.global_event_bus import event_bus

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import time
from config import Config as APP
from info import Info_SW as INFO
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Api_Fetch_Worker(QRunnable):
    def __init__(self, url, start_time=1000, parent=None, param:dict=None, **kwargs):
        super().__init__()
        self.url = url
        self.start_time = start_time
        self.event_bus = event_bus
        self.param = param
        self.kwargs = kwargs

        self.api = APP.API
        self.setAutoDelete(True)  ### 작업 완료 후 자동 삭제 설정


        self.dialog_config = { 
            # 'title': 'Loading 중입니다.잠시만 기다려 주십시요..', 
            # 'movie': 'loading.gif', 
            'start_time': self.start_time
        }
        self.timer:Optional[QTimer] = None

    ### start ThreadPoolExecutor
    def start(self):
        """스레드 풀에서 이 작업을 비동기적으로 실행합니다."""
        QThreadPool.globalInstance().start(self)
        return self

    def run(self):
        try:
            start_time = time.time()
            if INFO.IS_DEV:
                logger.info(f"Api_Fetch_Worker : {self.url} 시작, start_time: {self.start_time}")


            if self.param:
                self.run_with_param()
                return
            
            # 무조건 로딩 다이얼로그 표시 이벤트 발행
            # self.event_bus.publish('loading_dialog_show', self.get_dialog_config())
            if 'page_size' in self.url:
                is_Pagenation = bool ( 'page_size=0' not in self.url )
            else:
                is_Pagenation = False
            is_ok, results = self.api.getlist(self.url)
            ### 결과 수신시 timer 종료
            self.stop_timer()

            msg = {
                'is_Pagenation': is_Pagenation,
                'is_ok': is_ok,
                'results': results
            }
            self.event_bus.publish(f"fetch_{self.url}", msg)
            # self.event_bus.publish('loading_dialog_hide', True)                
            if INFO.IS_DEV:
                logger.info(f"Api_Fetch_Worker : {self.url} 소요시간 : {time.time() - start_time}: msg: {len(msg)}")
        except Exception as e:
            logger.error(f"Api_Fetch_Worker : {self.url} 오류 : {e}")
            logger.error(traceback.format_exc())
        finally:            
            self.close()

    def run_with_param(self):
        response = self.api.get( self.url, self.param, **self.kwargs )
        if 'page_size' in self.param:
            is_Pagenation = self.param['page_size'] != 0
        else:
            is_Pagenation = False
        
        msg = {
            'is_Pagenation': is_Pagenation,
            'is_ok': response.ok,
            'results': response.json() if response.ok else {'error': response.text() }
        }
        self.event_bus.publish(f"fetch_{self.url}", msg)
    
    def publish_event_show(self):
        """ 이벤트 발행 """
        try:
            logger.info(f"publish_event_show: {self.get_dialog_config()}")
            self.event_bus.publish('loading_dialog_show', self.get_dialog_config() )
        except Exception as e:
            logger.error(f"Api_Fetch_Worker : {self.url} 오류 : {e}")
            logger.error(traceback.format_exc())

    def close(self):
        if self.timer:
            self.timer.stop()
            self.timer = None

    def stop_timer(self):
        if self.timer:
            self.timer.stop()   
            self.timer = None

    ### builder 개념
    def with_url(self, url:str):
        self.url = url
        return self
    def with_start_time(self, start_time:int):
        self.start_time = start_time
        return self
    
    ### setter
    def set_start_time(self, start_time:int):
        self.start_time = start_time

    def set_url(self, url:str):
        self.url = url

    def set_dialog_config(self, title:str, movie:str):
        self.dialog_config = {
            'title': title,
            'movie': movie,
            'start_time': self.start_time
        }

    def get_dialog_config(self):
        return self.dialog_config


class Signal_Api_Fetch_Worker_V3(QObject):
    """V3 버젼"""
    finished = pyqtSignal(object)


class Api_Fetch_Worker_by_signal(QRunnable):
    """V3 버젼
    signal 을 사용하여 response  반환함.


    """

    def __init__(self, url, start_time=1000, parent=None, param:dict=None, **kwargs):
        super().__init__()
        self.url = url
        self.event_bus = event_bus
        self.param = param
        self.kwargs = kwargs

        self.signal = Signal_Api_Fetch_Worker_V3()

        self.api = APP.API
        self.setAutoDelete(True)  ### 작업 완료 후 자동 삭제 설정


    ### start ThreadPoolExecutor
    def start(self):
        """스레드 풀에서 이 작업을 비동기적으로 실행합니다."""
        QThreadPool.globalInstance().start(self)
        return self

    def run(self):
        try:
            start_time = time.perf_counter()
            response = self.api.getlist(self.url, params=self.param, **self.kwargs)
            
            self.signal.finished.emit(response)
               
            if INFO.IS_DEV:
                logger.info(f"Api_Fetch_Worker : {self.url} 소요시간 : {1000*(time.perf_counter() - start_time)} msec ")
        except Exception as e:
            logger.error(f"Api_Fetch_Worker : {self.url} 오류 : {e}")
            logger.error(traceback.format_exc())

