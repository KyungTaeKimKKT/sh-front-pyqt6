from modules.common_import import *

class TableView_차량관리_V2_기준정보(Base_Table_View):
    pass

class TableModel_차량관리_V2_기준정보(Base_Table_Model):

    @property
    def add_row_dict(self) -> dict:
        return {
            'remaining_keys': ['법인명' ],
            'remaining_add_dict': {},
            'update_dict': {'id': -1, 
                            '차종': '필수입력',
                            '차량번호': '필수입력',
                            '시작일': datetime.now().strftime("%Y-%m-%d"),
                            '종료일': datetime.now().strftime("%Y-%m-%d"),
                            '차량가격': 0,
                            '보증금': 0,
                            '대여료_VAT포함': 0,
                            '약정운행거리': 0,
                            '초과거리부담금': 0,
                            'is_exist': True,
                            },
        }

    @property
    def money_columns(self) -> list[str]:
        return ['차량가격','보증금','대여료_VAT포함', '약정운행거리']

    # #### Menu Hander 에서 호출되는 함수
    # def request_on_add_row(self, rowNo: int):

    #     copyed_row = copy.deepcopy(self._data[rowNo])
    #     copyed_row['id'] = -1
    #     copyed_row['등록일'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     copyed_row['user_list'] = []
    #     copyed_row['user_pks'] = []
    #     copyed_row['app사용자수'] = 0

    #     self.beginInsertRows(QModelIndex(), rowNo, rowNo)
    #     # self.insertRow(rowNo)
    #     self._data.insert(rowNo, copyed_row)
    #     self.endInsertRows()
    #     logger.info(f"[Base] Row {rowNo+1} 추가 완료")


    # def on_user_select(self, rowDict:dict):
    #     self.request_on_user_select( 
    #         rowNo=self._data.index(rowDict),
    #         colNo = self.get_column_No_by_field_name('user_list'),
    #     )



    # def request_on_user_select(self, rowNo:int, colNo:int):
    #     """ user select 시 호출되는 함수 """
    #     logger.info(f"request_on_user_select: {rowNo}, {colNo}")
        
    #     data:list[dict] = self._data[rowNo]['user_list']
    #     logger.info(f"data: {data}")
    #     id = self._data[rowNo]['id']
    #     editor = UsersDialog_with_tree_table( self.parent(),
    #                          app_ID =  self._data[rowNo]['id'],
    #                          pre_selected_ids = data,
    #                          api_url=API_URLS.APP권한_사용자_M2M_Bulk,
    #                          on_complete_channelName=None,
    #                          index = self.index(rowNo, colNo),
    #                          )
    #     if editor.exec():
    #         response_data = editor.get_response_data()
    #         Utils.generate_QMsg_Information(None, title="사용자 선택 완료", text="사용자 선택 완료", autoClose=1000)
    #         self.update_row_data(rowNo, response_data)
    #         logger.info(f"response_data: {response_data}") #### 현재 row data 전체를 받음.




    def _role_display(self, row: int, col: int) -> str:
        attr_name = self.get_attr_name_by_column_no(col)    
        if attr_name in self.money_columns:
            return self.convert_by_money_unit(self._data[row][attr_name])
        return super()._role_display(row, col)
    
    def _role_tooltip(self, row: int, col: int) -> str:
        if '관리자수' == self.get_attr_name_by_column_no(col):
            tooltip = ''
            for user_id in self._data[row]['관리자_ids']:
                user_info = INFO._get_user_info(user_id)
                if user_info:
                    user_name = user_info.get('user_성명', '알수없음')                    
                else:
                    user_name = '알수없음'
                tooltip += f"{user_name},"
            return tooltip
        return super()._role_tooltip(row, col)
    
    def _role_data(self, row: int, col: int) -> str:
        return super()._role_data(row, col)
    
    def _role_edit(self, row: int, col: int) -> str:
        return super()._role_edit(row, col)
    
    def _role_check(self, row: int, col: int) -> str:
        return super()._role_check(row, col)

    def convert_by_money_unit(self, value:int|float) -> str:
        """ 금액 단위 변환 """
        self.money_unit = 1
        match self.money_unit:
            case 1:
                return f"{value:,}"  # 천 단위 쉼표 추가
            case 1000:
                return f"{value/1000:,.0f}"  # 천원 단위, 소수점 없이
            case 1000000:
                return f"{value/1000000:,.0f}"  # 백만원 단위, 소수점 1자리
            case 100000000:
                return f"{value/100000000:,.2f}"  # 억 단위, 소수점 2자리
            case _:
                return str(value)

class TableDelegate_차량관리_V2_기준정보(Base_Delegate):

    def user_defined_creatorEditor_설정(self, widget:object, headerName:str, value:Any,  parent, index, option) -> object:
        self.current_editor = widget
        model:Base_Table_Model = index.model()
        db_attr_name = model.get_attr_name_by_column_no(index.column())
        if isinstance(widget, QDateEdit) and db_attr_name == '시작일':
            widget.setMinimumDate( QDate(2000, 1, 1) )
            widget.setMaximumDate( QDate(2999, 12, 31) )
        return widget




