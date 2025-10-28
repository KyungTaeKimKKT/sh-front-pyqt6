from cryptography.fernet import Fernet
import os
import errno
import json
import datetime
import traceback
from modules.logging_config import get_plugin_logger


LOGIN_JSON_FILE = '_info_login.json'


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Login_Info :
    """ fName은 default : '_info_login.json' , login_info는 api send data, timedelta는 자동 login이 유지되는 기간: 단위 day"""
    def __init__(self, fName:str=None, login_info:dict={}, end_time:datetime.datetime|None=None ) -> None:
        self.defaultName = LOGIN_JSON_FILE
        self.fName = self.defaultName if fName is None else fName
        self.id = login_info.get('user_mailid') if bool(login_info) else None
        self.pwd = login_info.get('password') if bool(login_info) else None
        self.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None
        self.end_time_datetime = end_time
        self.info = {}
        self.result = {}
        if bool(login_info) or end_time is None :
            if self.readFile():
                self.fernet = Fernet( str.encode(self.info.get('key')) )
    
    def generate(self):
        self.info['key'] = self.get_key()
        self.fernet = Fernet( self.info.get('key'))
        self.info['user_mailid'] = self.encrpyt(self.id)
        self.info['password'] = self.encrpyt(self.pwd)
        self.info['end_time'] = self.encrpyt(self.end_time)

    def write(self) -> bool:
        self.generate()
        return self.writeFile()

    def read(self) -> dict:
        if not self.readFile() : return {}
        for (key,value) in self.info.items():
            if key == 'key': continue
            self.result[key] = self.decrpty(value)
        return self.result

    def writeFile(self) -> bool:
        if os.path.isfile(self.fName):
            os.remove(self.fName)

        if not  os.path.isfile(self.fName):
            try:
                with open(self.fName, "w") as f:
                    json.dump(self.info, f)
                return True
            except OSError as exc: # Guard against race condition
                return False
                if exc.errno != errno.EEXIST:                    
                    raise
    
    def deleteFile(self):
        if os.path.isfile(self.fName):
            os.remove(self.fName)

    def updateFile(self, **kwargs ):
        """ kwargs: \n
            new_pwd :str \n
        """
        if os.path.isfile(self.fName) :
            try:
                self.readFile()
                self.info['password'] = self.encrpyt(kwargs['new_pwd'])
                with open(self.fName, "w") as f:
                    json.dump(self.info, f)
                return True
            except OSError as exc: # Guard against race condition
                return False


    def readFile(self) -> bool:
        if os.path.isfile(self.fName):
            try:
                with open(self.fName, "r") as f:
                    self.info = json.load(f)
                return True
            except OSError as exc: # Guard against race condition
                return False
                if exc.errno != errno.EEXIST:                    
                    raise
        else: return False

    

    def get_key(self) -> str:
        # generate a key for encryption and decryption
        # You can use fernet to generate nd
        # here I'm using fernet to generate key
        
        return Fernet.generate_key().decode('utf-8')
    
    def encrpyt(self, msg:str='') -> str:
        # then use the Fernet class instance 
        # to encrypt the string string must
        # be encoded to byte string before encryption
        return self.fernet.encrypt(msg.encode()).decode('utf-8')
    
    def decrpty(self, msg:str='') -> str :
        return self.fernet.decrypt(str.encode(msg) ).decode()

# endTime = datetime.datetime.now() + datetime.timedelta(days=7)
# str_Time = endTime.strftime('%Y-%m-%d %H:%M:%S')



# info_Instance = Login_Info(
#     id='admin',
#     pwd='1q2w3e4r5*!!',
#     timedelta=7
# )

# info_Instance.write()

# info_Instance = Login_Info()
# info_dict = info_Instance.read()
