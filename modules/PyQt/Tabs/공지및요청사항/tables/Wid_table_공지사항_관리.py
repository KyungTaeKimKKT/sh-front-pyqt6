from modules.common_import_v2 import *

from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지내용_편집 import Dialog_공지내용_편집
from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지사항_popup import Dialog_공지사항_Popup
from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지대상_편집 import Dialog_공지대상_편집

class TableView_공지사항_관리(Base_Table_View):
    pass

class TableModel_공지사항_관리(Base_Table_Model):

    POPUP_COLUMN_NO :int|None = None
    Field_Name_for_Popup :str|None = 'is_Popup'
    map_popup_to_color = {
        True : QColor(255, 255, 150),   ### 연한 노란색
        False : QColor(255, 255, 255),  ### 흰색
    }

    공지내용_COLUMN_NO :int|None = None
    add_row_dict = {
        'remaining_keys': ['공지내용'],
        'remaining_add_dict': {},
        'update_dict': {
            'id': -1,
            '제목': '공지내용을 입력하세요',
            '시작일' : datetime.now().strftime('%Y-%m-%d'),
            '종료일' : datetime.now().strftime('%Y-%m-%d'),
            # '공지내용' : '',
            'is_Popup' : False,
            'popup_시작일': datetime.now().strftime('%Y-%m-%d'),
            'popup_종료일': datetime.now().strftime('%Y-%m-%d'),
        },
    }


    def is_popup_visible(self, rowNo:int) -> bool:
        if self._data:
            return self._data[rowNo][self.Field_Name_for_Popup]
        return False        
    
    
    def request_add_gongi(self, rowNo:int):
        """ 여기서는 add_row 시 바로 db records 생성함. """
        super().request_add_row(
            rowNo=rowNo, 
            dlg_question=lambda : Utils.generate_QMsg_question(None, title="공지사항 추가", text="공지사항을 추가하시겠습니까?"),
            dlg_info=lambda : Utils.generate_QMsg_Information(None, title="공지사항 추가", text="공지사항 추가 성공", autoClose=1000),
            dlg_critical=lambda : Utils.generate_QMsg_critical(None, title="공지사항 추가", text="공지사항 추가 실패"),
        )
            

    def on_delete_gongi(self, rowNo:int):
        super().request_delete_row(
            rowNo=rowNo,
            dlg_question=lambda : Utils.generate_QMsg_question(None, title="공지사항  삭제", text="공지사항을 삭제하시겠습니까?"),
            dlg_info=lambda : Utils.generate_QMsg_Information(None, title="공지사항 삭제", text="공지사항 삭제 성공", autoClose=1000),
            dlg_critical=lambda : Utils.generate_QMsg_critical(None, title="공지사항 삭제", text="공지사항 삭제 실패"),
        )
       

    def on_gongi_edit(self, rowNo:int):
        dlg_gongi = Dialog_공지내용_편집 (self.parent(), obj=self._data[rowNo], url=self.url, is_api_send=False)
        if dlg_gongi.exec():
            # self.api_datas[rowNo] = dlg_gongi.get_result()
            self.update_row_data(rowNo, dlg_gongi.get_result())
            # print(f"self.api_datas[rowNo]: {self.api_datas[rowNo]}")
            # # self._data[rowNo][self.공지내용_COLUMN_NO] = dlg_gongi.get_result().get('공지내용', '')
            # self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.ItemDataRole.DisplayRole|Qt.ItemDataRole.BackgroundRole|Qt.ItemDataRole.EditRole])




    def _role_display(self, row:int, col:int) -> Any:
        attrName = self.get_field_name_by_column_no(col)
        if attrName in ['시작일', '종료일', 'popup_시작일', 'popup_종료일']:
            date_str = self._data[row][attrName] if attrName in self._data[row] else datetime.now().strftime('%Y-%m-%d')
            return Utils.format_date_str_with_weekday(date_str=date_str, with_year=True, with_weekday=True)
        elif attrName == '공지내용':
            value = self._data[row][attrName]
            if value:
                return value[0:40] + '...' if len(value) > 40 else value
            else:
                return '공지내용이 없습니다.'
        return super()._role_display(row, col)
    
    def _role_decoration(self, row: int, col: int) -> QPixmap:
        attrName = self.get_field_name_by_column_no(col)
        if attrName == '공지내용':  
            if self._role_display(row, col) == '공지내용이 없습니다.':
                return None
            pixmap = resources.get_pixmap('icon:gongi_html')
            if pixmap:
                return pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return super()._role_decoration(row, col)

    def _role_tooltip(self, row:int, col:int) -> str:
        attrName = self.get_field_name_by_column_no(col)
        if attrName == 'reading_count':
            return f"is_active = True 기준으로 총 읽은 사람 수 입니다."
        return super()._role_tooltip(row, col)
    
    def _role_background(self, row:int, col:int) -> QColor:
        return self.map_popup_to_color[self.is_popup_visible(row)]

   
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """
        return super()._is_editable(index)
  

    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            여기서는 bulk 안함.
        """
        super().on_api_send_By_Row()
       

