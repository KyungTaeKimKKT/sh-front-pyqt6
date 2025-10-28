main.py
import sys, os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMainWindow, QScrollArea, QMenu
from PyQt6.QtCore import Qt, QMimeDatabase, QEvent
from PyQt6.QtGui import QPixmap
from PyQt6 import QtGui
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop Image Here \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

    def setPixmap(self, image):
        super().setPixmap(image)

class AppDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.urls = []

        self.resize(400, 400)
        self.setAcceptDrops(True)

        self.scroll = QScrollArea()


        self.widget = QWidget()        
        self.mainLayout = QVBoxLayout(self.widget)
        self.widget.setLayout(self.mainLayout)
        self.photoViewer = ImageLabel()
        self.mainLayout.addWidget(self.photoViewer)

        #Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.setCentralWidget(self.scroll)

        self.is_event_valid = True


        # self.mainLayout
        # self.setLayout(self.mainLayout)
        # self.setCentralWidget(widget)

    # https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
    def eventFilter(self, source, event:QEvent):

        if event.type() == QEvent.ContextMenu:
            
            menu = QMenu()

            action_delete = menu.addAction('Delete')

            action = menu.exec_(event.globalPos())

            if action == action_delete:

                if (idx:=self._get_Index_layout(self.mainLayout, source) ) is not None:
                    self.urls.pop(idx)
                self.mainLayout.removeWidget(source)
                source.deleteLater()
                source = None
        return super().eventFilter(source, event)
    
    #### +1은 droplabel에 mainLayout 최상단에 있기 때문에 
    def _get_Index_layout(self, layout, widget) ->int:        
        for i in range(len(self.urls)+1):
            if  widget == layout.itemAt(i).widget():
                return i-1
        return None

    #### dragEnter => dragMove ==> drop Evnet 순
    def dragEnterEvent(self, event):
        if not isinstance(event, QtGui.QDragEnterEvent): return

        mimeData = event.mimeData()
        for url in mimeData.urls():
            self._check_file_type(url)
            if url in self.urls : 
                self.is_event_valid = False
                event.ignore()
            else:
                self.is_event_valid |= True
                event.accept()




    def dragMoveEvent(self, event):
        if not isinstance(event, QtGui.QDragMoveEvent): return
        if not self.is_event_valid : return

        if self.is_event_valid: event.accept()
        else: event.ignore()
        
        # mimeData = event.mimeData()

        # for url in mimeData.urls():
        #     if url in self.urls: event.ignore()


    def dropEvent(self, event):

        if not isinstance(event, QtGui.QDropEvent): return
        if not self.is_event_valid : return
        
        self._clear_widgets(self.mainLayout, [0,])
        mimeData = event.mimeData()
        for url in mimeData.urls():
            if url not in self.urls: self.urls.insert(0, url)

        for index, url in enumerate(self.urls):        
            if self.is_event_valid:
                event.setDropAction(Qt.CopyAction)               

                file_path = url.toLocalFile()
                self.insert_newLabel(index, file_path)

                event.accept()
            else:
                event.ignore()

    def set_image(self, file_path):
        self.photoViewer.setPixmap(QPixmap(file_path))

    def insert_newLabel(self, index:int, filepath):
        attrName = f"index={index}"
        setattr(self, attrName, QLabel())
        new_label = getattr(self, attrName)
        if isinstance( new_label, QLabel):
            new_label.setPixmap(QPixmap(filepath) )
            self.mainLayout.addWidget(new_label)
            new_label.installEventFilter(self)

    def _clear_widgets(self, layout, no_del:list) -> None:

        # for index in range(layout.count()):
        #     if index in no_del: continue
        #     else:
        #         widget = layout.itemAt(index).widget()
        #         layout.removeWidget(widget)
        #         widget.deleteLater()
        #         widget = None

        for widget in self.findChildren(QLabel):
            if widget == self.photoViewer: continue
            else :
                layout.removeWidget(widget)
                widget.deleteLater()
                widget = None

    def _check_file_type(self, url):
        db = QMimeDatabase()
        mimetype = db.mimeTypeForUrl(url)

        # if mimetype.name() == "application/pdf":
            #     urls.append(url)

app = QApplication(sys.argv)
demo = AppDemo()
demo.show()
sys.exit(app.exec_())