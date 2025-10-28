from __future__ import annotations
from modules.common_import_v2 import *
from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2

from functools import partial
from calendar import monthrange


CELL_WIDTH = 40
PLAN_ROW_HEIGHT = 15
ACTUAL_ROW_HEIGHT = 30
ROW_SPACING = 10  # 계획과 실적 간격
HEADER_HEIGHT = 40

ROW_HEIGHT = PLAN_ROW_HEIGHT + ACTUAL_ROW_HEIGHT + ROW_SPACING

def create_day_label(date: datetime.date) -> QGraphicsTextItem:
    weekday_kor = ['월', '화', '수', '목', '금', '토', '일']
    label_text = f"{date.day}\n{weekday_kor[date.weekday()]}"

    label = QGraphicsTextItem(label_text)
    font = QFont("Arial", 8)
    label.setFont(font)
    label.setTextWidth(CELL_WIDTH)  # 줄바꿈 기준 너비 설정

    # 텍스트 정렬 (가운데 정렬)
    label.setTextWidth(CELL_WIDTH)
    label.setDefaultTextColor(QColor({
        5: "blue",  # 토요일
        6: "red",   # 일요일
    }.get(date.weekday(), "black")))

    return label

class TodayRectItem(QGraphicsRectItem):
    default_color = QColor(255, 255, 0, 100)
    hover_color = QColor(255, 200, 0, 200)  # 더 강한 노란색
    default_pen = QPen(QColor("gray"), 1)
    hover_pen = QPen(QColor("red"), 2)
    hover_cursor = Qt.CursorShape.CrossCursor

    def __init__(self, rect, item_data:Optional[dict]=None, parent=None):
        super().__init__(rect, parent)
        self.item_data = item_data  # 여기서 저장

        self.setBrush(QBrush(self.default_color))     
        self.setPen(QPen(Qt.PenStyle.SolidLine))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setZValue(999)  # 최상단으로
        self.setBrush(QBrush(self.hover_color))
        self.setPen(self.hover_pen)
        self.setCursor(self.hover_cursor)
        event.accept()

    def hoverLeaveEvent(self, event):
        self.setZValue(0)  # 원래 z-index로 복원
        self.setBrush(QBrush(self.default_color))
        self.setPen(self.default_pen)
        self.unsetCursor()
        event.accept()
        
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        dialog = ActivityDialog(self.item_data)
        dialog.exec()
        event.accept()

class ActivityDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("활동 등록")
        self.setMinimumSize(300, 150)
        layout = QVBoxLayout()

        if item_data:
            현장명 = item_data.get("현장명", "정보없음")
            layout.addWidget(QLabel(f"현장명: {현장명}"))
            # 추가 데이터 표시 가능

        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        self.setLayout(layout)


class SiteEditDialog(QDialog):
    def __init__(self, site_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("현장 정보 수정")
        self.site_data = site_data

        layout = QVBoxLayout(self)
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(site_data["현장명"])
        layout.addWidget(self.name_edit)

        btn_ok = QPushButton("확인", self)
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)


class SiteLabelItem(QGraphicsRectItem):
    def __init__(self, site_data: dict):
        super().__init__()

        self.site_data = site_data
        self.main_wid:Optional[GanttMainWidget] = None
        self.table_name:Optional[str] = None
        self.map_actions:dict[str, QAction] = {}

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

        # 기본 스타일
        self.selected_color = QColor("white")
        self.selected_bg_color = QColor("#0077cc")
        self.normal_color = QColor("black")
        self.normal_bg_color = QColor("white")
        self.hover_color = QColor("black")        ## 검은색
        self.hover_bg_color = QColor("#fff9c4")     # 연한 노란색 (Lemon Chiffon 계열)
        # 내부 텍스트 아이템
        self.text_item = QGraphicsSimpleTextItem(site_data["현장명"], self)
        font = QFont("Arial", 10)
        self.text_item.setFont(font)

        # 아이콘도 원하면 삽입 가능
        # self.icon_item = QGraphicsPixmapItem(QPixmap("icon.png"), self)

        # 기본 스타일 적용
        self.update_style()

        # 배경 크기를 텍스트 기준으로 자동 설정
        padding = 4
        br = self.text_item.boundingRect().adjusted(-padding, -padding, padding, padding)
        self.setRect(br)

    def _show_contextMenu(self, global_pos: QPointF ):
        if not isinstance(self.get_main_wid(), GanttMainWidget):
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

        진행현황 = self.site_data.get('진행현황')
        claim_files_url = self.site_data.get('claim_files_url', [])
        activty_files_url = self.site_data.get('activty_files_url', [])
        match key:
            case 'Claim 수정 보기':
                if 진행현황 == 'Close' or 진행현황 == 'Open':
                    action.setText( 'Claim 보기' )
                else:
                    action.setText( 'Claim 수정' )
                return True
                return 진행현황 == 'Open' or 진행현황 == '작성'
            case 'Action 등록':
                return 진행현황 == 'Open'
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
                return 진행현황 == 'Open'
            case '클레임 열기':
                return 진행현황 == '작성'
            case _:
                return True
            
    def get_main_wid(self) -> GanttMainWidget:
        if self.main_wid:
            return self.main_wid

        scene = self.scene()
        view = scene.views()[0] if scene and scene.views() else None
        if view:
            if isinstance(view.parent(), GanttMainWidget):
                self.main_wid = view.parent()
                return self.main_wid
            else:
                raise ValueError(f"GanttMainWidget가 아닙니다. : {view.parent()}")
        else:
            raise ValueError(f"Scene이 없습니다. : {scene}")

    def update_style(self, _type: str = "normal"):
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


# class SiteLabelItem(QGraphicsTextItem):
#     hover_cursor = Qt.CursorShape.PointingHandCursor
#     hover_color = QColor("#0077cc") ### 파란색 강조
#     selected_bg_color = QColor("#0077cc") ### 파란색 강조
#     selected_color = QColor("white")
#     normal_bg_color = QColor("white")
#     normal_color = QColor("black")

