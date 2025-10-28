from modules.common_import_v2 import *
from modules.PyQt.compoent_v2.table_v2.Base_Table_Model_Role_Mixin import Base_Table_Model_Role_Mixin
from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2

from functools import partial
from calendar import monthrange
from collections import defaultdict

DEFAULT_SHAPE_CONFIG = {
            'start_y' : 10,
            'start_x' : 10,
            'row_height' : 50,
            'header_height' : 50,
            'menu_header': '현장명',
            'header' : {

            },
            'bar_layout' : {
                "완료요청일":     { "offset": 5,  "height": 20, "z_index": 10 },
                "완료목표일":     { "offset": 5,  "height": 20, "z_index": 11},
                "실적BAR":   { "offset": 15,  "height": 30, "z_index": 20 },  
                "지연BAR":   { "offset": 15,  "height": 30, "z_index": 21 },  # plan보다 약간 위에 겹쳐짐
                # "baseline": { "offset": 28, "height": 4,  "z_index": 0 },  # 맨 아래

            },
            "header_config" : {
                "default" : {
                    "brush_color" : QColor("#000000"),
                    "pen_color" : Qt.GlobalColor.white,
                    "font" : QFont("Arial", 12),
                    "bold" : True,
                },
            },
            "header_config" : {
                "default" : {
                    "brush_color" : QColor("#000000"),
                    "pen_color" : Qt.GlobalColor.white,
                    "font" :  {
                        'label' : QFont("Arial", 12),
                        'body' : QFont("Arial", 9),
                    },
                    "bold" : True,
                },
            },
            'bar_cell_width' : 50,
            "label_cell_config" : {
                "default" : {
                    "brush_color" : QColor("#FFFFE0"),
                    "pen_color" : Qt.GlobalColor.black,
                    "font" : QFont("Arial", 10),
                    "bold" : True,
                },
            }
        }

class Base_GanttModel(Base_Table_Model):
    """ shape_config : {
            'start_y' : 10,
            'start_x' : 10,
            'row_height' : 50,
            'header_height' : 50,
            'header' : {

            },
            'bar_layout' : {
                "plan":     { "offset": 5,  "height": 15, "z_index": 1 },
                "actual":   { "offset": 10,  "height": 30, "z_index": 2 },  # plan보다 약간 위에 겹쳐짐
                # "baseline": { "offset": 28, "height": 4,  "z_index": 0 },  # 맨 아래

            },
            "bar_cell_width" : 50,
            "label_cell_config" : {
                "default" : {
                    "brush_color" : Qt.GlobalColor.lightyellow,
                    "pen_color" : Qt.GlobalColor.black,
                    "font" : QFont("Arial", 16),
                    "bold" : True,
                },

            }
        }"""

