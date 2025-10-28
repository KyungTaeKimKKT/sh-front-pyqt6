from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.global_event_bus import event_bus
from info import Info_SW as INFO

class MenuManager:
    def __init__(self, parent_window: QMainWindow):
        self.parent_window = parent_window
        self.menubar = None
        
    def render_menu(self):
        self.menubar = QMenuBar(self.parent_window)
        
        # 시스템 메뉴 추가
        self._add_system_menu()
        
        self.parent_window.setMenuBar(self.menubar)
        return self.menubar
        
    def _add_system_menu(self):
        system_menu = self.menubar.addMenu('System')
        
        # 비밀번호 변경 액션
        change_password_action = QAction(
            QIcon(':/app-menu-icons/restart'), 
            '비밀번호 변경', 
            self.parent_window)
        change_password_action.setStatusTip('비밀번호를 변경합니다.')
        change_password_action.triggered.connect(
            lambda: event_bus.publish('system:password_change_requested', {})
        )
        system_menu.addAction(change_password_action)
        
        # 종료 액션
        exit_action = QAction(
            QIcon(':/app-menu-icons/restart'), 
            '종료', 
            self.parent_window)
        exit_action.setStatusTip('종료')
        exit_action.triggered.connect(
            lambda: event_bus.publish('system:exit_requested', {})
        )
        system_menu.addAction(exit_action)
        
        # 자동 로그인 삭제 후 종료 액션
        reset_auto_login_action = QAction(
            QIcon(':/app-menu-icons/restart'), 
            '종료-자동로그인 삭제', 
            self.parent_window)
        reset_auto_login_action.setStatusTip('자동 로그인 삭제-종료')
        reset_auto_login_action.triggered.connect(
            lambda: event_bus.publish('system:exit_reset_auto_login_requested', {})
        )
        system_menu.addAction(reset_auto_login_action)
        
        # 앱 재시작 액션
        restart_action = QAction(
            QIcon(':/app-menu-icons/restart'), 
            '앱 재시작', 
            self.parent_window)
        restart_action.setStatusTip('애플리케이션을 재시작합니다.')
        restart_action.triggered.connect(
            lambda: event_bus.publish('system:restart_application_requested', {})
        )
        system_menu.addAction(restart_action)