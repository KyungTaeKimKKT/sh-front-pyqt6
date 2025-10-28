from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.table.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table.Base_Delegate import Base_Delegate


from modules.PyQt.Tabs.영업mbo.dialog.dlg_default_input_setting import DefaultUserInputDialog
import json, os, io, copy
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()



class TableView_영업mbo_사용자등록(Base_Table_View):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_no_config_initial = False #### 💡 초기 tableconfig 있음

from modules.PyQt.Tabs.영업mbo.tables.mixin_model_입력 import Mixin_Model_입력

class TableModel_영업mbo_사용자등록(Mixin_Model_입력, Base_Table_Model):

    _unselected_rows = set()
    _selected_rows = set()
    
    db_field_default = {'id':None, '고객사':None, '구분':None, '기여도':None, '비고':None, '등록자':None, '등록자_snapshot':None, 'by_admin':False, 'is_선택':False}

    default_고객사 = '현대EL'
    default_구분 = 'MOD'
    default_기여도 = '3'

    map_선택_bg_color = {
        True: QColor(255, 255, 150),
        False: QColor(255, 255, 255),
    }
    map_선택_font_color = {
        True: QColor(0, 0, 0),   ### black
        False: QColor(128, 128, 128),  ### gray
    }    

    filter_text = ''

   
    def on_api_datas_received(self, api_datas:list[dict]):
        """ ovrride : gbus subscribe 된 api_datas 받아오면 호출되는 함수 """
        super().on_api_datas_received(api_datas)
        
        self._data_total = copy.deepcopy(api_datas)     # 사용자가 수정 가능한 전체 데이터
        self._unselected_rows.clear()
        self._selected_rows.clear()
        for row_index, rowDict in enumerate(self._data):
            ### 즉, db 저장된 데이터만 유효함.
            is_checked = rowDict['is_선택']
            if is_checked:
                self._selected_rows.add(row_index)
            else:
                self._unselected_rows.add(row_index)

        self.map_id_obj = { obj['id']: obj for obj in copy.deepcopy(api_datas) }

       #### 여기에 필터링 추가
        self.on_set_filter(self.filter_text)   

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.event_bus.subscribe(f"{self.table_name}:default_input_setting_reques", self.on_default_input_setting_request)
        self.event_bus.subscribe(f"{self.table_name}:set_filter", self.on_set_filter)


   
    def data(self, index:QModelIndex, role:int) -> Any:
        if role == Qt.CheckStateRole and self.is_check_column_no(index.column()):
        # int로 변환해서 명시적으로 체크 상태 반환
            return Qt.Checked if self._is_row_선택(index.row()) else Qt.Unchecked
        
        return super().data(index, role)
    
    def _role_background(self, row:int, col:int) -> QColor:
        return self.map_선택_bg_color[self._is_row_선택(row)]

    def _role_font(self, row:int, col:int) -> QFont:
        font = QFont()
        if self._is_row_선택(row):
            font.setBold(True)
            return font

        
    def _role_foreground(self, row:int, col:int) -> QColor:
        return self.map_선택_font_color[self._is_row_선택(row)]
    
    def _role_tooltip(self, row:int, col:int) -> str:
        if self._is_editable( self.index_from_row_col(row, col) ):
            return '편집가능합니다.'
        else:
            return '편집X'

   
    
    def setData(self, index:QModelIndex, value:Any, role:int) -> bool:
        print( "setData: ", index, value, role, role == Qt.CheckStateRole and self.is_check_column_no(index.column()))
        if role == Qt.CheckStateRole and self.is_check_column_no(index.column()):
            is_checked = value == Qt.CheckState.Checked
            obj = self._data[index.row()]
            obj['is_선택'] = is_checked
            try:
                if is_checked:
                    if self.is_db_id(index.row()):
                        obj['고객사'] = self._original_data[index.row()]['고객사']
                        obj['구분'] = self._original_data[index.row()]['구분']
                        obj['기여도'] = self._original_data[index.row()]['기여도']
                    else:
                        obj['고객사'] = self.default_고객사 #self.get_고객사_name(self._data[index.row()][현장명_colNo])
                        obj['구분'] = self.default_구분
                        obj['기여도'] = self.default_기여도
                    self._selected_rows.add(index.row())
                    self._unselected_rows.discard(index.row())
                else:
                    obj['고객사'] = ''
                    obj['구분'] = ''
                    obj['기여도'] = None
                    self._selected_rows.discard(index.row())
                    self._unselected_rows.add(index.row())

                self.map_id_obj[obj['id']] = obj
                self._data[index.row()] = obj

            except Exception as e:
                logger.error(f"setData 오류: {e}")
                logger.error(f"{traceback.format_exc()}")

            start_index = self.index(index.row(), 0)
            end_index = self.index(index.row(), self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.CheckStateRole])
            return True
                
        return super().setData(index, value, role)

   
    def flags(self, index:QModelIndex) -> Qt.ItemFlags:
        if self.is_check_column_no(index.column()):            
            return Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        
        return super().flags(index)
    
    def _is_editable(self, index:QModelIndex) -> bool:
        """ override : 편집 가능 여부 반환 """

        if self.is_check_column_no(index.column()):
            return True
        
        if self._is_row_선택(index.row()):
            pass    ### pass하여 뒤에서 처리함
        else:
            return False
        return super()._is_editable(index)
    


    def on_api_send_By_Row(self):
        """ 행 단위 저장 
            Base_Table_Model 은 파일 첨부 없이 저장함.
            여기서는 파일 첨부 처리함.
        """
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



