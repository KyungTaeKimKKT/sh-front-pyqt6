#!/usr/bin/env python3
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import typing
# 

from modules.PyQt.dialog.loading.ui.Ui_dlg_loading import Ui_Dialog_loading
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class LoadingDialog(QDialog):
    """
    loading dialog
    kwargs:
        movie: str, default="loading.gif"
        start_time: int, default=1000
    """
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        movie_default ="loading.gif"
        start_time_default = 1000

        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.ui = Ui_Dialog_loading()
        self.ui.setupUi(self)

        self.movie = QMovie(self.movie if hasattr(self, 'movie') else movie_default)
        self.start_time = self.start_time if hasattr(self, 'start_time') else start_time_default
        self.ui.label_loading.setMovie(self.movie)
        self.movie.start()

 
        self.setWindowTitle('Loading 중입니다.잠시만 기다려 주십시요..')
        # # self.setWindowModality(Qt.ApplicationModal)
        # self.setLayout(vlayout)
        # # self.setWindowIcon(QIcon(':/icons/loader.jpg'))
        self.show()

        # timer
        self.timer = QTimer(self)
        self.timer.start(100)
        self.timer.timeout.connect(self.timeout)
        self.소요시간 = 0

    def stop(self):
        self.timer.stop()
        self.close()


    def timeout(self):
        self.소요시간 += 0.1
        소요시간txt = "{:.1f}".format(self.start_time/1000+self.소요시간)
        title = f"Loading중입니다.({str(소요시간txt)} 초)"
        self.setWindowTitle(title)
        # self.title_bar.title.setText(title)

class LoadingThread(QThread):
    def __init__(self):
        super().__init__()
        self.dialog = LoadingDialog()
        self.is_Run = True

    def run(self):
        self.소요시간 = 0
        while self.is_Run:
            self.dialog.show()
        self.stop()

    def re_start(self):

        self.is_Run = True
        # self.run()

    def stop(self):

        # self.timer.stop()
        self.is_Run = False

        # self.dialog.close()



    def timeout(self):
        self.소요시간 += 0.1
        소요시간txt = "{:.1f}".format(self.소요시간)
        title = f"Loading중입니다.({str(소요시간txt)} 초)"
        self.setWindowTitle(title)
        # self.title_bar.title.setText(title)


def main():    
    import sys
    app=QApplication(sys.argv)
    window=LoadingDialog()
    window.show()
    app.exec()


if __name__ == "__main__":
    import sys
    sys.exit( main())


