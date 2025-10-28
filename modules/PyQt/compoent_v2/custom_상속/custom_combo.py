from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback
from modules.logging_config import get_plugin_logger

from config import Config as APP

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Custom_Combo(QComboBox):
    def __init__(self, parent=None, items:list[str]=[]):
        super().__init__(parent)
        # self.setup_default_style()
        self.items = items
        self.addItems(self.items)
        self.setToolTip("")


        self.currentTextChanged.connect(self.on_text_changed)

    # def event(self, event):
    #     match event.type():
    #         case QEvent.Type.FocusIn:
    #             self.setStyleSheet("background-color: #f4f5b8;font-weight: bold;")
    #         case QEvent.Type.FocusOut:
    #             self.setStyleSheet("background-color: #ffffff;")
    #     return super().event(event)

    def on_text_changed(self, text):
        # 텍스트 변경 시 스타일시트 적용
        self.setStyleSheet("background-color: #f4f5b8; font-weight: bold;")
        # 필요하다면 일정 시간 후 원래 스타일로 돌아가는 타이머 설정 가능
        QTimer.singleShot(1000, lambda: self.setStyleSheet("background-color: #ffffff;"))

class Custom_Combo_with_fetch(Custom_Combo):
    def __init__(self, parent=None, url:str=''):
        super().__init__(parent)
        self._url = ''
        self._loaded = False  # url 변경되면 다시 fetch 하게

        # self.items = ['2025','2024','2023','2022','2021','2020']
        # self.clear()
        # self.addItems(self.items)
        if self._url:
            self.run(self._url)

    
    def run(self, url:str):
        # self.items = ['2025','2024','2023','2022','2021','2020']
        # self.clear()
        # self.addItems(self.items)

        self.set_url(url)
        self.applay_data_from_fetch()

    def showPopup(self):
        # override showPopup: 클릭할 때 비동기 fetch 시도
        if not self._loaded and self._url:
            QTimer.singleShot(100, self.applay_data_from_fetch)  # UI block 방지
        super().showPopup()
    
    def applay_data_from_fetch(self):
        if not self._loaded and self._url:
            self.items = self.fetch_data()
            self.items = [ str(item) for item in self.items ]
            logger.debug(f"self.items: {self.items}")
            if self.items:
                self.clear()
                self.addItems(self.items)   
                # self._loaded = True
            else:
                logger.error(f"fastapi 호출 실패: {self._url}")

    def fetch_data(self) -> list[str]:
        _isok, _data = APP.API.getlist(self._url)
        # _isok, _data = APP.API.getlist(self._url)
        logger.debug(f"fetch_data : _isok : {_isok}, _data : {_data}")
        if _isok:
            return _data
        else:
            return []

    def set_url(self, url:str):
        self._url = url
        self._loaded = False  # url 변경되면 다시 fetch 하게
    
    def get_url(self):
        return self.url

class Combo_Select_Edit_Mode(Custom_Combo):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = ['Row', 'Cell']
        self.addItems(self.items)
        self.setToolTip("Table 편집 모드 선택")
        self.setCurrentText('Row')

class Custom_Combo_PageSize(QComboBox):
    def __init__(self, parent=None, items:list[str]=['ALL', '25', '50', '100']):
        super().__init__(parent)
        # self.setup_default_style()
        self.items = items
        self.addItems(self.items)
        self.setCurrentText('25')
        self.setToolTip("페이지 크기 선택")


        self.currentTextChanged.connect(self.on_text_changed)

    # def event(self, event):
    #     match event.type():
    #         case QEvent.Type.FocusIn:
    #             self.setStyleSheet("background-color: #f4f5b8;font-weight: bold;")
    #         case QEvent.Type.FocusOut:
    #             self.setStyleSheet("background-color: #ffffff;")
    #     return super().event(event)

    def on_text_changed(self, text):
        # 텍스트 변경 시 스타일시트 적용
        self.setStyleSheet("background-color: #f4f5b8; font-weight: bold;")
        # 필요하다면 일정 시간 후 원래 스타일로 돌아가는 타이머 설정 가능
        QTimer.singleShot(1000, lambda: self.setStyleSheet("background-color: #ffffff;"))

    # ### 아래는 chaining builder 패턴

    # def with_items(self, items:list[str]):
    #     self.items = items
    #     self.addItems(self.items)
    #     return self
    
    # def with_current_index(self, index:int):
    #     try:
    #         self.setCurrentIndex(index)
    #     except:
    #         logger.error(f"index 가 범위를 벗어났읍니다. index : {index}")
    #     return self
    
    # #### getters
    # def get_current_index(self) -> int:
    #     try:
    #         return self.currentIndex()
    #     except:
    #         logger.error(f"currentIndex 가 범위를 벗어났읍니다. currentIndex : {self.currentIndex()}")
    
    # def get_current_text(self) -> str:
    #     try:
    #         return self.currentText()
    #     except:
    #         logger.error(f"currentText 가 범위를 벗어났읍니다. currentText : {self.currentText()}")

    # #### setters
    # def set_current_index(self, index:int):
    #     self.current_index = index
    #     try:
    #         self.setCurrentIndex(index)
    #     except:
    #         logger.error(f"index 가 범위를 벗어났읍니다. index : {index}")

    # def set_current_text(self, text:str):
    #     self.current_text = text
    #     try:
    #         self.setCurrentText(text)
    #     except:
    #         logger.error(f"text 가 범위를 벗어났읍니다. text : {text}")

   
    # def set_styleSheet(self, styleSheet:str):
    #     self.setStyleSheet(styleSheet)
    #     return self
    
    

    # def setup_default_style(self):
    #     """기본 스타일 설정"""
    #     self.setStyleSheet("""
    #         QComboBox {
    #             background-color: #ffffff;
    #             color: #000000;
    #             border: 1px solid #cccccc;
    #             border-radius: 4px;
    #             padding: 2px 8px;
    #             min-height: 25px;
    #         }
    #         QComboBox:hover {
    #             border: 1px solid #aaaaaa;
    #         }
    #         QComboBox:focus {
    #             background-color: #f4f5b8;
    #             border: 1px solid #888888;
    #             font-weight: bold;
    #         }
    #         QComboBox::drop-down {
    #             subcontrol-origin: padding;
    #             subcontrol-position: right;
    #             width: 20px;
    #             border-left: 1px solid #cccccc;
    #         }
    #         QComboBox QAbstractItemView {
    #             selection-background-color: #4a90e2;
    #             selection-color: #ffffff;
    #             background-color: #ffffff;
    #             border: 1px solid #cccccc;
    #             border-radius: 2px;
    #         }
    #         QComboBox QAbstractItemView::item {
    #             min-height: 20px;
    #             padding: 2px;
    #         }
    #         QComboBox QAbstractItemView::item:hover {
    #             background-color: #e0e0e0;
    #             color: #000000;
    #         }
    #         QComboBox QAbstractItemView::item:selected {
    #             background-color: #4a90e2;
    #             color: #ffffff;
    #         }
    #     """)
    #     return self
