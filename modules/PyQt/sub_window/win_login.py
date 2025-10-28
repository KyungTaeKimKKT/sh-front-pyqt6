import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.sub_window.ui.Ui_login import Ui_Form


from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value
from modules.PyQt.User.handle_login_info import Login_Info
from config import Config as APP

from info import Info_SW as INFO

import datetime
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Login(QDialog):

    login_result_signal = pyqtSignal(bool, dict)

    def __init__(self,  parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        ### 개발자, 사용자에 따라 : INFO.IS_DEV
        if not INFO.IS_DEV:
            self.ui.ck_box_autoLogin.setText ( "오늘은 자동 Login 합니다")

        self.inputDict = {
            'user_mailid':self.ui.lineEdit_MailID,
            'password'  : self.ui.lineEdit_Password,
        }
        self.TriggerConnect()

        self.login_info = None
        self.formData = {}   ### 입력된 결과를 저장하고, api send함.
        self.auto_login_info = {}
    
    def TriggerConnect(self):
        self.ui.PB_save.clicked.connect(self.slot_pb_save)
        self.ui.PB_cancel.clicked.connect(self.slot_pb_cancel)
        for _, input in self.inputDict.items():
            input.textChanged.connect(self.check_Input )

    ##### slots #####
    @pyqtSlot()
    def slot_pb_save(self):
        self.formData = { key:input.text() for key, input in self.inputDict.items() }
        self.process_login()
    
    @pyqtSlot()
    def slot_pb_cancel(self):
        self.Signal.emit(False)
        self.close()

    @pyqtSlot()
    def check_Input(self):
        """ all input의 length가 >0 이면 일단 save button enable"""
        self.ui.PB_save.setEnabled ( all([ bool( len(wid.text()) ) for _, wid in self.inputDict.items()] ))

    ########################################

    ##### Major Methods ####
    def process_login(self):        
        def get_end_time( is_dev:bool= False):
            now_datetime = datetime.datetime.now()
            if is_dev:
                return now_datetime+datetime.timedelta( days=7)
            else:
                return  now_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)



        api = Api_SH()
        if api.get_jwt(login_info=self.formData ) :
            if self.ui.ck_box_autoLogin.isChecked():                
                handle_auto_login = Login_Info(login_info=self.formData, end_time=get_end_time(INFO.IS_DEV)  )
                handle_auto_login.write()
            ### config에 API 등록
            APP.API = api
            self.login_result_signal.emit(True, self.formData)
            self.close()

        else:
            msgBox = QMessageBox.warning(self,"Warning", "Mail ID와 Passwrod가 일치하지 않읍니다." )
            for key, input in self.inputDict.items():
                input.setText('')

    def auto_login(self):
        if bool( formData := self.check_auto_login() ):
            self.formData = formData
            self.process_login()
        else:
            self.show()
    
    def check_auto_login(self) -> dict:
        handle_auto_login = Login_Info()
        self.auto_login_info = handle_auto_login.read()
        _dict = self.auto_login_info.copy()
        if bool(_dict):
            end_time = datetime.datetime.strptime(_dict.get('end_time') , '%Y-%m-%d %H:%M:%S' )
            if ( datetime.datetime.now() <= end_time ):
                _dict.pop('key', None)
                _dict.pop('end_time', None)
                return _dict
        return {}

        
def main():    
    app=QApplication(sys.argv)
    window= Login({'test':'test'})
    window.auto_login()
    # window.show()
    app.exec()


if __name__ == "__main__":
    sys.exit( main())