#     def __init__(self, site_data:dict):
#         super().__init__( site_data["현장명"])
#         self.site_data = site_data
#         self.setAcceptHoverEvents(True)  # hover 이벤트 활성화
#         self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)  # 우클릭 포함
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
#         self.default_color = self.defaultTextColor()
#         self.table_name = None

#         self.main_wid = None

#         self.map_actions:dict[str, QAction] = {}

#         self._is_hovered = False
#         self.set_normal_style()

#     def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
#         if not isinstance(self.get_main_wid(), GanttMainWidget):
#             if INFO.IS_DEV:
#                 Utils.generate_QMsg_critical(
#                     None, 
#                     title="Fail: contextMenuEvent", 
#                     text= f"{self.__class__.__name__} : contextMenuEvent<br> self.get_main_wid() is not GanttMainWidget")
#             return
#         try:
            
#             self.menus_dict:dict = self.get_main_wid().Table_Menus
#             if not self.menus_dict:
#                 raise ValueError(f"{self.__class__.__name__} : contextMenuEvent<br> menus is None")
#         except Exception as e:
#             if INFO.IS_DEV:
#                 Utils.generate_QMsg_critical(
#                     None, 
#                     title="Fail: contextMenuEvent", 
#                     text= f"{self.__class__.__name__} : contextMenuEvent<br> self.get_main_wid().create_pb_info is not callable")
#             return
        
#         menu = QMenu()

#         for key, info in self.menus_dict.items():
#             action:QAction = menu.addAction(info['title'])
#             action.setToolTip(info['tooltip'])
#             action.triggered.connect(partial(self.get_main_wid().on_site_menu_action, key, self.site_data))
#             # action.triggered.connect( lambda checked, key=key : self.get_main_wid().on_site_menu_action(key, self.site_data) )
#             action.setEnabled(self.check_menu_enable( action,key, info))
#             self.map_actions[key] = action
        
#         action = menu.exec(event.screenPos())  # 글로벌 좌표 필요

#         # context 메뉴 이후 선택 해제 및 스타일 복원
#         self.setSelected(False)
#         self.set_normal_style()

#     def check_menu_enable(self, action:QAction, key:str, info:dict) -> bool:
#         """ 메뉴 활성화 여부 체크 """

#         진행현황 = self.site_data.get('진행현황')
#         claim_files_url = self.site_data.get('claim_files_url', [])
#         activty_files_url = self.site_data.get('activty_files_url', [])
#         match key:
#             case 'Claim 수정 보기':
#                 if 진행현황 == 'Close' or 진행현황 == 'Open':
#                     action.setText( 'Claim 보기' )
#                 else:
#                     action.setText( 'Claim 수정' )
#                 return True
#                 return 진행현황 == 'Open' or 진행현황 == '작성'
#             case 'Action 등록':
#                 return 진행현황 == 'Open'
#             case 'Claim 파일다운로드':
#                 return bool(claim_files_url)
#             case 'Claim 파일보기':
#                 return bool(claim_files_url)
#             case 'Action 파일다운로드':
#                 return bool(activty_files_url)
#             case 'Action 파일보기':
#                 return bool(activty_files_url)
#             case '지도보기':
#                 return bool(self.site_data.get('현장주소', ''))
#             case 'Excel 내보내기':
#                 return True
#             case 'Excel 내보내기(관리자)':
#                 return True
#             case '클레임 닫기(완료)':
#                 return 진행현황 == 'Open'
#             case '클레임 열기':
#                 return 진행현황 == '작성'
#             case _:
#                 return True

#     def set_normal_style(self):
#         color = self.hover_color if self._is_hovered else self.normal_color
#         self.setHtml(f'<div style="background-color:{self.normal_bg_color}; color:{color}">{self.site_data["현장명"]}</div>')

#     def set_selected_style(self):
#         self.setHtml(f'<div style="background-color:{self.selected_bg_color}; color:{self.selected_color}">{self.site_data["현장명"]}</div>')

#     def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
#         self._is_hovered = True
#         if not self.isSelected():
#             self.set_normal_style()
#         self.setCursor(self.hover_cursor)
#         super().hoverEnterEvent(event)

#     def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
#         self._is_hovered = False
#         if not self.isSelected():
#             self.set_normal_style()
#         self.unsetCursor()
#         super().hoverLeaveEvent(event)

#     def mousePressEvent(self, event):
#         self.setSelected(True)
#         print ( 'mousePressEvent:', self.isSelected())
#         # 🧠 원인 추정
#         # PyQt의 QGraphicsTextItem은 내부적으로 mousePressEvent 후 선택 상태 스타일을 시스템이 다시 적용하면서, 우리가 setHtml()로 준 스타일이 덮어쓰기 되는 경우가 있습니다.
#         # 즉:
#         # self.setHtml(...) 로 스타일 바꿔도
#         # super().mousePressEvent(...) 이후에 PyQt 쪽 internal style 로 롤백됨
#         # self.set_selected_style() 
#         super().mousePressEvent(event)
    
#     def mouseReleaseEvent(self, event):
#         if self.isSelected():
#             print ( 'mouseReleaseEvent:', self.isSelected() , 'set_selected_style')
#             self.set_selected_style()
#         else:
#             print ( 'mouseReleaseEvent:', self.isSelected() , 'set_normal_style')
#             self.set_normal_style()
#         super().mouseReleaseEvent(event)

#     def mouseDoubleClickEvent(self, event):
#         self.get_main_wid().request_open_form(self.site_data)

#         super().mouseDoubleClickEvent(event)


#     def get_main_wid(self) -> GanttMainWidget:
#         if self.main_wid:
#             return self.main_wid

#         scene = self.scene()
#         view = scene.views()[0] if scene and scene.views() else None
#         if view:
#             if isinstance(view.parent(), GanttMainWidget):
#                 self.main_wid = view.parent()
#                 return self.main_wid
#             else:
#                 raise ValueError(f"GanttMainWidget가 아닙니다. : {view.parent()}")
#         else:
#             raise ValueError(f"Scene이 없습니다. : {scene}")
        


