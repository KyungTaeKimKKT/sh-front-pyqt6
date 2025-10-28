from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PIL import Image
import io
from PyQt6.QtWidgets import QApplication

from datetime import datetime
from info import Info_SW as INFO
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

# 클래스 시작 부분에 이미지 크기 제한 설정 추가
QImageReader.setAllocationLimit(0)  # 이미지 크기 제한 해제


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ImageViewer(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.setMinimumSize ( 300, 300)
        self.is_Edit= True
        self.initUI()
        self.full_size_dialog = None  # Dialog 인스턴스를 저장할 변수 추가
        self.image_source = None  # 이미지 출처 저장 (파일경로 또는 URL)
        
        
        # 초기 URL이 제공된 경우 이미지 로드
        self.update_kwargs( **kwargs )


    def update_kwargs(self, **kwargs):
        """kwargs를 업데이트하고 이미지를 다시 로드합니다.\n
            'url', 'pilImage'
        """
        if 'url' in kwargs and kwargs['url']:
            self.loadImage(kwargs['url'])
        elif 'pilImage' in kwargs and kwargs['pilImage']:
            self.loadPilImage(kwargs['pilImage'])

        if 'is_Edit' in kwargs:
            setattr( self, 'is_Edit', kwargs.get('is_Edit', False ) )
            self.setAcceptDrops( self.is_Edit )
            if not self.current_image:
                self.imageLabel.setText("DB에 저장된 내용이 없읍니다.")


    def keyPressEvent(self, event):
        # Ctrl+V 감지 및 처리 방식 수정
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            self.pasteFromClipboard()
        
    def pasteFromClipboard(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasImage():
            # 클립보드에서 이미지 직접 가져오기
            pixmap = QPixmap(clipboard.image())
            if not pixmap.isNull():
                self.current_image = pixmap
                self.image_source = "clipboard"
                self._update_display()
        elif mime_data.hasUrls():
            for url in mime_data.urls():
                # 첫 번째 유효한 URL만 처리
                self.loadImage(url.toString())
                break

    def loadPilImage(self, pil_image):
        # PIL Image를 QPixmap으로 변환
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        
        if not pixmap.isNull():
            self.current_image = pixmap
            self.image_source = "pilImage"
            self._update_display()
    
    def initUI(self):
        self.vlayout = QVBoxLayout(self)
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 초기 안내 메시지 설정
        self.imageLabel.setText("Image File 1개만 Drag and Drop 가능합니다")
        self.vlayout.addWidget(self.imageLabel)
        
        # 키보드 포커스 정책 설정 추가
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Drag & Drop 활성화
        self.setAcceptDrops(True)
        
        # 네트워크 매니저 초기화 (URL 로딩용)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_network_response)
        
        # 이미지 데이터 저장
        self.current_image = None

        # Context Menu 활성화
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Context Menu 메서드 추가
    def _show_context_menu(self, position):
        from PyQt6.QtWidgets import QMenu
        context_menu = QMenu(self)
        add_action = context_menu.addAction("Add")
        add_action.triggered.connect(self.addImage)

        if self.current_image:            
            if self.is_Edit :                
                delete_action = context_menu.addAction("Delete")
                delete_action.triggered.connect(self.clearImage)
        
        context_menu.exec(self.mapToGlobal(position))        

        
    def dragEnterEvent(self, event: QDragEnterEvent):
        # 단일 파일만 허용
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]
            # 이미지 파일 확장자 검사
            file_path = url.toLocalFile()
            valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
            if file_path.lower().endswith(valid_extensions):
                event.acceptProposedAction()
                return
        event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()  # 드래그 중에도 수락 상태 유지
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = event.mimeData().urls()
        if files and len(files) == 1:
            image_path = files[0].toLocalFile()
            if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.loadImage(image_path)
                event.acceptProposedAction()  # 이벤트 수락 추가
            
    def loadImage(self, path):
        self.image_source = path  # 이미지 출처 저장
        if path.startswith(('http://', 'https://')):
            self._load_from_url(path)
        else:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.current_image = pixmap
                self._update_display()
            
    def _load_from_url(self, url:str):
        """URL 로딩 오류 처리 개선"""        
        try:
            if not url.startswith(('http://', 'https://')):
                url = INFO.URI + url

            request = QNetworkRequest(QUrl(url))
            request.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
            )
            self.network_manager.get(request)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load URL: {str(e)}")
        
    def _handle_network_response(self, reply):
        """네트워크 응답 처리 개선"""
        if reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) != 200:
            error_details = {
                'error_code': reply.error(),
                'error_string': reply.errorString(),
                'http_status': reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute),
                'content_type': reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader),
                'raw_headers': str(reply.rawHeaderList())
            }
            
            error_message = f"""
            Error Code: {error_details['error_code']}
            Error Message: {error_details['error_string']}
            HTTP Status: {error_details['http_status']}
            Content Type: {error_details['content_type']}
            Headers: {error_details['raw_headers']}
            """
            
            QMessageBox.critical(self, "Error", error_message)
            return
            
        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        if not pixmap.isNull():
            self.current_image = pixmap
            self._update_display()
            
    def _update_display(self):
        if self.current_image:
            scaled_pixmap = self.current_image.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.imageLabel.setPixmap(scaled_pixmap)
        else:
            # 이미지가 없을 때 안내 메시지 표시
            self.imageLabel.setText("Image File 1개만 Drag and Drop 가능합니다")
            
    def mousePressEvent(self, event):
        if self.current_image and event.button() == Qt.MouseButton.LeftButton:
            # 새 창에서 원본 크기로 이미지 표시
            self._show_full_size()
            
    def addImage(self):
        filter = 'Image Files(*.png *.jpg *.jpeg *.gif *.bmp)'
        path = Utils._getOpenFileName_only1(self, title='Open file', filter=filter, initialFilter=filter )
        if path:
            self.loadImage(path)

        
    def clearImage(self):
        self.current_image = None
        self.imageLabel.clear()
        
    def getValue(self):
        if not self.current_image:
            return None
        
        return {
            'type': 'url' if self.image_source and self.image_source.startswith(('http://', 'https://')) 
                else 'clipboard' if self.image_source == 'clipboard'
                else 'pilImage' if self.image_source == 'pilImage'
                else 'file',
            'source': self.image_source,
            'image': self.current_image
        }


    # def _show_full_size(self):
    #     if self.current_image:
    #         from PyQt6.QtWidgets import QDialog, QScrollArea
    #         self.full_size_dialog = QDialog()
    #         self.full_size_dialog.setWindowTitle("Original Size")
            
    #         # 스크롤 영역 생성
    #         scroll = QScrollArea()
    #         self.full_size_dialog.setLayout(QVBoxLayout())
    #         self.full_size_dialog.layout().addWidget(scroll)
            
    #         # 화면 크기 구하기
    #         screen = QApplication.primaryScreen().geometry()
    #         max_width = screen.width() * 0.8
    #         max_height = screen.height() * 0.8
            
    #         # 이미지 표시를 위한 라벨 생성
    #         label = QLabel()
    #         label.setPixmap(self.current_image)
            
    #         # 스크롤 영역 설정
    #         scroll.setWidget(label)
    #         scroll.setWidgetResizable(True)
            
    #         # 다이얼로그 크기 설정
    #         dialog_width = min(self.current_image.width(), int(max_width))
    #         dialog_height = min(self.current_image.height(), int(max_height))
    #         self.full_size_dialog.resize(dialog_width, dialog_height)
            
    #         self.full_size_dialog.show()


    def _show_full_size(self):
        if self.current_image:
            from PyQt6.QtWidgets import QDialog, QScrollArea, QSpinBox, QHBoxLayout
            self.full_size_dialog = QDialog()
            self.full_size_dialog.setWindowTitle("Original Size")
            
            # 메인 레이아웃
            main_layout = QVBoxLayout()
            self.full_size_dialog.setLayout(main_layout)
            
            # 컨트롤 레이아웃
            control_layout = QHBoxLayout()
            
            # 줌 스핀박스 추가
            self.zoom_spinbox = QSpinBox()
            self.zoom_spinbox.setRange(10, 500)  # 10% ~ 500%
            self.zoom_spinbox.setValue(100)
            self.zoom_spinbox.setSuffix("%")
            self.zoom_spinbox.valueChanged.connect(self._update_zoom)
            control_layout.addWidget(self.zoom_spinbox)
            control_layout.addStretch()
            
            main_layout.addLayout(control_layout)
            
            # 스크롤 영역 생성
            self.scroll = QScrollArea()
            main_layout.addWidget(self.scroll)
            
            # 이미지 표시를 위한 라벨 생성
            self.zoom_label = QLabel()
            self.zoom_label.setPixmap(self.current_image)
            
            # 스크롤 영역 설정
            self.scroll.setWidget(self.zoom_label)
            self.scroll.setWidgetResizable(True)
            
            # 이벤트 필터 설치
            self.scroll.viewport().installEventFilter(self)
            
            # 화면 크기 구하기
            screen = QApplication.primaryScreen().geometry()
            max_width = screen.width() * 0.8
            max_height = screen.height() * 0.8
            
            # 다이얼로그 크기 설정
            dialog_width = min(self.current_image.width(), int(max_width))
            dialog_height = min(self.current_image.height(), int(max_height))
            self.full_size_dialog.resize(dialog_width, dialog_height)
            
            self._update_zoom(100)  # 초기 줌 설정
            
            # 다이얼로그가 닫힐 때 이벤트 필터 제거
            self.full_size_dialog.finished.connect(lambda: self.scroll.viewport().removeEventFilter(self))
            
            self.full_size_dialog.show()

    def eventFilter(self, obj, event):
        if hasattr(self, 'scroll') and obj == self.scroll.viewport():
            if event.type() == event.Type.Wheel:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    delta = event.angleDelta().y()
                    if delta > 0:
                        self.zoom_spinbox.setValue(self.zoom_spinbox.value() + 10)
                    else:
                        self.zoom_spinbox.setValue(self.zoom_spinbox.value() - 10)
                    return True
        return super().eventFilter(obj, event)

    def _update_zoom(self, zoom_value):
        if hasattr(self, 'zoom_label') and self.current_image:
            # 원본 이미지 크기 계산
            original_width = self.current_image.width()
            original_height = self.current_image.height()
            
            # 새로운 크기 계산 (정수로 변환)
            new_width = int(original_width * zoom_value / 100)
            new_height = int(original_height * zoom_value / 100)
            
            # 이미지 크기 조정
            scaled_pixmap = self.current_image.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.zoom_label.setPixmap(scaled_pixmap)



