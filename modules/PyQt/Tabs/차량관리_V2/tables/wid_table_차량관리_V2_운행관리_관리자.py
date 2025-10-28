from modules.common_import import *

class TableView_차량관리_V2_운행관리_관리자(Base_Table_View):
    pass

class TableModel_차량관리_V2_운행관리_관리자(Base_Table_Model):

    

    @property
    def add_row_dict(self) -> dict:
        return {
            'remaining_keys': ['차량번호','차량번호_fk' ],
            'remaining_add_dict': {},
            'update_dict': {'id': self.created_id, 
                            '일자': datetime.now().isoformat(),
                            '주행거리': 0,
                            '정비금액': 0,
                            '담당자_snapshot': INFO.USERNAME,
                            '담당자_fk': INFO.USERID,
                            },
        }

    @property
    def money_columns(self) -> list[str]:
        return ['주행거리','정비금액']


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

class TableDelegate_차량관리_V2_운행관리_관리자(Base_Delegate):
    pass


class Wid_table_차량관리_V2_운행관리_관리자( Wid_table_Base_for_stacked ):

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
            # 'PB_New':           {'title': '신규 생성', 
            #                         'tooltip': '첫번째 줄에 신규 생성합니다.',
            #                         'slot' : self.on_new_row,
            #                         'disable_not_selected': False
            #                         },
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
    
    @property
    def new_default_dict(self):
        return {
            'id' : -1,
            '일자' : datetime.now().strftime("%Y-%m-%d"),
            '주행거리' : 0,
            '정비금액' : 0,
            '담당자' : INFO.USERNAME,
            '담당자_fk' : INFO.USERID,
        }
    


    def on_new_row(self):
        pass
    #     if self.model.rowCount() > 0:
    #         self.model.request_new_row( api_send=False)
    #     else:
    #         default_dict = {
    #             'id' : -1,
    #             '일자' : datetime.now().strftime("%Y-%m-%d"),
    #             '주행거리' : 0,
    #             '정비금액' : 0,
    #             '담당자' : INFO.USERNAME,
    #             '담당자_fk' : INFO.USERID,
    #             '차량번호': 
    #         }
    #         self.model.request_new_row( new_default_dict=default_dict, api_send=False)
    #     self.clear_selected_row()
    #     self.disable_pb_list_when_Not_row_selected()

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
        dlg = Dlg_Users_Select_Only_Table( self, 
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
        self.view = TableView_차량관리_V2_운행관리_관리자(self)
        self.model = TableModel_차량관리_V2_운행관리_관리자(self.view)
        self.delegate = TableDelegate_차량관리_V2_운행관리_관리자(self.view)
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

