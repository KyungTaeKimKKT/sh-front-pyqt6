from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# from modules.PyQt.compoent_v2.table_v2.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
from modules.PyQt.compoent_v2.table_v2.Wid_table_Base_for_stacked_V2 import Wid_table_Base_V2
from modules.PyQt.compoent_v2.table_v2.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model, DataFrameTableModel
from modules.PyQt.compoent_v2.table_v2.Base_Delegate import Base_Delegate

import pandas as pd
import json, os, io, copy, time, re
import platform
import math
from enum import Enum
from collections import defaultdict, Counter
from datetime import datetime, date, timedelta
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
from modules.envs.globaldata import GlobalData

import modules.user.utils as Utils
from modules.envs.resources import resources
#### tab을 위한 import
# from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
# from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table_v2.stacked_table import Base_Stacked_Table

from modules.PyQt.compoent_v2.widget_manager import WidgetManager

#### custom dialogs
from plugin_main.widgets.dlg_user_select_with_tree_table import UsersDialog_with_tree_table
from plugin_main.widgets.dlg_users_select_only_table import Dlg_Users_Select_Only_Table, Dlg_User_선택_Only_Table_No_Api
from plugin_main.widgets.fileopen_single import FileOpenSingle
from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


#### custom widgets
from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton
from modules.PyQt.compoent_v2.custom_상속.custom_lineEdit import Custom_LineEdit
from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_with_fetch, Custom_Combo
from modules.PyQt.compoent_v2.custom_상속.custom_listwidget import Custom_ListWidget

from modules.PyQt.compoent_v2.custom_상속.custom_lineEdit import Custom_Search_LineEdit

from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit



class EmptyChart(QWidget):
    def __init__(self, parent:QWidget=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        pass