# class Base_GanttModel(QAbstractTableModel,Base_Table_Model_Role_Mixin):
    def __init__(self, 
                 parent:QWidget|None=None,
                 api_datas:list[dict] = [], 
                 label_headers:list[str] = [], 
                 body_start:datetime|date = date.today(),  ##[datetime,date, time] 중 하나
                 body_end:datetime|date = date.today(),    ##[datetime,date, time] 중 하나
                 step_reference:str = 'day', #### 'hour', 'month', 'year' 등으로 확충
                 step:int = 1,
                 shape_config:dict = {},
                 **kwargs
                 ):
        super().__init__(parent)
        self._headers_storage = []  # 내부 저장소
        self.shape_config = self.set_shape_config(shape_config)
        self.map_col_to_width: dict[int, int] = {}
        self.step_reference = step_reference
        self.step = step
        self.label_headers = label_headers  # ex: ['현장명']
        self.body_start = body_start
        self.body_end = body_end
        self.kwargs = kwargs
        self.api_datas = api_datas
        self._data:list[dict] = api_datas
        self.original_datas = copy.deepcopy(api_datas)

        self.font_metrics = QFontMetrics(QFont())  # scene에서 쓰는 폰트 기준
        # self.body_headers = self._generate_date_headers(body_start_date, body_end_date)
        # self._headers = self.label_headers + self.body_headers

        # ✅ scene rect관련 변수
        self._label_widths: dict[int, int] = {}
        self._map_header_col_to_rect: dict[int, QRectF] = {}
        self._map_body_label_row_col_to_rect: dict[int, dict[int, QRectF]] = defaultdict(lambda: defaultdict(dict))
        self._map_body_bar_row_col_to_rect: dict[int, dict[int, dict[str, QRectF]]] = defaultdict(lambda: defaultdict(dict))
        self._map_body_background_row_col_to_rect: dict[int, dict[int, QRectF]] = defaultdict(lambda: defaultdict(dict))

        if self.api_datas:
            self.on_api_datas_received(self.api_datas)
    
    @property
    def body_headers(self):        
        return self._generate_date_headers()

    @property
    def _headers(self):
        return self.label_headers + self.body_headers
    
    @_headers.setter
    def _headers(self, value):
        self._headers_storage = value

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    #### getters
    def get_label_headers(self) -> list[str]:
        return self.label_headers

    ##### setters
    def set_shape_config(self, shape_config:dict):
        self.shape_config = shape_config

    def set_label_headers(self, label_headers:list[str]):
        self.label_headers = label_headers

    def set_body_start_date(self, body_start_date:datetime|date):
        self.body_start = body_start_date

    def set_body_end_date(self, body_end_date:datetime|date):
        self.body_end = body_end_date

    def set_step(self, step:int):
        self.step = step

    def set_step_reference(self, step_reference:str):
        if step_reference in ['day', 'hour', 'month', 'year']:
            self.step_reference = step_reference
        else:
            raise ValueError(f"Invalid step_reference: {step_reference}")
    
    ### ✅ 컬럼 너비 설정 : GanttHeaderItem 에서 mouseReleaseEvent 에서 호출
    def set_map_col_to_width(self, col: int, width: int):
        self.map_col_to_width[col] = width
        #### ✅ 헤더 너비 재생성
        self._generate_map_header_rect()
        self._generate_map_body_rect()
        self.layoutChanged.emit()

    def _generate_date_headers(self):
        """ ✅ 25-7-24: 추가적인 보완 필요 """
        start = self.body_start
        end = self.body_end
        step = self.step
        #### date 기준만 ==> 현재 적용
        if self.step_reference == 'day':
            if isinstance(start, date) and isinstance(end, date):
                days_range = (end - start).days + 1
                return [start + timedelta(days=i) for i in range(0, days_range, step)]
            elif isinstance(start, datetime) and isinstance(end, datetime):
                _start = start.date()
                _end = end.date()
                days_range = (_end - _start).days + 1
                return [_start + timedelta(days=i) for i in range(days_range, step)]

        #### datetime에서 시간 기준만
        elif isinstance(start, datetime) and isinstance(end, datetime):
            time_range = int(( (end - start).total_seconds() + 1)/3600 )
            return [start + timedelta(hours=i) for i in range(time_range, step)]
        else:
            return []

    			
    def data(self, index:QModelIndex, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole, **kwargs):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._data) or col < 0 or col >= len(self._headers):
            return None
        
        if role == Qt.ItemDataRole.UserRole:
            return self._data[row]
        
        return self.role_data(row, col, role, **kwargs)



    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        _role = Qt.ItemDataRole
        if role == _role.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.label_headers):
                    return self.label_headers[section]
                else:
                    _date = self.body_headers[section - len(self.label_headers)]
                    return Utils.format_date_str_with_weekday(_date.isoformat(), with_weekday=True, is_weekday_newLine=True)
            else:
                return self._data[section].get("현장명", "")
            
        if role == _role.EditRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.label_headers):
                    return self.label_headers[section]
                else:
                    _date = self.body_headers[section - len(self.label_headers)]
                    return _date

        

    def on_api_datas_received(self, api_datas:list[dict]):        
        self._data = api_datas
        self.original_datas = copy.deepcopy(api_datas)
        self.api_datas = api_datas
        # super().on_api_datas_received(api_datas)
        self._generate_map_col_to_shape_dict()


    def _generate_map_col_to_shape_dict(self):
        """ header, body 영역의 rect 생성 
            self._map_header_col_to_rect: dict[int, QRectF]
            self._map_body_row_col_to_rect: dict[int, dict[int, dict[str, QRectF]]]
        """
        self._generate_map_col_to_width() # 🔧 self._label_widths[i] 생성
        self._generate_map_header_rect()
        self._generate_map_body_rect()

    def _generate_map_header_rect(self):
        y = self._get_start_y()        
        x = self._get_start_x()
        header_height = self._get_header_height()        
        for col in range(self.columnCount()):
            width = self.get_width(col)
            rect = QRectF(x, y, width, header_height)
            self._map_header_col_to_rect[col] = rect
            x += width

    def _get_start_y(self):
        return self.shape_config.get('start_y', 10)
    
    def _get_start_x(self):
        return self.shape_config.get('start_x', 10)
    
    def _get_row_height(self, row:int=0):
        """ row 에 해당하는 높이 반환 """
        return self.shape_config.get('row_height', 50)
    
    def _get_header_height(self):
        return self.shape_config.get('header_height', 50)
    
    def _get_header_body_spacing(self):
        return self.shape_config.get('header_body_spacing', 5)
    
    def _get_body_cell_width(self):
        return self.shape_config.get('body_cell_width', 50)
    
    def _get_body_start_y(self):
        return self._get_start_y() + self._get_header_height() + self._get_header_body_spacing()
    
    def _get_bar_types(self) -> tuple[bool, list[str]]:
        """ bar_layout 에 있는 모든 타입을 반환 , True, _types 반환 , False, [] 반환 """
        bar_layout = self.shape_config.get('bar_layout', {})
        _types = list(bar_layout.keys())
        return (True, _types) if _types else (False, [])
    
    def _get_bar_y_offset_height(self, bar_type:str) -> tuple[int, int]:
        (_ok, _types) = self._get_bar_types()
        if _ok:
            bar_layout = self.shape_config.get('bar_layout', {})
            offset = bar_layout.get(bar_type, {}).get('offset', 0)
            height = bar_layout.get(bar_type, {}).get('height', 0)
            return ( offset, height )
        else:
            return ( 0, self._get_row_height() )
        
    def _generate_map_body_rect(self):
        y = self._get_body_start_y()
        for row in range(self.rowCount()):
            x = self._get_start_x()
            for col in range(self.columnCount()):
                width = self.get_width(col)
                if self._is_label_header(col):
                    self._map_body_label_row_col_to_rect[row][col] = QRectF(x, y, width, self._get_row_height(row))
                else:
                    isok, bar_types = self._get_bar_types()
                    if isok:
                        for bar_type in bar_types:
                            (offset, height) = self._get_bar_y_offset_height(bar_type)
                            rect = QRectF(x, y + offset, width, height)
                            self._map_body_bar_row_col_to_rect[row][col][bar_type] = rect
                    else:
                        rect = QRectF(x, y, width, self._get_row_height())
                        self._map_body_bar_row_col_to_rect[row][col]['default'] = rect
                x += width  
            y += self._get_row_height()

        #### 25-8-1 배경 셀 생성
        y = self._get_body_start_y()
        for row in range(self.rowCount()):
            x = self._get_start_x()
            for col in range(self.columnCount()):
                width = self.get_width(col)
                rect = QRectF(x, y, width, self._get_row_height())
                self._map_body_background_row_col_to_rect[row][col] = rect
                x += width
            y += self._get_row_height()

    def _is_label_header(self, col:int) -> bool:
        return col < len(self.label_headers)
    
    def _is_menu_header(self, col:int) -> bool:
        menu_header = self.shape_config.get('menu_header', '')
        return col == self.label_headers.index(menu_header)


    def _is_label_column(self, col:int) -> bool:
        return col < len(self.label_headers)
    
    def _is_body_column(self, col:int) -> bool:
        return col >= len(self.label_headers)

    def get_width(self, col:int) -> int:
        """ col 에 해당하는 너비 반환 """
        return self.map_col_to_width.get(col, self._get_body_cell_width(col))
    
    def _generate_map_col_to_width(self):
        self.map_col_to_width.clear()
        #### ✅ 전제가 왼쪽에 label , 오른쪽 body 에 date등 일정에 해당함. 
        #### ✅ 왼쪽 label 너비는 동적, 오른쪽 body 너비는 고정 :self.shape_config.get('body_cell_width', 50)        
        for col in range(self.columnCount()):
            if self._is_label_header(col):
                self.map_col_to_width[col] = self._get_label_widths(col)
            else:
                self.map_col_to_width[col] = self._get_body_cell_width(col)

        print('map_col_to_width: ', self.map_col_to_width)

    def _get_label_widths(self, col:int) -> int:
        key = self.get_label_headers()[col]
        font_config = self.get_labelCell_config_by_col(col)

        font = font_config.get("font", QFont("Arial", 10))
        if font_config.get("bold", False):
            font.setBold(True)

        metrics = QFontMetrics(font)
        max_val = max((str(d.get(key, "")) for d in self._data), key=len, default="")
        candidate = max([key, max_val], key=len)
        width = metrics.horizontalAdvance(candidate) + 20  # padding 포함
        return width
    
    def _get_body_cell_width(self, col:int) -> int:
        return self.shape_config.get('body_cell_width', 50)
    
   

    ##  ✅ SCENE rect관련  반환 메서드
    def get_header_rect(self, col:int=0) -> QRectF:
        return self._map_header_col_to_rect.get(col, QRectF(10, 10, 10, 10))
    
    def get_body_bar_rect(self, row:int=0, col:int=0, bar_type:str='plan') -> QRectF:
        if bar_type == 'background':
            return self._map_body_background_row_col_to_rect.get(row, {}).get(col, {}) #.get(bar_type, QRectF(10, 10, 10, 10))
        return self._map_body_bar_row_col_to_rect.get(row, {}).get(col, {}).get(bar_type, QRectF(10, 10, 10, 10))

    def get_body_label_rect(self, row:int=0, col:int=0) -> QRectF:
        return self._map_body_label_row_col_to_rect.get(row, {}).get(col, QRectF(10, 10, 10, 10))

    def get_bar_z_index(self, bar_type:str) -> int:
        if bar_type == 'background':
            return -1
        bar_layout = self.shape_config.get('bar_layout', {})
        return bar_layout.get(bar_type, {}).get('z_index', 0)

    def get_labelCell_config(self, index:QModelIndex) -> dict:
        row, col = index.row(), index.column()
        return  self.get_labelCell_config_by_col(col)


    def get_labelCell_config_by_col(self, col:int) -> dict:
        config = self.shape_config.get('label_cell_config', {}).get(col, {})
        if config:
            return config
        else:
            return self.shape_config.get('label_cell_config', {}).get('default', {})
        
    def get_header_config(self, col:int) -> dict:
        config = self.shape_config.get('header_config', {}).get(col, {})
        if config:
            return config
        else:
            return self.shape_config.get('header_config', {}).get('default', {})
        
    def get_body_data(self, index:QModelIndex, bar_type:str='plan') -> dict|None:
        """ body 데이터 반환 : 상속받은 곳에서 사용함 """
        return None
        
class GanttLabelCellItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model, index: QModelIndex, **kwargs):
        super().__init__(rect)
        self.kwargs = kwargs
        self.model = model
        self.index = index
        self.text = model.data(index, Qt.ItemDataRole.DisplayRole) or ""
        self.config = self.model.get_labelCell_config(index)
        self._apply_config()

        self.is_menu_header = self.model._is_menu_header(index.column())
        self.site_data:None|dict = None
        self.main_wid:QWidget|None = None
        self.map_actions:dict[str, QAction] = {}

        if self.is_menu_header:
            self.setAcceptHoverEvents(True)
            self.setFlag(QGraphicsItem.ItemIsSelectable)
            self.setFlag(QGraphicsItem.ItemIsFocusable)
            self.site_data = self.model._data[self.index.row()]

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def _apply_config(self):
        self.setBrush(QBrush(self.config.get('brush_color', Qt.GlobalColor.darkCyan)))
        self.setPen(QPen(self.config.get('pen_color', Qt.GlobalColor.red)))
        #### 폰트 적용
        self._font = QFont(self.config.get('font', QFont("Arial", 16)))
        self._font.setBold(self.config.get('bold', False))


    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        new_config = self.model.get_labelCell_config(self.index)
        if new_config != self.config:
            self.config = new_config
            self._apply_config()

        painter.setFont(self._font)  # ← 여기서 폰트 적용
        painter.drawText(self.rect().adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter, self.text)

    def refresh(self):
        self.site_data = self.model._data[self.index.row()]
        self.update()  # 자체 update()로 paint 재실행

    def _get_background_color(self):
        bg = self.model.data(self.index, Qt.ItemDataRole.BackgroundRole)
        return bg if isinstance(bg, QBrush) else QBrush(Qt.GlobalColor.white)
    
    def _show_contextMenu(self, global_pos: QPointF ):
        if not isinstance(self.get_main_wid(), Base_GanttMainWidget):
            if INFO.IS_DEV:
                Utils.generate_QMsg_critical(
                    None, 
                    title="Fail: contextMenuEvent", 
                    text= f"{self.__class__.__name__} : contextMenuEvent<br> self.get_main_wid() is not GanttMainWidget")
            return
        try:
            
            self.menus_dict:dict = self.get_main_wid().Table_Menus
            if not self.menus_dict:
                raise ValueError(f"{self.__class__.__name__} : contextMenuEvent<br> menus is None")
        except Exception as e:
            if INFO.IS_DEV:
                Utils.generate_QMsg_critical(
                    None, 
                    title="Fail: contextMenuEvent", 
                    text= f"{self.__class__.__name__} : contextMenuEvent<br> self.get_main_wid().create_pb_info is not callable")
            return
        
        menu = QMenu()

        for key, info in self.menus_dict.items():
            action:QAction = menu.addAction(info['title'])
            action.setToolTip(info['tooltip'])
            action.triggered.connect(partial(self.get_main_wid().on_site_menu_action, key, self.site_data))
            # action.triggered.connect( lambda checked, key=key : self.get_main_wid().on_site_menu_action(key, self.site_data) )
            action.setEnabled(self.check_menu_enable( action,key, info))
            self.map_actions[key] = action
        
        action = menu.exec(global_pos)  # 글로벌 좌표 필요 또는 QCursor.pos()

        # context 메뉴 이후 선택 해제 및 스타일 복원

        self.setSelected(False)
        self.update_style(_type="normal")

    def check_menu_enable(self, action:QAction, key:str, info:dict) -> bool:
        """ 메뉴 활성화 여부 체크 """
        print(f"check_menu_enable: {key} : self.site_data: {self.site_data}")
        진행현황 = self.site_data.get('진행현황')
        claim_files_url = self.site_data.get('claim_files_url', [])
        activty_files_url = self.site_data.get('activity_files_url', [])
        print(f"check_menu_enable: {key} : claim_files_url: {claim_files_url} : activty_files_url: {activty_files_url}")
        print(f"check_menu_enable: {key} : bool(claim_files_url): {bool(claim_files_url)} : bool(activty_files_url): {bool(activty_files_url)}")
        match key:
            case 'Claim 수정 보기':
                if 진행현황 == '완료' or 진행현황 == '반려':
                    action.setText( 'Claim 보기' )
                else:
                    action.setText( 'Claim 수정' )
                return True
                return 진행현황 == 'Open' or 진행현황 == '작성'
            case '클레임 접수'|'Claim 접수':
                return 진행현황 == '의뢰'
            case 'Action 등록':
                return 진행현황 == '접수'
            case 'Claim 파일다운로드':
                return bool(claim_files_url)
            case 'Claim 파일보기':
                return bool(claim_files_url)
            case 'Action 파일다운로드':
                return bool(activty_files_url)
            case 'Action 파일보기':
                return bool(activty_files_url)
            case '지도보기':
                return bool(self.site_data.get('현장주소', ''))
            case 'Excel 내보내기':
                return True
            case 'Excel 내보내기(관리자)':
                return True
            case '클레임 닫기(완료)':
                return 진행현황 == '접수'
            case '클레임 열기':
                return 진행현황 == '작성'
            case _:
                return True
            
    def get_main_wid(self) -> QWidget|None:
        if self.main_wid:
            return self.main_wid

        scene = self.scene()
        view = scene.views()[0] if scene and scene.views() else None
        if view:
            if isinstance(view.parent(), Base_GanttMainWidget):
                self.main_wid = view.parent()
                return self.main_wid
            else:
                raise ValueError(f"GanttMainWidget가 아닙니다. : {view.parent()}")
        else:
            raise ValueError(f"Scene이 없습니다. : {scene}")

    def update_style(self, _type: str = "normal"):
        return 
        match _type:
            case "normal":
                self.setBrush(QBrush(self.normal_bg_color))
                self.text_item.setBrush(QBrush(self.normal_color))
            case "hover":
                self.setBrush(QBrush(self.hover_bg_color))  # 배경은 그대로, 글자만 강조
                self.text_item.setBrush(QBrush(self.hover_color))
            case "selected":
                self.setBrush(QBrush(self.selected_bg_color))
                self.text_item.setBrush(QBrush(self.selected_color))
            case _:
                # fallback or log
                pass

    def mousePressEvent(self, event):
        self.setSelected(True)
        self.update_style(_type="selected")
        if event.button() == Qt.MouseButton.RightButton:
            if self.is_enable_context_menu():
                self._show_contextMenu(event.screenPos())  # or event.scenePos()
                return 
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        self.update_style(_type="hover")
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update_style(_type="normal")
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def is_enable_context_menu(self) -> bool:
        return True


class GanttBodyCellItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model:Base_GanttModel, index: QModelIndex, z_index:int=0, bar_type:str='default', **kwargs):        
        super().__init__(rect)
        self.kwargs = kwargs
        self.model = model
        self.index = index
        self.z_index = self.model.get_bar_z_index(bar_type, index)
        self.bar_type = bar_type
        self.display_role = self._get_display_role()
        self.decoration_role = self._get_decoration_role()
        self.background_role = self._get_background_role()
        self.is_hoverable = self.is_data_exist()

        self.setAcceptHoverEvents(self.is_hoverable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.setZValue(z_index)  # ✅ z-index 적용

        self._brush = self._get_background_role()
        self._pen = QPen(Qt.PenStyle.NoPen)
        self.setPen(self._pen)
        self.setBrush(self._brush)

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

        self.main_wid = None

    def get_main_wid(self) -> QWidget|None:
        if self.main_wid and isinstance(self.main_wid, Base_GanttMainWidget):
            return self.main_wid

        scene = self.scene()
        view = scene.views()[0] if scene and scene.views() else None
        if view:
            if isinstance(view.parent(), Base_GanttMainWidget):
                self.main_wid = view.parent()
                return self.main_wid
            else:
                raise ValueError(f"GanttMainWidget가 아닙니다. : {view.parent()}")
        else:
            raise ValueError(f"Scene이 없습니다. : {scene}")

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#d0f0ff")))

    def hoverLeaveEvent(self, event):
        self.setBrush(self._brush)

    def is_data_exist(self) -> bool:
        """ decoration_role 또는 display_role 중 하나라도 존재하면 True """
        return bool(self._get_decoration_role() )

    def contextMenuEvent(self, event):
        """ 가능한 상속받은데서 override 해서 사용할 것 """
        if not self.is_data_exist():
            return
        menu = QMenu()
        key = "작업 세부 정보 보기"
        action = menu.addAction(key)
        action.triggered.connect(partial(self.get_main_wid().on_body_menu_action, key, self.get_data()))
        menu.exec(event.screenPos())

    def get_data(self) -> dict|None:
        self._data = self.model.get_body_data(self.index, self.bar_type)
        return self._data

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        # 데코레이션 그리기
        docoration_role = self._get_decoration_role()
        if docoration_role and isinstance(docoration_role, QPixmap):
            icon_height = int(self.rect().height() /2 )
            icon = docoration_role.scaled(icon_height, icon_height)
            center = self.rect().center()
            offset = QPointF(8, 8)
            painter.drawPixmap(center - offset, icon)

        # 값 그리기
        display_role = self._get_display_role()
        if display_role:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(display_role))
        
        if self._brush != self._get_background_role():
            self._brush = self._get_background_role()
            self.setBrush(self._brush)

        if self.z_index and isinstance(self.z_index, (int, float)):
            self.setZValue(self.z_index)
    
    def _get_display_role(self):
        return self.model.data(self.index, Qt.ItemDataRole.DisplayRole, bar_type=self.bar_type)
    
    def _get_decoration_role(self) -> QPixmap|None:
        return self.model.data(self.index, Qt.ItemDataRole.DecorationRole, bar_type=self.bar_type)
    
    def _get_background_role(self) -> QBrush|None:
        return self.model.data(self.index, Qt.ItemDataRole.BackgroundRole, bar_type=self.bar_type)

    def refresh(self):
        self.update()  # 자체 update()로 paint 재실행


