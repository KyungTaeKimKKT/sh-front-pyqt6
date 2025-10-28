import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Add_SW(QMainWindow):

    Signal = pyqtSignal(object)

    def __init__(self,  parent=None, dbData=dict, header=list, inputType=dict):
        super().__init__(parent=parent)
        self.api_DB_list = parent.uiMainW.api_DB_list
        self.dbData = dbData
        self.header = header
        self.inputType = inputType

        self.changed_obj = {}

        self.inputDict = {}
        self.result = {}

        self.setWindowTitle('Add SW')
        self.setGeometry(450, 150, 500, 600)
        self.setMinimumSize( QSize(500, 600) )
        # self.setFixedSize(self.size())
        self.UI()
        self.TriggerConnect()


    def UI(self):
        wid = QWidget(self)
        self.setCentralWidget(wid)

        self.formlayout = QFormLayout()

        for key in self.header:
            (_txt, _input) = self.__gen_element(key, self.dbData.get(key))
            if  _txt is not None  and _input is not None:
                self.formlayout.addRow(_txt, _input)
        self.fileLabel= QLabel()
        self.formlayout.addRow(self.fileLabel)
        hbox = QHBoxLayout()
        hbox.addStretch()
        self.PB_save = QPushButton('저장')
        self.PB_save.setEnabled(False)
        self.PB_cancel = QPushButton('취소')
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

        for key in self.header:        
            if key in ['file', 'timestamp' ] : continue
            else :  self.result[key] = self.__get_value(key)

        self.Signal.emit({'type':'sendData', 'data': self.result, 'files': {'file':open(self.fName,'rb')} })
        self.is_Save = True
        self.func_cancel(is_send=True)
    
    def func_cancel(self, is_send=False):
        if not is_send :self.Signal.emit({'type':'close'})
        self.close()


    def func_FileOpen(self):
        ### ui class라서 ui에서 선언한 self.MainWindow 사용
        ### <class 'tuple'> ('/home/kkt/development/python/gui/release/release.zip', 'All Files (*)')
        fName = QFileDialog.getOpenFileName(self , 'Open file','./')

        if  len(fName[0]):        self.PB_save.setEnabled(True)
        else:        self.PB_save.setEnabled(False)
        self.fName = fName[0]
        self.fileLabel.setText(self.fName)

    ###########################################
    def App_Name_changed(self, value=str):
        # self.changed_obj['App이름'] = value.strip()
        self.check_OS_version()

    def OS_changed (self, value=str):
        # self.changed_obj['OS'] = value.strip()
        self.check_OS_version()
    
    def Div_changed(self, value=str):
        # self.changed_obj['종류'] = value.strip()
        self.check_OS_version()


    def check_OS_version(self):
        self.changed_obj['App이름'] = self.inputDict['App이름'].text()
        self.changed_obj['OS'] = self.inputDict['OS'].currentText()
        self.changed_obj['종류'] = self.inputDict['종류'].currentText()
         
        if (obj := self.get_latest_obj_from_db_list() ) is not None:
            startVer =  float(obj['버젼']) + 0.01
            self.inputDict['버젼'].setRange(startVer, 999.99)


    def get_latest_obj_from_db_list(self):

        for obj in self.api_DB_list:
            result = []
            for key in self.changed_obj.keys():
                value = self.changed_obj[key]
                if self.__get_ChoiceFiled(key, value)  == obj.get(key , None )  : result.append(True)
                else: result.append(False)
            if len(result) == 3 and all(result) : return obj
        return None

    def __get_ChoiceFiled(self, key, value):
        OS_dict = {
            'Windows':'W',
            'Linux':'L',
            'RPi' : 'R',
        }
        종류_dict = {
            '설치용':'I',
            'Update용':'U'
        }
        if key == 'OS':  
            return OS_dict.get(value)
        elif key == '종류': 
            return 종류_dict.get(value)
        elif key == 'App이름':
            return value
    ########################################

    def __get_value(self, key):
        input = self.inputDict[key]
        match self.inputType.get(key):
            case 'QLineEdit()':
                return input.text()
            
            case 'QComboBox()':
                return input.currentText()
            
            case 'QSpinBox':
                return input.value()
            
            case 'QDoubleSpinBox()':
                return input.value()
            
            case 'QCheckBox()':
                return input.isChecked()
            
            case 'QTextEdit()':
                return input.toPlainText()
        
            case _:
                return 'default'

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
            case 'App이름':
                input.setPlaceholderText("App이름을 넣으세요")
                input.textChanged.connect(self.App_Name_changed)
            case 'OS':
                input.addItems(['Windows', 'Linux', 'RPi'])
                input.currentTextChanged.connect(self.OS_changed)
            case '종류':
                input.addItems(['설치용', 'Update용'])
                input.currentTextChanged.connect(self.Div_changed)
            case '버젼':
                input.setDecimals(2)
                input.setRange(0.01, 999.99)
                input.setStepType( QAbstractSpinBox.AdaptiveDecimalStepType) 
            
            case '변경사항':
                input.setPlaceholderText("변경사항등을 넣으세요")

            case 'is_release':
                input.setChecked(True)
 
            case 'is_즉시':
                input.setChecked(True)  
            
            case 'file':
                input.clicked.connect( self.func_FileOpen )

            case 'timestamp'                   :
                return (None, None)
            
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