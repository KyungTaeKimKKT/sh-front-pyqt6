from __future__ import annotations
from modules.common_import_v2 import *
from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2

from modules.PyQt.compoent_v2.charts.gantt.base_gantt import (
    Base_GanttModel, Base_GanttScene, GanttHeaderItem, GanttLabelCellItem, GanttBodyCellItem,
    Base_GanttView, Base_GanttMainWidget
)
from functools import partial
from calendar import monthrange


NO_BRUSH = QBrush(Qt.BrushStyle.NoBrush)
PIXMAP_ACTIVITY = 'cs:activity'
STATUS = ['작성','의뢰','접수','완료']

MAP_COLOR_BY_진행현황 = {
    '작성' : {
        'plan' : QBrush(QColor("gray")),
        'actual' : NO_BRUSH,
    },
    '의뢰' : {
        'plan' : QBrush(QColor("gray")),
        'actual' : NO_BRUSH,
    },
    '접수' : {
        'plan' : {
            '완료요청일' : QBrush(QColor("gray")),
            '완료목표일' : QBrush(QColor("lightblue")),
        },
        'actual' : QBrush(QColor("yellow")),
    },
    '완료' : {
        'plan' : {
            '완료요청일' : QBrush(QColor("gray")),
            '완료목표일' : QBrush(QColor("lightblue")),
        },
        'actual' : QBrush(QColor("green")),
    },
    'default' : NO_BRUSH,
    '지연' : QBrush(QColor("red")),
}

MAP_COLOR_BY_BAR_TYPE = {
    '완료요청일' : QBrush(QColor("gray")),
    '완료목표일' : QBrush(QColor("lightblue")),
    '실적BAR' :  {
        '접수' : QBrush(QColor("yellow")),
        '완료' : QBrush(QColor("green")),
    },
    '지연BAR' : QBrush(QColor("red")),
    'default' : NO_BRUSH,
}

범례= {
    '계획' :{
        '영업 완료요청일': MAP_COLOR_BY_진행현황['작성']['plan'],
        'CS 완료목표일': MAP_COLOR_BY_진행현황['접수']['plan']['완료목표일'],
    },
    '실적' :{
        '접수/진행중': MAP_COLOR_BY_진행현황['접수']['actual'],
        '완료': MAP_COLOR_BY_진행현황['완료']['actual'],
        '지연': MAP_COLOR_BY_진행현황['지연'],
    },
}

class GanttBackgroundLegendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gantt 색상 범례")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        v_layout = QVBoxLayout()
        # 1. 설명 텍스트 (HTML + 스타일)
        _text = """
            <div style="font-size:13px; line-height:1.6;">
                <b>1.</b> 상단 bar: <span style="color:#555;">계획 (영업요청일, CS목표일)</span><br>
                <b>2.</b> 하단 bar: <span style="color:#555;">실적 (접수 이후부터 완료까지)</span><br>
                <b>3.</b> <span style="color:red;">지연</span>은 빨간색으로 표시<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(영업요청일 또는 CS목표일 중 <b>큰 날짜</b> 기준)<br>
                <b>4.</b> Cell에 아이콘 표시 시: 해당일 활동 존재<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(우클릭 시 활동 확인 가능)
            </div>
        """

        label = QLabel(_text)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        v_layout.addWidget(label)

        v_layout.addSpacing(16)

        # 범례 grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)  # 상태
        grid.setColumnStretch(1, 1)  # 항목
        grid.setColumnStretch(2, 2)  # 설명
        grid.setColumnStretch(3, 3)  # 색상 bar

        row = 0
        for status, bar_map in 범례.items():
            for bar_type, value in bar_map.items():
                if isinstance(value, QBrush):
                    if value.style() == Qt.BrushStyle.NoBrush:
                        continue
                    grid.addWidget(QLabel(status), row, 0)
                    grid.addWidget(QLabel(bar_type), row, 1)
                    grid.addWidget(QLabel(""), row, 2)
                    grid.addWidget(self._make_color_box(value), row, 3)
                    row += 1
                elif isinstance(value, dict):
                    for subkey, brush in value.items():
                        if brush.style() == Qt.BrushStyle.NoBrush:
                            continue
                        grid.addWidget(QLabel(status), row, 0)
                        grid.addWidget(QLabel(bar_type), row, 1)
                        grid.addWidget(QLabel(subkey), row, 2)
                        grid.addWidget(self._make_color_box(brush), row, 3)
                        row += 1

        v_layout.addLayout(grid)
        self.setLayout(v_layout)

    def _make_color_box(self, brush: QBrush) -> QWidget:
        color = brush.color().name()
        box = QWidget()
        box.setFixedSize(80, 14)  # ← bar 형태로 변경 (가로 길게, 세로 얇게)
        box.setStyleSheet(
            f"background-color: {color}; border: 1px solid #999; border-radius: 3px;"
        )
        return box


