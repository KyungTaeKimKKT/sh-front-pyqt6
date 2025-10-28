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
        self.category_combo_itmes = None

        self.initialized = False

        self.default_dept_combo_text = "회사계"
        self.default_category_combo_text = "TOTAL"

    def run( self):
        set_korean_font()
        self.init_ui()
        self.connect_signals()

    
    def stop(self):
        self.timer.stop()

    def set_initial_values(self):
        self.disconnect_signals()

        self.dept_combo_items = self.df["부서"].unique()
        self.category_combo_items = self.df["구분"].unique()   
        
        prev_dept_combo_text = self.dept_combo.currentText() if self.initialized else self.default_dept_combo_text
        prev_category_combo_text = self.category_combo.currentText() if self.initialized else self.default_category_combo_text

        self.dept_combo.clear()
        self.category_combo.clear()

        self.dept_combo.addItems(self.dept_combo_items)
        self.category_combo.addItems(self.category_combo_items)

        self.dept_combo.setCurrentText(prev_dept_combo_text)
        self.category_combo.setCurrentText(prev_category_combo_text)

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
        current_category_index = self.category_combo.currentIndex()

        # category_combo의 다음 인덱스를 설정합니다.
        next_category_index = (current_category_index + 1) % self.category_combo.count()

        # category_combo의 인덱스를 변경합니다.
        self.category_combo.setCurrentIndex(next_category_index)

        # category_combo가 처음으로 돌아왔을 때, dept_combo의 다음 인덱스로 이동합니다.
        if next_category_index == 0:
            next_dept_index = (current_dept_index + 1) % self.dept_combo.count()
            self.dept_combo.setCurrentIndex(next_dept_index)

    


    def init_ui(self):
        from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo
        self.layout = QVBoxLayout(self)

        self.h_layout = QHBoxLayout()
        self.h_layout.addStretch()
        label = QLabel('부서 선택 : ')
        self.h_layout.addWidget(label)

        self.dept_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.dept_combo)
        self.h_layout.addStretch()

        label = QLabel('구분 선택 : ')
        self.h_layout.addWidget(label)  
        self.category_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.category_combo)
        self.h_layout.addStretch()

        self.layout.addLayout(self.h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.canvas.setMinimumSize(200, 200)
        self.ax1 = self.canvas.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.layout.addWidget(self.canvas)

        self.show()



    def connect_signals(self):
        self.dept_combo.currentTextChanged.connect(self.update_chart)
        self.category_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.dept_combo.currentTextChanged.disconnect(self.update_chart)
            self.category_combo.currentTextChanged.disconnect(self.update_chart)
        except:
            pass

    def update_chart(self):
        dept = self.dept_combo.currentText()
        category = self.category_combo.currentText()
        months = [f"month_{i:02d}" for i in range(1, 13)]
        x = np.arange(1, 13)

        self.ax1.clear()
        self.ax2.clear()

        def get_data(구분, 분류):
            d = self.df[(self.df["부서"] == dept) & (self.df["구분"] == 구분) & (self.df["분류"] == 분류)]
            if not d.empty:
                values = d[months].astype(float).values[0]
                return values / 1e8 if 분류 in ["계획", "실적"] else values  # 달성률은 나누지 않음
            else:
                return np.zeros(12)
            
        def get_scale_max(dept, category):
            """dept : [회사계, 각지사들], category : [NE, MOD, TOTAL]"""
            if dept == "회사계":
                match category:
                    case "NE":
                        return 10
                    case "MOD":
                        return 20
                    case "TOTAL":
                        return 28
            else:
                match category:
                    case "NE":
                        return 10
                    case "MOD":
                        return 10
                    case "TOTAL":
                        return 15

        if category == "TOTAL":
            # Stacked bar 구성
            계획_ne = get_data("NE", "계획")
            계획_mod = get_data("MOD", "계획")
            실적_ne = get_data("NE", "실적")
            실적_mod = get_data("MOD", "실적")
            달성률 = get_data("TOTAL", "달성률")
            print( category, '  : 달성률:', 달성률)


            width = 0.35
            x1 = x - width / 2  # 계획 위치
            x2 = x + width / 2  # 실적 위치

            # 계획 stacked bar (NE + MOD)
            self.ax1.bar(x1, 계획_ne, width=width, label="계획(NE)", color='skyblue')
            self.ax1.bar(x1, 계획_mod, width=width, bottom=계획_ne, label="계획(MOD)", color='deepskyblue')

            # 실적 stacked bar (NE + MOD)
            self.ax1.bar(x2, 실적_ne, width=width, label="실적(NE)", color='lightgreen')
            self.ax1.bar(x2, 실적_mod, width=width, bottom=실적_ne, label="실적(MOD)", color='seagreen')

            for i in range(12):
                total_plan = 계획_ne[i] + 계획_mod[i]
                total_actual = 실적_ne[i] + 실적_mod[i]
                self.ax1.text(x1[i], total_plan + 0.1, f"{total_plan:.1f}", ha='center', fontsize=8)
                self.ax1.text(x2[i], total_actual + 0.1, f"{total_actual:.1f}", ha='center', fontsize=8)



        else:
            계획 = get_data(category, "계획")
            실적 = get_data(category, "실적")
            달성률 = get_data(category, "달성률")
            print( category, '  : 달성률:', 달성률)

            width = 0.35
            self.ax1.bar(x - width/2, 계획, width=width, label="계획", color='skyblue')
            self.ax1.bar(x + width/2, 실적, width=width, label="실적", color='steelblue')

            for i in range(12):
                self.ax1.text(x[i] - width/2, 계획[i] + 0.1, f"{계획[i]:.1f}", ha='center', fontsize=8)
                self.ax1.text(x[i] + width/2, 실적[i] + 0.1, f"{실적[i]:.1f}", ha='center', fontsize=8)

        
        ### 금액 scale 설정
        self.ax1.set_ylim(0, get_scale_max(dept, category))

        # 공통: 달성률
        self.ax2.plot(x, 달성률, color='tab:red', marker='o', label="달성률", linestyle='-', linewidth=2)
        for i in range(12):
            if 달성률[i] > 0:
                self.ax2.text(x[i], 달성률[i] + 3, f"{달성률[i]:.0f}%", color='tab:red', ha='center', fontsize=8)

        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.ax2.set_ylabel("달성률 (%)", color='tab:red')
        self.ax2.set_ylim(0, 120)

        self.ax1.set_ylabel("금액 (억 원)")
        self.ax1.set_xlabel("월")
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels([f"{i}월" for i in x])
        self.ax1.set_title(f"{dept} - {category} 계획/실적 & 달성률")
        # 금액(계획/실적) 레전드는 왼쪽 바깥 아래
        self.ax1.legend(loc='upper right', bbox_to_anchor=(0, +0.15), fontsize=9)

        # 달성률 레전드는 오른쪽 바깥 아래
        self.ax2.legend(loc='upper right', bbox_to_anchor=(1, +0.15), fontsize=9)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    from datas import datas

    window = ComboChartWidget()
    window.run(datas)

    sys.exit(app.exec())
