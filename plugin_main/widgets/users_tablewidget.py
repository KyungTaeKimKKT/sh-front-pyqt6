from typing import Any, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
import json, copy
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model_Mixin
class TableModel_Users(QAbstractTableModel, Base_Table_Model_Mixin):
    selected_changed  = pyqtSignal(dict)

    def __init__(self, parent=None, pre_selected_ids:list[dict]=None, all_users:list[dict]=None, view_type:str='select', user_attr:str='user_id'):
        super().__init__(parent)
        self.view_type = view_type
        self.pre_selected_ids = pre_selected_ids        
        self.all_users = self.get_all_users_except_admin(all_users)
        self.user_attr = self.check_is_user_attr(user_attr)
        print(f"{self.__class__.__name__} : __init__ : self.user_attr : {self.user_attr}")
        self._data :list[dict] = self.create_data()

        self.create_map_id_to_data()


    def check_is_user_attr(self, attr:str)->bool:
        print(f"{self.__class__.__name__} : check_is_user_attr : {attr} : {self.pre_selected_ids}")
        if not self.pre_selected_ids:
            return attr
        
        if attr in self.pre_selected_ids[0]:
            return attr
        if 'user' in self.pre_selected_ids[0]:
            return 'user'
        if 'user_fk' in self.pre_selected_ids[0]:
            return 'user_fk'
        return attr
    
    
    def get_map_id_to_selected_ids(self) -> dict[int, dict]:
        map = { selected.get(self.user_attr): selected for selected in self.pre_selected_ids } if self.pre_selected_ids else {}
        return map
    

    def create_map_id_to_data(self):
        self.map_id_to_data = { userObj.get(self.user_attr): userObj for userObj in self._data }
    
    def get_all_users_except_admin(self, all_users:Optional[list[dict]] =None) -> list[dict]:
        if all_users is None or not all_users:
            all_users = copy.deepcopy(INFO.ALL_USER)
        return [ userObj for userObj in all_users if userObj.get('id') != 1 ]



    @property
    def map_head_attr(self):
        return  {
            'id': 'id',
            'is_선택': 'is_선택',
            self.user_attr:  self.user_attr,
            '조직(3차)': '기본조직3',
            '조직(2차)': '기본조직2',
            '조직(1차)': '기본조직1',
            '성명': 'user_성명'
        }
    @property
    def headers(self):
        return list(self.map_head_attr.keys())

    def create_data(self):
        _data = []
        for user in self.all_users:            
            user_id = user['id']
            is_선택:bool = bool(user_id in self.get_map_id_to_selected_ids())
            _data.append({
                'id':  self.get_map_id_to_selected_ids()[user_id].get('id', -1) if is_선택 else -1,
                self.user_attr: user_id,
                '조직(3차)': user.get('기본조직3'),
                '조직(2차)': user.get('기본조직2'),
                '조직(1차)': user.get('기본조직1'),
                '성명': user.get('user_성명'),
                'is_선택': is_선택
            })
        self._data = _data
        return _data


    def get_headers(self):
        return self.headers

    def update_data(self, data:list[dict]):
        self._data = data
        self.layoutChanged.emit()

    def data(self, index:QModelIndex, role:Qt.ItemDataRole):
        userObj = self._data[index.row()]
        display_name = self.get_headers()[index.column()]
        if role == Qt.ItemDataRole.UserRole:
            return userObj

        if role == Qt.ItemDataRole.CheckStateRole:
            if display_name == 'is_선택':
                return Qt.Checked if userObj.get('is_선택') else Qt.Unchecked

        if role == Qt.ItemDataRole.DisplayRole:
            if display_name == 'is_선택':
                return '예' if userObj.get('is_선택') else '아니오'
            return self._data[index.row()][display_name]

        if role == Qt.ItemDataRole.BackgroundRole:
            is_selected = userObj.get('is_선택')
            if is_selected:
                return QColor(200, 255, 200)  # 연한 녹색
            else:
                return QColor(Qt.GlobalColor.white)
    
    def setData(self, index:QModelIndex, value:Any, role:int) -> bool:

        if role == Qt.ItemDataRole.CheckStateRole and self.is_check_column_no(index.column()):
            if self.view_type == 'preview':
                return False  # preview에서는 무조건 차단
            userObj = self._data[index.row()]
            userObj['is_선택'] = value == Qt.CheckState.Checked
            start_index = self.index(index.row(), 0)
            end_index = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole])
            self.selected_changed.emit(userObj)
            return True
        return False
    
    def is_check_column_no(self, column:int) -> bool:
        return 'is_선택' == self.get_headers()[column]
    
    ### basic methods
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if self.is_check_column_no(index.column()):
            if getattr(self, 'view_type', 'select') == 'preview':
                return Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable  # enabled 제거
            return Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        else:
            if getattr(self, 'view_type', 'select') == 'preview':
                return Qt.ItemFlag.ItemIsSelectable  # enabled 제거
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def rowCount(self, parent:QModelIndex=None):
        return len(self._data)
    
    def columnCount(self, parent:QModelIndex=None):
        return len(self.get_headers())
    
    def headerData(self, section:int, orientation:Qt.Orientation, role:Qt.ItemDataRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.get_headers()[section]
        return None

    ####
    def sync_with_tree(self, userObj:dict):
        """ userObj : {'is_선택':bool, 'user_id':int} 형태"""
        user_id = userObj['user_id']
        print ( 'user_id : ', user_id, self.map_id_to_data, user_id in self.map_id_to_data)
        if user_id in self.map_id_to_data:
            self.map_id_to_data[user_id]['is_선택'] = userObj['is_선택']    
            self.layoutChanged.emit()

    def get_checked_user_ids(self) -> list[int]:
        """ 선택된 사용자 ID 목록 반환 """
        return [userObj[self.user_attr] for userObj in self._data if userObj['is_선택']]

    def add_select_user(self, user_info_dict):
        self._data.append(user_info_dict)
        self.layoutChanged.emit()

    def remove_select_user(self, m2m_user_dict):
        self._data.remove(m2m_user_dict)
        self.layoutChanged.emit()

    #### moethod
    def remove_user_by_index(self, index:QModelIndex):
        self._data.pop(index.row())
        self.layoutChanged.emit()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """DisplayRole 기준으로 정렬"""
        if not self._data:
            return

        super().mixin_sort_by_display_role(column, order)

from modules.PyQt.compoent_v2.table.mixin_table_view import Mixin_Table_View
class TableView_Users(QTableView, Mixin_Table_View):
    row_deleted_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.setSortingEnabled(True)  # ✅ 정렬 활성화
        # self.setEditTriggers( QAbstractItemView.EditTrigger.SelectedClicked)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # self.doubleClicked.connect(self.on_double_clicked)

    def on_double_clicked(self, index:QModelIndex):
        model: TableModel_Users = self.model()
        userObj = model.data(index, Qt.ItemDataRole.UserRole)
        if hasattr(model, "remove_user_by_index"):
            model.remove_user_by_index(index)
        
        self.row_deleted_signal.emit(userObj)

class Delegate_Users(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def editorEvent(self, event, model, option, index):
        if hasattr(model, 'view_type') and model.view_type == 'preview':
            return False  # preview 모드에선 체크박스 변경 금지

        flags = index.flags()
        if (flags & Qt.ItemIsUserCheckable) and (flags & Qt.ItemIsEditable) and index.data(Qt.CheckStateRole) is not None:
            if event.type() in (QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick):
                new_val = Qt.Unchecked if index.data(Qt.CheckStateRole) == Qt.Checked else Qt.Checked
                model.setData(index, new_val, Qt.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)



class UsersTableWidget(QWidget):
    row_deleted_signal = pyqtSignal(dict)
    selected_changed = pyqtSignal(dict)
    def __init__(self, parent=None, pre_selected_ids:list[dict]=None, all_users:list[dict]=None, view_type:str='select', **kwargs):
        super().__init__(parent)
        self.pre_selected_ids = pre_selected_ids
        self.all_users = all_users or copy.deepcopy(INFO.ALL_USER)
        self.view_type = view_type
        self.setup_ui()
    
    def create_table(self):
        self.view = TableView_Users(self)
        self.model = TableModel_Users(self, self.pre_selected_ids, self.all_users, view_type=self.view_type)
        self.model.selected_changed.connect(lambda userObj: self.selected_changed.emit(userObj))
        self.delegate = Delegate_Users(self)
        self.view.setModel(self.model) 
        self.view.setItemDelegate(self.delegate)

    def closeEvent(self, event:QCloseEvent):
        try:
            self.row_deleted_signal.disconnect()
        except Exception as e:
            logger.error(f"UsersTableWidget closeEvent 오류: {e}")
        super().closeEvent(event)

    def setup_ui(self):
        self.create_table()
        self.v_layout = QVBoxLayout(self)
        self.v_layout.addWidget(self.view)
        self.setLayout(self.v_layout)

    def update_data(self, data:list[dict]):
        self.model.update_data(data)
        self.view.resizeColumnsToContents()
        self.view.resizeRowsToContents()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        self.model.sort(column, order)

    def add_select_user(self, user_info_dict):
        self.model.add_select_user(user_info_dict)

    def remove_select_user(self, m2m_user_dict):
        self.model.remove_select_user(m2m_user_dict)


    def sync_with_tree(self, userObj:dict):
        """ userObj : {'is_선택':bool, 'user_id':int} 형태"""
        self.model.sync_with_tree(userObj)

    def get_checked_user_ids(self) -> list[int]:
        """ 선택된 사용자 ID 목록 반환 """
        return self.model.get_checked_user_ids()
