from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


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



class 상급자평가_Base_TableModel(QAbstractTableModel):
    HEADERS = ["제출","피평가자", "피평가자_제출","역량평가", "성과평가", "특별평가", "종합평가"]

    def __init__(self, data: list[dict], parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=None):
        if self._data:
            return len(self._data)
        return 0

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() :
            return QVariant()
        
        rowDict = self._data[index.row()]
        colNo:int = index.column()
        colName:str = self.HEADERS[colNo]

        if role == Qt.ItemDataRole.UserRole:
            return rowDict

        if role == Qt.ItemDataRole.DisplayRole:
            match colName:
                case "제출":
                    keyName = f"평가체계_data"
                    is_submit = rowDict[keyName]["is_submit"]
                    return "제출" if is_submit else "미제출"
                case "피평가자":
                    keyName = f"평가체계_data"
                    피평가자_id = rowDict.get(keyName).get('피평가자')
                    user_info = INFO.USER_MAP_ID_TO_USER[int(피평가자_id)]
                    return f"{user_info.get('user_성명')}"
                case "역량평가"|"성과평가"|"특별평가":
                    keyName = f"{colName}_fk"
                    평가점수 = rowDict[keyName]["평가점수"]
                    return f"{평가점수:.2f}"
                case "피평가자_제출":
                    try:
                        keyName = f"피평가자_본인평가"
                        피평가자_is_submit = rowDict[keyName]['평가체계_data']['is_submit']
                        return "제출" if 피평가자_is_submit else "미제출"   
                    except Exception as e:
                        logger.error(f"피평가자_제출 오류: {e}")
                        return ""
                
                case "종합평가":
                    keyName = f"평가체계_data"
                    종합평가 = rowDict[keyName]["종합평가"]
                    return f"{종합평가:.2f}"
                
                case "등록일":
                    keyName = f"평가체계_data"
                    등록일 = rowDict[keyName]["등록일"]
                    return f"{등록일}"

                    
        if role == Qt.ItemDataRole.BackgroundRole:
            if self.is_editable(index):
                return QColor(255, 255, 255)
            else:
                if self.check_submit_status(rowNo=index.row()):
                    return QColor("#d0f0c0")  # 배경
                else:
                    return QColor(Qt.GlobalColor.red)
            
        if role == Qt.ItemDataRole.ForegroundRole:
            if self.is_editable(index):
                return QColor(Qt.GlobalColor.black)
            else:
                if self.check_submit_status(rowNo=index.row()):
                    return QColor("#2f6f1f")  # 글자
                else:
                    return QColor(Qt.GlobalColor.white)
                    


        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()

        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def flags(self, index):
        if self.is_editable(index):
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def is_editable(self, index):
        """ 피평가자가 제출한 경우 상급자 평가 실시 가능 """
        try:
            rowDict = self._data[index.row()]
            keyName = f"피평가자_본인평가"
            피평가자_is_submit = rowDict.get(keyName, {}).get('평가체계_data', {}).get('is_submit', False)

            submit_status = self.check_submit_status(rowNo=index.row())

            return 피평가자_is_submit and not submit_status
        except Exception as e:
            logger.error(f"is_editable 오류: {e}")
            return False
        
    def set_row_data(self, index:QModelIndex, rowDict:dict):
        self._data[index.row()] = rowDict
        self.dataChanged.emit(index, index)

    def get_data(self):
        return self._data
    
    def check_all_submit_status(self) -> bool:
        """ 모든 평가가 제출되었는지 확인 , 모두 제출되었으면 True, 아니면 False 반환 """
        if not self._data:
            return True
        _is_all_submit = all(self.check_submit_status(rowDict=rowDict) for rowDict in self._data )
        return _is_all_submit
    
    def check_submit_status(self, rowDict:dict=None, rowNo:int=None) -> bool:
        """ 평가가 제출되었는지 확인 , 제출되었으면 True, 아니면 False 반환 
            rowDict 또는 rowNo 중 하나만 전달 가능
        """
        if rowDict:
            return rowDict['평가체계_data']['is_submit']
        elif rowNo is not None:
            return self._data[rowNo]['평가체계_data']['is_submit']
        else:
            return False



