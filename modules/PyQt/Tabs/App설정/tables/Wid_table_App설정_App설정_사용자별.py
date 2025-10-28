from PyQt6.QtGui import QColor
from modules.common_import_v2 import *


class TableView_App설정_App설정_사용자별(Base_Table_View):
    pass


class TableModel_App설정_App설정_사용자별(Base_Table_Model):

    @property
    def CHECK_COLUMN_ATTR_NAME(self):
        return 'is_user'

    def clear_all_select(self):
        for row in self._data:
            row[self.CHECK_COLUMN_ATTR_NAME] = False
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data) - 1, 0), [Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.CheckStateRole])
        self.layoutChanged.emit()

    def select_all(self):
        for row in self._data:
            row[self.CHECK_COLUMN_ATTR_NAME] = True
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data) - 1, 0), [Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.CheckStateRole])
        self.layoutChanged.emit()
    #### methods
    def get_checked_rows(self) -> list[dict]:
        return [row for row in self._data if row[self.CHECK_COLUMN_ATTR_NAME]]
    
    def get_changed_rows(self) -> list[dict]:
        """ 변경된 행 목록 반환 """
        changed_rows = []
        for original, current in zip(self._original_api_datas, self._data):
            if original != current :
                changed_rows.append(current)
        return changed_rows

    def is_check_column_no(self, column:int) -> bool:
        return self.CHECK_COLUMN_ATTR_NAME == self.get_attr_name_by_column_no(column)
    
    #### basic
    def _role_background(self, row: int, col: int) -> QColor:
        if self._data[row][self.CHECK_COLUMN_ATTR_NAME]:
            return QColor(255, 255, 204)  # RGB
        return super()._role_background(row, col)
    
    def _role_checkState(self, row:int, col:int) -> Qt.CheckState:
        return super()._role_checkState(row, col)

    def flags(self, index:QModelIndex) -> Qt.ItemFlags:
        if self.is_check_column_no(index.column()):            
            return Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
    def setData(self, index:QModelIndex, value:Any, role:int) -> bool:

        if role == Qt.ItemDataRole.CheckStateRole and self.is_check_column_no(index.column()):
            userObj = self._data[index.row()]
            userObj[self.CHECK_COLUMN_ATTR_NAME] = value == Qt.CheckState.Checked
            start_index = self.index(index.row(), 0)
            end_index = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole])
            # value = value == Qt.CheckState.Checked
            # self.setData_by_edit_mode(index, value, role)
            return True
        return False

    def on_api_send_By_Row(self):
        """ api view로 bulk로 보낼 것임"""
        changed_rows = self.get_changed_rows()
        prev_enabled_app_count = len ( [ _obj for _obj in self._original_data if _obj['is_user']  ] )
        current_enabled_app_count = len ( [ _obj for _obj in self._data if _obj['is_user']  ] )
        권한_추가된_앱_개수 = len ( [ _obj for _obj in changed_rows if _obj['is_user']  ] ) 
        권한_삭제된_앱_개수 = len ( [ _obj for _obj in changed_rows if not _obj['is_user']  ] ) 
        검증결과 = '예' if current_enabled_app_count == prev_enabled_app_count + 권한_추가된_앱_개수 - 권한_삭제된_앱_개수 else '아니오'
        _text = f"""
        <b style="color:#2c3e50; font-size: 13pt;">사용자 권한 변경 요약</b><br><br>
        <span style="color:#34495e;">이전 사용자 앱 개수:</span> <b>{prev_enabled_app_count}</b><br>
        <span style="color:#34495e;">현재 사용자 앱 개수:</span> <b>{current_enabled_app_count}</b><br><br>
        <u>상세내용</u><br>
        <span style="color:green;">➕ 권한 추가된 앱 개수:</span> <b>{권한_추가된_앱_개수}</b><br>
        <span style="color:red;">➖ 권한 삭제된 앱 개수:</span> <b>{권한_삭제된_앱_개수}</b><br><br>
        <b>🛠️ 검증결과:</b> <span style="color:#2980b9;">{검증결과}</span>
        """
        if not Utils.QMsg_question( None, title='API 호출 검증', text= _text ):
            return False

        if changed_rows:            
            send_data = []
            user_id = changed_rows[0]['user_id']
            for row in changed_rows:
                _obj  = copy.deepcopy(row)
                for key in list(row.keys()):
                    if key not in ['id', 'app_권한_id', 'is_user']:
                        del _obj[key]
                send_data.append(_obj)
            isok, _json = APP.API.post_json(url= f"{self.url}?user_id={user_id}", data= send_data )
            if isok:          
                self.clear_all_modifications()
                self.on_api_datas_received(_json)                
                Utils.QMsg_Info( None, title='API 호출 성공', text='API 호출 성공' , autoClose=1000)
                return True
            else:
                Utils.QMsg_critical( None, title='API 호출 실패', text=f'API 호출 실패<br>{json.dumps(_json, indent=4)}' )
                return False
        
 

class TableDelegate_App설정_App설정_사용자별(Base_Delegate):
    def editorEvent(self, event, model, option, index):
        if index.flags() & Qt.ItemFlag.ItemIsUserCheckable and index.data(Qt.ItemDataRole.CheckStateRole) is not None:
            if event.type() in (QEvent.Type.MouseButtonRelease, QEvent.MouseButtonDblClick):
                new_val = Qt.CheckState.Unchecked if index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked else Qt.CheckState.Checked
                model.setData(index, new_val, Qt.ItemDataRole.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)
    
       

class Wid_table_App설정_App설정_사용자별( Wid_table_Base_V2 ):

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()

    def setup_table(self):
        self.view = TableView_App설정_App설정_사용자별(self)
        self.model = TableModel_App설정_App설정_사용자별(self.view)
        self.delegate = TableDelegate_App설정_App설정_사용자별(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()
        # self.subscribe_gbus()




    def get_model_data(self):
        return self.model._data

    def get_changed_rows(self) -> list[dict]:
        return self.model.get_changed_rows()


    def on_clear_all(self):
        if Utils.QMsg_question(None, 
                               title='사용자 권한 초기화', 
                               text='사용자 권한 초기화 하시겠습니까?'):
            self.model.clear_all_select()


    def on_select_all(self):
        if Utils.QMsg_question(None, 
                               title='사용자 권한 전체 선택', 
                               text='사용자 권한 전체 선택 하시겠습니까?'):
            self.model.select_all()