class GanttBody_BackgroundCellItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, model:Base_GanttModel, index: QModelIndex, z_index:int=-1, bar_type:str='background', **kwargs):        
        super().__init__(rect)
        self.kwargs = kwargs
        self.model = model
        self.index = index
        self.z_index = z_index
        self.bar_type = bar_type
        self.display_role = model.data(index, Qt.ItemDataRole.DisplayRole, bar_type=self.bar_type)
        self.decoration_role = model.data(index, Qt.ItemDataRole.DecorationRole, bar_type=self.bar_type)
        self.background_role = model.data(index, Qt.ItemDataRole.BackgroundRole, bar_type=self.bar_type)
        self.is_hoverable = model._get_hoverable(index, bar_type=self.bar_type)
        self.is_context_menu = self.is_hoverable
        self.setAcceptHoverEvents(self.is_hoverable)
        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.setZValue(z_index)  # ✅ z-index 적용

        self._brush = self._get_background_role()
        self._pen = QPen(Qt.PenStyle.NoPen)
        self.setPen(self._pen)
        self.setBrush(self._brush )

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#d0f0ff")))

    def hoverLeaveEvent(self, event):
        self.setBrush(self._brush)

    def contextMenuEvent(self, event):
        if not self.is_context_menu:
            return
        menu = QMenu()
        action = menu.addAction("작업 세부 정보 보기")
        action.triggered.connect(lambda: print(f"Context clicked: {self.index.data()}"))
        menu.exec(event.screenPos())

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        # 데코레이션 그리기
        docoration_role = self._get_decoration_role()
        if docoration_role and isinstance(docoration_role, QPixmap):
            icon_height = int(self.rect().height() /2 )
            icon = docoration_role.scaled(icon_height, icon_height)
            center = self.rect().center()
            offset = QPointF(8, 8)
            painter.drawPixmap(center - offset, icon)

        # 값 그리기
        display_role = self._get_display_role()
        if display_role:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(display_role))
        
        if self._brush != self._get_background_role():
            self._brush = self._get_background_role()
            self.setBrush(self._brush)

        if self.z_index and isinstance(self.z_index, (int, float)):
            self.setZValue(self.z_index)
    
    def _get_display_role(self):
        return self.model.data(self.index, Qt.ItemDataRole.DisplayRole, bar_type=self.bar_type)
    
    def _get_decoration_role(self) -> QPixmap|None:
        return self.model.data(self.index, Qt.ItemDataRole.DecorationRole, bar_type=self.bar_type)
    
    def _get_background_role(self) -> QBrush|None:
        return self.model.data(self.index, Qt.ItemDataRole.BackgroundRole, bar_type=self.bar_type)

    def refresh(self):
        self.update()  # 자체 update()로 paint 재실행


