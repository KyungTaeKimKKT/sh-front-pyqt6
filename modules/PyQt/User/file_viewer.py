from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.component.imageViewer2 import ImageViewer_확대보기
from modules.PyQt.User.pdf_viewer import Pdf_Viewer


import modules.user.utils as Utils
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class FileViewer:
    def __init__ (self, wid:QWidget, data:dict={}):
        self.data = data
        self.parent = wid

    def run(self) :
        if not self.data : return
        for key, fileName in self.data.items():
            match Utils.check_file확장자_view지원( fileName ):
                case 'PDF':
                    Pdf_Viewer(self.parent, self.data)
                case 'IMG':                    
                    if key == 'file':
                        img_view_form = ImageViewer_확대보기(QPixmap(fileName))
                        img_view_form.set_image()
                    elif key == 'url' :
                        img_view_form = ImageViewer_확대보기()
                        img_view_form.set_image_from_URL(fileName)

                case _:
                    pass
                
