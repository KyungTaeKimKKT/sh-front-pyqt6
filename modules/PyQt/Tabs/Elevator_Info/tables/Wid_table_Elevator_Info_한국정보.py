from modules.common_import_v2 import *

class TableView_한국정보(Base_Table_View):
	pass


class TableModel_한국정보(Base_Table_Model):
    pass


class TableDelegate_한국정보(Base_Delegate):
	pass
      

class Wid_table_한국정보( Wid_table_Base_V2 ):
    
    def setup_table(self):
        self.view = TableView_한국정보(self)
        self.model = TableModel_한국정보(self.view)
        self.delegate = TableDelegate_한국정보(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_map_view(self):
        Utils.map_view( address=self.selected_dataObj['건물주소_찾기용'], parent=self)
        self.reset_selected_row()