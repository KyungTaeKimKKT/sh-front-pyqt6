from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from pathlib import Path

from modules.PyQt.Tabs.일일업무.ui.Ui_dlg_file_upload_전기사용량 import Ui_Dialog_fileUpload
# from Ui_dlg_file_upload_전기사용량 import Ui_Dialog_fileUpload
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_FileUpload_form(QDialog , Qwidget_Utils):
    signal_save = pyqtSignal(QDialog, dict,dict)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.fName_PO = ''
        self.fName_HI = ''
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.ui = Ui_Dialog_fileUpload()        
        self.ui.setupUi(self)
        self.triggerConnect()        

        self.show()

    def triggerConnect(self):
        self.ui.PB_Save.clicked.connect (self.on_PB_Save_clicked)
        self.ui.PB_HI.clicked.connect( self.on_PB_HI_clicked)
        self.ui.PB_PO.clicked.connect( self.on_PB_PO_clicked)

    @pyqtSlot()
    def on_PB_Save_clicked(self):
        ### kwargs : api_Dict 받음
        self.signal_save.emit( self, self.api_Dict, {  '하이전기_file': self.fName_HI, '폴리전기_file': self.fName_PO})

    @pyqtSlot()
    def on_PB_HI_clicked(self):
        options = QFileDialog.Option.DontUseNativeDialog
        title = 'File Upload'
        path = str(Path.home() )
        filter = "Excel Files(*.xlsx);; ALL Files(*.*)"
        self.fName_HI , _ = QFileDialog.getOpenFileName( self, caption=title, directory=path, filter=filter, initialFilter= "Excel Files(*.xlsx)",options=options)
        self.ui.PB_Save.setEnabled( self._is_fNames_all_exist() )
        self.ui.label_HI.setText( self.fName_HI if self.fName_HI else '')

    @pyqtSlot()
    def on_PB_PO_clicked(self):
        # options = QFileDialog.Option.
        options = QFileDialog.Option.DontUseNativeDialog
        title = 'File Upload'
        path = str(Path.home() )
        filter = "Excel Files(*.xlsx);; ALL Files(*.*)"
        self.fName_PO, _ = QFileDialog.getOpenFileName(self, caption=title, directory=path, filter=filter, initialFilter= "Excel Files(*.xlsx)",options=options)
        self.ui.PB_Save.setEnabled( self._is_fNames_all_exist() )
        self.ui.label_PO.setText( self.fName_PO if self.fName_PO else '')

    def _is_fNames_all_exist(self) -> bool:
        return bool(self.fName_HI and self.fName_PO)
    

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    ex = Dialog_FileUpload_form(None, )
    sys.exit(app.exec())
