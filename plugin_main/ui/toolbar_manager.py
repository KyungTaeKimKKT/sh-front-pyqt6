from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from copy import deepcopy
from modules.global_event_bus import event_bus

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.envs.global_bus_event_name import Global_Bus_Event_Name as GBus
# from modules.PyQt.ui.Ui_toolbar import Ui_Toolbar
from modules.PyQt.User.toast import User_Toast
from info import Info_SW as INFO
from local_db.models import ToolbarSettings

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

if TYPE_CHECKING:
    from main import MainWindow

class ToolbarManager (QObject):
    def __init__(self, main_wid:MainWindow):
        super().__init__(main_wid)
        self.main_wid = main_wid
        self.tb = None
        self.toolbar_container = None
        self.divButtons = {}
        self.scroll_area = None
        self.current_orientation = None  # 초기값
        # self.tb = None  # QToolBar
        self._init_toolbar_settings()
        self.subscribe_gbus()

    def subscribe_gbus(self):
        event_bus.subscribe(
            INFO.get_WS_URL_by_name('app_권한'), 
            self.render_toolbar
        )

    def _init_toolbar_settings(self):
        self.styles = {
            'toolbar': {
                'background-color': '#000000',
                'color': '#f6f5f4',
                'font-family': 'Arial',
                'font-size': '16pt',
                'font-weight': 'bold'
            },
            'button': {
                'color': '#f6f5f4',
                'background-color': '#000000',
                'font-family': 'Arial',
                'font-size': '16pt',
                'font-weight': 'bold'
            },
            'hover': {
                'background-color': '#ffffff',
                'color': '#000000'
            }
        }

        self.current_settings = {
            'toolbar_font': QFont('Arial', 16, 7),
            'toolbar_color': '#f6f5f4',
            'toolbar_bg_color': '#000000'
        }
        self.load_settings()
        self.styles['button']['QToolButton:hover'] = {
            'background-color': self.current_settings['toolbar_bg_color'],
            'color': self._get_contrast_color(self.current_settings['toolbar_bg_color'])
        }


    def render_toolbar(self, action: str):
        if action != 'init':
            return
        self.app_권한 = deepcopy(INFO.APP_권한)
        logger.info(f"render_toolbar : app권한 수 :{len(self.app_권한)}")

        # 기존 툴바 제거
        if self.tb:
            try:    
                self.tb.removeEventFilter(self)  # 기존 필터 제거
                self.main_wid.removeToolBar(self.tb)
                self.tb.setParent(None)  # 기존 툴바를 부모에서 분리
                self.tb = None
            except Exception as e:
                logger.error(f"툴바 제거 오류: {e}\n{traceback.format_exc()}")

        # 새 QToolBar 생성
        self.tb = self.main_wid.addToolBar("Dynamic Toolbar")
        self.current_orientation = self.tb.orientation()  # orientation 저장
        self.tb.setMovable(True)  # QToolBar 이동 가능
        self.tb.setFloatable(False)
        self.tb.setAllowedAreas(Qt.TopToolBarArea | Qt.LeftToolBarArea | Qt.RightToolBarArea | Qt.BottomToolBarArea)
        self.tb.setIconSize(QSize(24, 24))
        self.tb.setStyleSheet("background-color: black;")

        # 컨테이너와 스크롤 영역 구성
        self.toolbar_container = QWidget()
        self.toolbar_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.toolbar_container.setFixedHeight(60)
        scroll_layout = QHBoxLayout(self.toolbar_container)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(2)

        # 세로로 배치되면 QVBoxLayout으로 변경
        if self.tb.orientation() == Qt.Vertical:
            scroll_layout = QVBoxLayout(self.toolbar_container)
            scroll_layout.setContentsMargins(5, 5, 5, 5)
            scroll_layout.setSpacing(2)
            self.toolbar_container.setFixedWidth(60)

        # 스크롤 영역 설정
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scroll_area.setFixedHeight(70)
        self.scroll_area.setWidget(self.toolbar_container)

        # scroll_area를 QToolBar에 추가
        self.tb.addWidget(self.scroll_area)

        # 버튼 추가
        self.tb_layout = scroll_layout

        ### home 맨 처음 추가
        # self.PB_HOME = QPushButton('홈')
        # self.PB_HOME.clicked.connect(lambda: event_bus.publish(GBus.HOME_WIDGET_SHOW, True))
        # self.tb_layout.addWidget(self.PB_HOME)

        self._render_by_표시명()

        # 툴바의 이동 감지: 툴바의 위치가 변경될 때마다 orientation을 체크하고 render_toolbar 호출
        self.tb.installEventFilter(self)  # QToolBar에 이벤트 필터 설치
 
    def go_home(self):
        self.curr
        self.main_wid.home_widget.show()

    def eventFilter(self, obj, event):
        if obj == self.tb and event.type() == QEvent.Move:
            new_orientation = self.tb.orientation()
            if new_orientation != self.current_orientation:
                logger.info("Toolbar orientation changed, scheduling re-render...")
                self.current_orientation = new_orientation
                QTimer.singleShot(0, lambda: self.render_toolbar("re-render"))
        return super().eventFilter(obj, event)
    

    def _render_by_표시명(self):
        self.표시명_구분s = []
        self.divButtons = {}

        for appDict in self.app_권한:
            표시명_구분 = appDict.get('표시명_구분')
            if 표시명_구분 and 표시명_구분 not in self.표시명_구분s:
                self.표시명_구분s.append(표시명_구분)

        menu_dict = {}

        self.PB_HOME = QToolButton(self.main_wid)
        self.PB_HOME.setText('홈')
        self.PB_HOME.clicked.connect(lambda: event_bus.publish(GBus.HOME_WIDGET_SHOW, True))
        self.tb_layout.addWidget(self.PB_HOME)

        for 표시명_구분 in self.표시명_구분s:
            obj = QToolButton(self.main_wid)
            obj.setText(표시명_구분)
            self.divButtons[표시명_구분] = obj
            self.tb_layout.addWidget(obj)

            menu = QMenu()
            _appList = []

            for appObj in [a for a in self.app_권한 if a.get('표시명_구분') == 표시명_구분]:
                if INFO.USERID != 1 and not appObj.get('is_Active'):
                    continue
                표시명_항목 = appObj.get('표시명_항목')
                if 표시명_항목:
                    divName, appName = appObj['div'], appObj['name']
                    action = QAction(
                        icon=QIcon(f':/app-icons-{divName}/{appName}'),
                        text=표시명_항목,
                        parent=self.main_wid
                    )
                    action.setObjectName(f'appid_{appObj.get("id")}')
                    if INFO.USERID != 1:
                        action.setEnabled(appObj.get('is_Run', False))
                    action.triggered.connect(
                        lambda checked, app=appObj, menu_name=표시명_구분, act_name=action.objectName():
                            event_bus.publish('toolbar_menu_clicked', {
                                'appObj': app, 'menu': menu_name, 'action': act_name
                            })
                    )
                    menu.addAction(action)
                    _appList.append(appObj)
                    INFO.set_menu_to_action( div = divName, name = appName, action = action)                    

            menu_dict[표시명_구분] = _appList
            menu.setStyleSheet("""
                QMenu {
                    background-color:gray;
                    font-weight:bold;
                    padding:2px 5px;
                }
                QMenu::item {
                    spacing: 3px;
                    padding: 10px 85px 10px 20px;
                    background: transparent;
                }
                QMenu:selected {
                    background-color:black;
                    color:yellow;
                }
            """)
            qtoolbtn = self.divButtons[표시명_구분]
            qtoolbtn.setMenu(menu)
            qtoolbtn.setPopupMode(QToolButton.InstantPopup)

        INFO.MENU_DICT = menu_dict

    def _update_all_styles(self):
        button_style = "; ".join(f"{k}: {v}" for k, v in self.styles['button'].items())
        hover_style = "; ".join(f"{k}: {v}" for k, v in self.styles['hover'].items())

        full_style = f"""
            QToolButton {{ {button_style}; }}
            QToolButton:hover {{ {hover_style}; }}
        """

        if self.scroll_widget:
            self.scroll_widget.setStyleSheet(full_style)

    def load_settings(self):
        try:
            settings = ToolbarSettings.objects.filter(is_active=True).order_by('-id').first()
            if settings:
                font = QFont(settings.font_family, settings.font_size, QFont.Weight.Bold if settings.font_bold else QFont.Weight.Normal)
                self.current_settings['toolbar_font'] = font
                self.current_settings['toolbar_color'] = settings.toolbar_color
                self.current_settings['toolbar_bg_color'] = settings.toolbar_bg_color
                self.styles['toolbar'].update({
                    'font-family': font.family(),
                    'font-size': f"{font.pointSize()}pt",
                    'font-weight': 'bold' if font.bold() else 'normal',
                    'color': settings.toolbar_color,
                    'background-color': settings.toolbar_bg_color
                })
                self.styles['button']['color'] = settings.toolbar_color
                self.styles['button']['QToolButton:hover'] = {
                    'background-color': settings.toolbar_bg_color,
                    'color': self._get_contrast_color(settings.toolbar_bg_color)
                }
                self._update_all_styles()
            else:
                self.save_settings()
        except Exception as e:
            logger.error(f"설정 로드 오류: {e}\n{traceback.format_exc()}")

    def save_settings(self):
        try:
            font = self.current_settings['toolbar_font']
            settings, created = ToolbarSettings.objects.get_or_create(
                defaults={
                    'font_family': font.family(),
                    'font_size': font.pointSize(),
                    'font_bold': font.bold(),
                    'toolbar_color': self.current_settings['toolbar_color'],
                    'toolbar_bg_color': self.current_settings['toolbar_bg_color']
                }
            )
            if not created:
                settings.font_family = font.family()
                settings.font_size = font.pointSize()
                settings.font_bold = font.bold()
                settings.toolbar_color = self.current_settings['toolbar_color']
                settings.toolbar_bg_color = self.current_settings['toolbar_bg_color']
                settings.save()
            User_Toast(INFO.MAIN_WINDOW, 3000, '설정 저장', '툴바 설정이 저장되었읍니다.', 'SUCCESS')
        except Exception as e:
            User_Toast(INFO.MAIN_WINDOW, 3000, '설정 저장 실패', f'오류: {str(e)}', 'ERROR')
            logger.error(f"설정 저장 오류: {e}\n{traceback.format_exc()}")

    def _get_contrast_color(self, bg_color):
        color = QColor(bg_color)
        brightness = ((color.red() * 299) + (color.green() * 587) + (color.blue() * 114)) / 1000
        return '#000000' if brightness > 128 else '#ffffff'

    def _update_all_styles(self):
        hover_style = "QToolButton:hover { " + "; ".join(f"{k}: {v}" for k, v in self.styles['button']['QToolButton:hover'].items()) + " }"
        toolbar_style = "QToolBar, QToolBar QToolButton { " + "; ".join(f"{k}: {v}" for k, v in self.styles['toolbar'].items()) + " }"
        button_style = "QToolButton { " + "; ".join(f"{k}: {v}" for k, v in self.styles['button'].items() if k != 'QToolButton:hover') + " }"
        combined_style = "\n".join([toolbar_style, button_style, hover_style])
        self.main_wid.setStyleSheet(combined_style)

