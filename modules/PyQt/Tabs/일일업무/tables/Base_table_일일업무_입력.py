from modules.common_import_v2 import *

class Base_TableView_일일업무_입력(Base_Table_View):
    pass


class Base_TableModel_일일업무_입력(Base_Table_Model):
    # lazy_attr_names = INFO.Table_Model_Lazy_Attr_Names 

    _3days = {}         #### { '어제, 오늘,내일' : 날짜str}
    _3days_reverse = {} #### { 날짜str : '어제, 오늘,내일' }
    _editable_3days = {} #### {날짜: True or False }

    일자_COLUMN_NO = None
    일자_attr_name = '일자'
    add_row_dict = {
        'remaining_keys': ['일자'],
        'remaining_add_dict': {},
        'update_dict': {
            'id': -1,
            '소요시간': 0,
            '등록자_id': INFO.USERID,
        },
    }

    def get_3days_by_api(self:Base_Table_Model):
        """ 3일 조회 후 데이터 저장 """
        if self.table_name and self.url:
            is_ok, _json = APP.API.getlist( self.url + 'get_3days/')
            if is_ok:
                logger.info(f"on_lazy_attr_ready:  'get_3days' 호출 성공: {_json}")
                self._3days = _json
                self._editable_3days = { day: True if txt_순서 in ['오늘', '내일', '금일'] else False for txt_순서, day  in self._3days.items()   }
                self._3days_reverse = { day: txt_순서 for txt_순서, day  in self._3days.items()   }
                self.layoutChanged.emit()
            else:
                logger.error(f"on_lazy_attr_ready: {_json}")
        else:
            raise Exception(f"table_name 또는 url이 없읍니다.")

    def on_all_lazy_attrs_ready(self, APP_ID:Optional[int] = None, **kwargs):
        super().on_all_lazy_attrs_ready(APP_ID, **kwargs)
        self.get_3days_by_api()


    def is_일자_column(self, col:int) -> bool:
        return '일자' == self.get_attr_name_by_column_no(col)

    def _role_display(self, row:int, col:int) -> Any:
        """ 표시 데이터 반환 """
        if self.is_일자_column(col):
            date_str = self._data[row][self.일자_attr_name]
            if date_str in self._3days_reverse:
                return f"{Utils.format_date_str_with_weekday(date_str)}\n({self._3days_reverse[date_str]})"
            else:
                return Utils.format_date_str_with_weekday(date_str)
        else:
            return super()._role_display(row, col)


    
    def _role_background(self, row:int, col:int) -> Optional[QColor]:
        if hasattr(self, '_3days_reverse') and self._3days_reverse:
            match self._3days_reverse[self._data[row][self.일자_attr_name]]:
                case '오늘'|'금일':
                    return QColor(255, 255, 150)  # 연한 노란색
                case '내일'|'익일':
                    return QColor(200, 255, 200)  # 연한 연두색/녹색
                #### 어제는 no_editable로, Base_Delegate에서 처리함
                case _:
                    return QColor(255, 255, 255)  # 흰색 
                
        return None
                
    
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """
        if self._editable_3days:
            일자_data = self._data[index.row()][self.일자_attr_name]
            
            if 일자_data in self._editable_3days:
                return self._editable_3days[일자_data] and super()._is_editable(index)
            else:
                return False
        return False

    def setData_by_edit_mode(self, index:QModelIndex, value, role:Qt.ItemDataRole=Qt.ItemDataRole.EditRole):
        """ override: cell 모드이지만, 행단위 저장"""
        row, col = index.row(), index.column()
        db_attr_name = self.get_field_name_by_index(index)
        match self.lazy_attr_values['edit_mode'].lower():
            case 'row':
                if INFO.IS_DEV:
                    print(f" 'row mode' : setData_by_edit_mode : {row}, {col}, {value}, {db_attr_name}")
                self.update_cell_data(index, value)
                self._mark_row_as_modified(row)
                return True
            case 'cell':
                sendData = self._data[row]
                sendData.update({db_attr_name: value})
                _isok, _json = APP.API.Send(
                            url= self.url, 
                            dataObj= self._data[row], 
                            sendData=  sendData
                            )
                if _isok:
                    self.update_row_data(row, _json)
                    self._mark_cell_as_modified(row, col)
                    return True
                else:
                    return False
            case 'none'|'no_edit':
                return False

            case _:
                raise ValueError(f"Invalid edit mode: {self.lazy_attr_values['edit_mode']}")


    def exist_deleted_일자(self, deleted_일자:str) -> bool:
        for row in self._data:
            if row['일자'] == deleted_일자:
                return True
        return False
    
class Base_TableDelegate_일일업무_입력(Base_Delegate):
    pass