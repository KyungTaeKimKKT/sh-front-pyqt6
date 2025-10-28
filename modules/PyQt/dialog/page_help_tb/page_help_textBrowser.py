from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy

from modules.PyQt.dialog.page_help_tb.ui.Ui_dialog_page_info import Ui_Dialog_textEdit
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_Help_Page ( QDialog ):
    """         
        kwargs  \n
            text_원본 : str \n\n
        signal  \n
            signal_accepted --> str

    """
    def __init__(self, parent, **kwargs ):
        self.text_원본 : str
        self._windowTitle : str
        super().__init__(parent)

        for key, value in kwargs.items():
            setattr(self, key, value)
        

        self.ui = Ui_Dialog_textEdit()
        self.ui.setupUi(self)

        self.setWindowTitle ( self._windowTitle if hasattr(self, '_windowTitle') and len(self._windowTitle) else 'Page Help')

        self.ui.pb_ok.clicked.connect( self.close )
       

        self._update_tb( self.text_원본 if hasattr(self, 'text_원본') else '' )
        self.show()

    
    def _update_tb(self, text:str) -> None:
        self.ui.textBrowser.setAcceptRichText(True)
        self.ui.textBrowser.setText(text)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ex = Dialog_Help_Page (None)
    sys.exit(app.exec())

    
    
        
