from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy

from modules.PyQt.dialog.textedit.ui.Ui_dialog_rich_text_edit import Ui_Dialog_textEdit
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_RichTextEdit ( QDialog ):
    """         
        kwargs  \n
            text_원본 : str \n\n
        signal  \n
            signal_accepted --> str

    """
    signal_accepted = pyqtSignal(str)

    def __init__(self, parent, **kwargs ):
        super().__init__(parent)

        self.text_원본 :str

        for key, value in kwargs.items():
            setattr(self, key, value)
        

        self.ui = Ui_Dialog_textEdit()
        self.ui.setupUi(self)

        self.ui.textEdit.textChanged.connect(self.slot_update_TextBrowser )
        self.ui.buttonBox.accepted.connect(self.slot_handle_accepted  )
        # self.ui.buttonBox.accepted.connect(lambda:self.signal_accepted.emit( self.ui.textEdit.toPlainText()  ))
        

        self._update_TextEdit( self.text_원본 if hasattr(self, 'text_원본') else '' )
        self.show()

    def _update_TextEdit(self, text:str ) -> None:
        self.ui.textEdit.setPlainText(text)
    
    def _update_TextBrowser(self, text:str) -> None:
        self.ui.textBrowser.setAcceptRichText(True)
        self.ui.textBrowser.setText(text)

    @pyqtSlot()
    def slot_handle_accepted(self):
        self.text_원본
        if self.text_원본 != self.get_textEdit_contents() :
            self.signal_accepted.emit (self.get_textEdit_contents()  )

    @pyqtSlot()
    def slot_update_TextBrowser(self):
        self._update_TextBrowser ( self.ui.textEdit.toPlainText() )

    def get_textEdit_contents(self) -> str:
        return self.ui.textEdit.toPlainText()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ex = Dialog_RichTextEdit(None)
    sys.exit(app.exec())

    
    
        
