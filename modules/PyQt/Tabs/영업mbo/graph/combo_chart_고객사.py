
import sys
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import copy
import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.rcParams['font.family'] = 'NanumGothic'  # Ubuntu/Debian
# matplotlib.rcParams['axes.unicode_minus'] = False
from modules.PyQt.Tabs.영업mbo.graph.set_korean_font import set_korean_font
# from set_korean_font import set_korean_font
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()
class ComboChartWidget(QWidget):
    def __init__(self , parent: QWidget=None):
        super().__init__(parent)
        self.df: pd.DataFrame = None
        self.datas: list[dict] = None
        self.prev_dept_combo_itmes = None
        self.prev_category_combo_itmes = None
        self.dept_combo_itmes = None
        self.customer_combo_itmes = None

        self.initialized = False

        self.default_dept_combo_text = "전체"
        self.default_category_combo_text ="전체"
        self.init_ui()
        self.connect_signals()


    
    def stop(self):
        self.timer.stop()

    def set_initial_values(self):
        self.disconnect_signals()

        self.dept_combo_items = list(self.df["부서"].unique())
        self.customer_combo_items = list(self.df["고객사"].unique())   
        if '비정규' in self.dept_combo_items:
            del self.dept_combo_items[self.dept_combo_items.index('비정규')]
        
        prev_dept_combo_text = self.dept_combo.currentText() if self.initialized else self.default_dept_combo_text
        prev_category_combo_text = self.customer_combo.currentText() if self.initialized else self.default_category_combo_text

        self.dept_combo.clear()
        self.customer_combo.clear()

        self.dept_combo.addItems(self.dept_combo_items)
        self.customer_combo.addItems(self.customer_combo_items)

        self.dept_combo.setCurrentText(prev_dept_combo_text)
        self.customer_combo.setCurrentText(prev_category_combo_text)

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


    def test_process(self):
        """ timer로 5초씩 변경 """

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.test_click)
        self.timer.start(5000)

    def test_click(self):
                # 현재 선택된 인덱스를 가져옵니다.
        current_dept_index = self.dept_combo.currentIndex()
        current_category_index = self.customer_combo.currentIndex()

        # category_combo의 다음 인덱스를 설정합니다.
        next_category_index = (current_category_index + 1) % self.customer_combo.count()

        # category_combo의 인덱스를 변경합니다.
        self.customer_combo.setCurrentIndex(next_category_index)

        # category_combo가 처음으로 돌아왔을 때, dept_combo의 다음 인덱스로 이동합니다.
        if next_category_index == 0:
            next_dept_index = (current_dept_index + 1) % self.dept_combo.count()
            self.dept_combo.setCurrentIndex(next_dept_index)

    


    def init_ui(self):
        from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo
        # from custom_combo import Custom_Combo
        self.layout = QVBoxLayout(self)

        self.h_layout = QHBoxLayout()
        self.h_layout.addStretch()

        label = QLabel('부서 선택 : ')
        self.h_layout.addWidget(label)

        self.dept_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.dept_combo)
        self.h_layout.addStretch()

        label = QLabel('고객사 선택 : ')
        self.h_layout.addWidget(label)

        self.customer_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.customer_combo)
        self.h_layout.addStretch()

        self.layout.addLayout(self.h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax1 = self.canvas.figure.add_subplot(111)  # 기본 축만 사용
        # self.ax2 = self.ax1.twinx()  # ❌ 삭제

        self.layout.addWidget(self.canvas)

        self.show()



    def connect_signals(self):
        self.dept_combo.currentTextChanged.connect(self.update_chart)
        self.customer_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.dept_combo.currentTextChanged.disconnect(self.update_chart)
            self.customer_combo.currentTextChanged.disconnect(self.update_chart)
        except:
            pass

    def update_chart(self):
        dept = self.dept_combo.currentText()
        customer = self.customer_combo.currentText()
        months = [f"month_{i:02d}" for i in range(1, 13)]
        x = np.arange(1, 13)

        self.ax1.clear()

        def get_data(고객사, 분류):
            if dept == "전체":
                # 전체 부서에서 고객사 + 분류에 해당하는 모든 행을 더함
                d = self.df[(self.df["고객사"] == 고객사) & (self.df["분류"] == 분류)]
                if not d.empty:
                    values = d[months].astype(float).sum(axis=0).values
                    return values / 1e8 if 분류 in ["계획", "실적"] else values
                else:
                    return np.zeros(12)
            else:
                # 특정 부서만 필터링
                d = self.df[(self.df["부서"] == dept) & (self.df["고객사"] == 고객사) & (self.df["분류"] == 분류)]
                if not d.empty:
                    values = d[months].astype(float).values[0]
                    return values / 1e8 if 분류 in ["계획", "실적"] else values
                else:
                    return np.zeros(12)
            
        def get_scale_max(dept, customer):
            if dept == "전체":
                match customer:
                    case "현대EL": return 10
                    case "OTIS": return 10
                    case "TKE": return 10
                    case "기타": return 10
                    case "전체": return 25
            else:
                match customer:
                    case "현대EL": return 10
                    case "OTIS": return 10
                    case "TKE": return 10
                    case "기타": return 10
                    case "전체": return 15

        width = 0.35

        if customer =="전체":
            실적_현대EL = get_data("현대EL", "실적")
            실적_OTIS = get_data("OTIS", "실적")
            실적_TKE = get_data("TKE", "실적")
            실적_기타 = get_data("기타", "실적")

            x1 = x - width / 2
            x2 = x + width / 2


            self.ax1.bar(x2, 실적_현대EL, width=width, label="실적(현대EL)", color='lightgreen')
            self.ax1.bar(x2, 실적_OTIS, width=width, bottom=실적_현대EL, label="실적(OTIS)", color='seagreen')
            self.ax1.bar(x2, 실적_TKE, width=width, bottom=실적_현대EL + 실적_OTIS, label="실적(TKE)", color='deepskyblue')
            self.ax1.bar(x2, 실적_기타, width=width, bottom=실적_현대EL + 실적_OTIS + 실적_TKE, label="실적(기타)", color='steelblue')

            for i in range(12):
                total_actual = 실적_현대EL[i] + 실적_OTIS[i] + 실적_TKE[i] + 실적_기타[i]
                self.ax1.text(x2[i], total_actual + 0.1, f"{total_actual:.1f}", ha='center', fontsize=8)

        else:
            실적 = get_data(customer, "실적")

            self.ax1.bar(x + width/2, 실적, width=width, label="실적", color='steelblue')

            for i in range(12):
                self.ax1.text(x[i] + width/2, 실적[i] + 0.1, f"{실적[i]:.1f}", ha='center', fontsize=8)
                
        self.ax1.set_ylim(0, get_scale_max(dept, customer))
        self.ax1.set_ylabel("금액 (억 원)")
        self.ax1.set_xlabel("월")
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels([f"{i}월" for i in x])
        self.ax1.set_title(f"{dept} - {customer} 실적")
        self.ax1.legend(loc='upper left', bbox_to_anchor=(1, +0.15), fontsize=9)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    from datas import datas

    window = ComboChartWidget()
    window.run()
    window.apply_api_datas(datas)

    sys.exit(app.exec())
