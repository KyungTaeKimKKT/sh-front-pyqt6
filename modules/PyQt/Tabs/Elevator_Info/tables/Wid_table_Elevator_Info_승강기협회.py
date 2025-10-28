from modules.common_import_v2 import *

class TableView_승강기협회(Base_Table_View):
	pass


class TableModel_승강기협회(Base_Table_Model):
    pass


class TableDelegate_승강기협회(Base_Delegate):
	pass
      

class Wid_table_승강기협회( Wid_table_Base_V2 ):
    
    def setup_table(self):
        self.view = TableView_승강기협회(self)
        self.model = TableModel_승강기협회(self.view)
        self.delegate = TableDelegate_승강기협회(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_map_view(self):
        Utils.map_view( address=self.selected_dataObj['건물주소_찾기용'], parent=self)
        self.reset_selected_row()

