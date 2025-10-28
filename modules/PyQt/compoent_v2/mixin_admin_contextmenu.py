from __future__ import annotations
from typing import TYPE_CHECKING, Callable
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from dataclasses import dataclass

import copy, json

from info import Info_SW as INFO
from modules.logging_config import get_plugin_logger
import modules.user.utils as utils
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.json_editor import Dialog_JsonEditor

@dataclass
class AdminAction:
    title: str
    slot_func: Callable

    def __post_init__(self):
        if self.title == "seperator":
            return
        if not callable(self.slot_func):
            raise TypeError(
                f"slot_func for '{self.title}' must be callable, got {type(self.slot_func)}"
                )


class Base_AdminContextMenu:
    def init_admin_context_menu(self, target_widget):
        """관리자용 context menu를 target_widget에 붙임"""
        self._admin_context_target = target_widget
        self._admin_context_target.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._admin_context_target.customContextMenuRequested.connect(self._show_admin_context_menu)


class Mixin_AdminContextMenu_TableMenu(Base_AdminContextMenu):

    @property
    def admin_actions(self) -> list[AdminAction]:
        """관리자용 context menu의 액션들을 정의"""
        return [
            AdminAction("🔄 Reload Table Config", self._on_reload_config),
            AdminAction("🐞 Print Debug Info", self._on_print_debug),
            AdminAction("⚡ Force Refresh", self._on_force_refresh),
            AdminAction("seperator", None ),
            AdminAction("🔄 선택된 row Dict 보기", self._show_selected_row_dict),
            AdminAction("🔄 App메뉴", self._on_app_menu),
            AdminAction("🔄 Lazy속성", self._on_lazy_property),
            AdminAction("🔄 Table메뉴", self._on_table_menu),
        ]

    def _show_admin_context_menu(self, pos):
        """dataclass 기반 액션 목록을 QMenu로 표시"""
        menu = QMenu(self._admin_context_target)
        # 스타일 지정 (예: 배경, 글자색, 패딩 등)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f0f0f0;
                color: #202020;
                border: 1px solid #888;
            }
            QMenu::item:selected {
                background-color: #a0c4ff;
            }
        """)

        for action in self.admin_actions:
            if action.title == "seperator":
                menu.addSeparator()
                continue
            q_action = QAction(action.title, self)
            q_action.triggered.connect(action.slot_func)
            menu.addAction(q_action)

        menu.exec(self._admin_context_target.mapToGlobal(pos))

    def _on_app_menu(self):
        self._on_appDict_info('App_Menus')

    def _on_lazy_property(self):
        self._on_appDict_info('lazy_attrs')

    def _on_table_menu(self):
        self._on_appDict_info('Table_Menus')

    def _on_appDict_info(self, _menu_type:str):
        form = Dialog_JsonEditor(None, self.url, _dict_data=self.appDict[_menu_type])
        if form.exec():
            resultObj = form.get_value()
            self.appDict[_menu_type] = resultObj

    # @property
    # def admin_map_name_to_action_info(self) -> dict[str, QAction]:
    #     """관리자용 context menu의 액션들을 정의하는 메서드"""
    #     return {
    #         "reload":  {
    #             "title" : "🔄 Reload Table Config",
    #             "slot_func" : self._on_reload_config,
    #         },
    #         "debug": {
    #             "title" : "🐞 Print Debug Info",
    #             "slot_func" : self._on_print_debug,
    #         },
    #         "force_refresh": {
    #             "title" : "⚡ Force Refresh",
    #             "slot_func" : self._on_force_refresh,
    #         }
    #     }

    # def _show_admin_context_menu(self, pos):
    #     menu = QMenu(self._admin_context_target)

    #     for action_name, action_info in self.admin_map_name_to_action_info.items():
    #         action = QAction(action_info["title"], self)
    #         action.triggered.connect(action_info["slot_func"])
    #         menu.addAction(action)

    #     menu.exec(self._admin_context_target.mapToGlobal(pos))

    # === 액션 처리 메서드들 ===
    def _on_reload_config(self):
        print("Reload Config 실행")

    def _on_print_debug(self):
        print("Debug Info:", getattr(self, "Table_Menus", None))

    def _on_force_refresh(self):
        if hasattr(self, "refresh_table"):
            self.refresh_table(force=True)
        else:
            print("refresh_table() 없음")

    def _show_selected_row_dict(self):
        print("선택된 row Dict 보기")
        print(self.selected_dataObj)