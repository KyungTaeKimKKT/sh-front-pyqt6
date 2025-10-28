from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import fitz
import os
import requests
import tempfile
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class PDFViewer(QWidget):
    def __init__(self, parent, path=None):
        super().__init__(parent)
        self.setMinimumSize(800, 800)
        self.path = path
        self.current_page = 0
        self.zoom_level = 1.0
        self.rotation = 0
        self.doc = None
        self.search_text = ""
        self.search_results = []
        self.current_result = -1
        self.temp_file = None

        self.init_ui()
        if path:
            self.load_pdf(path)

    def init_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self.go_to_page)

        zoom_in_btn = QPushButton("확대(+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn = QPushButton("축소(-)")
        zoom_out_btn.clicked.connect(self.zoom_out)

        rotate_btn = QPushButton("회전")
        rotate_btn.clicked.connect(self.rotate_page)

        self.fit_combo = QComboBox()
        self.fit_combo.addItems(["너비에 맞춤", "높이에 맞춤", "페이지에 맞춤"])
        self.fit_combo.currentIndexChanged.connect(self.fit_page)

        prev_page_btn = QPushButton("이전 페이지")
        next_page_btn = QPushButton("다음 페이지")
        prev_page_btn.setToolTip("이전 페이지 (←)")
        next_page_btn.setToolTip("다음 페이지 (→)")
        prev_page_btn.clicked.connect(self.prev_page)
        next_page_btn.clicked.connect(self.next_page)

        self.page_info_label = QLabel()

        control_layout.addWidget(QLabel("페이지:"))
        control_layout.addWidget(self.page_spin)
        control_layout.addWidget(zoom_in_btn)
        control_layout.addWidget(zoom_out_btn)
        control_layout.addWidget(rotate_btn)
        control_layout.addWidget(self.fit_combo)
        control_layout.addWidget(prev_page_btn)
        control_layout.addWidget(next_page_btn)
        control_layout.addWidget(self.page_info_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력")
        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self.search_text_in_pdf)
        prev_btn = QPushButton("이전")
        next_btn = QPushButton("다음")
        prev_btn.clicked.connect(lambda: self.navigate_search_results(-1))
        next_btn.clicked.connect(lambda: self.navigate_search_results(1))

        self.search_info_label = QLabel()

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(prev_btn)
        search_layout.addWidget(next_btn)
        search_layout.addWidget(self.search_info_label)

        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_widget.setFixedHeight(50)

        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        search_widget.setFixedHeight(40)

        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.pdf_label)
        self.scroll_area.setWidgetResizable(True)

        layout.addWidget(control_widget)
        layout.addWidget(search_widget)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.reset_zoom)
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_page)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_page)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_combo.currentIndex() == 2:
            self.fit_page(2)

    def load_pdf(self, path):
        try:
            if path.startswith('http'):
                response = requests.get(path)
                response.raise_for_status()
                if self.temp_file:
                    os.unlink(self.temp_file.name)
                self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                self.temp_file.write(response.content)
                self.temp_file.close()
                path = self.temp_file.name

            if os.path.exists(path):
                self.doc = fitz.open(path)
                self.page_spin.setMaximum(len(self.doc))
                self.current_page = 0
                self.fit_combo.setCurrentIndex(2)
                QTimer.singleShot(0, lambda: self.fit_page(2))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"PDF 로딩 실패: {str(e)}")

    def update_page(self):
        if self.doc is None:
            return
        page = self.doc[self.current_page]
        mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
        pix = page.get_pixmap(matrix=mat)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.pdf_label.setPixmap(pixmap)
        self.page_spin.setValue(self.current_page + 1)
        self.page_info_label.setText(f"{self.current_page + 1} / {len(self.doc)}")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.go_to_page(self.current_page)

    def next_page(self):
        if self.doc and self.current_page < len(self.doc) - 1:
            self.go_to_page(self.current_page + 2)

    def go_to_page(self, page_num):
        if self.doc and 1 <= page_num <= len(self.doc):
            self.current_page = page_num - 1
            self.update_page()

    def zoom(self, factor):
        self.zoom_level *= factor
        self.update_page()

    def rotate_page(self):
        self.rotation = (self.rotation + 90) % 360
        self.update_page()

    def fit_page(self, index):
        if self.doc is None:
            return
        page = self.doc[self.current_page]
        rect = page.rect

        view_width = self.scroll_area.viewport().width()
        view_height = self.scroll_area.viewport().height()

        if index == 0:  # 너비에 맞춤
            self.zoom_level = view_width / rect.width
        elif index == 1:  # 높이에 맞춤
            self.zoom_level = view_height / rect.height
        else:  # 페이지에 맞춤
            width_zoom = view_width / rect.width
            height_zoom = view_height / rect.height
            self.zoom_level = min(width_zoom, height_zoom)

        self.update_page()


    def search_text_in_pdf(self):
        self.search_text = self.search_input.text()
        self.search_results.clear()
        self.current_result = -1

        if not self.search_text:
            return

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            areas = page.search_for(self.search_text)
            for area in areas:
                self.search_results.append((page_num, area))

        if self.search_results:
            self.navigate_search_results(1)

    def navigate_search_results(self, direction):
        if not self.search_results:
            return
        self.current_result = (self.current_result + direction) % len(self.search_results)
        page_num, _ = self.search_results[self.current_result]
        self.search_info_label.setText(f"{self.current_result + 1} / {len(self.search_results)} 결과")
        if page_num != self.current_page:
            self.go_to_page(page_num + 1)
        else:
            self.update_page()

    def zoom_in(self):
        self.zoom(1.25)

    def zoom_out(self):
        self.zoom(0.8)

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.update_page()