class GanttScene(QGraphicsScene):
    PLAN_COLOR = QColor(64, 64, 64)
    ACTUAL_COLOR = QColor(34, 139, 34)           # 완료일 정상 컬러 (초록)
    ACTUAL_COLOR_DELAY = QColor(255, 165, 0)     # 지연중 컬러 (주황)
    PROGRESS_COLOR = QColor(144, 238, 144)       # 진행중 연한 녹색
    DELAY_COLOR = QColor("red")                   # 지연중 빨강
    COMPLETE_TEXT_COLOR = QColor("green")         # 완료 텍스트 색상
    DELAY_TEXT_COLOR = QColor("red")              # 지연 텍스트 색상
    WEEKEND_BG_COLOR = QColor("#dbdbc5")
    WEEKEND_TEXT_COLOR = QColor("#afafaf")
    STATUS_COLOR_PALETTE = {
        "작성": {
            "brush": QColor(144, 238, 144),
            "pen": QColor(0, 128, 0),
            "text_color": QColor("black"),
        },
        "의뢰": {
            "brush": QColor(144, 238, 144),
            "pen": QColor(0, 128, 0),
            "text_color": QColor("black"),
        },
        "접수:정상": {
            "brush": QColor(34, 139, 34),
            "pen": QColor(0, 100, 0),
            "text_color": QColor("green"),
        },
        "접수:지연": {
            "brush": QColor("red"),
            "pen": QColor("red"),
            "text_color": QColor("red"),
        },

        "완료:정상": {
            "brush": QColor(34, 139, 34),
            "pen": QColor(0, 100, 0),
            "text_color": QColor("green"),
        },
        "완료:지연": {
            "brush": QColor(255, 165, 0),
            "pen": QColor(255, 140, 0),
            "text_color": QColor("red"),
        },
        "기본": {
            "brush": QColor("gray"),
            "pen": QColor("darkgray"),
            "text_color": QColor("black"),
        }
    }

    LEFT_MARGIN = -250  # 왼쪽 여백 시작 위치
    label_widths = []


    def __init__(self, data, parent=None):
        super().__init__(parent)

        self.data = data
        self.LABEL_COLUMNS = [
            ("현장명", lambda d: SiteLabelItem( site_data= d ), 100),
            ("부서", lambda d: QGraphicsTextItem(GanttScene.get_dept_name(d["등록자_fk"])), 80),
            ("고객사", lambda d: QGraphicsTextItem(d.get("Elevator사", "미등록")), 80),
        ]
        self.draw_chart()

    def update_data(self, data: list[dict]):
        self.data = copy.deepcopy(data)        
        self.clear()  # 모든 아이템 삭제
        self.draw_chart()

    def draw_label_headers(self):
        x_offset = self.LEFT_MARGIN
        for col_idx, (field_name, _, _) in enumerate(self.LABEL_COLUMNS):
            header_item = QGraphicsTextItem(field_name)
            header_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header_item.setDefaultTextColor(Qt.GlobalColor.black)
            header_item.setPos(x_offset, 0)  # 상단에 표시
            self.addItem(header_item)
            x_offset += self.label_widths[col_idx] + 10

    def draw_date_headers(self, start_date, total_days):
        today = datetime.today().date()
        row_count = len(self.data)

        for day in range(total_days):
            curr_date = start_date + timedelta(days=day)
            x = day * CELL_WIDTH

            # 주말 배경 표시
            if curr_date.weekday() in (5, 6):
                rect = QGraphicsRectItem(x, 0, CELL_WIDTH, HEADER_HEIGHT + row_count * ROW_HEIGHT)
                rect.setBrush(QColor(self.WEEKEND_BG_COLOR))
                rect.setPen(QPen(Qt.PenStyle.NoPen))
                self.addItem(rect)

            # 날짜 라벨 (1,2,3,...)
            top_date_label = QGraphicsTextItem(str(curr_date.day))
            top_date_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            top_date_label.setDefaultTextColor(Qt.GlobalColor.black)
            top_date_label.setPos(x, 0)
            self.addItem(top_date_label)

            # 구분선
            line = QGraphicsLineItem(x, HEADER_HEIGHT, x, HEADER_HEIGHT + row_count * ROW_HEIGHT)
            line.setPen(QPen(Qt.GlobalColor.lightGray))
            self.addItem(line)

            # 오늘 날짜 강조 표시
            if curr_date == today:
                for row_idx, row_data in enumerate(self.data):
                    start = row_data.get("등록일")
                    end = row_data.get("완료요청일")
                    if start and end and start <= curr_date <= end:
                        rect_y = HEADER_HEIGHT + row_idx * ROW_HEIGHT
                        rect = TodayRectItem(QRectF(x, rect_y, CELL_WIDTH, ROW_HEIGHT), item_data=row_data)
                        self.addItem(rect)

    def draw_chart(self):
        if not self.data:
            self.clear()
            return

        # 🔥 필터에서 연/월 가져오기
        wid_parent:GanttMainWidget = self.parent().parent()
        filter_year = int(wid_parent.filter_widget.year_cb.currentText())
        filter_month = int(wid_parent.filter_widget.month_cb.currentText())
        last_day = monthrange(filter_year, filter_month)[1]

        start_date = date(filter_year, filter_month, 1)
        end_date = date(filter_year, filter_month, last_day)
        total_days = (end_date - start_date).days + 1
        today = datetime.today().date()

        # 날짜 파싱 및 보정
        # for d in self.data:
        #     d["등록일"] = self._parse_date(d.get("등록일"), default=start_date)
        #     d["완료요청일"] = self._parse_date(d.get("완료요청일"), default=d["등록일"] + timedelta(days=7))
        #     d["완료일"] = self._parse_date(d.get("완료일"), default=None)

        self.LEFT_MARGIN, self.label_widths = self.calculate_left_margin()
        self.draw_label_headers()
        self.draw_date_headers(start_date, total_days)

        for idx, d in enumerate(self.data):
            base_y = HEADER_HEIGHT + idx * (PLAN_ROW_HEIGHT + ACTUAL_ROW_HEIGHT + ROW_SPACING)
            x_offset = self.LEFT_MARGIN

            for col_idx, (_, item_fn, _) in enumerate(self.LABEL_COLUMNS):
                item = item_fn(d)
                item.setPos(x_offset, base_y)
                self.addItem(item)
                x_offset += self.label_widths[col_idx] + 10

            # 계획 막대
            plan_start = max(d["등록일"], start_date)
            plan_end = min(d["완료요청일"], end_date)
            plan_duration = (plan_end - plan_start).days + 1
            plan_x = (plan_start - start_date).days * CELL_WIDTH

            self._add_rect(plan_x, base_y, plan_duration, PLAN_ROW_HEIGHT, self.PLAN_COLOR, Qt.GlobalColor.gray)

            # 실적 막대
            actual_y = base_y + PLAN_ROW_HEIGHT
            actual_start = max(d["등록일"], start_date)
            actual_end = d["완료일"] or min(today, end_date)
            actual_end = min(actual_end, end_date)
            actual_duration = (actual_end - actual_start).days + 1
            actual_x = (actual_start - start_date).days * CELL_WIDTH
            self._add_rect(actual_x, actual_y, actual_duration, ACTUAL_ROW_HEIGHT, brush, pen)

            # 상태
            brush, pen, status_text, status_text_color = self.get_variables_for_status(d)
            

            text_x = actual_x + actual_duration * CELL_WIDTH + 5
            if d["완료일"] and d["완료일"] > end_date:
                text_x = total_days * CELL_WIDTH + 10  # 말일 이후에 표시

            text_item = QGraphicsTextItem(status_text)
            text_item.setDefaultTextColor(status_text_color)
            text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            text_item.setPos(text_x, actual_y + ACTUAL_ROW_HEIGHT / 4)
            self.addItem(text_item)

    def get_variables_for_status(self, d:dict) -> tuple[QColor, QColor, str, QColor]:
        """ return 은 rect 의 brush color, pen color 및 상태 문자열, 상태 문자열 색상 """
        # 상태
        #### 진행현황은, 작성, Open, Close 3단계임.
        ####  Open, Close 경우,  
        ####💥  Open :  완료요청일이 오늘 날짜보다 크면, '진행', 적으면 '지연' 을 추가함.
        ####💥  Close :  완료일이  완료요청일보다 크면, '지연', 적으면 '정상' 을 추가함.
        진행현황 = d.get("진행현황", "").strip()
        완료요청일: date = d.get("완료요청일")
        완료일: date = d.get("완료일")
        today: date = datetime.today().date()

        key = "기본"
        _text = "Unknown"

        if 진행현황 == "작성":
            _text = "작성"

        elif 진행현황 == "의뢰":
            key = f"{진행현황}"
            경과일:timedelta = today - d['등록일'].date()
            _text = f"의뢰:미접수중 ({경과일.days}일)"
        
        elif 진행현황 == "접수":
            if 완료요청일 < today:
                key = f"접수:지연"
                경과일:timedelta = today - 완료요청일
                _text =  f"처리중:지연 ({경과일.days}일)"
            else:
                key = f"접수:정상"
                _text = "처리중:정상"
        
        elif 진행현황 == "완료":
            if 완료일 > 완료요청일:
                key = f"완료:지연"
                경과일:timedelta = 완료일 - 완료요청일
                _text = f"완료:지연 ({경과일.days}일)"
            else:
                key = f"완료:정상"
                _text = "완료:정상"

        style = self.STATUS_COLOR_PALETTE.get(key, self.STATUS_COLOR_PALETTE["기본"])
        return style["brush"], QPen(style["pen"]), _text, style["text_color"]

    def _parse_date(self, val, default):
        if not val:
            return default
        if isinstance(val, str):
            return datetime.strptime(val.split("T")[0], "%Y-%m-%d").date()
        return val

    def _add_rect(self, x, y, days, height, brush_color, pen_color):
        rect = QGraphicsRectItem(x, y, days * CELL_WIDTH, height)
        rect.setBrush(QBrush(brush_color))
        rect.setPen(QPen(pen_color))
        self.addItem(rect)

    
    def draw_date_headers(self, start_date, total_days):
        # 날짜 헤더
        today = datetime.today().date()
        for day in range(total_days):
            curr_date = start_date + timedelta(days=day)
            # curr_date = curr_datetime.date()
            x = day * CELL_WIDTH

            if curr_date.weekday() in (5, 6):
                rect = QGraphicsRectItem(x, 0, CELL_WIDTH, HEADER_HEIGHT + len(self.data) * ROW_HEIGHT)
                rect.setBrush(QColor( self.WEEKEND_BG_COLOR))
                rect.setPen(QPen(Qt.PenStyle.NoPen))
                self.addItem(rect)

            top_date_label = create_day_label(curr_date)
            top_date_label.setPos(x, 0)
            self.addItem(top_date_label)

            line = QGraphicsLineItem(x, HEADER_HEIGHT, x, HEADER_HEIGHT + len(self.data) * ROW_HEIGHT)
            line.setPen(QPen(Qt.GlobalColor.lightGray))
            self.addItem(line)

            if curr_date == today:
                for row_idx, row_data in enumerate(self.data):
                    start = row_data["등록일"]
                    end = row_data["완료요청일"]
                    if start <= curr_date <= end:
                        rect_y = HEADER_HEIGHT + row_idx * ROW_HEIGHT
                        rect = TodayRectItem(QRectF(x, rect_y, CELL_WIDTH, ROW_HEIGHT), item_data=row_data)
                        self.addItem(rect)

 

    def calculate_left_margin(self):
        # 각 컬럼의 실제 최대 폭 측정
        label_widths = [0] * len(self.LABEL_COLUMNS)

        for d in self.data:
            for i, (field_name, item_fn, _) in enumerate(self.LABEL_COLUMNS):
                item = item_fn(d)
                width = item.boundingRect().width()
                if width > label_widths[i]:
                    label_widths[i] = width

        # 실제 필요한 왼쪽 margin은 전체 너비 합의 음수
        total_width = sum(label_widths) + (len(label_widths) - 1) * 10  # 간격 10px
        return -total_width, label_widths

    @staticmethod
    def get_dept_name( user_id:int):
        # 사용자 아이디로 부서명 조회
        if user_id in INFO.USER_MAP_ID_TO_USER:
            _dict = INFO.USER_MAP_ID_TO_USER[user_id]
            MBO_표시명_부서 = _dict['MBO_표시명_부서']
            if MBO_표시명_부서 and len(MBO_표시명_부서) > 1:
                return MBO_표시명_부서
            else:
                return _dict['기본조직1']
        else:
            return "Unknown"

