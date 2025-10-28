from modules.common_import_v2 import *

from modules.PyQt.Tabs.home.server_resource.cpu_ram import DashboardWidget_ServerResource
from modules.PyQt.Tabs.home.server_resource.network_summary import DashboardWidget_NetworkSummary
from modules.PyQt.Tabs.home.app_usage.client_usage import DashboardWidget_ClientUsage
from modules.PyQt.Tabs.home.apps.mbo_report import DashboardWidget_MBO_Report_지사구분, DashboardWidget_MBO_Report_지사고객사
from modules.PyQt.Tabs.home.server_resource.db_status import DashboardWidget_ServerDB_Status

from plugin_main.websocket.handlers.server_monitor import ServerMonitorHandler_V2
from plugin_main.websocket.handlers.network_monitor import NetworkMonitorHandler_V2
from plugin_main.websocket.handlers.client_app_access_log import ClientAppAccessDashboardHandler
from plugin_main.websocket.handlers.apps_handler import AppsHandler_V2
from plugin_main.websocket.handlers.server_db_status_handler import ServerDB_Status_Handler_No_Thread


from modules.PyQt.text_animation.marquee import Marquee
from modules.PyQt.text_animation.typewriter import TypewriterLabel

class DummyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: transparent; border: none;")

class DashboardTable(QTableWidget):
    def __init__(self, parent=None, widgets:Optional[QWidget]=[], row=2, col=2, default_dict=None, **kwargs):
        super().__init__(parent)
        self.widgets = widgets
        self.default_dict = default_dict or {}

        # 헤더 표시 (사용자 조절 가능하도록)
        self.horizontalHeader().setVisible(True)
        self.verticalHeader().setVisible(True)

        # 헤더 섹션 크기 조절 모드 고정
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        self.setShowGrid(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.columns = col  # 초기값
        self.rows = row  # 초기값
        # 초기 컬럼 및 너비 설정
        self.init_columns_by_width()

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     self.init_columns_by_width()

    def init_columns_by_width(self):
        w = self.width()
        if w < 1000:
            cols = 2
            col_width = int(w / 2.5)
        elif w < 2000:
            cols = 3
            col_width = int(w / 3.5)
        else:
            cols = 4
            col_width = int(w / 4.5)

        self.setColumnCount(cols)
        for col in range(cols):
            self.setColumnWidth(col, col_width)

        if self.widgets:
            self.rearrange_widgets()

    def set_widgets(self, widgets:list[QWidget]):
        self.widgets = widgets
        self.rearrange_widgets()

    # def add_dashboard_widget(self, widget):
    #     self.widgets.append(widget)
    #     self.rearrange_widgets()

    def rearrange_widgets(self):
        self.setRowCount(0)  # 모든 행 제거

        if self.columnCount() == 0:
            return

        row = 0
        col = 0
        for w in self.widgets:
            if col >= self.columnCount():
                col = 0
                row += 1
            if self.rowCount() <= row:
                self.insertRow(row)
            self.setCellWidget(row, col, w)
            # 행 높이 고정
            self.setRowHeight(row, 400)
            col += 1

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     min_width = 300
    #     new_columns = max(2, min(4, self.width() // min_width))
    #     if new_columns != self.columnCount():
    #         self.setColumnCount(new_columns)
    #         QTimer.singleShot(0, self.rearrange_widgets)  # 레이아웃 재배치 지연 실행
    #     col_width = self.viewport().width() // self.columnCount()
    #     for col in range(self.columnCount()):
    #         self.setColumnWidth(col, col_width)


class DraggableWidget(QWidget):
    def __init__(self, inner_widget, parent=None):
        super().__init__(parent)
        self.inner_widget = inner_widget
        self.inner_widget.setParent(self)

        self.setFixedSize(inner_widget.size())
        self.drag_start_pos = None

        self.dragging = False
        self.drag_offset = QPointF(0,0)

        self.edit_mode = False

    def set_edit_mode(self, mode:bool):
        self.edit_mode = mode
        self.inner_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, mode)        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.inner_widget.resize(self.size())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position()
            self.dragging = False
            self.original_pos = self.pos()  # 드래그 시작 시 위치 저장
        super().mousePressEvent(event)

    # def mouseMoveEvent(self, event: QMouseEvent):
    #     if self.drag_start_pos is not None:
    #         distance = (event.position() - self.drag_start_pos).manhattanLength()
    #         if distance > QApplication.startDragDistance():
    #             # signal to parent that drag started
    #             self.parent().start_drag(self, event.globalPosition())

    def mouseMoveEvent(self, event:QMouseEvent):
        if self.drag_start_pos is not None:
            distance = (event.position() - self.drag_start_pos).manhattanLength()
            if distance > QApplication.startDragDistance():
                if not self.dragging:
                    # signal to parent that drag started
                    self.parent().start_drag(self, event.globalPosition())
                    # 드래그 시작 - 드래그 상태 true, 오프셋 계산
                    self.dragging = True
                    # 위젯 내부 좌표 기준 오프셋
                    self.drag_offset = event.position()
                    self.raise_()  # 최상위로 띄움
                # 현재 마우스 위치에 위젯 이동
                global_pos = self.mapToParent(event.position().toPoint() - self.drag_offset.toPoint())
                self.move(global_pos)
                # 부모에게 drag 위치 업데이트 신호(선택적으로)
                # self.parent().update_drag_position(self, global_pos)

    # def mouseReleaseEvent(self, event: QMouseEvent):
    #     pos = event.globalPosition()
    #     pos_int = QPoint(int(pos.x()), int(pos.y()))
    #     self.parent().end_drag(pos_int)

    def mouseReleaseEvent(self, event:QMouseEvent):
        if self.dragging:
            # 드래그 끝
            self.dragging = False
            pos = event.globalPosition()
            pos_int = QPoint(int(pos.x()), int(pos.y()))
            self.parent().end_drag(pos_int)
        self.drag_start_pos = None

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.dragging:
            # 반투명 오버레이로 드래그중임 시각화
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(100, 100, 100, 100))


