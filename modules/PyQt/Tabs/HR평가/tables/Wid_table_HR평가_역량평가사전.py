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



class TableView_HR평가_역량평가사전(Base_Table_View):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_no_config_initial = False #### 💡 초기 tableconfig 있음
        self.v_header_menu_by_coding = [
            {                   
                'v_header': {
                    'name' : 'add_row',
                    'slot_func' : self.on_add_row,
                    'title': '역량평가 추가',
                    'tooltip': '역량평가 추가합니다',
                    'visible': True,
                },
            },
            {                   
                'v_header': {
                    'name' : 'delete_row',
                    'slot_func' : self.on_delete_row,
                    'title': '역량평가 삭제',
                    'tooltip': '역량평가 삭제합니다',
                    'visible': True,
                },
            },
        ]
        self.cell_menu_by_coding = [
        ]

    
    def on_add_row(self, rowNo:int):
        logger.info(f"on_add_row: {rowNo}")
        self.model().request_add_row(rowNo)

    def on_delete_row(self, rowNo:int):
        logger.info(f"on_delete_row: {rowNo}")
        self.model().request_delete_row(rowNo)


    def on_file_upload(self, rowNo:int, colNo:int):
        logger.info(f"on_file_upload: {rowNo}, {colNo}")
        self.model().request_file_upload(rowNo, colNo)

    def on_file_download(self, rowNo:int, colNo:int):
        logger.info(f"on_file_download: {rowNo}, {colNo}")
        self.model().request_file_download(rowNo, colNo)



class TableModel_HR평가_역량평가사전(Base_Table_Model):

    def request_add_row(self, rowNo:int):

        logger.info(f"request_add_claim_project: {rowNo}")
        copyed_row = copy.deepcopy( self._data[rowNo])
      
        id_colNo = self.get_column_No_by_field_name('id')

        for idx, value in enumerate(copyed_row):
            if idx == id_colNo: 
                copyed_row[idx] = -1
            else:
                copyed_row[idx] = None

        # View에 삽입 알림 시작
        self.beginInsertRows(QModelIndex(), rowNo, rowNo)
        self._data.insert(rowNo, copyed_row)    
        self.endInsertRows()
        self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])

    def request_delete_row(self, rowNo:int):
        logger.info(f"request_delete_row: {rowNo}")
        dlg_res_button = Utils.generate_QMsg_question(
            None, 
            title="역량평가 삭제", 
            text="역량평가를 삭제하시겠습니까?"
            )
        if dlg_res_button != QMessageBox.StandardButton.Ok :
            return

        self.beginRemoveRows(QModelIndex(), rowNo, rowNo)
        try:
            if self._data[rowNo][self.get_column_No_by_field_name('id')] > 0:
                _isOk = APP.API.delete(self.url + f"{self._data[rowNo][self.get_column_No_by_field_name('id')]}")
                if _isOk:
                    self.event_bus.publish(f"{self.table_name}:data_deleted", True)
                    Utils.generate_QMsg_Information(
                        None, 
                        title="역량평가 삭제", 
                        text="역량평가 삭제 성공", 
                        autoClose=1000
                        )
                    self._data.pop(rowNo)

                    if not self._data:
                        self.event_bus.publish(f"{self.table_name}:empty_data", True)
                else:
                    raise Exception(f"역량평가 삭제 실패: {_isOk}")
            else:
                self._data.pop(rowNo)
            self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])
        except Exception as e:
            logger.error(f"request_delete_row: {e}")
            logger.error(f"{traceback.format_exc()}")
            Utils.generate_QMsg_critical(None, title="역량평가 삭제", text="역량평가 삭제 실패")
        finally:
            self.endRemoveRows()
            return

    def request_file_upload(self, rowNo:int, colNo:int):
        file_colNo = self.get_column_No_by_field_name('file')
        if colNo == file_colNo:
            file_path = Utils._getOpenFileName_only1( self.parent() )
            if file_path:
                self._data[rowNo][file_colNo] = file_path
                self.dataChanged.emit(self.index(rowNo, file_colNo), self.index(rowNo, file_colNo), [Qt.DisplayRole])


    def request_file_download(self, rowNo:int, colNo:int):
        file_colNo = self.get_column_No_by_field_name('file')
        if colNo == file_colNo:
            urls = self._data[rowNo][self.get_column_No_by_field_name('file')]
            self._download_multiple_files([urls])
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
        logger.info(f"on_api_send_By_Row : {self._modified_rows}", extra={'action': f"{self.table_name}:on_api_send_By_Row"})
        if self._modified_rows:
            bulk_data = []
            for row in list(self._modified_rows):
                send_data = self.get_row_data(row)
                send_file = None
                if 'file' in send_data:
                    file_path = send_data.pop('file')
                    if not file_path.startswith('http'):
                        send_file = {'file': open(file_path, 'rb')}

                _isok, _json = APP.API.Send(url= self.url,  dataObj={'id':send_data.pop('id') }, sendData=send_data, sendFiles=send_file)
                if _isok:
                    logger.info(f"API 호출 성공:  {type(_json)}, {_json}")
                    self.update_api_response( _json, row)
                    self.clear_modified_rows(list(self._modified_rows))
                    logger.info(f"API 호출 성공: {_json}")
                    Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
                else:
                    Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
	
       
   

