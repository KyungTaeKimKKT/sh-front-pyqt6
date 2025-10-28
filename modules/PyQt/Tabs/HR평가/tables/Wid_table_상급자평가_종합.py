from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


from modules.PyQt.Tabs.HR평가.tables.Wid_table_상급자평가_base import 상급자평가_Base_TableModel
import json, os, io, copy
import platform
from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class 평가결과TableModel(상급자평가_Base_TableModel):

    def set_data(self, api_data: list[dict]):
        self._data = api_data
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data) - 1, len(self.HEADERS) - 1))

        
    
    def is_editable(self, index) -> bool:
        """ base class override : 피평가자가 제출한 경우 상급자 평가 실시 가능 
            여기서는 column 에 따라서 return 값을 다르게 해야 함.
        """
        try:
            rowDict = self._data[index.row()]
            keyName = f"피평가자_본인평가"
            피평가자_is_submit = rowDict.get(keyName, {}).get('평가체계_data', {}).get('is_submit', False)
            submit_status = self.check_submit_status(rowDict=rowDict)

            final_editable = 피평가자_is_submit and not submit_status
            if final_editable:
                headerName = self.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                return  headerName in ["역량평가", "성과평가", "특별평가"]
            else:
                return False
        except Exception as e:
            logger.error(f"is_editable 오류: {e}")
            return False

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            headerName = self.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            keyName = f"{headerName}_fk"
            self._data[index.row()][keyName]["평가점수"] = value
            self._data[index.row()]["평가체계_data"]["종합평가"] = self.calculate_종합평가(self._data[index.row()])
            # ✅ 행 전체 emit
            topLeft = self.index(index.row(), 0)
            bottomRight = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(topLeft, bottomRight)
            return True
        return False
    
    def calculate_종합평가(self, rowDict:dict):
        평가설정_data = rowDict["평가설정_data"]
        평가체계_data = rowDict["평가체계_data"]
        if 평가설정_data:
            차수 = 평가체계_data["차수"]
            점유_역량 = 평가설정_data["점유_역량"]
            점유_성과 = 평가설정_data["점유_성과"]
            점유_특별 = 평가설정_data["점유_특별"]
            종합평가 =  (
                rowDict["역량평가_fk"]["평가점수"] * 점유_역량  
                + rowDict["성과평가_fk"]["평가점수"] * 점유_성과
                + rowDict["특별평가_fk"]["평가점수"] * 점유_특별
                ) / 100
            return 종합평가
        return 0.0
    
    def get_graph_data(self):
        """ {id: 종합평가} 형태로 반환 """

        graph_data:dict[int,float] = {
             rowDict['평가체계_data']['피평가자']: rowDict['평가체계_data']['종합평가']
             for rowDict in self._data
        }
        return graph_data
    



from modules.PyQt.compoent_v2.custom_상속.custom_spinbox import Custom_DobleSpinBox
class 평가_spinbox(Custom_DobleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 5.0)
        self.setSingleStep(0.01)



class 상급자평가_종합_Delegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return 평가_spinbox(parent)
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if isinstance( editor, 평가_spinbox):
            editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        if isinstance( editor, 평가_spinbox):
            model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class Wid_table_상급자평가_종합(QWidget):
    def __init__(self, parent=None,  api_data: list[dict] = None):
        super().__init__(parent)
        self.api_data = api_data
        self.is_set_model = False

        self.UI()
        self.check_submit_status()
    
    def UI(self):
        layout = QVBoxLayout(self)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        self.PB_TempSave = QPushButton("임시저장")  
        self.PB_TempSave.setEnabled(False)
        self.PB_TempSave.clicked.connect(self.on_temp_save_clicked)
        btn_layout.addWidget(self.PB_TempSave)
        self.PB_Submit = QPushButton("최종 제출")
        self.PB_Submit.setEnabled(False)
        self.PB_Submit.clicked.connect(self.on_submit_clicked)
        btn_layout.addWidget(self.PB_Submit)
        layout.addWidget(btn_container)

        self.table = QTableView()
        self.model = 평가결과TableModel(self.api_data)
        self.table.setModel(self.model)
        self.delegate = 상급자평가_종합_Delegate(self)
        self.table.setItemDelegate(self.delegate)

        self.table.resizeColumnsToContents()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
    
    def on_temp_save_clicked(self):
        model_data = self.model.get_data()
        if self.api_send(model_data):
            Utils.generate_QMsg_Information(self, title="임시저장 완료", text="임시저장 완료", autoClose=1000)
        else:
            Utils.generate_QMsg_critical(self, title="임시저장 실패", text="임시저장 실패")
        
    
    def on_submit_clicked(self):
        """ confirm dialog 표시 후 제출 
            confirm dialog는 histogram 형태로 표시됨.
        """
        from modules.PyQt.Tabs.HR평가.dialog.dlg_histogram import Dlg_상급자_종합평가_제출_확인
        dlg = Dlg_상급자_종합평가_제출_확인(self, data_dict=self.model.get_graph_data(), title="상급자 종합평가 제출 확인")
        if not dlg.exec():
            return
        
        model_data = self.model.get_data()
        for row in model_data:
            row["평가체계_data"]["is_submit"] = True
        if self.api_send(model_data):
            self.set_data(model_data)
            Utils.generate_QMsg_Information(self, title="최종 제출 완료", text="최종 제출 완료", autoClose=1000)
        else:
            Utils.generate_QMsg_critical(self, title="최종 제출 실패", text="최종 제출 실패")

    
    def set_data(self, api_data: list[dict]):
        self.api_data = api_data
        if self.is_set_model:
            self.model.set_data(self.api_data)
        
        else:
            self.model = 평가결과TableModel(self.api_data)
            self.table.setModel(self.model)

        self.is_set_model = True
        self.check_submit_status()

    def check_submit_status(self):
        if self.model.check_all_submit_status():
            self.PB_TempSave.setEnabled(False)
            self.PB_Submit.setEnabled(False)
            self.PB_Submit.setText("제출이 완료되었읍니다.")
        else:
            self.PB_TempSave.setEnabled(True)
            self.PB_Submit.setEnabled(True)
            self.PB_Submit.setText("최종 제출")

    def api_send(self, model_data: list[dict]):
        URL = 'HR평가_V2/상급자평가_BatchUpdate_Api_View/'
        _isok, _json = APP.API.post_json(URL, model_data)
        if _isok:
            return True
        else:
            return False

if __name__ == '__main__':
    api_datas=  [{'id': 10694, '차수': 2, 'is_참여': True, '평가설정_fk': 44, '평가자': 1, '피평가자': 2, '역량평가': {'id': 609, 'is_submit': False, '평가종류': '종합', '평가점수': 0.0, '평가체계_fk': 10694}, '성과평가': {'id': 609, 'is_submit': False, '평가종류': '종합', '평가점수': 0.0, '평가체계_fk': 10694}, '특별평가': {'id': 609, 'is_submit': False, '평가종류': '종합', '평가점수': 0.0, '평가체계_fk': 10694}}]

    app = QApplication([])
    main_window = QMainWindow()
    wid_table = Wid_table_상급자평가_종합(main_window)
    wid_table.set_data(api_datas)
    main_window.setCentralWidget(wid_table)
    main_window.show()
    app.exec()