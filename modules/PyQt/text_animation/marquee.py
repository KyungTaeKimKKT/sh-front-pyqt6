from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()
import time

class Marquee(QLabel):
    directions = ['left', 'right', 'up', 'down']

    def __init__(self, parent=None, 
                 direction='left', 
                 speed = 3, 
                 loop=-1, 
                 text='시범용 test입니다',
                 datas:Optional[list[str]]=[],
                 pause_duration=3000,
                 flow_interval=16,
                 **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.datas = datas
        self.current_text_index = 0
        self.direction = direction if direction in self.directions else 'left'
        self.speed = max(1, speed)
        self.loop = loop
        self.current_loop = 0
        self.paused = False
        self.pause_duration = pause_duration
        self.flow_interval = flow_interval

        self.offset_x = 0
        self.offset_y = 0

        self.document = QTextDocument(self)
        self.document.setUseDesignMetrics(True)

        self.style_sheet = kwargs.get('style_sheet', "background-color: white;color:black;font-weight:bold;")

        self.init_timer()

        self.setup_ui()

        self.text = text
        if text:
            if text not in self.datas:
                self.datas.append(text)
            self.current_text_index = self.datas.index(text)   

        if self.datas:
            self.setText( self.datas[self.current_text_index])

    def add_text(self, text:str):
        if text not in self.datas:
            self.datas.append(text)
            self.current_text_index = len(self.datas) - 1
            self.setText(text)


    def set_direction(self, direction:str):
        self.direction = direction if direction in self.directions else 'left'
        self.reset_position()

    def set_speed(self, speed:int):
        self.speed = max(1, speed)
        self.reset_position()

    def set_loop(self, loop:int):
        self.loop = loop
        self.reset_position()

    def set_pause_duration(self, pause_duration:int):
        self.pause_duration = pause_duration
        self.stop_timer()
        self.init_timer()   
        self.reset_position()

    def set_flow_interval(self, flow_interval:int):
        self.flow_interval = flow_interval
        self.stop_timer()
        self.init_timer()   
        self.reset_position()

    def init_timer(self):
        if not hasattr(self, 'flow_timer'):
            self.flow_timer = QTimer(self)
            self.flow_timer.timeout.connect(self.update_position)
        if not hasattr(self, 'pause_timer'):
            self.pause_timer = QTimer(self)
            self.pause_timer.setSingleShot(True)
            self.pause_timer.timeout.connect(self.resume_flow)

        self.is_paused_at_center = False
        self.center_pause_handled = False
        self.last_pause_offset = None

        self.flow_timer.setInterval(self.flow_interval)
        self.flow_timer.start()

    def stop_timer(self):
        self.flow_timer.stop()
        self.pause_timer.stop()

    def pause_at_center(self):
        self.is_paused_at_center = True
        self.center_pause_handled = True
        self.flow_timer.stop()
        self.pause_timer.start(self.pause_duration)

    def resume_flow(self):
        self.is_paused_at_center = False
        self.flow_timer.start()


    def setup_ui(self):
        self.setMinimumSize( self.kwargs.get('min_width', 600), self.kwargs.get('min_height', 30))
        self.setFixedHeight(self.kwargs.get('height', 30))
        self.setFixedWidth(self.kwargs.get('width', 600))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(self.style_sheet)

    def loop_finished(self):
        if self.loop == -1:
            self.reset_position()
        else:
            self.current_loop += 1
            if self.current_loop >= self.loop:
                self.timer.stop()
            else:
                self.reset_position()

    

    def setText(self, text):
        super().setText('')  # QLabel 기본 텍스트는 빈값으로
        # 텍스트를 두 번 반복하여 무한 스크롤 효과
       
        self.document.setPlainText(text)
        self.document.setDefaultFont(self.font())

        self.reset_position()

    def next_text(self):
        self.current_text_index += 1
        if self.current_text_index >= len(self.datas):
            self.current_text_index = 0
            self.current_loop += 1
            if self.loop != -1 and self.current_loop >= self.loop:
                self.stop_timer()
                return
        self.setText(self.datas[self.current_text_index])


    def reset_position(self):
        doc_size = self.document.size()
        width = doc_size.width()
        height = doc_size.height()

        if self.direction == 'left':
            # 텍스트가 완전히 오른쪽 밖에서 시작 (오른쪽 끝 위치)
            self.offset_x = self.width()
            self.offset_y = 0
        elif self.direction == 'right':
            # 텍스트가 완전히 왼쪽 밖에서 시작 (음수 폭만큼 왼쪽)
            self.offset_x = -width
            self.offset_y = 0
        elif self.direction == 'up':
            # 텍스트가 아래쪽 밖에서 시작
            self.offset_y = self.height()
            self.offset_x = 0
        elif self.direction == 'down':
            # 텍스트가 위쪽 밖에서 시작
            self.offset_y = -height
            self.offset_x = 0

    def update_position(self):
        if self.is_paused_at_center:
            return

        doc_size = self.document.size()
        width = doc_size.width()
        height = doc_size.height()

        center_x = (self.width() - width) / 2
        center_y = (self.height() - height) / 2

        # 이동
        if self.direction == 'left':
            self.offset_x -= self.speed

            # 중앙 도달 판단 - 한번만 멈추도록 제어
            if (not self.center_pause_handled
                and abs(self.offset_x - center_x) < self.speed):
                self.pause_at_center()
                self.last_pause_offset = self.offset_x

            # 멈춘 뒤 충분히 움직였는지 체크해 플래그 리셋
            if self.center_pause_handled and abs(self.offset_x - self.last_pause_offset) > self.speed * 2:
                self.center_pause_handled = False

            # 화면 밖 나가면 리셋
            if self.offset_x + width < 0:
                self.next_text()

        elif self.direction == 'right':
            self.offset_x += self.speed

            if (not self.center_pause_handled
                and abs(self.offset_x - center_x) < self.speed):
                self.pause_at_center()
                self.last_pause_offset = self.offset_x

            if self.center_pause_handled and abs(self.offset_x - self.last_pause_offset) > self.speed * 2:
                self.center_pause_handled = False

            if self.offset_x > self.width():
                self.next_text()

        elif self.direction == 'up':
            self.offset_y -= self.speed

            if (not self.center_pause_handled
                and abs(self.offset_y - center_y) < self.speed):
                self.pause_at_center()
                self.last_pause_offset = self.offset_y

            if self.center_pause_handled and abs(self.offset_y - self.last_pause_offset) > self.speed * 2:
                self.center_pause_handled = False

            if self.offset_y + height < 0:
                self.next_text()

        elif self.direction == 'down':
            self.offset_y += self.speed

            if (not self.center_pause_handled
                and abs(self.offset_y - center_y) < self.speed):
                self.pause_at_center()
                self.last_pause_offset = self.offset_y

            if self.center_pause_handled and abs(self.offset_y - self.last_pause_offset) > self.speed * 2:
                self.center_pause_handled = False

            if self.offset_y > self.height():
                self.next_text()

        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        
        doc_size = self.document.size()
        w, h = self.width(), self.height()
        
        if self.direction in ['left', 'right']:
            # 수직 중앙 정렬, x는 offset_x 이동
            offset_y = (h - doc_size.height()) / 2
            painter.translate(self.offset_x, offset_y)
        elif self.direction in ['up', 'down']:
            # 수평 중앙 정렬, y는 offset_y 이동
            offset_x = (w - doc_size.width()) / 2
            painter.translate(offset_x, self.offset_y)

        self.document.drawContents(painter)
