from PyQt6.QtWidgets import *


from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_PasswordChange(QWidget):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.old_password = QLineEdit()
        self.old_password.setPlaceholderText('현재 비밀번호')
        self.old_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText('새 비밀번호')
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText('새 비밀번호 확인')
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        change_btn = QPushButton('비밀번호 변경')
        change_btn.clicked.connect(self.change_password)
        
        layout.addWidget(self.old_password)
        layout.addWidget(self.new_password)
        layout.addWidget(self.confirm_password)
        layout.addWidget(change_btn)
        
        self.setLayout(layout)
        self.setWindowTitle('비밀번호 변경')
        
    def change_password(self):
        old_pwd = self.old_password.text()
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()
        
        if not all([old_pwd, new_pwd, confirm_pwd]):
            Utils.generate_QMsg_critical(self, title='오류', text='모든 필드를 입력해주세요.')
            return
            
        if new_pwd != confirm_pwd:
            Utils.generate_QMsg_critical(self, titlle='오류', text='새 비밀번호가 일치하지 않읍니다.')
            return
            
        try:
            sendData={
                    'old_password': old_pwd,
                    'new_password': new_pwd,
                    'confirm_password': confirm_pwd
                },
            _isOk, _json = APP.API.Send( self.url, self.dataObj, sendData )
            
            if _isOk:
                Utils.generate_QMsg_Information(self, title='Password 변경 성공', text='비밀번호가 성공적으로 변경되었읍니다.')
                self.close()
            else:
                Utils.generate_QMsg_critical(self, title='Password 변경 fail',  text='확인 후 다시 시됴해 주십시요.')
                
        except Exception as e:
            Utils.generate_QMsg_critical(self, title='Server 통신 오류', text=f'서버 통신 중 오류가 발생했읍니다: {str(e)}')
    
