from __future__ import annotations
from typing import Optional, TYPE_CHECKING,  Any, Union
import sys
import pandas as pd
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as plt
import copy

# import matplotlib
# matplotlib.rcParams['font.family'] = 'NanumGothic'  # Ubuntu/Debian
# matplotlib.rcParams['axes.unicode_minus'] = False

from modules.PyQt.Tabs.영업mbo.graph.set_korean_font import set_korean_font

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class PieChartWidget(QWidget):
    def __init__(self , parent: QWidget=None):
        super().__init__(parent)
        self.df: pd.DataFrame = None
        self.datas: list[dict] = None
        self.prev_datas = None
        self.person_combo_itmes = None
        self.prev_person_combo_itmes = None
        self.month_combo_itmes = None
        self.prev_month_combo_itmes = None

        self.initialized = False

        self.default_person_combo_text = "전체"
        self.default_month_combo_text = "누적"


    def run( self):
        set_korean_font()
        self.init_ui()
        self.connect_signals()

            # self.test_process()

    def stop(self):
        self.timer.stop()

    def set_initial_values(self):
        self.disconnect_signals()

        self.person_combo_items = list(self.df["담당자"].unique())      ##AttributeError: 'numpy.ndarray' object has no attribute 'index'
        if '비정규' in self.person_combo_items:
            del self.person_combo_items[self.person_combo_items.index('비정규')]
        self.person_combo.clear()
        self.person_combo.addItems([self.default_person_combo_text] )

        self.init_month_combo()

        prev_person_combo_text = self.person_combo.currentText() if self.initialized else self.default_person_combo_text
        prev_month_combo_text = self.month_combo.currentText() if self.initialized else self.default_month_combo_text

        self.person_combo.setCurrentText(prev_person_combo_text)
        self.month_combo.setCurrentText(prev_month_combo_text)
        
        self.update_chart()
        self.connect_signals()                
        self.initialized = True

    def on_apply_api_datas(self, datas: list[dict]):
        """실질적인 run 함수"""
        self.prev_datas = copy.deepcopy(self.datas)
        self.datas = copy.deepcopy(datas)
        if self.prev_datas and self.prev_datas == self.datas:
            return

        self.df = pd.DataFrame(self.datas)
        self.set_initial_values()

    def init_ui(self):
        from modules.PyQt.compoent_v2.custom_상속.custom_combo import  Custom_Combo
        # from custom_combo import Custom_Combo
        self.layout = QVBoxLayout(self)

        self.h_layout = QHBoxLayout()
        self.h_layout.addStretch()
        self.h_layout.addWidget(QLabel('부서 선택 : '))

        self.person_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.person_combo)

        self.h_layout.addStretch()
        self.h_layout.addWidget(QLabel('월별 선택 : '))

        self.month_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.month_combo)
        self.h_layout.addStretch()

        self.layout.addLayout(self.h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.canvas.setMinimumSize(200, 200)
        self.ax = self.canvas.figure.add_subplot(111)
        self.layout.addWidget(self.canvas)
        self.show()


    def init_month_combo(self):
        valid_months = []
        실적_df = self.df[(self.df["담당자"] != "전체") & (self.df["분류"] == "실적")]

        for i in range(1, 13):
            col = f"month_{i:02d}"
            if 실적_df[col].apply(pd.to_numeric, errors="coerce").fillna(0).sum() > 0:
                valid_months.append(f"{i:02d}")

        self.month_combo.addItems(['누적'] + valid_months)

    def connect_signals(self):
        self.person_combo.currentTextChanged.connect(self.update_chart)
        self.month_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.person_combo.currentTextChanged.disconnect()
            self.month_combo.currentTextChanged.disconnect()
        except:
            pass

    def update_chart(self):
        dept = self.person_combo.currentText()
        month_text = self.month_combo.currentText()
        month = "합계" if month_text == "누적" else f"month_{month_text}"

        # 데이터 필터링: "전체"는 부서 조건 없이
        data = self.df[
            (self.df["분류"] == "실적")
        ][["담당자", month]].copy()

        if dept != "전체":
            data = data[data["담당자"] == dept]

        # 담당자별 실적 합계
        data = data.groupby("담당자", as_index=False)[month].sum()


        data[month] = pd.to_numeric(data[month], errors="coerce").fillna(0)
        data[month] = data[month] / 1e8  # 억 원 단위


        non_zero_data = data[data[month] > 0]
        zero_data = data[data[month] == 0]

        self.ax.clear()
        # self.ax.set_aspect('equal')  # 이 줄을 추가하여 비율을 설정합니다.


        total_value = data[month].sum()

        if not non_zero_data.empty:
            wedges, texts, autotexts = self.ax.pie(
                non_zero_data[month],
                labels=non_zero_data["담당자"],
                autopct=lambda p: f"{int(round(p))}%" if p > 0 else "",
                startangle=90,
                # wedgeprops=dict(width=0.),
                pctdistance=0.7  # 퍼센트 텍스트를 바깥쪽에 위치시킴
            )

            total = non_zero_data[month].sum()
            self.ax.text(0, 0, f"{total:.1f} 억", ha="center", va="center", fontsize=12, weight="bold")
        else:
            self.ax.text(0.5, 0.5, "실적 데이터 없음", ha="center", va="center", fontsize=14)


        # 타이틀 처리
        if month_text == "누적":
            # 누적일 경우, 마지막 실적이 있는 월까지
            last_valid_month = 0
            for i in range(1, 13):
                col = f"month_{i:02d}"
                subset = self.df[
                    (self.df["분류"] == "실적") &
                    ((self.df["담당자"] == dept) if dept != "전체" else True)
                ]
                if pd.to_numeric(subset[col], errors="coerce").fillna(0).sum() > 0:
                    last_valid_month = i
            
            title_month = f"(1월~{last_valid_month}월)" if last_valid_month > 0 else ""
            title_text = f"{dept} - 누적 {title_month}"
        else:
            title_text = f"{dept} - {int(month_text)}월 실적 분포"

        # 실적 0 담당자: 오른쪽 레전드에 추가
        if not zero_data.empty:
            no_perf_labels = [f"{name} (0억)" for name in zero_data["담당자"]]
            self.ax.legend(
                no_perf_labels,
                title="실적 없음",
                loc="lower right",
                bbox_to_anchor=(1.0, 0.0),  # 오른쪽 아래, 축 바깥
                fontsize=6,           # 기존 9에서 약 60% 수준
                title_fontsize=7.5    # 기존 10에서 약 75% 수준
            )

        # 원형 배경 및 중앙 텍스트 (합계만)
        circle = plt.Circle((0, 0), 0.35, color='yellow', zorder=2, transform=self.ax.transData, clip_on=False)
        self.ax.add_artist(circle)

        center_text = f"{total_value:.1f} 억"
        self.ax.text(0, 0, center_text, ha='center', va='center', fontsize=12, weight='bold', zorder=3)

        self.ax.set_title(title_text)
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from datas import datas
    window = PieChartWidget()
    window.run()
    window.apply_api_datas(datas)

    sys.exit(app.exec())
