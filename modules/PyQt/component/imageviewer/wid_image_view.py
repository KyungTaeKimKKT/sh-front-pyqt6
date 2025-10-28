import sys, os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.component.imageviewer.ui.Ui_wid_imagView import Ui_wid_imageViewer

from PIL.ImageQt import ImageQt
import PIL.Image
import io
import urllib.request

import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger


# # https://learndataanalysis.org/how-to-implement-image-drag-and-drop-feature-PyQt6-tutorial/#google_vignette
# class ImageLabel(QLabel):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.parent = parent

#         self.setAlignment(Qt.AlignCenter)
#         self.setText('\n\n Image file을 넣으세요 \n\n')
#         self.setStyleSheet('''
#             QLabel{
#                 border: 4px dashed #aaa
#             }
#         ''')

    
#     def setPixmap(self, image):
#         super().setPixmap(image.scaled( self.parent.width(), self.parent.height(), Qt.KeepAspectRatio , Qt.SmoothTransformation))
#         # super().setPixmap(image)
#         # self.setScaledContents(True)

#     def init_labelText(self):
#         self.setText('\n\n Image file을 넣으세요 \n\n')
#         self.setStyleSheet('''
#             QLabel{
#                 border: 4px dashed #aaa
#             }
#         ''')


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_Image_Viewer(QWidget):
    """ kwargs \n
            _url =str, \n
            _pixmap = QPixmap , \n
    """
    def __init__(self, parent:QWidget|None=None, **kwargs):
        super().__init__(parent)
        self._url :str =''
        self._pixmap : QPixmap = None


        self.setAcceptDrops(True)
        self.file_path = None

        for k, v in kwargs.items():
            setattr( self, k, v )

        self.ui = Ui_wid_imageViewer()
        self.ui.setupUi(self)

        self._render()


        # #Scroll Area Properties
        # self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # # self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.scroll.setWidgetResizable(True)
        # self.scroll.setWidget(self.widget)

        # self.setCentralWidget(self.scroll)

        self.is_event_valid = True
        self._resizeFlag = True
        self.pilImageName = ''
        self.is_clipboard = False
        self.url_DB삭제 = False
        # self.clip = QtGui.QClipboard()

    def _render(self):
        if hasattr(self, '_pixmap') and self._pixmap:
            self.ui.label_imageView.setPixmap(self._pixmap)
        
        elif hasattr( self, '_url') and self._url:
            if ( pixmap := self._getPixmapFromURL() ):
                if isinstance(pixmap, QPixmap):
                    self.ui.label_imageView.setPixmap ( pixmap)                
                else:
                    Utils.generate_QMsg_critical( self, title='File Preview Error', text= pixmap )
        
        self.user_defined_UI()


    def user_defined_UI(self):
        if hasattr( self, '_minimumSize'):  self.setMinimumSize ( self._minimumSize )
        if hasattr( self, '_maximumSize'):  self.setMaximumSize ( self._maximumSize )
        if hasattr(self, '_fixedSize') : self.setFixedSize ( self._fixedSize )

        self.ui.label_imageView.setScaledContents ( self._scaledContents if hasattr(self, '_scaledContents') else True )

    def _update_Data( self, **kwargs):
        """ kwargs \n
            class kwargs와 동일 \n
            update_Data 하면 다시 image render함. \n
        """
        for k, v in kwargs.items():
            setattr( self, k, v)
        
        self._render()

    def _clear(self):
        self.ui.label_imageView.clear()

        # self.setMaximumSize(400, 400)
        # self.scroll = QScrollArea()



    
    # def keyPressEvent(self, e):
    #     if (e.modifiers() & Qt.ControlModifier):
    #         #selected = self.table.selectedRanges()
                 
    #         if e.key() == Qt.Key_V:#past

    #             # qimg = self.clip.image()
    #             # self.displayImage(qimg)

    #         elif e.key() == Qt.Key_C: #copy
    #             pass

    def readOnly(self):
        self.setAcceptDrops(False)
    # def run(self):
    #     """
    #         url read :https://stackoverflow.com/questions/24003043/pyqt4-and-python-3-display-an-image-from-url
    #     """
    #     data = urllib.request.urlopen(self.url).read()
    #     image = QtGui.QImage()
    #     image.loadFromData(data)
    #     self.file_path = QtGui.QPixmap(image)
    #     self.set_image(self.file_path)

    def _getValue(self, key:str="Rendering_file") -> tuple:
        """
            if file_path return (...) else () ==> empty tule은 기존 url을 유지함
        """

        if self.file_path:
            return (key, open(self.file_path, 'rb') )
        elif self.pilImageName :
            # https://stackoverflow.com/questions/50350624/sending-pil-image-over-request-in-python
            byte_io = io.BytesIO()  # `BinaryIO` is essentially a file in memory
            self.pilImage : PIL.Image
            self.pilImage.save(byte_io,  'png' )  # Since there is no filename,
                                        # you need to be explicit about the format
            byte_io.seek(0)  # rewind the file we wrote into
            return ( key, (self.pilImageName, byte_io) )
        elif self.is_clipboard:
            fName = './temp/rendering.png'
            self.pixMap.save(fName)
            return ( key, open(fName, 'rb' ) )

        elif self.url:
            if self.url_DB삭제 : return ( 'DB삭제', self.url_DB삭제)
            else:  return ()
        return ()


    def _getPixmapFromURL(self, url:str='') -> QPixmap|str:
        url = url if url else self._url
        if url:
            try:
                data = urllib.request.urlopen(url).read()
                image = QtGui.QImage()
                image.loadFromData(data)
                return  QtGui.QPixmap(image)
            except Exception as e:
                return f'파일 open error : {e}'
        return '파일경로가 없읍니다.'


    # https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
    def eventFilter(self, source, event:QEvent):
        # if event.type() == QEvent.Resize and self._resizeFlag:
        #     if self.file_path:
        #         # self._resizeFlag = False
        #         self.set_image(self.file_path)
                # QTimer.singleShot(100, lambda: setattr(self, "_resizeFlag", True ))

        if event.type() == QEvent.ContextMenu:
            is_삭제_Active = False
            menu = QMenu()
            action_paste_clip = menu.addAction('Paste From Clipboard')
            action_view_fullscreen = menu.addAction('확대보기')
            # action_delete = menu.addAction('삭제')

            clipboard = QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if mimeData.hasImage():
                action_paste_clip.setVisible(True)
                is_삭제_Active = True
            else: 
                action_paste_clip.setVisible(False)

            if self.file_path or self.url or self.pilImageName:
                action_view_fullscreen .setVisible(True)
                is_삭제_Active = True
            else:
                action_view_fullscreen.setVisible(False)
            
            # action_delete.setVisible( is_삭제_Active )

            action = menu.exec_(event.globalPos())
  
            if action == action_view_fullscreen:
                full_screen_widget = ImageViewer_확대보기(self.pixMap)
            elif action == action_paste_clip:
                self.is_clipboard = True
                self.set_image_from_pixmap(pixMap=QPixmap(mimeData.imageData()))
            # elif action == action_delete:
            #     self.file_path = None 
            #     self.url_DB삭제 = True
            #     self.pixMap = None
            #     self.pilImage = None
            #     self.is_clipboard = False
            #     self.photoViewer.clear()
            #     self.photoViewer.init_labelText()

        return super().eventFilter(source, event)


    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            self.file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(self.file_path)

            event.accept()
        else:
            event.ignore()

    def set_image(self, file_path):
        self.pixMap = QPixmap(file_path)
        self.photoViewer.setPixmap(self.pixMap)
    
    def set_image_from_pixmap(self, pixMap):
        self.pixMap = pixMap
        self.photoViewer.setPixmap(self.pixMap)
    
    def set_image_from_QImage(self, qImg):
        self.pixMap =  QPixmap.fromImage(qImg) 
        self.photoViewer.setPixmap( self.pixMap )

    def set_image_from_pillowImage(self, pillowImage:ImageQt, fileName:str):
        """https://stackoverflow.com/questions/63138735/how-to-insert-a-pil-image-in-a-pyqt-canvas-PyQt6"""
        self.pilImageName = fileName if fileName else ''
        self.pilImage = pillowImage
        imageQt = ImageQt(pillowImage).copy()
        self.pixMap  = QPixmap.fromImage(imageQt)
        self.photoViewer.setPixmap(self.pixMap)
        
    def setText(self, text:str):
        pass


class ImageViewer_확대보기(QWidget):
    def __init__(self, pixmap:QPixmap|None):
        super().__init__()
        self.pixmap = pixmap
        self._resizeFlag = True

        self.UI()

    def UI(self):
        self.setMinimumSize(600, 600)
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.photoViewer = ImageLabel(self) 
        self.mainLayout.addWidget(self.photoViewer)

        self.photoViewer.installEventFilter(self)

        self.show()

    def set_image(self):
        self.photoViewer.setPixmap( self.pixmap )

    # https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
    def eventFilter(self, source, event:QEvent):

        if event.type() == QEvent.Resize and self._resizeFlag:
            if self.pixmap is not None:
                # self._resizeFlag = False
                self.set_image()
                # QTimer.singleShot(100, lambda: setattr(self, "_resizeFlag", True ))


        return super().eventFilter(source, event)


# app = QApplication(sys.argv)
# demo = ImageViewer()
# demo.show()
# sys.exit(app.exec_())