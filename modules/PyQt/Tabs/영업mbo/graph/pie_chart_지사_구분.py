from __future__ import annotations
from typing import Optional, TYPE_CHECKING,  Any, Union

from modules.common_import_v2 import *
from modules.common_graphic_import import *

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class PieChartDataManager:
    def __init__(self):
        self.df = None

    def load_data(self, datas: list[dict]):
        self.df = pd.DataFrame(copy.deepcopy(datas))

    def get_departments(self):
        return self.df["부서"].unique().tolist()

    def get_valid_months(self):
        valid_months = []
        실적_df = self.df[(self.df["구분"] != "TOTAL") & (self.df["분류"] == "실적")]
        for i in range(1, 13):
            col = f"month_{i:02d}"
            if 실적_df[col].apply(pd.to_numeric, errors="coerce").fillna(0).sum() > 0:
                valid_months.append(f"{i:02d}")
        return valid_months

    def filter_data(self, dept, month_text):
        month = "합계" if month_text == "누적" else f"month_{month_text}"
        data = self.df[
            (self.df["부서"] == dept) & 
            (self.df["구분"] != "TOTAL") & 
            (self.df["분류"] == "실적")
        ][["구분", month]].copy()
        data[month] = pd.to_numeric(data[month], errors="coerce").fillna(0) / 1e8
        return data, month

    def get_goal_and_rate(self, dept, month_text, month):
        목표금액 = self.df[
            (self.df["부서"] == dept) &
            (self.df["구분"] == "TOTAL") &
            (self.df["분류"] == "계획")
        ]
        달성률 = self.df[
            (self.df["부서"] == dept) &
            (self.df["구분"] == "TOTAL") &
            (self.df["분류"] == "달성률")
        ]
        실적_df = self.df[
                (self.df["부서"] == dept) &
                (self.df["구분"] != "TOTAL") &
                (self.df["분류"] == "실적")
            ]

        if month_text == "누적":
            month_cols = [f"month_{i:02d}" for i in range(1, 13)]

            실적_sum = 실적_df[month_cols].astype(float).sum()
            유효_월 = 실적_sum[실적_sum > 0].index.tolist()
            if 유효_월:
                목표값 = 목표금액[유효_월].astype(float).sum(axis=1).values[0] / 1e8 if not 목표금액.empty else 0
                실적값 = 실적_sum[유효_월].astype(float).sum() / 1e8 if not 실적_sum.empty else 0
                달성률값 = 실적값 / 목표값 * 100 if 목표값 > 0 else 0
            else:
                목표값 = 달성률값 = 0
                실적값 = 0
        else:
            목표값 = 목표금액[month].astype(float).values[0] / 1e8 if not 목표금액.empty else 0
            달성률값 = 달성률[month].astype(float).values[0] if not 달성률.empty else 0
            실적값 = 실적_df[month].astype(float).values[0] / 1e8 if not 실적_df.empty else 0
        return 목표값, 실적값, 달성률값

