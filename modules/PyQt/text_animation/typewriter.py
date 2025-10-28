from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()
import time

# class TypewriterLabel(QLabel):
#     def __init__(self, parent:QWidget=None, 
#                  text="",  
#                  datas:list[str]=[], 
#                  char_interval=100, 
#                  str_interval=1000, 
#                  cursor_interval=400,
#                  cursor_char="▌",
#                  loop=-1, 
#                  position:str="center", #['center', 'left', 'right', 'fixed_center']
#                  **kwargs
#                  ):
#         super().__init__(parent)
#         self.kwargs = kwargs
#         self.datas = datas
#         self.full_text = text
#         self.char_interval = char_interval  # ms 단위 (한 글자 표시 간격)
#         self.str_interval = str_interval  # ms 단위 (한 문장 표시 간격)
#         self.loop = loop
#         self.current_loop = 0
#         self.current_show_char_index = 0    ### 보여주는 str의 char index
#         self.current_text_index = 0          ### 보여주는 datas :list[str]의 index
#         ### cursor 관련 
#         self.cursor_visible = True
#         self.cursor_interval = cursor_interval
#         self.cursor_char = cursor_char
#         self.position = position
#         self.default_style_sheet = "background-color: white;color:black;font-weight:bold;"
#         self.style_sheet = kwargs.get('style_sheet', self.default_style_sheet)

#         self.setup_ui()
#         self.init_timer()       ### 2개의 timer 초기화 : self.char_timer, self.str_timer

#         self.is_finished = False

#         if text:
#             self.set_text(text)

#         if self.datas:
#             self.start_animation( self.datas[self.current_text_index])

#     def pause_animation(self):
#         self.char_timer.stop()
#         self.str_timer.stop()
    
#     def resume_animation(self):
#         self.char_timer.start(self.char_interval)

#     def stop_animation(self):
#         """ 현재 text 도 clear 하고, 애니메이션 중지 """
#         self.setText("")
#         self.char_timer.stop()
#         self.str_timer.stop()

#     def set_text(self, text:str):
#         """ 텍스트 설정, self.datas 에 없으면 추가하여 self.current_text_index 설정 """
#         if text:
#             if text not in self.datas:
#                 self.datas.append(text)
#             self.current_text_index = self.datas.index(text)   

#     def set_interval(self, char_interval:Optional[int]=None, str_interval:Optional[int]=None, cursor_interval:Optional[int]=None):
#         """ 애니메이션 간격 설정 """
#         is_valid_interval = lambda interval: interval is not None and isinstance(interval, int) and interval > 0
#         if is_valid_interval(char_interval):
#             self.char_interval = char_interval
#         if is_valid_interval(str_interval):
#             self.str_interval = str_interval
#         if is_valid_interval(cursor_interval):
#             self.cursor_interval = cursor_interval
#         self.init_timer()

#     def set_style_sheet(self, style_sheet:str):
#         self.style_sheet = style_sheet
#         self.setStyleSheet(self.style_sheet)

#     def setup_ui(self):
#         alignment_map = {
#             "center": Qt.AlignmentFlag.AlignCenter,
#             "left": Qt.AlignmentFlag.AlignLeft,
#             "right": Qt.AlignmentFlag.AlignRight,
#             "fixed_center": Qt.AlignmentFlag.AlignCenter
#         }
#         self.setAlignment(alignment_map.get(self.position, Qt.AlignmentFlag.AlignCenter))
#         self.setStyleSheet(self.style_sheet)

#     def init_timer(self):
#         self.init_char_timer()
#         self.init_str_timer()
#         self.init_cursor_timer()

#     def init_char_timer(self):
#         if not getattr(self, 'char_timer', None):
#             self.char_timer = QTimer(self)
#             self.char_timer.timeout.connect(self._show_next_char)

#     def init_str_timer(self):
#         if not getattr(self, 'str_timer', None):
#             self.str_timer = QTimer(self)
#             self.str_timer.setSingleShot(True)
#             self.str_timer.timeout.connect(self.next_text)
    
#     def init_cursor_timer(self):
#         if not getattr(self, 'cursor_timer', None):
#             self.cursor_timer = QTimer(self)
#             self.cursor_timer.timeout.connect(self._toggle_cursor)
#             self.cursor_timer.start(self.cursor_interval)


#     def start_animation(self, text=None):
#         """애니메이션 시작"""
#         text = text or self.datas[self.current_text_index]
#         if text:
#             self.full_text = text
#         self.current_show_char_index = 0
#         self.is_finished = False
#         self.setText("")
#         self.init_char_timer()
#         self.char_timer.start(self.char_interval)
    
