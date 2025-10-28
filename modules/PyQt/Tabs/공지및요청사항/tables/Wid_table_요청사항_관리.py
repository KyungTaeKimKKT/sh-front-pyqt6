from modules.common_import_v2 import *


class TableView_요청사항_관리(Base_Table_View):
    pass    

class TableModel_요청사항_관리(Base_Table_Model):

    FILES_COLUMN_NO :int|None = None
    Field_Name_for_files :str|None = 'files'

    def _role_display(self, row:int, col:int) -> Any:
        attr_name = self.get_field_name_by_column_no(col)
        value = self._data[row].get(attr_name, '')
        match attr_name:
            case '등록자':
                return INFO._get_username(value)
            case '등록일':
                return Utils.format_date_str_with_weekday( value, with_year=True )
            case '처리일자':
                if value:
                    return Utils.format_date_str_with_weekday( value, with_year=True )
                else:
                    return ''
            case _:
                return super()._role_display(row, col)

   
    def _role_background(self, row:int, col:int) -> QColor:
        is_완료 = self._data[row].get('is_완료', False)
        if  not is_완료:
            return QColor(255, 255, 200)                
    
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """

        #### 권한 모드에 따라 편집 가능 여부 반환
        if not hasattr(self, '권한_mode'):
            return False
        
        if self.권한_mode == '관리자':
            return super()._is_editable(index)
        elif self.권한_mode == '사용자':
            is_완료 = self._original_data[index.row()].get('is_완료', False)
            is_owner = self._original_data[index.row()].get('등록자', -1) == INFO.USERID
            is_editable = super()._is_editable(index)
            return not is_완료 and is_owner and is_editable
        return False
    
    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            여기서는 bulk 로 multiple 파일 첨부 처리함.
        """
        if self._modified_rows:
            for row in list(self._modified_rows):
                # sendData, sendFiles = self.get_sendData_and_sendFiles(self.get_row_data(row), ['help_page'])
                sendData, sendFiles = self.get_sendData_and_multiple_sendFiles(self._data[row], file_field_name='files')
                _isok, _json = 	APP.API.Send_bulk(url= self.url, added_url='bulk', 
                                                dataObj=  self._data[row],
                                                sendData=sendData,
                                                sendFiles=sendFiles
                                                )
                if _isok:
                    self.update_row_data(row, _json)
                    Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
                    self.clear_modified_rows([row])
                else:
                    Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
                    return False
            return True
        else:
            return False


class TableDelegate_요청사항_관리(Base_Delegate):
    def custom_editor_handler(self, db_attr_name:str, event: QEvent, model: TableModel_요청사항_관리, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        match db_attr_name:
            case '요청구분':
                url = f"{self.url}/get_요청구분_list/".replace('//', '/')
                is_ok, _json = APP.API.getlist (url )   ### list 형태로 받음
                if is_ok:
                    _list = _json
                    print(f"list: {_list}")
                else:
                    Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패 <br> 요청구분 선택 불가<br> 관리자에게 문의하세요.")
                    return False
                is_cached = False
                if (editor := self.get_cached_editor(db_attr_name)):
                    #### 캐시된 인스턴스 사용 ==> instance 마다 다르니까 set_value등은 확인
                    editor.set_value(_list)
                    is_cached = True
                else:
                    editor_class = self.get_custom_editor( db_attr_name )
                    if not isinstance(editor_class, Dialog_list_edit):
                        return False
                    validator = QRegularExpressionValidator(QRegularExpression(r"^[가-힣a-zA-Z\s]{1,20}$"))
                    editor = editor_class(option.widget,
                                        _list = _list , 
                                        is_sorting=False, 
                                        validator=validator, 
                                        config_line_edit={'placeholder_text': "최대 20자 이내로 간략히  입력"}
                                        )                                    
                    self.set_cached_editor(db_attr_name, editor)
                if editor.exec():
                    model.setData(index, editor.get_value(), Qt.ItemDataRole.EditRole)
                    return True
                else:
                    return False
            case _:
                logger.error(f"custom_editor_handler: {db_attr_name} 에디터 클래스가 없읍니다.")
                return False

       

class Wid_table_요청사항_관리( Wid_table_Base_V2):
    
    def setup_table(self):
        self.view = TableView_요청사항_관리(self)
        #✅   kwargs 넘기는 경우 : 초기화 + on_all_lazy_attrs_ready 에서 2번이며
        #✅   모두 setattr함으로, 가능한 속성으로 확인할 것
        self.model = TableModel_요청사항_관리(self.view, **self.kwargs)
        self.delegate = TableDelegate_요청사항_관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_new_row(self):
        self.model.on_new_row_by_template()

        self.reset_selected_row()

    def on_delete_row(self):
        self.model.on_delete_row( rowNo=self.selected_rowNo)
        self.reset_selected_row()


    def on_file_upload(self):
        file_paths = Utils._getOpenFileNames_multiple(self )
        if file_paths:
            print(f"file_paths: {file_paths}")
            self.selected_dataObj['files'] = file_paths
            self.model.update_row_data( rowNo=self.selected_rowNo, value=self.selected_dataObj)
        self.reset_selected_row()



    def on_file_download(self):
        """list 로 multiple 파일 다운로드"""
        files:list[dict] = self.selected_dataObj.get('files', [])
        if files:
            Utils.file_download_multiple(urls= [f['file'] for f in files])
        self.reset_selected_row()

    def on_file_view(self):
        files:list[dict] = self.selected_dataObj.get('files', [])
        if files:
            Utils.file_view(urls= [f['file'] for f in files])
        self.reset_selected_row()

