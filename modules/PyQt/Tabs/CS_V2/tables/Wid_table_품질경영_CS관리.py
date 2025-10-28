from modules.common_import_v2 import *



class TableView_품질경영_CS관리(Base_Table_View):
    pass



class TableModel_품질경영_CS관리(Base_Table_Model):

    등록자_fk_Column_No = None
    완료자_fk_Column_No = None
    claim_file_수_Column_No = None
    activity_file_수_Column_No = None   
    Column_No_Dict = {
        '등록자_fk': 등록자_fk_Column_No,
        '완료자_fk': 완료자_fk_Column_No,
        'claim_file_수': claim_file_수_Column_No,
        'activity_file_수': activity_file_수_Column_No,
    }




    def on_request_claim_open(self, selected_rows:list[dict]):
        logger.info(f"on_request_claim_open: {selected_rows}")
        if not selected_rows and isinstance(selected_rows, list) and isinstance(selected_rows[0], dict):
            return
        selected_rows_data = [self.create_model_data_by_row(row) for row in selected_rows]
        selected_rows_ids = [row['id'] for row in selected_rows]

        try:
            for id, selected_row in zip(selected_rows_ids, selected_rows_data):                
                index = self._data.index( selected_row )
                logger.info(f"index: {index}")
                _isok, _json = APP.API.Send(self.url, { 'id': id }, { 'id': id , '진행현황':'Open'})

                if _isok:
                    self._data.pop(index)
                    self.beginRemoveRows(QModelIndex(), index, index)
                    self.endRemoveRows()
                    self.dataChanged.emit(self.index(index, 0), self.index(index, self.columnCount() - 1), [Qt.DisplayRole])
                    #### empty
                    if not self._data:
                        self.event_bus.publish(f"{self.table_name}:empty_data", True)
                else:
                    Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")

        except Exception as e:
            logger.error(f"on_request_claim_open: {e}")
            logger.error(f"{traceback.format_exc()}")
            Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")
	
    def request_add_claim_project(self, rowNo:int):
        return 
        logger.info(f"request_add_claim_project: {rowNo}")
        copyed_row = copy.deepcopy( self._data[rowNo])
        일자_colNo = self.get_column_No_by_field_name('일자')        
        id_colNo = self.get_column_No_by_field_name('id')
        소요시간_colNo = self.get_column_No_by_field_name('소요시간')
        for idx, value in enumerate(copyed_row):
            if idx == id_colNo: 
                copyed_row[idx] = -1
            elif idx == 소요시간_colNo:
                copyed_row[idx] = 0
            elif idx != 일자_colNo:
                copyed_row[idx] = ''

        # View에 삽입 알림 시작
        self.beginInsertRows(QModelIndex(), rowNo, rowNo)
        self._data.insert(rowNo, copyed_row)    
        self.endInsertRows()
        self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])

    def request_delete_claim_project(self, rowNo:int):
        super().request_delete_row(
            rowNo= rowNo,
            dlg_question= lambda : Utils.generate_QMsg_question(None, title="클레임 프로젝트 삭제", text="클레임 프로젝트를 삭제하시겠습니까?"),
            dlg_info = lambda : Utils.generate_QMsg_Information(None, title="Claim 삭제", text="Claim 삭제 성공", autoClose=1000),
            dlg_critical = lambda : Utils.generate_QMsg_critical(None, title="Claim 삭제", text="Claim 삭제 실패"),
            )


    def request_file_view(self, rowNo:int, colNo:int):
        if not (self.claim_file_수_Column_No  and self.activity_file_수_Column_No ):
            self.get_class_attr_column_No()

        if colNo == self.claim_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('claim_files_url')]
        elif colNo == self.activity_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('activty_files_url')]
        else:
            return

        if urls :
            dlg = FileViewer_Dialog( self.parent(), files_list=urls)
            dlg.exec()

    def request_file_download(self, rowNo:int, colNo:int):
        if not (self.claim_file_수_Column_No  and self.activity_file_수_Column_No ):
            self.get_class_attr_column_No()

        if colNo == self.claim_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('claim_files_url')]
            self._download_multiple_files(urls)

        elif colNo == self.activity_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('activty_files_url')]
            self._download_multiple_files(urls)

        else:
            return  


    def _download_multiple_files(self, urls:list[str]):
        if not urls:
            return
        try:
            for url in urls:
                fName = Utils.func_filedownload(url)
        except Exception as e:
            logger.error(f"request_file_download: {e}")
            logger.error(f"{traceback.format_exc()}")
            Utils.generate_QMsg_critical(None, title="파일 다운로드 실패", text="파일 다운로드 실패")


    def get_class_attr_column_No(self):
        if hasattr(self, 'Column_No_Dict'):
            for attr_name, column_no_value in self.Column_No_Dict.items():
                if column_no_value is None:
                    col_no = self.get_column_No_by_field_name(attr_name)
                    setattr(self, f"{attr_name}_Column_No", col_no)
                    self.Column_No_Dict[attr_name] = col_no  # 선택적: dict도 업데이트해두면 추후 디버깅에 편함

    def _role_display(self, row:int, col:int) -> Any:
        return super()._role_display(row, col)
        self.get_class_attr_column_No()

        if col ==self.등록자_fk_Column_No or col == self.완료자_fk_Column_No:
            try:
                _fk:int = self._data[row][col]
                if isinstance(_fk, int) and _fk > 0:
                    return INFO.USER_MAP_ID_TO_USER[_fk]['user_성명']
            except Exception as e:
                logger.error(f"get_class_attr_column_No: {e}")
                logger.error(f"{traceback.format_exc()}")
                return str(_fk)        
        
        return super()._role_display(row, col)

    def format_date_str(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
            day = dt.day
            month = dt.month
            return f"{month}월{day}일 ({weekday_kr})"  # 줄바꿈 포함
        except Exception:
            return date_str

    def _role_background(self, row:int, col:int) -> QColor:
        return super()._role_background(row, col)
				
    
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """
        return super()._is_editable(index)
    
    def _is_menu_visible(self, rowNo:int) -> bool:
        """ override : 편집 불가능 row는 메뉴 생성 안함."""
        return True


    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
        super().on_api_send_By_Row()
        # logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
        # if self._modified_rows:
        #     bulk_data = []
        #     for row in list(self._modified_rows):
        #         #### 무조건 보냄... 원본과 비교가 불가: 왜냐면 막  추가되는 경우가 많음
        #         # if self._data[row] == self._original_data[row]:
        #         #     continue
        #         bulk_data.append( self.get_row_data(row) )
        #     if bulk_data:                    

        #         _isok, _json = APP.API.post(url= self.url+f"bulk/",  data={'datas': json.dumps(bulk_data, ensure_ascii=False)})
        #         if _isok:
        #             logger.info(f"API 호출 성공:  {type(_json)}, {_json}")
        #             self.event_bus.publish(f"{self.table_name}:datas_changed", _json)
        #             self.clear_modified_rows(list(self._modified_rows))
        #             logger.info(f"API 호출 성공: {_json}")
        #             Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
        #         else:
        #             Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
	
  


class TableDelegate_품질경영_CS관리(Base_Delegate):

    def custom_editor_handler(self, display_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        return False


        

class Wid_table_품질경영_CS관리( Wid_table_Base_V2):

    def setup_table(self):
        self.view = TableView_품질경영_CS관리(self)
        self.model = TableModel_품질경영_CS관리(self.view)
        self.delegate = TableDelegate_품질경영_CS관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def subscribe_gbus(self):
        super().subscribe_gbus()
        self.event_bus.subscribe(f"{self.table_name}:gantt_chart_action", self.on_gantt_chart_action)

    def unsubscribe_gbus(self):
        super().unsubscribe_gbus()
        self.event_bus.unsubscribe(f"{self.table_name}:gantt_chart_action", self.on_gantt_chart_action)

    def on_gantt_chart_action(self, event_data:dict):
        print(f"event_data : {event_data}")
        key = event_data.get('key', '')
        id = event_data.get('selected_id', -1)
        if id > 0:
            self.selected_dataObj = self.id_to_api_data.get(id, None)
            print(f"self.selected_dataObj : {self.selected_dataObj}")
            self.enable_pb_list_when_row_selected()
        else:
            self.selected_dataObj = None
            self.disable_pb_list_when_Not_row_selected()
        
        pb: QPushButton = self.map_menu_to_pb.get(key, None)
        if pb:
            pb.click()
        else:
            print(f"pb is not found : {key}")
        self.reset_selected_row()



    def on_claim_new_project(self):
        self._lazy_source_widget.on_claim_new_project()
        self.reset_selected_row()
        

    def on_claim_edit_view(self):
        self._lazy_source_widget.on_claim_edit_view(self.selected_dataObj)
        self.reset_selected_row()

    def on_action_register(self):
        self._lazy_source_widget.on_action_register(self.selected_dataObj)
        self.reset_selected_row()

    def on_action_view(self):
        self._lazy_source_widget.on_action_view(self.selected_dataObj)
        self.reset_selected_row()


    def on_file_download_multiple(self):
        objectName = self.sender().objectName()
        urls = self.selected_dataObj[objectName]
        if urls:
            self._lazy_source_widget.on_file_download_multiple(urls)
        self.reset_selected_row()

    def on_file_view(self):
        objectName = self.sender().objectName()
        urls = self.selected_dataObj.get(objectName, [])
        if urls:
            self._lazy_source_widget.on_file_view(urls)
        self.reset_selected_row()

    def on_delete_row(self):
        self._lazy_source_widget.on_delete_row(self.selected_dataObj)
        self.reset_selected_row()

    def on_request_claim_open(self):
        self._lazy_source_widget.on_request_claim_open(self.selected_dataObj)
        self.reset_selected_row()

    def on_request_claim_accept(self):
        self._lazy_source_widget.on_request_claim_accept(self.selected_dataObj)
        self.reset_selected_row()

    def on_request_claim_close(self):
        self._lazy_source_widget.on_request_claim_close(self.selected_dataObj)
        self.reset_selected_row()


    def on_request_claim_open(self):
        try:
            self._lazy_source_widget.on_request_claim_open(self.selected_dataObj)
            self.reset_selected_row()
        except Exception as e:
            logger.error(f"on_request_claim_open : {e}")
            return

    def on_request_claim_close(self):
        try:
            self._lazy_source_widget.on_request_claim_close(self.selected_dataObj)
            self.reset_selected_row()
        except Exception as e:
            logger.error(f"on_request_claim_close : {e}")
            return


    def on_request_map_view(self):
        try:
            self._lazy_source_widget.on_request_map_view(self.selected_dataObj)
            self.reset_selected_row()
        except Exception as e:
            logger.error(f"on_request_map_view : {e}")
            return

    def on_request_action_register(self):
        try:
            self._lazy_source_widget.on_request_action_register(self.selected_dataObj)
            self.reset_selected_row()
        except Exception as e:
            logger.error(f"on_claim_project_activity : {e}")
            return

    def on_map_view(self):
        try:
            self._lazy_source_widget.on_map_view(self.selected_dataObj)
            self.reset_selected_row()
        except Exception as e:
            logger.error(f"on_map_view : {e}")
            return
   