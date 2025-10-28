from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO
import copy, json
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

URL_BULK_UPDATE = 'bulk_update/'


def lookup_user_id_by_name(name: str) -> int | None:
    # 예시: INFO.USER_MAP_NAME_TO_ID = {'홍길동': 1, ...}
    user_id = INFO.USER_MAP_NAME_TO_USER.get(name, {}).get('id', None)
    if user_id is None:
        Utils.generate_QMsg_critical( None, title="사용자 검색 실패", text="사용자 검색 실패")
        return None
    return user_id

class CopyPasteTableView(QTableView):
    ALLOWED_COLUMNS = [ '1차 평가자', '2차 평가자']  # 허용된 column

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)


    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            self.handle_paste()
        else:
            super().keyPressEvent(event)

    def handle_paste(self):
        model = self.model()
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not model:
            return

        # 선택된 단일 셀만 허용
        indexes = self.selectedIndexes()
        if len(indexes) != 1:
            return
        index = indexes[0]

        col_name = model.columns[index.column()]
        if col_name not in self.ALLOWED_COLUMNS:
            return

        start_row = index.row()
        col = index.column()

        lines = text.strip().split('\n')
        for i, line in enumerate(lines):
            user_name = line.strip()
            user_id = lookup_user_id_by_name(user_name)
            if user_id is None:
                continue
            model_index = model.index(start_row + i, col)
            if model_index.isValid() and model.is_참여_enabled(model_index.row()):
                model.setData(model_index, user_id, Qt.EditRole)


class 평가체계도_TableModel(QAbstractTableModel):
    
    dataChangedExternally = pyqtSignal(dict)  # 변경된 row emit

    def __init__(self, parent=None, data:list[dict]=[]):
        super().__init__(parent)
        self._data = data
        self.user_map = INFO.USER_MAP_ID_TO_USER
        self.columns = ["is_참여", "기본조직3", "기본조직2", "기본조직1", 
                        "피평가자", "0차 평가자", "1차 평가자", "2차 평가자"]
        self.allowed_columns = [ "1차 평가자", "2차 평가자"]
        


    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        피평가자_idx = self.columns.index('피평가자')


        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        key = self.columns[col]
        피평가자_id = self._data[index.row()].get('피평가자')
        피평가자_dict = INFO.USER_MAP_ID_TO_USER[피평가자_id]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            match key:
                case 'is_참여':
                    return None  # 체크박스만 표시하므로 텍스트는 없음
                case '기본조직3':
                    return 피평가자_dict.get('기본조직3')
                case '기본조직2':
                    return 피평가자_dict.get('기본조직2')
                case '기본조직1':
                    return 피평가자_dict.get('기본조직1')
                case _:
                    user_id = self._data[row].get(key)
                    if user_id:
                        return self.user_map.get(user_id).get('user_성명','Unknown')
                    else:
                        return ''
                    
        
        if role == Qt.CheckStateRole and key == 'is_참여':
            return Qt.Checked if self._data[row].get('is_참여', False) else Qt.Unchecked
        
        if role == Qt.BackgroundRole:
            light_gray = QColor(211, 211, 211)  # 밝은 회색
            white = QColor(255, 255, 255)
            if not self._data[row].get('is_참여', False):
                return light_gray
            else:
                return white



    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()
        key = self.columns[col]

        if key == 'is_참여' and role == Qt.CheckStateRole:
            is_checked = int(value) == Qt.Checked.value
            self._data[row]['is_참여'] = is_checked
            start_index = self.index(row, 0)
            end_index = self.index(row, self.columnCount() - 1) 
            self.dataChanged.emit(start_index, end_index, [Qt.DisplayRole, Qt.CheckStateRole])
            self.dataChangedExternally.emit(self._data[row])
            return True

        if role == Qt.EditRole:
            self._data[row][key] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            self.dataChangedExternally.emit(self._data[row])
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        
        key = self.columns[index.column()]
        base_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        if key == 'is_참여':
            return base_flags | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        elif key in self.allowed_columns:
            return base_flags | Qt.ItemIsEditable
        else:
            return base_flags
        
    def is_참여_enabled(self, row:int):
        return self._data[row].get('is_참여', False)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return super().headerData(section, orientation, role)
    

