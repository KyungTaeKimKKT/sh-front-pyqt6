from PyQt6.QtCore import *

import cv2 , os
from pyzbar import pyzbar
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Barcode_scan(QThread):
    signal_scan = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.is_Run = True
        self.cam = None

        # Open the default camera
        self.cam = cv2.VideoCapture(0)

    def run(self):
        while self.is_Run and self.cam :
            ret, frame = self.cam.read()
            if not ret : break            

            self.signal_scan.emit( frame, frame )
                # barcode = self.read_QR_Code( frame )

                # if barcode and barcode.data !='':
                # # Print the barcode data 
 
 
            # 10ms 기다리고 다음 프레임으로 전환, Esc누르면 while 강제 종료
        #     if cv2.waitKey(10) == 27:
        #         break
        # self.cam.release() # 사용한 자원 해제
        # cv2.destroyAllWindows()           


    def stop(self):
        # self.is_Run = False
        self.is_Run = False

    def resume(self):
        self.is_Run = True
        self.run()
    
    def read_QR_Code ( self, img ) :	     
        # read the image in numpy array using cv2 
        # img = cv2.imread(image) 
        
        # Decode the barcode image 
        detectedBarcodes = pyzbar.decode(img) 
        
        # If not detected then print the message 
        if not detectedBarcodes: 
            pass
 
        else:         
            # Traverse through all the detected barcodes in image 
            for barcode in detectedBarcodes:          
    
                # Locate the barcode position in image 
                (x, y, w, h) = barcode.rect               
                # Put the rectangle in image using  
                # cv2 to highlight the barcode 
                cv2.rectangle(img, (x-10, y-10), 
                              (x + w+10, y + h+10),  
                              (255, 0, 0), 2) 
                
                if barcode.data!="":                 
                    return barcode
                else:
                    return None