from modules.common_import import *

from modules.PyQt.Tabs.차량관리_V2.tables.wid_table_차량관리_V2_운행관리_관리자 import (
    Wid_table_차량관리_V2_운행관리_관리자, 
    TableView_차량관리_V2_운행관리_관리자, 
    TableModel_차량관리_V2_운행관리_관리자, 
    TableDelegate_차량관리_V2_운행관리_관리자,
)

class TableView_차량관리_V2_운행관리_사용자(TableView_차량관리_V2_운행관리_관리자):
    pass

class TableModel_차량관리_V2_운행관리_사용자(TableModel_차량관리_V2_운행관리_관리자):
    pass

class TableDelegate_차량관리_V2_운행관리_사용자(TableDelegate_차량관리_V2_운행관리_관리자):
    pass


class Wid_table_차량관리_V2_운행관리_사용자( Wid_table_Base_for_stacked  ):

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

            'PB_copy_new_row':  {'title': '복사 생성', 
                                    'tooltip': '선택한 줄에 복사 상단에 신규 생성합니다.',
                                    'slot' : self.on_copy_new_row,
                                    'disable_not_selected': True
                                    },
            'PB_Delete': {'title': '삭제', 
                                    'tooltip': '삭제',
                                    'slot' : self.on_delete_row,
                                    'disable_not_selected': True
                                    },
        }
    
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
 

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_차량관리_V2_운행관리_사용자(self)
        self.model = TableModel_차량관리_V2_운행관리_사용자(self.view)
        self.delegate = TableDelegate_차량관리_V2_운행관리_사용자(self.view)
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



