from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QAction
from PyQt6.QtCore import Qt
import sys
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TextEdit_ContextMenu(QTextEdit):
    """
        context Menu로 'bold', '밑줄', 'color'가 있음
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 포맷 관련 변수 초기화
        self.current_format = QTextCharFormat()
        self.is_bold = False
        self.is_underline = False
        self.current_color = QColor("#000000")

        self.setMinimumHeight(96)

        # 컨텍스트 메뉴 초기화
        self.initFormatActions()

    def contextMenuEvent(self, event):
        # 현재 선택된 텍스트의 서식 확인
        cursor = self.textCursor()
        if cursor.hasSelection():
            fmt = cursor.charFormat()
            self.is_bold = fmt.fontWeight() == QFont.Weight.Bold
            self.is_underline = fmt.underlineStyle() == QTextCharFormat.UnderlineStyle.SingleUnderline
            self.current_color = fmt.foreground().color()
            
            # 메뉴 상태 업데이트
            self.bold_action.setChecked(self.is_bold)
            self.underline_action.setChecked(self.is_underline)

        # 기존 메뉴 생성 코드
        menu = self.createStandardContextMenu()
        # 기본 컨텍스트 메뉴 생성
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        
        # 서식 메뉴 추가
        format_menu = menu.addMenu("서식")
        format_menu.addAction(self.bold_action)
        format_menu.addAction(self.underline_action)
        format_menu.addAction(self.color_action)
        
        # 메뉴 표시
        menu.exec(event.globalPos())

    def initFormatActions(self):
        # Bold 액션
        self.bold_action = QAction('굵게', self)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)

        # 밑줄 액션
        self.underline_action = QAction('밑줄', self)
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self.toggle_underline)

        # 색상 액션
        self.color_action = QAction('색상 변경...', self)
        self.color_action.triggered.connect(self.change_color)

    def toggle_bold(self, checked):
        cursor = self.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)
        self.current_format = fmt
        self.is_bold = checked

    def toggle_underline(self, checked):
        cursor = self.textCursor()
        fmt = cursor.charFormat()
        fmt.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SingleUnderline if checked 
            else QTextCharFormat.UnderlineStyle.NoUnderline
        )
        cursor.mergeCharFormat(fmt)
        self.current_format = fmt
        self.is_underline = checked

    def change_color(self):
        color = QColorDialog.getColor(initial=self.current_color)
        if color.isValid():
            cursor = self.textCursor()
            fmt = cursor.charFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.current_format = fmt
            self.current_color = color

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            super().keyPressEvent(event)
            
            # 커서 위치의 포맷 설정
            cursor = self.textCursor()
            fmt = QTextCharFormat(self.current_format)
            fmt.setFontWeight(QFont.Weight.Bold if self.is_bold else QFont.Weight.Normal)
            fmt.setUnderlineStyle(
                QTextCharFormat.UnderlineStyle.SingleUnderline if self.is_underline 
                else QTextCharFormat.UnderlineStyle.NoUnderline
            )
            self.setCurrentCharFormat(fmt)
        else:
            super().keyPressEvent(event)

class Test_TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('텍스트 에디터')
        self.setGeometry(100, 100, 800, 600)
        
        # 커스텀 텍스트 에디터 사용
        self.text_edit = TextEdit_ContextMenu(self)
        self.setCentralWidget(self.text_edit)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = Test_TextEditor()
    editor.show()
    sys.exit(app.exec())