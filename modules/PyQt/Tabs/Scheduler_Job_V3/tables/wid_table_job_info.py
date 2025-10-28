from modules.common_import_v2 import *

from modules.PyQt.compoent_v2.list_select.list_select import Base_List_Select

class Dialog_WS_선택( Base_List_Select ):
	""" kwargs:
		title: str = '테이블 선택'
		search_placeholder: str = '테이블 이름 검색...'
	"""
	def __init__(self, parent:QWidget, data:list[dict]=[], url:str=None, list_name_key:str='name', **kwargs):
		super().__init__(parent, data, url, list_name_key, **kwargs)




class View_job_info(Base_Table_View):
    pass

class Model_job_info(Base_Table_Model):
    pass

class Delegate_job_info(Base_Delegate):
    pass

class Wid_table_job_info( Wid_table_Base_V2):

    def setup_table(self):
        self.view = View_job_info(self)
        self.model = Model_job_info(self.view)
        self.delegate = Delegate_job_info(self.view)

        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_new_row(self):
        self.model.on_new_row_by_template()
        if self.selected_rows:
            self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):
        self.model.on_delete_row(rowDict=self.selected_rows[0])
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()


    def on_select_ws(self):
        self.selected_dataObj
        url = f"{INFO.get_API_URL( app_info={'div': 'Config','name':'WS_URLS관리'})}?page_size=0"
        print ( url )
        dlg = Dialog_WS_선택(self, url =url , is_auto_fetch=True)
        if dlg.exec():
            item = dlg.get_selected_item()
            print ( item )
            self.model.setData( index= self.model.index( self.selected_rowNo, self.model.get_column_no_from_attr_name('ws_url_db')),
                               value=item['id'],
                               role=Qt.ItemDataRole.EditRole
                               )
            self.model.setData( index= self.model.index( self.selected_rowNo, self.model.get_column_no_from_attr_name('ws_url_name')),
                               value = f"{item['group']}/{item['channel']}",
                               role=Qt.ItemDataRole.EditRole
                               )
            # self.selected_dataObj['ws_url_db'] = item['id']
            print ( self.selected_dataObj )


