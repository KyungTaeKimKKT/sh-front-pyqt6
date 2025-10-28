from PyQt6.QtCore import *

import time, datetime
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Clock(QThread):
    timeout = pyqtSignal(object)    

    def __init__(self):
        super().__init__()
        self.second = 0

    def run(self):
        while True:
            now = datetime.datetime.now()
            if ( self.second != now.second): 
                self.timeout.emit ( now.strftime("%Y-%m-%d %H:%M:%S"))
                self.second = now.second