class GanttView(QGraphicsView):

    def __init__(self, parent:Optional[QWidget]=None, data:Optional[list[dict]]=None):
        super().__init__(parent)
        self.data = data or []
        self.scale_factor = 1.0  # ✅ 항상 초기화
        if data:
            self.set_data(data)

    def _init_by_data(self, data):
        if data and isinstance(data, list):
            self.data = data
            self.setScene(GanttScene(data, self))
            self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
            self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.scale_factor = 1.0  # 초기 배율
        else:
            raise ValueError("data is required")
    
    def set_data(self, data: list[dict]):
        if isinstance(self.scene(), GanttScene):
            self.scene().clear()
        if not data or not isinstance(data, list):
            return
        
        self.data = data
        self._update_scene(data)


    def _update_scene(self, data: list[dict]):

        # if hasattr(self, 'scene') and isinstance(self.scene(), GanttScene):
        #     scene : GanttScene = self.scene()
        #     scene.clear()  # 기존 아이템 제거
        #     scene.update_data(data)  # 내부 상태만 갱신
        # else:
        #     scene = GanttScene(data, self)
        #     self.setScene(scene)
        # ✅그냥 새 Scene 으로 교체해 버리는 게 가장 확실하고 안전, 왜냐면 업데이트가 안된다.
        scene = GanttScene(data, self)
        self.setScene(scene)

        # 💡 자동으로 사이즈 맞추기
        scene = self.scene()
        scene.setSceneRect(scene.itemsBoundingRect())

        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)


    def wheelEvent(self, event):
        # Ctrl 키와 함께 휠 -> 확대/축소
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.1 if angle > 0 else 0.9
            self.scale_factor *= factor
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)