class GanttHeaderItem(QGraphicsRectItem):
    RESIZE_MARGIN = 5  # 리사이징 감지 여백

    def __init__(self, rect: QRectF, model: Base_GanttModel, colNo: int):
        super().__init__(rect)
        self.model = model
        self.colNo = colNo
        self.setAcceptHoverEvents(True)  # 마우스 hover 감지
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.config = self.model.get_header_config(colNo)
        self._apply_config()

        self._resizing = False
        self._resize_start_x = 0
        self._original_width = 0

        self._data = self._get_original_data()
        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

    def _apply_config(self):
        self.setBrush(QBrush(self.config.get('brush_color', Qt.GlobalColor.darkCyan)))
        self.setPen(QPen(self.config.get('pen_color', Qt.GlobalColor.red)))
        #### 폰트 적용
        font_config = self.config.get('font', {})
        if self.model._is_label_header(self.colNo):
            self._font = font_config.get('label', QFont("Arial", 12))
        else:
            self._font = font_config.get('body', QFont("Arial", 10))
        self._font.setBold(font_config.get('bold', False))

    def _get_original_data(self):
        return self.model.headerData(self.colNo, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole)

    def _get_display_data(self):
        return self.model.headerData(self.colNo, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        super().paint(painter, option, widget)

        new_config = self.model.get_header_config(self.colNo)
        if new_config != self.config:
            self.config = new_config
            self._apply_config()
        painter.setFont(self._font)  # ← 여기서 폰트 적용
        
        text = self._get_display_data()
        if text:
            lines = str(text).split('\n')
            rect = self.rect().adjusted(3, 3, -3, -3)
            line_height = painter.fontMetrics().height()
            total_height = line_height * len(lines)
            start_y = rect.top() + (rect.height() - total_height) / 2

            for i, line in enumerate(lines):
                painter.drawText(
                    int(rect.left()),
                    int(start_y + i * line_height),
                    int(rect.width()),
                    int(line_height),
                    Qt.AlignmentFlag.AlignCenter,
                    line
                )

        

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        # 우측 가장자리에 마우스가 위치하면 커서 변경
        if abs(event.pos().x() - self.rect().right()) < self.RESIZE_MARGIN:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if abs(event.pos().x() - self.rect().right()) < self.RESIZE_MARGIN:
            self._resizing = True
            self._resize_start_x = event.scenePos().x()
            self._original_width = self.rect().width()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._resizing:
            delta = event.scenePos().x() - self._resize_start_x
            new_width = max(30, self._original_width + delta)
            self.prepareGeometryChange()
            self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, self.rect().height())))
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._resizing:
            self._resizing = False
            final_width = self.rect().width()
            if hasattr(self.model, "set_map_col_to_width"):
                self.model.set_map_col_to_width(self.colNo, final_width)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def refresh(self):
        self.update()

