
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

class ComboChartWidget(QWidget):
    def __init__(self , parent: QWidget=None):
        super().__init__(parent)
        self.df: pd.DataFrame = None
        self.datas: list[dict] = None
        self.prev_person_combo_itmes = None
        self.prev_category_combo_itmes = None
        self.person_combo_itmes = None
        self.person_combo_itmes = None

        self.initialized = False

        self.default_person_combo_text = "전체"
        self.default_category_combo_text ="전체"


    def run( self):
        set_korean_font()
        self.init_ui()
        self.connect_signals()

    
    def stop(self):
        self.timer.stop()

    def set_initial_values(self):
        self.disconnect_signals()

        self.person_combo_items = list(self.df["담당자"].unique())
        # self.person_combo_items = list(self.df["담당자"].unique())   
        if '비정규' in self.person_combo_items:
            del self.person_combo_items[self.person_combo_items.index('비정규')]
        
        prev_person_combo_text = self.person_combo.currentText() if self.initialized else self.default_person_combo_text
        # prev_category_combo_text = self.person_combo.currentText() if self.initialized else self.default_category_combo_text

        self.person_combo.clear()
        # self.person_combo.clear()

        self.person_combo.addItems([self.default_person_combo_text] + self.person_combo_items)
        # self.person_combo.addItems(self.person_combo_items)

        self.person_combo.setCurrentText(prev_person_combo_text)
        # self.person_combo.setCurrentText(prev_category_combo_text)

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
        pass

    


    def init_ui(self):
        from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo
        # from custom_combo import Custom_Combo
        self.layout = QVBoxLayout(self)

        self.h_layout = QHBoxLayout()
        self.h_layout.addStretch()

        label = QLabel('담당자 선택 : ')
        self.h_layout.addWidget(label)

        self.person_combo = Custom_Combo(self)
        self.h_layout.addWidget(self.person_combo)
        self.h_layout.addStretch()

        # label = QLabel('담당자 선택 : ')
        # self.h_layout.addWidget(label)

        # self.person_combo = Custom_Combo(self)
        # self.h_layout.addWidget(self.person_combo)
        # self.h_layout.addStretch()

        self.layout.addLayout(self.h_layout)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax1 = self.canvas.figure.add_subplot(111)  # 기본 축만 사용
        self.ax2 = self.ax1.twinx()  # ❌ 삭제

        self.layout.addWidget(self.canvas)

        self.show()



    def connect_signals(self):
        self.person_combo.currentTextChanged.connect(self.update_chart)
        # self.person_combo.currentTextChanged.connect(self.update_chart)

    def disconnect_signals(self):
        try:
            self.person_combo.currentTextChanged.disconnect(self.update_chart)
            # self.person_combo.currentTextChanged.disconnect(self.update_chart)
        except:
            pass

    def update_chart(self):
        person = self.person_combo.currentText()
        months = [f"month_{i:02d}" for i in range(1, 13)]
        x = np.arange(1, 13)

        self.ax1.clear()
        self.ax2.clear()

        def get_data(담당자, 분류):
            df_filtered = self.df[self.df["분류"] == 분류]
            if 담당자 != "전체":
                df_filtered = df_filtered[df_filtered["담당자"] == 담당자]
            return df_filtered[months].astype(float).sum(axis=0).values / 1e8  # 억 단위

        width = 0.35
 
        if person == "전체":
            담당자_list = self.person_combo_items
            

            # 실적, 계획: 각 담당자별로 가져오기
            실적_dict = {name: get_data(name, "실적") for name in 담당자_list}
            계획_dict = {name: get_data(name, "계획") for name in 담당자_list}

            실적_합계 = sum(실적_dict.values())
            계획_합계 = sum(계획_dict.values())

                # Top 5 담당자 결정
            담당자_합계 = {name: np.sum(val) for name, val in 실적_dict.items()}
            top5 = sorted(담당자_합계.items(), key=lambda x: x[1], reverse=True)[:5]
            top5_names = [name for name, _ in top5]

            x1 = x - width / 2
            x2 = x + width / 2

            # 계획 막대 (왼쪽) - 하나의 색상
            계획_누적 = 계획_합계
            self.ax1.bar(x1, 계획_누적, width=width, label="계획", color='lightgray')
            for i in range(12):
                self.ax1.text(x1[i], 계획_누적[i] + 0.1, f"{계획_누적[i]:.1f}", ha='center', fontsize=8)

            # 실적 stacked bar
            실적_누적_bottom = np.zeros(12)
            color_palette = plt.cm.tab10.colors  # 고유 색상
            for idx, name in enumerate(담당자_list):
                values = 실적_dict[name]
                if name in top5_names:
                    color = color_palette[top5_names.index(name) % len(color_palette)]
                    self.ax1.bar(x2, values, width=width, bottom=실적_누적_bottom,
                                color=color, label=name)
                else:
                    self.ax1.bar(x2, values, width=width, bottom=실적_누적_bottom,
                                color='lightgray')
                실적_누적_bottom += values

            # stacked bar 위에 월별 전체 실적 합계 표시
            for i in range(12):
                self.ax1.text(x2[i], 실적_누적_bottom[i] + 0.2, f"{실적_누적_bottom[i]:.1f}", 
                            ha='center', va='bottom', fontsize=8, fontweight='bold')
                
            # 달성률
            달성률 = (실적_합계 / 계획_합계) * 100
            self.ax2.plot(x, 달성률, label="달성률(%)", color='red', marker='o')
            for i in range(12):
                self.ax2.text(x[i], 달성률[i] + 2, f"{달성률[i]:.0f}%", ha='center', fontsize=8)

        else:
            계획 = get_data(person, "계획")
            실적 = get_data(person, "실적")
            달성률 = (실적 / 계획) * 100

            self.ax1.bar(x - width / 2, 계획, width=width, label="계획", color='lightgray')
            self.ax1.bar(x + width / 2, 실적, width=width, label="실적", color='steelblue')
            # 바 위 금액 표시
            for i in range(12):
                self.ax1.text(x[i] - width / 2, 계획[i] + 0.1, f"{계획[i]:.1f}", ha='center', fontsize=8)
                self.ax1.text(x[i] + width / 2, 실적[i] + 0.1, f"{실적[i]:.1f}", ha='center', fontsize=8)


            self.ax2.plot(x, 달성률, label="달성률(%)", color='red', marker='o')
            for i in range(12):
                self.ax2.text(x[i], 달성률[i] + 2, f"{달성률[i]:.0f}%", ha='center', fontsize=8)


        # 공통 설정
        self.ax1.set_xlabel("월")
        self.ax1.set_ylabel("금액 (억 원)")
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels([f"{i}월" for i in x])
        self.ax1.set_title(f"{person} 월별 계획/실적 및 달성률")
        self.ax1.set_ylim(0, 30 if person == "전체" else 5)

        self.ax2.plot(x, 달성률, color='tomato', marker='o', label="달성률")
        self.ax2.set_ylim(0, 120)
        self.ax2.set_ylabel("달성률 (%)", labelpad=15)
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()

        # 범례 (담당자들 + 달성률만)
        self.ax1.legend(loc='upper left', bbox_to_anchor=(1, 0.2), fontsize=9)
        # self.ax2.legend(loc='upper left', bbox_to_anchor=(1, 0.1), fontsize=9)


        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    from datas import datas

    window = ComboChartWidget()
    window.run()
    window.apply_api_datas(datas)

    sys.exit(app.exec())
