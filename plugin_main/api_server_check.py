from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.global_event_bus import event_bus  
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import psutil
import requests

from config import Config as APP
from info import Info_SW as INFO
from modules.envs.fastapi_urls import fastapi_urls
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Api_Server_Check(QObject):
    """
    PC 자원 사용률 업데이트 이벤트 처리
    url : API 서버 URL
    timer_interval : 업데이트 주기 (ms) , default : 10000ms
    """
    def __init__(self, url:str=fastapi_urls.get_URL('URL_API_SERVER_CHECK_NO_AUTH'), timer_interval:int=10000):
        super().__init__()
        self.event_bus_type:str = GBus.API_STATUS
        logger.debug(f"Api_Server_Check: {fastapi_urls.get_URL('URL_API_SERVER_CHECK_NO_AUTH')}")
        self.url = url
        self.event_bus = event_bus
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_api_server_check)
        self.timer.setInterval(timer_interval)
        self.thread_pool = ThreadPoolExecutor(max_workers=1)

    def start(self):
        self.update_api_server_check()
        self.timer.start()

    def close(self):
        self.timer.stop()
        self.timer.deleteLater()
        self.thread_pool.shutdown(wait=True)   


    def set_timer_interval(self, timer_interval:int):
        self.timer.setInterval(timer_interval)
    
    def get_timer_interval(self):
        return self.timer.interval()

    def stop(self):
        self.timer.stop()

    def update_api_server_check(self):
        """
        API 서버 상태 확인 이벤트 처리
        GET 요청을 보내고 응답 결과를 이벤트로 발행
        """
        self.thread_pool.submit(self.check_api_server)


    def check_api_server(self):
        """
        API 서버 상태 확인 이벤트 처리
        GET 요청을 보내고 응답 결과를 이벤트로 발행
        """
        try:
            # logger.debug(f"check_api_server: {self.url}")

            url = INFO.URI_FASTAPI + self.url
            response = requests.get(url)
            if response.status_code == 200:
                _json = response.json()
                ###{'status': 'success', 'client_ip': '192.168.7.108'}
                # logger.debug(f"check_api_server: {_json}")
                event_bus.publish(self.event_bus_type, True)

            else:
                logger.error(f"check_api_server: {response.status_code}")
                raise Exception(f"API 서버 확인 중 오류 발생:")
            
            # _isOk, _ = APP.API.getObj_byURL(self.url, timeout=5)
            # if not _isOk:   
            #     raise Exception(f"API 서버 확인 중 오류 발생: {_}")
        except Exception as e:
            logger.error(f"API 서버 확인 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            event_bus.publish(self.event_bus_type, False)
        finally:
            ###  요청만 하고, 결과는 API Class에서 처리
            pass
