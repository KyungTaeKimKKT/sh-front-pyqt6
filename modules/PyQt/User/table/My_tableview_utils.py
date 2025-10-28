from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import typing

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
####
from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class My_Table_View_Utils:

    def __init__(self):
        self.setMouseTracking(True)

    def mouseMoveEvnet(self, event:QEvent):
        super().mouseMoveEvent(event)