class PieChartRenderer:
    def __init__(self, ax: Axes):
        self.ax: Axes = ax
        self.canvas = ax.figure.canvas
        self._cid =  None

        self._wedges = []
        self._labels = []
        self._values = []
        self._total = 0


    # ---------- 계산 관련 메서드 ----------
    def _compute_scale(self) -> Tuple[float, float]:
        """figure 크기 기반 scale과 fontsize 산출"""
        fig_w, fig_h = self.ax.figure.get_size_inches() * self.ax.figure.dpi
        scale: float = min(fig_w, fig_h) / 400  # 기준 400px
        return scale, max(8, 12 * scale)

    def _make_title(self, dept: str, month_text: str, fontsize: float) -> Tuple[str, float]:
        """타이틀 반환"""
        if month_text == "누적":
            return f"{dept} - 누적", fontsize * 1.2
        return f"{dept} - {int(month_text)}월 실적 분포", fontsize * 1.2

    def _make_center_text(self, 목표값: float, 실적값: float, 달성률값: float) -> str:
        """중앙 텍스트 반환"""
        return f"목표: {목표값:.1f}억\n실적: {실적값:.1f}억\n달성률: {달성률값:.1f}%"
    
    # ---------- 클릭 이벤트 ----------

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return
        for i, w in enumerate(self._wedges):
            contains, _ = w.contains(event)
            if contains:
                label = self._labels[i]
                value = self._values[i]
                pct = value / self._total * 100 if self._total > 0 else 0
                QMessageBox.information(
                    self.canvas.parent(), "상세 정보",
                    f"{label}\n{pct:.1f}% ({value:.1f}억)"
                )
                break

    # ---------- 렌더링 보조 메서드 ----------
    def _draw_pie(
        self,
        values,  # 보통 pandas.Series
        labels,  # 보통 list[str] 또는 pd.Series
        fontsize: float,
        total: float,
        adaptive: bool = True
    ) -> None:
        """adaptive 모드 piechart 렌더링"""
        fig_w, fig_h = self.ax.figure.get_size_inches() * self.ax.figure.dpi

        if adaptive and (fig_w < 250 or fig_h < 250):
            # 작은 경우 → legend 사용, unpack error 방지
            result = self.ax.pie(values, startangle=140)
            if len(result) == 2:
                wedges, texts = result
                autotexts = []
            else:
                wedges, texts, autotexts = result

            self.ax.legend(
                wedges, labels, loc="center left",
                bbox_to_anchor=(1, 0.5), fontsize=fontsize*0.9
            )
        else:
            wedges, texts, autotexts = self.ax.pie(
                values,
                labels=labels,
                autopct=lambda p: f"{p:.1f}%\n({p*total/100:.1f} 억)",
                startangle=140
            )
            for t in texts + autotexts:
                t.set_fontsize(fontsize)
            # 예: 특정 label 강조
            for i, label in enumerate(labels):
                if label == "MOD":
                    autotexts[i].set_color("white")

        # _draw_pie 끝에
        self._wedges = wedges
        self._labels = list(labels)
        self._values = list(values)
        self._total = total


    def _draw_center(self, text: str, fontsize: float) -> None:
        """중앙 원 + 텍스트"""
        circle = plt.Circle((0, 0), 0.35, color='yellow', zorder=2,
                            transform=self.ax.transData, clip_on=False)
        self.ax.add_artist(circle)
        self.ax.text(0, 0, text,
                     ha='center', va='center',
                     fontsize=fontsize * 1.1, weight='bold', zorder=3)

    # ---------- 메인 렌더링 ----------
    def render(
        self,
        data,       # 보통 pandas.DataFrame
        month: str, # '1', '2', ... 또는 '누적'
        dept: str,
        month_text: str,
        목표값: float,
        실적값: float,
        달성률값: float
    ) -> None:
        self.ax.clear()
        self.ax.set_aspect('equal')

        scale, fontsize = self._compute_scale()
        values = data[month]
        total = values.sum()

        if total == 0:
            self.ax.text(0.5, 0.5, "실적 데이터 없음",
                         ha='center', va='center',
                         fontsize=fontsize, transform=self.ax.transAxes)
        else:
            self._draw_pie(values, data["구분"], fontsize, total)
            #### draw 후 클릭 이벤트 연결
            if self._cid is not None:
                print("disconnect: ", self._cid)
                self.canvas.mpl_disconnect(self._cid)
            self._cid = self.canvas.mpl_connect("button_press_event", self._on_click)

        # 중앙 텍스트 + 배경
        center_text = self._make_center_text(목표값, 실적값, 달성률값)
        self._draw_center(center_text, fontsize)

        # 타이틀
        title, title_fontsize = self._make_title(dept, month_text, fontsize)
        self.ax.set_title(title, fontsize=title_fontsize)

        self.ax.figure.tight_layout()


