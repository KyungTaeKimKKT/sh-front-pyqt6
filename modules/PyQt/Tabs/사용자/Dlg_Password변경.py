from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtCore import *

import datetime

from modules.PyQt.Tabs.사용자.wid_password_change import Wid_PasswordChange
from modules.PyQt.User.handle_login_info import Login_Info

from info import Info_SW as INFO

class Dlg_Password변경(QDialog):
    def __init__(self, parent , **kwargs ):
        super().__init__(parent)

        layout = QVBoxLayout()
        wid_password = Wid_PasswordChange(self, **kwargs)
        layout.addWidget(wid_password)

        self.setLayout(layout)
        self.setWindowTitle ('비밀번호 변경')
        self.setFixedSize( 400, 300)
        self.show()

        wid_password.signal_passwordChanged.connect ( self.slot_write_loginInfo)

    @pyqtSlot(str)
    def slot_write_loginInfo(self, new_pwd:str) :
        handle_auto_login = Login_Info() 
        if handle_auto_login.updateFile(new_pwd=new_pwd):

        else:

        self.close()
        return 

        def get_end_time( is_dev:bool= False):
            now_datetime = datetime.datetime.now()
            if is_dev:
                return now_datetime+datetime.timedelta( days=7)
            else:
                return  now_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
        formData =  {
            'user_mailid':INFO.USER_INFO['user_mailid'],
            'password'  : new_pwd,
        }
        handle_auto_login = Login_Info(login_info=formData, end_time=get_end_time(INFO.IS_DEV)  )
        handle_auto_login.updateFile()

        self.close()