# class PDFViewer(QWidget):
#     def __init__(self, parent, path=None):
#         super().__init__(parent)

#         self.setMinimumSize ( 800, 800)
#         self.path = path
#         self.current_page = 0
#         self.zoom_level = 1.0
#         self.rotation = 0
#         self.doc = None
#         self.search_text = ""
#         self.search_results = []
#         self.current_result = -1
#         self.temp_file = None  # 임시 파일 저장을 위한 변수 추가
#         self.scroll_area = None

#         self.init_ui()
#         if path:
#             self.load_pdf(path)

#     def init_ui(self):
#         # 메인 레이아웃
#         layout = QVBoxLayout()
        
#         # 컨트롤 패널
#         control_layout = QHBoxLayout()
        
#         # 페이지 네비게이션
#         self.page_spin = QSpinBox()
#         self.page_spin.setMinimum(1)
#         self.page_spin.valueChanged.connect(self.go_to_page)
        
#         # 확대/축소 컨트롤
#         zoom_in_btn = QPushButton("확대(+)")
#         zoom_in_btn.clicked.connect(lambda: self.zoom(1.25))
#         zoom_out_btn = QPushButton("축소(-)")
#         zoom_out_btn.clicked.connect(lambda: self.zoom(0.8))
        
#         # 회전 버튼
#         rotate_btn = QPushButton("회전")
#         rotate_btn.clicked.connect(self.rotate_page)
        
#         # 페이지 맞춤 콤보박스
#         self.fit_combo = QComboBox()
#         self.fit_combo.addItems(["너비에 맞춤", "높이에 맞춤", "페이지에 맞춤"])
#         self.fit_combo.currentIndexChanged.connect(self.fit_page)
        
#         # PDF 표시 레이블
#         self.pdf_label = QLabel()
#         self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
#         # 컨트롤 패널에 위젯 추가
#         control_layout.addWidget(QLabel("페이지:"))
#         control_layout.addWidget(self.page_spin)
#         control_layout.addWidget(zoom_in_btn)
#         control_layout.addWidget(zoom_out_btn)
#         control_layout.addWidget(rotate_btn)
#         control_layout.addWidget(self.fit_combo)
#             # 이전/다음 페이지 버튼 추가
#         prev_page_btn = QPushButton("이전 페이지")
#         next_page_btn = QPushButton("다음 페이지")
#         prev_page_btn.clicked.connect(self.prev_page)
#         next_page_btn.clicked.connect(self.next_page)
        
#         control_layout.addWidget(prev_page_btn)
#         control_layout.addWidget(next_page_btn)
            
#         self.search_text = ""
#         self.search_results = []
#         self.current_result = -1

#         # 검색 컨트롤 추가
#         search_layout = QHBoxLayout()
#         self.search_input = QLineEdit()
#         self.search_input.setPlaceholderText("검색어 입력")
#         search_btn = QPushButton("검색")
#         search_btn.clicked.connect(self.search_text_in_pdf)
#         next_btn = QPushButton("다음")
#         next_btn.clicked.connect(lambda: self.navigate_search_results(1))
#         prev_btn = QPushButton("이전")
#         prev_btn.clicked.connect(lambda: self.navigate_search_results(-1))
        
#         search_layout.addWidget(self.search_input)
#         search_layout.addWidget(search_btn)
#         search_layout.addWidget(prev_btn)
#         search_layout.addWidget(next_btn)

#         # 페이지 정보 레이블 추가
#         self.page_info_label = QLabel()
#         control_layout.addWidget(self.page_info_label)

#         # 컨트롤 패널 고정 크기 설정
#         control_widget = QWidget()
#         control_widget.setLayout(control_layout)
#         control_widget.setFixedHeight(50)  # 높이 고정

#         # 검색 패널 고정 크기 설정
#         search_widget = QWidget()
#         search_widget.setLayout(search_layout)
#         search_widget.setFixedHeight(40)  # 높이 고정

#                 # 스크롤 영역 추가
#         self.scroll_area = QScrollArea()
#         self.scroll_area.setWidget(self.pdf_label)
#         self.scroll_area.setWidgetResizable(True)

#         # 메인 레이아웃에 위젯 추가 (기존 코드 수정)
#         layout.addWidget(control_widget)
#         layout.addWidget(search_widget)
#         layout.addWidget(self.scroll_area)
        