class Base_GanttScene(QGraphicsScene):
    def __init__(self, model: Base_GanttModel, cell_height=30, header_height=30, label_width=150, cell_width=80):
        super().__init__()
        self.model = model
        self.header_height = header_height
        self.cell_height = cell_height
        self.label_width = label_width
        self.cell_width = cell_width
        self.map_col_to_x_and_width: dict[int, tuple[float, int]] = {}

        self.model.layoutChanged.connect(self.refresh)
        self.model.dataChanged.connect(self.refresh)

        self.refresh()

    def refresh(self):
        self.clear()
        self._draw()

    def _draw(self):
        self._draw_headers()
        self._draw_body()


    # def _get_map_col_to_x_and_width(self):
    #     x = 0
    #     self.map_col_to_x_and_width = {}
    #     for col in range(self.model.columnCount()):
    #         w = self.model.get_column_width(col)
    #         self.map_col_to_x_and_width[col] = (x, w)
    #         x += w
    #     print(self.map_col_to_x_and_width)

    def _draw_headers(self):        
        for col in range(self.model.columnCount()):
            rect = self.model.get_header_rect(col=col)
            item = self._create_header_item(rect, col)
            self.addItem(item)

    def _draw_body(self):
        for row in range( self.model.rowCount()):
            for col in range(self.model.columnCount()):
                index = self.model.index(row, col)
                if self.model._is_label_header(col):
                    rect = self.model.get_body_label_rect(row=row, col=col)
                    item = self._create_label_cell(rect, index)
                    self.addItem(item)
                else:
                    isok, bar_types = self.model._get_bar_types()
                    if isok:
                        #### 배경 셀 생성
                        rect = self.model.get_body_bar_rect(row=row, col=col, bar_type='background')                                        
                        z_index = self.model.get_bar_z_index('background')                            
                        item = self._create_background_bar_cell(rect, index, bar_type='background', z_index=z_index)
                        self.addItem(item)
                        #### 바 셀 생성
                        for bar_type in bar_types:
                            rect = self.model.get_body_bar_rect(row=row, col=col, bar_type=bar_type)                
                            z_index = self.model.get_bar_z_index(bar_type)                            
                            item = self._create_bar_cell(rect, index, bar_type=bar_type, z_index=z_index)
                            self.addItem(item)
                    else:
                        rect = self.model.get_body_bar_rect(row=row, col=col, bar_type='default')
                        z_index = self.model.get_bar_z_index('default')                        
                        item = self._create_bar_cell(rect, index, bar_type='default', z_index=z_index)
                        self.addItem(item)

    # ✅ 템플릿 메서드: override point
    def _create_header_item(self, rect, col):
        return GanttHeaderItem(rect, self.model, col)

    def _create_label_cell(self, rect, index):
        return GanttLabelCellItem(rect, self.model, index )

    def _create_bar_cell(self, rect, index, bar_type:str="default", z_index:int|float=0):
        return GanttBodyCellItem(rect, self.model, index, bar_type=bar_type, z_index=z_index)
    
    ###### 배경 셀 생성
    def _create_background_bar_cell(self, rect, index, bar_type:str="background", z_index:int|float=-1):
        return GanttBody_BackgroundCellItem(rect, self.model, index, bar_type=bar_type, z_index=z_index)

    

class Base_GanttView(QGraphicsView):
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint( self.renderHints() | QPainter.RenderHint.Antialiasing )
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._zoom_factor = 1.15
        self._min_scale = 0.5
        self._max_scale = 1.6
        self._base_scale = 1.0
        self._current_scale = 1.0

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            scale_factor = self._zoom_factor if angle > 0 else 1 / self._zoom_factor
            self._apply_zoom(scale_factor)
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        self._apply_zoom(self._zoom_factor)

    def zoom_out(self):
        self._apply_zoom(1 / self._zoom_factor)

    def reset_zoom(self):
        self.resetTransform()
        self._current_scale = self._base_scale
        self.zoomChanged.emit(self._current_scale)

    def _apply_zoom(self, factor: float):
        new_scale = self._current_scale * factor
        if self._min_scale <= new_scale <= self._max_scale:
            self.scale(factor, 1.0)
            self._current_scale = new_scale
            self.zoomChanged.emit(self._current_scale)

    def showEvent(self, event):
        super().showEvent(event)
        self.reset_view_to_top_left()

    def reset_view_to_top_left(self):
        # 스크롤바를 강제로 맨 앞(0,0)으로 이동
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)