class Dlg_차량관리_V2_기준정보_사용자선택(Dlg_Users_Select_Only_Table):

    def confirm_save(self, selected_users:list[int]=[], added_users:list[int]=[], deleted_ids:list[int]=[], **kwargs) -> bool:
        """저장 확인 대화창 표시"""
        _text = f"""
        <b>기존 사용자</b>: {self.pre_selected_user_count}명 → <b>변경 사용자</b>: {len(selected_users)}명<br><br>
        <u>상세내역</u><br>
        <span style="color:green;">➕ 추가 사용자</span>: {len(added_users)}명<br>
        <span style="color:red;">➖ 삭제 사용자</span>: {len(deleted_ids)}명<br><br>
        <b>저장하시겠습니까?</b><br><br>
        <i><b>참조: 자동으로 App권한 사용자에 update 됩니다.</b></i>
        """
        return Utils.QMsg_question (self, title="사용자 변경 정보", text=_text) 


class Wid_table_차량관리_V2_기준정보( Wid_table_Base_for_stacked ):

    @property
    def map_index_to_widget(self):
        if not hasattr(self, 'widget_menu') or not isinstance(self.widget_menu, QWidget):
            self.widget_menu = self._create_widget_menu()
        return {
            1: self.widget_menu
        }

    @property
    def map_pb_to_generate_info(self):
        """ widget 버튼 접근은 self.key_name 으로 접근함. 
            즉, self.PB_New 로 접근함.
        """
        return {
            'PB_New':           {'title': '신규 생성', 
                                    'tooltip': '첫번째 줄에 신규 생성합니다.',
                                    'slot' : self.on_new_row,
                                    'disable_not_selected': False
                                    },
            'PB_copy_new_row':  {'title': '복사 생성', 
                                    'tooltip': '선택한 줄에 복사 상단에 신규 생성합니다.',
                                    'slot' : self.on_copy_new_row,
                                    'disable_not_selected': True
                                    },
            'PB_User_Select': {'title': '사용자 선택', 
                                    'tooltip': '✅ 차량 등록 저장 후 사용자 선택 가능합니다.',
                                    'slot' : self.on_user_select,
                                'disable_not_selected': True
                                    },
            'PB_Delete': {'title': '삭제', 
                                    'tooltip': '삭제',
                                    'slot' : self.on_delete_row,
                                    'disable_not_selected': True
                                    },
        }
    
    def on_new_row(self):
        self.model.request_new_row( api_send=False)
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()

    def on_copy_new_row(self):
        if not (hasattr(self, 'selected_rows') or self.selected_rows):
            return
        self.model.request_add_row(rowNo=self.selected_rowNo, api_send=False)
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):
        if not ( self.selected_rowNo and self.selected_dataObj ):
            return
        self.model.request_delete_row(
            rowNo=self.selected_rowNo,
            dlg_question=lambda: Utils.QMsg_question(self, title="삭제 확인", text="삭제하시겠습니까?"),
            dlg_info=lambda: Utils.QMsg_Info(self, title="삭제 완료", text="삭제 완료", autoClose=1000),
            dlg_critical=lambda: Utils.QMsg_Critical(self, title="삭제 실패", text="삭제 실패"),
            # rowObj=self.selected_dataObj,
        )
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()

    def on_user_select(self):
        ### ✅ 25-7-3 추가
        if self.selected_rowNo is None or self.selected_dataObj is None or not self.selected_dataObj:
            return
      
        pre_selected_ids:list[dict] = self.selected_dataObj.get('사용자_datas', [])
        app_id = self.selected_dataObj.get('id')
        
        if app_id < 1:
            Utils.QMsg_Critical(self, title="차량 선택 오류", text="차량은 먼저 저장되어야 합니다.")
            return
        dlg = Dlg_차량관리_V2_기준정보_사용자선택( self, 
                                app_ID= app_id,
                               all_users=INFO.ALL_USER, 
                               api_url= f"{self.url}사용자_M2M_Bulk/".replace('//', '/'), 
                               on_complete_channelName=None, 
                               pre_selected_ids = pre_selected_ids,
                               user_attr_name='user_fk'
                               )
        if dlg.exec():
            response_data = dlg.get_response_data()
            self.model.update_row_data(rowNo=self.selected_rowNo, value=response_data)
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()


    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_차량관리_V2_기준정보(self)
        self.model = TableModel_차량관리_V2_기준정보(self.view)
        self.delegate = TableDelegate_차량관리_V2_기준정보(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()

    def init_attributes(self):
        super().init_attributes()

    def init_ui(self):
        super().init_ui()

    def subscribe_gbus(self):
        super().subscribe_gbus()
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        # if hasattr(self, 'table_name') and self.table_name:
        #     self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.api_datas_changed )
            
    def unsubscribe_gbus(self):
        try:
            super().unsubscribe_gbus()
            self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        except Exception as e:
            logger.error(f"unsubscribe_gbus error: {e}")


            
    def connect_signals(self):
        """ signal 연결 """
        super().connect_signals()


    def run(self):
        if not ( hasattr(self, 'url') and self.url):
            logger.error(f"url이 없읍니다.")

        if not ( hasattr(self, 'table_name') and self.table_name):
            logger.error(f"table_name이 없읍니다.")

        super().run()

    def disable_pb_list_when_Not_row_selected(self):
        super().disable_pb_list_when_Not_row_selected()
        ###  사용자는 다른 MODEL 이므로, 먼저 차량정보가 DB에 저장을 선행함.
        self.PB_User_Select.setEnabled( bool( self.selected_rowNo and self.selected_dataObj['id'] > 1 ))

