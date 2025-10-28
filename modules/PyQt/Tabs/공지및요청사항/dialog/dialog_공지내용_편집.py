from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy
import json
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Dialog_공지내용_편집 ( QDialog ):

    def __init__(self, parent, obj:dict|None=None, url:str|None=None, is_api_send:bool=True, **kwargs ):
        super().__init__(parent)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.url : str = url or ''
        self.obj = obj or {}
        self.resultDict = {}
        self.is_api_send = is_api_send
        self.setupUi()

        if self.obj:
            self._update_Text( self.obj.get('공지내용') )


    def setupUi(self):
        self.setWindowTitle('공지사항 작성 / 편집')
        self.resize(1000, 800)
        self.mainLayout = QVBoxLayout(self)

        self.lb_caution = QLabel('<span style="color: orange; font-weight: bold;">🔔</span> 필히 작성 후 저장을 해야 합니다.', self)
        self.lb_caution.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb_caution.setStyleSheet('background-color:black;color:yellow;font-size:24px;font-weight:bold;')
        self.mainLayout.addWidget(self.lb_caution)

        main_container = QWidget(self)
        main_container.setLayout( QHBoxLayout())



        edit_container = QWidget(main_container)
        edit_container.setLayout( QVBoxLayout())
        lb_edit = QLabel(parent=self)
        lb_edit.setText('원본') 
        edit_container.layout().addWidget(lb_edit)
        self.textEdit = QTextEdit(parent=self)
        self.textEdit.setGeometry(QRect(40, 70, 381, 431))
        self.textEdit.setObjectName("textEdit")
        edit_container.layout().addWidget(self.textEdit)

        preview_container = QWidget(main_container) 
        preview_container.setLayout( QVBoxLayout())
        lb_preview = QLabel(parent=self)
        lb_preview.setText('Preview')
        preview_container.layout().addWidget(lb_preview)
        self.textBrowser = QTextBrowser(parent=self)
        self.textBrowser.setAcceptRichText(True)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setOpenLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        preview_container.layout().addWidget(self.textBrowser)

        main_container.layout().addWidget(edit_container)
        main_container.layout().addWidget(preview_container)

        btn_container = QWidget(main_container)
        btn_container.setLayout( QHBoxLayout())
        self.buttonBox = QDialogButtonBox(parent=self)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        btn_container.layout().addStretch() 
        btn_container.layout().addWidget(self.buttonBox)

        self.mainLayout.addWidget(main_container)
        self.mainLayout.addWidget(btn_container)

        self.buttonBox.accepted.connect(self.slot_handle_accepted) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore

        self.textEdit.textChanged.connect(lambda:self._update_TextBrowser(self.textEdit.toPlainText()) )

    def _update_Text(self, text:str ) -> None:
        self.textEdit.setPlainText(text)
    
    def _update_TextBrowser(self, text:str) -> None:
        self.textBrowser.setAcceptRichText(True)
        self.textBrowser.setText ('<p style="background-color:black;color:yellow')
        self.textBrowser.setText(text)

    @pyqtSlot()
    def slot_handle_accepted(self):
        공지내용 = self.textEdit.toPlainText() 
        if self.obj.get('공지내용') == 공지내용:
            self.reject()
            return
        
        if self.is_api_send:
            _isOk, _json = APP.API.Send( self.url, self.obj, {'공지내용': 공지내용})
            if _isOk:
                Utils.generate_QMsg_Information(None, title="공지사항 수정", text="공지사항 수정 되었읍니다.", autoClose=1000)
                self.resultDict = _json
                self.accept()
            else:                
                Utils.generate_QMsg_critical(None, title="공지사항 수정 실패", text=f"공지사항 수정 실패<br> {json.dumps(_json, indent=4)}")
                self.reject()
        else:
            self.resultDict = copy.deepcopy(self.obj)
            self.resultDict['공지내용'] = 공지내용
            print(f"self.resultDict: {self.resultDict}")
            self.accept()

    def get_result(self):
        if self.resultDict:
            if isinstance(self.resultDict, dict):
                return self.resultDict
            elif isinstance(self.resultDict, list):
                return self.resultDict[0]
            else:
                raise ValueError(f"resultDict is not a valid dictionary or list: {type(self.resultDict)}")
        return {}


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ex = Dialog_공지내용_편집(None)
    sys.exit(app.exec())

    
    
        
