from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import typing
# 
from modules.envs.resources import resources


from plugin_main.dialog.ui.Ui_loading_dialog import Ui_Dialog_loading
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class LoadingDialog(QDialog):
    """
    loading dialog
        movie: str, default="loading:animation" => resources.get_movie("loading:animation") 형태로 사용됨
        start_time: int, default=1000 => start method 호출 후, 표시까지 지연시간
    """
    def __init__(self, parent=None, movie_str:str="loading:animation", start_time:int=1000, **kwargs ):
        super().__init__(parent)
        self.kwargs = kwargs
        
        
        self.movie_str = movie_str
        
        self.title_str = f'Loading 중입니다.<br>잠시만 기다려 주십시요..<br>'
        self.start_time = start_time

        self.interval:int = kwargs.get('interval', 100)
        self.소요시간:int = 0

        self.set_window_title( self.kwargs.get('title', 'Loading'))
        self.setMinimumSize( kwargs.get('width', 300), kwargs.get('height', 300))

        self.setup_ui()        
        self.setModal( kwargs.get('modal', True))

        self.stop_display()

    def start_display(self, start_time:int=1000):
        print (f"start_display: {start_time}")
        self.start_time = start_time
        self.소요시간 = 0
        self.start_trigger_timer = QTimer(self)
        self.start_trigger_timer.setSingleShot(True)
        self.start_trigger_timer.timeout.connect(self.start_display_timer)
        self.start_trigger_timer.start(self.start_time)

        
    def start_display_timer(self):
        self.show()
        self.소요시간 = self.start_time
        print (f"start_display_timer: {self.movie_str}")
        # self.set_movie(self.movie_str)
        # self.stop_display()

        data = resources.get_bytes(self.movie_str)# bytes
        buffer = QBuffer()
        buffer.setData(QByteArray(data))
        buffer.open(QBuffer.OpenModeFlag.ReadOnly)

        movie = QMovie()
        movie.setDevice(buffer)
        buffer.setParent(movie)  # GC 방지

        self.lb_loading.setMovie(movie)
        movie.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        self.timer.start(self.interval)



    def timeout(self):
        self.소요시간 += int(self.interval)
        소요시간txt = "{:.1f}".format( self.소요시간 / 1000)
        self.lb_title.setText( f"Loading중입니다.({str(소요시간txt)} 초)")

        print (f"timeout: {self.movie_str} {self.소요시간}")

    def stop_display(self):
        self.timer = getattr(self, 'timer', None)
        if self.timer and isinstance(self.timer, QTimer) and self.timer.isActive():
            self.timer.stop()
            self.timer = None
        self.hide()


    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        ### 1. self.lb_title
        self.lb_title = QLabel(self)
        self.lb_title.setText(self.title_str)
        self.lb_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lb_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb_title.setStyleSheet("font-size:32px;color:white;background-color:black;")
        self.main_layout.addWidget(self.lb_title)
        ### 2. self.lb_loading
        self.lb_loading = QLabel(self)
        self.lb_loading.setText("Loading...")
        self.lb_loading.setMinimumSize(200, 200)
        self.lb_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.lb_loading)
        self.setLayout(self.main_layout)


    ### setters
    def set_window_title(self, title:str):
        self.window_title = title
        self.setWindowTitle(self.window_title)

    def set_movie(self, movie:str):
        self.movie = resources.get_movie(movie)
        if self.movie is None:
            self.lb_loading.setText("Loading...")
            return
        print (f"set_movie:{type(self.movie)} : {self.movie}")
        self.lb_loading.setMovie(self.movie)
        QTimer.singleShot(0, lambda: self.movie.start())

    def set_start_time(self, start_time:int):
        self.start_time = start_time


# class LoadingThread(QThread):
#     def __init__(self):
#         super().__init__()
#         self.dialog = LoadingDialog()
#         self.is_Run = True

#     def run(self):
#         self.소요시간 = 0
#         while self.is_Run:
#             self.dialog.show()
#         self.stop()

#     def re_start(self):

#         self.is_Run = True
#         # self.run()

#     def stop(self):

#         # self.timer.stop()
#         self.is_Run = False

#         # self.dialog.close()



    # def timeout(self):
    #     self.소요시간 += 0.1
    #     소요시간txt = "{:.1f}".format(self.소요시간)
    #     title = f"Loading중입니다.({str(소요시간txt)} 초)"
    #     self.setWindowTitle(title)
    #     # self.title_bar.title.setText(title)


def main():    
    import sys
    app=QApplication(sys.argv)
    window=LoadingDialog()
    window.show()
    app.exec()


if __name__ == "__main__":
    import sys
    sys.exit( main())


