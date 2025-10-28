from __future__ import annotations
from typing import Optional, TYPE_CHECKING,  Any, Union

from modules.common_import_v2 import *
from modules.common_graphic_import import *

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class PieChartDataManager:
    def __init__(self):
        self.df: pd.DataFrame = None
        self.datas: list[dict] = None
        self.prev_datas: list[dict] = None

    def apply_api_datas(self, datas: list[dict]) -> bool:
        """새 데이터를 적용하고 변경 여부를 반환"""
        self.prev_datas = copy.deepcopy(self.datas)
        self.datas = copy.deepcopy(datas)

        if self.prev_datas and self.prev_datas == self.datas:
            return False  # 데이터 변화 없음

        self.df = pd.DataFrame(self.datas)
        return True

    def get_unique_departments(self, exclude: list[str] = None) -> list[str]:
        items = list(self.df["부서"].unique())
        if exclude:
            items = [i for i in items if i not in exclude]
        return items

    def get_valid_months(self) -> list[str]:
        valid_months = []
        실적_df = self.df[self.df["부서"] != "전체"]
        for i in range(1, 13):
            col = f"month_{i:02d}"
            if 실적_df[col].apply(pd.to_numeric, errors="coerce").fillna(0).sum() > 0:
                valid_months.append(f"{i:02d}")
        return valid_months

class PieChartRenderer:
    def __init__(self, ax):
        self.ax = ax

    def render(self, df, dept: str, month_text: str):
        month = "합계" if month_text == "누적" else f"month_{month_text}"

        # 데이터 필터링
        data = df[df["분류"] == "실적"][["부서", "고객사", month]].copy()
        if dept != "전체":
            data = data[data["부서"] == dept]

        # 고객사별 합계
        data = data.groupby("고객사", as_index=False)[month].sum()
        data[month] = data[month].apply(pd.to_numeric, errors="coerce").fillna(0) / 1e8

        # 그래프 초기화
        self.ax.clear()
        self.ax.set_aspect('equal')

        total_value = data[month].sum()
        if total_value == 0:
            self.ax.text(0.5, 0.5, "실적 데이터 없음", ha='center', va='center', fontsize=14)
        else:
            wedges, texts, autotexts = self.ax.pie(
                data[month],
                labels=data["고객사"],
                autopct=lambda p: f"{p:.2f}%\n({p * total_value / 100:.2f} 억)",
                startangle=140,
                wedgeprops={'zorder': 1}
            )

        # 타이틀 처리
        if month_text == "누적":
            last_valid_month = 0
            for i in range(1, 13):
                col = f"month_{i:02d}"
                subset = df[(df["분류"] == "실적") & ((df["부서"] == dept) if dept != "전체" else True)]
                if pd.to_numeric(subset[col], errors="coerce").fillna(0).sum() > 0:
                    last_valid_month = i
            title_month = f"(1월~{last_valid_month}월)" if last_valid_month > 0 else ""
            title_text = f"{dept} - 누적 {title_month}"
        else:
            title_text = f"{dept} - {int(month_text)}월 실적 분포"

        # 중앙 원 & 합계
        circle = plt.Circle((0, 0), 0.35, color='yellow', zorder=2, transform=self.ax.transData, clip_on=False)
        self.ax.add_artist(circle)
        self.ax.text(0, 0, f"{total_value:.1f} 억", ha='center', va='center', fontsize=12, weight='bold', zorder=3)
        self.ax.set_title(title_text)


