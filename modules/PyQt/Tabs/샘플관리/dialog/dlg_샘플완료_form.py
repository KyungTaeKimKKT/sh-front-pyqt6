from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import*
import os
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("이미지 미리보기")
        
        layout = QVBoxLayout(self)
        label = QLabel()
        pixmap = QPixmap(image_path)
        
        # 화면 크기의 80%로 조정
        screen = QApplication.primaryScreen().geometry()
        scaled_pixmap = pixmap.scaled(
            int(screen.width() * 0.8),
            int(screen.height() * 0.8),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        
        label.setPixmap(scaled_pixmap)
        layout.addWidget(label)
        
        # ESC 키로 닫기 가능하도록 설정
        self.setModal(True)


class ImageWidget(QWidget):
    delete_requested = pyqtSignal(str)  # 이미지 경로를 시그널로 전달
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 이미지 표시
        self.image_label = QLabel()
        self.pixmap = QPixmap(self.image_path)
        self.update_image_size(200)  # 기본 크기
        self.image_label.mousePressEvent = self.show_preview
        layout.addWidget(self.image_label)
        
        # 파일명과 삭제 버튼을 위한 하단 레이아웃
        bottom_layout = QHBoxLayout()
        filename_label = QLabel(os.path.basename(self.image_path))
        filename_label.setWordWrap(True)
        delete_btn = QPushButton("삭제")
        delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        delete_btn.clicked.connect(self.request_delete)
        
        bottom_layout.addWidget(filename_label)
        bottom_layout.addWidget(delete_btn)
        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        layout.addStretch()

        self.setLayout(layout)
        
    def update_image_size(self, size):
        scaled_pixmap = self.pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
    def show_preview(self, event):
        preview = ImagePreviewDialog(self.pixmap)
        preview.exec()
        
    def request_delete(self):
        self.delete_requested.emit(self.image_path)

class ImageViewer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # 상단 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 행 수 선택 콤보박스
        self.row_combo = QComboBox()
        self.row_combo.addItems(['1', '2', '3', '4', '5'])
        self.row_combo.setCurrentText('3')
        self.row_combo.currentTextChanged.connect(self.update_grid)
        control_layout.addWidget(QLabel("행 수:"))
        control_layout.addWidget(self.row_combo)
        
        # 이미지 크기 조절 슬라이더
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(50, 300)
        self.size_slider.setValue(150)
        self.size_slider.valueChanged.connect(self.update_image_size)
        control_layout.addWidget(QLabel("이미지 크기:"))
        control_layout.addWidget(self.size_slider)
        
        self.layout.addLayout(control_layout)
        
        # 스크롤 영역에 그리드 레이아웃 추가
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.scroll.setWidget(self.grid_widget)
        self.layout.addWidget(self.scroll)
        
        self.images = []
        self.image_widgets = []
        
        # 드래그 앤 드롭 설정
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.add_image(f)
        event.accept()  # 이벤트 처리 완료

    def add_image(self, image_path):
        # 이미지 위젯 생성
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # 이미지 라벨
        label = ClickableLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(
            self.size_slider.value(), 
            self.size_slider.value(), 
            Qt.AspectRatioMode.KeepAspectRatio
        )
        label.setPixmap(scaled_pixmap)        
        label.clicked.connect(lambda: self.show_full_image(image_path))
        
        # 삭제 버튼
        delete_btn = QPushButton("삭제")
        delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        delete_btn.clicked.connect(lambda: self.remove_image(image_widget))
        
        image_layout.addWidget(label)
        image_layout.addWidget(delete_btn,  alignment=Qt.AlignmentFlag.AlignHCenter)
        image_layout.addStretch()
        
        self.images.append(image_path)
        self.image_widgets.append(image_widget)
        self.update_grid()

    def update_grid(self):
        # 기존 위젯들 제거
        for widget in self.image_widgets:
            self.grid_layout.removeWidget(widget)
        
        # 그리드에 위젯들 재배치
        row_count = int(self.row_combo.currentText())
        for i, widget in enumerate(self.image_widgets):
            row = i // row_count
            col = i % row_count
            self.grid_layout.addWidget(widget, row, col)

    def update_image_size(self):
        size = self.size_slider.value()
        for widget in self.image_widgets:
            label = widget.layout().itemAt(0).widget()
            if isinstance(label, ClickableLabel) and label.pixmap():
                original_pixmap = QPixmap(self.images[self.image_widgets.index(widget)])
                scaled_pixmap = original_pixmap.scaled(
                    size, size, 
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                label.setPixmap(scaled_pixmap)

    def remove_image(self, widget):
        idx = self.image_widgets.index(widget)
        self.images.pop(idx)
        self.image_widgets.remove(widget)
        widget.deleteLater()
        self.update_grid()

    def show_full_image(self, image_path):
        dialog = ImagePreviewDialog(image_path, self)
        dialog.exec()

class Dialog_샘플완료(QDialog):
    completed = pyqtSignal(dict)
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setWindowTitle("완료 처리")
        self.setMinimumSize( 600, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        hbox_header = QHBoxLayout()
        # 완료 의견 입력
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("완료 의견을 입력하세요")
        hbox_header.addWidget(self.comment_edit)
       # 버튼들
        self.complete_btn = QPushButton("완료 처리")
        self.cancel_btn = QPushButton("취소")

        self.complete_btn.clicked.connect(self.handle_completion)
        self.cancel_btn.clicked.connect(self.reject)

        hbox_header.addWidget(self.complete_btn)
        hbox_header.addWidget(self.cancel_btn)
        layout.addLayout(hbox_header)

        # 이미지 뷰어
        hbox_image = QHBoxLayout()
        self.image_viewer = ImageViewer(self)
        hbox_image.addWidget(self.image_viewer)
        layout.addLayout(hbox_image)

        self.show()
        
    def handle_completion(self):
        result = {
            '완료file_fks': self.image_viewer.images,
            '완료의견': self.comment_edit.text()
        }
        self.completed.emit(result)
        # self.accept()