class CS_Gantt_BodyCellItem(GanttBodyCellItem):

    def contextMenuEvent(self, event):
        """ 가능한 상속받은데서 override 해서 사용할 것 """
        if not self.is_data_exist():
            return
        menu = QMenu()
        key = "Activity 보기"
        action = menu.addAction(key)
        if Utils.is_valid_method(self.get_main_wid(), 'on_body_menu_action'):
            action.triggered.connect(partial(self.get_main_wid().on_body_menu_action, key, self.get_data()))
        else:
            logger.critical(f"on_body_menu_action 메서드가 없습니다. : {self.get_main_wid()}")
        menu.exec(event.screenPos())

class CS_Gantt_HeaderCellItem(GanttHeaderItem):
    pass

class CS_Gantt_LabelCellItem(GanttLabelCellItem):

    def is_enable_context_menu(self) -> bool:
        if Utils.is_valid_method(self.model, 'is_enable_context_menu'):
            return self.model.is_enable_context_menu(self.index)
        return False


# class CS_Gantt_Model(Base_GanttModel):
class CS_Gantt_Model(Base_GanttModel):

    def is_enable_context_menu(self, index:QModelIndex, **kwargs) -> bool:
        header_name = self.get_label_headers()[index.column()]
        return header_name == '현장명'

    
    def _get_hoverable(self, index:QModelIndex, **kwargs) -> bool:
        bar_type = kwargs.get('bar_type', 'default')
        if bar_type == 'background':
            return False
        if bar_type == 'plan' or bar_type == 'default':
            return False

        row, col = index.row(), index.column()
        claimID = self._data[row].get('id', '')
        col_date = self.body_headers[col - len(self.label_headers)]
        return self.check_activity_in_date(claimID, col_date)


    def _role_display(self, row: int, col: int, **kwargs) -> str:
        task = self._data[row]
        # LABEL 영역
        if self._is_label_column(col):
            key = self.get_label_headers()[col]
            try:
                if key == "현장주소":
                    _text = task.get(key, "").strip().split(' ')                
                    return f"{_text[0]} {_text[1]}"                
                return task.get(key, "")
            except Exception as e:
                print(f"CS_Gantt_Model: _role_display: {e}")
                return task.get(key, "")
 
        # BODY 영역
        elif self._is_body_column(col):
            try:
                _type = kwargs.get('_type', 'unknown')


                col_date = self.body_headers[col - len(self.label_headers)]

                start = datetime.fromisoformat(task['등록일']).date()
                end = datetime.fromisoformat(task['완료요청일']).date()
                # print(f"_type: {_type}, start: {start}, end: {end}, col_date: {col_date} : {start <= col_date <= end}")
                if start <= col_date <= end:
                    return "■"
                return ""
            except Exception as e:
                print(f"CS_Gantt_Model: _role_display: {e}")
                return ""

    def _role_background(self, row: int, col: int, **kwargs) -> QBrush:
        bar_type = kwargs.get('bar_type', 'default')
        col_date = self.body_headers[col - len(self.label_headers)]
        today = date.today()

        if bar_type == 'background':
            if INFO._is_holiday(col_date):
                return QBrush(QColor("lightgray"))
            if col_date == date.today():
                return QBrush(QColor("lightblue"))
            return MAP_COLOR_BY_진행현황['default']

        진행현황 = self._data[row].get('진행현황', '')
        등록일_str = self._data[row].get('등록일', '')
        접수일_str = self._data[row].get('접수일', '')
        완료요청일_str = self._data[row].get('완료요청일', '')
        완료목표일_str = self._data[row].get('완료목표일', 완료요청일_str)
        완료일_str = self._data[row].get('완료일', '')

        default = MAP_COLOR_BY_진행현황['default']
        지연bar = MAP_COLOR_BY_진행현황['지연']
        등록일 = datetime.fromisoformat(등록일_str).date()
        완료요청일 = datetime.fromisoformat(완료요청일_str).date()
        
        match bar_type:
            case '완료요청일':
                if 등록일 <= col_date <= 완료요청일:
                    return MAP_COLOR_BY_BAR_TYPE[bar_type]
                
            case '완료목표일':
                if 진행현황 != '작성':
                    if 완료목표일_str:
                        완료목표일 = datetime.fromisoformat(완료목표일_str).date()
                        if 등록일 <= col_date <= 완료목표일:
                            return MAP_COLOR_BY_BAR_TYPE[bar_type]
                
            case '실적BAR':
                if 진행현황 == '접수': #### 진행중
                    접수일 = datetime.fromisoformat(접수일_str).date()
                    if 접수일 <= col_date <= today:
                        return MAP_COLOR_BY_BAR_TYPE[bar_type][진행현황]
                elif 진행현황 == '완료':                   
                    접수일 = datetime.fromisoformat(접수일_str).date()
                    완료일 = datetime.fromisoformat(완료일_str).date()
                    if 접수일 <= col_date <= 완료일:
                        return MAP_COLOR_BY_BAR_TYPE[bar_type][진행현황]
                
            case '지연BAR':
                if 진행현황 == '접수' or 진행현황 == '완료':
                    if self._is_지연(col_date, row, 진행현황):
                        return MAP_COLOR_BY_BAR_TYPE[bar_type]                

        return MAP_COLOR_BY_진행현황['default']
    
    def _is_지연(self, col_date:date, row:int, 진행현황:str) -> bool:
        dataObj = self._data[row]
        today = date.today()
        match 진행현황:
            case '접수':
                접수일 = datetime.fromisoformat(dataObj.get('접수일', '')).date()
                if 접수일 <= col_date <= today:
                    완료목표일 = datetime.fromisoformat(dataObj.get('완료목표일', '')).date()
                    return col_date > 완료목표일
            case '완료':
                접수일 = datetime.fromisoformat(dataObj.get('접수일', '')).date()
                완료일 = datetime.fromisoformat(dataObj.get('완료일', '')).date()
                완료목표일 = datetime.fromisoformat(dataObj.get('완료목표일', '')).date()
                if 접수일 <= col_date <= 완료일:
                    return col_date > 완료목표일
            case _:
                return False
        return False


    def get_bar_z_index(self, bar_type:str, index:None|QModelIndex =None) -> int:
        if bar_type == 'background':
            return -1
        bar_layout = self.shape_config.get('bar_layout', {})
        if index is None:
            return bar_layout.get(bar_type, {}).get('z_index', 0)
        else:
            obj = self._data[index.row()]
            _완료요청일_str = obj.get('완료요청일', '')
            _완료목표일_str = obj.get('완료목표일', _완료요청일_str)
            if _완료요청일_str:
                완료요청일 = datetime.fromisoformat(_완료요청일_str).date()
            else:
                return bar_layout.get(bar_type, {}).get('z_index', 0)
            if _완료목표일_str:
                완료목표일 = datetime.fromisoformat(_완료목표일_str).date()
            else:
                return bar_layout.get(bar_type, {}).get('z_index', 0)
            
            match bar_type:
                case '완료요청일':
                    if 완료요청일 >= 완료목표일:
                        return 10
                    else:
                        return 15
                case '완료목표일':
                    if 완료요청일 >= 완료목표일:
                        return 15
                    else:
                        return 10
                case '실적BAR':
                    return 20
                case '지연BAR':
                    return 21

    
    def _role_decoration(self, row: int, col: int, **kwargs) -> QPixmap:
        task = self._data[row]
        bar_type = kwargs.get('bar_type', 'default')
        if bar_type == '완료요청일' or bar_type == '완료목표일':
            return None
        col_date = self.body_headers[col - len(self.label_headers)]
        if self.check_activity_in_date(task['id'], col_date):
            return resources.get_pixmap( PIXMAP_ACTIVITY)
        
    def on_api_datas_received(self, api_datas:list[dict]):
        self.make_claimID_to_activity_dict(api_datas)
        self._data = api_datas
        self.api_datas = api_datas
        self.original_datas = copy.deepcopy(api_datas)
        self._generate_map_col_to_shape_dict()
        # super().on_api_datas_received(api_datas)

    def make_claimID_to_activity_dict(self, api_datas:list[dict]) -> dict:
        self._claimID_to_activity_set:dict[int, list[dict]] = {}
        self._claimID_to_activity_활동일 :dict[int, list[date]] = {} ### 활동일은 drf에서 datetime field임.
        for obj in copy.deepcopy(api_datas):
            activity_set = obj.get('activity_set', [])
            self._claimID_to_activity_set[obj['id']] = activity_set
            self._claimID_to_activity_활동일[obj['id']] = [datetime.fromisoformat(activity['활동일']).date() for activity in activity_set]


    def check_activity_in_date(self, claimID:int, col_date:date) -> bool:
        return col_date in self._claimID_to_activity_활동일[claimID]
    
    def get_body_data(self, index:QModelIndex, bar_type:str='plan') -> dict|None:
        """ body 데이터 반환 : 상속받은 곳에서 사용함 """
        print(f"get_body_data: {index} : {bar_type}")
        if bar_type in ['실적BAR', '지연BAR']:
            dataObj = self._data[index.row()]
            col_date = self.body_headers[index.column() - len(self.label_headers)]
            _activity_set = dataObj.get('activity_set', [])
            result = [ obj for obj in _activity_set 
                      if datetime.fromisoformat(obj['활동일']).date() == col_date ]
            return result
        return []


