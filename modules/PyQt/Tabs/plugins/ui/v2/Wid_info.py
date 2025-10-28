from __future__ import annotations
from typing import Optional, Any
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

import copy
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import time, traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Wid_Info(QWidget, LazyParentAttrMixin):
    def __init__(self, parent=None, appID:Optional[int]=None):
        super().__init__(parent)
        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.start_init_time = time.perf_counter()
        self.appDict:dict = {}

        self.setup_ui()

        self.run_lazy_attr()

    def setup_ui(self):
        self.resize(1670, 27)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(-1, 1, -1, 1)

        self.pb_info = QPushButton(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_info.sizePolicy().hasHeightForWidth())
        self.pb_info.setText('도움말')
        self.pb_info.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        font.setItalic(True)
        self.pb_info.setFont(font)
        self.pb_info.setObjectName("pb_info")
        self.main_layout.addWidget(self.pb_info)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)
        self.label_title = QLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_title.sizePolicy().hasHeightForWidth())
        self.label_title.setSizePolicy(sizePolicy)
        self.label_title.setStyleSheet("background-color:black;color:yellow;font-weight:bold;")
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_title.setObjectName("label_title")
        self.main_layout.addWidget(self.label_title)
        self.label_sub = QLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_sub.sizePolicy().hasHeightForWidth())
        self.label_sub.setSizePolicy(sizePolicy)
        self.label_sub.setText("")
        self.label_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_sub.setObjectName("label_sub")
        self.main_layout.addWidget(self.label_sub)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem1)

        self.setLayout(self.main_layout)

    def update_ui(self):
        self.update_titles(
            title = f"{self.appDict['표시명_구분']} : {self.appDict['표시명_항목']}",
            sub=self.appDict['info_title']
            )
        self.update_help_page(self.appDict['help_page'])

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.table_name = Utils.get_table_name(APP_ID)
            ### 2025-06-11 12:33:01,257 - Wid_info - INFO - self.appDict: 
            # {'id': 153, 'div': 'App설정', 'name': 'App설정_개발자', 'url': '', 'api_url': 'app권한-개발자/', 
            # 'api_uri': '/api/users/', '표시명_구분': 'App설정', '표시명_항목': 'App설정_개발자', 'is_Active': False, 'is_Run': False, '순서': 0, 'is_dev': True, 'user_pks': [1]}
            self.appDict = copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)
            self.subscribe_gbus()

            self.update_ui()

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")


    def subscribe_gbus(self):
        """ 추후에 appDict가 바뀌면 update할 수 있도록 """
        pass

    def unsubscribe_gbus(self):
        pass

    def update_titles(self, title:str='', sub:str=''):
        """ title : 타이틀, sub : 부제목 """
        self.label_title.setText(title)
        self.label_sub.setText(sub)

    def update_help_page(self, url_file_path:str):
        """URL 정보 설정 (기본적인 검증만 수행)"""
        # 기본적인 URL 형식 확인 (INFO.URI 포함 여부)

        
        has_url = bool(url_file_path) and '/helppage/' in url_file_path
        
        # 버튼 활성화/비활성화 설정
        self.pb_info.setEnabled(has_url)
        
        # 스타일 적용
        self._apply_help_button_style(has_url)
        
        # URL 저장
        self.help_url = f"{INFO.URI}media{url_file_path}" if has_url else None
        
        # 클릭 이벤트 연결 - try/except로 예외 처리
        if has_url:
            try:
                if self.pb_info.receivers(self.pb_info.clicked) > 0:
                    self.pb_info.clicked.disconnect()
            except TypeError:
                pass  # 연결된 시그널이 없는 경우 예외 처리
            self.pb_info.clicked.connect(self.on_help_button_clicked)

    def on_help_button_clicked(self):
        """버튼 클릭 시 실제 URL 유효성 검사 후 파일 뷰어 실행"""
        if not self.help_url:
            return
        
        # 클릭 시점에 URL 유효성 검사 (필요시)
        Utils.file_view( [self.help_url])


    def _apply_help_button_style(self, is_active:bool):
        """도움말 버튼 스타일 적용"""
        if is_active:
            # 활성화 스타일
            self.pb_info.setIcon(QIcon(":/icons/help.png"))
            self.pb_info.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
        else:
            # 비활성화 스타일
            self.pb_info.setIcon(QIcon(":/icons/help_disabled.png"))
            self.pb_info.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
