from PyQt6 import QtCore, QtGui, QtWidgets
import modules.user.utils as utils

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Ui_Tabs:
    signal = QtCore.pyqtSignal(object)

    def __init__(self, MainWindow:QtWidgets.QMainWindow , selected_표시명_구분:list[dict], appDict:dict):
        self.MainWindow = MainWindow
        self.selected_표시명_구분 = selected_표시명_구분
        self.appDict = appDict
        # self.triggerConnect()


    def render(self):
        if not self.selected_표시명_구분:
            return None
        
        표시명_구분 = self.selected_표시명_구분[0].get('표시명_구분','')
        tabs = QtWidgets.QTabWidget()
        tabs.setObjectName(표시명_구분)
        curIndex = self.selected_표시명_구분.index(self.appDict)
        for idx, app in enumerate(self.selected_표시명_구분):
            tabObj = self._create_tab_widget(app)
            ### tab Widget에 tab 추가
            tabs.addTab(tabObj, app.get('표시명_항목') )
            # tabs.tabBarClicked.connect(self.slot_tabBarClicked)
            if INFO.USERID != 1 :
                tabs.setTabEnabled(idx, app.get('is_Run', False) )

        return (tabs, curIndex)
    
    ################ slot ############

    def slot_tabBarClicked(self, index):
        logger.info(f"탭 클릭: {index}")


    def _create_tab_widget(self, appDict:dict):
        divName , appName = appDict.get('div'), appDict.get('name')    
        tabObj = QtWidgets.QWidget()
        tabObj.setObjectName(f'appid_{appDict.get("id")}')
        # 앱 참조를 저장할 속성 추가
        tabObj.app = None
        return tabObj