class ImageViewer_With_GraphicsView(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0

        self.setMinimumSize(300, 300)
        self.is_Edit = True
        self.image_source = None
        self.current_pixmap_item = None
        self.pixmap_item = None

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        # self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.addWidget(self.view)

        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_network_response)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.update_kwargs(**kwargs)

    def update_kwargs(self, **kwargs):
        if 'url' in kwargs and kwargs['url']:
            self.loadImage(kwargs['url'])
        elif 'pilImage' in kwargs and kwargs['pilImage']:
            self.loadPilImage(kwargs['pilImage'])

        if 'is_Edit' in kwargs:
            self.is_Edit = kwargs['is_Edit']
            self.setAcceptDrops(self.is_Edit)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = event.mimeData().urls()
        if files and len(files) == 1:
            image_path = files[0].toLocalFile()
            if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.loadImage(image_path)
                event.acceptProposedAction()

    def loadImage(self, path):
        self.image_source = path
        if path.startswith(('http://', 'https://')):
            self._load_from_url(path)
        else:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._set_pixmap(pixmap)

    def loadPilImage(self, pil_image):
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        if not pixmap.isNull():
            self.image_source = "pilImage"
            self._set_pixmap(pixmap)

    def _load_from_url(self, url):
        try:
            request = QNetworkRequest(QUrl(url))
            request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                                  QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            self.network_manager.get(request)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load URL: {str(e)}")

    def _handle_network_response(self, reply):
        if reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) != 200:
            QMessageBox.critical(self, "Error", f"HTTP Error: {reply.errorString()}")
            return
        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        if not pixmap.isNull():
            self._set_pixmap(pixmap)

    def _set_pixmap(self, pixmap):
        # self.scene.clear()
        # self.current_pixmap_item = QGraphicsPixmapItem(pixmap)
        # self.scene.addItem(self.current_pixmap_item)
        # self.view.fitInView(self.current_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        self.current_image = pixmap
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.view.resetTransform()
        self.zoom_level = 1.0
        QTimer.singleShot(0, lambda: self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio))

    def _show_context_menu(self, position):
        context_menu = QMenu(self)
        add_action = context_menu.addAction("Add")
        add_action.triggered.connect(self.addImage)

        if self.current_pixmap_item and self.is_Edit:
            delete_action = context_menu.addAction("Delete")
            delete_action.triggered.connect(self.clearImage)

        context_menu.exec(self.mapToGlobal(position))

    def addImage(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Image Files (*.png *.jpg *.jpeg *.gif *.bmp)')
        if path:
            self.loadImage(path)

    def clearImage(self):
        self.scene.clear()
        self.current_pixmap_item = None
        self.image_source = None

    def getValue(self):
        if not self.current_pixmap_item:
            return None
        return {
            'type': 'url' if self.image_source and self.image_source.startswith(('http://', 'https://'))
            else 'pilImage' if self.image_source == 'pilImage'
            else 'file',
            'source': self.image_source,
            'image': self.current_pixmap_item.pixmap()
        }
    
    def zoom_in(self):
        new_zoom = self.zoom_level * 1.25
        if new_zoom <= self.max_zoom:
            self.view.scale(1.25, 1.25)
            self.zoom_level = new_zoom

    def zoom_out(self):
        new_zoom = self.zoom_level * 0.8
        if new_zoom >= self.min_zoom:
            self.view.scale(0.8, 0.8)
            self.zoom_level = new_zoom

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     if self.pixmap_item:
    #         QTimer.singleShot(0, lambda: self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio))

    # def showEvent(self, event):
    #     super().showEvent(event)
    #     if self.pixmap_item:
    #         QTimer.singleShot(0, lambda: self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio))