#     def _toggle_cursor(self):
#         self.cursor_visible = not self.cursor_visible
#         if not self.is_finished:
#             # 타이핑 중에는 현재까지 표시된 텍스트 + 커서
#             self._refresh_cursor()
#         else:
#             # 타이핑 끝나면 전체 문장 + 커서
#             self.setText(self.full_text + (self.cursor_char if self.cursor_visible else ""))

#     def _refresh_cursor(self):
#         """현재 텍스트에 커서만 업데이트"""
#         visible_part = self.full_text[:self.current_show_char_index]
#         if self.position == "fixed_center":
#             padded_text = visible_part.ljust(len(self.full_text), " ")
#         else:
#             padded_text = visible_part
#         self.setText(padded_text + (self.cursor_char if self.cursor_visible else ""))

#     def _show_next_char(self):
#         """ 한 글자씩 표시 """
#         if self.current_show_char_index < len(self.full_text):
#             visible_part = self.full_text[:self.current_show_char_index + 1]

#             if self.position == "fixed_center":
#                 # 남은 부분 공백 채우기 → 중앙 위치 고정
#                 padded_text = visible_part.ljust(len(self.full_text), " ")
#             else:
#                 padded_text = visible_part

#             # 커서 붙이기
#             self.setText(padded_text + (self.cursor_char if self.cursor_visible else ""))
#             self.current_show_char_index += 1
#             self.is_finished = False
#         else:
#             self.char_timer.stop()
#             self.is_finished = True
#             self.str_timer.start(self.str_interval)     ### 다음 문장 표시 시작 timer 시작 : single shot -> next_text() 호출

#     def next_text(self):
#         self.current_text_index += 1
#         if self.current_text_index >= len(self.datas):
#             self.current_text_index = 0
#             self.current_loop += 1
#             if self.loop != -1 and self.current_loop >= self.loop:
#                 self.stop_animation()
#                 return
#         self.start_animation(self.datas[self.current_text_index])

