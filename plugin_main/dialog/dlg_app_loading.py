from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import json, os, io, copy
import platform
import pandas as pd
from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO

from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class Dialog_App_Loading(QDialog):
    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)
        self.gif_path = gif_path
        self.label_text_list = [
            "Application 불러오는 중 입니다....",
            "Server에서 Data 수신중입니다...",
        ]
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)
        self.setFixedSize(300, 300)

        self.UI()

        self.subscribe_tasks  = [
            (INFO.get_WS_URL_by_name('app_권한'), self.app_ws_handler),
            (INFO.get_WS_URL_by_name('active_users'), self.active_users_ws_handler),
            (f"{GBus.TABLE_TOTAL_REFRESH}", self.table_total_config_ws_handler),
            # (INFO.get_WS_URL_by_name('table_total_config'), self.table_total_config_ws_handler),
            (INFO.get_WS_URL_by_name('resource'), self.resources_ws_handler),
        ]
        self.subscribe_result = {
            INFO.get_WS_URL_by_name('app_권한'): False,
            INFO.get_WS_URL_by_name('active_users'): False,
            f"{GBus.TABLE_TOTAL_REFRESH}": False,
            INFO.get_WS_URL_by_name('resource'): False,
        }

        self.subscribe_gbus()

    def UI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.gif_path:
            self.label_animation = QLabel()
            self.movie = QMovie(self.gif_path)
            self.label_animation.setMovie(self.movie)
            self.movie.start()

        self.label_text = QLabel(self.label_text_list[0])
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label_animation)
        layout.addWidget(self.label_text)

        self.setLayout(layout)
    # def closeEvent(self, event):
    #     event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()

    def subscribe_gbus(self):
        for channelName, handler in self.subscribe_tasks:
            event_bus.subscribe(f"{channelName}", handler)

    def update_label_text(self, text:str):
        _text = self.label_text.text()
        self.label_text.setText(f"{_text} <br> {text}")

    def app_ws_handler(self, _action:str):
        """ AppAuthorityHandler._handle_init()에서 publish 를 subscribe 함."""
        if _action != 'init':
            return
        self.subscribe_result[INFO.get_WS_URL_by_name('app_권한')] = True
        self.update_label_text("app_권한 수신 완료")
        self.check_all_done()

    def active_users_ws_handler(self, _action:str):
        """ UsersHandler._handle_init()에서 publish 를 subscribe 함."""
        if _action != 'init':
            return
        self.subscribe_result[INFO.get_WS_URL_by_name('active_users')] = True
        self.update_label_text("active_users 수신 완료")
        self.check_all_done()

    def table_total_config_ws_handler(self, is_refresh:bool):
        if not is_refresh:
            return
        self.subscribe_result[f"{GBus.TABLE_TOTAL_REFRESH}"] = True
        self.update_label_text("table_total_config 수신 완료")
        self.check_all_done()

    def resources_ws_handler(self, _action:str):
        if _action != 'init':
            return
        self.subscribe_result[INFO.get_WS_URL_by_name('resource')] = True
        self.update_label_text("resources 수신 완료")
        self.check_all_done()


    def check_all_done(self):
        all_done = all(self.subscribe_result.values())
        if all_done:
            self.update_label_text("모든 수신 완료")
            if INFO.IS_DEV :
                self.update_label_text(f"<br><br> <b>App 설정 관리자 : {INFO._get_is_app_admin()}</b>")
                QTimer.singleShot(3000, self.accept)
            else:
                self.accept()




if __name__ == "__main__":
    app = QApplication([])
    dialog = Dialog_App_Loading("/home/kkt/development/python/PyQt6/sh_app/modules/PyQt/dialog/loading/app_loading.gif")
    # 이벤트 루프 시작 직후 다이얼로그 표시
    QTimer.singleShot(0, dialog.show)
    app.exec()