class PieChartWidget(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self._cid = None
        self.kwargs = kwargs
        self.data_manager = PieChartDataManager()
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        layout = QVBoxLayout(self)
        h_layout = QHBoxLayout()
        h_layout.addStretch()    # 왼쪽 여백
        h_layout.addWidget(QLabel('부서 선택 :'))
        self.dept_combo = Custom_Combo(self)
        h_layout.addWidget(self.dept_combo)
        h_layout.addSpacing(16*2)

        h_layout.addWidget(QLabel('월별 선택 :'))
        self.month_combo = Custom_Combo(self)
        h_layout.addWidget(self.month_combo)
        h_layout.addStretch()    # 오른쪽 여백
        layout.addLayout(h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.ax = self.canvas.figure.add_subplot(111)
        layout.addWidget(self.canvas)

    def connect_signals(self):
        self.dept_combo.currentTextChanged.connect(self.update_chart)
        self.month_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.dept_combo.currentTextChanged.disconnect()
            self.month_combo.currentTextChanged.disconnect()
        except:
            pass

    def set_data(self, datas):
        self.data_manager.load_data(datas)
        self.dept_combo.clear()
        self.dept_combo.addItems(self.data_manager.get_departments())
        self.month_combo.clear()
        self.month_combo.addItems(['누적'] + self.data_manager.get_valid_months())
        self.update_chart()

    def update_chart(self):
        dept = self.dept_combo.currentText()
        month_text = self.month_combo.currentText()
        if not dept or not month_text:
            return
        data, month = self.data_manager.filter_data(dept, month_text)
        목표값, 실적값, 달성률값 = self.data_manager.get_goal_and_rate(dept, month_text, month)

        self.renderer = PieChartRenderer(self.ax)
        self.renderer.render(data, month, dept, month_text, 목표값, 실적값, 달성률값)
        self.canvas.draw()

        # #### draw 후 클릭 이벤트 연결
        # if self._cid is not None:
        #     print("disconnect: ", self._cid)
        #     self.canvas.mpl_disconnect(self._cid)
        # self._cid = self.canvas.mpl_connect("button_press_event", self.renderer._on_click)


# class PieChartWidget(QWidget):
#     def __init__(self , parent: QWidget=None, **kwargs ):
#         super().__init__(parent)
#         self.df: pd.DataFrame = None
#         self.datas: list[dict] = None
#         self.prev_datas = None
#         self.dept_combo_itmes = None
#         self.prev_dept_combo_itmes = None
#         self.month_combo_itmes = None
#         self.prev_month_combo_itmes = None

#         self.initialized = False

#         self.default_dept_combo_text = "회사계"
#         self.default_month_combo_text = "누적"


#     def run( self):
#         set_korean_font()
#         self.init_ui()
#         self.connect_signals()
#             # self.test_process()

#     def stop(self):
#         self.timer.stop()

#     def set_initial_values(self):
#         self.disconnect_signals()

#         self.dept_combo_items = self.df["부서"].unique()
#         self.dept_combo.clear()
#         self.dept_combo.addItems(self.dept_combo_items)

#         self.init_month_combo()

#         prev_dept_combo_text = self.dept_combo.currentText() if self.initialized else self.default_dept_combo_text
#         prev_month_combo_text = self.month_combo.currentText() if self.initialized else self.default_month_combo_text

#         self.dept_combo.setCurrentText(prev_dept_combo_text)
#         self.month_combo.setCurrentText(prev_month_combo_text)
        
#         self.update_chart()
#         self.connect_signals()                
#         self.initialized = True

#     def on_apply_api_datas(self, datas: list[dict]):
#         """실질적인 run 함수"""
#         self.prev_datas = copy.deepcopy(self.datas)
#         self.datas = copy.deepcopy(datas)
#         if self.prev_datas and self.prev_datas == self.datas:
#             return

#         self.df = pd.DataFrame(self.datas)
#         self.set_initial_values()

#     def init_ui(self):
#         from modules.PyQt.compoent_v2.custom_상속.custom_combo import  Custom_Combo
#         self.layout = QVBoxLayout(self)

#         self.h_layout = QHBoxLayout()
#         self.h_layout.addStretch()
#         self.h_layout.addWidget(QLabel('부서 선택 : '))

#         self.dept_combo = Custom_Combo(self)
#         self.h_layout.addWidget(self.dept_combo)

#         self.h_layout.addStretch()
#         self.h_layout.addWidget(QLabel('월별 선택 : '))

#         self.month_combo = Custom_Combo(self)
#         self.h_layout.addWidget(self.month_combo)
#         self.h_layout.addStretch()

#         self.layout.addLayout(self.h_layout)

#         self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
#         self.canvas.setMinimumSize(200, 200)
#         self.ax = self.canvas.figure.add_subplot(111)
#         self.layout.addWidget(self.canvas)
#         self.show()


#     def init_month_combo(self):
#         valid_months = []
#         실적_df = self.df[(self.df["구분"] != "TOTAL") & (self.df["분류"] == "실적")]

#         for i in range(1, 13):
#             col = f"month_{i:02d}"
#             if 실적_df[col].apply(pd.to_numeric, errors="coerce").fillna(0).sum() > 0:
#                 valid_months.append(f"{i:02d}")

#         self.month_combo.addItems(['누적'] + valid_months)

#     def connect_signals(self):
#         self.dept_combo.currentTextChanged.connect(self.update_chart)
#         self.month_combo.currentTextChanged.connect(self.update_chart)

#     def disconnect_signals(self):
#         try:
#             self.dept_combo.currentTextChanged.disconnect()
#             self.month_combo.currentTextChanged.disconnect()
#         except:
#             pass

#     def update_chart(self):
#         dept = self.dept_combo.currentText()
#         month_text = self.month_combo.currentText()
#         month = "합계" if month_text == "누적" else f"month_{month_text}"
#         print ( dept, month_text, month )

#         data = self.df[
#             (self.df["부서"] == dept) & 
#             (self.df["구분"] != "TOTAL") & 
#             (self.df["분류"] == "실적")
#         ][["구분", month]].copy()

#         data[month] = pd.to_numeric(data[month], errors="coerce").fillna(0)
#         data[month] = data[month] / 1e8  # 억 원 단위
#         print ( data )
#         self.ax.clear()
#         try:
#             self.ax.set_aspect('equal')  # 이 줄을 추가하여 비율을 설정합니다.
#         except:
#             pass
#         if data[month].sum() == 0:
#             self.ax.text(0.5, 0.5, "실적 데이터 없음", ha='center', va='center', fontsize=14)
#         else:
#             wedges, texts, autotexts = self.ax.pie(
#                 data[month], 
#                 labels=data["구분"],
#                 autopct=lambda p: f"{p:.2f}%\n({p * data[month].sum() / 100:.2f} 억)",
#                 startangle=140,
#                 wedgeprops={'zorder': 1}  # 낮은 zorder로 설정
#             )

#         # 색상 수정: MOD는 글자색 흰색으로
#         for i, label in enumerate(data["구분"]):
#             if label == "MOD":
#                 autotexts[i].set_color("white")

#         # 타이틀 처리
#         if month_text == "누적":
#             # 누적일 경우, 마지막 실적이 있는 월까지
#             last_valid_month = 0
#             for i in range(1, 13):
#                 col = f"month_{i:02d}"
#                 subset = self.df[
#                     (self.df["부서"] == dept) &
#                     (self.df["구분"] != "TOTAL") &
#                     (self.df["분류"] == "실적")
#                 ]
#                 if pd.to_numeric(subset[col], errors="coerce").fillna(0).sum() > 0:
#                     last_valid_month = i

#             title_month = f"(1월~{last_valid_month}월)" if last_valid_month > 0 else ""
#         else:
#             title_month = f"({int(month_text)}월)"


#         # 목표 금액과 달성률 표시 (중앙 텍스트)
#         목표금액 = self.df[
#             (self.df["부서"] == dept) &
#             (self.df["구분"] == "TOTAL") &  # 목표 기준은 TOTAL 기준으로
#             (self.df["분류"] == "계획")
#         ]

#         달성률 = self.df[
#             (self.df["부서"] == dept) &
#             (self.df["구분"] == "TOTAL") &
#             (self.df["분류"] == "달성률")
#         ]

#         # 월 선택 (누적이면 합계, 아니면 해당 month)
#         if month_text == "누적":
#          # 누적 실적 기준으로 유효한 월 결정
#             실적_df = self.df[
#                 (self.df["부서"] == dept) &
#                 (self.df["구분"] != "TOTAL") &
#                 (self.df["분류"] == "실적")
#             ]
#             month_cols = [f"month_{i:02d}" for i in range(1, 13)]
#             실적_sum = 실적_df[month_cols].astype(float).sum()
#             유효_월 = 실적_sum[실적_sum > 0].index.tolist()  # 실적이 있는 월만

#             if 유효_월:
#                 누적_월들 = 유효_월
#                 목표값 = 목표금액[누적_월들].astype(float).sum(axis=1).values[0] / 1e8 if not 목표금액.empty else 0
#                 달성률값 = 달성률[누적_월들].astype(float).sum(axis=1).values[0] / len(누적_월들) if not 달성률.empty else 0
#                 title_text = f"{dept} - 누적 ({int(누적_월들[0][-2:])}월~{int(누적_월들[-1][-2:])}월)"
#             else:
#                 목표값 = 달성률값 = 0
#                 title_text = f"{dept} - 누적 (데이터 없음)"
#         else:
#             목표값 = 목표금액[month].astype(float).values[0] / 1e8 if not 목표금액.empty else 0
#             달성률값 = 달성률[month].astype(float).values[0] if not 달성률.empty else 0
#             title_text = f"{dept} - {int(self.month_combo.currentText())}월 실적 분포"

#         # 원형 배경 추가
#         circle = plt.Circle((0, 0), 0.35, color='yellow', zorder=2, transform=self.ax.transData, clip_on=False)
#         self.ax.add_artist(circle)

#         # 중앙 텍스트 삽입
#         center_text = f"목표: {목표값:.1f}억\n달성률: {달성률값:.1f}%"
#         self.ax.text(0, 0, center_text, ha='center', va='center', fontsize=11, weight='bold', zorder=3)

#         self.ax.set_title(title_text)
#         self.canvas.draw()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     from datas import datas
#     window = PieChartWidget()
#     window.run(datas=datas)

#     sys.exit(app.exec())
