from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QScrollArea, QWidget, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import requests
from io import BytesIO
from PIL import Image

class Dialog_ImageViewer(QDialog):
    def __init__(self, parent, url_list):
        super().__init__(parent)
        self.url_list = url_list
        self.current_columns = 3
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("이미지 뷰어")
        self.resize(800, 600)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 컬럼 선택 콤보박스
        self.column_combo = QComboBox()
        self.column_combo.addItems(['1', '2', '3', '4', '5'])
        self.column_combo.setCurrentText('3')
        self.column_combo.currentTextChanged.connect(self.update_grid)
        main_layout.addWidget(self.column_combo)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        
        # 그리드를 포함할 위젯
        self.grid_widget = QLabel()
        self.grid_layout = QGridLayout(self.grid_widget)
        scroll.setWidget(self.grid_widget)
        
        self.load_images()

        self.show()
        
    def load_images(self):
        for i, url in enumerate(self.url_list):
            try:
                response = requests.get(url)
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.getvalue())
                
                # 이미지 라벨 생성
                label = QLabel()
                label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.mousePressEvent = lambda e, url=url: self.show_large_image(url)
                
                # 그리드에 추가
                row = i // self.current_columns
                col = i % self.current_columns
                self.grid_layout.addWidget(label, row, col)
                
            except Exception as e:

    
    def update_grid(self, columns):
        # 기존 위젯들 제거
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        self.current_columns = int(columns)
        self.load_images()
    
    def show_large_image(self, url):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        
        try:
            response = requests.get(url)
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.getvalue())
            
            label = QLabel()
            label.setPixmap(pixmap.scaled(800, 800, Qt.AspectRatioMode.KeepAspectRatio))
            layout.addWidget(label)
            
            dialog.setWindowTitle("확대 보기")
            dialog.resize(850, 850)
            dialog.exec()
            
        except Exception as e:
