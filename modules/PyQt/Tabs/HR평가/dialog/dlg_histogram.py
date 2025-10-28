from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm


import json, os, io, copy
import platform
from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

def get_font_family():
    return 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic' if platform.system() == 'macOS' else 'NanumGothic'

import matplotlib
matplotlib.rcParams['font.family'] = get_font_family()
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지


class HistogramWidget(QWidget):
    """ kwargs 로 파라미터 전달 가능 
        title: str, win_width: int, win_height: int,

        data_dict: dict[int,float]
    """
    def __init__(self, parent=None, data_dict:dict[int,float] = None, **kwargs):
        super().__init__(parent)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.combo_text = ["인원 수", "정규분포(빈도)"]
        self.default_text = "인원 수"

        self.data_dict = data_dict or {}
        self.y_mode = self.default_text  # 또는 "빈도"

        self._mpl_cid = None

        self._init_ui()
        self.plot_histogram()

        self.combo_y_mode.setCurrentText(self.default_text)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        combo_container = QWidget()
        combo_container.setFixedHeight(50)  # ← 높이 고정
        combo_container_h_layout = QHBoxLayout(combo_container)
        combo_container_h_layout.setContentsMargins(0, 0, 0, 0)  # ← 여백 최소화
        combo_container_h_layout.setSpacing(10)  # ← 간격 약간 주기
        label = QLabel("y축 표시 선택 : ")
        combo_container_h_layout.addWidget(label)
        self.combo_y_mode = QComboBox()
        self.combo_y_mode.addItems(self.combo_text)
        self.combo_y_mode.currentTextChanged.connect(self.on_y_mode_changed)
        combo_container_h_layout.addWidget(self.combo_y_mode)
        combo_container_h_layout.addStretch()
        layout.addWidget(combo_container)

        self.label_info = QLabel("평가 점수 구간 클릭 시 해당 인원 목록 표시됩니다.")
        self.label_info.setStyleSheet("font-size: 12px; background-color: gray; color: white;")
        layout.addWidget(self.label_info)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
    

    def on_y_mode_changed(self, mode: str):
        self.y_mode = mode
        self.plot_histogram()

    def plot_histogram(self):
        self.ax.clear()
        values = list(self.data_dict.values())
        self.user_ids = list(self.data_dict.keys())  # 사용자 ID 보존

        # 히스토그램 bin 설정
        bins = np.arange(0, 4.2, 0.2)
        bin_width = bins[1] - bins[0]

        # 히스토그램
        counts, bins, self.patches = self.ax.hist(
            values,
            bins=bins,
            density= bool(self.y_mode == "정규분포(빈도)"),
            alpha=0.6,
            edgecolor="black",
            label="히스토그램"
        )

        # 정규분포 곡선
        mean = np.mean(values)
        std = np.std(values)
        x = np.linspace(min(bins), max(bins), 500)
        if self.y_mode == "정규분포(빈도)":
            y = norm.pdf(x, mean, std)
        else:
            y = norm.pdf(x, mean, std) * len(values) * bin_width  # 인원 수 scale

        self.ax.plot(x, y, color='red', linewidth=2, label="정규분포 곡선" )

        # 라벨
        self.ax.set_title("종합 평가 점수 분포")
        self.ax.set_xlabel("평가 점수")
        self.ax.set_ylabel("정규분포(빈도)" if self.y_mode == "정규분포(빈도)" else "인원 수")
        self.ax.legend()

        # 평균 수직선 + 텍스트 표시
        self.ax.axvline(mean, color='blue', linestyle='--', label=f'평균: {mean:.2f}')
        # 먼저 y축 범위 구함
        ymin, ymax = self.ax.get_ylim()
        text_y = ymax * 0.98  # y축 최상단 근처

        self.ax.text(
            mean, text_y, f'평균={mean:.2f}',
            ha='center', va='top',
            color='black', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", alpha=0.8)
        )
        
        self.canvas.draw()

        # 이벤트 연결
        if self._mpl_cid is None:
            self._mpl_cid = self.canvas.mpl_connect("button_press_event", self.on_click_bar)


    def on_click_bar(self, event):
        if event.inaxes != self.ax:
            return

        for i, patch in enumerate(self.patches):
            x0 = patch.get_x()
            x1 = x0 + patch.get_width()
            if x0 <= event.xdata <= x1:
                # 해당 구간 범위 추출
                score_min, score_max = x0, x1
                selected_users = [
                    INFO.USER_MAP_ID_TO_USER[uid]['user_성명'] for uid, score in self.data_dict.items()
                    if score_min <= score < score_max
                ]
                # 표시: 예시 - 팝업
                from PyQt6.QtWidgets import QMessageBox
                msg = f"점수 구간: {score_min:.1f} ~ {score_max:.1f}\n해당 인원 수: {len(selected_users)}\n\nUser ID 목록:\n{selected_users}"
                QMessageBox.information(self, "선택된 구간 정보", msg)
                break


class HistogramDialog(QDialog):
    def __init__(self, parent=None, data_dict:dict[int,float] = None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle( self.title if hasattr(self, 'title') else "종합평가 분포")
        self.resize( self.win_width if hasattr(self, 'win_width') else 800, self.win_height if hasattr(self, 'win_height') else 600)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(HistogramWidget(parent=self, data_dict=data_dict, **kwargs))
        self.setLayout(self.layout)


class Dlg_상급자_종합평가_제출_확인(QDialog):
    def __init__(self, parent=None, data_dict:dict[int,float] = None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("상급자 종합평가 제출 확인")
        self.resize( 800, 600)

        self.layout = QVBoxLayout(self)        


        # --- 버튼 컨테이너
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        # Label
        self.label_info = QLabel("제출 시 모든 평가 점수가 확정됩니다. 계속하시겠습니까?")
        self.label_info.setStyleSheet("font-size: 12px; background-color: black; color: yellow;")
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_layout.addWidget(self.label_info)

        # Spacing between label and buttons
        btn_layout.addSpacing(20)

        # OK Button
        self.PB_OK = QPushButton("제출 확인")
        self.PB_OK.setFixedWidth(100)
        self.PB_OK.clicked.connect(self.accept)
        btn_layout.addWidget(self.PB_OK)

        # Cancel Button
        self.PB_Cancel = QPushButton("취소")
        self.PB_Cancel.setFixedWidth(100)
        self.PB_Cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.PB_Cancel)

        self.layout.addWidget(btn_container)

        # Histogram Widget 아래에 삽입


        self.layout.addWidget(HistogramWidget(parent=self, data_dict=data_dict, **kwargs))
        self.setLayout(self.layout)