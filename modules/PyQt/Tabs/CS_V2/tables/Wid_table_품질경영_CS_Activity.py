from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.table.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table.Base_Delegate import Base_Delegate

from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
from modules.PyQt.compoent_v2.custom_상속.custom_listwidget import Custom_ListWidget
from modules.PyQt.Tabs.영업mbo.dialog.dlg_default_input_setting import DefaultUserInputDialog
import json, os, io, copy
import platform
from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


from modules.PyQt.Tabs.품질경영.tables.Wid_table_품질경영_CS관리 import TableModel_품질경영_CS관리, TableView_품질경영_CS관리, TableDelegate_품질경영_CS관리, Wid_table_품질경영_CS관리


class TableView_품질경영_CS_Activity(TableView_품질경영_CS관리):
    pass
    # set_row_span_list = [
    #     ('일자', [] ),
    # ]

    # def _apply_spans(self):
    #     """ span 적용 : trigger 는 setModel 시점에 연결됨 """
    #     self.clear_all_span()
    #     if hasattr( self, 'set_row_span_list') and self.set_row_span_list:            
    #         for colName, subNames in self.set_row_span_list:
    #             self.setRowSpan(colName, subNames)

    # def __init__(self, parent=None):
    #     super().__init__(parent)
    #     self.is_no_config_initial = False #### 💡 초기 tableconfig 있음
    #     self.v_header_menu_by_coding = [
    #         {   
    #             'v_header': {
    #                 'name' : 'add_row',
    #                 'slot_func' : self.on_add_claim_project,
    #                 'title': '클레임 프로젝트 추가',
    #                 'tooltip': '클레임 프로젝트 추가합니다',
    #                 'visible': True,
    #             },
    #         },
    #         {   
    #             'v_header': {
    #                 'name' : 'delete_row',
    #                 'slot_func' : self.on_delete_claim_project,
    #                 'title': '클레임 프로젝트 삭제',
    #                 'tooltip': '클레임 프로젝트 삭제합니다',
    #                 'visible': True,
    #             },
    #         },
    #     ]
    #     self.cell_menu_by_coding = [
    #         {
    #             'col_name': 'claim_file_수',
    #             'menus': [
    #                 {   
    #                     'name' : 'claim_file_view',
    #                     'slot_func' : self.on_file_view,
    #                     'title': '클레임 파일 보기',
    #                     'tooltip': '클레임 파일을 보여줍니다.',
    #                     'visible': True,
    #                 },
    #                 {   
    #                     'name' : 'claim_file_download',
    #                     'slot_func' : self.on_file_download,
    #                     'title': '클레임 파일 다운로드',
    #                     'tooltip': '클레임 파일을 다운로드합니다.',
    #                     'visible': True,
    #                 },
    #             ]
    #         },
    #         {
    #             'col_name': 'activity_file_수',
    #             'menus': [
    #                 {   
    #                     'name' : 'activity_file_view',
    #                     'slot_func' : self.on_file_view,
    #                     'title': '활동 파일 보기',
    #                     'tooltip': '활동 파일을 보여줍니다.',
    #                     'visible': True,
    #                 },
    #                 {   
    #                     'name' : 'activity_file_download',
    #                     'slot_func' : self.on_file_download,
    #                     'title': '활동 파일 다운로드',
    #                     'tooltip': '활동 파일을 다운로드합니다.',
    #                     'visible': True,
    #                 },
    #             ]
    #         }
    #     ]

    
    # def on_add_claim_project(self, rowNo:int):
    #     logger.info(f"on_add_claim_project: {rowNo}")
    #     self.model().request_add_claim_project(rowNo)

    # def on_delete_claim_project(self, rowNo:int):
    #     logger.info(f"on_delete_claim_project: {rowNo}")
    #     self.model().request_delete_claim_project(rowNo)

    # def show_v_header_context_menu(self, position):
    #     """ override : edit 불가능 row는 메뉴 생성 안함."""
    #     selected_row = self.currentIndex().row()
    #     if self.model()._is_menu_visible(selected_row):
    #         super().show_v_header_context_menu(position)
    #     else:
    #         logger.info(f"show_v_header_context_menu: {selected_row} is not editable")

    # def on_file_view(self, rowNo:int, colNo:int):
    #     logger.info(f"on_file_view: {rowNo}, {colNo}")
    #     self.model().request_file_view(rowNo, colNo)

    # def on_file_download(self, rowNo:int, colNo:int):
    #     logger.info(f"on_file_download: {rowNo}, {colNo}")
    #     self.model().request_file_download(rowNo, colNo)



class TableModel_품질경영_CS_Activity(TableModel_품질경영_CS관리):
    pass

    # def on_lazy_attr_ready(self, attr_name:str, attr_value:Any):
    #     super().on_lazy_attr_ready(attr_name, attr_value)

    #     if attr_name == 'table_name':
    #         self.event_bus.subscribe(f"{self.table_name}:request_claim_open", self.on_request_claim_open)

    # def request_claim_open(self, claim_id:int):
    #     logger.info(f"request_claim_open: {claim_id}")
    #     self.event_bus.publish(f"{self.table_name}:request_claim_open", claim_id)


    # def on_request_claim_open(self, selected_rows:list[dict]):
    #     logger.info(f"on_request_claim_open: {selected_rows}")
    #     try:
    #         for selected_row in selected_rows:
    #             claim_id = self.get_column_No_by_field_name('id')
    #             index = self._data.index(selected_row)
    #             _isok, _json = APP.API.Send(self.url, { 'id': claim_id }, { 'id': claim_id , '진행현황':'Open'})
    #             if _isok:
    #                 self._data.remove(selected_row)
    #                 self.beginRemoveRows(QModelIndex(), index, index)
    #                 self.endRemoveRows()
    #                 self.dataChanged.emit(self.index(index, 0), self.index(index, self.columnCount() - 1), [Qt.DisplayRole])
    #                 #### empty
    #                 if not self._data:
    #                     self.event_bus.publish(f"{self.table_name}:empty_data", True)
    #             else:
    #                 Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")

    #             self.request_claim_open(claim_id)
    #     except Exception as e:
    #         logger.error(f"on_request_claim_open: {e}")
    #         logger.error(f"{traceback.format_exc()}")
    #         Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")





class TableDelegate_품질경영_CS_Activity(TableDelegate_품질경영_CS관리):
    pass

    # def custom_editor_handler(self, display_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
    #     return False
    #     logger.debug(f"custom_editor_handler: {display_name}, {editor_class}, {event}, {model}, {option}, {index}")
    #     logger.debug(f"self.custom_editor_info: {self.custom_editor_info}")
    #     field_name = model.get_field_name_by_display_name(display_name)
    #     if field_name in self.custom_editor_info:
    #         match field_name:
    #             case '고객사'|'구분'|'기여도':
    #                 editor = editor_class(option.widget,                                         
    #                                     on_complete_channelName=f"{self.table_name}:custom_editor_complete",
    #                                     index=index,
    #                                     _list = self.MAP_DisplayName_to_list[display_name],
    #                                     title=f"{display_name} 선택"
    #                                     )
    #                 editor.exec_()


    #             case _:
    #                 logger.error(f"custom_editor_handler: {display_name} 에디터 클래스가 없읍니다.")
    #                 return False
                
    #         return True
    #     return False

        
class Wid_table_품질경영_CS_Activity( Wid_table_품질경영_CS관리 ):
    no_edit_columns_by_coding = 'all'
    edit_mode = 'None'



