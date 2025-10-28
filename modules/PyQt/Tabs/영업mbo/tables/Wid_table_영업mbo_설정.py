from __future__ import annotations
from modules.common_import_v2 import *
from pathlib import Path

class Status(Enum):
    READY = "준비"
    RUNNING = "진행중"
    COMPLETED = "완료"
    UNDEFINED = "미정"

def check_status(rowDict:dict) -> Status:
    """ 행의 상태를 체크하여 문자열로 반환 : 준비, 진행중, 완료, 미정 """
    is_ready = all ( [ not rowDict.get('is_완료'), not rowDict.get('is_시작')] )
    is_running = all ( [ not rowDict.get('is_완료'), rowDict.get('is_시작')] )
    is_completed = all ( [rowDict.get('is_완료'), rowDict.get('is_시작')] )    
    if is_ready:
        return Status.READY
    elif is_running:
        return Status.RUNNING
    elif is_completed:
        return Status.COMPLETED
    else:
        return Status.UNDEFINED

class TableView_영업mbo_설정(Base_Table_View):
    pass


class TableModel_영업mbo_설정(Base_Table_Model):


    def _role_background(self, row: int, col: int) -> QColor:
        map_status_to_color = {
            Status.READY: QColor(230, 240, 255),     # 준비 → 연한 파랑 (대기 느낌)
            Status.RUNNING: QColor(220, 255, 220),   # 진행중 → 연한 초록 (활동 느낌)
            Status.COMPLETED: QColor(240, 240, 240), # 완료 → 회색톤 (끝난 느낌)
            Status.UNDEFINED: QColor(255, 240, 200), # 미정 → 연한 주황 (경고 느낌)
        }
        return map_status_to_color[check_status(self._data[row])]

        
    def _role_tooltip(self, row: int, col: int) -> str:
        map_status_to_tooltip = {
            Status.READY: "준비 ==> 시작 버튼 클릭하기 바랍니다. <br>시작시 app은 자동 활성화 됩니다.",
            Status.RUNNING: "진행중 ==> 완료는 관리자 등록에서 처리합니다.",
            Status.COMPLETED: "완료 ==> 파일 다운로드",
            Status.UNDEFINED: "미정",
        }
        return map_status_to_tooltip[check_status(self._data[row])]


    # def request_add_row(self, rowNo:int):        
    #     copyed_rowDict = self.copy_row(
    #         rowNo, 
    #         **self.add_row_dict,
    #     )
    #     #### copyed_row 에 추가
    #     try:
    #         latest_row = self._data[0]        
    #         copyed_rowDict['매출_month'] = latest_row['매출_month'] +1 if latest_row['매출_month'] < 12 else 1
    #         copyed_rowDict['매출_year'] = latest_row['매출_year']+1 if copyed_rowDict['매출_month'] == 1 else latest_row['매출_year'] 
    #     except Exception as e:
    #         from datetime import date
    #         copyed_rowDict['매출_month'] = date.today().month -1 if date.today().month > 1 else 12
    #         copyed_rowDict['매출_year'] = date.today().year -1 if date.today().month == 1 else date.today().year
        
    #     _text_question = f"""<p>MBO 설정을 추가하시겠습니까?</p>
    #                         <br>
    #                         <b>매출_year</b>: {copyed_rowDict['매출_year']}년<br>
    #                         <b>매출_month</b>: {copyed_rowDict['매출_month']}월<br><br>
    #                         <span style="color:red; font-weight:bold;">
    #                         순서는 <br>
    #                         1. 'file' 업로드만 가능합니다. ( cell 더블클릭으로 업로드 ) <br>
    #                         2. 'Row 저장' 버튼을 눌러야 추가됩니다. => 업로드된 엑셀 파일 검증<br>
    #                         3. 이후,  'is_시작' 체크 후 'Row 저장' 버튼 클릭으로 MBO 시작.<br>
    #                         4. 평가 후, MBO 완료 체크 후 'Row 저장' 버튼 클릭으로 MBO 완료.<br><br>                                            
    #                         </span>
    #                         """
    #     super().request_add_row(
    #         rowNo=rowNo, 
    #         dlg_question=lambda:Utils.generate_QMsg_question(None, title="MBO 설정 추가", text=_text_question),
    #         dlg_info=lambda:Utils.generate_QMsg_Information(None, title="MBO 설정 추가", text="MBO 설정을 추가되었읍니다.", autoClose=1000),
    #         dlg_critical=lambda:Utils.generate_QMsg_critical(None, title="MBO 설정 추가 실패", text="MBO 설정을 추가하는데 실패했읍니다."),
    #         copyed_rowDict=copyed_rowDict,
    #         api_send = False,
    #     )

    # def request_delete_row(self, rowNo:int):
    #     super().request_delete_row(rowNo)

    # def _is_editable(self, index:QModelIndex) -> bool:
    #     rowNo, colNo = index.row(), index.column()
    #     rowDict = self._data[rowNo]
    #     if all( [rowDict['is_시작'], rowDict['is_완료']] ):
    #         return False

    #     if rowDict['id'] == -1:
    #         col_list = [ self.get_column_no_from_attr_name('file') ]
    #         return colNo in col_list

    #     if not rowDict['is_시작']:
    #         col_list = [ self.get_column_no_from_attr_name('file') ,  self.get_column_no_from_attr_name('is_시작')]
    #         return colNo in col_list
    #     else:
    #         col_list = [ self.get_column_no_from_attr_name('is_완료'), ]
    #         return colNo in col_list
    #     #### unreachable
    #     return super()._is_editable(index)  


    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
        super().on_api_send_By_Row_with_file( file_field_name='file')
        # logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
        # if self._modified_rows:
        #     for row in list(self._modified_rows):
        #         sendData, sendFiles = self.get_sendData_and_sendFiles(self.get_row_data(row), ['file'])
        #         logger.info(f"sendData: {sendData}")
        #         logger.info(f"sendFiles: {sendFiles}")                
        #         _isok, _json = 	APP.API.Send(url= self.url, 
        #                         dataObj=  self.get_id_dict( row ),
        #                         sendData=sendData,
        #                         sendFiles=sendFiles
        #                         )
        #         if _isok:
        #             self.clear_modified_rows([row])
        #             # self.update_api_response( _json , row)
        #             logger.info(f"API 호출 성공: {_json}")
        #             Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
        #             return True
        #         else:
        #             Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
        #             return False
        # else:
        #     return False

