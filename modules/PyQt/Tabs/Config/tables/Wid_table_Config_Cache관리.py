from modules.common_import_v2 import *

class TableView_Config_Cache관리(Base_Table_View):
    pass

class TableModel_Config_Cache관리(Base_Table_Model):
    def _role_display( self, row:int, col:int) -> str:
        """표시 데이터 반환
        기본적으로 self._data 가 api_datas 인 list[dict] 인 경우 적용   
        ✅  여기서는, 가장 긴 keys를 기준으로 header를 표시하였으므로, 
        없는 경우에 error 가 발생하니, try except 로 처리함.

        """
        if not hasattr(self, '_data') or not self._data:
            return ''
        display_header_name = self._headers[col]
        attribute_name = self.table_config["_mapping_display_to_attr"][display_header_name] if self.table_config else display_header_name
        try:
            if attribute_name not in self._data[row]:
                return '-'
            elif self._data[row][attribute_name] is None:
                return ''
            else:
                return self._data[row][attribute_name]
            
        except Exception as e:
            logger.error(f"TableModel_Config_Cache관리._role_display 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return 'e'
        

class TableDelegate_Config_Cache관리(Base_Delegate):
    pass

        

class Wid_table_Config_Cache관리( Wid_table_Base_V2 ):

    def setup_table(self):
        self.view = TableView_Config_Cache관리(self)
        self.model = TableModel_Config_Cache관리(self.view)
        self.delegate = TableDelegate_Config_Cache관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

