from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import traceback

from local_db.models import Search_History
from info import Info_SW as INFO
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Custom_LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)



    def event(self, event):
        match event.type():
            case QEvent.Type.FocusIn:
                self.setStyleSheet("background-color: #f4f5b8;font-weight: bold;")
            case QEvent.Type.FocusOut:
                self.setStyleSheet("background-color: #ffffff;")
            case QEvent.Type.KeyPress:
                self.setStyleSheet("background-color: #f4f5b8; font-weight: bold;")
        return super().event(event)

    ### 아래는 chaining builder 패턴

    def _set_text(self, text:str):
        self.setText(text)
        return self

    def _set_placeholderText(self, text:str):
        self.setPlaceholderText(text)
        return self
    
    def _set_toolTip(self, text:str):
        self.setToolTip(text)
        return self
   
    def _set_styleSheet(self, styleSheet:str):
        self.setStyleSheet(styleSheet)
        return self
    
    
class Custom_Search_LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.appID = -1
        self.setPlaceholderText("검색")
        self.setToolTip("검색")

    def event(self, event):
        match event.type():
            case QEvent.Type.FocusIn:
                self.setStyleSheet("background-color: #f4f5b8;font-weight: bold;")
            case QEvent.Type.FocusOut:
                self.setStyleSheet("background-color: #ffffff;")
            case QEvent.Type.KeyPress:
                self.setStyleSheet("background-color: #f4f5b8; font-weight: bold;")
        return super().event(event)

    def set_completer(self, appID:int = 0):
        self.appID = appID
        if appID>0:
            try:
                self.search_history  = list(set(Search_History.objects.filter(appID=appID).order_by('-count')[:10].values_list('search_text', flat=True)))
                if INFO.IS_DEV:
                    logger.debug(f"search_history: {self.search_history}")
                self.model = QStringListModel(self.search_history)
                self.completer = QCompleter(self.model)
                self.setCompleter(self.completer)

                self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                self.completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
                return True
            except Exception as e:
                logger.error(f"set_completer 실패: {e}")
                logger.error(traceback.format_exc())
                return False
        return False
    

    def db_save_search_history(self):
        if self.appID > 0:
            try:
                search_text = self.text().rstrip()
                if search_text:
                    # 기존 리스트 불러오기
                    history = self.model.stringList()
                    
                    # 중복 제거하고 맨 앞에 삽입
                    if search_text in history:
                        history.remove(search_text)
                    history.insert(0, search_text)

                    # 모델에 반영
                    self.model.setStringList(history)

                    # DB 저장
                    Search_History.objects.get_or_create(appID=self.appID, search_text=search_text)
            except Exception as e:
                logger.error(f"db_save_search_history 실패: {e}")
                logger.error(traceback.format_exc())


    ### 아래는 chaining builder 패턴

    def _set_text(self, text:str):
        self.setText(text)
        return self

    def _set_placeholderText(self, text:str):
        self.setPlaceholderText(text)
        return self
    
    def _set_toolTip(self, text:str):
        self.setToolTip(text)
        return self
   
    def _set_styleSheet(self, styleSheet:str):
        self.setStyleSheet(styleSheet)
        return self
    