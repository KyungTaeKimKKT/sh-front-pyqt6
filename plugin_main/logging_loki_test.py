import requests
import time
import concurrent.futures

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from config import Config as APP
from info import Info_SW as INFO
# 쓰레드 풀 생성
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

LOKI_URL = 'http://loki.logging.sh/loki/api/v1/push'

def get_stream(
    job:str="PyQt6-Logger", 
    app:str="test-logger", 
    user:str="shinwoohipo", 
    host:str="localhost",
    message:str="test-message"
) -> dict:
    """
    Get stream data for Loki
    
    :param job: Job name
    :param app: Application name
    :param user: User name
    :param host: Host name
    :param message: Message
    :return: Stream data
    """
    timestamp = str(int(time.time() * 1e9))
    return [
        {
            "stream": {
                "job": job,
                "app": app,
                "user": user,
                "host": host
            },
            "values": [
                [timestamp, message]
            ]
        }
    ]

def send_log_to_loki(streams):
    try:
        response = requests.post(LOKI_URL, json={"streams": streams}, timeout=2)
        response.raise_for_status()
        print("로그 전송 성공:", response.text)
        # 성공 여부 무시하거나 로깅할 수 있음
    except Exception as e:
        print("로그 전송 실패:", e)

def logging_loki_async(streams:list):
    executor.submit(send_log_to_loki, streams)

def logging_loki(msg:str):    
    try:
        response = requests.post(LOKI_URL, json={"streams": get_stream(message=msg)})
        response.raise_for_status()
        print("로그 전송 성공:", response.text)
    except requests.exceptions.RequestException as e:
        print("로그 전송 실패:", e)


class Logging_Loki(QRunnable):
    """
    Logging data for Loki
    
    :param logging_data: Logging data
    :param loki_url: Loki URL
    :return: None
    :logging_data:
    {
        'job': 'PyQt6-Logger',
        'app': 'test-logger',
        'user': 'shinwoohipo',
        'host': 'localhost',
        'message': 'test-message'
    }
    :example:
    Logging_Loki(logging_data={'message': f"login success"}).start()
    
    """
    def __init__(self, logging_data:dict, loki_url:str=INFO.LOKI_URL):
        super().__init__()
        self.logging_data = logging_data
        self.streams = get_stream(**logging_data)
        self.loki_url = loki_url

        self.setAutoDelete(True)

    def start(self):
        QThreadPool.globalInstance().start(self)
        return self

    def run(self):
        try:
            response = requests.post(self.loki_url, json={"streams": self.streams}, timeout=2)
            response.raise_for_status()
            if INFO.IS_DEV:
                print("로그 전송 성공:", response.text)
        except Exception as e:
            if INFO.IS_DEV:
                print("로그 전송 실패:", e)

# 사용 예제
if __name__ == "__main__":
    for i in range(20):
        s = time.perf_counter()
        # logging_loki(msg=f"test-message {i}")
        logging_loki_async(streams=get_stream(message=f"test-message {i}"))
        e = time.perf_counter()
        print(f"소요시간: { int(1000 * (e - s))} milliseconds")
        time.sleep(0.1)


    # 모든 비동기 요청이 끝날 때까지 기다리기
    executor.shutdown(wait=True)