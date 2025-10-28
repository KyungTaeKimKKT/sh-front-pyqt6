#### 25-7-11 추가

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.Tabs.plugins.ui.v2.Wid_info import Wid_Info
from modules.PyQt.Tabs.plugins.ui.v2.Wid_page_common import Wid_Page_Common
from modules.PyQt.Tabs.plugins.ui.v2.Wid_search_common import Wid_Search_Common

from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton

from info import Info_SW as INFO
import modules.user.utils as Utils
from modules.envs.resources import resources

import logging, traceback
logger = logging.getLogger(__name__)

class Ui_Base_Tab_V2:
    """ 
    BaseTab_V2에서 사용하는 공통 UI : mixin 클래스
    """
    @property
    def default_container_margins(self) -> tuple[int, int, int, int]:
        return (5, 1, 5, 1)

    @property
    def default_container_stylesheet(self) -> str:
        return """
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
        """
    
   
    def _create_wid_info(self) -> Wid_Info:
        """ 필요시 오버라이드"""
        try:
            if hasattr(self, 'lazy_attrs') and self.lazy_attrs.get('is_no_info_create', False):
                return None
            self.wid_info = Wid_Info(self)
            return self.wid_info
        except Exception as e:
            logger.error(f"create_wid_info 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='create_wid_info 오류', text=f"{e}<br>{trace}")
            return None
    
    def _create_wid_app_menu(self) -> QWidget:
        """ 필요시 오버라이드 : 정리해야 함."""
        self.map_pbName_to_pbWidget = {}

        self.wid_app_menu = QWidget()
        layout = QHBoxLayout(self.wid_app_menu)
        if not Utils.is_valid_attr_name(self, 'App_Menus', dict):
            if INFO.IS_DEV:
                pass
                # Utils.QMsg_Critical(None, title="app menu 없음", text=f"{self.__class__.__name__} : _create_wid_app_menu : App_Menus 없음")                
            return None
        #### 
        lb = QLabel('App_Menus')
        layout.addWidget(lb)
        layout.addStretch()
        for name, menu_dict in self.App_Menus.items():
            layout.addWidget(self._create_pb_menu(menu_dict))
        return self.wid_app_menu
    
    def _create_pb_menu(self, config:dict) -> CustomPushButton:
        pb = QPushButton(self)
        pb.setText(config['name'])
        pb.setObjectName(config['name'])
        if (icon := resources.get_icon(config['icon'])):
            pb.setIcon(icon)
            pb.setIconSize(QSize(16, 16))
            pb.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            pb.setStyleSheet("text-align: center; padding-left: 0px;")
        pb.setToolTip(config['tooltip'])
        if Utils.is_valid_method(self, config['slot_func']):
            pb.clicked.connect(getattr(self, config['slot_func']))
            self.map_pbName_to_pbWidget[config['name']] = pb
        else:
            if INFO.IS_DEV:               
                Utils.QMsg_Critical(None, title="slot_func 없음", text=f"{self.__class__.__name__} : _create_pb_menu : {config['slot_func']} 메서드가 없음")
        return pb

    def _create_wid_search(self) -> Wid_Search_Common:
        """ 필요시 오버라이드"""
        try:
            if hasattr(self, 'lazy_attrs') and self.lazy_attrs.get('is_no_search_create', False):
                return None
            self.wid_search = Wid_Search_Common(self)
            return self.wid_search
        except Exception as e:
            logger.error(f"create_wid_search 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='create_wid_search 오류', text=f"{e}<br>{trace}")
            return None

    def _create_wid_pagination(self) -> Wid_Page_Common:
        """ 필요시 오버라이드"""
        try:
            if hasattr(self, 'lazy_attrs') and any([self.lazy_attrs.get(key, False) for key in ['is_no_pagination_create', 'is_no_search_create']]):
                return None
            self.wid_pagination = Wid_Page_Common(self)
            return self.wid_pagination
        except Exception as e:
            logger.error(f"create_wid_pagination 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='create_wid_pagination 오류', text=f"{e}<br>{trace}")
            return None
    
    def _create_wid_main(self) -> QStackedWidget:
        """ 필요시 오버라이드"""
        self.wid_main = QStackedWidget(self)
        return self.wid_main


    
    # ----------------------------
    # container 생성 메서드들
    # ----------------------------

    def _get_stylesheet(self, object_name: str) -> str:
        return f"""
            #{object_name} {{
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
            }}
        """

    @property
    def container_config(self) -> dict[str, dict]:
        return{
            'info': {
                "object_name": "container_info",
                "layout_contents_margins": self.default_container_margins,
                "layout_spacing": 4,
                "widget": self._create_wid_info(),
                "layout_type": 'horizontal',
            },
            'app_menu': {
                "object_name": "container_app_menu",
                "layout_contents_margins": self.default_container_margins,
                "layout_spacing": 4,
                "widget": self._create_wid_app_menu(),
                "layout_type": 'horizontal',
            },
            'search': {
                "object_name": "container_search",
                "layout_contents_margins": self.default_container_margins,
                "layout_spacing": 4,
                "widget": self._create_wid_search(),
                "layout_type": 'horizontal',
            },
            'pagination': {
                "object_name": "container_pagination",
                "layout_contents_margins": self.default_container_margins,
                "layout_spacing": 4,
                "widget": self._create_wid_pagination(),
                "layout_type": 'horizontal',
            },
        }

    def _create_container(
            self,
            object_name: str,
            layout_contents_margins: tuple[int, int, int, int] = (5, 3, 5, 3),
            layout_spacing: int = 4,
            widget: QWidget = None,
            layout_type: str = 'horizontal',  # ✔️ 명확하게
    ) -> QWidget:
        container = QWidget()
        container.setObjectName(object_name)
        if layout_type == 'horizontal':
            layout = QHBoxLayout(container)
        else:
            layout = QVBoxLayout(container)
        layout.setContentsMargins(*layout_contents_margins)
        layout.setSpacing(layout_spacing)
        if widget:
            layout.addWidget(widget)

        container.setStyleSheet(self._get_stylesheet(object_name))
        return container
    
    def _create_container_main(self) -> QWidget:
        raise NotImplementedError("상속받은 클래스에서 구현해야 합니다.")
        # container = QWidget()
        # layout = QVBoxLayout(container)
        # layout.addWidget(self._create_wid_main())
        # return container


    # ----------------------------
    # setup_ui
    # ----------------------------
    def setup_ui(self):
        self.resize(1670, 853)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)   # 좌우상하 여백
        self.main_layout.setSpacing(4)                   # 위젯 간 간격

        for container in self.container_config.values():
            self.main_layout.addWidget(self._create_container(**container))

        self.container_main = self._create_container_main()
        self.main_layout.addWidget(self.container_main)
        

    #### 25-7-22 추가
    def _create_select_main_widget(self) -> QWidget:
        try:
            self.wid_select_main = QWidget()
            h_layout = QHBoxLayout(self.wid_select_main)
            self.mapping_name_to_widget = self.lazy_attrs.get('mapping_name_to_widget', {})
            self.select_main_list = self.mapping_name_to_widget.keys()
            lb_select_main = QLabel('선택 : ')
            self.cb_select_main = QComboBox()
            self.cb_select_main.addItems(self.select_main_list)
            self.cb_select_main.setCurrentText(self.lazy_attrs.get('Default_view', 'empty'))
            self.cb_select_main.currentTextChanged.connect(self.on_select_main)
            h_layout.addWidget(lb_select_main)
            h_layout.addWidget(self.cb_select_main)
            _text = self.mapping_name_to_widget.get("info", {}).get(self.cb_select_main.currentText(), '')
            self.lb_additional_info = QLabel(_text)
            h_layout.addWidget(self.lb_additional_info)
            h_layout.addStretch()
            return self.wid_select_main
        except Exception as e:
            logger.error(f"create_select_main_widget 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='create_select_main_widget 오류', text=f"{e}<br>{trace}")
            return None
        
    def on_select_main(self, text:str):
        print (f"on_select_main: {text}")
        return 
        self.lazy_attrs['Default_view'] = text
        self.lb_additional_info.setText(self.mapping_name_to_widget.get("info", {}).get(text, ''))

    # def _create_container_info(self) -> QWidget:
    #     object_name = "container_info"
    #     container = QWidget()
    #     container.setObjectName(object_name)
    #     layout = QVBoxLayout(container)
    #     layout.setContentsMargins(5, 3, 5, 3)
    #     layout.addWidget(self._create_wid_info())
    #     container.setStyleSheet(self._get_stylesheet(object_name))
    #     return container

    # def _create_container_app_menu(self) -> QWidget:
    #     object_name = "container_app_menu"
    #     container = QWidget()
    #     container.setObjectName(object_name)
    #     layout = QVBoxLayout(container)
    #     layout.addWidget(self._create_wid_app_menu())
    #     container.setStyleSheet(self._get_stylesheet(object_name))
    #     return container

    # def _create_container_search(self) -> QWidget:
    #     object_name = "container_search"
    #     container = QWidget()
    #     container.setObjectName(object_name)
    #     layout = QVBoxLayout(container)
    #     layout.addWidget(self._create_wid_search())
    #     container.setStyleSheet(self._get_stylesheet(object_name))
    #     return container

    # def _create_container_pagination(self) -> QWidget:
    #     object_name = "container_pagination"
    #     container = QWidget()
    #     container.setObjectName(object_name)
    #     layout = QVBoxLayout(container)
    #     layout.addWidget(self._create_wid_pagination())
    #     container.setStyleSheet(self._get_stylesheet(object_name))
    #     return container



