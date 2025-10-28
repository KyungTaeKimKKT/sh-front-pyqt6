from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class WebPreviewDialog(QDialog):
    def __init__(self, parent=None, url: str=None):
        super().__init__(parent)
        self.url = url
        self.setWindowTitle("웹 페이지 미리보기")
        self.resize(1000, 700)

        # 웹 뷰 생성
        if self.url:
            self.UI()

    def UI(self):
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(self.url))

        # 닫기 버튼
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.close)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        layout.addWidget(self.close_btn)
        self.setLayout(layout)
