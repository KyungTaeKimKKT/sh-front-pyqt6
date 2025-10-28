from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtGui import QHideEvent
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from info import Info_SW as INFO
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Empty_For_QStackedWidget(QLabel):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setText("조회된 데이터가 없읍니다.")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: gray;")
        self.setFont(QFont("Arial", 24))
        self.show()

    def hideEvent(self, a0: QHideEvent) -> None:
        self.hide()
        return super().hideEvent(a0)
    
    def showEvent(self, a0: QShowEvent) -> None:
        self.show()
        return super().showEvent(a0)


class Custom_QStackedWidget(QStackedWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.mapping_widgets = {}
        self.empty_widget = Empty_For_QStackedWidget(self)
        self.table_name = None

        self.addWidget('empty', self.empty_widget)
        self.setCurrentWidget('empty')

        self.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: 5px solid black;
            }
        """)


        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 400)

    def addWidget(self, name: str, widget: QWidget) -> None:
        """name은 반드시 지정해야 한다."""
        self.mapping_widgets[name] = widget
        super().addWidget(widget)
        # self.setCurrentWidget(name)

    def removeWidget(self, name: str) -> None:
        widget = self.mapping_widgets.pop(name, None)
        if widget:
            super().removeWidget(widget)

    def setCurrentWidget(self, name: str) -> None:
        if INFO.IS_DEV:
            logger.debug(f"{self.__class__.__name__} : setCurrentWidget: {name}")
            logger.debug(f"{self.__class__.__name__} : setCurrentWidget: {self.mapping_widgets}")
            logger.debug(f"{self.__class__.__name__} : setCurrentWidget: {self.table_name}")
        widget = self.mapping_widgets.get(name)
        if widget:
            # for w in self.mapping_widgets.values():
            #     w.hide()
            # widget.show()
            super().setCurrentWidget(widget)
            self.current_widget = widget
            self.current_widget_name = name
        else:
            self.setCurrentWidget('empty')

    def add_Widgets(self, mapping_widgets: dict[str, QWidget]) -> None:
        for name, widget in mapping_widgets.items():
            self.addWidget(name, widget)

    def remove_Widgets(self, names: list[str]) -> None:
        for name in names:
            self.removeWidget(name)

    def clear_Widgets(self) -> None:
        for widget in self.mapping_widgets.values():
            super().removeWidget(widget)
        self.mapping_widgets.clear()

    def get_current_widget_name(self) -> str:
        return self.current_widget_name

# class Custom_QStackedWidget(QStackedWidget):
#     def __init__(self, parent: QWidget = None):
#         super().__init__(parent)
#         self.current_index = 0
#         self.empty_widget = Empty_For_QStackedWidget(self)

#         self.mapping_widgets = {
#             "empty": self.empty_widget,
#         }


#     def init_ui(self):
#         self.addWidget('empty', self.empty_widget)
#         self.setCurrentWidget('empty')

#         self.setStyleSheet("""QStackedWidget { 
#                            background-color: white;
#                            border: 5px solid black;
#                            }""")

#     def setCurrentIndex(self, index: int) -> None:
#         self.current_index = index
#         super().setCurrentIndex(index)


#     def setCurrentWidget(self, name: str) -> None:
#         self.current_widget = self.mapping_widgets.get(name, None)
#         super().setCurrentWidget(self.current_widget)


#     def addWidget(self, name: str, widget: QWidget) -> None:
#         """ 
#         override: name 은 반드시 넣어야 함. 
#         self.mapping_widgets[name] = widget 으로 추가됨
#         """
#         self.mapping_widgets[name] = widget
#         super().addWidget(widget)


#     def removeWidget(self, name: str) -> None:
#         """ 
#         override: name 은 반드시 넣어야 함. 
#         self.mapping_widgets.pop(name, None) 으로 삭제됨
#         """
#         self.mapping_widgets.pop(name, None)
#         super().removeWidget(self.mapping_widgets[name])

#     def add_Widgets ( self, mapping_widgets: dict[str, QWidget]) -> None:
#         """ 
#         mapping_widgets을 넘기는 경우, addWidget 호출로 인하여,  
#         self.mapping_widgets[name] = widget 으로 추가됨
#         """
#         for name, widget in mapping_widgets.items():
#             self.addWidget(name, widget)

#     def remove_Widgets(self, names: list[str]) -> None:
#         for name in names:
#             self.removeWidget(name)

#     def clear_Widgets(self) -> None:
#         self.mapping_widgets.clear()
#         self.clear()