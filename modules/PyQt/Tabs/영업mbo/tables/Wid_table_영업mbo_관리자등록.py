from modules.common_import import *

from modules.PyQt.Tabs.영업mbo.dialog.dlg_default_input_setting import DefaultUserInputDialog

class TableView_영업mbo_관리자등록(Base_Table_View):
    pass

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_사용자등록 import TableModel_영업mbo_사용자등록
from modules.PyQt.Tabs.영업mbo.tables.mixin_model_입력 import Mixin_Model_입력
class TableModel_영업mbo_관리자등록(TableModel_영업mbo_사용자등록):

    filter_text = ''
    # lazy_attr_names = ['table_name', 'url', 'no_edit_columns_by_coding', 'edit_mode'] + [ 'filter_field', 'filter_value']
    _table_type_ = None

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.event_bus.subscribe(f"{self.table_name}:set_filter", self.on_set_filter)
        try:
            self.event_bus.unsubscribe(f"{self.table_name}:custom_editor_complete")
        except :
             pass
        
        #### kwargs 로 초기화 된 경우
        try:
            self.filter_field = self.kwargs['filter_field']
            self.filter_value = self.kwargs['filter_value']
            if self.filter_value >= 2:    ## 중복시
                self._table_type = 'Duplicated'
            elif self.filter_value == 1:
                self._table_type = 'Normal'
            elif self.filter_value == 0:
                self._table_type = 'Empty'
            else:
                logger.error(f"{self.__class__.__name__} : on_all_lazy_attr_ready : filter_value is not valid")
                return
            #### table_type 별로 구독함
            self.event_bus.subscribe(f"{self.table_name}:{self._table_type}:custom_editor_complete", self.on_custom_editor_complete)
        except Exception as e:
            logger.error(f"{self.__class__.__name__} : on_all_lazy_attr_ready : {e}")
            logger.error(f"{self.__class__.__name__} : on_all_lazy_attr_ready : {traceback.format_exc()}")
            raise ValueError(f"{self.__class__.__name__} : on_all_lazy_attr_ready : {e}")
   
    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
        if self._table_type == 'Duplicated':
            """ 모든 table data 저장함"""
            changed_rows =  list(self.map_id_obj.values())
            delete_rows = [row for row in changed_rows if not row['is_선택']]
            _text = f"""
                <b>대상 Row 수:</b> <span style='color:blue;'>{len(changed_rows)}</span><br>
                <b>※ 주의:</b> <span style='color:red;'>is_선택 미체크된 중복 데이터</span> 
                <span style='color:gray;'>(총 {len(delete_rows)}건)</span>은 <b>삭제</b>됩니다.<br>
                저장된 Row는 <b>"정상 보기"</b> 탭으로 이동됩니다.<br><br>
                정말 <b>저장</b>하시겠습니까?
            """
            if not Utils.QMsg_question(None, title="모든 데이터를 저장하시겠습니까?", text=_text):
                return
        elif self._table_type == 'Empty':
            total_rows = list(self.map_id_obj.values())
            changed_rows = [row for row in total_rows 
                            if row['is_선택'] and all ( [bool(row['고객사']), bool(row['구분']), bool(row['기여도']), bool(row['담당자_fk']) ] ) ]
            _text = f"""
                <b>총 Row 수:</b> <span style='color:blue;'>{len(total_rows)}</span><br>
                <b>저장 대상 Row 수:</b> <span style='color:green;'>{len(changed_rows)}</span><br><br>
                <span style='color:red;'>※ 고객사, 구분, 기여도, 담당자</span>가 모두 입력되어야 저장됩니다.<br>
                저장된 Row는 <b>"정상 보기"</b> 탭으로 이동됩니다.<br><br>
                <b>저장 하시겠습니까?</b>
            """
            if not Utils.QMsg_question(None, title="모든 데이터를 저장하시겠습니까?", text=_text):
                return

        else:
            changed_rows = [model_obj for original_obj, model_obj in
                         zip( self.api_datas, list(self.map_id_obj.values())) if model_obj != original_obj ]
        logger.info(f"on_api_send_By_Row : {changed_rows}")
        if changed_rows:
            url = f"{self.url}batch_post/".replace('//', '/')
            _isok, _json = APP.API.post(url= url,  data={'datas': json.dumps(changed_rows, ensure_ascii=False)})
            if _isok:
                self.event_bus.publish(f"{self.table_name}:datas_changed", _json)
                Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
            else:
                Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")

    def on_api_datas_received(self, api_datas:list[dict]):
        """ ovrride : gbus subscribe 된 api_datas 받아오면 호출되는 함수 """
        copyed_api_datas = copy.deepcopy(api_datas)
        match self._table_type:
            case 'Duplicated':
                filtered_api_datas = [data for data in copyed_api_datas if data[self.filter_field] >= self.filter_value]
            case 'Normal':
                filtered_api_datas = [data for data in copyed_api_datas if data[self.filter_field] == self.filter_value]
            case 'Empty':
                filtered_api_datas = [data for data in copyed_api_datas if data[self.filter_field] == self.filter_value]
            case _:
                logger.error(f"{self.__class__.__name__} : on_api_datas_received : _table_type is not valid")
                raise ValueError(f"{self.__class__.__name__} : on_api_datas_received : _table_type is not valid")
        super().on_api_datas_received(filtered_api_datas)


    def unsubscribe_gbus(self):
        super().unsubscribe_gbus()
        if self._table_type is not None and self._table_type != '':
            self.event_bus.unsubscribe( f"{self.table_name}:{self._table_type}:custom_editor_complete", self.on_custom_editor_complete )

    def on_custom_editor_complete(self, data:dict):
        """ Custom editor delegate에서 완료 후 들어오는 값을 반영 """
        print (f"on_custom_editor_complete : {data}")
        index = data.get('index')
        value = data.get('value')
        attr_name = self.get_field_name_by_index(index)
        if attr_name == '담당자_fk':
            self._data[index.row()]['담당자_fk'] = value['id']
            self._data[index.row()]['담당자'] = value['user_성명']
            self._data[index.row()]['부서'] = value['MBO_표시명_부서']
            start_index = self.index( index.row(), 0)
            end_index = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index, [Qt.DisplayRole, Qt.CheckStateRole])
            return True

        return super().on_custom_editor_complete(data)

    
    def setData(self, index:QModelIndex, value:Any, role:int) -> bool:
        # print( "setData: ", index, value, role, role == Qt.CheckStateRole and self.is_check_column_no(index.column()))
        if role == Qt.CheckStateRole and self.is_check_column_no(index.column()):
            is_checked = value == Qt.CheckState.Checked
            obj = self._data[index.row()]
            obj['is_선택'] = is_checked
            if not (hasattr(self, '_table_type') or self._table_type is not None):
                raise ValueError(f"{self.__class__.__name__} : setData : _table_type is not set")

            # ✅ Duplicated 테이블일 경우 기존 선택 해제
            if self._table_type == 'Duplicated' and is_checked:
                target_fk = self._data[index.row()]['신규현장_fk']
                for i, row in enumerate(self._data):
                    신규현장_fk = row['신규현장_fk']
                    is_선택 = row['is_선택']
                    if i != index.row() and 신규현장_fk == target_fk and is_선택:
                        row['is_선택'] = False
                        start_index = self.index(i, 0)
                        end_index = self.index(i, self.columnCount() - 1)
                        self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole])


        return super().setData(index, value, role)
            # self._data[index.row()]['is_선택'] = is_checked

 

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_사용자등록 import TableDelegate_영업mbo_사용자등록
class TableDelegate_영업mbo_관리자등록(TableDelegate_영업mbo_사용자등록 ):

    def custom_editor_handler(self, 
                              display_name:str, 
                              editor_class:callable, 
                              event: QEvent, 
                              model: TableModel_영업mbo_관리자등록, 
                              option: QStyleOptionViewItem, 
                              index: QModelIndex) -> bool:
        field_name = model.get_attrName_from_display(display_name)
        if field_name in self.custom_editor_info :
            match field_name:
                case '담당자_fk':                                     
                    ### 💡 3개 table사용으로 channelName에 _table_type_ 추가함 => model subscribe도 변경해야 함.
                    editor = editor_class(option.widget,                                         
                                        on_complete_channelName=f"{self.table_name}:{model._table_type}:custom_editor_complete",
                                        index=index,
                                        data = INFO.MBO_사용자,
                                        )
                    editor.exec()
                    return True
                case '고객사'|'구분'|'기여도':
                    editor = editor_class(option.widget,                                         
                                        on_complete_channelName=f"{self.table_name}:{model._table_type}:custom_editor_complete",
                                        index=index,
                                        _list = self.MAP_DisplayName_to_list[display_name],
                                        title=f"{display_name} 선택"
                                        )
                    editor.exec()
        
        return False





