from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import concurrent.futures

import pathlib
import typing
import copy
import json


from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model, TableModelBuilder
# from modules.PyQt.compoent_v2.table.Base_Table_Delegate import Base_Table_Delegate
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.compoent_v2.fileview.wid_fileview import Wid_FileViewer

# from modules.PyQt.Tabs.생산지시서.dialog.list_edit.dlg_판금처선택 import 판금처선택다이얼로그

from modules.PyQt.dialog.file.dialog_file_upload_with_listwidget import Dialog_file_upload_with_listwidget

# from modules.PyQt.Tabs.품질경영.dialog.dlg_cs_등록 import Dlg_CS_등록
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
# import sub window
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()
ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dlg_Table_Config_설정(QDialog):
	
    def __init__(self, parent=None, api_datas:list[dict]=[], table_name:str='', **kwargs ):
        super().__init__(parent)
        self.parent = parent
        self.kwargs = kwargs

        self.api_datas:list[dict] = api_datas
        self.table_name:str = table_name
        url = f"config/table_config/?table_name={table_name}"
        _isOk, _json = APP.API.getlist( url)
        if _isOk:
            self.config_datas =_json

        self.UI()

    def UI(self):
        self.setWindowTitle('테이블 설정')
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint)  
        v_layout = QVBoxLayout()
        from modules.PyQt.Tabs.Config.tables.table_Config_Table_old import Wid_Table_for_Config_Table
        table = (Wid_Table_for_Config_Table()
                 ._set_api_datas( self.api_datas )
                 ._set_table_config_datas( self.config_datas )
                 .process_table_config_from_api()
        )
        v_layout.addWidget(table)
        self.setLayout(v_layout)
        self.exec_()

    
