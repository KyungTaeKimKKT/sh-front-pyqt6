import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Login(QMainWindow):

    Signal = pyqtSignal(object, object)

    def __init__(self,  parent=None):
        super().__init__(parent=parent)
        self.header = ['Mail_ID', 'Password']
       
        self.inputType = {
            'Mail_ID': 'QLineEdit()',
            'Password': 'QLineEdit()',
        }

        self.login_info = None
        self.inputDict = {}
        self.result = {}
        
        self.win_W , self.win_H = 500, 600
        self.setWindowTitle('Login')
        self.setGeometry(450, 150, self.win_W, self.win_H)
        self.setMinimumSize( QSize(self.win_W, self.win_H) )
        self.__center()
        # self.setFixedSize(self.size())
        self.UI()
        self.TriggerConnect()


    def UI(self):
        wid = QWidget(self)
        self.setCentralWidget(wid)

        self.formlayout = QFormLayout()

        self.title = QLabel()
        self.title.setText('환영합니다')
        self.title.setSizePolicy(QSizePolicy.Expanding, 0)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:64px;color:white;background-color:black;")
        self.formlayout.addRow(self.title)

        self.logo = QLabel()
        pixmap = QPixmap(":/images/sw_logo.png" )
        self.logo.setPixmap(pixmap)
        pixmap.scaled(self.win_W,self.win_H,Qt.KeepAspectRatio)
        self.logo.setScaledContents(True)
        self.formlayout.addRow(self.logo)

        for key in self.header:
            (_txt, _input) = self.__gen_element(key, None)
            if  _txt is not None  and _input is not None:
                self.formlayout.addRow(_txt, _input)
        self.fileLabel= QLabel()
        self.formlayout.addRow(self.fileLabel)
        hbox = QHBoxLayout()
        hbox.addStretch()
        self.PB_save = QPushButton('Login')
        self.PB_save.setEnabled(False)
        self.PB_cancel = QPushButton('Cancel')
        hbox.addWidget(self.PB_save)
        hbox.addWidget(self.PB_cancel)
        self.formlayout.addRow(hbox)
        

        wid.setLayout(self.formlayout)
        self.show()

    def TriggerConnect(self):
        self.PB_save.clicked.connect(self.func_save)
        self.PB_cancel.clicked.connect(self.func_cancel)

    ##### Trigger Func. #####
    def func_save(self):
        conversion_dict = {'Mail_ID':'user_mailid',
            'Password': 'password'}
        for key in self.header:        
            if key in ['file', 'timestamp' ] : continue
            else :  self.result[conversion_dict.get(key)] = self.__get_value(key)

        self.process_login(login_info=self.result)

        # self.Signal.emit({'type':'sendData', 'data': self.result, 'files': {'file':open(self.fName,'rb')} })
        # self.is_Save = True

    
    def func_cancel(self, is_send=False):
        # if not is_send :self.Signal.emit({'type':'close'})
        self.close()
    ########################################

    ##### Major Methods ####
    def process_login(self, login_info:dict):        
        api = Api_SH()
        if api.get_jwt(login_info=login_info) :
            self.Signal.emit(api, True)
            self.func_cancel(is_send=True)
        else:
            msgBox = QMessageBox.warning(self,"Warning", "Mail ID와 Passwrod가 일치하지 않읍니다." )
            for key in self.header:
                self.inputDict[key].setText('')


    ###########################################
    def __center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
        
    
    ###########################################
    def Mail_ID_changed(self, value=str):
        # self.changed_obj['App이름'] = value.strip()
        self.check_Input()

    def PWD_changed(self, value=str):
        # self.changed_obj['OS'] = value.strip()
        self.check_Input()
    
    def check_Input(self):
        if self.inputDict['Mail_ID'].text() and self.inputDict['Password'].text():
            self.PB_save.setEnabled(True)


    ########################################
    def __get_value(self, key):
        input = self.inputDict[key]
        value =  Object_Get_Value(input)
        return value.get()


    def __gen_element(self, key=str, value=None):
        setattr(self, key+'_txt', QLabel() )
        txt = getattr(self, key+'_txt' )
        txt.setText(key)
        setattr(self, key+'_input', eval(value) if len(value:= self.inputType[key]) >2 else QLineEdit() )
        input = getattr(self, key+'_input' )

        return self.__gen_by_key(key, value, txt, input)

    ### Hard-coding 
    def __gen_by_key(self, key=str, value=None, txt=object, input=object):
        match key:
            case 'Mail_ID':
                input.setPlaceholderText("사내 MAIL ID를 넣으세요")
                input.textChanged.connect(self.Mail_ID_changed)
            case 'Password':
                input.setPlaceholderText("비밀번호를 넣으세요")
                input.setEchoMode( QLineEdit.Password)
                input.textChanged.connect(self.PWD_changed)
            
            case _:
                pass
                
            
        self.inputDict[key] = input

        return (txt, input)
        

        
# def main():    

#     app=QApplication(sys.argv)
#     window= Add_SW({'test':'test'})
#     # window.show()
#     app.exec_()


# if __name__ == "__main__":
#     sys.exit( main())