class TableDelegate_영업mbo_사용자등록(Base_Delegate):
    고객사_list = ['현대EL', 'OTIS', 'TKE', '기타']
    구분_list = ['MOD', 'NE', '비정규']
    기여도_list = ['1', '2', '3', '4', '5']

    MAP_DisplayName_to_list = {
        '고객사': 고객사_list,
        '구분': 구분_list,
        '기여도': 기여도_list,
    }

    def editorEvent(self, event, model, option, index):
        if index.flags() & Qt.ItemIsUserCheckable and index.data(Qt.CheckStateRole) is not None:
            if event.type() in (QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick):
                new_val = Qt.Unchecked if index.data(Qt.CheckStateRole) == Qt.Checked else Qt.Checked
                model.setData(index, new_val, Qt.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)


    def custom_editor_handler(self, display_name:str, editor_class:callable, event: QEvent, model: TableModel_영업mbo_사용자등록, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        field_name = model.get_attrName_from_display(display_name)
        if field_name in self.custom_editor_info:
            match field_name:
                case '고객사'|'구분'|'기여도':
                    editor = editor_class(option.widget,                                         
                                        on_complete_channelName=f"{self.table_name}:custom_editor_complete",
                                        index=index,
                                        _list = self.MAP_DisplayName_to_list[display_name],
                                        title=f"{display_name} 선택"
                                        )
                    editor.exec()


                case _:
                    logger.error(f"custom_editor_handler: {display_name} 에디터 클래스가 없읍니다.")
                    return False
                
            return True
        return False

       

class Wid_table_영업mbo_사용자등록( Wid_table_Base_for_stacked ):
    """ 1. 기본입력 설정과 저장이 이 widget내에 위치"""
    

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_영업mbo_사용자등록(self)
        self.model = TableModel_영업mbo_사용자등록(self.view)
        self.delegate = TableDelegate_영업mbo_사용자등록(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

        self.view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        # self.view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()

    def init_attributes(self):
        super().init_attributes()

    def disable_row_add_button(self):
        super().disable_row_add_button()
 

    def init_ui(self):
        """ override"""
        super().init_ui()

        self.wid_header.hide_all()
        self.label_selected_현장 = QLabel('선택 현장')
        self.wid_header.layout().addWidget(self.label_selected_현장)
        self.label_all_현장 = QLabel(' / 전체 현장')
        self.wid_header.layout().addWidget(self.label_all_현장)

        #### 기본 self.wid_header 제거 및 bbtn(기본입력설정 및 저장 ) 추가
        self.btn_container = QWidget()
        btn_h_layout = QHBoxLayout()
        btn_h_layout.addStretch()        
        self.pb_config_input_setting = QPushButton('기본 입력 설정')
        btn_h_layout.addWidget(self.pb_config_input_setting)
        self.pb_save = QPushButton('저장')        
        btn_h_layout.addWidget(self.pb_save)    
        self.btn_container.setLayout(btn_h_layout)
        self.wid_header.layout().addWidget(self.btn_container)

        self.pb_config_input_setting.clicked.connect(lambda:self.model.on_default_input_setting_request(True))
        self.pb_save.clicked.connect(self.model.on_api_send_By_Row)

    def subscribe_gbus(self):
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        # if hasattr(self, 'table_name') and self.table_name:
        self.event_bus.subscribe( f"{self.table_name}:datas_changed", 
                                 lambda datas: QTimer.singleShot(100, lambda: self.update_label_현장_count()) )

    def update_label_현장_count(self):
        self.label_selected_현장.setText(f" db에 저장된 결과입니다(변경시 꼭 저장하길 바랍니다) =>  선택된 현장 : {self.model.선택된_현장} 개 ")
        self.label_all_현장.setText(f" / 전체 현장 : {self.model.전체_현장} 개 ")
            
    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.

            
    def connect_signals(self):
        """ wid_header의 signal 연결인데, 여기서는 불필요 """
        super().connect_signals()
        


    def run(self):
        if not hasattr(self, 'url') and not self.url:
            logger.error(f"url이 없읍니다.")
        else:
            _isok, _json = APP.API.getlist( self.url + 'default-user-input/')
            logger.debug(f"run: get_default_user_input: {_isok}, {_json}")
            if _isok:
                logger.debug(f"get_default_user_input: {_json}")
                self.model.default_고객사 = _json.get('고객사', '현대EL')
                self.model.default_구분 = _json.get('구분', 'MOD')
                self.model.default_기여도 = _json.get('기여도', '3')
            else:
                logger.error(f"run 오류: {_json}")

        if not ( hasattr(self, 'table_name') and self.table_name ):
            logger.error(f"table_name이 없읍니다.")

        super().run()
