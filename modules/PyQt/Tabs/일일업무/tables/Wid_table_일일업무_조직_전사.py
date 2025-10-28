from modules.common_import_v2 import *
from modules.PyQt.Tabs.일일업무.tables.Base_table_일일업무_입력 import (
    Base_TableView_일일업무_입력,
    Base_TableModel_일일업무_입력,
    Base_TableDelegate_일일업무_입력
)


class TableView_일일업무_조직_전사(Base_TableView_일일업무_입력):
    pass

class TableModel_일일업무_조직_전사(Base_TableModel_일일업무_입력):
    
    def _is_editable(self, index: QModelIndex) -> bool:
        return super()._is_editable(index)

class TableDelegate_일일업무_조직_전사(Base_TableDelegate_일일업무_입력):
    pass


        

class Wid_table_일일업무_조직_전사( Wid_table_Base_V2 ):

   
    def setup_table(self):
        self.view = TableView_일일업무_조직_전사(self)
        self.model = TableModel_일일업무_조직_전사(self.view)
        self.delegate = TableDelegate_일일업무_조직_전사(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

 