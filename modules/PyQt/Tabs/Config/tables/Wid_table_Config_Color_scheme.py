from modules.common_import_v2 import *

DECORATION_SIZE = (48, 48)

from modules.PyQt.compoent_v2.table_v3.Base_Table_Model import Base_Table_Model as Base_Table_Model_V3
from modules.PyQt.compoent_v2.table_v3.Base_Table_View import Base_Table_View as Base_Table_View_V3
from modules.PyQt.compoent_v2.table_v3.Base_Delegate import Base_Delegate as Base_Delegate_V3

def create_pixmap(data:dict, size:tuple[int, int]=DECORATION_SIZE, _text:str='Aa') -> QPixmap:
    bg = data.get('bg', None)   ### str:'#E8F5E9'
    font_color = data.get('font', None) ### str:'#4CAF50'
    if not all([bg, font_color]):
        return None
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(QColor(bg))

    painter = QPainter(pixmap)
    painter.setPen(QColor(font_color))
    painter.setFont(QFont("Arial", 12))  # 기본 폰트 + 크기
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, _text)
    painter.end()

    return pixmap

class TableView_Color_scheme(Base_Table_View_V3):
    pass

class TableModel_Color_scheme(Base_Table_Model_V3):

    def on_api_send_By_Row(self):
        super().on_api_send_By_Row_with_file(file_field_name='file')

    def _role_decoration(self, row: int, col: int) -> QPixmap:
        attrName = self.get_field_name_by_column_no(col)
        match attrName:
            case 'description':
                pixmap = create_pixmap( self._data[row] )
                if pixmap:
                    return pixmap.scaled(DECORATION_SIZE[0], DECORATION_SIZE[1], 
                                         Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return pixmap

        return super()._role_decoration(row, col)


class TableDelegate_Color_scheme(Base_Delegate_V3):
    
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


from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_설정 import Dlg_Excel_미리보기
class Dlg_Color_scheme_bulk_preview(Dlg_Excel_미리보기):
        
    def get_summary_text(self) -> str:
        return f"""
            <p>총 건수 : {len(self.df)}</p>
        """
    
    def on_save(self):
        self.send_data['excel_datas'] = self.df.to_dict(orient='records')
        self.accept()


class Dlg_Color_scheme_preview(QDialog):
    def __init__(self, parent=None, data:dict=None, **kwargs ):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Color Scheme Preview")
        self.setMinimumSize(800, 600)
        if data:
            self.setup_ui()
        
    def _create_label(self, attr:str, alignment:Qt.AlignmentFlag=Qt.AlignmentFlag.AlignCenter) -> QLabel:
        lb = QLabel(self)
        _text = f"{attr.upper()} : {self.data.get(attr, '')}"
        lb.setText(_text)
        lb.setAlignment(alignment)
        font_color = self.data.get('font', '#4CAF50')
        bg_color = self.data.get('bg', '#E8F5E9')
        lb.setStyleSheet(f"font-size: 12pt;font-weight:bold;color: {font_color};background-color: {bg_color};border: 1px solid #888;")
        lb.setWordWrap(True)
        return lb

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        for attr in ['name', 'bg', 'font', 'description']:
            self.main_layout.addWidget(self._create_label(attr))
            self.main_layout.addSpacing(10)

        self.main_layout.addStretch()

    def set_data(self, data:dict):
        self.data = data
        Utils.deleteLayout(self.main_layout)
        self.setup_ui()


from modules.PyQt.compoent_v2.table_v2.Wid_table_Base_for_stacked_V2 import Wid_table_Base_V3

class Wid_table_Color_scheme( Wid_table_Base_V3 ):

    def setup_table(self):
        self.view = TableView_Color_scheme(self) 
        self.model = TableModel_Color_scheme(self.view)
        self.delegate = TableDelegate_Color_scheme(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_new_row(self):        
        self.model.on_new_row_by_template(added_url='template/')
        self.reset_selected_row()

    def on_delete_row(self):        
        self.model.request_delete_row( rowObj=self.selected_rows[0])
        self.reset_selected_row()

    def on_file_bulk(self):
        editor = FileOpenSingle(self)
        file_path = editor.open_file_dialog()

        if all ( [file_path, os.path.exists(file_path)] ):
            dlg = Dlg_Color_scheme_bulk_preview(self, 
                                path=file_path, 
                                title="Color Scheme Spreadsheet Bulk 미리보기",
                                required_cols= ['name', 'bg','font', 'description','is_active','source'],
                                data_type_dict={'name': str, 'bg': str, 'font': str, 'description': str, 'is_active': bool, 'source': str},
                                unique_same_cols=[],
                                unique_not_duplicated=['name'],
                                )
            if dlg.exec():
                send_data, send_file = dlg.get_send_data()
                send_data['excel_datas'] = json.dumps(send_data['excel_datas'], ensure_ascii=False)
                # url = f"{self.url}/bulk_create/".replace('//','/')
                _isok, _json = APP.API.Send_bulk( url=self.url, added_url='bulk_create/', detail=False, dataObj={'id':-1}, 
                                                 sendData=send_data, sendFiles=send_file )
                if _isok:
                    if ( refresh_func := getattr(self._lazy_source_widget, 'simulate_search_pb_click', None) ) and callable(refresh_func):
                        refresh_func()
                    else:
                        logger.error(f"refresh_func is not found in {self._lazy_source_widget}")
                else:
                    Utils.generate_QMsg_critical(self, title="Color Scheme 추가 실패", text=f"Color Scheme 추가 실패; <br>{_json}")
        else:
            Utils.generate_QMsg_critical(self, title="파일 없음", text=f"{file_path} 파일이 없습니다.")


    def on_color_scheme_preview(self):
        self.dlg_color_scheme_preview = getattr(self, 'dlg_color_scheme_preview', None )
        if not self.dlg_color_scheme_preview:
            self.dlg_color_scheme_preview = Dlg_Color_scheme_preview(self, data=self.selected_dataObj)
        else:
            self.dlg_color_scheme_preview.set_data(self.selected_dataObj)
        self.dlg_color_scheme_preview.show()
