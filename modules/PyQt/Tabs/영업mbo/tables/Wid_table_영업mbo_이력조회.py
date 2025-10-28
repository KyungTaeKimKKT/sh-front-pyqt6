from modules.common_import_v2 import *


class TableView_영업mbo_이력조회(Base_Table_View):
    pass


class TableModel_영업mbo_이력조회(Base_Table_Model):

    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
        super().on_api_send_By_Row()

    def on_custom_editor_complete(self, data:dict):
        """ Custom editor delegate에서 완료 후 들어오는 값을 반영 """

        index = data.get('index')
        value = data.get('value')
        attr_name = self.get_attr_name_by_index(index)
        if attr_name == '담당자':
            self._data[index.row()]['담당자'] = value['user_성명']
            self._data[index.row()]['부서'] = value['MBO_표시명_부서']
            start_index = self.index( index.row(), 0)
            end_index = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index, [Qt.DisplayRole, Qt.CheckStateRole])
            return True
        return super().on_custom_editor_complete(data)

    def setData(self, index:QModelIndex, value:Any, role:int) -> bool:
        super().setData(index, value, role)

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_사용자등록 import TableDelegate_영업mbo_사용자등록 
class TableDelegate_영업mbo_이력조회(TableDelegate_영업mbo_사용자등록):

    def custom_editor_handler(self, 
                              display_name:str, 
                              editor_class:callable, 
                              event: QEvent, 
                              model: TableModel_영업mbo_이력조회, 
                              option: QStyleOptionViewItem, 
                              index: QModelIndex) -> bool:
        field_name = model.get_attrName_from_display(display_name)
        if field_name in self.custom_editor_info and field_name == '담당자':
            ### 💡 3개 table사용으로 channelName에 _table_type_ 추가함 => model subscribe도 변경해야 함.
            editor = editor_class(option.widget,                                         
                                on_complete_channelName=f"{self.table_name}:custom_editor_complete",
                                index=index,
                                data = INFO.MBO_사용자,
                                )
            editor.exec()
            return True
        
        return super().custom_editor_handler(display_name, editor_class, event, model, option, index)



        

class Wid_table_영업mbo_이력조회( Wid_table_Base_for_stacked ):
    
    def setup_table(self):
        self.view = TableView_영업mbo_이력조회(self)
        self.model = TableModel_영업mbo_이력조회(self.view)
        self.delegate = TableDelegate_영업mbo_이력조회(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()

    def init_attributes(self):
        super().init_attributes()

    def disable_row_add_button(self):
        super().disable_row_add_button()
 

    def init_ui(self):
        super().init_ui()

    def subscribe_gbus(self):
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        # if hasattr(self, 'table_name') and self.table_name:
        #     self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.api_datas_changed )
            
    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.

            
    def connect_signals(self):
        """ signal 연결 """
        super().connect_signals()


    def run(self):
        if not hasattr(self, 'url') and not self.url:
            logger.error(f"url이 없읍니다.")

        if not hasattr(self, 'table_name') and not self.table_name:
            logger.error(f"table_name이 없읍니다.")

        super().run()
