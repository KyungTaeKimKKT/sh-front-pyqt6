#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import typing

import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class LoadingDialog(QDialog):
    def __init__(self, parent:typing.Optional[QWidget]=None):
        super().__init__(parent)

        vlayout= QVBoxLayout()
        self.loadingLabel = QLabel()
        self.movie = QMovie("loading.gif")
        self.loadingLabel.setMovie(self.movie)
        self.movie.start()
        vlayout.addWidget(self.loadingLabel)
        # QDialog 세팅
 
        self.setWindowTitle('Loading')
        # self.setWindowModality(Qt.ApplicationModal)
        self.resize(300, 300)
        self.setLayout(vlayout)
        # self.setWindowIcon(QIcon(':/icons/loader.jpg'))
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
        소요시간txt = "{:.1f}".format(self.소요시간)
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



app=QApplication(sys.argv)

window=LoadingDialog()


app.exec()