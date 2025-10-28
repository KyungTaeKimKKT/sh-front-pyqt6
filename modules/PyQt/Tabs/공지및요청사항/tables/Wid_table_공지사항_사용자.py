from modules.common_import_v2 import *

from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지내용_편집 import Dialog_공지내용_편집
from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지사항_popup import Dialog_공지사항_Popup
from modules.PyQt.Tabs.공지및요청사항.tables.Wid_table_공지사항_관리 import TableView_공지사항_관리 , TableModel_공지사항_관리, TableDelegate_공지사항_관리, Wid_table_공지사항_관리

class TableView_공지사항_사용자(TableView_공지사항_관리):
    pass

class TableModel_공지사항_사용자(TableModel_공지사항_관리):
   
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """
        id = self._original_data[index.row()].get('id', -1)
        is_신규 = id == -1
        return  is_신규 and super()._is_editable(index)
  
      

class TableDelegate_공지사항_사용자(TableDelegate_공지사항_관리):
    pass

      

class Wid_table_공지사항_사용자( Wid_table_공지사항_관리 ):
    
    def setup_table(self):
        self.view = TableView_공지사항_사용자(self) 
        self.model = TableModel_공지사항_사용자(self.view)
        self.delegate = TableDelegate_공지사항_사용자(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)