class DashboardGridWidget(QWidget):
    def __init__(self, parent=None, widgets:Optional[QWidget]=[], max_row_height:int=400, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.fixed_spacing = self.kwargs.get('fixed_spacing', 10)
        self.widgets = widgets
        self.columns = self.kwargs.get('columns', 2)  # 초기 컬럼 수
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(self.fixed_spacing)
        self.max_row_height = max_row_height
        self.setLayout(self.grid_layout)

        # 래퍼로 감싸서 드래그 이벤트 처리 위임
        self.draggable_widgets = []
        self.original_widgets = []
        for w in self.widgets:
            dw = DraggableWidget(w, self)
            self.draggable_widgets.append(dw)
            dw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.dragging_widget = None

        if self.widgets:
            self._relayout()

        self.edit_mode = False

    def add_dashboard_widget(self, widget):
        dw = DraggableWidget(widget, self)
        dw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.draggable_widgets.append(dw)
        self._relayout()

    def set_edit_mode(self, mode:bool):
        self.edit_mode = mode
        if mode:
            # 원본 위젯 리스트 저장 (드래거블 래퍼가 아니라)
            self.original_widgets = self.widgets[:]
        for dw in self.draggable_widgets:
            dw.set_edit_mode(mode)


    def apply_to_original_widgets(self):
        # widgets를 원본으로 복원
        self.widgets = self.original_widgets[:]

        # 기존 draggable_widgets 제거 및 재생성
        for dw in self.draggable_widgets:
            self.grid_layout.removeWidget(dw)
            dw.deleteLater()
        self.draggable_widgets.clear()

        for w in self.widgets:
            dw = DraggableWidget(w, self)
            dw.set_edit_mode(self.edit_mode)
            self.draggable_widgets.append(dw)

        self._relayout()



    def _relayout(self):
        # 기존 레이아웃 정리
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)


        w = self.width()
        total_spacing = self.fixed_spacing * (self.columns - 1)
        fixed_width = ( w - total_spacing) // self.columns
        fixed_height = self.max_row_height

        total_widgets = len(self.widgets)
        # 마지막 행에 필요한 dummy 갯수 계산
        remainder = total_widgets % self.columns
        if remainder != 0:
            dummy_count = self.columns - remainder
        else:
            dummy_count = 0

        # 위젯 배치
        total_widgets = len(self.draggable_widgets)
        remainder = total_widgets % self.columns
        dummy_count = (self.columns - remainder) if remainder != 0 else 0

        all_widgets = self.draggable_widgets + [QWidget(self) for _ in range(dummy_count)]
        row = 0
        col = 0
        for widget in all_widgets:
            self.grid_layout.addWidget(widget, row, col)
            widget.setFixedSize(fixed_width, fixed_height)
            col += 1
            if col >= self.columns:
                col = 0
                row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 컬럼 수 계산 (부모 너비 기준으로)
        w = self.width()
        if w < 600:
            new_columns = 1
        elif w < 1200:
            new_columns = 2
        elif w < 1800:
            new_columns = 3
        else:
            new_columns = 4
        
        if not hasattr(self, '_prev_width'):
            setattr(self, '_prev_width', w)

        # 컬럼 수 변경 또는 너비 변경 시 relayout
        if new_columns != self.columns or abs(w - self._prev_width) > self.fixed_spacing * 3:
            self.columns = new_columns
            self._prev_width = w
            if hasattr(self, '_resize_timer'):
                self._resize_timer.stop()
            else:
                self._resize_timer = QTimer(self)
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self._relayout)
            self._resize_timer.start(300)

    
    def start_drag(self, widget, global_pos):
        if self.dragging_widget is None:
            self.dragging_widget = widget
            self.dragging_start_pos = global_pos

    def end_drag(self, global_pos):
        if self.dragging_widget is None:
            return

        # global_pos는 QPointF이므로 QPoint로 변환 (정수 좌표)
        pos = self.mapFromGlobal(QPoint(int(global_pos.x()), int(global_pos.y())))
        target_index = self._widget_index_at_pos(pos)

        dragging_index = self.draggable_widgets.index(self.dragging_widget)

        if target_index is None:
            # 유효하지 않은 위치 → 원래 위치로 복귀
            self.draggable_widgets[dragging_index].move(self.draggable_widgets[dragging_index].original_pos)
        elif dragging_index != target_index:
            # 위치 변경 가능 → 스왑
            self.draggable_widgets[dragging_index], self.draggable_widgets[target_index] = (
                self.draggable_widgets[target_index],
                self.draggable_widgets[dragging_index],
            )
            self._relayout()
        else:
            # 같은 자리면 원래 위치로
            self.draggable_widgets[dragging_index].move(self.draggable_widgets[dragging_index].original_pos)

        self.dragging_widget = None

    def _widget_index_at_pos(self, pos: QPoint):
        """pos (local coord)에서 그리드 내 위젯 인덱스 반환"""
        if not self.draggable_widgets:
            return None
        # 각 셀 너비, 높이
        w = self.width()
        total_spacing = self.fixed_spacing * (self.columns - 1)
        cell_width = (w - total_spacing) // self.columns
        cell_height = self.max_row_height

        col = int(pos.x() // (cell_width + self.fixed_spacing))
        row = int(pos.y() // (cell_height + self.fixed_spacing))

        index = row * self.columns + col
        if 0 <= index < len(self.draggable_widgets):
            return index
        return None

class HomeDashboardWidget(QWidget):
    """
    Home 대시보드 위젯
    """
    HEADER_FIXED_HEIGHT = 120

    def __init__(self, parent=None):
        super().__init__(parent)

        self.edit_mode = False
        self.default_dict = {
            'server_monitor' : {
                'ws_url_name' : 'server_monitor',
                'ws_handler_cls' : ServerMonitorHandler_V2,
                'app_info' : {'div':'monitor', 'name':'server_monitor'},
                'cpu_config' : {'label' : 'CPU 사용률', 'max_value' : 100, 'warning_threshold' : 80},
                'mem_config' : {'label' : '메모리 사용률', 'max_value' : 100, 'warning_threshold' : 85},
            },
            'db_live_dashboard' : {
                'ws_url_name' : 'db_live_dashboard',
                'ws_handler_cls' : ServerDB_Status_Handler_No_Thread,
                'app_info' : {'div':'monitor', 'name':'Server_DB_Status'},
            },
            'network_monitor' : {
                'ws_url_name' : 'network_monitor',
                'ws_handler_cls' : NetworkMonitorHandler_V2,
                'app_info' : {'div':'monitor', 'name':'network_monitor'},
                'max_ping_count' : 6,                
            },
            'client_app_access_dashboard' : {
                'ws_url_name' : 'client_app_access_dashboard',
                'ws_handler_cls' : ClientAppAccessDashboardHandler,
                'app_info' : {'div':'monitor', 'name':'client_app_access_dashboard'},
                'max_app_best' : 10,
            },
            'mbo_report_지사구분' : {
                'ws_url_name' : 'mbo_report:지사_구분',
                'ws_handler_cls' : AppsHandler_V2,
                'app_info' : {'div':'영업mbo', 'name':'년간보고_지사_구분'},
                'ws_handler_kwargs' : {
                    'connect_msg' : {
                        'main_type' : 'init',
                        'sub_type' : 'request',
                        'action' : 'init',
                        'subject' : '지사_구분_report',
                        'receiver' : 'server',
                        'sender' : INFO.USERID,
                    },
                },
            },
            'mbo_report_지사고객사' : {
                'ws_url_name' : 'mbo_report:지사_고객사',
                'ws_handler_cls' : AppsHandler_V2,
                'app_info' : {'div':'영업mbo', 'name':'년간보고_지사_고객사'},
                'ws_handler_kwargs' : {
                    'connect_msg' : {
                        'main_type' : 'init',
                        'sub_type' : 'request',
                        'action' : 'init',
                        'subject' : '지사_고객사_report',
                        'receiver' : 'server',
                        'sender' : INFO.USERID,
                    },
                },
            },
        }
        

        self.setup_ui()

    def create_widgets(self):
        widgets :list[QWidget] = []
        widgets.append(DashboardWidget_ServerResource(self, **self.default_dict['server_monitor'] ))
        widgets.append(DashboardWidget_ServerDB_Status(self, **self.default_dict['db_live_dashboard'] ))
        widgets.append(DashboardWidget_NetworkSummary(self, **self.default_dict['network_monitor'] ))
        widgets.append(DashboardWidget_ClientUsage(self, **self.default_dict['client_app_access_dashboard'] ))
        widgets.append(DashboardWidget_MBO_Report_지사구분(self, **self.default_dict['mbo_report_지사구분'] ))
        widgets.append(DashboardWidget_MBO_Report_지사고객사(self, **self.default_dict['mbo_report_지사고객사'] ))
        return widgets

    def create_header_normal(self) -> QWidget:
        self.wid_header_normal = QWidget()
        self.wid_header_normal.setStyleSheet("background-color: #4caf50;")  # 부드러운 초록 계열
        self.wid_header_normal.setFixedHeight(self.HEADER_FIXED_HEIGHT)
        self.h_layout_header_normal = QHBoxLayout(self.wid_header_normal)

        ###  textanimation 사용

        self.wid_label_container = QWidget()
        v_layout_label_container = QVBoxLayout(self.wid_label_container)
        layout1 = QHBoxLayout()
        self.marquee_label_normal = Marquee(self, text='Live Dashboard 동작중입니다.!!!')
        layout1.addWidget(self.marquee_label_normal)
        v_layout_label_container.addLayout(layout1)
        layout2 = QHBoxLayout()
        self.typewriter_label_normal = TypewriterLabel(self, datas=["Live Dashboard 동작중입니다.!!!"], char_interval=200, position="fixed_center")
        layout2.addWidget(self.typewriter_label_normal)
        v_layout_label_container.addLayout(layout2)

        if INFO._get_is_app_admin() :
            self._create_marquee_debug( layout=layout1)
            self._create_typewriter_debug(layout=layout2)
        
        self.h_layout_header_normal.addWidget(self.wid_label_container)

        self.h_layout_header_normal.addStretch()

        self.PB_edit = QPushButton('Layout 편집모드')
        self.PB_edit.clicked.connect(lambda: self.set_edit_mode())
        self.h_layout_header_normal.addWidget(self.PB_edit)
        return self.wid_header_normal
    
    def _create_marquee_debug(self, layout:QHBoxLayout) -> QWidget:
        # 1. cb 방향
        layout.addWidget(QLabel('방향:'))
        self.cb_direction = QComboBox()
        for direction in Marquee.directions:
            self.cb_direction.addItem(direction, userData=direction)
        self.cb_direction.currentTextChanged.connect(lambda text: self.marquee_label_normal.set_direction(text))
        layout.addWidget(self.cb_direction)
        # 2. sb 속도
        layout.addWidget(QLabel('속도:'))
        self.sb_speed = QSpinBox()
        self.sb_speed.setRange(1, 10)
        self.sb_speed.setValue(3)
        self.sb_speed.valueChanged.connect(lambda value: self.marquee_label_normal.set_speed(value))
        layout.addWidget(self.sb_speed)
        # 3. sb loop
        layout.addWidget(QLabel('loop:'))
        self.sb_loop = QSpinBox()
        self.sb_loop.setRange(-1, 10)
        self.sb_loop.setValue(-1)
        self.sb_loop.valueChanged.connect(lambda value: self.marquee_label_normal.set_loop(value))
        layout.addWidget(self.sb_loop)
        # 4. pause duration
        layout.addWidget(QLabel('중지시간:'))
        self.sb_pause_duration = QSpinBox()
        self.sb_pause_duration.setRange(100, 10000)
        self.sb_pause_duration.setValue(3000)
        self.sb_pause_duration.valueChanged.connect(lambda value: self.marquee_label_normal.set_pause_duration(value))
        layout.addWidget(self.sb_pause_duration)
        # 5. flow interval
        layout.addWidget(QLabel('흐름 간격:'))
        self.sb_flow_interval = QSpinBox()
        self.sb_flow_interval.setRange(1, 1000)
        self.sb_flow_interval.setValue(16)
        self.sb_flow_interval.valueChanged.connect(lambda value: self.marquee_label_normal.set_flow_interval(value))
        layout.addWidget(self.sb_flow_interval)
        # 5. text
        self.le_text_marquee = QLineEdit()
        self.le_text_marquee.setPlaceholderText('텍스트 추가')
        self.le_text_marquee.returnPressed.connect(lambda: self.marquee_label_normal.add_text(self.le_text_marquee.text()))
        layout.addWidget(self.le_text_marquee)
        

    def _create_typewriter_debug(self, layout:QHBoxLayout) -> QWidget:
        # 1. cb 방향
        layout.addWidget(QLabel('위치:'))
        self.cb_position = QComboBox()
        for position in TypewriterLabel.position_list:
            self.cb_position.addItem(position, userData=position)
        self.cb_position.currentTextChanged.connect(lambda text: self.typewriter_label_normal.set_position(text))
        layout.addWidget(self.cb_position)
        # 2. char_interval
        layout.addWidget(QLabel('문자 간격:'))
        self.sb_char_interval = QSpinBox()
        self.sb_char_interval.setRange(1, 1000)
        self.sb_char_interval.setValue(200)
        self.sb_char_interval.valueChanged.connect(lambda value: self.typewriter_label_normal.set_char_interval(value))
        layout.addWidget(self.sb_char_interval)
        # 3. str_interval
        layout.addWidget(QLabel('문자열 간격:'))
        self.sb_str_interval = QSpinBox()
        self.sb_str_interval.setRange(1, 1000)
        self.sb_str_interval.setValue(1000)
        self.sb_str_interval.valueChanged.connect(lambda value: self.typewriter_label_normal.set_str_interval(value))
        layout.addWidget(self.sb_str_interval)

        # 4. blink_interval
        layout.addWidget(QLabel('깜빡임 간격:'))
        self.sb_blink_interval = QSpinBox()
        self.sb_blink_interval.setRange(100, 10000)
        self.sb_blink_interval.setValue(3000)
        self.sb_blink_interval.valueChanged.connect(lambda value: self.typewriter_label_normal.set_blink_interval(value))
        layout.addWidget(self.sb_blink_interval)
        # 5. text
        self.le_text_typewriter = QLineEdit()
        self.le_text_typewriter.setPlaceholderText('텍스트 추가')
        self.le_text_typewriter.returnPressed.connect(lambda: self.typewriter_label_normal.add_text(self.le_text_typewriter.text()))
        layout.addWidget(self.le_text_typewriter)

    
    def create_header_edit_layout(self) -> QWidget:
        self.wid_header_edit_layout = QWidget()
        self.wid_header_edit_layout.setStyleSheet("background-color: #4caf50;")  # 부드러운 초록 계열
        self.wid_header_edit_layout.setFixedHeight(60)
        self.h_layout_header_edit = QHBoxLayout(self.wid_header_edit_layout)
        ###  textanimation 사용
        # self.marquee_label_edit = Marquee(self, text='Live Dashboard Layout [ 편집 ]중입니다.!!!')
        # self.h_layout_header_edit.addWidget(self.marquee_label_edit)

        self.h_layout_header_edit.addStretch()

        self.PB_save = QPushButton('Layout 저장')
        self.PB_save.clicked.connect(lambda: self.save_edit_layout())
        self.h_layout_header_edit.addWidget(self.PB_save)

        self.PB_cancel = QPushButton('Layout 취소')
        self.PB_cancel.clicked.connect(lambda: self.cancel_edit_layout())
        self.h_layout_header_edit.addWidget(self.PB_cancel)

        return self.wid_header_edit_layout

    def set_edit_mode(self):
        self.edit_mode = True
        self.wid_header_normal.hide()
        self.wid_header_edit_layout.show()
        self.grid_container.set_edit_mode(True)

    def exit_edit_mode(self):
        self.edit_mode = False
        self.wid_header_normal.show()
        self.wid_header_edit_layout.hide()
        self.grid_container.set_edit_mode(False)

    def save_edit_layout(self):
        ### 저장은 나중에
        self.exit_edit_mode()

    def cancel_edit_layout(self):
        self.exit_edit_mode()
        self.grid_container.apply_to_original_widgets()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.create_header_normal())
        self.main_layout.addWidget(self.create_header_edit_layout())
        self.wid_header_edit_layout.hide()
        # self.grid_container = DashboardTable(self, widgets=self.create_widgets())
        self.grid_container = DashboardGridWidget(self, widgets=self.create_widgets())

        self.main_layout.addWidget(self.grid_container)

        self.main_layout.addStretch()
        self.setLayout(self.main_layout)




