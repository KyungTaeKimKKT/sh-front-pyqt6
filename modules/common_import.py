from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.table.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table.Base_Delegate import Base_Delegate

import json, os, io, copy, time
import platform
from collections import defaultdict, Counter
from datetime import datetime, date, timedelta
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

#### tab을 위한 import
from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table


#### custom dialogs
from plugin_main.widgets.dlg_user_select_with_tree_table import UsersDialog_with_tree_table
from plugin_main.widgets.dlg_users_select_only_table import Dlg_Users_Select_Only_Table, Dlg_User_선택_Only_Table_No_Api
from plugin_main.widgets.fileopen_single import FileOpenSingle
from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


#### custom widgets
from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton
from modules.PyQt.compoent_v2.custom_상속.custom_lineEdit import Custom_LineEdit
from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_with_fetch, Custom_Combo
from modules.PyQt.compoent_v2.custom_상속.custom_listwidget import Custom_ListWidget