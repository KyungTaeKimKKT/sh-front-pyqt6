from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import sys
from datetime import datetime, timedelta

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

class SiteLabelItem(QGraphicsTextItem):
    hover_cursor = Qt.CursorShape.PointingHandCursor
    hover_color = QColor("#0077cc") ### 파란색 강조

    def __init__(self, site_data):
        super().__init__(site_data["현장명"])
        self.site_data = site_data
        self.setAcceptHoverEvents(True)  # hover 이벤트 활성화
        self.default_color = self.defaultTextColor()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.setCursor(self.hover_cursor)
        self.setDefaultTextColor(self.hover_color)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.unsetCursor()
        self.setDefaultTextColor(self.default_color)
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        dialog = SiteEditDialog(self.site_data)
        if dialog.exec():
            updated_name = dialog.name_edit.text()
            self.setPlainText(updated_name)
            self.site_data["현장명"] = updated_name
        super().mouseDoubleClickEvent(event)



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

    LEFT_MARGIN = -250  # 왼쪽 여백 시작 위치
    label_widths = []

    LABEL_COLUMNS = [
        ("현장명", lambda d: SiteLabelItem({"현장명": d["현장명"]}), 100),
        ("부서", lambda d: QGraphicsTextItem(GanttScene.get_dept_name(d["등록자_fk"])), 80),
        ("고객사", lambda d: QGraphicsTextItem(d.get("Elevator사", "미등록")), 80),
    ]


    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
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

    def draw_chart(self):
        # 날짜 파싱 및 기본값 설정
        ### 등록일 : datetime, 완료요청일: date, 완료일:datetime 형태임
        for d in self.data:
            d["등록일"] = datetime.strptime(d["등록일"].split('T')[0], "%Y-%m-%d").date()
            if d.get("완료요청일"):
                d["완료요청일"] = datetime.strptime(d["완료요청일"], "%Y-%m-%d").date()
            else:
                d["완료요청일"] = d["등록일"] + timedelta(days=7)
            if d.get("완료일"):
                d["완료일"] = datetime.strptime(d["완료일"].split('T')[0], "%Y-%m-%d").date()
            else:
                d["완료일"] = None

        start_date = min(d["등록일"] for d in self.data)
        end_date_candidates = [d["완료요청일"] for d in self.data] + [d["완료일"] for d in self.data if d["완료일"]]
        end_date = max(end_date_candidates)
        total_days = (end_date - start_date).days + 1
        today = datetime.today().date()

        self.LEFT_MARGIN, self.label_widths = self.calculate_left_margin()
        self.draw_label_headers()
        self.draw_date_headers(start_date, total_days)


        # 현장명 및 일정 데이터 그리기
        for idx, d in enumerate(self.data):
            base_y = HEADER_HEIGHT + idx * (PLAN_ROW_HEIGHT + ACTUAL_ROW_HEIGHT + ROW_SPACING)

            ### 현장명, 부서, 고객사 라벨 생성
            # === 동적으로 컬럼 라벨 생성 ===
            x_offset = self.LEFT_MARGIN
            for col_idx, (field_name, item_fn, _) in enumerate(self.LABEL_COLUMNS):
                item = item_fn(d)
                item.setPos(x_offset, base_y)
                self.addItem(item)
                x_offset += self.label_widths[col_idx] + 10  # +10: 간격
            
            # 계획(완료요청일) 막대: 연한 회색, 높이 PLAN_ROW_HEIGHT
            plan_start_x = (d["등록일"] - start_date).days * CELL_WIDTH
            plan_duration = (d["완료요청일"] - d["등록일"]).days + 1
            plan_rect = QGraphicsRectItem(plan_start_x, base_y, plan_duration * CELL_WIDTH, PLAN_ROW_HEIGHT)
            plan_rect.setBrush(QBrush(self.PLAN_COLOR))  # 연한 회색
            plan_rect.setPen(QPen(Qt.GlobalColor.gray))
            self.addItem(plan_rect)


            # 실적 막대 및 상태 텍스트: ACTUAL_ROW_HEIGHT 위치
            actual_y = base_y + PLAN_ROW_HEIGHT
            actual_start_x = plan_start_x

            if d["완료일"]:
                actual_duration = (d["완료일"] - d["등록일"]).days + 1
                if d["완료일"] <= d["완료요청일"]:
                    color = self.ACTUAL_COLOR
                    pen = QPen(Qt.GlobalColor.darkGreen)
                    status_text = "완료"
                    status_text_color = self.COMPLETE_TEXT_COLOR
                else:
                    color = self.ACTUAL_COLOR_DELAY
                    pen = QPen(QColor(255, 165, 0))
                    status_text = "지연중"
                    status_text_color = self.DELAY_TEXT_COLOR
            else:
                actual_duration = (today - d["등록일"]).days + 1
                if today <= d["완료요청일"]:
                    color = self.PROGRESS_COLOR
                    pen = QPen(Qt.GlobalColor.darkGreen)
                    status_text = "진행중"
                    status_text_color = QColor("black")  # 진행중 텍스트는 검정으로
                else:
                    color = self.DELAY_COLOR
                    pen = QPen(self.DELAY_COLOR)
                    status_text = "지연중"
                    status_text_color = self.DELAY_TEXT_COLOR

            actual_rect = QGraphicsRectItem(actual_start_x, actual_y, actual_duration * CELL_WIDTH, ACTUAL_ROW_HEIGHT)
            actual_rect.setBrush(QBrush(color))
            actual_rect.setPen(pen)
            self.addItem(actual_rect)

            status_item = QGraphicsTextItem(status_text)
            status_item.setDefaultTextColor(status_text_color)
            status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            status_item.setPos(actual_start_x + actual_duration * CELL_WIDTH + 5, actual_y + ACTUAL_ROW_HEIGHT / 4)
            self.addItem(status_item)

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
        dept_data = { 15: '중부지사', 1: '관리자'}
        return dept_data.get(user_id, "Unknown")

class GanttView(QGraphicsView):
    def __init__(self, data):
        super().__init__()
        self.setScene(GanttScene(data))
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scale_factor = 1.0  # 초기 배율

    def wheelEvent(self, event):
        # Ctrl 키와 함께 휠 -> 확대/축소
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.1 if angle > 0 else 0.9
            self.scale_factor *= factor
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)




if __name__ == "__main__":
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