#         self.setLayout(layout)

#                 # 단축키 추가
#         QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
#         QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
#         QShortcut(QKeySequence("Ctrl+0"), self, self.reset_zoom)

#     def load_pdf(self, path):
#         try:
#             if path.startswith('http'):
#                 # URL인 경우 임시 파일로 다운로드
#                 response = requests.get(path)
#                 response.raise_for_status()
                
#                 # 이전 임시 파일이 있다면 삭제
#                 if self.temp_file:
#                     os.unlink(self.temp_file.name)
                
#                 # 새 임시 파일 생성
#                 self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
#                 self.temp_file.write(response.content)
#                 self.temp_file.close()
#                 path = self.temp_file.name
            
#             if os.path.exists(path):
#                 self.doc = fitz.open(path)
#                 self.page_spin.setMaximum(len(self.doc))
#                 self.current_page = 0
#                 self.update_page()
#         except Exception as e:
#             QMessageBox.critical(self, "오류", f"PDF 로딩 실패: {str(e)}")
        
#     def update_page(self):
#         if self.doc is None:
#             return
            
#         page = self.doc[self.current_page]
#         mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
#         pix = page.get_pixmap(matrix=mat)
        
#         # 검색 결과 하이라이트
#         if self.search_text:
#             areas = page.search_for(self.search_text)
#             for area in areas:
#                 page.draw_rect(area, color=(1, 1, 0), fill=(1, 1, 0, 0.3))
        
#         img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
#         pixmap = QPixmap.fromImage(img)
        
#         self.pdf_label.setPixmap(pixmap)
#         self.page_spin.setValue(self.current_page + 1)
        
#         # 페이지 정보 업데이트
#         self.page_info_label.setText(f"{self.current_page + 1} / {len(self.doc)}")

#     # 새로운 메서드 추가
#     def prev_page(self):
#         if self.doc and self.current_page > 0:
#             self.go_to_page(self.current_page)

#     def next_page(self):
#         if self.doc and self.current_page < len(self.doc) - 1:
#             self.go_to_page(self.current_page + 2)

#     def go_to_page(self, page_num):
#         if self.doc and 1 <= page_num <= len(self.doc):
#             self.current_page = page_num - 1
#             self.update_page()

#     def zoom(self, factor):
#         self.zoom_level *= factor
#         self.update_page()

#     def rotate_page(self):
#         self.rotation = (self.rotation + 90) % 360
#         self.update_page()

#     def fit_page(self, index):
#         if self.doc is None:
#             return
            
#         page = self.doc[self.current_page]
#         rect = page.rect
        
#         if index == 0:  # 너비에 맞춤
#             self.zoom_level = self.width() / rect.width
#         elif index == 1:  # 높이에 맞춤
#             self.zoom_level = self.height() / rect.height
#         else:  # 페이지에 맞춤
#             width_zoom = self.width() / rect.width
#             height_zoom = self.height() / rect.height
#             self.zoom_level = min(width_zoom, height_zoom)
        
#         self.update_page()

#     def search_text_in_pdf(self):
#         self.search_text = self.search_input.text()
#         self.search_results = []
#         self.current_result = -1
        
#         if not self.search_text:
#             return
            
#         # 모든 페이지에서 검색
#         for page_num in range(len(self.doc)):
#             page = self.doc[page_num]
#             areas = page.search_for(self.search_text)
#             for area in areas:
#                 self.search_results.append((page_num, area))
        
#         if self.search_results:
#             self.navigate_search_results(1)

#     def navigate_search_results(self, direction):
#         if not self.search_results:
#             return
            
#         self.current_result = (self.current_result + direction) % len(self.search_results)
#         page_num, _ = self.search_results[self.current_result]
        
#         if page_num != self.current_page:
#             self.go_to_page(page_num + 1)
#         else:
#             self.update_page()

#     # 새로운 메서드 추가
#     def zoom_in(self):
#         self.zoom(1.25)
        
#     def zoom_out(self):
#         self.zoom(0.8)
        
#     def reset_zoom(self):
#         self.zoom_level = 1.0
#         self.update_page()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    from pdfviewer_pymupdf import PDFViewer
    import sys
    app = QApplication(sys.argv)
    path = 'http://192.168.7.108:9999/media/%EC%98%81%EC%97%85-%EB%94%94%EC%9E%90%EC%9D%B8%EA%B4%80%EB%A6%AC/%EC%98%81%EC%97%85image/%EC%9D%98%EB%A2%B0%ED%8C%8C%EC%9D%BC/2025-1-8/7c84bffc-ee5d-436d-aa53-6ae04fe749b9/%ED%94%84%EB%A6%AC%EB%AF%B8%EC%97%84%EC%9D%B8%ED%85%8C%EB%A6%AC%EC%96%B4_%EC%B9%B4%ED%83%88%EB%A1%9C%EA%B7%B8_%EC%9B%90%EA%B3%A0-23.11_compressed_1.pdf'
    viewer = PDFViewer(path)
    viewer.show()
    sys.exit(app.exec())