class TableDelegate_영업mbo_설정(Base_Delegate):

    def custom_editor_handler(self, db_attr_name:str,  event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        match db_attr_name:
            case 'file':
                editor_class = self.get_custom_editor( db_attr_name )
                editor = editor_class( option.widget)
                if not isinstance( editor, FileOpenSingle ):
                    logger.error(f"custom_editor_handler: {db_attr_name} 에디터 클래스가 없읍니다.")
                    return False

                file_path = editor.open_file_dialog()
                if file_path:
                    parentWid = model.parent().parent()
                    if isinstance(parentWid, Wid_table_영업mbo_설정):

                        parentWid.excel_to_tableview(path= file_path)
                model.setData(index, file_path, Qt.ItemDataRole.EditRole)
                return True

            case _:
                logger.error(f"custom_editor_handler: {db_attr_name} 에디터 클래스가 없읍니다.")
            
        return False


class Dlg_Excel_미리보기(QDialog):
    """ kwargs 에 따라 미리보기 데이터를 검증하고 저장 데이터를 반환함. 
        path : local file path
        kwargs : 
            required_cols : 필수 컬럼 리스트
            data_type_dict : 데이터 타입 검증 딕셔너리
            unique_same_cols : 동일성 검증 컬럼 리스트
    """
    def __init__(self, parent=None, path:str=None, **kwargs):
        super().__init__(parent)
        self.path = path
        self.kwargs = kwargs
        self.df : Optional[pd.DataFrame] = None
        self.send_data:dict = {}
        self.send_file:dict = {}
        self.setMinimumSize( kwargs.get('minw', 1200), kwargs.get('minh', 1200) )

        self.init_all()

    def init_all(self):
        _data_ok, _data_msg = self.init_data()
        if not _data_ok:
            Utils.generate_QMsg_critical(self, title=_data_msg['title'], text=_data_msg['text'])
            self.reject()
        
        _validate_ok, _validate_msg = self.validate_data()
        if not _validate_ok:
            Utils.generate_QMsg_critical(self, title=_validate_msg['title'], text=_validate_msg['text'])
            self.reject()

        self.setup_ui()

    def init_data(self) -> tuple[bool, dict]:
        if not self.check_file_path(self.path):
            return False, {'title': "파일 없음", 'text': "파일이 없습니다."}
        ext = Path(self.path).suffix.lower()

        try:
            if ext in [".xls", ".xlsx"]:
                self.df = pd.read_excel(self.path)
            elif ext == ".csv":
                self.df = pd.read_csv(self.path, encoding="utf-8-sig")
            else:
                return False, {
                    'title': "지원하지 않는 형식",
                    'text': f"지원하지 않는 파일 확장자입니다: {ext}"
                }
        except Exception as e:
            return False, {'title': "읽기 오류", 'text': str(e)}

        return True, {}
    
    def validate_data(self) -> tuple[bool, dict]:
        # 1. 필수 컬럼 검증
        df = self.df
        required_cols = self.kwargs.get('required_cols', ['매출_year', '매출_month', '금액','현장명','id_made'])
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return False, {'title': "컬럼 누락", 'text': f"Excel 파일에 다음 필수 컬럼이 없습니다:\n{', '.join(missing_cols)}"}

        # 2. 데이터 타입 검증 (int)
        data_type_dict = self.kwargs.get('data_type_dict', {'매출_year': int, '매출_month': int, '금액': int})
        for col, data_type in data_type_dict.items():
            if df[col].isnull().any():
                return False, {'title': "데이터 오류", 'text': f"'{col}' 컬럼에 빈 값이 있습니다."}
            try:
                df[col] = df[col].astype(data_type)
            except ValueError as e:
                return False, {'title': "데이터 오류", 'text': f"'{col}' 컬럼에 {data_type}가 아닌 값이 있습니다.\n{e}"}

        # 3. 매출_year / 매출_month 동일성 검증
        unique_same_cols = self.kwargs.get('unique_same_cols', ['매출_year', '매출_month'])
        for col in unique_same_cols:
            if len(df[col].unique()) != 1:
                return False, {'title': "데이터 오류", 'text': f"모든 행의 '{col}' 는 동일해야 합니다."}

        # 4. unique, not duplicated 검증
        unique_not_duplicated = self.kwargs.get('unique_not_duplicated', [])
        for col in unique_not_duplicated:
            duplicated = df[df[col].duplicated(keep=False)][col].unique()
            if len(duplicated) > 0:
                return False, {
                    'title': "데이터 오류",
                    'text': f"'{col}' 컬럼에 중복 값이 있습니다:\n{', '.join(map(str, duplicated))}"
                }
            
        return True, {}
    
    def check_file_path(self, path:str):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "파일 없음", "파일이 없습니다.")
            return False
        return True
    

    
    def _set_stylesheet(self, widget:QWidget):
        widget.setStyleSheet("""
            font-weight: bold;               /* 글자 굵게 */
            background-color: lightyellow;   /* 배경색 */
            color: darkblue;                 /* 글자색 */
            border: 1px solid gray;          /* 테두리 */
            border-radius: 5px;              /* 모서리 둥글게 */
            padding: 5px;                    /* 안쪽 여백 */
            font-size: 13pt;                 /* 글자 크기 */
        """)

    def setup_ui(self):
        
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(self.kwargs.get('title', "MBO 실적 Excel 미리보기"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(10, 10, 10, 10)
        btn_layout.addStretch()
        self.btn_save = QPushButton("저장")
        self.btn_save.clicked.connect( self.on_save)
        btn_layout.addWidget(self.btn_save)
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.clicked.connect(self.reject )
        btn_layout.addWidget(self.btn_cancel)
        layout.addWidget(btn_container)

        summary_text = self.get_summary_text()
        summary_label = QLabel(summary_text)
        self._set_stylesheet(summary_label)
        layout.addWidget(summary_label)

        view = QTableView(self)
        model = DataFrameTableModel(self.df, parent=view)  # DataFrame → TableView 모델
        view.setModel(model)
        view.resizeColumnsToContents()
        layout.addWidget(view)

    def get_summary_text(self) -> str:
        total_amount = self.df['금액'].sum()
        return f"""
            <p>총 건수 : {len(self.df)}</p>
            <p>매출_year : {self.df['매출_year'].iloc[0]}</p>
            <p>매출_month : {self.df['매출_month'].iloc[0]}</p>
            <p>총 금액 : {total_amount/1e8:.2f} 억원 ( {total_amount:,} 원 )</p>
        """

    def on_save(self):
        self.send_data = {
            '매출_year': self.df['매출_year'].iloc[0],
            '매출_month': self.df['매출_month'].iloc[0],
            'is_시작': False,
            'is_완료': False,
        }
        self.send_data['excel_datas'] = self.df.to_dict(orient='records')
        self.send_file = { 'file': open(self.path, 'rb') }
        self.accept()

    def get_send_data(self) -> tuple[dict, list]:
        return self.send_data, self.send_file
        

class Wid_table_영업mbo_설정( Wid_table_Base_V2 ):

    def setup_table(self):
        self.view = TableView_영업mbo_설정(self)
        self.model = TableModel_영업mbo_설정(self.view)
        self.delegate = TableDelegate_영업mbo_설정(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)




    def _check_MENU_by_selected_row(self, selected_rowNo:int) -> None:
        """ 선택된 행에 따라 활성/비활성 처리 : self.validate_menu_pb 에서 호출됨 """
        default_names = [  "PB_File_Download" ] 
        enable_map = {
            Status.READY : ["시작", "PB_Delete", ],
            Status.RUNNING : [ "PB_Delete" ],   ### 완료는 여기서 못함 : admin 등록 app에서 처리함.
            Status.COMPLETED : [ ] if INFO.USERID != 1 else ["PB_Delete"],
        }
        status = check_status(self.selected_dataObj)
        if status == Status.UNDEFINED:
            print(f"status is UNDEFINED : {self.selected_dataObj}")
            return
        enable_names = enable_map[status] + default_names        
        #### enable, disable 처리
        for name, PB in self.map_menu_to_pb.items():
            if name in enable_names:
                PB.setEnabled(True)
            else:
                PB.setEnabled(False)


    def _check_MENU_by_not_selected(self) -> None:
        """ api_datas에 따라 "disable_not_selected": true 인 pb활성/비활성: self.validate_menu_pb 에서 호출됨  """
        if self.api_datas:
            ### "PB_New", "PB_New_by_File"
            PB = self.map_menu_to_pb.get('PB_New', None)
            if PB:
                PB.setEnabled(False)
            PB = self.map_menu_to_pb.get('PB_New_by_File', None)
            if PB:
                is_completed = all ( [self.api_datas[0].get('is_완료'), self.api_datas[0].get('is_시작')] )
                PB.setEnabled(is_completed)



    def on_new_row_by_excel(self):
        editor = FileOpenSingle(self)
        file_path = editor.open_file_dialog()
        if all ( [file_path, os.path.exists(file_path)] ):
            dlg = Dlg_Excel_미리보기(self, path=file_path, title="MBO 실적 Excel 미리보기")
            if dlg.exec():
                send_data, send_file = dlg.get_send_data()
                send_data['excel_datas'] = json.dumps(send_data['excel_datas'], ensure_ascii=False)
                # url = f"{self.url}/bulk_create/".replace('//','/')
                _isok, _json = APP.API.Send_bulk( url=self.url, added_url='bulk_create/', detail=False, dataObj={'id':-1}, 
                                                 sendData=send_data, sendFiles=send_file )
                if _isok:
                    self.api_datas.insert(0, _json)
                    # self.model._data.insert(0, _json)
                    self.model.layoutChanged.emit()
                    Utils.generate_QMsg_Information(self, title="MBO 실적 추가", text="MBO 실적 추가 완료", autoClose=1000)
                else:
                    Utils.generate_QMsg_critical(self, title="MBO 실적 추가 실패", text=f"MBO 실적 추가 실패; <br>{_json}")
        else:
            Utils.generate_QMsg_critical(self, title="파일 없음", text=f"{file_path} 파일이 없습니다.")
        

    def on_file_upload(self):
        model : TableModel_영업mbo_설정 = self.model
        index = model.index_from_row_col(self.selected_rowNo, model.get_column_no_from_attr_name('file'))
        self.simulate_double_click(index= index )
        # self.excel_to_tableview(path= model.data(index, Qt.ItemDataRole.EditRole))

        self.reset_selected_row()


    # def on_file_download(self):
    #     pass


    def on_start_mbo(self):
        _is_ok, _json = APP.API.Send_bulk( url=self.url, added_url='update_진행현황/', detail=True,
                                          dataObj=self.selected_dataObj, sendData={'is_시작':True})
        if _is_ok:
            self.model.update_row_data(self.selected_rowNo, _json)
            Utils.generate_QMsg_Information(self, title="MBO 시작", text="MBO 시작 완료", autoClose=1000)
        else:
            Utils.generate_QMsg_critical(self, title="MBO 시작 실패", text=f"MBO 시작 실패:<br>{_json}")

        self.reset_selected_row()

    def on_gongji_popup(self):
        from modules.PyQt.Tabs.공지및요청사항.dialog.dialog_공지내용_편집 import Dialog_공지내용_편집
        id = self.selected_dataObj['id']
        _isok, _json = APP.API.getObj_byURL( f"{self.url}{id}/get_gongi/")
        if _isok:
            dlg = Dialog_공지내용_편집(self, obj=_json, url=self.url)            
            dlg.exec()
        else:
            Utils.generate_QMsg_critical(self, title="공지사항 조회 실패", text="공지사항 조회 실패")



    def excel_to_tableview(self, path: str):
        """
        Excel 파일을 읽어 TableView에 미리 적용 (사전 검증)
        :param path: Excel 파일 경로
        """
        try:
            # 0. 파일 존재 여부 확인
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "파일 없음", "파일이 없습니다.")
                return

            # 1. Excel 읽기
            df = pd.read_excel(path)

            # 2. 필수 컬럼 검증
            required_cols = ['매출_year', '매출_month', '금액','현장명','id_made']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                QMessageBox.warning(
                    self, "컬럼 누락",
                    f"Excel 파일에 다음 필수 컬럼이 없습니다:\n{', '.join(missing_cols)}"
                )
                return

            # 3. 데이터 타입 검증 (int)
            for col in ['매출_year', '매출_month', '금액']:
                if df[col].isnull().any():
                    QMessageBox.warning(self, "데이터 오류", f"'{col}' 컬럼에 빈 값이 있습니다.")
                    return
                try:
                    df[col] = df[col].astype(int)
                except ValueError as e:
                    QMessageBox.warning(self, "데이터 오류", f"'{col}' 컬럼에 숫자가 아닌 값이 있습니다.\n{e}")
                    return

            # 4. 매출_year / 매출_month 동일성 검증
            if len(df['매출_year'].unique()) != 1 or len(df['매출_month'].unique()) != 1:
                QMessageBox.warning(self, "데이터 오류", "모든 행의 매출_year / 매출_month는 동일해야 합니다.")
                return

            # 5. 사전 검증 메시지
            total_amount = df['금액'].sum()
            _text = f"""
                <p>총 건수 : {len(df)}</p>
                <p>매출_year : {df['매출_year'].iloc[0]}</p>
                <p>매출_month : {df['매출_month'].iloc[0]}</p>
                <p>총 금액 : {total_amount/1e8:.2f} 억원 ( {total_amount:,} 원 )</p>
            """

            # 6. Dialog + TableView
            dlg = QDialog(self)
            dlg.setWindowTitle("Excel 미리보기")
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(10, 10, 10, 10)

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(10, 10, 10, 10)
            btn_layout.addStretch()
            btn_save = QPushButton("저장")
            btn_save.clicked.connect(lambda: self.on_save_excel(df))
            btn_layout.addWidget(btn_save)
            btn_cancel = QPushButton("취소")
            btn_cancel.clicked.connect(dlg.close)
            btn_layout.addWidget(btn_cancel)
            layout.addWidget(btn_container)
            layout.addSpacing(10)

            view = QTableView(dlg)
            model = DataFrameTableModel(df, parent=view)  # DataFrame → TableView 모델
            view.setModel(model)
            view.resizeColumnsToContents()
            layout.addWidget(view)

            dlg.exec()

        except Exception as e:
            QMessageBox.critical(
                self, "Excel 로드 실패",
                f"파일을 열 수 없습니다:\n{e}"
            )