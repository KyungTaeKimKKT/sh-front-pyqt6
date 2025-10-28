from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from modules.PyQt.component.ui.Ui_imageViewer import Ui_Form 
from info import Info_SW as INFO
import modules.user.utils as Utils

from PIL.ImageQt import ImageQt
import PIL.Image
import io
import urllib.request
import traceback
from modules.logging_config import get_plugin_logger


# https://learndataanalysis.org/how-to-implement-image-drag-and-drop-feature-PyQt6-tutorial/#google_vignette

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Image file을 넣으세요 \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

    
    def setPixmap(self, image):
        super().setPixmap(image.scaled( self.parent.width(), self.parent.height(), Qt.KeepAspectRatio , Qt.SmoothTransformation))
        # super().setPixmap(image)
        # self.setScaledContents(True)

    def init_labelText(self):
        self.setText('\n\n Image file을 넣으세요 \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

class ImageViewer2(QWidget, Ui_Form ):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.url = ''
        self.file_path = None
        self.pixMap = None

        self.UI()

        self.is_readOnly = False
        self.is_event_valid = True
        self._resizeFlag = True
        self.pilImageName = ''
        self.is_clipboard = False
        self.url_DB삭제 = False
        # self.clip = QtGui.QClipboard()

    def UI(self):
        if hasattr(self, 'vLayout') : Utils.deleteLayout(self.vLayout)
        self.setupUi(self)
        self.installEventFilter(self)
        self.setAcceptDrops(True)

    
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
        self.is_readOnly = True

    def _getValue(self, key:str="Rendering_file") -> dict[str:object]:
        """
            if file_path return (...) else () ==> empty tule은 기존 url을 유지함
        """
        if self.file_path:
            return { 'file' : self.file_path }
        elif self.pilImageName :
            return { 'pilImage': self.pilImage}
        elif self.is_clipboard:
            return { 'pixMap' : self.pixMap }
        elif self.url:
            if self.url_DB삭제 : return { 'DB삭제', self.url_DB삭제 }
            else:  return { 'url' : 'url' }
        return {}

    # https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
    def eventFilter(self, source, event:QEvent):
        if event.type() == QEvent.Resize and self._resizeFlag:
            if not self.pixMap: return False
            self.label_ImageView.setPixmap(self._get_pixmap() )

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
            
            if self.is_readOnly: 
                action_paste_clip.setVisible(False)
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
            #     self.label_ImageView.clear()
            #     self.label_ImageView.init_labelText()

        return super().eventFilter(source, event)


    def dragEnterEvent(self, event:QDragEnterEvent):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event:QDragMoveEvent):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event:QDropEvent):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            self.file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(self.file_path)

            event.accept()
        else:
            event.ignore()

    def _get_pixmap(self, pixMap:QPixmap|None=None, is_KeepRatio:bool=True) -> QPixmap:        
        """ default keeyRatio =True """
        if not pixMap and not self.pixMap : return 
        pixMap = pixMap if pixMap else self.pixMap
        if is_KeepRatio:
            return pixMap.scaled(  self.width(), self.height(), Qt.KeepAspectRatio , Qt.SmoothTransformation )
        else:
            return pixMap

    def set_image(self, file_path):
        self.pixMap = QPixmap(file_path)
        self.label_ImageView.setPixmap(self._get_pixmap() )
    
    # url read :https://stackoverflow.com/questions/24003043/pyqt4-and-python-3-display-an-image-from-url
    def set_image_from_URL(self, url:str) -> None:
        """
            read URL and display             
        """
        if url:
            self.url = Utils.get_Full_URL(url)
            data = urllib.request.urlopen(self.url).read()
            image = QImage()
            image.loadFromData(data)
            self.pixMap = QPixmap(image)
            self.set_image(self.pixMap)

    def set_image_from_pixmap(self, pixMap):
        self.pixMap = pixMap
        self.label_ImageView.setPixmap(self._get_pixmap() )
    
    def set_image_from_QImage(self, qImg):
        self.pixMap = QPixmap.fromImage(qImg) 
        self.label_ImageView.setPixmap( self._get_pixmap() )

    def set_image_from_pillowImage(self, pillowImage:ImageQt, fileName:str):
        """https://stackoverflow.com/questions/63138735/how-to-insert-a-pil-image-in-a-pyqt-canvas-PyQt6"""
        self.pilImageName = fileName if fileName else ''
        self.pilImage = pillowImage
        imageQt = ImageQt(pillowImage).copy()
        self.pixMap  = QPixmap.fromImage(imageQt)
        self.label_ImageView.setPixmap(self._get_pixmap() )
        
    def setText(self, text:str):
        pass

class ImageViewer_확대보기(QWidget):
    def __init__(self, pixmap:QPixmap|None=None):
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
    
    def set_image_from_URL(self, url:str) -> None:
        """
            read URL and display             
        """
        if url:
            self.url = Utils.get_Full_URL(url)
            data = urllib.request.urlopen(self.url).read()
            image = QImage()
            image.loadFromData(data)
            self.pixmap = QPixmap(image)
            self.set_image()

    # https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
    def eventFilter(self, source, event:QEvent):

        if event.type() == QEvent.Resize and self._resizeFlag:
            if self.pixmap is not None:
                # self._resizeFlag = False
                self.set_image()
                # QTimer.singleShot(100, lambda: setattr(self, "_resizeFlag", True ))


        return super().eventFilter(source, event)


class Image_Barcode(ImageViewer2):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self._resizeFlag = False
        self.is_keep_ratio = False
    
    def UI(self):
        if hasattr(self, 'vLayout') : Utils.deleteLayout(self.vLayout)
        self.setupUi(self)
        # self.installEventFilter(self)
        self.setAcceptDrops(False)

    def eventFilter(self,  source, event:QEvent):
        return super().eventFilter(source, event)

    def _get_pixmap(self, pixMap:QPixmap|None=None, is_KeepRatio:bool=False) -> QPixmap:        
        """ default keeyRatio =True """
        if not pixMap and not self.pixMap : return 
        pixMap = pixMap if pixMap else self.pixMap
        if is_KeepRatio:
            return pixMap.scaled(  self.width(), self.height(), Qt.KeepAspectRatio , Qt.SmoothTransformation )
        else:
            return pixMap

# app = QApplication(sys.argv)
# demo = ImageViewer()
# demo.show()
# sys.exit(app.exec_())