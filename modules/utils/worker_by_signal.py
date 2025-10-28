from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from copy import deepcopy
from modules.global_event_bus import event_bus
from PyQt6.QtCore import *
import time
from config import Config as APP
from info import Info_SW as INFO
import modules.user.utils as Utils
import copy
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Signal_Worker(QObject):
    finished = pyqtSignal(object,bool, object)

class Worker_by_signal(QRunnable):
    """
    Callable(worker) 실행 후 결과를 시그널로 전달하는 범용 QRunnable
    - worker는 임의의 반환값을 가질 수 있음 (tuple/list/dict/None/객체)
    - kwargs를 통해 worker에 인자 전달 가능
    - emit 시 mutable 객체는 deepcopy 처리
    """
    def __init__(self, worker: Callable,  **kwargs):
        super().__init__()
        self.worker = worker
        self.kwargs = kwargs
        self.signal = Signal_Worker()
        self.setAutoDelete(True)
        self.result = False

    def run(self):
        response = None
        try:
            start_time = time.perf_counter()
            # worker 실행
            res = self.worker(**self.kwargs)
            # print (f"res: {res}")
            self.result = True
            # mutable 객체 안전을 위해 deepcopy
            response = copy.deepcopy(res)
            if INFO.IS_DEV:
                logger.info(f"Worker_by_signal: {self.worker.__name__} 완료, 소요시간: {1000*(time.perf_counter()-start_time):.2f} msec")
        except Exception as e:
            logger.error(f"Worker_by_signal 예외: {e}")
            logger.error(traceback.format_exc())
            self.result = False
        finally:
            self.signal.finished.emit(self, self.result, response)

    def start(self):
        """스레드풀에서 비동기 실행"""
        QThreadPool.globalInstance().start(self)
        return self