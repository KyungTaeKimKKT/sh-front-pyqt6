from modules.common_import_v2 import *

class TableView_App설정_App설정_개발자(Base_Table_View):
    pass


class TableModel_App설정_App설정_개발자(Base_Table_Model):

    @property
    def add_row_dict(self):
        return {
            'remaining_keys': [ ],
            'remaining_add_dict': {},
            'update_dict': {'id': -1},
        }

    def on_api_send_By_Row(self):
        """ 행 단위 저장 , 파일 첨부 처리함.
            Base_Table_Model 은 파일 첨부 하는 method 호출함
            여기서는 파일 첨부 처리함.
        """
        super().on_api_send_By_Row_with_file(file_field_name='help_page')

    def get_sendData_and_sendFiles(self, sendData:dict, file_headers:list[str]) -> tuple[dict, dict]:
        """ 행 단위 저장 시 파일 첨부 """
        sendData, sendFiles = super().get_sendData_and_sendFiles(sendData, file_headers)
        if sendData and 'lazy_attrs' in sendData and sendData['lazy_attrs']:
            sendData['lazy_attrs'] = json.dumps(sendData['lazy_attrs'], ensure_ascii=False)
        if sendData and 'App_Menus' in sendData and sendData['App_Menus']:
            sendData['App_Menus'] = json.dumps(sendData['App_Menus'], ensure_ascii=False)
        if sendData and 'Table_Menus' in sendData and sendData['Table_Menus']:
            sendData['Table_Menus'] = json.dumps(sendData['Table_Menus'], ensure_ascii=False)
        return sendData, sendFiles


    def on_user_select(self, rowNo:int, rowDict:dict):
        self.request_on_user_select( 
            rowNo=self._data.index(rowDict),
            rowDict=rowDict,
        )

    def request_on_user_select(self, rowNo:int, colNo:Optional[int]=None, rowDict:Optional[dict]=None):
        """ user select 시 호출되는 함수 """
        if rowDict is not None:
            data = rowDict['user_list']
        else:
            data = self._data[rowNo]['user_list']
        colNo = self.get_column_no_from_attr_name('user_list')
        if INFO.IS_DEV:
            logger.info(f"data: {data}")
        id = self._data[rowNo]['id']
        editor = UsersDialog_with_tree_table( self.parent(),
                             app_ID =  id,
                             pre_selected_ids = data,
                             api_url=API_URLS.APP권한_사용자_M2M_Bulk,
                             on_complete_channelName=None,
                             index = self.index(rowNo, colNo),
                             )
        if editor.exec():
            response_data = editor.get_response_data()
            Utils.generate_QMsg_Information(None, title="사용자 선택 완료", text="사용자 선택 완료", autoClose=1000)
            self.update_row_data(rowNo, response_data)
            if INFO.IS_DEV:
                logger.info(f"response_data: {response_data}") #### 현재 row data 전체를 받음.


    #### Menu Hander 에서 호출되는 함수
    def request_on_add_row(self, rowNo: int):
        logger.info(f"[Base] Row 추가 rowNo: {rowNo}")
        copyed_row = copy.deepcopy(self._data[rowNo])
        copyed_row['id'] = -1
        from datetime import datetime
        copyed_row['등록일'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        copyed_row['user_list'] = []
        copyed_row['user_pks'] = []
        copyed_row['app사용자수'] = 0

        self.beginInsertRows(QModelIndex(), rowNo, rowNo)
        # self.insertRow(rowNo)
        self._data.insert(rowNo, copyed_row)
        self.endInsertRows()
        logger.info(f"[Base] Row {rowNo+1} 추가 완료")


class TableDelegate_App설정_App설정_개발자(Base_Delegate):

    def custom_editor_handler(self, db_attr_name:str,  event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        match db_attr_name:
            case 'help_page':
                editor_class = self.get_custom_editor( db_attr_name )
                editor = editor_class( option.widget)
                if not isinstance( editor, FileOpenSingle ):
                    logger.error(f"custom_editor_handler: {db_attr_name} 에디터 클래스가 없읍니다.")
                    return False

                file_path = editor.open_file_dialog()
                model.setData(index, file_path, Qt.ItemDataRole.EditRole)
                return True

            case _:
                logger.error(f"custom_editor_handler: {db_attr_name} 에디터 클래스가 없읍니다.")
            
        return False

        

class Wid_table_App설정_App설정_개발자( Wid_table_Base_V2 ):

    def setup_table(self):        
        self.view = TableView_App설정_App설정_개발자(self)
        self.model = TableModel_App설정_App설정_개발자(self.view)
        self.delegate = TableDelegate_App설정_App설정_개발자(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_setup_lazy_attr(self):
        self.base_json_setup_menus('lazy_attrs')
    
    def on_setup_app_menus(self):
        self.base_json_setup_menus('App_Menus')

    def on_setup_table_menus(self):
        self.base_json_setup_menus('Table_Menus')


    def base_json_setup_menus(self, _menu_type:str ):
        from modules.PyQt.compoent_v2.json_editor import Dialog_JsonEditor
        _dict_data = self.selected_dataObj[_menu_type]
        form = Dialog_JsonEditor(None, self.url, _dict_data=_dict_data)
        if form.exec():			
            resultObj = form.get_value()
            index = self.model.get_index_from_row_col(self.selected_rowNo, self.model.get_column_no_from_attr_name(_menu_type))
            self.model.setData(index, resultObj, Qt.ItemDataRole.EditRole)
            # self.selected_dataObj[_menu_type] = resultObj
            # self.model.update_row_data( self.selected_rowNo, self.selected_dataObj)
            # print(f"resultObj : {resultObj}")

    def on_new_row(self):
        pass

    def on_copy_new_row(self):
        if not  Utils.is_valid_attr_name(self, 'selected_rowNo', int):
            return
        if not Utils.QMsg_question(None, title="복사 생성", text=f"선택한 row no는 {self.selected_rowNo} 입니다. 복사 생성 하시겠습니까?"):
            return
        self.model.on_copy_new_row_by_template(rowNo=self.selected_rowNo)
        self.reset_selected_row()

    def on_delete_row(self):
        if not (hasattr(self, 'selected_rows') or self.selected_rows):
            return
        self.model.on_delete_row(rowDict=self.selected_dataObj)
        self.reset_selected_row()

    def on_user_select(self):
        self.model.on_user_select(rowNo=self.selected_rowNo, rowDict=self.selected_rows[0])
        self.reset_selected_row()


    def on_clear_tableconfig(self):

        if not Utils.QMsg_question(self, title='테이블 초기화', text='테이블 초기화 하시겠습니까?') :
            return

        _is_ok = APP.API.delete( f"{self.url}{self.selected_dataObj['id']}/manage_table_config/")
        if _is_ok:
            Utils.generate_QMsg_Information(self, title='테이블 초기화', text='테이블 초기화 완료', autoClose= 1000)
        else:
            Utils.generate_QMsg_critical(self, title='테이블 초기화 실패', text='테이블 초기화 실패' )
    
        self.reset_selected_row()

    def on_create_tableconfig(self):
        if not Utils.QMsg_question(self, title='테이블 생성 및 update', text='테이블 생성 및 update 하시겠습니까?') :
            return
        _is_ok, _ = APP.API.getObj_byURL( f"{self.url}{self.selected_dataObj['id']}/manage_table_config/")
        if _is_ok:
            Utils.generate_QMsg_Information(self, title='테이블 생성 및 update', text='테이블 생성 및 update 완료', autoClose= 1000)
        else:
            Utils.generate_QMsg_critical(self, title='테이블 생성 및 update 실패', text='테이블 생성 및 update 실패' )
        self.reset_selected_row()
