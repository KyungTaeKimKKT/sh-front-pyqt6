import sys
import matplotlib
matplotlib.use('Qt5Agg')

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import random
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.canvas_widgets = {}
  
        self.UI()
        self.init_data_plot_all()
        # self.init_data_plot()
        self.timer_update()

        self.show()

    def UI(self):
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        wid = QWidget()        
        self.vLayout_main = QVBoxLayout()

        hLayout = QHBoxLayout()
        label = QLabel()
        label.setText('Matplot Graph')
        hLayout.addWidget(label)
        self.btn_loadData = QPushButton()
        self.btn_loadData.setText('Load Data')
        self.btn_loadData.clicked.connect(self.func_load_data)        
        hLayout.addWidget(self.btn_loadData)
        self.vLayout_main.addLayout(hLayout)

        for i in range(4):
            canvas_layout = QVBoxLayout()
            self.canvas_widgets[i] = {}
            (self.canvas_widgets[i]['canvas'], toolbar )= self.create_Canvas()
            canvas_layout.addWidget(toolbar)
            canvas_layout.addWidget(self.canvas_widgets[i]['canvas'])

            self.vLayout_main.addLayout(canvas_layout)

            ### canvas 당 datas 초기화
            self.canvas_widgets[i]['datas'] = {'_plot_ref':None}

   
        wid.setLayout(self.vLayout_main)
        self.setCentralWidget(wid)

    def create_Canvas(self) -> tuple[MplCanvas, NavigationToolbar]:
        canvas = MplCanvas(self, width=5, height=4, dpi=100)

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(canvas, self)
        return (canvas, toolbar)

    def timer_update(self):
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot_all)
        self.timer.start()

    def init_data_plot_all(self):
        for (k, obj) in self.canvas_widgets.items():
            self.init_data_plot( obj )

    def init_data_plot(self, obj:dict):
        canvas:MplCanvas = obj.get('canvas')
        datas = obj.get('datas')
        
        n_data = 50 
        datas['xdata'] = list(range(n_data))
        datas['ydata'] = [random.randint(0, 10) for i in range(n_data)]

        # We need to store a reference to the plotted line
        # somewhere, so we can apply the new data to it.
        datas['_plot_ref'] = None    
        obj['datas'] = datas  
        self.update_plot_InPlace(obj)
        # self.update_plot_Clear( obj )

    def update_plot_all(self):
        for (k, obj) in self.canvas_widgets.items():
            # self.update_plot_Clear( obj )
            self.update_plot_InPlace( obj )

    # Clear Redraw
    def update_plot_Clear(self, obj:dict ):
        canvas:MplCanvas = obj.get('canvas')
        datas = obj['datas']
        # Drop off the first y element, append a new one.
        new_data = random.randint(0, 10)

        datas['ydata'] = datas['ydata'][1:] + [new_data]


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
       
    #### trigger function
    def func_load_data(self):
        return 

app = QApplication(sys.argv)
w = MainWindow()
app.exec_()