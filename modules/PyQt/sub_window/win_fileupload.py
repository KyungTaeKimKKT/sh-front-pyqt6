import sys, os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from pathlib import Path
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 전기사용량_Form(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.urls = []

        # self.resize(400, 400)
        # self.setAcceptDrops(False)

        self.scroll = QScrollArea()
        ### parent AppData 상속
        self.formData :dict= parent.appData.form

        self.UI()


    def UI(self):

        # self.widget = QWidget()        
        # self.mainLayout = QVBoxLayout(self.widget)
        # self.widget.setLayout(self.mainLayout)
        self.vLayout = QVBoxLayout()
        
        self.frame_upload = QFrame()
        self.vLayout.addWidget(self.frame_upload)
        self.formlayout_up = QFormLayout(self.frame_upload)
   
        # self.widget.setLayout(self.formlayout_up)
        ####
        self.title = QLabel(self)
        self.title.setText("Upload")
        self.title.setSizePolicy(QSizePolicy.Expanding, 0)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:32px;color:white;background-color:black;")
        self.formlayout_up.addRow(self.title)

        for (key, value) in self.formData.get('inputType').items():
            # if key in self.skip: continue
   
            match key:
                case '신우하이테크':
                    (_txt, self.file_upload_area_신우하이테크) = self.gen_file_upload_element(key, value)
                    if  _txt is not None  and self.file_upload_area_신우하이테크 is not None:
                        self.formlayout_up.addRow(_txt, self.file_upload_area_신우하이테크)
                    hbox = QHBoxLayout()
                    hbox.addStretch()
                    self.pb_신우하이테크_up = QPushButton("Upload")
                    self.pb_신우하이테크_up.setObjectName('신우하이테크')
                    hbox.addWidget(self.pb_신우하이테크_up)
                    self.pb_신우하이테크_up.clicked.connect(self.func_fileupload)
                    self.formlayout_up.addRow(self.pb_신우하이테크_up)

                case '신우폴리텍스':
                    (_txt, self.file_upload_area_신우폴리텍스) = self.gen_file_upload_element(key, value)
                    if  _txt is not None  and self.file_upload_area_신우폴리텍스 is not None:
                        self.formlayout_up.addRow(_txt, self.file_upload_area_신우폴리텍스)
                    hbox = QHBoxLayout()
                    hbox.addStretch()
                    self.pb_신우폴리텍스_up = QPushButton("Upload")
                    self.pb_신우폴리텍스_up.setObjectName('신우폴리텍스')
                    hbox.addWidget(self.pb_신우폴리텍스_up)
                    self.pb_신우폴리텍스_up.clicked.connect(self.func_fileupload)
                    self.formlayout_up.addRow(self.pb_신우폴리텍스_up)

                case _:
                    pass

        hbox = QHBoxLayout()
        hbox.addStretch()

 
        self.formlayout_up.addRow(hbox)

        self.frame_download = QFrame()
        self.vLayout.addWidget(self.frame_download)
        self.formlayout_down = QFormLayout(self.frame_download)


        self.title = QLabel(self)
        self.title.setText("Download")
        self.title.setSizePolicy(QSizePolicy.Expanding, 0)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:32px;color:white;background-color:black;")
        self.formlayout_down.addRow(self.title)

        for (key, value) in self.formData.get('inputType').items():
            # if key in self.skip: continue
   
            match key:
                case '신우하이테크':
                    (_txt, self.file_download_area_신우하이테크) = self.gen_file_upload_element(key, value)
                    if  _txt is not None  and self.file_download_area_신우하이테크 is not None:
                        self.formlayout_down.addRow(_txt, self.file_download_area_신우하이테크)
                    hbox = QHBoxLayout()
                    hbox.addStretch()
                    self.pb_신우하이테크_down = QPushButton("Download")
                    self.pb_신우하이테크_down.setObjectName('신우하이테크')
                    hbox.addWidget(self.pb_신우하이테크_down)
                    self.pb_신우하이테크_down.clicked.connect(self.func_fileupload)
                    self.formlayout_down.addRow(self.pb_신우하이테크_down)

                case '신우폴리텍스':
                    (_txt, self.file_download_area_신우폴리텍스) = self.gen_file_upload_element(key, value)
                    if  _txt is not None  and self.file_download_area_신우폴리텍스 is not None:
                        self.formlayout_down.addRow(_txt, self.file_download_area_신우폴리텍스)
                    hbox = QHBoxLayout()
                    hbox.addStretch()
                    self.pb_신우폴리텍스_down = QPushButton("Download")
                    self.pb_신우폴리텍스_down.setObjectName('신우폴리텍스')
                    hbox.addWidget(self.pb_신우폴리텍스_down)
                    self.pb_신우폴리텍스_down.clicked.connect(self.func_fileupload)
                    self.formlayout_down.addRow(self.pb_신우폴리텍스_down)

                case _:
                    pass

        hbox = QHBoxLayout()
        hbox.addStretch()

  
        self.formlayout_down.addRow(hbox)

        self.setLayout(self.vLayout)        
        self.vLayout.setSpacing(96)
        # self.vLayout.alignment(Qt.AlignCenter)


        # self.setCentralWidget(self.widget)
        self.show()

    
    ##### Trigger Func. #####
    def func_fileupload(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open file', 
            str(Path.home() / "Downloads"), '*.*(*.*)')
        # if fileName:
        #     self.file_upload_area.setText(fileName)

    def func_save(self):
        for (key, input) in self.inputType.items():
            if key in self.skip: continue
            self.result[key] = self._get_value(key)
        
    
    def func_cancel(self, is_send=False):
        # if not is_send :self.Signal.emit({'type':'close'})
        self.close()

        ############### element generate #########
    def gen_file_upload_element(self,key, value):
        setattr(self, key+'_label', QLabel() )
        label = getattr(self, key+'_label' )
        label.setText(key)

        upload_area = QLabel()
        upload_area.setAlignment(Qt.AlignCenter)
        upload_area.setText('')
        upload_area.setWordWrap(True)
        upload_area.setFixedHeight(48)
        upload_area.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

        return (label, upload_area)

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

    def _check_file_type(self, url):
        db = QMimeDatabase()
        mimetype = db.mimeTypeForUrl(url)
        # if mimetype.name() == "application/pdf":
            #     urls.append(url)

    def _hide_upload_frame(self):
        self.frame_upload.hide()

# app = QApplication(sys.argv)
# demo =전기사용량_Upload()
# demo.show()
# sys.exit(app.exec_())