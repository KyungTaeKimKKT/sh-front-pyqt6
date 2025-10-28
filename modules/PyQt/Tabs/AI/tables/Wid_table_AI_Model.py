from modules.common_import_v3 import *

class TableView_AI_Model(Base_Table_View):
    pass


class TableModel_AI_Model(Base_Table_Model):
    pass

class TableDelegate_AI_Model(Base_Delegate):
    pass

        

class Wid_table_AI_Model( Wid_table_Base_V2 ):

    def setup_table(self):        
        self.view = TableView_AI_Model(self)
        self.model = TableModel_AI_Model(self.view)
        self.delegate = TableDelegate_AI_Model(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_disactive(self):
        _isok, _json = APP.API.Send (self.url, {'id':self.selected_dataObj['id'] }, {'is_active':False})
        if _isok:
            self.model.update_row_data(self.selected_rowNo, _json)
            Utils.generate_QMsg_Information(self, title='AI 모델 비활성화', text='AI 모델 비활성화 완료', autoClose= 1000)
        else:
            Utils.generate_QMsg_critical(self, title='AI 모델 비활성화 실패', text='AI 모델 비활성화 실패' )