class TableDelegate_공지사항_관리(Base_Delegate):
    pass

      

class Wid_table_공지사항_관리( Wid_table_Base_V2 ):
    
    def setup_table(self):
        self.view = TableView_공지사항_관리(self) 
        self.model = TableModel_공지사항_관리(self.view)
        self.delegate = TableDelegate_공지사항_관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_new_row(self):
        self.model.on_new_row_by_template()

        self.reset_selected_row()

    def on_delete_row(self):
        self.model.on_delete_gongi( rowNo=self.selected_rowNo)
        self.reset_selected_row()

    def on_WS_trigger(self):
        _text = f"""
            ⚠️ 공지사항을 즉시 배포하겠읍니까?<br><br>
            이 작업은 <b>모든 접속된 사용자에게 즉시</b> 배포합니다.<br>
            pop-up 형태로 즉시 발생되며 읽음 확인이 되어야만 종료됩니다.<br>
            계속하시겠습니까?
            """
        if Utils.QMsg_question( self, title='공지사항 즉시 배포', text=_text):
            action_url = 'request_ws_redis_publish'
            url = f"{self.url}/{self.selected_dataObj['id']}/{action_url}".replace('//', '/')
            _isok, _json = APP.API.getlist( url=  url )
            if _isok:
                Utils.QMsg_Info( self, title='공지사항 즉시 배포', text=f"공지사항 즉시 배포 성공<br>{json.dumps(_json, indent=4, ensure_ascii=False)}<br>" , autoClose=1000)
            else:
                Utils.QMsg_Critical( self, title='공지사항 즉시 배포', text=f'공지사항 즉시 배포 실패<br>{json.dumps(_json, indent=4, ensure_ascii=False)}<br>')

    def on_gongi_edit(self):
        self.model.on_gongi_edit( rowNo=self.selected_rowNo)
        self.reset_selected_row()

    def on_gongi_popup(self):
        try:            
            dlg_gongi = Dialog_공지사항_Popup(self, obj=self.selected_dataObj, view_type='preview')
            dlg_gongi.exec()
        except Exception as e:
            logger.error(f"on_gongi_popup: {e}")
            traceback.print_exc()
        self.reset_selected_row()

    def on_view_reading_users(self):
        ### 7-17 수정 : view_type 추가
        dlg = Dlg_Users_Select_Only_Table(self, 
                                          pre_selected_ids=[{'user': user} for user in self.selected_dataObj.get('reading_users', [])], 
                                          view_type='preview')
        dlg.exec()


    def on_gongi_target_edit(self):
        dlg = Dialog_공지대상_편집(self, 
                             all_data=self.get_app권한_all_data(), 
                             obj=self.selected_dataObj
                             )
        if dlg.exec():  
            checked_status, ids = dlg.get_selected_ids()
            print ( 'checked_status:', checked_status )
            print ( 'ids:', ids )
            popup_대상 = ''
            match checked_status:
                case 'all':
                    popup_대상 = checked_status
                case 'none':
                    popup_대상 = checked_status
                case 'partial':
                    popup_대상 = ','.join(map(str, ids))
                case _:
                    print ( "알수 없는 형태 : ", checked_status, 'ids:', ids )
                    popup_대상 = 'unknown'
            self.model.setData ( self.model.index(self.selected_rowNo, self.model.get_column_no_from_attr_name('popup_대상')), 
                                popup_대상 )
            self.reset_selected_row()


    def get_app권한_all_data(self):
        return [ obj for obj in INFO.APP_권한_TOTAL 
                if all( [ obj.get('is_Active'), not obj.get('is_dev') ] ) ]
