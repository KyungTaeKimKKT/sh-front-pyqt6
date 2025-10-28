from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Combo_작지_dashboard_날짜(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_작지_dashboard_날짜_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)

class Combo_작지_dashboard_고객사(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_작지_dashboard_고객사_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)

class Combo_작지_dashboard_구분(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_작지_dashboard_구분_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)


class Combo_작지_dashboard_GraphType(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_작지_dashboard_GraphType_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)

class Combo_생지_form_생산형태(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_생지_form_생산형태_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)


class Combo_table_row(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = INFO.Combo_table_row_Items
        self.addItems(self.items)
        self.setCurrentIndex(0)