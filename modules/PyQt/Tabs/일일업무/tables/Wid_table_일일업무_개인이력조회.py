from modules.common_import_v2 import *
from modules.PyQt.Tabs.일일업무.tables.Base_table_일일업무_조회 import (
    Base_TableView_일일업무_조회,
    Base_TableModel_일일업무_조회,
    Base_TableDelegate_일일업무_조회
)


class TableView_일일업무_개인이력조회(Base_TableView_일일업무_조회):
    pass
    


class TableModel_일일업무_개인이력조회(Base_TableModel_일일업무_조회):
    pass


class TableDelegate_일일업무_개인이력조회(Base_TableDelegate_일일업무_조회):
    pass
        

class Wid_table_일일업무_개인이력조회( Wid_table_Base_V2 ):

    def setup_table(self):
        self.view = TableView_일일업무_개인이력조회(self)
        self.model = TableModel_일일업무_개인이력조회(self.view)
        self.delegate = TableDelegate_일일업무_개인이력조회(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)
