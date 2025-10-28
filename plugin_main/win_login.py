import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.sub_window.ui.Ui_login import Ui_Form

import copy, time
from modules.user.api import Api_SH
import requests
from config import Config as APP
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.fastapi_urls import fastapi_urls as FastAPI_URLS
from local_db.models import Login_User
import uuid
import datetime
import traceback
import modules.user.utils as Utils
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Server_URL_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.UI()

    def UI(self):
        self.setWindowTitle("접속서버 선택")
        
        main_layout = QVBoxLayout()

        # 서버 입력 줄
        server_layout = QHBoxLayout()
        label_server = QLabel("서버 :")
        self.line_edit_server = QLineEdit(self)
        self.line_edit_server.setText('192.168.7.129')
        server_layout.addWidget(label_server)
        server_layout.addWidget(self.line_edit_server)

        # 포트 입력 줄
        port_layout = QHBoxLayout()
        label_port = QLabel("포트 :")
        self.line_edit_port = QLineEdit(self)
        self.line_edit_port.setText('9999')
        port_layout.addWidget(label_port)
        port_layout.addWidget(self.line_edit_port)

        # 저장 및 취소 버튼
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # 전체 레이아웃 구성
        main_layout.addLayout(server_layout)
        main_layout.addLayout(port_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_url(self) -> tuple[str, str]:
        return self.line_edit_server.text().strip(), self.line_edit_port.text().strip()


class Login(QDialog):

    def __init__(self,  parent=None, face_recognition_login_data:dict=None, **kwargs):
        super().__init__(parent=parent)

        self.event_bus_type = GBus.LOGIN
        self.event_bus = event_bus

        self.login_info = None

        self.setup_shortcuts()

        if face_recognition_login_data:
            self.process_ok_face_recognition(face_recognition_login_data)
            return
        
        self.run()

    def setup_shortcuts(self):
        # Ctrl + S 또는 S 키에 대한 단축키 설정
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.show_server_dialog)

    def show_server_dialog(self):
        dialog = Server_URL_Dialog(self)
        if dialog.exec():
            server_url, port = dialog.get_url()
            INFO._update_SERVER(server_url, port)
            self.reload_ui()

    #     dialog = QDialog(self)
    #     dialog.setWindowTitle("접속서버 선택")
        
    #     layout = QVBoxLayout()
    #     label = QLabel("접속서버 선택", dialog)
    #     line_edit = QLineEdit(dialog)
        
    #     # 저장 및 취소 버튼 추가
    #     button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
    #     button_box.accepted.connect(lambda: self.save_url(line_edit.text().strip(), dialog))
    #     button_box.rejected.connect(dialog.reject)
        
    #     layout.addWidget(label)
    #     layout.addWidget(line_edit)
    #     layout.addWidget(button_box)
        
    #     dialog.setLayout(layout)
    #     dialog.exec()

    # def save_url(self, url, dialog):
    #     logger.info(f"입력한 URL: {url}")
    #     INFO._update_SERVER(url)
    #     dialog.accept()
    #     self.reload_ui()

    def reload_ui(self):
        # 기존 위젯들 제거 (중복되지 않게)
        if hasattr(self, 'ui'):
            self.disconnect_signals()
            self.clear_layout()
            self.ui = None

        # 서버 정보 다시 로드, 이미지 다시 받고
        self.UI()

    def clear_layout(self):
        layout = self.layout()
        if layout is not None:
            # 모든 위젯 제거
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
            # 레이아웃 제거
            QWidget().setLayout(layout)

    ### 안됨..ㅜㅜ;;
    # def restart_login(self):
    #     global login_window
    #     self.close()
    #     login_window = Login()
    #     QTimer.singleShot(0, login_window.run)

    def get_logo(self) -> QPixmap:
       # 서버에서 이미지 요청
        start_time = time.time()
        #    response = requests.get(f'{INFO.URI}/config/resources/login-logo/')
        url = INFO.URI_FASTAPI + FastAPI_URLS.URL_RESOURCES_LOGIN_LOGO
        response = requests.get( url )
                
        logger.info(f"이미지 요청 완료 :{url}: {response.status_code}")
        if response.status_code == 200:
            # 이미지 데이터를 QPixmap으로 변환
            try:
                image_data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(image_data))
                end_time = time.time()
                logger.info(f"이미지 로드 완료 : {int((end_time - start_time)*1000)} msec")
                return pixmap
            except Exception as e:
                logger.error(f"이미지 로드 오류: {e}")
                logger.error(f"{traceback.format_exc()}")
                return None
        else:
            logger.error(f"Error: {response.status_code}")           
            return None

    def UI(self):
        self.formData = {}
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        _pixmap = self.get_logo()
        if _pixmap:
            self.ui.label.setPixmap(_pixmap)
        else:
            self.ui.label.setText("서버와 통신이 불안정합니다. 잠시 후 다시 시도해주세요.")

        ### 개발자, 사용자에 따라 : INFO.IS_DEV
        if not INFO.IS_DEV:
            self.ui.ck_box_autoLogin.setText ( "오늘은 자동 Login 합니다")

        self.inputDict = {
            'user_mailid':self.ui.lineEdit_MailID,
            'password'  : self.ui.lineEdit_Password,
        }
        self.TriggerConnect()
        self.show()

    def run(self):
        if self.check_auto_login():
            if self.auto_login():
                self.event_bus.publish(self.event_bus_type, True)
                self.accept()
                return 
                self.close()
                return 
        
        self.UI()


    def auto_login(self) -> bool:        
        try:
            api = Api_SH()
            api.set_refresh_token(self.login_info.refresh_token)
            success = api.regen_access_key()
            logger.info(f"자동 로그인 regen_access_key: {success}")
            if success:
                APP.API = api
                #### 토큰 갱신 타이머 시작
                api.start_jwt_refresh_timer()
                # 사용자 정보 업데이트
                INFO._update_UserInfo({
                    'id':self.login_info.user_id,
                    'user_mailid':self.login_info.user_mailid,
                    'user_성명':self.login_info.user_성명,
                })
                return True
            return False
        except Exception as e:
            logger.error(f"자동 로그인 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return False


    def check_auto_login(self)-> bool:
        """ 자동 로그인 정보 확인 """
        try:
            
            for info in Login_User.objects.all():
                logger.info(f"자동 로그인 정보: { {k:v for k,v in info.__dict__.items()  } }")
            self.login_info = Login_User.objects.filter(
                    created_at__date=datetime.datetime.now().date(),
                    is_auto_login=True).order_by('-id').first()    
            logger.info(f"자동 로그인 정보: {self.login_info}")
            if self.login_info and self.login_info.refresh_token and self.login_info.is_auto_login:
                logger.info(f"자동 로그인 정보 확인 완료: True")
                return True
            return False
        except Exception as e:
            logger.error(f"자동 로그인 정보 확인 오류: {e}")
            return False

    def TriggerConnect(self):
        self.ui.PB_save.clicked.connect(self.slot_pb_save)
        self.ui.PB_cancel.clicked.connect(self.slot_pb_cancel)
        for _, input in self.inputDict.items():
            input.textChanged.connect(self.check_Input )

    def disconnect_signals(self):
        try:
            self.ui.PB_save.clicked.disconnect()
            self.ui.PB_cancel.clicked.disconnect()
            for _, input in self.inputDict.items():
                input.textChanged.disconnect()
        except Exception as e:
            logger.error(f"disconnect_signals 오류: {e}")

    ### for face recognition login
    def process_ok_face_recognition(self, res:dict):
        api = Api_SH()
        api.process_ok(res)
        self.process_ok(res, api)

    ##### slots #####
    @pyqtSlot()
    def slot_pb_save(self):
        self.formData = { key:input.text() for key, input in self.inputDict.items() }
        if INFO.IS_DEV:
            self.formData['is_dev'] = True
        
        try:
            api = Api_SH()
            _is_ok, res = api.get_jwt(login_info=self.formData)
            if _is_ok:
                self.process_ok(res, api=api)
                return 
                # self.close()
            else:
                msgBox = QMessageBox.warning(self, "Warning", "Mail ID와 Password가 일치하지 않읍니다.")
                for key, input in self.inputDict.items():
                    input.setText('')
        except Exception as e:
            logger.error(f"로그인 처리 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            msgBox = QMessageBox.critical(self, "Error", "로그인 처리 중 오류가 발생했읍니다.")


    def process_ok(self, res:dict, api:Api_SH=None):
        # 자동 로그인 정보 저장
        try:
            is_auto_login = self.ui.ck_box_autoLogin.isChecked()
        except Exception as e:
            is_auto_login = False
            
        Login_User.objects.all().delete()
        self.login_info = Login_User.objects.create(
            user_id = res['user_info']['id'], 
            user_mailid = res['user_info']['user_mailid'], 
            user_성명 = res['user_info']['user_성명'], 
            refresh_token = res['refresh'], 
            is_auto_login = is_auto_login,
            created_at = datetime.datetime.now() 
        )
        logger.info(f"로그인 정보 저장: {self.login_info}")
        APP.API = api
        INFO._update_UserInfo(res['user_info'])

        ### 25-8-8 추가
        if res['ws_url_db']:
            INFO.set_WS_URLS(res['ws_url_db'])
        else:
            logger.critical(f"res['ws_url_db'] is None")
        #### 25-8-13
        if res['is_app_admin']:
            INFO._set_is_app_admin(res['is_app_admin'])
        else:
            INFO._set_is_app_admin(False)
        if res['is_table_config_admin']:
            INFO._set_is_table_config_admin(res['is_table_config_admin'])
        else:
            INFO._set_is_table_config_admin(False)
        self.event_bus.publish(self.event_bus_type, res['user_info'])
        self.accept()
    
    @pyqtSlot()
    def slot_pb_cancel(self):
        self.event_bus.publish(self.event_bus_type, None)
        self.reject()
        return 
        self.close()

    @pyqtSlot()
    def check_Input(self):
        """ all input의 length가 >0 이면 일단 save button enable"""
        self.ui.PB_save.setEnabled ( all([ bool( len(wid.text()) ) for _, wid in self.inputDict.items()] ))

    ########################################

    # ##### Major Methods ####
    # def process_login(self):       
    #     try:  
            
    #             is_ok ,res = api.get_jwt(login_info=self.formData )
    #             if is_ok:
    #                 ### 자동 로그인을 위해 DB 저장
    #                 if self.ui.ck_box_autoLogin.isChecked():                        
    #                     Login_User.objects.create(
    #                         user_id = res['user_info']['id'], 
    #                         user_mailid =self.formData['user_mailid'], 
    #                         user_성명 = res['user_info']['user_성명'], 
    #                         refresh_token = res['refresh'], 
    #                         created_at =datetime.datetime.now() 
    #                     )
    #                 ### config에 API 등록
    #                 APP.API = api
    #                 self.event_bus.publish(self.event_bus_type, copy.deepcopy(res['user_info']) )
    #                 # self.login_result_signal.emit(True, self.formData)
    #                 self.close()
    #             else:
    #                 msgBox = QMessageBox.warning(self,"Warning", "Mail ID와 Passwrod가 일치하지 않읍니다." )
    #                 for key, input in self.inputDict.items():
    #                     input.setText('')
                        
    #     except Exception as e:
    #         logger.error(f"process_login 오류: {e}")
    #         logger.error(f"{traceback.format_exc()}")


    # def auto_login(self):
    #     if bool( formData := self.check_auto_login() ):
    #         self.formData = formData
    #         self.process_login()
    #     else:
    #         self.show()
    
    # def check_auto_login(self) -> dict:
    #     handle_auto_login = Login_Info()
    #     self.auto_login_info = handle_auto_login.read()
    #     _dict = self.auto_login_info.copy()
    #     if bool(_dict):
    #         end_time = datetime.datetime.strptime(_dict.get('end_time') , '%Y-%m-%d %H:%M:%S' )
    #         if ( datetime.datetime.now() <= end_time ):
    #             _dict.pop('key', None)
    #             _dict.pop('end_time', None)
    #             return _dict
    #     return {}

from plugin_main.websocket.temp_ws import TempWSClient
from plugin_main.menus.ai.face_recoginition import FaceRecognizeDialog_with_grpc
import uuid
class Face_Recognition_Login(FaceRecognizeDialog_with_grpc):
    result_signal = pyqtSignal(dict)
    images_signal = pyqtSignal(list)
    def __init__(self, parent=None, 
                verify_url:str="ai-face/user-face/facelogin_via_rpc/", 
                user_id:int=None, 
                api_client=None,  
                is_hidden:bool=False,
                is_hidden_dlg_status_verify:bool=False,
                **kwargs
                ):
        super().__init__(parent=parent, verify_url=verify_url, user_id=user_id, api_client=api_client, is_hidden=is_hidden, is_hidden_dlg_status_verify=is_hidden_dlg_status_verify, **kwargs)

        self.result = None

        self.btn_verify.click()


    def send_verify(self):
        try:
            data, files = self.get_send_data_and_files()
            res = requests.post( INFO.URI + self.verify_url, data=data, files=files )
            if res.status_code == 200 :
                self.result = res.json()
                self.accept()
            else:
                self.reject()
        except Exception as e:
            logger.error(f"send_verify 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            self.reject()
    

    def closeEvent(self, event):
        print (f"closeEvent: {self}")
        super().closeEvent(event)
        if getattr(self, 'ws_manager', None) and hasattr(self.ws_manager, 'close'):
            QTimer.singleShot(0, lambda: self.ws_manager.close())
            # self.ws_manager.close()


    def set_result(self, result:dict):
        self.result = result

    def get_result(self):
        return self.result

def main():    
    app=QApplication(sys.argv)
    window= Login({'test':'test'})
    window.auto_login()
    # window.show()
    app.exec()


if __name__ == "__main__":
    sys.exit( main())