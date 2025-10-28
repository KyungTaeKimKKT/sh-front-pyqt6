from modules.common_import_v2 import *

class TableView_Config_WS_URLS관리(Base_Table_View):
    pass

class TableModel_Config_WS_URLS관리(Base_Table_Model):

    def on_api_send_By_Row(self):
        super().on_api_send_By_Row()

    def _role_decoration(self, row: int, col: int) -> QPixmap:
        attrName = self.get_field_name_by_column_no(col)
        if attrName == 'file':
            name = self._data[row].get('name', None)
            if name:
                pixmap = resources.get_pixmap(name)
                if pixmap:
                    return pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return super()._role_decoration(row, col)


class TableDelegate_Config_WS_URLS관리(Base_Delegate):
    
    def custom_editor_handler(self, db_attr_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        match db_attr_name:
            case 'file':
                editor = editor_class(option.widget,                                         
                                    on_complete_channelName=f"{self.table_name}:custom_editor_complete",
                                    index=index,
                                    )
                if isinstance( editor, FileOpenSingle ):
                    editor.open_file_dialog()
                    return True
        
        return False
    

        

class Wid_table_Config_WS_URLS관리( Wid_table_Base_V2  ):

    def setup_table(self):
        self.view = TableView_Config_WS_URLS관리(self) 
        self.model = TableModel_Config_WS_URLS관리(self.view)
        self.delegate = TableDelegate_Config_WS_URLS관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_new_row(self):        
        self.model.on_new_row_by_template(added_url='template/')
        self.reset_selected_row()

    def on_delete_row(self):        
        self.model.request_delete_row( rowObj=self.selected_rows[0])
        self.reset_selected_row()

    def on_fileview(self):        
        try:
            dlg = FileViewer_Dialog(self)
            dlg.add_file( self.selected_dataObj['file'])
            dlg.exec()
        except Exception as e:
            logger.error(f"on_fileview 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            _text = f"on_fileview 오류: {e}<br> {trace}"
            Utils.generate_QMsg_critical(None, title='파일보기 오류', text=_text)
        self.reset_selected_row()

    def on_file_upload(self):
        wid = FileOpenSingle(self)
        wid.open_file_dialog()
        file_path = wid.get_file_path()
        if file_path:
            self.selected_dataObj['file'] = file_path
            self.model.update_row_data(self.selected_rowNo, self.selected_dataObj)
        self.reset_selected_row()

    def on_file_download(self):
        Utils.download_file_from_url(self.selected_dataObj['file'])
        self.reset_selected_row()