class Wid_table_영업mbo_관리자등록( Wid_table_Base_for_stacked ):

    @property
    def map_index_to_widget(self):
        if not hasattr(self, 'widget_menu'):
            self._create_widget_menu()
            self.lb_menu_title.setText('관리자등록')
        return {
            1: self.widget_menu
        }
    
    @property
    def map_pb_to_generate_info(self):
        print (self.kwargs)
        print (self.kwargs['filter_field'])
        print (self.kwargs['filter_value'])
        print (self.kwargs['filter_field'] == '사용자등록수')
        print (self.kwargs['filter_value'] == 0)
        print (self.kwargs['filter_field'] == '사용자등록수' and self.kwargs['filter_value'] == 0)
        if self.kwargs['filter_field'] == '사용자등록수' and self.kwargs['filter_value'] == 0:
            return {
                'PB_Default_Setting': {'title': '기본 입력 설정', 
                                    'tooltip': '기본 입력 설정',
                                    'slot' : lambda: self.model.on_default_input_setting_request(True) ,
                                    'disable_not_selected': False
                                   },
            }

    def setup_table(self):
        print ( self.kwargs )
        self.view = TableView_영업mbo_관리자등록(self)
        self.model = TableModel_영업mbo_관리자등록(self.view, **self.kwargs)
        self.delegate = TableDelegate_영업mbo_관리자등록(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()


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