class Base_GanttMainWidget(QWidget, LazyParentAttrMixin_V2):
    def __init__(self, parent:QWidget|None=None, api_datas:list[dict]=[], **kwargs):
        super().__init__(parent)        
        self.kwargs = kwargs
        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.lazy_attr_names = ['APP_ID']
        self.lazy_ready_flags = {}
        self.lazy_attr_values = {}
        self.lazy_ws_names = []
        self.table_name = None
        self.api_datas = api_datas

        self.shape_config = self._get_shape_config()

        self.run_lazy_attr()
        self._init_flag = False

    def _get_shape_config(self):
        return self.kwargs.get('shape_config', DEFAULT_SHAPE_CONFIG)
    
    def _reset_ui(self, data: list[dict]):
        # 💥 기존 layout 제거
        if self.layout():
            QWidget().setLayout(self.layout())  # 기존 layout 제거용 trick

        self._init_flag = False
        self.setup_ui()
        self.on_data_changed(data or self.api_datas)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.view = self._create_main_widget()
        self.main_layout.addWidget(self.view)
        self.setLayout(self.main_layout)
        self._init_flag = True

    def _create_main_widget(self) -> QGraphicsView:
        NotImplementedError("subclass should implement this method")
        self.model = self.setup_model()
        self.scene = Base_GanttScene(self.model)
        self.view = Base_GanttView(self.scene)
        return self.view
    
    def _create_label_headers(self) -> list[str]:
        NotImplementedError("subclass should implement this method")
        return ["현장명", "현장주소","Elevator사","부적합유형","등록일","완료요청일"]
    
    def _create_body_config(self) -> dict:
        NotImplementedError("subclass should implement this method")
        return {
            'start_date' : datetime(2025, 7, 1).date(),
            'end_date' : datetime(2025, 7, 31).date(),
            'step_reference' : 'day',
        }
    
   
    
    def setup_model(self) -> Base_GanttModel:
        self.model = Base_GanttModel(self)
        self.model.set_label_headers(self._create_label_headers())
        body_config  = self._create_body_config()
        self.model.set_body_start_date(body_config['start_date'])
        self.model.set_body_end_date(body_config['end_date'])
        self.model.set_step_reference(body_config['step_reference'])
        self.model.set_shape_config(self._get_shape_config())
        return self.model

    def api_data_update(self, api_datas:list[dict] = None):        
        self.api_datas = copy.deepcopy(api_datas) or self.api_datas
        self.model.on_api_datas_received(self.api_datas)
        self.model.layoutChanged.emit()

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.APP_ID = APP_ID
            self.app_dict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            self.setup_ui()
            self.subscribe_gbus()

            if hasattr(self, 'api_datas') and self.api_datas:
                self.on_data_changed(self.api_datas)

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")
  

    def subscribe_gbus(self):
        self.event_bus.subscribe(f'{self.table_name}:datas_changed', self.on_data_changed)

    def on_data_changed(self, api_datas: list[dict]):
        try:
            self.api_datas = api_datas or self.api_datas
            self.model.on_api_datas_received(self.api_datas)
            self.model.layoutChanged.emit()
        except Exception as e:
            logger.error(f"on_data_changed 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_data_changed 오류', text=f"{e}<br>{trace}")


    def on_site_menu_action(self, key:str, site_data:dict):
        """ app 내에서 바로 gantt_chart에서 table widget으로 publish 함
            만약, table widget 에서 site_data 변경 시 자동 update 됨 ( site_data가 self.site_data 임 )
        """

        senddata =  {'key':key, 'selected_id':site_data['id']}
        구독자수 = self.event_bus.publish( f"{self.table_name}:gantt_chart_action", senddata )
        

# def run_app(task_data):
#     import sys
#     app = QApplication(sys.argv)
#     window = QMainWindow()
#     window.setWindowTitle("Gantt Chart Example (with Model)")
#     widget = GanttMainWidget(task_data)
#     window.setCentralWidget(widget)
#     window.resize(1200, 600)
#     window.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     task_data = [
#         {'id': 51, '현장명': '삼라마이다스빌', '현장주소': '광주광역시 북구 동운로 141', 'Elevator사': 'TKE',
#          '부적합유형': '스크래치', '등록일': '2025-07-21T17:57:50', '완료요청일': '2025-07-26'},
#         {'id': 37, '현장명': '한울3차아파트(K20240590)', '현장주소': '충청남도 아산시 어의정로183번길 14',
#          'Elevator사': 'TKE', '부적합유형': '스크래치', '등록일': '2025-07-12T17:06:18.231341', '완료요청일': '2025-07-18'},
#         {'id': 34, '현장명': '코오롱동신아파트', '현장주소': '충청북도 충주시 금릉로 14', 'Elevator사': '현대',
#          '부적합유형': '스크래치', '등록일': '2025-07-09T08:21:45.446129', '완료요청일': '2025-07-21'}
#     ]
#     run_app(task_data)

