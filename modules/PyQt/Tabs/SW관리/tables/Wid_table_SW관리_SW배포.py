from modules.common_import_v2 import *


class TableView_SW관리_SW배포(Base_Table_View):
    pass

class TableModel_SW관리_SW배포(Base_Table_Model):

    add_row_dict = {
        'remaining_keys': ['App이름', 'OS', '종류', '버젼'],
        'remaining_add_dict': {},
        'update_dict': {
            'id': -1,
            'is_즉시': False,
            'is_release': False,
        },
    }

	
    def request_on_add_row(self, rowNo:int, api_send:bool=True):
        copyed_row = self.copy_row(
            rowNo, 
            **self.add_row_dict,
        )
        #### 버젼만 증가
        try:
            copyed_row['버젼'] = str(float(copyed_row['버젼'])+0.01)
        except Exception as e:
            copyed_row['버젼'] = '0.0'

        qmsg_text = f"""SW 추가하시겠습니까?<br>
                    <br>
                    <b>App이름</b>: {copyed_row['App이름']}<br>
                    <b>OS</b>: {copyed_row['OS']}<br>
                    <b>종류</b>: {copyed_row['종류']}<br>
                    <b>버젼</b>: {copyed_row['버젼']} => 0.01씩 증가됩니다.<br>
                    <br>
                    <b>is_release</b>: 를 활성화해야지 배포됩니다.
        """
        super().request_on_add_row(
            rowNo=rowNo, 
            copyed_rowDict=copyed_row,
            dlg_question=lambda:Utils.generate_QMsg_question(None, title="SW 추가", text=qmsg_text),
            dlg_info=lambda:Utils.generate_QMsg_Information(None, title="SW 추가", text="SW 추가 성공", autoClose=1000),
            dlg_critical=lambda:Utils.generate_QMsg_critical(None, title="SW 추가", text="SW 추가 실패"),
            api_send=api_send,
            )



    def request_on_delete_row(self, rowNo:int):
        super().request_on_delete_row(rowNo,
                                      dlg_question=lambda:Utils.generate_QMsg_question(None, title="SW 삭제", text="SW 삭제하시겠습니까?"),
                                      dlg_info=lambda:Utils.generate_QMsg_Information(None, title="SW 삭제", text="SW 삭제 성공", autoClose=1000),
                                      dlg_critical=lambda:Utils.generate_QMsg_critical(None, title="SW 삭제", text="SW 삭제 실패"),
                                      )

    


    def _role_display(self, row:int, col:int) -> Any:
        return super()._role_display(row, col)


    def _role_background(self, row:int, col:int) -> QColor:
        return super()._role_background(row, col)
				
    
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """
        return super()._is_editable(index)


    def _is_menu_visible(self, rowNo:int) -> bool:
        """ override : 편집 불가능 row는 메뉴 생성 안함."""
        return True


    def on_api_send_By_Row(self):
        """ 행 단위 저장 , 파일 첨부 처리함.
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
        super().on_api_send_By_Row_with_file(file_field_name='file')
	
    
    def get_choice_list(self, index:QModelIndex) -> list:
        rowNo = index.row()
        colNo = index.column()
        field_name = self.get_attrName_from_display( display_name=self._headers[colNo])

        map_field_name_to_list = {
            'OS': self._data[rowNo]['OS_choices'],
            '종류': self._data[rowNo]['종류_choices'],            
        }
        if field_name in map_field_name_to_list :
            return map_field_name_to_list[field_name]
        else:
            return []



class TableDelegate_SW관리_SW배포(Base_Delegate):

    def setEditorData(self, editor:QWidget, index:QModelIndex):
        logger.debug(f"setEditorData: {editor}, {index}")
        model : TableModel_SW관리_SW배포 = index.model()
        rowNo, colNo = index.row(), index.column()

        if isinstance(editor, QComboBox):
            choice_list = model.get_choice_list(index)
            if choice_list:
                map_value_to_display = {item['value']: item['display'] for item in choice_list}
                editor.addItems( [item['display'] for item in choice_list] )
                value = model.data(index, Qt.ItemDataRole.EditRole)
                editor.setCurrentText(map_value_to_display.get(value, value))
                return 
            else:
                logger.error(f"choice_list is empty: {choice_list}")
                return 
        
        super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: TableModel_SW관리_SW배포, index: QModelIndex) -> None:
        rowNo, colNo = index.row(), index.column()

        if isinstance(editor, QComboBox):
            choice_list = model.get_choice_list(index)
            if choice_list:
                map_display_to_value = {item['display']: item['value'] for item in choice_list}                
                model.setData(index, map_display_to_value[editor.currentText()], Qt.ItemDataRole.EditRole)
                return 
            else:
                logger.error(f"choice_list is empty: {choice_list}")
                return 

        super().setModelData(editor, model, index)

    def custom_editor_handler(self, db_attr_name:str,  event: QEvent, model: TableModel_SW관리_SW배포, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        match db_attr_name:
            case 'file':
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


class Wid_table_SW관리_SW배포( Wid_table_Base_V2 ):

    def setup_table(self):
        self.view = TableView_SW관리_SW배포(self)
        self.model = TableModel_SW관리_SW배포(self.view)
        self.delegate = TableDelegate_SW관리_SW배포(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_file_upload(self):
        objectName = self.sender().objectName()
        if objectName:
            _info = json.loads(objectName)
            if 'db_attr_name' in _info:
                db_attr_name = _info['db_attr_name']
                colNo = self.model.get_column_no_from_attr_name(db_attr_name)
                index = self.model.get_index_from_row_col(rowNo=self.selected_rowNo, colNo=colNo)
                self.simulate_double_click(index=index)
                
        self.reset_selected_row()

    def on_file_download(self):
        objectName = self.sender().objectName()
        print(f"objectName: {objectName}")
        if objectName:
            _info = json.loads(objectName)
            print(f"_info: {_info}")
            if 'db_attr_name' in _info:
                db_attr_name = _info['db_attr_name']
                print(f"db_attr_name: {db_attr_name}")
                Utils.download_file_from_url(url= self.selected_dataObj[db_attr_name])

        self.reset_selected_row()   


    def on_copy_new_row(self):
        self.model.on_copy_new_row_by_template(rowNo=self.selected_rowNo)

        self.reset_selected_row()


