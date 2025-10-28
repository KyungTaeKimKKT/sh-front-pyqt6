from __future__ import annotations
from typing import TYPE_CHECKING
from modules.common_import_v2 import *

from plugin_main.websocket.handlers.base_handlers import Base_WSMessageHandler_V2

class TooltipEventFilter(QObject):
    def __init__(self, button, tooltip_func):
        super().__init__(button)
        self.button = button
        self.tooltip_func = tooltip_func

    def eventFilter(self, obj, event):
        if obj == self.button and event.type() == QEvent.Type.Enter:
            # 마우스가 버튼 위로 올라가면 tooltip 갱신
            self.button.setToolTip(self.tooltip_func())
        return super().eventFilter(obj, event)

class BaseAppDashboard(QFrame):
    """ app"""
    def __init__(self, 
                 parent=None, 
                 ws_url_name:str=None, 
                 ws_handler_cls : Optional[Base_WSMessageHandler_V2] = None,
                 app_info:dict = {'div':'monitor', 'name':'server_monitor'}, 
                 duration_data_status:int = 3000,
                 **kwargs
                 ):
        super().__init__(parent)
        self.kwargs = kwargs
        self.duration_data_status = duration_data_status
        self.app_info = app_info
        self.app_name = kwargs.get('app_name', None)
        self.ws_url_name = ws_url_name
        self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)
        self.ws_handler_cls = ws_handler_cls
        self.ws_handler = None
        self.try_count = 0
        self._data:dict = None
        self.event_bus = event_bus
        self.txt_app_name = f"App Name: "
        self.txt_last_update = f"Data 기준: "
        self.txt_move_button = f"해당 App 이동"

        self.is_updating = False # data 수신 또는 update 중인지 여부 ==> update_dashboard_area() 에서 사용

        self.setObjectName(f"app_dashboard__{self.app_info.get('div', 'N/A')}_{self.app_info.get('name', 'N/A')}")
        self.style_data_updated = kwargs.get('style_data_updated', f"border: 1px solid rgb(200, 220, 255);background-color:rgb(200, 220, 255);")
        self.style_data_idle = kwargs.get('style_data_idle', f"border: 1px solid black;background-color:white;")

        self.color_data_updated = kwargs.get('color_data_updated', QColor(200, 220, 255))
        self.color_data_idle = kwargs.get('color_data_idle', QColor(255, 255, 255))
        
        ### data 수신 표시용 timer
        self.timer_data_status = QTimer()
        self.timer_data_status.setSingleShot(True)
        self.timer_data_status.timeout.connect(self.render_data_idle )

        self.init_kwargs()
        self.init_ui()
        self.connect_signals()
        # self.check_ws_handler()       ## thread  방식시 필요
        self.check_ws()                 ## non-thread 방식시 필요
        self.subscribe_gbus()


    def paintEvent(self, event):
        super().paintEvent(event)

        if self.is_updating:
            painter = QPainter(self)

            # 전체 영역
            full_region = QRegion(self.rect())

            # child 영역 빼기
            for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
                full_region -= QRegion(child.geometry())

            # 남은 영역만 칠하기
            painter.setClipRegion(full_region)
            painter.fillRect(self.rect(), self.color_data_updated)

            # 테두리 그리기
            pen = QPen(self.color_data_updated)  # 파란색 border
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setClipping(False)  # 테두리는 전체 영역에 그려야 하니까 클리핑 해제
            painter.drawRect(self.rect().adjusted(1,1,-2,-2))
  

    def init_kwargs(self):
        """ 필요시 부모에서 override 해서 사용 """
        return 

    def render_data_updated(self):
        self.is_updating = True
        self.update()
        # self.setStyleSheet(f"#{self.objectName()} {{ {self.style_data_updated} }}") #CSS의 {를 쓰고 싶을 땐 중괄호를 두 번 써서 escape해야 합니다.

    def render_data_idle(self):
        self.is_updating = False
        self.update()
        # self.setStyleSheet(f"#{self.objectName()} {{ {self.style_data_idle} }}")  #CSS의 {를 쓰고 싶을 땐 중괄호를 두 번 써서 escape해야 합니다.

    def init_ui(self):

        self.setMinimumSize(self.kwargs.get('min_width', 300), self.kwargs.get('min_height', 300))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setFrameShape(QFrame.StyledPanel)
        self.main_layout = QVBoxLayout(self)

        self.main_layout.addWidget(self._create_header())

        # 하단 대시보드 영역
        self.main_layout.addWidget ( self._create_dashboard_area() )

        self.setLayout(self.main_layout)

    def _create_dashboard_area(self) -> QFrame:
        """ child 에서 구현해야 함 """
        raise NotImplementedError("_create_dashboard_area() 함수는 child 에서 구현해야 함")
        self.dashboard_area = QFrame()
        self.dashboard_area.setFrameShape(QFrame.StyledPanel)
        return self.dashboard_area

    def _create_header(self) -> QWidget:
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(60)
        self.header_widget.setStyleSheet("background-color: #4caf50;")  # 부드러운 초록 계열

        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(10, 0, 10, 0)

        # 왼쪽에 2줄 텍스트용 vertical layout
        left_text_layout = QVBoxLayout()
        left_text_layout.setContentsMargins(0, 0, 0, 0)
        left_text_layout.setSpacing(2)

        # app_name_label, last_update_label을 2줄로 세로 배치
        self.app_name_label = QLabel(self.txt_app_name)
        # self.app_name_label.setWordWrap(True)
        self.app_name_label.setStyleSheet("font-weight: bold; color: white;")
        self.last_update_label = QLabel(self.txt_last_update)
        # self.last_update_label.setWordWrap(True)
        self.last_update_label.setStyleSheet("color: white; font-size: 11pt;")

        left_text_layout.addWidget(self.app_name_label)
        left_text_layout.addWidget(self.last_update_label)

        self.header_layout.addLayout(left_text_layout)
        self.header_layout.addStretch()

        # 오른쪽에 move_button
        self.move_button = QPushButton(self.txt_move_button)
        self.move_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.move_button.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        if INFO._get_is_app_admin():
            # 이벤트 필터 설치
            self.move_button.installEventFilter(TooltipEventFilter(self.move_button, self._get_move_button_tooltip))

        self.header_layout.addWidget(self.move_button)

        return self.header_widget
    

    def _get_move_button_tooltip(self):
        _text = f"""ws_url_name: {self.ws_url_name} <br>
        ws_url: {self.ws_url} <br>
        ws.handler : { 'None' if self.ws_handler is None else '있음'} <br>
        """
        print (f"self.ws_handler : {self.ws_handler}")
        return _text

    def connect_signals(self):    
        self.move_button.clicked.connect(self.on_move_button_clicked)
    
    def on_move_button_clicked(self):
        if not self.app_info or self.app_info is None:
            logger.error(f"app_info 가 없습니다. {self.app_info}")
            return
        action = INFO.get_menu_to_action(**self.app_info)
        if action and isinstance(action, QAction):
            action.trigger()
        else:
            logger.error(f"action 가 없습니다. {action}")

    def check_ws(self):
        if not self.ws_url:
            self.set_ws_url(self.ws_url_name)

        if not self.ws_url:
           raise ValueError(f"ws_url 이 없습니다. {self.ws_url}")
        
        if self.ws_url not in INFO.WS_TASKS:
            ws_manager = APP.get_WS_manager()
            connect_msg = self.kwargs.get('ws_handler_kwargs', {}).get('connect_msg', {})
            ws_manager.add(self.ws_url, connect_msg=connect_msg)
        

    

    # def check_ws_handler(self):
    #     #### 검증 처리
    #     if not self.ws_url:
    #         self.set_ws_url(self.ws_url_name)

    #     if not self.ws_url:
    #         logger.error(f"ws_url 이 없습니다. {self.ws_url}")
    #         return
        
    #     if self.ws_handler is None and not isinstance(self.ws_handler_cls, type):
    #         logger.error(f"ws_handler_cls 가 없거나 올바르지 않습니다. {self.ws_handler_cls}")
    #         return
        
    #     #### 처리  : 만약 handler가 없으면 생성
    #     if self.ws_url not in INFO.WS_TASKS:
    #         self.ws_handler = self.ws_handler_cls(self.ws_url, **self.kwargs.get('ws_handler_kwargs', {}))
    #         INFO.WS_TASKS[self.ws_url] = self.ws_handler


    def set_ws_url(self, ws_url_name:str=None):
        self.ws_url_name = ws_url_name or self.ws_url_name
        self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)

    def subscribe_gbus(self):
        if not self.ws_url:
            logger.error(f"ws_url 이 없습니다. {self.ws_url}")
            return
        self.event_bus.subscribe( self.ws_url, self.on_data_changed)


    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe( self.ws_url, self.on_data_changed)

    def activate_data_status_timer(self):
        """ update_dashboard_area() 에서 호출. 왜냐면 update 시, 무조건 호출하면 ws 든, 아니든 모두 호출되기 때문에 따로 호출하지 않음 """
        self.timer_data_status.stop()
        self.timer_data_status.start(self.duration_data_status)
        self.render_data_updated()

    def on_data_changed(self, data: dict):
        try:
            self.activate_data_status_timer()
            self._data = data.copy()
            self._update_timestamp()
            self._update_app_name()
            self.update_dashboard_area()
        except Exception as e:
            logger.error(f"on_data_changed 오류: {e}")
            logger.error(traceback.format_exc())

    def update_dashboard_area(self):
        """ child 에서 구현해야 함 :   _create_dashboard_area() 에서 생성된 widget 에 데이터 업데이트 """
        raise NotImplementedError(f"{self.__class__.__name__} : update_dashboard_area() 함수는 child 에서 구현해야 함")
    

    def _update_timestamp(self):
        if self._data:
            timestamp = self._data.get('timestamp', datetime.now().isoformat())
            _update_time = Utils.format_datetime_str_with_weekday(timestamp, with_year=True, with_weekday=True)
            self.last_update_label.setText(f"{self.txt_last_update}{_update_time}")
        else:
            self.last_update_label.setText(f"Data 기준(update 시간) : data 가 없읍니다(N/A)")

    def _update_app_name(self):
        app_name = self.app_name or f"{self.app_info.get('div', 'N/A')}/{self.app_info.get('name', 'N/A')}"
        self.app_name_label.setText(f"{self.txt_app_name}{app_name}")




    # def resizeEvent(self, event):
    #     if self.width() <= 0 or self.height() <= 0:
    #         return
    #     super().resizeEvent(event)