class CS_GanttScene(Base_GanttScene):

    def _create_header_item(self, rect, col):
        return CS_Gantt_HeaderCellItem(rect, self.model, col)

    def _create_label_cell(self, rect, index):
        return CS_Gantt_LabelCellItem(rect, self.model, index)


    def _create_bar_cell(self, rect, index, bar_type:str="default", z_index:int|float=0):
        return CS_Gantt_BodyCellItem(rect, self.model, index, bar_type=bar_type, z_index=z_index)


class CS_GanttView(Base_GanttView):
    pass

class CS_GanttMainWidget(Base_GanttMainWidget):

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.select_container = self._create_select_container()
        self.main_layout.addWidget(self.select_container)

        self.view = self._create_main_widget()

        self.main_layout.addWidget(self.view)
        self.setLayout(self.main_layout)
        self._init_flag = True

    def _create_select_container(self) -> QWidget:
        self.select_container = QWidget()
        layout = QHBoxLayout(self.select_container)
        lb = QLabel("조회기준 : ")
        layout.addWidget(lb)

        self.ref_cb = QComboBox()
        self.ref_cb.addItems(["등록일", "접수일", "완료요청일", "완료목표일"])
        self.ref_cb.setCurrentText("등록일")
        layout.addWidget(self.ref_cb)
        layout.addSpacing(16)

        self.year_cb = QComboBox()
        self.month_cb = QComboBox()
        now = datetime.now()
        self.default_year = now.year
        self.default_month = now.month

        YEAR_LIST =  [ year for year in range ( 2025, datetime.now().year + 1)]
        MONTH_LIST = [ month for month in range(1, 13)]
        self.year_cb.addItems([str(y) for y in YEAR_LIST])
        self.month_cb.addItems([f"{m:02}" for m in MONTH_LIST])         
        self.year_cb.setCurrentText(str(self.default_year))
        self.month_cb.setCurrentText( f"{self.default_month:02}" )

        self.ref_cb.currentIndexChanged.connect(self.on_filter_changed)
        self.year_cb.currentIndexChanged.connect(self.on_filter_changed)
        self.month_cb.currentIndexChanged.connect(self.on_filter_changed)
        #### 초기값 실행
        # 🔥 emit 지연 실행
        QTimer.singleShot(0, self.on_filter_changed)

        layout.addWidget(QLabel("년"))
        layout.addWidget(self.year_cb)
        layout.addWidget(QLabel("월"))
        layout.addWidget(self.month_cb)
        layout.addStretch()

        # 🔍 확대/축소/리셋 버튼 추가
        self.zoom_lb_title = QLabel("확대축소 비율(50%~150%) : 현재 ")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("background-color: lightyellow;font-weight: bold; margin: 0px 10px;")
        self.zoom_in_btn = QPushButton("확대 +")
        self.zoom_out_btn = QPushButton("축소 -")
        self.zoom_reset_btn = QPushButton("Reset")
        ### lazy로 추가: 초기화가 순서가 btn 이 먼저고, 혹 view가 변경되어도 ok.
        self.zoom_in_btn.clicked.connect( lambda: self.view.zoom_in() )
        self.zoom_out_btn.clicked.connect( lambda: self.view.zoom_out() )
        self.zoom_reset_btn.clicked.connect( lambda: self.view.reset_zoom() )

        layout.addWidget(self.zoom_lb_title)
        layout.addWidget(self.zoom_label)
        layout.addWidget(self.zoom_in_btn)
        layout.addWidget(self.zoom_out_btn)
        layout.addWidget(self.zoom_reset_btn)


        self.pb_legend_dialog = QPushButton("색상 범례")
        self.pb_legend_dialog.clicked.connect(self.show_legend_dialog)
        layout.addWidget(self.pb_legend_dialog)

        self.select_container.setLayout(layout)
        return self.select_container
    
    def show_legend_dialog(self):
        if getattr(self, 'legend_dialog', None) is None:
            self.legend_dialog = GanttBackgroundLegendDialog(self)
        
        self.legend_dialog.show()  # 또는 exec(), 목적에 따라 선택

    def on_filter_changed(self):
        logger.critical(f"on_filter_changed: {self._init_flag}, {len(self.api_datas)}")
        if not self.api_datas : #or not self._init_flag:
            return
        self.apply_date_filter(self._get_cb_year(), self._get_cb_month(), self._get_cb_ref())

    def _get_cb_year(self) -> int:
        return int(self.year_cb.currentText())

    def _get_cb_month(self) -> int:
        return int(self.month_cb.currentText())
    
    def _get_cb_ref(self) -> str:
        return self.ref_cb.currentText()

    def apply_date_filter(self, year:Optional[int] = None, month:Optional[int] = None, ref:Optional[str] = None) -> list[dict]:
        def check_date( _datetime:datetime.datetime, year:int, month:int) -> bool:
            return _datetime.year == year and _datetime.month == month

        filtered_data = [item for item in self.api_datas 
                         if check_date(Utils.get_datetime_from_datetimestr(item.get(ref, datetime.now())), year, month)]
        logger.critical(f"filtered_data: {filtered_data}")
        self.model.set_body_start_date(datetime(year, month, 1).date())
        self.model.set_body_end_date(datetime(year, month, monthrange(year, month)[1]).date())
        self.model.on_api_datas_received(filtered_data)
        self.model.layoutChanged.emit()
        return filtered_data
    
    def _create_main_widget(self) -> QGraphicsView:
        self.model = self.setup_model()
        self.scene = CS_GanttScene(self.model)
        self.view = CS_GanttView(self.scene)

        self.view.zoomChanged.connect(lambda scale: self.zoom_label.setText(f"{int(scale * 100)}%"))

        # 초기값 수동 emit (optional)
        QTimer.singleShot(0, lambda: self.view.zoomChanged.emit(self.view._current_scale))
        return self.view
    
    def setup_model(self) -> CS_Gantt_Model:
        self.model = CS_Gantt_Model(self)
        self.model.set_label_headers(self._create_label_headers())
        body_config  = self._create_body_config()
        self.model.set_body_start_date(body_config['start_date'])
        self.model.set_body_end_date(body_config['end_date'])
        self.model.set_step_reference(body_config['step_reference'])
        self.model.set_shape_config(self._get_shape_config())
        return self.model
    
    def _create_label_headers(self):
        return ["현장명", "현장주소","Elevator사","부적합유형","진행현황","등록일","완료요청일"]
    
    def _create_body_config(self):
        return {
            'start_date' : datetime(2025, 7, 1).date(),
            'end_date' : datetime(2025, 7, 31).date(),
            'step_reference' : 'day',
        }
    
    def _get_shape_config(self):
        return super()._get_shape_config()


    # def setup_model(self) -> CS_Gantt_Model:
    #     self.model = CS_Gantt_Model(self)
    #     self.model.set_label_headers(["현장명", "현장주소","Elevator사","부적합유형","등록일","완료요청일"])
    #     self.model.set_body_start_date(datetime(2025, 7, 1).date())
    #     self.model.set_body_end_date(datetime(2025, 7, 31).date())
    #     self.model.set_step_reference('day')
    #     self.model.set_shape_config(self.shape_config)
    #     return self.model


    def on_data_changed(self, api_datas:list[dict]):
        self.api_datas = copy.deepcopy(api_datas) or self.api_datas
        self.filtered_data = self.apply_date_filter( self._get_cb_year(), self._get_cb_month(), self._get_cb_ref())
        self.model.on_api_datas_received(self.filtered_data)
        self.model.layoutChanged.emit()
        # self.on_filter_changed()
        # filtered_data = self.apply_date_filter(year, month)
        # self.model.on_api_datas_received(self.api_datas)
        # self.model.layoutChanged.emit()


    def on_body_menu_action(self, key:str, data:dict|any|None):
        print(f"CS_GanttMainWidget: on_body_menu_action: {key} : {data}")

        match key:
            case "Activity 보기":
                if Utils.is_valid_method(self._lazy_source_widget, 'on_activity_view_by_cell_menu') and data:
                    self._lazy_source_widget.on_activity_view_by_cell_menu(data)
                else:
                    print(f"!!!!  on_body_menu_action: unknown method: self._lazy_source_widget.on_activity_view_by_cell_menu")
            case _:
                print(f"!!!! Unknown Key : CS_GanttMainWidget: on_body_menu_action: {key}")