class TypewriterLabel(QLabel):
    position_list = ['fixed_center', 'left', 'right', 'center' ]
    position_map = {
        "center": Qt.AlignmentFlag.AlignCenter,
        "left": Qt.AlignmentFlag.AlignLeft,
        "right": Qt.AlignmentFlag.AlignRight,
        "fixed_center": Qt.AlignmentFlag.AlignCenter
    }

    def __init__(self, parent: QWidget = None, 
                 text="",
                 datas=[], 
                 char_interval=100, 
                 str_interval=1000, 
                 loop=-1,
                 position="fixed_center", 
                 cursor_char="▌", 
                 blink_interval=500,
                 **kwargs
                 ):
        super().__init__(parent)
        self.kwargs = kwargs
        self.datas = list(datas) if datas else []
        self.full_text = text or ""
        if text and text not in self.datas:
            self.datas.append(text)

        self.char_interval = max(1, int(char_interval))
        self.str_interval = max(1, int(str_interval))
        self.loop = loop

        self.position = position  or self.position_list[0] # "left" | "right" | "center" | "fixed_center"
        self.cursor_char = cursor_char
        self.blink_interval = max(50, int(blink_interval))

        self.current_loop = 0
        self.current_show_char_index = 0
        self.current_text_index = 0
        self.is_finished = False
        self.cursor_visible = True

        style_sheet = kwargs.get(
            'style_sheet',
            "background-color: white; color: black; font-weight: bold;"
        )
        self.setup_ui()
        self.setStyleSheet(style_sheet)
        self._apply_alignment()  # non-fixed 모드 정렬

        # 타이머들
        self.char_timer = QTimer(self)
        self.char_timer.timeout.connect(self._show_next_char)

        self.str_timer = QTimer(self)
        self.str_timer.setSingleShot(True)
        self.str_timer.timeout.connect(self._next_text)

        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor)
        self.cursor_timer.start(self.blink_interval)

        # 시작
        if self.datas:
            self._start_animation(self.datas[self.current_text_index])
        elif self.full_text:
            if self.full_text not in self.datas:
                self.datas.append(self.full_text)
            self._start_animation(self.full_text)

    # ---------- 외부 API ----------
    def set_text(self, text: str):
        if text and text not in self.datas:
            self.datas.append(text)
        if text:
            self.current_text_index = self.datas.index(text)

    def set_position(self, pos: str):
        self.position = pos or self.position
        self._apply_alignment()
        # fixed_center 전환 시 setText로 그리던 문자열을 지우고 페인터 경로로 전환
        if self._use_painter():
            super().setText("")
            self.update()
        else:
            self._update_label_text()

    def set_char_interval(self, char_interval:int):
        self.char_interval = max(1, int(char_interval))
        self.char_timer.start(self.char_interval)

    def set_str_interval(self, str_interval:int):
        self.str_interval = max(1, int(str_interval))
        self.str_timer.start(self.str_interval)

    def set_blink_interval(self, blink_interval:int):
        self.blink_interval = max(50, int(blink_interval))
        self.cursor_timer.start(self.blink_interval)

    def set_intervals(self, char_interval=None, str_interval=None, blink_interval=None):
        if char_interval:
            self.char_interval = max(1, int(char_interval))
        if str_interval:
            self.str_interval = max(1, int(str_interval))
        if blink_interval:
            self.blink_interval = max(50, int(blink_interval))
            self.cursor_timer.start(self.blink_interval)

    def pause_animation(self):
        self.char_timer.stop()
        self.str_timer.stop()

    def resume_animation(self):
        if not self.is_finished:
            self.char_timer.start(self.char_interval)

    def stop_animation(self):
        self.char_timer.stop()
        self.str_timer.stop()
        super().setText("")
        self.update()

    def add_text(self, text: str):
        if text and text not in self.datas:
            self.datas.append(text)

    # ---------- 내부 로직 ----------
    def setup_ui(self):
        self.setMinimumSize( self.kwargs.get('min_width', 600), self.kwargs.get('min_height', 30))
        self.setFixedHeight(self.kwargs.get('height', 30))
        self.setFixedWidth(self.kwargs.get('width', 600))

    def _apply_alignment(self):
        if self._use_painter():
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 배경만
        else:
            self.setAlignment(self.position_map.get(self.position, Qt.AlignmentFlag.AlignCenter))

    def _use_painter(self) -> bool:
        return self.position == "fixed_center"

    def _start_animation(self, text: str):
        self.full_text = text or ""
        self.current_show_char_index = 0
        self.is_finished = False
        if not self._use_painter():
            super().setText("")
        self.char_timer.start(self.char_interval)
        self.update()

    def _show_next_char(self):
        if self.current_show_char_index < len(self.full_text):
            self.current_show_char_index += 1
            if self._use_painter():
                # 문자열은 paintEvent에서 그림
                self.update()
            else:
                self._update_label_text()
        else:
            self.char_timer.stop()
            self.is_finished = True
            self.str_timer.start(self.str_interval)

    def _next_text(self):
        if not self.datas:
            return
        self.current_text_index += 1
        if self.current_text_index >= len(self.datas):
            self.current_text_index = 0
            self.current_loop += 1
            if self.loop != -1 and self.current_loop >= self.loop:
                self.stop_animation()
                return
        self._start_animation(self.datas[self.current_text_index])

    def _toggle_cursor(self):
        self.cursor_visible = not self.cursor_visible
        if self._use_painter():
            self.update()
        else:
            # 현재 텍스트에 커서만 토글
            self._update_label_text()

    def _visible_part(self) -> str:
        return self.full_text[:self.current_show_char_index]

    def _update_label_text(self):
        # label 경로: 텍스트 문자열 자체에 커서를 덧붙인다
        base = self._visible_part()
        if not self.is_finished and self.cursor_visible:
            super().setText(base + self.cursor_char)
        else:
            super().setText(base)

    # ---------- 페인팅 ----------
    def paintEvent(self, event):
        if not self._use_painter():
            # 기본 라벨 렌더링 경로
            return super().paintEvent(event)

        # fixed_center: 직접 그리기 (앵커 고정)
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        fm = QFontMetrics(self.font())

        full_w = fm.horizontalAdvance(self.full_text)
        visible = self._visible_part()
        vis_w = fm.horizontalAdvance(visible)

        # 고정 앵커: 라벨 중앙에 전체문장을 중앙정렬한 것과 동일한 왼쪽 x
        anchor_x = (self.width() - full_w) / 2.0
        baseline_y = (self.height() + fm.ascent() - fm.descent()) / 2.0

        # 1) 현재까지 타이핑된 부분을 그린다
        painter.drawText(int(anchor_x), int(baseline_y), visible)

        # 2) 커서 (끝 좌표에 붙인다)
        if not self.is_finished and self.cursor_visible:
            cursor_x = anchor_x + vis_w
            painter.drawText(int(cursor_x), int(baseline_y), self.cursor_char)


# class DemoWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("타자기 스타일 텍스트 애니메이션")

#         layout = QVBoxLayout()

#         self.label = TypewriterLabel(self, datas=["영화처럼 한 글자씩 나타나는 효과!", '2번째 문장으로, 📌  😄 표시하는데 어떻게 될까...ㅜㅜ;;'], char_interval=200, position="fixed_center")
#         layout.addWidget(self.label)

#         btn_start = QPushButton("애니메이션 시작")
#         btn_start.clicked.connect(lambda: self.label.start_animation())
#         layout.addWidget(btn_start)

#         self.setLayout(layout)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = DemoWindow()
#     window.resize(500, 200)
#     window.show()
#     sys.exit(app.exec())