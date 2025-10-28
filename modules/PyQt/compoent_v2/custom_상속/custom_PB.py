from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen

class CustomPushButton(QPushButton):
    """ 버튼 스타일 커스터마이징 """    

    def __init__(self, parent=None, text="", icon=None):
        super().__init__(text, parent)
        
        # 기본 스타일 설정
        # 스타일 인스턴스 속성으로 설정 (서브클래스 오버라이드 가능)
        self.default_style = {
            'bg_color': QColor(240, 240, 240),
            'text_color': QColor(0, 0, 0),
        }
        self.hover_style = {
            'bg_color': QColor(220, 220, 220),
            'text_color': QColor(0, 0, 0),
        }
        self.pressed_style = {
            'bg_color': QColor(200, 200, 200),
            'text_color': QColor(0, 0, 0),
        }
        self.disabled_style = {
            'bg_color': QColor(230, 230, 230),
            'text_color': QColor(150, 150, 150),
        }

            
        self.default_text_color = QColor(0, 0, 0)
        self.hover_text_color = QColor(0, 0, 0)
        self.pressed_text_color = QColor(0, 0, 0)
        self.disabled_text_color = QColor(150, 150, 150)
        
        self.border_radius = 5
        self.border_width = 1
        self.border_color = QColor(200, 200, 200)
        self.disabled_border_color = QColor(210, 210, 210)
        
        # 현재 상태
        self._is_hovered = False
        self._is_pressed = False
        
        # 아이콘 설정
        if icon:
            self.setIcon(icon)
        
        # 이벤트 필터 설치
        self.installEventFilter(self)
        
        # 스타일시트 제거 (직접 그리기 위해)
        self.setStyleSheet("")
        
    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Enter:
                self._is_hovered = True
                self.update()
                return True
            elif event.type() == QEvent.Leave:
                self._is_hovered = False
                self.update()
                return True
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._is_pressed = True
                self.update()
                return False  # 이벤트 전파 허용
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._is_pressed = False
                self.update()
                return False  # 이벤트 전파 허용
        
        return super().eventFilter(obj, event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        style = self.default_style
        # 배경색 결정
        if not self.isEnabled():
            style = self.disabled_style
            border_color = self.disabled_border_color
        elif self._is_pressed:
            style = self.pressed_style
            border_color = self.border_color
        elif self._is_hovered:
            style = self.hover_style
            border_color = self.border_color
        else:
            style = self.default_style
            border_color = self.border_color
        
        # 배경 그리기
        painter.setPen(QPen(border_color, self.border_width))
        painter.setBrush(QBrush(style['bg_color']))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 
                               self.border_radius, self.border_radius)
        
        # 텍스트 그리기
        painter.setPen(QPen(style['text_color']))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        # 아이콘이 있으면 그리기
        if not self.icon().isNull():
            icon_rect = self.rect().adjusted(5, 5, -5, -5)
            self.icon().paint(painter, icon_rect, Qt.AlignCenter)
        
        painter.end()
    
    # 스타일 커스터마이징 메서드들
    def setDefaultBgColor(self, color):
        self.default_style['bg_color'] = QColor(color)
        self.update()
    
    def setHoverBgColor(self, color):
        self.hover_style['bg_color'] = QColor(color)
        self.update()
    
    def setPressedBgColor(self, color):
        self.pressed_style['bg_color'] = QColor(color)
        self.update()
    
    def setDisabledBgColor(self, color):
        self.disabled_style['bg_color'] = QColor(color)
        self.update()
    
    def setDefaultTextColor(self, color):
        self.default_style['text_color'] = QColor(color)
        self.update()
    
    def setHoverTextColor(self, color):
        self.hover_style['text_color'] = QColor(color)
        self.update()
    
    def setPressedTextColor(self, color):
        self.pressed_style['text_color'] = QColor(color)
        self.update()
    
    def setDisabledTextColor(self, color):
        self.disabled_style['text_color'] = QColor(color)
        self.update()
    
    def setBorderRadius(self, radius):
        self.border_radius = radius
        self.update()
    
    def setBorderWidth(self, width):
        self.border_width = width
        self.update()
    
    def setBorderColor(self, color):
        self.border_color = QColor(color)
        self.update()
    
    def setDisabledBorderColor(self, color):
        self.disabled_border_color = QColor(color)
        self.update()


    def set_released(self):
        if not self._is_pressed:
            return
        self._is_pressed = False
        self.update()

    def set_pressed(self):
        if self._is_pressed:
            return
        self._is_pressed = True
        self.update()

class HR평가_Stacked_PB(CustomPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pressed_style = {
            'bg_color' : QColor("black"),
            'text_color' : QColor("yellow"),
        }
    
    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Enter:
                self._is_hovered = True
                self.update()
                return True
            elif event.type() == QEvent.Leave:
                self._is_hovered = False
                self.update()
                return True
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._is_pressed = True
                self.update()
                return False  # 이벤트 전파 허용
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                return False  # 이벤트 전파 허용
        
        return super().eventFilter(obj, event)
    
class HR평가_차수별_역량평가_PB(HR평가_Stacked_PB):

    def __init__(self, _text:str, parent=None):
        super().__init__(parent)
        self.setText(_text)

class Custom_PB_Query(CustomPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        pass
    
# 사용 예시
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # 기본 버튼
    btn1 = CustomPushButton(text="기본 버튼")
    layout.addWidget(btn1)
    
    # 커스텀 스타일 버튼
    btn2 = CustomPushButton(text="커스텀 스타일 버튼")
    btn2.setDefaultBgColor("#3498db")
    btn2.setHoverBgColor("#2980b9")
    btn2.setPressedBgColor("#1c6ea4")
    btn2.setDefaultTextColor("#ffffff")
    btn2.setHoverTextColor("#ffffff")
    btn2.setPressedTextColor("#ffffff")
    btn2.setBorderRadius(10)
    layout.addWidget(btn2)
    
    # 비활성화 버튼
    btn3 = CustomPushButton(text="비활성화 버튼")
    btn3.setEnabled(False)
    layout.addWidget(btn3)
    
    window.setCentralWidget(central_widget)
    window.setGeometry(100, 100, 300, 200)
    window.setWindowTitle("커스텀 푸시버튼 예제")
    window.show()
    
    sys.exit(app.exec())  # PyQt6에서는 app.exec() 사용 (괄호 없이)