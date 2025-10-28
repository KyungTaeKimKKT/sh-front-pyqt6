from modules.common_import_v2 import *

class TableView_App설정_errorlog(Base_Table_View):
    pass
        
class TableModel_App설정_errorlog(Base_Table_Model):

    def _role_display(self, row:int, col:int) -> str:
        attr_name = self.get_attr_name_by_column_no(col)
        if 'user_fk' in attr_name:
            user_id = self._data[row][attr_name]
            return  INFO.USER_MAP_ID_TO_USER[user_id]['user_성명']
        return super()._role_display(row, col)




class TableDelegate_App설정_errorlog(Base_Delegate):
    pass

        

class Wid_table_App설정_errorlog( Wid_table_Base_V2  ):

    def setup_table(self):
        self.model = TableModel_App설정_errorlog(self)
        self.view = TableView_App설정_errorlog(self)
        self.delegate = TableDelegate_App설정_errorlog(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)
        self.view.setWordWrap(True)

    
    def on_file_view(self):
        if INFO.IS_DEV:
            urls= [self.selected_dataObj['file'] ]
            print(urls)
        Utils.file_view(urls= [self.selected_dataObj['file'] ])
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_file_download(self):
        if INFO.IS_DEV:
            urls= [self.selected_dataObj['file'] ]
            print(urls)
        Utils.file_download_multiple(urls= [self.selected_dataObj['file'] ])
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):
        if not (hasattr(self, 'selected_dataObj') or self.selected_dataObj):
            return
        self.model.on_delete_row(rowDict=self.selected_dataObj)
        self.selected_dataObj = None
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()
        # self.view.resizeRowsToContents()