class GanttFilterWidget(QWidget):
    """ argument:
        year_cb_list: list[int]
        month_cb_list: list[int]
        default_year: int
        default_month: int
    """
    filter_changed = pyqtSignal(int, int)  # year, month

    def __init__(self, 
                 parent=None,
                 year_cb_list: list[int] =[], 
                 month_cb_list: list[int] =[], 
                 default_year: int =0, 
                 default_month: int =0, 
                 ):



        super().__init__(parent)

        self.year_cb_list = year_cb_list
        self.month_cb_list = month_cb_list
        self.default_year = default_year
        self.default_month = default_month

        self.UI()

    def UI(self):
        layout = QHBoxLayout()

        self.year_cb = QComboBox()
        self.month_cb = QComboBox()

        self.year_cb.addItems([str(y) for y in self.year_cb_list])
        self.month_cb.addItems([f"{m:02}" for m in self.month_cb_list])         


        self.year_cb.setCurrentText(str(self.default_year)) # 년도 기본값 설정
        self.month_cb.setCurrentText( f"{self.default_month:02}" ) # 월 기본값 설정

        self.year_cb.currentIndexChanged.connect(self._emit_filter_changed)
        self.month_cb.currentIndexChanged.connect(self._emit_filter_changed)
        #### 초기값 실행
        # 🔥 emit 지연 실행
        QTimer.singleShot(0, self._emit_filter_changed)

        layout.addWidget(QLabel("년"))
        layout.addWidget(self.year_cb)
        layout.addWidget(QLabel("월"))
        layout.addWidget(self.month_cb)
        layout.addStretch()
        self.setLayout(layout)

    def _emit_filter_changed(self) -> tuple[int, int]:
        year = int(self.year_cb.currentText())
        month = int(self.month_cb.currentText())
        self.filter_changed.emit(year, month)


