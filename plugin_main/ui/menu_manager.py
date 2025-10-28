from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.global_event_bus import event_bus
from plugin_main.websocket.main_ws_init import WS_Manager_by_each
from plugin_main.websocket.handlers.pyro5_handler import Pyro5Handler

from info import Info_SW as INFO
import modules.user.utils as Utils

import platform
import subprocess

#### AI
from plugin_main.menus.ai.image_roi_editor import Dlg_Image_ROI_Editor

import datetime
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.Tabs.사용자.wid_password_change import Wid_PasswordChange

if TYPE_CHECKING:
    from main import MainWindow
    from modules.PyQt.Qthreads.WS_Thread_AsyncWorker import WS_Thread_AsyncWorker

def _connect_rdp_windows(ip, port):
    """ Windows에서 MSTSC (RDP 클라이언트) 실행 """
    try:
        # /v:IP:PORT 옵션 사용
        command = f"mstsc /v:{ip}:{port}"
        subprocess.Popen(command, shell=True)
    except Exception as e:
        print(f"Windows RDP 실행 실패: {e}")


def _connect_rdp_linux(ip, port):
    """ Linux (Ubuntu)에서 RDP 클라이언트 실행 (xfreerdp or remmina) """
    # 우선순위: remmina > xfreerdp
    try:
        # remmina 명령어로 실행
        if _is_command_available("remmina"):
            subprocess.Popen(["remmina", f"rdp://{ip}:{port}"])
        elif _is_command_available("xfreerdp"):
            subprocess.Popen([
                "xfreerdp",
                f"/v:{ip}:{port}",
                "/u:your_username",  # 필요 시 사용자 정보
                "/cert:ignore"       # 인증서 무시 옵션
            ])
        else:
            raise Exception("RDP 클라이언트(remmina, xfreerdp)가 설치되어 있지 않습니다.")
    except Exception as e:
        print(f"Linux RDP 실행 실패: {e}")


def _is_command_available(cmd):
    """ 명령어 설치 여부 확인 """
    from shutil import which
    return which(cmd) is not None


