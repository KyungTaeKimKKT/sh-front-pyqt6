from modules.common_import_v2 import *
from modules.PyQt.Tabs.일일업무.tables.Base_table_일일업무_입력 import (
    Base_TableView_일일업무_입력,
    Base_TableModel_일일업무_입력,
    Base_TableDelegate_일일업무_입력
)


class  TableView_일일업무_조직(Base_TableView_일일업무_입력):
    pass

class TableModel_일일업무_조직(Base_TableModel_일일업무_입력):
    pass

class TableDelegate_일일업무_조직(Base_TableDelegate_일일업무_입력):
    pass


class Wid_table_일일업무_조직(Wid_table_Base_V2):

    
    def setup_table(self):
        self.view = TableView_일일업무_조직(self)
        self.model = TableModel_일일업무_조직(self.view)
        self.delegate = TableDelegate_일일업무_조직(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

 
    def on_new_copy_row(self):
        copyed = copy.deepcopy(self.model._data[self.selected_rowNo])
        copyed['id'] = -1
        copyed['활동현황'] = ''
        copyed['세부내용'] = ''
        copyed['진척율'] = ''
        copyed['유관부서']  =''
        copyed['비고'] = ''
        self.model._data.insert(self.selected_rowNo, copyed)
        self.model.layoutChanged.emit()

        self.reset_selected_row()


    def on_delete_row(self):
        rowNo =  copy.deepcopy(self.selected_rowNo)
        deleted_일자 = self.selected_dataObj['일자']
        super().on_delete_row()

        #### ✅ 삭제 후, 만약 해당 일자에 data 가 없으면
        #### 검색버튼을 click하여, refresh 하면서 server 에서 생성시킴 
        if not self.model.exist_deleted_일자(deleted_일자):
            self._lazy_source_widget.simulate_search_pb_click()
        