from PyQt6.QtCore import *

import cv2 , os
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Camera(QThread):
    signal_scan = pyqtSignal(object)

    def __init__(self,parent):
        super().__init__(parent)
        self.is_Run = True
        self.is_Running = False
        self.cam = None

        # Open the default camera
        self.cam = cv2.VideoCapture(0)

    def run(self):
        while self.is_Run and self.cam :
            self.is_Running = True
            ret, frame = self.cam.read()
            if not ret : break            

            self.signal_scan.emit( frame  )
                # barcode = self.read_QR_Code( frame )

                # if barcode and barcode.data !='':
                # # Print the barcode data 
 
 
            # 10ms 기다리고 다음 프레임으로 전환, Esc누르면 while 강제 종료
        #     if cv2.waitKey(10) == 27:
        #         break
        self.cam.release() # 사용한 자원 해제
        cv2.destroyAllWindows()           


    def stop(self):
        # self.is_Run = False
        self.is_Run = False

    def resume(self):
        self.is_Run = True
        self.run()
 
    def get_run_state(self):
        return self.is_Running