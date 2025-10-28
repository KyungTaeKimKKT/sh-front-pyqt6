from __future__ import annotations
from typing import Optional

from modules.PyQt.Tabs.plugins.ui.Ui_table_head import Ui_tableheader

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class Wid_Header(QWidget):
    edit_mode_changed = pyqtSignal(str) ### 'row' or 'cell' or 'no'
    save_requested = pyqtSignal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_tableheader()
        self.ui.setupUi(self)
        self.ui.PB_save.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.connect_signals()
        
    def closeEvent(self, event):
        self.disconnect_signals()
        super().closeEvent(event)

    def hide_all(self):
        self.ui.label_7.setVisible(False)
        self.ui.label_update_gap.setVisible(False)
        self.ui.label_update_time.setVisible(False)
        self.hide_modeCombo_and_saveButton()


    def hide_modeCombo_and_saveButton(self):
        self.ui.label_8.setVisible(False)
        self.ui.comboBox_edit_mode.setVisible(False)
        self.ui.PB_save.setVisible(False)
        
    def update_api_query_time(self, time_str:Optional[str]=None):
        self.time_str = time_str or QDateTime.currentDateTime().toString("HH:mm:ss")
        self.ui.label_update_time.setText(self.time_str)
        self.ui.label_update_gap.setText(' (방금 전) ')
    
    def update_no_change_data(self):
        self.ui.label_update_time.setText(
            self.ui.label_update_time.text() + 
            '  ( 이전 데이터 변경 없음 )' )

    def update_api_query_gap(self, time_str:Optional[str]=None):
        if time_str:
            try:
                # 라벨에서 업데이트 시간 읽기
                update_time_str = self.ui.label_update_time.text()
                if not update_time_str:
                    return
                    
                current_time = QDateTime.currentDateTime()
                
                # 현재 날짜와 라벨에서 읽은 시간을 결합하여 QDateTime 객체 생성
                current_date = current_time.toString("yyyy-MM-dd")
                
                # 시간 문자열에서 초 부분을 0으로 설정
                update_time_parts = update_time_str.split(":")
                if len(update_time_parts) >= 3:
                    update_time_parts[2] = "00"  # 초를 00으로 설정
                    update_time_str = ":".join(update_time_parts)
                
                update_time_full = f"{current_date} {update_time_str}"
                update_time = QDateTime.fromString(update_time_full, "yyyy-MM-dd HH:mm:ss")
                
                # 만약 계산된 시간이 미래라면 하루 전으로 조정
                if update_time > current_time:
                    update_time = update_time.addDays(-1)
                
                # 시간 차이 계산 (초 단위)
                seconds_diff = update_time.secsTo(current_time)
                
                # 시간 차이 포맷팅
                if seconds_diff < 60:
                    time_gap = f"방금 전"
                elif seconds_diff < 3600:
                    minutes = seconds_diff // 60
                    time_gap = f"{minutes}분 전"
                else:
                    hours = seconds_diff // 3600
                    remaining_minutes = (seconds_diff % 3600) // 60
                    time_gap = f"{hours}시간 {remaining_minutes}분 전"
                
                # 라벨에 시간 차이 표시
                self.ui.label_update_gap.setText(f"({time_gap})")
            except Exception as e:
                logger.error(f"시간 차이 계산 중 오류 발생: {e}")
                self.ui.label_update_gap.setText("(시간 계산 오류)")

    
    def connect_signals(self):
        self.ui.comboBox_edit_mode.currentTextChanged.connect(self.slot_edit_mode_changed )
        self.ui.PB_save.clicked.connect( lambda: self.save_requested.emit() )

    def disconnect_signals(self):
        try:
            self.ui.comboBox_edit_mode.currentTextChanged.disconnect(self.slot_edit_mode_changed )
            self.ui.PB_save.clicked.disconnect( lambda: self.save_requested.emit() )
        except Exception as e:
            logger.error(f"disconnect_signals : {e}")

    def slot_edit_mode_changed(self, mode:str):
        self.ui.PB_save.setVisible(mode.lower() == 'row')
        self.edit_mode_changed.emit(mode.lower())

    def set_ui_combo_edit_mode(self, mode:str):
        self.ui.comboBox_edit_mode.setCurrentText(mode)
