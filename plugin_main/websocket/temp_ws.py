from typing import Callable
import threading
import websocket
import json

class TempWSClient:
    def __init__(self, url:str, on_message:Callable, on_error:Callable=None):
        self.url = url
        self.on_message = on_message
        self.on_error = on_error
        self.ws = None
        self.thread = None
        self._running = threading.Event()

    def start(self):
        def run():
            self._running.set()
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=lambda ws, msg: self.on_message(self.url, json.loads(msg)),
                on_error=lambda ws, err: self.on_error and self.on_error(self.url, str(err)),
                on_close=lambda ws, code, reason: self._running.clear()
            )
            # ping_interval 지정하면 죽은 연결도 감지 가능
            self.ws.run_forever(ping_interval=30, ping_timeout=10)

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def send(self, msg: dict):
        if self.ws and self._running.is_set():
            try:
                self.ws.send(json.dumps(msg))
            except Exception as e:
                if self.on_error:
                    self.on_error(self.url, f"send error: {e}")

    def stop(self):
        """WS 연결을 종료만 (스레드는 join 안 함)"""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self._running.clear()

    def close(self, timeout: float = 3.0):
        """WS 종료 + 스레드 정리"""
        self.stop()
        if (
            self.thread 
            and self.thread.is_alive() 
            and threading.current_thread() != self.thread
        ):
            self.thread.join(timeout=timeout)
        self.ws = None
        self.thread = None
        self._running.clear()