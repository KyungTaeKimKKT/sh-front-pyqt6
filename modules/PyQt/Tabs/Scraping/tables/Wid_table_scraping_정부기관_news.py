from modules.common_import_v2 import *

from modules.PyQt.Tabs.Scraping.dialog.dlg_web_preview import WebPreviewDialog



class TableView_정부기관NEWS(Base_Table_View):
    pass



class TableModel_정부기관NEWS(Base_Table_Model):

    map_링크_유효성_bg = {
        True: QColor(200, 255, 200),   # 연한 연두 (유효한 링크)
        False: QColor(255, 220, 220),  # 연한 분홍 (무효한 링크)
    }

    def request_web_preview(self, rowNo:int, colNo:int):
        if not self.is_링크_column(colNo):
            return 
        if self.is_링크_valid( link_data := self._data[rowNo]['링크']):
            dialog = WebPreviewDialog(self.parent(), url=link_data)
            dialog.exec()
        else:
            Utils.generate_QMsg_critical(None, title="링크 유효성 검사 실패", text="링크 유효성 검사 실패")


    def _role_display(self, row:int, col:int) -> Any:
        if self.is_링크_column(col):
            return '링크' if self.is_링크_valid(self._data[row]['링크']) else ''
        
        return super()._role_display(row, col)
    
    def _role_background(self, row:int, col:int) -> Any:
        if self.is_링크_column(col) :
            return self.map_링크_유효성_bg[self.is_링크_valid(self._data[row]['링크'])]
            
        return super()._role_background(row, col)
    
    def _role_tooltip(self, row: int, col: int) -> Any:
        if self.is_링크_column(col):
            link = self._data[row].get('링크', '')
            if self.is_링크_valid(link):
                return f"""<b>유효한 링크입니다.</b><br>
                           {link}"""
            else:
                return "<b style='color:red;'>유효하지 않은 링크입니다.</b><br>http:// 또는 https:// 로 시작해야 합니다."
        return super()._role_tooltip(row, col)

    def is_링크_column(self, colNo:int) -> bool:
        return '링크' == self.get_attr_name_by_column_no(colNo)

    def is_링크_valid(self, link_data: str) -> bool:
        """링크 유효성 검사: 존재 여부 + http/https로 시작"""
        if not link_data:
            return False
        link_data = link_data.strip()
        return link_data.startswith('http://') or link_data.startswith('https://')

class TableDelegate_정부기관NEWS(Base_Delegate):
    pass



class Wid_table_정부기관NEWS( Wid_table_Base_V2 ):

    def setup_table(self):
        self.view = TableView_정부기관NEWS(self)
        self.model = TableModel_정부기관NEWS(self.view)
        self.delegate = TableDelegate_정부기관NEWS(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_web_preview(self):
        링크_data = self.model._data[self.selected_rowNo]['링크']
        if self.model.is_링크_valid(링크_data):
            dialog = WebPreviewDialog(self, url=링크_data)
            dialog.exec()
        else:
            Utils.generate_QMsg_critical(None, title="링크 유효성 검사 실패", text="링크 유효성 검사 실패")

    def on_copy_url(self):

        링크_data = self.model._data[self.selected_rowNo]['링크']
        if self.model.is_링크_valid(링크_data):
            clipboard = QApplication.clipboard()
            clipboard.setText(링크_data)
        else:
            Utils.generate_QMsg_critical(self, title="링크 복사 실패", text="링크가 유효하지 않습니다.")
        
        
