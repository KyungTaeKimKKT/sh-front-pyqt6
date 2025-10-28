from modules.common_import_v2 import *



class Base_TableView_일일업무_조회(Base_Table_View):
    pass
    


class Base_TableModel_일일업무_조회(Base_Table_Model):
    일자_COLUMN_NO = None
    일자_attr_name = '일자'
    
    def _role_display(self, row:int, col:int) -> Any:
        if '일자' == self.get_field_name_by_column_no(col):
            date_str = self._data[row][self.일자_attr_name]
            return f"{Utils.format_date_str_with_weekday(date_str, with_year=True )}"
        return super()._role_display(row, col)



class Base_TableDelegate_일일업무_조회(Base_Delegate):
    pass