class 평가체계도_Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.user_map = user_map
        # self.user_ids = list(user_map.keys())

    def createEditor(self, parent, option, index) -> QWidget:
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index) -> None:
        super().setEditorData(editor, index)
        # current_name = index.model().data(index, Qt.DisplayRole)
        # i = editor.findText(current_name)
        # if i >= 0:
        #     editor.setCurrentIndex(i)

    def setModelData(self, editor, model, index) -> None:
        if isinstance(editor, QLineEdit):            
            user_id  = lookup_user_id_by_name ( editor.text() )
            model.setData(index, user_id, Qt.EditRole)




class Wid_table_HR평가_평가체계도(QWidget):
    """
    data = [
    {"피평가자": 1, "0차 평가자": 1, "1차 평가자": 2, "2차 평가자": 3},
    {"피평가자": 4, "0차 평가자": 4, "1차 평가자": 2, "2차 평가자": 3},
]
    """
    api_result = pyqtSignal(bool)
    
    def __init__(self, parent=None, past_data:list[dict]=[] , 평가설정_fk:int=-1):        
        super().__init__(parent)
        self.평가설정_fk = 평가설정_fk
        self.past_data = past_data
        self.past_data_map = {f"{row['피평가자']}-{row['차수']}": row for row in copy.deepcopy(past_data)}
        self.full_data = self.generate_merged_evaluation_data(past_data)
        self.filtered_data = self.full_data.copy()
        self.original_map = {row["피평가자"]: row for row in copy.deepcopy(self.full_data)}
        self.changed_dict = {}  # {피평가자: 변경된 row}

        self.setup_table()
        self.UI()

        self.model.dataChangedExternally.connect(self.on_model_data_changed)

        self.update_statistics()

    def setup_table(self):
        self.model = 평가체계도_TableModel(self, self.filtered_data)
        self.view = CopyPasteTableView(self)
        self.delegate = 평가체계도_Delegate(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def UI(self):
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("이름 또는 조직명으로 검색")
        self.search_box.textChanged.connect(self.apply_filter)
        h_layout.addWidget(self.search_box)
        h_layout.addStretch()
        self.pb_save = QPushButton("저장")
        self.pb_save.setEnabled(False)  # ✅ 기본 비활성화
        self.pb_save.clicked.connect(self.on_save_data)
        h_layout.addWidget(self.pb_save)
        v_layout.addLayout(h_layout)

        self.stats_label = QLabel()
        v_layout.addWidget(self.stats_label)
        v_layout.addWidget(self.view)
        self.setLayout(v_layout)

    def on_model_data_changed(self, changed_row: dict):
        user_id = changed_row["피평가자"]
        original_row = self.original_map.get(user_id, None)
        logger.info(f"changed_row : {changed_row}")
        logger.info(f"original_row : {original_row}")
        if not original_row:
            return

        if changed_row == original_row:
            self.changed_dict.pop(user_id, None)
        else:
            self.changed_dict[user_id] = changed_row.copy()

        self.update_statistics()

    def on_save_data(self) :
        logger.info(f"변경된 평가체계 : {self.changed_dict}")

        payload = []
        payload = []
        for 피평가자_user_id, changed_row in self.changed_dict.items():
            for 차수 in [0, 1, 2]:
                past_row = self.past_data_map.get(f"{피평가자_user_id}-{차수}", None)
                if not past_row:
                    #### 신규 생성
                    past_row = {
                        "id" : -1,
                        "평가설정_fk": self.평가설정_fk,
                        "피평가자": 피평가자_user_id,
                        "차수": 차수,
                        "is_참여": changed_row.get('is_참여', True),
                        "평가자": changed_row.get(f"{차수}차 평가자", None),
                    }
                else:    
                    past_row['is_참여'] = changed_row.get('is_참여', True)
                    past_row['평가자'] = changed_row.get(f"{차수}차 평가자", None)
                payload.append(past_row)

        logger.info(f"변경된 평가체계 payload: {payload}")
        url = f"{INFO.URL_HR평가_평가체계DB}/{URL_BULK_UPDATE}/".replace('//', '/')
        is_ok, _json = APP.API.post(url, {'update_list': json.dumps(payload, ensure_ascii=False)})
        if is_ok:
            Utils.generate_QMsg_Information(self, title="평가체계도 저장 완료", text="평가체계도 저장 완료", autoClose=1000)
            self.api_result.emit(True)

        else:
            Utils.generate_QMsg_critical(self, title="평가체계도 저장 실패", text="평가체계도 저장 실패")
            self.api_result.emit(False)


    def apply_filter(self, text: str):
        text = text.strip().lower()
        self.filtered_data = []

        for row in self.full_data:
            user_id = row.get("피평가자")
            user = INFO.USER_MAP_ID_TO_USER.get(user_id, {})
            match_texts = [
                user.get("user_성명", ""),
                user.get("기본조직1", ""),
                user.get("기본조직2", ""),
                user.get("기본조직3", ""),
            ]
            if any(text in str(val).lower() for val in match_texts):
                self.filtered_data.append(row)

        # 모델에 필터된 데이터 적용
        self.model.beginResetModel()
        self.model._data = self.filtered_data
        self.model.endResetModel()
        self.update_statistics()


    def update_statistics(self):
        total = len(self.full_data)
        selected = sum(1 for row in self.full_data if row.get("is_참여"))
        changed = len(self.changed_dict)

        self.stats_label.setText(
            f"전체 {total}명 중 선택된 사람: {selected}명 (변경됨: {changed}명)"
        )
        self.pb_save.setEnabled(changed > 0)

    
    def generate_merged_evaluation_data(self, past_data:list[dict]):
        # 1. 최신 사용자 기반 기본 구조
        base_data = []
        user_map = {}  # {피평가자id: row index}
        
        sorted_user = sorted(INFO.ALL_USER, key=lambda x: (x.get('기본조직3',''), x.get('기본조직2',''), x.get('기본조직1','')))
        for idx, user in enumerate(sorted_user):
            row = {
                "is_참여": False,
                "피평가자": user.get('id'),
                "0차 평가자": user.get('id'),  # default는 자기자신
                "1차 평가자": None,
                "2차 평가자": None,
            }
            base_data.append(row)
            user_map[user.get('id')] = idx

        # 2. 과거 데이터 적용 (update)
        for item in past_data:
            피평가자 = item['피평가자']
            if 피평가자 not in user_map:
                continue  # 과거에는 있었지만 지금은 없는 사람 무시

            idx = user_map[피평가자]
            row = base_data[idx]
            row['is_참여'] = item.get('is_참여', row['is_참여'])

            차수 = item['차수']
            if 차수 in [0, 1, 2]:
                row[f"{차수}차 평가자"] = item['평가자']
        
        logger.info(f"평가체계도 생성 : base_data : {base_data}")

        return base_data
    
class Dialog_평가체계도(QDialog):

    def __init__(self, parent=None, past_data:list[dict]=[] , 평가설정_fk:int=-1):
        super().__init__(parent)
        self.past_data = past_data
        self.평가설정_fk = 평가설정_fk
        self.UI()       

    def UI(self):
        self.setMinimumSize(1000, 800)
        self.setWindowTitle('평가체계 구성')
        layout = QVBoxLayout()
        self.wid = Wid_table_HR평가_평가체계도(self, past_data=self.past_data, 평가설정_fk=self.평가설정_fk)
        self.wid.api_result.connect(self.on_api_result)
        layout.addWidget(self.wid)
        self.setLayout(layout)
        self.show()

    def on_api_result(self, is_ok:bool):
        if is_ok:
            self.accept()
        
