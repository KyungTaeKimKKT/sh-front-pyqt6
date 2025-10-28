import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import random
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # plt.subplot 의 입력값은 행의수, 열의수, index 순 https://pyvisuall.tistory.com/68
        self.subplot_type = 111

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(self.subplot_type)
        super(MplCanvas, self).__init__(fig)


class Graph_Matplot(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ### graph 설정
        self.graph_width  = 5
        self.graph_height = 4
        self.graph_dpi    = 100

        self.x_datas = []
        self.y_datas = []
        ###😀 INFO의 Combo_작지_dashboard_GraphType_Items = ['Line', 'Bar', 'Pie'] 참조
        self.graph_type = 'Line'


    def UI(self):
        if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
        self.vLayout_main = QVBoxLayout()

        (self.canvas, self.toolbar) = self.create_Canvas()
        self.vLayout_main.addWidget( self.toolbar)
        self.vLayout_main.addWidget( self.canvas)
        
        self.setLayout(self.vLayout_main)

    def create_Canvas(self) -> tuple[MplCanvas, NavigationToolbar]:
        canvas = MplCanvas(self, width=self.graph_width, height=self.graph_height, dpi=self.graph_dpi )

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(canvas, self)
        return (canvas, toolbar)

    def run(self):
        self.UI()

        self.draw()
        
        self.show()

    def draw(self):
        self._plot_ref = None
        self.draw_by_graph_type()

    def test_run(self):
        """ test용 run"""
        # We need to store a reference to the plotted line
        # somewhere, so we can apply the new data to it.
        n_data = 50 
        self.x_datas = list(range(n_data))
        self.y_datas = [random.randint(0, 10) for i in range(n_data)]

        self._plot_ref = None
        self.update_plot()

                # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def clear_clf(self):
        try:
            self.canvas.figure.clear()
            self.canvas.draw()
        except:
            pass
    
    def clear_cla(self):
        try:
            self.canvas.axes.clear()
            self.canvas.draw()
        except:
            pass



    def draw_by_graph_type(self):
        self.clear_cla()
        match self.graph_type:
            case 'Line'|'line' :
                self.canvas.axes.plot(self.x_datas, self.y_datas, 'r')
            case 'Bar'|'bar':
                self.canvas.axes.bar(self.x_datas, self.y_datas)
            case 'Pie'|'pie':
                self.canvas.axes.pie(self.y_datas, labels=self.x_datas,autopct= '%1.1f%%')

    def update_plot(self) -> None:
        self.update_plot_Clear()

  # Clear Redraw
    def update_plot_Clear(self ):
        canvas = self.canvas
        
        canvas.axes.cla()
        canvas.axes.plot(datas['xdata'], datas['ydata'], 'r')

        # Trigger the canvas to update and redraw.

        canvas.draw()

    # In-place Redraw
    def update_plot_InPlace(self, obj:dict ):
        canvas:MplCanvas = obj.get('canvas')
        datas = obj['datas']
        # Drop off the first y element, append a new one.
        datas['ydata'] = datas['ydata'][1:] + [random.randint(0, 10)]

        # Note: we no longer need to clear the axis.
        if datas['_plot_ref'] is None:
            # First time we have no plot reference, so do a normal plot.
            # .plot returns a list of line <reference>s, as we're
            # only getting one we can take the first element.
            plot_refs = canvas.axes.plot(datas['xdata'], datas['ydata'], 'r')
            datas['_plot_ref'] = plot_refs[0]
        else:
            # We have a reference, we can use it to update the data for that line.
            datas['_plot_ref'].set_ydata(datas['ydata'])

        # Trigger the canvas to update and redraw.

        canvas.draw()