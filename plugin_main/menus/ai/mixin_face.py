from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v3 import *
import cv2
import uuid


class Mixin_Face:


    def find_available_camera(self, max_index=10) -> list[int]:
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.release()
                available.append(i)
        return available

    def mixin_init_camera(self):
        # 카메라 & 타이머
        available = self.find_available_camera()
        if len(available) > 0:
            self.cam_index = min(available)
            self.cap = cv2.VideoCapture(self.cam_index)
        else:
           raise Exception("No available camera")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def mixin_init_ws(self, ws_manager=None, ws_url_base:str="broadcast/"):
        self.uuid = str(uuid.uuid4())
        self.ws_manager = ws_manager or APP.get_WS_manager()       
        self.ws_url = f"{ws_url_base}{self.uuid}/"

        if self.ws_url in INFO.WS_TASKS:
            self.ws_manager.remove(self.ws_url)
        
        if self.ws_manager:
            self.ws_manager.add(
                self.ws_url, 
                message_slot_func=self.on_ws_message, 
                error_slot_func=self.on_ws_error
                )
        else:
            print (f"ws_manager is None")

    def on_ws_error(self, url: str, err: str):
        print (f"on_ws_error: {url} {err}")