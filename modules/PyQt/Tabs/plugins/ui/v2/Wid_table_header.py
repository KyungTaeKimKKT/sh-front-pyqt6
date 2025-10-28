from __future__ import annotations
from typing import Optional

from modules.PyQt.Tabs.plugins.ui.Ui_table_head import Ui_tableheader

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.custom_상속.custom_PB import Custom_PB_Query
from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode

class Wid_Table_Header(QWidget):
    edit_mode_changed = pyqtSignal(str) ### 'row' or 'cell' or 'no'
    save_requested = pyqtSignal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_update_time: Optional[QDateTime] = None
        
        self.setup_ui()
        self.connect_signals()



    def setup_ui(self):

        self.setObjectName("tableheader")
        self.resize(1378, 61)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.main_layout = QHBoxLayout(self)

        ### 1. Data Update 시간
        self.lb_update = QLabel(parent=self)
        self.lb_update.setText("Data Update 시간")
        self.main_layout.addWidget(self.lb_update)

        ### 2. Data Update 시간
        self.lb_update_time = QLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_update_time.sizePolicy().hasHeightForWidth())
        self.lb_update_time.setSizePolicy(sizePolicy)
        self.lb_update_time.setStyleSheet("background-color:yellow;font-weight:bold;padding:5px, 0px;")
        self.lb_update_time.setAlignment( Qt.AlignmentFlag.AlignCenter)
        self.lb_update_time.setObjectName("label_update_time")
        self.main_layout.addWidget(self.lb_update_time)

        ### 3. Data Update 시간 차이
        self.lb_update_gap = QLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_update_gap.sizePolicy().hasHeightForWidth())
        self.lb_update_gap.setSizePolicy(sizePolicy)
        self.lb_update_gap.setStyleSheet("font-weight:bold")
        self.lb_update_gap.setObjectName("label_update_gap")
        self.main_layout.addWidget(self.lb_update_gap)
        spacerItem = QSpacerItem(120, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem)

        ### 4. lable 편집모드
        self.lb_edit_mode = QLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_edit_mode.sizePolicy().hasHeightForWidth())
        self.lb_edit_mode.setSizePolicy(sizePolicy)
        self.lb_edit_mode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb_edit_mode.setObjectName("label_8")
        self.main_layout.addWidget(self.lb_edit_mode)

        ### 5. 편집모드 콤보박스
        self.comboBox_edit_mode = Combo_Select_Edit_Mode(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_edit_mode.sizePolicy().hasHeightForWidth())
        self.comboBox_edit_mode.setSizePolicy(sizePolicy)
        self.comboBox_edit_mode.setObjectName("comboBox_edit_mode")
        self.main_layout.addWidget(self.comboBox_edit_mode)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addItem(spacerItem1)
        
        self.PB_save = Custom_PB_Query(parent=self)
        self.PB_save.setText("Row 저장")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PB_save.sizePolicy().hasHeightForWidth())
        self.PB_save.setSizePolicy(sizePolicy)
        self.PB_save.setObjectName("PB_save")
        self.main_layout.addWidget(self.PB_save)


       
    def closeEvent(self, event):
        self.disconnect_signals()
        super().closeEvent(event)

    def hide_modeCombo_and_saveButton(self):
        self.lb_edit_mode.setVisible(False)
        self.comboBox_edit_mode.setVisible(False)
        self.PB_save.setVisible(False)
        
    def update_api_query_time(self):
        now = QDateTime.currentDateTime()
        if self.last_update_time is not None:
            seconds = self.last_update_time.secsTo(now)
            if seconds < 60:
                gap_text = f"({seconds}초 전)"
            elif seconds < 3600:
                minutes = seconds // 60
                gap_text = f"({minutes}분 전)"
            else:
                hours = seconds // 3600
                remaining_minutes = (seconds % 3600) // 60
                gap_text = f"({hours}시간 {remaining_minutes}분 전)"
        else:
            gap_text = ' (방금 전) '
        self.lb_update_time.setText(now.toString("HH:mm:ss"))
        self.lb_update_gap.setText(gap_text)

        self.last_update_time = now
    

    
    def connect_signals(self):
        self.comboBox_edit_mode.currentTextChanged.connect(self.slot_edit_mode_changed )
        self.PB_save.clicked.connect( lambda: self.save_requested.emit() )

    def disconnect_signals(self):
        try:
            self.comboBox_edit_mode.currentTextChanged.disconnect(self.slot_edit_mode_changed )
            self.PB_save.clicked.disconnect( lambda: self.save_requested.emit() )
        except Exception as e:
            logger.error(f"disconnect_signals : {e}")

    def slot_edit_mode_changed(self, mode:str):
        self.PB_save.setVisible(mode.lower() == 'row')
        self.edit_mode_changed.emit(mode.lower())

    def set_ui_combo_edit_mode(self, mode:str):
        self.comboBox_edit_mode.setCurrentText(mode)
