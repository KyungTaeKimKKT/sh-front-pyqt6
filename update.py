from PyQt6.QtWidgets import QMessageBox

import os, json, requests
from urllib.parse import unquote, quote  
import pathlib, shutil
from zipfile import ZipFile
import psutil
import platform
###
from modules.PyQt.User.toast import User_Toast
from config import Config as APP

from info import Info_SW as INFO
### user 
from modules.user.api import Api_SH, Api_SH_update
import modules.user.utils as utils
import time


from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger

ST = StyleSheet()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Update():
    def __init__(self):
        self.latest_Info = {}        
        self.is_Run = True

    def run(self):        
        while self.is_Run:
            self.update_routine()
    
    def update_routine(self) ->str:
        if self.get_info_from_api():
            if self.is_same_version():
                return ''
            else:
                return self.upgrade_processing()

        else: return ''
    
    def upgrade_processing(self) -> bool:
        # User_Toast(parent=None, title="APP Upgrade", text='APP Upgrade진행중입니다.', style="INFORMATION")
        if (path := self.get_latestFile() ) is not None:
                return self.fName
        return False

    def stop(self):
        self.is_Run = False
        return True

    # def read_info(self) -> bool:
    #     try:
    #         with open('./_info.json', 'r', encoding='UTF-8') as f:
    #             INFO = json.load(f)
    #         return True
    #     except:
    #         INFO ={}
    #         return False
    #     # print ( INFO)
    
    def get_info_from_api(self):
        api = Api_SH_update()        
        info_list = api.getlist( INFO.API_Update_URL+ f"?App이름={INFO.APP_Name}&OS={INFO.OS_choiceName}&page_size=0" )

        if not len(info_list): return False

        self.latest_Info = info_list[0]

        return True
    
    def is_same_version(self):
        if (DB_ver :=float(self.latest_Info.get('버젼') ) )== ( local_ver := INFO.Version ) :

            return True
        else: 
            msg = f' 현재 {local_ver} 버전에서 {DB_ver} 버전으로  upgrade  입니다. <br><br><br>설치파일 다운로드 완료시 자동 실행됩니다.<br>  '
            self.msgBox = QMessageBox()
            self.msgBox.setInformativeText('새로운 버젼으로 Upgrade 준비중입니다.' )            
            self.msgBox.setStyleSheet (ST.sw_upgrade_msgbox )
            
            match INFO.종류:
                case 'I':
                    self.msgBox.setStandardButtons(QMessageBox.Ok)
                    self.msgBox.setText( msg)
                    self.msgBox.exec()
                    return False
                case 'U':
                    self.msgBox.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
                    self.msgBox.setDefaultButton(QMessageBox.Ok)
                    msg += '<br> update용(python script file) update 하시겠습니까? <br><br>'
                    self.msgBox.setText( msg)
                    ret = self.msgBox.exec()
                    match ret:
                        case QMessageBox.Ok:
                            return False 
                        case QMessageBox.Cancel :
                            return True ### version 같은 것으로 하여 update 안함

            return False

    def get_latestFile(self):
        response = requests.get( self.latest_Info.get('file'))
        if response.ok:
            pathlib.Path('./download').mkdir(parents=True, exist_ok=True)



            if 'utf-8' in ( raw := response.headers.get("Content-Disposition") ) :
                raw_fname = raw.split("filename*=")[1]
                fName = unquote(raw_fname.replace("utf-8''", ""))
            else :
                raw_fname = raw.split("filename=")[1]
                fName = raw_fname.replace('"','' )

            self.fName = './download/'+fName
            with open(self.fName, 'wb') as download:
                download.write(response.content)
            
            return self.fName

        else:

            return None

    #### update는 zip file로 ==> EXE FILE시, 실행에???
    def extract(self, path):
        if path is not None:
            application_path = os.path.dirname(os.path.realpath(__file__))

            match INFO.OS_choiceName:
                case 'W':
                    pass
                    # application_path = pathlib.Path(application_path).parent.absolute()
                    # application_path = os.path.join( application_path, 'update')
                case 'L':
                    application_path = application_path
                    with ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(os.path.join(application_path) )
                case 'R':
                    application_path = application_path
                    with ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(os.path.join(application_path) )


    def check_stop_this_process_running(self):
        if INFO.PID_Main :
            if psutil.pid_exists(INFO.PID_Main):
                return self.kill_pid(INFO.PID_Main)
        return True



    def kill_pid(self, pid:int=None):
        p = psutil.Process(pid)
        try :
            p.terminate()

            return True
        except Exception as e:

            return False


    def restart_Main_App(self):
        import subprocess
        try:
            match INFO.OS_choiceName:
                case 'W':
                    self.msgBox.accept()
                    subprocess.call( [f"{self.fName}"])
                    # rt_code =subprocess.call ( ['main.exe'])
                case 'L':
                    rt_code =subprocess.call ( ['python','main.py'])
                case 'R':
                    rt_code =subprocess.call ( ['python','main.py'])
            
            return True
        except Exception as e:

            return False
        # self.stop()
        # return None





# update = Update()
# update.run()


# def main():    
#     update = Update()
#     update.run()


#     app = QtWidgets.QApplication(sys.argv)
#     MainWindow = MyWindow()
#     # ui = Ui_MainWindow()
#     # ui.setupUi(MainWindow)
#     # MainWindow.show()
#     sys.exit(app.exec_())


# if __name__ == "__main__":
#     main()