class PieChartWidget(QWidget):
    def __init__(self, parent: QWidget=None, **kwargs):
        super().__init__(parent)
        self.data_manager = PieChartDataManager()
        self.df: pd.DataFrame = None
        self.initialized = False

        self.default_dept_combo_text = "전체"
        self.default_month_combo_text = "누적"

        self.init_ui()
        # self.connect_signals()

    def stop(self):
        pass  # 필요 시 타이머 정리

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.h_layout = QHBoxLayout()

        self.h_layout.addStretch()
        self.h_layout.addWidget(QLabel('부서 선택 : '))
        self.dept_combo = QComboBox(self)
        self.dept_combo.addItems(['전체', '비정규','ㅁㅁㅁ'])
        self.h_layout.addWidget(self.dept_combo)
        print ( f'{self.dept_combo} ' )

        self.h_layout.addStretch()
        self.h_layout.addWidget(QLabel('월별 선택 : '))
        self.month_combo = QComboBox(self)
        self.h_layout.addWidget(self.month_combo)

        self.h_layout.addStretch()

        self.main_layout.addLayout(self.h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.ax = self.canvas.figure.add_subplot(111)
        self.renderer = PieChartRenderer(self.ax)
        self.main_layout.addWidget(self.canvas)
        self.show()

    def connect_signals(self):
        self.dept_combo.currentTextChanged.connect(self.update_chart)
        self.month_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.dept_combo.currentTextChanged.disconnect()
            self.month_combo.currentTextChanged.disconnect()
        except:
            pass

    def on_apply_api_datas(self, datas: list[dict]):

        if self.data_manager.apply_api_datas(datas):
            self.df = self.data_manager.df
            print(f"on_apply_api_datas: {self.df.columns.tolist()}")

            # 1. 콤보박스 채우기
            self.set_initial_values()
           

    def set_initial_values(self):

        self.disconnect_signals()

        if self.initialized:
            prev_dept_combo_text = self.dept_combo.currentText()
            prev_month_combo_text = self.month_combo.currentText()
        else:
            prev_dept_combo_text = self.default_dept_combo_text
            prev_month_combo_text = self.default_month_combo_text


        dept_items = copy.deepcopy(self.data_manager.get_unique_departments(exclude=["비정규"]))
        month_items = copy.deepcopy(['누적'] + self.data_manager.get_valid_months())

        self.dept_combo.clear()
        self.dept_combo.addItems(dept_items)

        self.month_combo.clear()
        self.month_combo.addItems(month_items)

        self.dept_combo.setCurrentIndex( dept_items.index(prev_dept_combo_text) if prev_dept_combo_text in dept_items else 0 )
        self.month_combo.setCurrentIndex(month_items.index(prev_month_combo_text) if prev_month_combo_text in month_items else 0)

        self.update_chart()
        self.connect_signals()
        self.initialized = True

    def update_chart(self):
        dept = self.dept_combo.currentText()
        month_text = self.month_combo.currentText()
        self.renderer.render(self.df, dept, month_text)
        self.canvas.draw()




# class PieChartWidget(QWidget):
#     def __init__(self , parent: QWidget=None):
#         super().__init__(parent)
#         self.df: pd.DataFrame = None
#         self.datas: list[dict] = None
#         self.prev_datas = None
#         self.dept_combo_itmes = None
#         self.prev_dept_combo_itmes = None
#         self.month_combo_itmes = None
#         self.prev_month_combo_itmes = None

#         self.initialized = False

#         self.default_dept_combo_text = "전체"
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

#         self.dept_combo_items = list(self.df["부서"].unique())      ##AttributeError: 'numpy.ndarray' object has no attribute 'index'
#         if '비정규' in self.dept_combo_items:
#             del self.dept_combo_items[self.dept_combo_items.index('비정규')]
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
#         # from custom_combo import Custom_Combo
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
#         실적_df = self.df[(self.df["부서"] != "전체") ]

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

#         # 데이터 필터링: "전체"는 부서 조건 없이
#         data = self.df[
#             (self.df["분류"] == "실적")
#         ][["부서", "고객사", month]].copy()

#         if dept != "전체":
#             data = data[data["부서"] == dept]

#         # 고객사별 실적 합계
#         data = data.groupby("고객사", as_index=False)[month].sum()


#         data[month] = pd.to_numeric(data[month], errors="coerce").fillna(0)
#         data[month] = data[month] / 1e8  # 억 원 단위

#         self.ax.clear()
#         self.ax.set_aspect('equal')  # 이 줄을 추가하여 비율을 설정합니다.


#         total_value = data[month].sum()

#         if total_value == 0:
#             self.ax.text(0.5, 0.5, "실적 데이터 없음", ha='center', va='center', fontsize=14)
#         else:
#             wedges, texts, autotexts = self.ax.pie(
#                 data[month],
#                 labels=data["고객사"],
#                 autopct=lambda p: f"{p:.2f}%\n({p * total_value / 100:.2f} 억)",
#                 startangle=140,
#                 wedgeprops={'zorder': 1}
#             )

#         # 타이틀 처리
#         if month_text == "누적":
#             # 누적일 경우, 마지막 실적이 있는 월까지
#             last_valid_month = 0
#             for i in range(1, 13):
#                 col = f"month_{i:02d}"
#                 subset = self.df[
#                     (self.df["분류"] == "실적") &
#                     ((self.df["부서"] == dept) if dept != "전체" else True)
#                 ]
#                 if pd.to_numeric(subset[col], errors="coerce").fillna(0).sum() > 0:
#                     last_valid_month = i
            
#             title_month = f"(1월~{last_valid_month}월)" if last_valid_month > 0 else ""
#             title_text = f"{dept} - 누적 {title_month}"
#         else:
#             title_text = f"{dept} - {int(month_text)}월 실적 분포"

#         # 원형 배경 및 중앙 텍스트 (합계만)
#         circle = plt.Circle((0, 0), 0.35, color='yellow', zorder=2, transform=self.ax.transData, clip_on=False)
#         self.ax.add_artist(circle)

#         center_text = f"{total_value:.1f} 억"
#         self.ax.text(0, 0, center_text, ha='center', va='center', fontsize=12, weight='bold', zorder=3)

#         self.ax.set_title(title_text)
#         self.canvas.draw()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     from datas import datas
#     window = PieChartWidget()
#     window.run()
#     window.apply_api_datas(datas)

#     sys.exit(app.exec())