class RDPConnectDialog(QDialog):
    def __init__(self, default_ip: str = "127.0.0.1", default_port: int = 3389, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RDP 서버 접속 정보")
        self.setModal(True)

        self.ip_input = QLineEdit(default_ip)
        self.port_input = QLineEdit(str(default_port))

        self._setup_ui()

        self.result_ip = None
        self.result_port = None

    def _setup_ui(self):
        layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("서버 IP:"))
        ip_layout.addWidget(self.ip_input)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("포트:"))
        port_layout.addWidget(self.port_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("확인")
        cancel_btn = QPushButton("취소")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(ip_layout)
        layout.addLayout(port_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _on_ok(self):
        self.result_ip = self.ip_input.text().strip()
        try:
            self.result_port = int(self.port_input.text())
        except ValueError:
            self.result_port = 3389  # fallback

        self.accept()

    def get_result(self):
        return self.result_ip, self.result_port

class MenuManager:
    def __init__(self, menubar: QMenuBar, **kwargs):
        self.menubar = menubar
        self.main_wid:MainWindow = self.menubar.parent()


        self.default_menu_config = {
            'System':[
                    {
                    'name':'비밀번호 변경',
                    'icon': None,
                    'action': self._on_change_password,
                    'status_tip': '비밀번호를 변경합니다.',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '비밀번호를 변경합니다.',
                },
                {
                    'name':'종료',
                    'icon': None,
                    'action': self._on_exit,
                    'status_tip': '종료',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '종료',
                },
                {
                    'name':'자동 로그인 삭제-종료',
                    'icon': None,
                    'action': self._on_exit_reset_auto_login,
                    'status_tip': '자동 로그인 삭제-종료',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '자동 로그인 삭제-종료',
                },
                {
                    'name':'앱 재시작',
                    'icon': None,
                    'action': self._on_restart_application,
                    'status_tip': '앱 재시작',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '앱 재시작',
                },
            ],
            '원격접속':[
                {
                    'name':'원격조정 요청',
                    'icon': None,
                    'action': self._on_remote_control_request,
                    'status_tip': '원격조정 요청',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '관리자에게 원격조정 요청을 보냅니다.',
                },
                {
                    'name':'원격조정 수락',
                    'icon': None,
                    'action': self._on_remote_control_accept,
                    'status_tip': '원격조정 요청 수락',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '원격조정 요청에 대하여 수락(별도 창 띄우기) 합니다.',
                },
                {
                    'name':'접속서버 원격접속',
                    'icon': None,
                    'action': self._on_server_connect,
                    'status_tip': '접속서버 원격접속',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': True,
                    'visible': True,
                    'tooltip': '접속서버 원격접속',
                },
            ],
            'AI':[
                {
                    'name':'Live HI 영상 설정(RTSP)',
                    'icon': None,
                    'action': self._on_HI_rtsp_live_setting,
                    'status_tip': 'Live HI 영상 설정(RTSP)',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': INFO._get_is_app_admin(),
                    'visible': INFO._get_is_app_admin(),
                    'tooltip': 'Live HI 영상 편집(RTSP)',
                },
                {
                    'name':'얼굴등록',
                    'icon': None,
                    'action': self._on_face_register,
                    'status_tip': '얼굴등록',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': INFO._get_is_app_admin(),
                    'visible': INFO._get_is_app_admin(),
                    'tooltip': '얼굴등록',
                },
                {
                    'name':'얼굴인식',
                    'icon': None,
                    'action': self._on_face_recognize,
                    'status_tip': '얼굴인식',
                    'shortcut': None,
                    'checkable': False,
                    'enabled': INFO._get_is_app_admin(),
                    'visible': INFO._get_is_app_admin(),
                    'tooltip': '얼굴인식',
                },
            ],

        }
        self.menu_config = kwargs.get('menu_config', self.default_menu_config)

        self.map_menu_to_action = {}

        self.setup()

    def setup(self):
        for menu_name, menu_items in self.menu_config.items():
            menu = self.menubar.addMenu(menu_name)
            for item in menu_items:
                action = QAction(item['name'], self.menubar)

                if item.get('icon'):
                    action.setIcon(item['icon'])
                if item.get('shortcut'):
                    action.setShortcut(item['shortcut'])
                if item.get('status_tip'):
                    action.setStatusTip(item['status_tip'])
                if item.get('tooltip'):
                    action.setToolTip(item['tooltip'])


                action.setEnabled(item.get('enabled', True))
                action.setCheckable(item.get('checkable', False))
                action.setVisible(item.get('visible', True))

                action.triggered.connect(item['action'])

                menu.addAction(action)
                self.map_menu_to_action[f"{menu_name}:{item['name']}"] = action

        INFO.MAP_MENU_TO_ACTION = self.map_menu_to_action

    def _on_change_password(self):
        # lambda: event_bus.publish('system:password_change_requested', {})
        dlg = QDialog(self.main_wid)
        layout = QVBoxLayout()

        wid_password = Wid_PasswordChange(dlg)

        wid_password.signal_passwordChanged.connect (lambda _isOk:   dlg.close() if _isOk else None )
        layout.addWidget(wid_password)
        dlg.setLayout(layout)


        dlg.setWindowTitle ('비밀번호 변경')
        dlg.setFixedSize( 400, 300)
        dlg.exec()



    def _on_exit(self):
        # lambda: event_bus.publish('system:exit_requested', {})
        try:            
            self.main_wid.close()
        except Exception as e:
            logger.error(f"종료 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def _on_exit_reset_auto_login(self):
        # lambda: event_bus.publish('system:exit_reset_auto_login_requested', {})
        try:
            from local_db.models import Login_User
            Login_User.objects.all().delete()
            self.main_wid.close()
        except Exception as e:
            logger.error(f"자동 로그인 삭제-종료 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def _on_restart_application(self):
        # lambda: event_bus.publish('system:restart_application_requested', {})
        try:
            self.main_wid.restart_application()
        except Exception as e:
            logger.error(f"애플리케이션 재시작 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def _on_remote_control_request(self):
        if Utils.QMsg_question(self.main_wid, title="원격조정 요청", text="원격조정 요청을 보내시겠습니까?"):

            # 이전 인스턴스 제거 (있다면)
            WS_URL_NAME_원격관리 = INFO.get_WS_URL_by_name('원격관리')
            if WS_URL_NAME_원격관리 in INFO.WS_TASKS:
                old_worker: WS_Thread_AsyncWorker = INFO.WS_TASKS.pop( WS_URL_NAME_원격관리 )
                old_worker.close()

            # 새 인스턴스 생성 및 등록
            self.ws_handler = Pyro5Handler(WS_URL_NAME_원격관리, connect_msg = {
                "action": "remote_control_request",		#### 25-7 초기 연결 요청 : init ==> init_request로 변경
                "from_id": INFO.USERID,
                "from_name": INFO.USERNAME,
                "timestamp": datetime.datetime.now().isoformat()
            })
            self.ws_handler.set_is_request(True)
            
            INFO.WS_TASKS[WS_URL_NAME_원격관리] = self.ws_handler

            print (f"self.ws_handler : {self.ws_handler} start!!!!")


    def _on_remote_control_accept(self):
        from plugin_main.dialog.remote_control_accept import RemoteViewerDialog, RemoteControlClient
        dlg = RemoteViewerDialog()
        ### 녹화는 dialog 안에서 pb_recording 버튼 클릭시 시작
        # dlg.start_recording( "./debug/remote_control_accept.mp4", size=(1600, 1200), fps= 4)
        dlg.exec()
        # dlg.stop_recording()

    def _on_server_connect(self):
        """ 메뉴 클릭 시 OS에 맞게 RDP 접속 실행 """
        
        dlg = RDPConnectDialog(default_ip=INFO.API_SERVER, default_port=3389)
        if dlg.exec():
            rdp_ip, rdp_port = dlg.get_result()
        else:
            return 

        system = platform.system().lower()

        try:
            if "windows" in system:
                _connect_rdp_windows(rdp_ip, rdp_port)
            elif "linux" in system:
                _connect_rdp_linux(rdp_ip, rdp_port)
            else:
                raise Exception(f"지원하지 않는 운영체제: {system}")
        except Exception as e:
            print(f"원격 연결 실패: {e}")
            # 필요 시 QMessageBox로 사용자 알림


    def _on_HI_rtsp_live_setting(self):
        if not Utils.QMsg_question( self.main_wid, title="Live HI 영상 설정(RTSP)", 
                text="""
                Live HI 영상 설정(RTSP)을 진행하시겠습니까?<br>
                Server AI Service 의 설정을 변경하는 것이므로, <br> 
                필히 개발자와 사전에 확인 바랍니다. <br> 
                1:1 scale 이므로 영상이 큽니다. <br>
                
                """
                ):
            return

        editor = Dlg_Image_ROI_Editor(parent=None, url= "rtsp_cam/camera_settings/")
        editor.resize(1200, 1000)

        #### 테스트용
        # editor.main_widget.source_type.setCurrentText("RTSP URL")
        # editor.main_widget.input_path.setText("rtsp://admin:1q2w3e4r5*!!@192.168.14.100:10500")
        # editor.main_widget.btn_load.click()

        if editor.exec():
            pass

    def _on_face_register(self):
        from plugin_main.menus.ai.face_register import FaceRegisterDialog
        dlg = FaceRegisterDialog(parent=None, url="ai-face/user-face/")
        if dlg.exec():
            pass

    def _on_face_recognize(self):
        from plugin_main.menus.ai.face_recoginition import FaceRecognizeDialog_with_grpc
        dlg = FaceRecognizeDialog_with_grpc(
                    parent=None, 
                    verify_url="ai-face/user-face/recognize_via_rpc/", 
                    is_hidden=False, 
                    is_hidden_dlg_status_verify=False)
        if dlg.exec():
            pass