class GanttMainWidget(QWidget, LazyParentAttrMixin_V2):
    def __init__(self, parent=None, data: list[dict] =[] ):        
        super().__init__(parent)
        self.start_init_time = time.perf_counter()
        self.event_bus = event_bus
        self.lazy_attr_names = ['APP_ID']
        self.lazy_ready_flags = {}
        self.lazy_attr_values = {}
        self.lazy_ws_names = []
        self.table_name = None

        self.run_lazy_attr()
        self._init_flag = False
        
        if data:
            self._init_by_data(data)

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.APP_ID = APP_ID
            self.app_dict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            self.subscribe_gbus()

            if hasattr(self, 'data') and self.data:
                self._init_by_data(self.data)
        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")
  

    def subscribe_gbus(self):
        self.event_bus.subscribe(f'{self.table_name}:datas_changed', self.on_data_changed)

    def on_data_changed(self, data: list[dict]):
        try:
            self.data = self.conversion_data(copy.deepcopy(data))
            self._reset_ui(self.data)
        except Exception as e:
            logger.error(f"on_data_changed 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_data_changed 오류', text=f"{e}<br>{trace}")

    def _reset_ui(self, data: list[dict]):
        # 💥 기존 layout 제거
        if self.layout():
            QWidget().setLayout(self.layout())  # 기존 layout 제거용 trick

        self._init_flag = False
        self._init_by_data(data)

    
    def conversion_data(self, data:list[dict]) -> list[dict]:
        for d in data:
            d["등록일"] = self._parse_date(d.get("등록일"), default=None)
            d["완료요청일"] = self._parse_date(d.get("완료요청일"), default=d["등록일"] + timedelta(days=7))
            d["완료일"] = self._parse_date(d.get("완료일"), default=None)
            # obj['등록일'] = Utils.convert_date_from_datestr(obj['등록일'])
            # obj['완료요청일'] = Utils.convert_date_from_datetimestr(obj['완료요청일'])
            # obj['완료일'] = Utils.convert_date_from_datetimestr(obj['완료일'])
        return data
    
    def _parse_date(self, val, default):
        if not val:
            return default
        if isinstance(val, str):
            return datetime.strptime(val.split("T")[0], "%Y-%m-%d").date()
        return val


    def _init_by_data(self, data:list[dict]):
        if self._init_flag:
            return  
        
        self.data = data
        layout = QVBoxLayout()

        # 1. 등록일 기준으로 연도/월 목록 추출
        dates = [
            item['등록일']
            for item in data
            if item.get('등록일')
        ]
        years = sorted({dt.year for dt in dates}, reverse=True)
        months = sorted({dt.month for dt in dates}, reverse=True)

        # 2. 가장 최근 등록일 기준 default 값 설정
        latest_date = max(dates) if dates else datetime.today()
        default_year = latest_date.year
        default_month = latest_date.month

        # 3. 필터 위젯 초기화 시 필요한 값 전달
        self.filter_widget = GanttFilterWidget(
            self,
            year_cb_list=years,
            month_cb_list=months,
            default_year=default_year,
            default_month=default_month
        )

        self.view = GanttView(parent=self, data=data)

        layout.addWidget(self.filter_widget)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.filter_widget.filter_changed.connect(self.apply_date_filter)

        self._init_flag = True

    def apply_date_filter(self, year:Optional[int] = None, month:Optional[int] = None):
        if year is None:
            year = self.filter_widget.year_cb.currentText()
        if month is None:
            month = self.filter_widget.month_cb.currentText()

        filtered_data = [item for item in self.data 
                         if Utils.convert_str_to_date(item['등록일']).year == year and 
                         Utils.convert_str_to_date(item['등록일']).month == month]
        

        self.view.set_data(filtered_data)

    def on_site_menu_action(self, key:str, site_data:dict):
        """ app 내에서 바로 gantt_chart에서 table widget으로 publish 함
            만약, table widget 에서 site_data 변경 시 자동 update 됨 ( site_data가 self.site_data 임 )
        """

        senddata =  {'key':key, 'selected_id':site_data['id']}
        구독자수 = self.event_bus.publish( f"{self.table_name}:gantt_chart_action", senddata )
        




if __name__ == "__main__":
    import sys
    task_data = [ 
            {'id': 51, 'el_info_fk': 148832, 'el수량': 2, '운행층수': 11, '현장명': '삼라마이다스빌', 
            '현장주소': '광주광역시 북구 동운로 141', 'Elevator사': 'TKE', '부적합유형': '스크래치', 
            '불만요청사항': '1\n2\n3\n4\n5', '고객명': '관리소장', '고객연락처': '011-1111-1111', '차수': 1, '진행현황': '작성', '품질비용': 0, '등록자': 'admin', '등록자_fk': 1, 
            '등록일': '2025-05-21T17:57:50', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': '2025-05-26', 'claim_file_수': 7, 'activity_수': 0, 'claim_files_ids': [121, 124, 127, 128, 129, 130, 131], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/d4332a4b-5897-4b9a-b4e0-532947476190/local.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/45e871a1-fd8f-47fc-a8ae-3eb38cee5b9d/server.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/01bc8292-8e77-45fb-af34-71ce1f76ad12/%ED%99%94%EC%82%B4%ED%91%9C.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/1a408f74-036c-421d-9aa8-3136ff8a86ed/%EB%AC%BC%EA%B2%B0.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/97d9add2-ba57-477d-a37e-77fb45b4503b/%EB%B3%BC%EB%9D%BC%EC%9D%B8.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/4bf4559f-81c1-4921-a644-24bf6b473582/24-079_1.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/ea75a40d-b765-4b81-9121-ede92aa0b5dd/24-079_2.png'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 39, 'el_info_fk': 85945, 'el수량': 3, '운행층수': 48, '현장명': '덕암아파트', 
            '현장주소': '대전광역시 대덕구 덕암로265번길 81', 'Elevator사': 'OTIS', '부적합유형': '스크래치', 
            '불만요청사항': '기준층도어, 기타층도어 전층 밴딩부 색까짐 현장 발생되었읍니다.\n설치 초기부터 발생되었으며 감리사 지적사항입니다.\n당사 CS팀 이영훈주임님이  25.01.17 현장방문하여 당일 보수불가 판단하여 추후 재방문하겠다고 소장님께 전달하였으나 현재까지 별도의 조치가 없는 상황이라고 하셨읍니다.\n바쁘시겠지만 방문하시어 처리 부탁드리겠읍니다.', '고객명': '덕암아파트 관리소장', '고객연락처': '010-2252-3309', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 116, '등록일': '2025-05-20T08:53:57.957268', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 7, 'activity_수': 0, 'claim_files_ids': [104, 105, 106, 107, 108, 109, 110], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/c5ba57e4-0a80-47d8-ba56-ee6848bbf6f0/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B81.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/a4f0f79f-d9bd-472c-bb47-2ddd535922bf/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B82.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/104f5453-4be5-4a96-a72e-8499d5f1d337/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B83.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/4896a5c7-e418-4557-ba81-e4ebf24dc175/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B84.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/bad8507b-6348-455a-a39f-ea3ecd191ac9/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B85.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/9d562f3d-ca83-4713-9782-854576f83b9c/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B86.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/bcc61cb8-0acc-4462-b6b8-9aa90ef0d163/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B87.jpg'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 37, 'el_info_fk': None, 'el수량': 1, '운행층수': 1, '현장명': '한울3차아파트(K20240590)', 
            '현장주소': '충청북도 청주시 청원구 주성로96번길 12', 'Elevator사': 'TKE', '부적합유형': '박리', 
            '불만요청사항': '잠 밴딩부 뜯김 발생\n-감리 지적사항\n-아파트 및 EL사 빠른 보수진행 요청\n-조건부 승인 상태임', '고객명': '아파트 관리소장', '고객연락처': '043-213-4211', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, 
            '등록자_fk': 15, '등록일': '2025-05-16T09:15:28.845602', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 1, 'activity_수': 0, 'claim_files_ids': [103], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-16/1204f1cb-414d-4a74-b449-fcc0bb8c8648/%ED%95%9C%EC%9A%B83%EC%B0%A8.jpg'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, {'id': 36, 'el_info_fk': None, 'el수량': 11, '운행층수': 1, '현장명': '천안)두정대우2차', '현장주소': '충청남도 천안시 서북구 두정동 530', 'Elevator사': '현대', '부적합유형': '스크래치', '불만요청사항': '후면 중앙판넬 팬딩부 뜯김 발생\n-전호기 점검 요청 드립니다.\n-주변현장 교체공사 준비중 견학단지입니다.\n-최대한 빠른 요청 드립니다.\n-현장 견학 후 의장재 선정 계획 입니다.', '고객명': '관리소장', '고객연락처': '041-568-2440', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, '등록일': '2025-05-15T07:56:53.774219', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 35, 'el_info_fk': None, 'el수량': 27, '운행층수': 1, '현장명': '아산주은환타지아', 
            '현장주소': '충청남도 아산시 어의정로183번길 14', 'Elevator사': 'TKE', '부적합유형': '스크래치', 
            '불만요청사항': '상판 기포발생부분 점검요청 드립니다.\n-전호기 상판에 있음\n-교체 및 보수에관하여 협의 요청 드립니다.\n\n스크레치 및 기타사항도 전호기 점검 요청 드립니다.', '고객명': '아파트 관리소장', '고객연락처': '041-533-0167', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, 
            '등록자_fk': 15, 
            '등록일': '2025-05-12T17:06:18.231341', '완료자': None, '완료자_fk': None, 
            '완료일': '2025-05-20T17:57:50', 
            '완료요청일': '2025-05-18', 
            'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 34, 'el_info_fk': None, 'el수량': 32, '운행층수': 1, '현장명': '코오롱동신아파트', 
            '현장주소': '충청북도 충주시 금릉로 14', 'Elevator사': '현대', '부적합유형': '스크래치', 
            '불만요청사항': '무상보수 2회 약속 현장이며\n충주지역 많은 소개와 지원을 해주시는 분입니다.\n\n기스발생현장은 얼마 되지 않으나 빠른 점검 요청 드립니다.\n\n양영모 수석님과 6월 말경 약속한 현장 입니다.\n(6월 20일~ 30일) 사이 일정협의하시고 진행요청 드립니다.', '고객명': '이성욱 관리소장', '고객연락처': '010-5233-5000', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, 
            '등록일': '2025-05-09T08:21:45.446129', '완료자': None, '완료자_fk': None, 
            '완료일':'2025-05-17T17:57:50', 
            '완료요청일': '2025-05-21', 
            'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, {'id': 33, 'el_info_fk': None, 'el수량': 20, '운행층수': 1, '현장명': '세원느티마을', '현장주소': '충청북도 청주시 흥덕구 진재로 67', 'Elevator사': 'OTIS', '부적합유형': '스크래치', '불만요청사항': '무상보수 1회 약속 현장이며\n무상보수 요청건 입니다.\n\n전호기 점검 요청 드립니다.', '고객명': '관리소장', '고객연락처': '010-9165-3051', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, '등록일': '2025-05-07T17:30:59.929696', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0},

     ]  # ← 위 JSON 리스트 붙여넣기
    task_data = [ 
            {'id': 51, 'el_info_fk': 148832, 'el수량': 2, '운행층수': 11, '현장명': '삼라마이다스빌', 
            '현장주소': '광주광역시 북구 동운로 141', 'Elevator사': 'TKE', '부적합유형': '스크래치', 
            '불만요청사항': '1\n2\n3\n4\n5', '고객명': '관리소장', '고객연락처': '011-1111-1111', '차수': 1, '진행현황': '작성', '품질비용': 0, '등록자': 'admin', '등록자_fk': 1, 
            '등록일': '2025-05-21T17:57:50', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': '2025-05-26', 'claim_file_수': 7, 'activity_수': 0, 'claim_files_ids': [121, 124, 127, 128, 129, 130, 131], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/d4332a4b-5897-4b9a-b4e0-532947476190/local.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/45e871a1-fd8f-47fc-a8ae-3eb38cee5b9d/server.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/01bc8292-8e77-45fb-af34-71ce1f76ad12/%ED%99%94%EC%82%B4%ED%91%9C.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/1a408f74-036c-421d-9aa8-3136ff8a86ed/%EB%AC%BC%EA%B2%B0.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/97d9add2-ba57-477d-a37e-77fb45b4503b/%EB%B3%BC%EB%9D%BC%EC%9D%B8.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/4bf4559f-81c1-4921-a644-24bf6b473582/24-079_1.png', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-21/ea75a40d-b765-4b81-9121-ede92aa0b5dd/24-079_2.png'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 39, 'el_info_fk': 85945, 'el수량': 3, '운행층수': 48, '현장명': '덕암아파트', 
            '현장주소': '대전광역시 대덕구 덕암로265번길 81', 'Elevator사': 'OTIS', '부적합유형': '스크래치', 
            '불만요청사항': '기준층도어, 기타층도어 전층 밴딩부 색까짐 현장 발생되었읍니다.\n설치 초기부터 발생되었으며 감리사 지적사항입니다.\n당사 CS팀 이영훈주임님이  25.01.17 현장방문하여 당일 보수불가 판단하여 추후 재방문하겠다고 소장님께 전달하였으나 현재까지 별도의 조치가 없는 상황이라고 하셨읍니다.\n바쁘시겠지만 방문하시어 처리 부탁드리겠읍니다.', '고객명': '덕암아파트 관리소장', '고객연락처': '010-2252-3309', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 116, '등록일': '2025-05-20T08:53:57.957268', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 7, 'activity_수': 0, 'claim_files_ids': [104, 105, 106, 107, 108, 109, 110], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/c5ba57e4-0a80-47d8-ba56-ee6848bbf6f0/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B81.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/a4f0f79f-d9bd-472c-bb47-2ddd535922bf/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B82.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/104f5453-4be5-4a96-a72e-8499d5f1d337/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B83.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/4896a5c7-e418-4557-ba81-e4ebf24dc175/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B84.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/bad8507b-6348-455a-a39f-ea3ecd191ac9/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B85.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/9d562f3d-ca83-4713-9782-854576f83b9c/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B86.jpg', '/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-20/bcc61cb8-0acc-4462-b6b8-9aa90ef0d163/%EB%8D%95%EC%95%94%EC%95%84%ED%8C%8C%ED%8A%B87.jpg'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 37, 'el_info_fk': None, 'el수량': 1, '운행층수': 1, '현장명': '한울3차아파트(K20240590)', 
            '현장주소': '충청북도 청주시 청원구 주성로96번길 12', 'Elevator사': 'TKE', '부적합유형': '박리', 
            '불만요청사항': '잠 밴딩부 뜯김 발생\n-감리 지적사항\n-아파트 및 EL사 빠른 보수진행 요청\n-조건부 승인 상태임', '고객명': '아파트 관리소장', '고객연락처': '043-213-4211', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, 
            '등록자_fk': 15, '등록일': '2025-05-16T09:15:28.845602', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 1, 'activity_수': 0, 'claim_files_ids': [103], 'claim_files_url': ['/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EA%B3%A0%EA%B0%9D%EC%9A%94%EC%B2%AD/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2025-5-16/1204f1cb-414d-4a74-b449-fcc0bb8c8648/%ED%95%9C%EC%9A%B83%EC%B0%A8.jpg'], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, {'id': 36, 'el_info_fk': None, 'el수량': 11, '운행층수': 1, '현장명': '천안)두정대우2차', '현장주소': '충청남도 천안시 서북구 두정동 530', 'Elevator사': '현대', '부적합유형': '스크래치', '불만요청사항': '후면 중앙판넬 팬딩부 뜯김 발생\n-전호기 점검 요청 드립니다.\n-주변현장 교체공사 준비중 견학단지입니다.\n-최대한 빠른 요청 드립니다.\n-현장 견학 후 의장재 선정 계획 입니다.', '고객명': '관리소장', '고객연락처': '041-568-2440', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, '등록일': '2025-05-15T07:56:53.774219', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 35, 'el_info_fk': None, 'el수량': 27, '운행층수': 1, '현장명': '아산주은환타지아', 
            '현장주소': '충청남도 아산시 어의정로183번길 14', 'Elevator사': 'TKE', '부적합유형': '스크래치', 
            '불만요청사항': '상판 기포발생부분 점검요청 드립니다.\n-전호기 상판에 있음\n-교체 및 보수에관하여 협의 요청 드립니다.\n\n스크레치 및 기타사항도 전호기 점검 요청 드립니다.', '고객명': '아파트 관리소장', '고객연락처': '041-533-0167', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, 
            '등록자_fk': 15, 
            '등록일': '2025-05-12T17:06:18.231341', '완료자': None, '완료자_fk': None, 
            '완료일': '2025-05-20T17:57:50', 
            '완료요청일': '2025-05-18', 
            'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, 
            {'id': 34, 'el_info_fk': None, 'el수량': 32, '운행층수': 1, '현장명': '코오롱동신아파트', 
            '현장주소': '충청북도 충주시 금릉로 14', 'Elevator사': '현대', '부적합유형': '스크래치', 
            '불만요청사항': '무상보수 2회 약속 현장이며\n충주지역 많은 소개와 지원을 해주시는 분입니다.\n\n기스발생현장은 얼마 되지 않으나 빠른 점검 요청 드립니다.\n\n양영모 수석님과 6월 말경 약속한 현장 입니다.\n(6월 20일~ 30일) 사이 일정협의하시고 진행요청 드립니다.', '고객명': '이성욱 관리소장', '고객연락처': '010-5233-5000', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, 
            '등록일': '2025-05-09T08:21:45.446129', '완료자': None, '완료자_fk': None, 
            '완료일':'2025-05-17T17:57:50', 
            '완료요청일': '2025-05-21', 
            'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0}, {'id': 33, 'el_info_fk': None, 'el수량': 20, '운행층수': 1, '현장명': '세원느티마을', '현장주소': '충청북도 청주시 흥덕구 진재로 67', 'Elevator사': 'OTIS', '부적합유형': '스크래치', '불만요청사항': '무상보수 1회 약속 현장이며\n무상보수 요청건 입니다.\n\n전호기 점검 요청 드립니다.', '고객명': '관리소장', '고객연락처': '010-9165-3051', '차수': 1, '진행현황': 'Open', '품질비용': 0, '등록자': None, '등록자_fk': 15, '등록일': '2025-05-07T17:30:59.929696', '완료자': None, '완료자_fk': None, '완료일': None, '완료요청일': None, 'claim_file_수': 0, 'activity_수': 0, 'claim_files_ids': [], 'claim_files_url': [], 'activity_files_ids': [], 'activity_files_url': [], 'activity_file_수': 0},

    ]  # ← 위 JSON 리스트 붙여넣기


    app = QApplication(sys.argv)
    window = GanttView(task_data)
    window.setWindowTitle("일정 관리 Gantt 차트")
    window.resize(1200, 600)
    window.show()
    sys.exit(app.exec())
