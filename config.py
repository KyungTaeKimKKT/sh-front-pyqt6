from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.user.api import Api_SH
    from main_test import WSManager
    from plugin_main.dialog.loading_dialog import LoadingDialog

import json
import traceback



### 싱글톤 클래스로 변경
class Config_Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.API = None
            cls._instance.CAM = None
        return cls._instance

    ### setter
    def set_API(self, api:Api_SH):
        self.API = api

    def set_CONFIG_개인(self, config_개인:dict):
        self.CONFIG_개인 = config_개인

    def set_CAM(self, cam:dict):
        self.CAM = cam

    def set_WS_manager(self, ws_manager:WSManager):
        print (f"set_WS_manager : {ws_manager}")
        self.WS_manager = ws_manager

    def set_DLG_LOADING(self, dlg_loading:LoadingDialog) -> None:
        self.DLG_LOADING = dlg_loading

    ### getter
    def get_API(self):
        return self.API

    def get_CONFIG_개인(self):
        return self.CONFIG_개인

    def get_CAM(self):
        return self.CAM

    def get_WS_manager(self):
        return self.WS_manager

    def get_DLG_LOADING(self) -> LoadingDialog:
        return getattr(self, 'DLG_LOADING', None)



Config = Config_Singleton()
