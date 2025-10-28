from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.PyQt.Tabs.망관리.dialog.ui.Ui_망등록_Dialog import Ui_Dialog as Ui_Dialog_망등록
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from modules.PyQt.User.validator import 망등록_망번호_Validator
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_망등록(QDialog,  Ui_Dialog_망등록,  Qwidget_Utils):
    """ kwargs \n
        url = str,\n
        dataObj = {}
    """
    signal_refresh = pyqtSignal()

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.dataObj = {}        
        self.len_망번호 = 6

        self.url = INFO.URL_망관리_관리

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.setupUi(self)
        self.inputDict ={
            '망번호' : self.lineEdit_MangNo,
            '고객사' : self.widget_Gogaek,
            '현장명' : self.lineEdit_Hyunjang,
            '문양'   : self.lineEdit_Munyang,
            '의장종류' : self.widget_Uljang,
            '할부치수' : self.widget_Halbu,
            '품명'     :  self.widget_Pummyung,
            '망사'     : self.widget_Mangsa,
            '사용구분' : self.widget_SayongGubun,
            '세부내용' : self.plainTextEdit_Sebu,
            '비고'     : self.plainTextEdit_Bigo,
            '검색key'  : self.lineEdit_Gumsaek,
        }

        self.imageViewerDict = {
            'upload_path_1' : self.widget_Image1,
            'upload_path_2' : self.widget_Image2,
        }

        for _, wid in self.imageViewerDict.items():
            wid._resizeFlag = False

        self.lineEdit_MangNo.textChanged.connect( self.check_lineEdit_MangNo_validation)
        self.lineEdit_MangNo.setValidator(망등록_망번호_Validator(qRegEx=None, wid=self.lineEdit_MangNo ) )


    @pyqtSlot()
    def on_PB_Save_clicked(self):
        sendData = self._get_value_from_InputDict()
        imageList = self._get_value_from_ImageViewer()
        ### sendData 보완 
        sendData['author'] = INFO.USERID
        sendData['등록자'] = INFO.USERNAME
        sendData['망사']   = int( sendData['망사']  )

        sendFiles =[]
        for idx, obj in enumerate(imageList):
            keyName = f'file{idx+1}'
            if (file := obj.get('file', None)):
                fileObj = open( obj.get('file'), 'rb')
            elif ( pixMap:= obj.get('pixMap', None) ):
                pixMap : QPixmap
                fName = f"{sendData.get('현장명')}_file{idx+1}"
                fileObj = ( fName,  self._get_Bytes_from_pixmap(pixMap) )
            sendFiles.append ( (keyName, fileObj) )

        is_ok, _json = APP.API.Send( url= self.url,
                                    dataObj= self.dataObj,
                                    sendData=sendData,
                                    sendFiles=sendFiles)
        if is_ok:
            self.signal_refresh.emit()

    @pyqtSlot()
    def on_PB_CheckMangNo_clicked(self):
        if not len( 망번호 := self.lineEdit_MangNo.text() ) : return
        suffix = f"?망번호={망번호}&page_size=0"
        is_ok, _json = APP.API.getlist(self.url+suffix)

        if _json:
            QMessageBox.warning(self, '중복된 망번호', f"{망번호}는 중복되었읍니다.", QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok )        
        self.PB_Save.setEnabled( not bool(len(_json)) )

    @pyqtSlot()
    def check_lineEdit_MangNo_validation(self) -> None:
        self.PB_CheckMangNo.setEnabled ( len(self.lineEdit_MangNo.text()) == self.len_망번호 )

    def viewMode(self):
        self.setWindowTitle('망 등록정보 View')
        self.PB_CheckMangNo.hide()
        self.PB_Save.setText('확인')
        self.PB_Save.setEnabled(True)
        self.PB_Save.clicked.disconnect()
        self.PB_Save.clicked.connect(self.close )
        super().viewMode()