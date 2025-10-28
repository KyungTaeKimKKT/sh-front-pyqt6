import time
import requests
from typing import Dict, Optional

from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal

## 설정 불러오기
from info import Info_SW as INFO


# ---- 공용 설정 ----
_threadpool = QThreadPool.globalInstance()

def ns_now() -> str:
    return str(int(time.time() * 1e9))


def build_stream(message: str, level: str, labels: Optional[Dict[str, str]] = None):
    base = {
        "job": "PyQt6-Logger",
        "app": INFO.APP_Name,
        "user": INFO.USERNAME,
        "host": INFO._get_HOSTNAME(),
        "ip": INFO._get_IP(),
        "level": level.upper(),
    }
    if labels:
        base.update(labels)
    return [{"stream": base, "values": [[ns_now(), message]]}]


# ---- 비동기 작업 ----
class LokiPushTask(QRunnable):
    def __init__(self, streams: list, loki_url: str):
        super().__init__()
        self.setAutoDelete(True)
        self.streams = streams
        self.loki_url = loki_url

    def run(self):
        try:
            with requests.Session() as s:
                r = s.post(self.loki_url, json={"streams": self.streams}, timeout=2)
                r.raise_for_status()
            if INFO.IS_DEV:
                print("[LOKI] OK", r.status_code)
        except Exception as e:
            if INFO.IS_DEV:
                print("[LOKI] FAIL:", e)


# ---- 메인 함수 ----
def log_loki(
    message: str,
    level: str = "INFO",
    labels: Optional[Dict[str, str]] = None,
    async_mode: bool = True,
):
    if not INFO.LOKI_ENABLE:
        return

    streams = build_stream(message, level, labels)
    if async_mode:
        _threadpool.start(LokiPushTask(streams, INFO.LOKI_URL))
    else:
        try:
            r = requests.post(INFO.LOKI_URL, json={"streams": streams}, timeout=2)
            r.raise_for_status()
            if INFO.IS_DEV:
                print("[LOKI] OK", r.status_code)
        except Exception as e:
            if INFO.IS_DEV:
                print("[LOKI] FAIL:", e)


# ---- 편의용 단축 함수 ----
def info(msg: str, **kw):     log_loki(msg, level="INFO", **kw)
def debug(msg: str, **kw):    log_loki(msg, level="DEBUG", **kw)
def error(msg: str, **kw):    log_loki(msg, level="ERROR", **kw)
def critical(msg: str, **kw): log_loki(msg, level="CRITICAL", **kw)



# def log_loki_async(
#     message: str,
#     labels: Optional[Dict[str, str]] = None,
#     loki_url: str = INFO.LOKI_URL,
#     is_dev: bool = INFO.IS_DEV,
# ) -> LokiPushTask:

#     """
#     # ---- 사용 예 ----
#     # task = log_loki_async("login success", {"app": "sh-app", "user": "shinwoohipo"}, is_dev=True)
#     # task.signals.ok.connect(lambda: print("pushed"))
#     # task.signals.fail.connect(lambda err: print("push failed:", err))
#     """
#     if INFO.LOKI_ENABLE:
#         task = LokiPushTask(
#             line=message,
#             labels=labels or {},
#             loki_url=loki_url,
#             is_dev=is_dev,
#         )
#         _threadpool.start(task)
#         return task


