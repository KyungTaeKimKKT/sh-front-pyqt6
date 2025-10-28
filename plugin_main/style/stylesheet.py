from modules.envs.resources import resources as Resources

class StyleSheet:
    def __init__(self):
        # 기본 색상 정의
        self.primary_color = "#3498db"       # 파란색 계열 (주 색상)
        self.secondary_color = "#2ecc71"     # 녹색 계열 (보조 색상)
        self.warning_color = "#f39c12"       # 주황색 계열 (경고 색상)
        self.danger_color = "#e74c3c"        # 빨간색 계열 (위험 색상)
        self.info_color = "#9b59b6"          # 보라색 계열 (정보 색상)
        
        # 배경 및 텍스트 색상
        self.bg_color = "#f5f5f5"            # 밝은 회색 (기본 배경)
        self.bg_dark = "#2c3e50"             # 어두운 파란색 (어두운 배경)
        self.text_color = "#333333"          # 어두운 회색 (기본 텍스트)
        self.text_light = "#ffffff"          # 흰색 (밝은 배경 위 텍스트)
        
        # 테두리 및 그림자
        self.border_color = "#dddddd"        # 연한 회색 (테두리)
        self.shadow = "0 2px 5px rgba(0, 0, 0, 0.1)"  # 그림자 효과
        
        # 기본 스타일시트 생성
        self.create_stylesheets()
    
    def create_stylesheets(self):
        # 메인 윈도우 스타일
        self.main_window = f"""
            QMainWindow {{
                background-color: {self.bg_color};
            }}
        """
        
        # 메뉴바 스타일
        self.menubar = f"""
            QMenuBar {{
                background-color: {self.bg_dark};
                color: {self.text_light};
                padding: 2px;
                font-weight: bold;
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 10px;
                border-radius: 4px;
                margin: 1px 2px;
            }}
            
            QMenuBar::item:selected {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            
            QMenu {{
                background-color: {self.bg_dark};
                color: {self.text_light};
                border: 1px solid {self.border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            
            QMenu::item {{
                padding: 6px 25px 6px 20px;
                border-radius: 3px;
            }}
            
            QMenu::item:selected {{
                background-color: rgba(255, 255, 255, 0.35); /* 더 밝게 */
                color: #ffffff;                             /* 텍스트도 흰색으로 */
                font-weight: bold;                          /* 강조된 글씨 */
                border: 1px solid #ffffff30;                /* 부드러운 테두리 효과 */
            }}

            QMenu::item:disabled {{
                color: rgba(255, 255, 255, 0.4);  /* 흐리게 */
                font-style: italic;
            }}
        """
        
        # 툴바 스타일
        self.toolbar = f"""
            QToolBar {{
                background-color: {self.bg_dark};
                border-bottom: 1px solid {self.border_color};
                spacing: 5px;
                padding: 3px;
            }}
            
            QToolBar QToolButton {{
                background-color: transparent;
                color: {self.text_light};
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }}
            
            QToolBar QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            
            QToolBar QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """
        
        # 탭 위젯 스타일
        self.tab_widget = f"""
            QTabWidget::pane {{
                border: 1px solid {self.border_color};
                border-radius: 4px;
                background-color: white;
                top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: #e6e6e6;
                color: {self.text_color};
                border: 1px solid {self.border_color};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
                font-weight: normal;
            }}
            
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
                font-weight: bold;
                color: {self.primary_color};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #f0f0f0;
            }}
            
            QTabBar::tab:disabled {{
                color: #bbbbbb;
                background-color: #f0f0f0;
            }}
        """
        
        # 버튼 스타일
        self.button = f"""
            QPushButton {{
                background-color: {self.primary_color};
                color: {self.text_light};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            
            QPushButton:pressed {{
                background-color: #1f6aa5;
            }}
            
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #888888;
            }}
            
            QPushButton.success {{
                background-color: {self.secondary_color};
            }}
            
            QPushButton.success:hover {{
                background-color: #27ae60;
            }}
            
            QPushButton.warning {{
                background-color: {self.warning_color};
            }}
            
            QPushButton.warning:hover {{
                background-color: #e67e22;
            }}
            
            QPushButton.danger {{
                background-color: {self.danger_color};
            }}
            
            QPushButton.danger:hover {{
                background-color: #c0392b;
            }}
        """
        
        # 입력 필드 스타일
        self.input_fields = f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                border: 1px solid {self.border_color};
                border-radius: 4px;
                padding: 1px;
                background-color: white;
                selection-background-color: {self.primary_color};
            }}
            QLineEdit {{
                padding: 2px 4px;
                min-height: 20px;
                qproperty-alignment: AlignVCenter;
            }}
            QTextEdit, QPlainTextEdit {{
                min-height: 80px;  /* 4줄 정도의 높이 */
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {self.primary_color};
            }}
            

        """

            # QComboBox {{
            #     border: 1px solid {self.border_color};
            #     border-radius: 4px;
            #     padding: 4px;
            #     padding-right: 20px;    /* 드롭다운 버튼 공간 */
            #     background-color: white;
            # }}
            
            # QComboBox::drop-down {{
            #     subcontrol-origin: padding;
            #     subcontrol-position: right center;
            #     width: 20px;
            #     border-left: 1px solid {self.border_color};
            # }}

            # QComboBox::down-arrow {{
            #     image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
            #     width: 10px;
            #     height: 10px;
            # }}
            
            # QComboBox QAbstractItemView {{
            #     border: 1px solid {self.border_color};
            #     border-radius: 4px;
            #     background-color: white;
            #     selection-background-color: {self.primary_color};
            #     selection-color: {self.text_light};
            # }}
        
        # 테이블 위젯 스타일
        self.table = f"""
            QTableView, QTableWidget {{
                border: 1px solid {self.border_color};
                border-radius: 4px;
                background-color: white;
                gridline-color: {self.border_color};
                selection-background-color: {self.primary_color};
                selection-color: {self.text_light};
            }}
            
            QTableView::item, QTableWidget::item {{
                padding: 1px;
            }}
            
            QHeaderView::section {{
                background-color: #e6e6e6;
                padding: 5px;
                border: 1px solid {self.border_color};
                font-weight: bold;
            }}
        """
        
        # 진행 표시기 스타일
        self.progress = f"""
            QProgressBar {{
                border: 1px solid {self.border_color};
                border-radius: 4px;
                text-align: center;
                background-color: white;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.primary_color};
                border-radius: 3px;
            }}
        """
        
        # 스크롤바 스타일
        self.scrollbar = f"""
            QScrollBar:vertical {{
                border: none;
                background-color: #f0f0f0;
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #a0a0a0;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background-color: #f0f0f0;
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: #c0c0c0;
                min-width: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: #a0a0a0;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
        
        # 다이얼로그 스타일
        self.dialog = f"""
            QDialog {{
                background-color: {self.bg_color};
                border-radius: 6px;
            }}
            
            QDialog QLabel {{
                color: {self.text_color};
            }}
            
            QMessageBox {{
                background-color: {self.bg_color};
            }}
            
            QMessageBox QLabel {{
                color: {self.text_color};
            }}
        """
        
        # 상태 표시줄 스타일
        self.statusbar = f"""
            QStatusBar {{
                background-color: {self.bg_dark};
                color: {self.text_light};
                padding: 3px;
            }}
            
            QStatusBar::item {{
                border: none;
            }}
        """
        
        # 토스트 메시지 스타일
        self.toast = f"""
            QFrame#toast_frame {{
                background-color: rgba(44, 62, 80, 0.9);
                border-radius: 6px;
            }}
            
            QFrame#toast_frame QLabel {{
                color: {self.text_light};
            }}
            
            QFrame#toast_frame.success {{
                background-color: rgba(46, 204, 113, 0.9);
            }}
            
            QFrame#toast_frame.warning {{
                background-color: rgba(243, 156, 18, 0.9);
            }}
            
            QFrame#toast_frame.error {{
                background-color: rgba(231, 76, 60, 0.9);
            }}
            
            QFrame#toast_frame.information {{
                background-color: rgba(52, 152, 219, 0.9);
            }}
        """
        
        # 윈도우 타이틀 텍스트 스타일 (setWindowTitle로 설정된 텍스트용)
        self.window_title_text = f"""
            QMainWindow::title {{
                color: {self.text_color};
                font-weight: bold;
                font-size: 24pt;
            }}
        """

        # 윈도우 타이틀 스타일
        # self.window_title = f"""
        #     QWidget#windowTitle {{
        #         background-color: {self.bg_dark};
        #         color: {self.text_light};
        #         padding: 8px;
        #         font-weight: bold;
        #         font-size: 11pt;
        #         border-bottom: 1px solid {self.border_color};
        #     }}
            
        #     QWidget#windowTitle QLabel {{
        #         color: {self.text_light};
        #         font-weight: bold;
        #     }}
            
        #     QWidget#windowTitle QPushButton {{
        #         background-color: transparent;
        #         border: none;
        #         padding: 4px;
        #         border-radius: 4px;
        #     }}
            
        #     QWidget#windowTitle QPushButton:hover {{
        #         background-color: rgba(255, 255, 255, 0.2);
        #     }}
            
        #     QWidget#windowTitle QPushButton:pressed {{
        #         background-color: rgba(255, 255, 255, 0.1);
        #     }}
            
        #     QWidget#windowTitle QPushButton#closeButton:hover {{
        #         background-color: {self.danger_color};
        #     }}
        # """
        
        # 전체 스타일시트 결합
        self.global_style = f"""
            * {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }}
            
            QWidget {{
                color: {self.text_color};
            }}
            
            QLabel {{
                background-color: transparent;
            }}
            
            QGroupBox {{
                border: 1px solid {self.border_color};
                border-radius: 4px;
                margin-top: 1.5ex;
                padding-top: 1ex;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {self.primary_color};
                font-weight: bold;
            }}
            
            {self.main_window}
            {self.menubar}
            {self.toolbar}
            {self.tab_widget}
            {self.button}
            {self.input_fields}
            {self.table}
            {self.progress}
            {self.scrollbar}
            {self.dialog}
            {self.statusbar}
            {self.toast}
            
            {self.window_title_text}
        """
    
    def get_style(self, style_name=None):
        """특정 스타일 또는 전체 스타일시트를 반환합니다."""
        if style_name:
            return getattr(self, style_name, "")
        return self.global_style
    
    def apply_to_app(self, app):
        """애플리케이션에 전체 스타일시트를 적용합니다."""
        app.setStyleSheet(self.global_style)
    
    def apply_to_widget(self, widget, style_name=None):
        """특정 위젯에 스타일시트를 적용합니다."""
        if style_name:
            widget.setStyleSheet(getattr(self, style_name, ""))
        else:
            widget.setStyleSheet(self.global_style)
    
    # 테마 변경 메서드
    def set_dark_theme(self):
        """다크 테마로 변경합니다."""
        self.bg_color = "#2c3e50"
        self.bg_dark = "#1a2530"
        self.text_color = "#ecf0f1"
        self.text_light = "#ffffff"
        self.border_color = "#34495e"
        self.create_stylesheets()
    
    def set_light_theme(self):
        """라이트 테마로 변경합니다."""
        self.bg_color = "#f5f5f5"
        self.bg_dark = "#2c3e50"
        self.text_color = "#333333"
        self.text_light = "#ffffff"
        self.border_color = "#dddddd"
        self.create_stylesheets()
    
    # 사용자 정의 색상 설정
    def set_custom_colors(self, primary="#3498db", secondary="#2ecc71", 
                         warning="#f39c12", danger="#e74c3c"):
        """사용자 정의 색상을 설정합니다."""
        self.primary_color = primary
        self.secondary_color = secondary
        self.warning_color = warning
        self.danger_color = danger
        self.create_stylesheets()