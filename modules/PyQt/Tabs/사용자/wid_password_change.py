from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import re

from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_PasswordChange(QWidget):
    signal_passwordChanged = pyqtSignal(bool)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.initUI()
        self.url =INFO.URL_PASSWORD_CHANGE
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 비밀번호 규칙 안내 레이블 추가
        rule_label = QLabel('비밀번호 규칙:\n- 최소 8자 이상\n- 영문, 숫자, 특수문자(!@#$%^&*(),.?":{}|<>) 포함')
        rule_label.setStyleSheet('color: #666666; font-size: 10pt;')
                
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
        
        # 유효성 상태 표시 레이블
        self.validation_label = QLabel('')
        self.validation_label.setStyleSheet('color: red; font-size: 10pt;')

        layout.addWidget(rule_label)
        layout.addWidget(self.old_password)
        layout.addWidget(self.new_password)
        layout.addWidget(self.validation_label)
        layout.addWidget(self.confirm_password)
        layout.addWidget(change_btn)
        
        self.setLayout(layout)        
        self.setWindowTitle('비밀번호 변경')

        # 실시간 유효성 검사를 위한 이벤트 연결
        self.new_password.textChanged.connect(self.validate_password)
        
        self.show()
        
    def change_password(self):
        old_pwd = self.old_password.text()
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()
        
        if not all([old_pwd, new_pwd, confirm_pwd]):
            Utils.generate_QMsg_critical(self, title='오류', text='모든 필드를 입력해주세요.')
            return
            
        if not self.validate_password(new_pwd):
            Utils.generate_QMsg_critical(self, title='오류', text='비밀번호는 최소 8자 이상이며, 영문, 숫자, 특수문자를 포함해야 합니다.')
            return

        if new_pwd != confirm_pwd:
            Utils.generate_QMsg_critical(self, titlle='오류', text='새 비밀번호가 일치하지 않읍니다.')
            return
        
        # # 새 비밀번호 유효성 검사
        # is_valid, error_message = self.validate_password(new_pwd)
        # if not is_valid:
        #     Utils.generate_QMsg_critical(self, title='Password Validation 오류', text=error_message)
        #     return
            
        try:
            sendData={
                    'old_password': old_pwd,
                    'new_password': new_pwd,
                    'confirm_password': confirm_pwd
                }
            # API 클래스의 특수 메소드 호출 (비밀번호 변경 및 토큰 갱신)
            _isOk  = APP.API.change_password_and_refresh_token(sendData=sendData, url=self.url)
            
            if _isOk:
                logger.info(f"비밀번호 변경 성공")

                Utils.generate_QMsg_Information(self, title='Password 변경 성공', text='비밀번호가 성공적으로 변경되었읍니다.')
                self.signal_passwordChanged.emit(True)
                self.close()
            else:
                Utils.generate_QMsg_critical(self, title='Password 변경 fail',  text='확인 후 다시 시됴해 주십시요.')
                
        except Exception as e:
            Utils.generate_QMsg_critical(self, title='Server 통신 오류', text=f'서버 통신 중 오류가 발생했읍니다: {str(e)}')

    def validate_password(self, password):
        
        # 비밀번호 규칙 검사
        has_letter = bool(re.search(r'[a-zA-Z]', password))
        has_number = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        is_valid = len(password) >= 8 and has_letter and has_number and has_special
        
        if not password:
            self.validation_label.setText('')
        elif not is_valid:
            missing = []
            if len(password) < 8:
                missing.append('8자 이상')
            if not has_letter:
                missing.append('영문')
            if not has_number:
                missing.append('숫자')
            if not has_special:
                missing.append('특수문자')
            
            self.validation_label.setText(f'필요: {", ".join(missing)}')
            self.validation_label.setStyleSheet('color: red;')
        else:
            self.validation_label.setText('유효한 비밀번호입니다')
            self.validation_label.setStyleSheet('color: green;')
        
        return is_valid
