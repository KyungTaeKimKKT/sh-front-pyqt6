from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import inspect
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table.Base_Delegate import Base_Delegate

from modules.PyQt.Tabs.plugins.ui.Wid_config_mode import Wid_Config_Mode
from modules.PyQt.Tabs.plugins.ui.Wid_header import Wid_Header

from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode
from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton

import json, os
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

       

class Wid_table_Base(QWidget):
    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent, **kwargs)
        self.event_bus = event_bus
        self.edit_mode = 'row' ### 'row' or 'cell'
        self.selected_rows:list[dict] = None
        self.selected_row:dict = None

        self.model:Optional[Base_Table_Model] = None
        self.view:Optional[Base_Table_View] = None
        self.delegate:Optional[Base_Delegate] = None

        self.is_api_datas_applied = False

    def showEvent(self, event:QShowEvent):
        super().showEvent(event)
        logger.debug(f" {self.__class__.__name__} showEvent")
        print(f" {self.__class__.__name__} showEvent")
        self.render_emptyLabel_table()

    def hideEvent(self, event:QHideEvent):
        super().hideEvent(event)
        logger.debug(f" {self.__class__.__name__} hideEvent")
        print(f" {self.__class__.__name__} hideEvent")
        self.label_table_empty.setVisible(False)
        self.PB_add_row.setVisible(False)
        self.view.setVisible(False)
        self.wid_header.setVisible(False)


    def init_by_parent(self):
        """ 이 method 는 상속 받은 class에서 필히 호출함
            왜냐면 scope 문제, base에서 불필요한 초기화 제한.            
        """
        raise NotImplementedError("init__by_parent 메서드는 상속 받은 클래스에서 구현해야 합니다.")


    def resolve_calling_context(self):
        """자식 클래스가 init 호출한 모듈의 globals / module name 추출"""
        frame = inspect.currentframe()
        logger.debug(f"frame: {frame}")
        caller_frame = frame.f_back
        logger.debug(f"caller_frame: {caller_frame}")
        self.calling_globals = caller_frame.f_globals
        logger.debug(f"self.calling_globals: {self.calling_globals}")
        self.calling_module_name = self.calling_globals.get('__name__')
        logger.debug(f"self.calling_module_name: {self.calling_module_name}")
        return self.calling_globals, self.calling_module_name

    def init_attributes(self):
        self.is_tableConfigMode = False
        self.update_time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.api_datas:Optional[list[dict]] = None
        self.model_datas:Optional[list[list]] = None
        self.table_header:Optional[list[str]] = None
        self.prev_api_datas:Optional[list[dict]] = None
        self.model_datas:Optional[list[list]] = None

        if hasattr(self, 'kwargs'):
            for key, value in self.kwargs.items():
                setattr(self, key, value)


    def init_ui(self):
        self.layout = QVBoxLayout()

        self.label_table_empty = QLabel('조회된 데이터가 없읍니다.', self)
        self.label_table_empty.setAlignment(Qt.AlignCenter)        
        self.label_table_empty.setStyleSheet("font-weight: bold; background-color: #f0f0f0;")
        self.PB_add_row = QPushButton('신규TABLE ROW 추가', self)
        self.layout.addWidget(self.label_table_empty)
        self.layout.addWidget(self.PB_add_row)

        self.wid_header = Wid_Header(self)
        self.wid_config = Wid_Config_Mode(self)
        self.layout.addWidget(self.wid_header)
        self.layout.addWidget(self.wid_config)

        self.layout.addWidget(self.view)
        self.setLayout(self.layout)
        self.render_emptyLabel_table()

    def disable_row_add_button(self):
        self.PB_add_row.setVisible(False)

    
    def render_emptyLabel_table(self, is_datas:Optional[bool]=None):
        """ 배타적 view 노출 여부 설정 """
        is_datas = is_datas or self.model.is_datas()
        self.label_table_empty.setVisible( not is_datas )
        self.PB_add_row.setVisible( not is_datas )
        self.view.setVisible( is_datas )
        self.wid_header.setVisible( is_datas )

    def subscribe_gbus(self):
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
    def connect_signals(self):
        """ signal 연결 """
        self.view.signal_table_config_mode.connect( self.slot_table_config_mode )
        self.wid_header.edit_mode_changed.connect( lambda mode: self.model.set_edit_mode(mode) )
        self.wid_header.save_requested.connect( self.slot_api_send_By_Row )
        self.PB_add_row.clicked.connect( lambda: self.view.menu_handler.slot_v_header__add_row(0) )

        ### model data 변경시 slot_model_data_changed 호출
        self.model.user_data_changed.connect( self.slot_model_data_changed )
        self.view.signal_select_rows.connect( lambda rowList: self.set_selected_rows(rowList) )
        self.view.signal_select_row.connect( lambda rowDict: self.set_selected_row(rowDict) )
        self.delegate.commitEdit.connect( self.slot_api_send_By_Cell )

    def run(self):
        self.view.set_Table_name(self.objectName())
        self.model.set_Table_name(self.objectName())
        self.model.set_edit_mode(self.edit_mode)
        # self.view.setModel(self.model)
        self.view.run()
        self.delegate.run()

        # self.show()

    def slot_model_data_changed(self, is_datas:Optional[bool]=None):
        is_datas = is_datas or self.model.is_datas()
        self.render_emptyLabel_table(is_datas)
        self.wid_header.update_api_query_time()

    def slot_table_config_mode(self, is_config:bool):
        self.wid_config.setVisible(is_config)
        self.wid_header.setVisible(not is_config)
        self.wid_config.run()

    def gbus_timer_1min(self, time_str:str):
        """ 매 분:0초마다 호출되는 함수 """
        self.wid_header.update_api_query_gap(time_str)

    def slot_api_send_By_Row(self):
        """편집 모드: row 일 때 save button 클릭 시 호출되는 함수
           bulk with files 로 구현됨.
        """
        try:
            modified_data = self.model.get_modified_rows_data()
            logger.debug(f"modified_data: {modified_data}")
            
            # 데이터 준비
            data_list = []
            files_dict = {}
            
            for item in modified_data:
                item_rowNo = item.pop('rowNo', -1)  ### tableview에서 rowNo : int
                item_copy = item.copy()
                
                # 파일 객체 처리
                if 'files' in item_copy:
                    files = item_copy.pop('files')
                    if files:
                        # ID 필드 확인
                        item_id = item_copy.get('id') or item_copy.get('pk')
                        
                        for field_name, file_obj in files.items():
                            # 파일 키 생성 (ID가 있으면 ID_필드명, 없으면 new_필드명)
                            file_key = f"{item_id}_{field_name}" if item_id else f"new_{field_name}"
                            
                            # files 딕셔너리에 추가
                            file_name = os.path.basename(file_obj.name)
                            files_dict[file_key] = (file_name, file_obj, 'application/octet-stream')
                
                # 데이터 리스트에 추가
                data_list.append(item_copy)
            
            # 요청 데이터 준비
            data = {
                'datas': json.dumps(data_list, ensure_ascii=False)
            }
            
            logger.debug(f"data: {data}")
            logger.debug(f"files_dict: {files_dict}")
            # API 요청 보내기
            url = self.url + 'bulk_generate_with_files/'
            is_ok, response = APP.API.post(url, data, files_dict)
            
            # 파일 객체 닫기 (요청 후)
            for file_tuple in files_dict.values():
                try:
                    file_tuple[1].close()
                except:
                    pass
            
            if is_ok:
                self.model.update_api_response(response, rowNo=item_rowNo)
            else:
                logger.error(f"API 요청 실패: {response}")
                QMessageBox.warning(self, "저장 실패", "데이터 저장에 실패했읍니다. 로그를 확인하세요.")
        except Exception as e:
            logger.error(f"slot_api_send_By_Row 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def slot_api_send_By_Cell(self, editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, _sendData:dict , files:object):
        """ 편집 모드: cell일 때, delegate 에서 바로 emit 시, handle(호출)되는 함수 """

        if self.url:
            logger.debug(f"files: {files}")
            if files:
                # filename = files.pop('filename')
                # fieldname = files.pop('field_name')
                is_ok, _json = APP.API.Send( self.url, id_obj , {}, files )
            else:
                is_ok, _json = APP.API.Send( self.url, id_obj , _sendData )

            if is_ok:
                try:
                    logger.debug(f" cell update : index : {index} : value : {value}")
                    self.delegate.force_close_editor(editor, model, index, value)
                except Exception as e:
                    logger.error(f"에디터 종료 오류: {e}")
                    logger.error(f"{traceback.format_exc()}")
            else:
                logger.error(f"API 요청 실패: {_json}")
        else:
            logger.error(f"url이 없읍니다.")


    def clear_layout(self):
        """레이아웃 초기화"""
        try:
            if self.layout:
                Utils.deleteLayout(self.layout)
        except Exception as e:
            logger.error(f"레이아웃 초기화 중 오류 발생: {e}")

    ### apply method들은 run script 형태임
    def apply_api_datas(self, api_datas:list[dict]):
        """ api fectch worker 처리 후 호출되는 함수 """        
        self.set_api_datas(api_datas)
        self.compare_api_datas()

    def compare_api_datas(self):
        """ self.prev_api_datas 와 self.api_datas 비교 하여 render 함"""
        self.wid_header.update_api_query_time(self.update_time_str)
        self.model.clear_modified_rows()
        if self.prev_api_datas is None:
            self.model.apply_api_datas(self.api_datas)
            self.render_emptyLabel_table()
        else:
            if self.model.is_same_api_datas():                
                self.model.apply_api_datas(self.api_datas)
            else:
                self.model.apply_api_datas(self.prev_api_datas)
                self.wid_header.update_no_change_data()
        

    ### utils method
    def create_model_datas(self, api_datas:list[dict]) -> list[list]:
        """ api_datas를 model_datas로 변환 """
        if not api_datas:
            return []
        model_datas = []
        for obj in api_datas:
            model_datas.append(self.get_table_row_data(obj))
        self.set_model_datas(model_datas)
        self.model_datas = model_datas
        return model_datas
    
    def create_table_header_from_config(self ):
        """ table config 를 이용 생성"""
        pass

    def create_table_header_from_api_datas(self):
        """ api_datas를 이용 생성 """
        if self.api_datas and len(self.api_datas) > 0:
            return list(self.api_datas[0].keys())
        else:
            return []
        
    ####
    def get_selected_rows(self):
        return self.selected_rows
    
    def get_selected_row(self):
        return self.selected_row
    
   
    ####
        
    def get_table_row_data(self, obj:dict) -> list:
        """ obj를 table row data로 변환 """
        return [ obj.get(key, '') for key in self.get_table_header() ]


    #### setters
    def set_api_datas(self, api_datas:list[dict]):
        self.prev_api_datas = self.api_datas
        self.api_datas = api_datas

    def set_model_datas(self, model_datas:list[list]):
        self.prev_model_datas = self.model_datas
        self.model_datas = model_datas

    def set_update_time(self, time_str:Optional[str]=None):
        self.update_time_str = time_str or QDateTime.currentDateTime().toString("HH:mm:ss")

    def set_tableConfigMode(self, is_tableConfigMode:bool):
        self.is_tableConfigMode = is_tableConfigMode

    def set_is_no_config_initial(self, is_no_config_initial:bool=False):
        self.is_no_config_initial = is_no_config_initial
        self.view.set_is_no_config_initial(is_no_config_initial)

    def set_row_span(self, colName: str, subNames: list[str]=[]) -> None:
        """ self.view에 대한 row span 설정
            kwargs:
                colName: str
                subNames: list[str]
        """
        self.view.setRowSpan(colName, subNames)

    def set_selected_rows(self, rowList:list[dict]):
        self.selected_rows = rowList

    def set_selected_row(self, rowDict:dict):
        self.selected_row = rowDict

    #### getters
    def get_table_header(self) -> list[str]:
        """ table header 반환 """
        if not self.table_header:
            #### api_datas를 통해서 생성함
            self.table_header = list(self.api_datas[0].keys())
        
        return self.table_header