class TableDelegate_HR평가_역량평가사전(Base_Delegate):
    pass
    # map_colNo_to_field_name = {}

    # def setEditorData(self, editor:QWidget, index:QModelIndex):
    #     logger.debug(f"setEditorData: {editor}, {index}")
    #     model : TableModel_HR평가_역량평가사전 = index.model()
    #     rowNo, colNo = index.row(), index.column()
    #     if self.OS_colNo is None:
    #         self.OS_colNo = model.get_column_No_by_field_name('OS')
    #     if self.종류_colNo is None:
    #         self.종류_colNo = model.get_column_No_by_field_name('종류')
    #     if not self.map_colNo_to_field_name:
    #         self.map_colNo_to_field_name = {self.OS_colNo: 'OS', self.종류_colNo: '종류'}

    #     if self.map_colNo_to_field_name and colNo in self.map_colNo_to_field_name:
    #         if isinstance(editor, QComboBox):
    #             choice_list = model.get_choice_list(self.map_colNo_to_field_name[colNo])
    #             map_value_to_display = {item['value']: item['display'] for item in choice_list}
    #             editor.addItems( [item['display'] for item in choice_list] )
    #             value = model.data(index, Qt.ItemDataRole.EditRole)
    #             editor.setCurrentText(map_value_to_display.get(value, value))
    #             return 

    #     super().setEditorData(editor, index)

    # def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
    #     rowNo, colNo = index.row(), index.column()

    #     if self.map_colNo_to_field_name and colNo in self.map_colNo_to_field_name:
    #         choice_list = model.get_choice_list(self.map_colNo_to_field_name[colNo])
    #         map_display_to_value = {item['display']: item['value'] for item in choice_list}
    #         model.setData(index, map_display_to_value.get(editor.currentText(), model._data[rowNo][colNo]), Qt.ItemDataRole.EditRole)
    #         return 

    #     super().setModelData(editor, model, index)


    # def custom_editor_handler(self, display_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
    #     return False
    #     logger.debug(f"custom_editor_handler: {display_name}, {editor_class}, {event}, {model}, {option}, {index}")
    #     logger.debug(f"self.custom_editor_info: {self.custom_editor_info}")
    #     field_name = model.get_field_name_by_display_name(display_name)
    #     if field_name in self.custom_editor_info:
    #         match field_name:
    #             case 'OS'|'종류':
    #                 editor = editor_class(option.widget,                                         
    #                                     data = index.data(),
    #                                     choice_list = model.get_choice_list(field_name),                                        
    #                                     )
    #                 return True

    #             case _:
    #                 logger.error(f"custom_editor_handler: {display_name} 에디터 클래스가 없읍니다.")
    #                 return False
                
    #         return True
    #     return False


from modules.PyQt.compoent_v2.widget_manager import WidManager  

class Wid_table_HR평가_역량평가사전( Wid_table_Base_for_stacked ):

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_HR평가_역량평가사전(self)
        self.model = TableModel_HR평가_역량평가사전(self.view)
        self.delegate = TableDelegate_HR평가_역량평가사전(self.view)
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
        if not ( hasattr(self, 'url') and self.url):
            logger.error(f"url이 없읍니다.")

        if not ( hasattr(self, 'table_name') and self.table_name):
            logger.error(f"table_name이 없읍니다.")

        super().run()

