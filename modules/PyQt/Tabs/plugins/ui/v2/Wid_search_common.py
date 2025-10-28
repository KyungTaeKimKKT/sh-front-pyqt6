from __future__ import annotations
from typing import Optional, Any

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

from modules.PyQt.Tabs.plugins.ui.Ui_search_common import Ui_Search
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import time, traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.custom_상속.custom_PB import Custom_PB_Query
from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_PageSize
from modules.PyQt.compoent_v2.custom_상속.custom_lineEdit import Custom_Search_LineEdit

from local_db.models import Search_History

class Wid_Search_Common(QWidget, LazyParentAttrMixin):
    def __init__(self, parent=None, pageSize_choices:list[str]=['25', '50', '100'], le_config:dict=None):
        super().__init__(parent)
        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.pageSize_choices = pageSize_choices+['ALL'] if INFO._get_is_app_admin() else pageSize_choices
        self.pageSize = self.pageSize_choices[0]

        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.search_history:list[str] = []
        self.is_ui_initialized = False

        self.default_le_config = le_config = {
                'placeholder': '공란이면 전체 조회입니다.',
                'maxLength': 100,
                # 'text': '', default text로 disalbe
                'readOnly': False,
                'clearButtonEnabled': True,
                'tooltip': '검색 또는 Enter를 누르세요.',
            }
        self.le_config = le_config or self.default_le_config

        self.run_lazy_attr()

    def set_le_search_config(self, config: dict):
        if not hasattr(self, 'le_search'):
            return  # le_search가 아직 없을 경우 방어
        if not config:
            self.le_config = self.default_le_config

        self.le_search.setPlaceholderText(config.get('placeholder', '공란이면 전체 조회입니다.'))

        if 'text' in config:
            self.le_search.setText(config['text'])

        if 'maxLength' in config:
            self.le_search.setMaxLength(config['maxLength'])

        if 'font' in config and isinstance(config['font'], QFont):
            self.le_search.setFont(config['font'])

        if 'readOnly' in config:
            self.le_search.setReadOnly(config['readOnly'])

        if 'clearButtonEnabled' in config:
            self.le_search.setClearButtonEnabled(config['clearButtonEnabled'])

        if 'tooltip' in config:
            self.le_search.setToolTip(config['tooltip'])



    def setup_ui(self):
        self.setObjectName("Search")
        self.resize(1378, 68)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(-1, 0, -1, 0)

        ### 1.  검색
        self.lb_검색  = QLabel(parent=self)
        self.lb_검색.setText("검색")
        self.main_layout.addWidget(self.lb_검색)
        self.le_search = Custom_Search_LineEdit(parent=self)
        self.le_search.setObjectName("le_search")
        self.main_layout.addWidget(self.le_search)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)

        ### 2. 조회조건 : 현재는 disable
        self.PB_Option = Custom_PB_Query(parent=self)
        self.PB_Option.setText("조회조건")
        self.PB_Option.setEnabled(False)
        self.main_layout.addWidget(self.PB_Option)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)

        ### 3. page combobox 
        self.lb_pageSize = QLabel(parent=self)
        self.lb_pageSize.setText("PageSize")
        self.main_layout.addWidget(self.lb_pageSize)

        self.comboBox_pageSize = Custom_Combo_PageSize(parent=self, items=self.pageSize_choices)
        self.comboBox_pageSize.setCurrentIndex(0)
        self.main_layout.addWidget(self.comboBox_pageSize)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)

        ### 4. 조회
        self.PB_Search = Custom_PB_Query(parent=self)
        self.PB_Search.setText("조회")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PB_Search.sizePolicy().hasHeightForWidth())
        self.PB_Search.setSizePolicy(sizePolicy)
        self.main_layout.addWidget(self.PB_Search)

        self.setLayout(self.main_layout)

        self.is_ui_initialized = True

    def closeEvent(self, event):
        self.disconnect_signals()
        super().closeEvent(event)

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)
    
    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]

            if not self.is_ui_initialized:
                self.setup_ui()
                self.set_le_search_config(self.le_config)

            self.set_focus_to_search()
            self.set_completer( APP_ID )
            self.channel_name = f"AppID:{APP_ID}_"
            self.connect_signals()
        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")
    


    def connect_signals(self):
        self.PB_Search.clicked.connect( self.on_search ) #lambda: self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, self.get_search_keyword()) )
        self.le_search.returnPressed.connect( self.on_search ) #lambda: self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, self.get_search_keyword()) )
    
    def on_search(self):
        search_keyword = self.get_search_keyword()
        self.event_bus.publish(self.channel_name+GBus.SEARCH_REQUESTED, search_keyword)

    def disconnect_signals(self):
        try:
            self.PB_Search.clicked.disconnect()
            self.le_search.returnPressed.disconnect()
        except Exception as e:
            pass

    def hide_search_edit(self):
        self.lb_검색.hide()
        self.le_search.hide()
    
    def hide_pagesize_combo(self):
        # self.comboBox_pageSize.setCurrentText('ALL')
        self.comboBox_pageSize.hide()
        self.lb_pageSize.hide()

    def hide_pb_option(self):
        self.PB_Option.hide()

    def hide_except_pb_search(self):
        self.hide_search_edit()
        self.hide_pagesize_combo()
        self.hide_pb_option()


    def set_completer(self, id:int):
        self.le_search.set_completer(id)
    
    def db_save_search_history(self):
        self.le_search.db_save_search_history()

    def set_focus_to_search(self):
        # 이 메서드를 통해 검색창에 포커스 설정 가능
        self.le_search.setFocus()

    def showEvent(self, event):
        # 위젯이 표시될 때마다 포커스 설정
        super().showEvent(event)
        if hasattr(self, 'le_search'):
            self.le_search.setFocus()

    def get_search_keyword(self) -> dict:
        params = {}
        if ( search_keyword := self.le_search.text() ):
            self.db_save_search_history()
            params['search'] = search_keyword

        page = self.comboBox_pageSize.currentText()
        params['page_size'] = 0 if page.lower() == 'all' else page

        if INFO.IS_DEV:
            print(f"get_search_keyword: {params}")

        return params
    


class Wid_Search_Only_Refresh(Wid_Search_Common):

    def setup_ui(self):
        super().setup_ui()
        self.hide_except_pb_search()
        self.PB_Search.setText("새로고침")

    def get_search_keyword(self) -> dict:
        return {'page_size': 0}