class 세부평가_Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        return None
    
    def editorEvent(self, event, model:상급자평가_Base_TableModel, option, index):
        """ 피평가자가 제출한 경우 상급자 평가 실시 가능 """
   
        if not model.is_editable(index):
            return False
        colName = model.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        if colName in [ "역량평가", "성과평가", "특별평가"]:
            rowDict = model.data(index, Qt.ItemDataRole.UserRole)
            logger.info(f"editorEvent : rowDict: {rowDict}")
            if isinstance(rowDict, QVariant):
                rowDict = rowDict.value()
                if not isinstance(rowDict, dict):
                    raise ValueError(f"rowDict is not dict even after QVariant: {type(rowDict)}")
            elif isinstance(rowDict, dict):
                pass
            else:
                raise ValueError(f"rowDict is not QVariant or dict: {type(rowDict)}")
            
            try:
                from modules.PyQt.Tabs.HR평가.HR평가_본인평가 import 본인평가__for_Tab
                dlg = QDialog(self.parent())
                dlg.setMinimumSize(1200, 800)
                layout = QVBoxLayout(dlg)
                app_dict = INFO.APP_권한_MAP_ID_TO_APP[167] #### 본인평가 앱 정보
                wid_세부평가 = 본인평가__for_Tab(dlg, **app_dict)
                param = f"?action=상급자평가&평가체계_fk={rowDict.get('평가체계_data').get('id')}"
                url = f'HR평가/세부평가_Api_View/'
                #### 
                wid_세부평가.run_by_(url=url, param=param, is_external_exec=True , external_data =rowDict )

                layout.addWidget(wid_세부평가)
                wid_세부평가.api_data_changed.connect(lambda api_data: model.set_row_data(index, api_data))
                if dlg.exec():
                    pass
            except Exception as e:
                logger.error(f"세부평가 오류: {e}")
                logger.error(traceback.format_exc())
                return False

            return True
        return False
    

    
    def is_save_before(self, rowDict:dict):
        """ 상급자 평가가 최초인지 확인하여, 한번도 안 했으면 피평가자 제출한 자료 줌. """
        역량평가_api_datas = rowDict.get('역량평가_fk').get('역량평가_api_datas')
        성과평가_api_datas = rowDict.get('성과평가_fk').get('성과평가_api_datas')
        특별평가_api_datas = rowDict.get('특별평가_fk').get('특별평가_api_datas')
        if all ( [ bool(역량평가_api_datas), bool(성과평가_api_datas), bool(특별평가_api_datas) ] ):
            return True
        else: 
            return False


class Wid_table_상급자평가_개별(QWidget):
    def __init__(self, parent=None,  api_data: list[dict] = None):
        super().__init__(parent)
        self.api_data = api_data
        self.UI()

    def UI(self):
        layout = QVBoxLayout(self)

        self.table = QTableView()
        self.model = 상급자평가_Base_TableModel(self.api_data)
        self.table.setModel(self.model)
        self.delegate = 세부평가_Delegate(self)
        self.table.setItemDelegate( self.delegate )
        self.table.resizeColumnsToContents()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
    
    def set_data(self, api_data: list[dict]):
        self.api_data = api_data
        self.model = 상급자평가_Base_TableModel(self.api_data)
        self.table.setModel(self.model)



if __name__ == '__main__':
    api_datas= [{'id': 10597, '차수': 1, 'is_참여': True, '평가설정_fk': 44, '평가자': 1, '피평가자': 2, '역량평가': {'id': 512, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10597}, '성과평가': {'id': 512, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10597}, '특별평가': {'id': 512, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10597}}]

    app = QApplication([])
    main_window = QMainWindow()
    wid_table = Wid_table_상급자평가_개별(main_window)
    wid_table.set_data(api_datas)
    main_window.setCentralWidget(wid_table)
    main_window.show()
    app.exec()