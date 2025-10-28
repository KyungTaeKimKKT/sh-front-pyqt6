# network_viewer/pinger.py
from PyQt6.QtCore import pyqtSignal, QObject
import asyncio
import aioping
import time

class PingManager(QObject):
    ping_updated = pyqtSignal(dict)

    def __init__(self, targets:list[str]):
        super().__init__()
        self.targets = targets

    async def _ping_target(self, ip):
        try:
            await aioping.ping(ip, timeout=1.0)
            return ip, True
        except Exception:
            return ip, False

    async def _run_all(self):
        start_time = time.time()
        tasks = [self._ping_target(ip) for ip in self.targets]
        results = await asyncio.gather(*tasks)
        result_dict = dict(results)
        self.ping_updated.emit(result_dict)
        end_time = time.time()
        print(f"Ping 실행 시간: {end_time - start_time}초")

    def run_once(self):
        asyncio.run(self._run_all())



    # async def ping_target(self, ip):
    #     try:
    #         await aioping.ping(ip, timeout=1.0)
    #         return ip, True
    #     except asyncio.TimeoutError:
    #         return ip, False
    #     except Exception:
    #         return ip, False

    # async def run(self):
    #     self._running = True
    #     while self._running:
    #         # 모든 ping을 병렬 실행
    #         start_time = time.time()
    #         tasks = [self.ping_target(ip) for ip in self.targets]
    #         results = await asyncio.gather(*tasks)
    #         end_time = time.time()
    #         print(f"Ping 실행 시간: {end_time - start_time}초")

    #         for ip, status in results:
    #             self.results[ip] = status
            
    #         # ✅ UI에 emit
    #         self.ping_updated.emit(self.results.copy())

    #         await asyncio.sleep(self.interval)

    # def stop(self):
    #     self._running = False

    # def get_results(self):
    #     return self.results.copy()