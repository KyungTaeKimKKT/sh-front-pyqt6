from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import time

from modules.webEngine.googlemap.ui.Ui_google_map_dialog import Ui_Dialog
import traceback
from modules.logging_config import get_plugin_logger

# from ui.Ui_google_map_dialog import Ui_Dialog


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Google_Map_Dialog( QDialog, Ui_Dialog) :
    def __init__(self, parent=None, location:str='', **kwargs):        
        super().__init__(parent)
        for k, v in kwargs:
            setattr( self, k, v)

        self.search_str = location
        """ 😀 location은 goolgemap 초기화 할 때 사용하므로 필수"""
        

        self.setupUi(self)

        self.wid_GoogleMap.signal_loadFinished.connect( self.slot_GoolgeMap_loadFinished )
        self.PB_Search.clicked.connect ( self.on_PB_Search_clicked )

        self.show()
        # mo = self.metaObject()
        # for m in range(mo.methodOffset(), mo.methodCount()):

        

    @pyqtSlot()
    def on_PB_Search_clicked(self):
        self.action_search()

    @pyqtSlot(bool)
    def slot_GoolgeMap_loadFinished(self, is_ok):

        if is_ok and self.search_str:
            self.set_search_str(self.search_str)
            QTimer.singleShot( 1000, lambda: self.action_search(self.search_str) )

    @pyqtSlot()
    def on_lineEditJuso_textChanged(self):
        pass

    
    ### methods
    def action_search(self, search_str:str=''):
        search_str = search_str if search_str else self.get_search_str()

        self.wid_GoogleMap.run(location=search_str)

    def set_search_str(self, search_str:str='') ->None:
        self.lineEditJuso.setText(search_str)

    def get_search_str(self) -> str:
        return self.lineEditJuso.text()
    

    
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    demo = Google_Map_Dialog()
    demo.show()
    sys.exit(app.exec())