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


class TableView_품질경영_CS관리(Base_Table_View):
    # set_row_span_list = [
    #     ('일자', [] ),
    # ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_no_config_initial = False #### 💡 초기 tableconfig 있음
        self.v_header_menu_by_coding = [

            {   
                'v_header': {
                    'name' : 'delete_row',
                    'slot_func' : self.on_delete_claim_project,
                    'title': '클레임 프로젝트 삭제',
                    'tooltip': '클레임 프로젝트 삭제합니다',
                    'visible': True,
                },
            },
        ]
        self.cell_menu_by_coding = [
            {
                'col_name': 'claim_file_수',
                'menus': [
                    {   
                        'name' : 'claim_file_view',
                        'slot_func' : self.on_file_view,
                        'title': '클레임 파일 보기',
                        'tooltip': '클레임 파일을 보여줍니다.',
                        'visible': True,
                    },
                    {   
                        'name' : 'claim_file_download',
                        'slot_func' : self.on_file_download,
                        'title': '클레임 파일 다운로드',
                        'tooltip': '클레임 파일을 다운로드합니다.',
                        'visible': True,
                    },
                ]
            },
            {
                'col_name': 'activity_file_수',
                'menus': [
                    {   
                        'name' : 'activity_file_view',
                        'slot_func' : self.on_file_view,
                        'title': '활동 파일 보기',
                        'tooltip': '활동 파일을 보여줍니다.',
                        'visible': True,
                    },
                    {   
                        'name' : 'activity_file_download',
                        'slot_func' : self.on_file_download,
                        'title': '활동 파일 다운로드',
                        'tooltip': '활동 파일을 다운로드합니다.',
                        'visible': True,
                    },
                ]
            }
        ]

    
    def on_add_claim_project(self, rowNo:int):
        logger.info(f"on_add_claim_project: {rowNo}")
        model:TableModel_품질경영_CS관리 = self.model()
        model.request_add_claim_project(rowNo)

    def on_delete_claim_project(self, rowNo:int):
        logger.info(f"on_delete_claim_project: {rowNo}")
        model:TableModel_품질경영_CS관리 = self.model()
        model.request_delete_claim_project(rowNo)

    def show_v_header_context_menu(self, position):
        """ override : edit 불가능 row는 메뉴 생성 안함."""
        selected_row = self.currentIndex().row()
        if self.model()._is_menu_visible(selected_row):
            super().show_v_header_context_menu(position)
        else:
            logger.info(f"show_v_header_context_menu: {selected_row} is not editable")

    def on_file_view(self, rowNo:int, colNo:int):
        logger.info(f"on_file_view: {rowNo}, {colNo}")
        model:TableModel_품질경영_CS관리 = self.model()
        model.request_file_view(rowNo, colNo)

    def on_file_download(self, rowNo:int, colNo:int):
        logger.info(f"on_file_download: {rowNo}, {colNo}")
        model:TableModel_품질경영_CS관리 = self.model()
        model.request_file_download(rowNo, colNo)



class TableModel_품질경영_CS관리(Base_Table_Model):

    등록자_fk_Column_No = None
    완료자_fk_Column_No = None
    claim_file_수_Column_No = None
    activity_file_수_Column_No = None   
    Column_No_Dict = {
        '등록자_fk': 등록자_fk_Column_No,
        '완료자_fk': 완료자_fk_Column_No,
        'claim_file_수': claim_file_수_Column_No,
        'activity_file_수': activity_file_수_Column_No,
    }


    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        if self.table_name:
            self.event_bus.subscribe(f"{self.table_name}:request_claim_open", self.on_request_claim_open)
        else:
            logger.critical(f" {self.__class__.__name__} {self.table_name} is not ready ==> no on_request_claim_open subscribe")


    def on_request_claim_open(self, selected_rows:list[dict]):
        logger.info(f"on_request_claim_open: {selected_rows}")
        if not selected_rows and isinstance(selected_rows, list) and isinstance(selected_rows[0], dict):
            return
        selected_rows_data = [self.create_model_data_by_row(row) for row in selected_rows]
        selected_rows_ids = [row['id'] for row in selected_rows]

        try:
            for id, selected_row in zip(selected_rows_ids, selected_rows_data):                
                index = self._data.index( selected_row )
                logger.info(f"index: {index}")
                _isok, _json = APP.API.Send(self.url, { 'id': id }, { 'id': id , '진행현황':'Open'})

                if _isok:
                    self._data.pop(index)
                    self.beginRemoveRows(QModelIndex(), index, index)
                    self.endRemoveRows()
                    self.dataChanged.emit(self.index(index, 0), self.index(index, self.columnCount() - 1), [Qt.DisplayRole])
                    #### empty
                    if not self._data:
                        self.event_bus.publish(f"{self.table_name}:empty_data", True)
                else:
                    Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")

        except Exception as e:
            logger.error(f"on_request_claim_open: {e}")
            logger.error(f"{traceback.format_exc()}")
            Utils.generate_QMsg_critical(None, title="Claim 열기 실패", text="Claim 열기 실패")
	
    def request_add_claim_project(self, rowNo:int):
        return 
        logger.info(f"request_add_claim_project: {rowNo}")
        copyed_row = copy.deepcopy( self._data[rowNo])
        일자_colNo = self.get_column_No_by_field_name('일자')        
        id_colNo = self.get_column_No_by_field_name('id')
        소요시간_colNo = self.get_column_No_by_field_name('소요시간')
        for idx, value in enumerate(copyed_row):
            if idx == id_colNo: 
                copyed_row[idx] = -1
            elif idx == 소요시간_colNo:
                copyed_row[idx] = 0
            elif idx != 일자_colNo:
                copyed_row[idx] = ''

        # View에 삽입 알림 시작
        self.beginInsertRows(QModelIndex(), rowNo, rowNo)
        self._data.insert(rowNo, copyed_row)    
        self.endInsertRows()
        self.dataChanged.emit(self.index(rowNo, 0), self.index(rowNo, self.columnCount() - 1), [Qt.DisplayRole])

    def request_delete_claim_project(self, rowNo:int):
        super().request_delete_row(
            rowNo= rowNo,
            dlg_question= lambda : Utils.generate_QMsg_question(None, title="클레임 프로젝트 삭제", text="클레임 프로젝트를 삭제하시겠습니까?"),
            dlg_info = lambda : Utils.generate_QMsg_Information(None, title="Claim 삭제", text="Claim 삭제 성공", autoClose=1000),
            dlg_critical = lambda : Utils.generate_QMsg_critical(None, title="Claim 삭제", text="Claim 삭제 실패"),
            )


    def request_file_view(self, rowNo:int, colNo:int):
        if not (self.claim_file_수_Column_No  and self.activity_file_수_Column_No ):
            self.get_class_attr_column_No()

        if colNo == self.claim_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('claim_files_url')]
        elif colNo == self.activity_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('activty_files_url')]
        else:
            return

        if urls :
            dlg = FileViewer_Dialog( self.parent(), files_list=urls)
            dlg.exec()

    def request_file_download(self, rowNo:int, colNo:int):
        if not (self.claim_file_수_Column_No  and self.activity_file_수_Column_No ):
            self.get_class_attr_column_No()

        if colNo == self.claim_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('claim_files_url')]
            self._download_multiple_files(urls)

        elif colNo == self.activity_file_수_Column_No:
            urls = self._data[rowNo][self.get_column_No_by_field_name('activty_files_url')]
            self._download_multiple_files(urls)

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
        self.get_class_attr_column_No()

        if col ==self.등록자_fk_Column_No or col == self.완료자_fk_Column_No:
            try:
                _fk:int = self._data[row][col]
                if isinstance(_fk, int) and _fk > 0:
                    return INFO.USER_MAP_ID_TO_USER[_fk]['user_성명']
            except Exception as e:
                logger.error(f"get_class_attr_column_No: {e}")
                logger.error(f"{traceback.format_exc()}")
                return str(_fk)        
        
        return super()._role_display(row, col)

    def format_date_str(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
            day = dt.day
            month = dt.month
            return f"{month}월{day}일 ({weekday_kr})"  # 줄바꿈 포함
        except Exception:
            return date_str

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
                #### 무조건 보냄... 원본과 비교가 불가: 왜냐면 막  추가되는 경우가 많음
                # if self._data[row] == self._original_data[row]:
                #     continue
                bulk_data.append( self.get_row_data(row) )
            if bulk_data:
                _isok, _json = APP.API.post(url= self.url+f"bulk/",  data={'datas': json.dumps(bulk_data, ensure_ascii=False)})
                if _isok:
                    logger.info(f"API 호출 성공:  {type(_json)}, {_json}")
                    self.event_bus.publish(f"{self.table_name}:datas_changed", _json)
                    self.clear_modified_rows(list(self._modified_rows))
                    logger.info(f"API 호출 성공: {_json}")
                    Utils.generate_QMsg_Information(None, title="API 호출 성공", text="API 호출 성공", autoClose=1000)
                else:
                    Utils.generate_QMsg_critical(None, title="API 호출 실패", text="API 호출 실패")
	
       
    def get_row_data(self, row:int) -> dict:
        """ 특정 행의 데이터를 API 형식(dict)으로 반환 :modify
        """
        _dict =  super().get_row_data(row)
        _dict['등록자_id'] = INFO.USERID        
        return _dict


class TableDelegate_품질경영_CS관리(Base_Delegate):

    def custom_editor_handler(self, display_name:str, editor_class:callable, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        return False
        logger.debug(f"custom_editor_handler: {display_name}, {editor_class}, {event}, {model}, {option}, {index}")
        logger.debug(f"self.custom_editor_info: {self.custom_editor_info}")
        field_name = model.get_field_name_by_display_name(display_name)
        if field_name in self.custom_editor_info:
            match field_name:
                case '고객사'|'구분'|'기여도':
                    editor = editor_class(option.widget,                                         
                                        on_complete_channelName=f"{self.table_name}:custom_editor_complete",
                                        index=index,
                                        _list = self.MAP_DisplayName_to_list[display_name],
                                        title=f"{display_name} 선택"
                                        )
                    editor.exec_()


                case _:
                    logger.error(f"custom_editor_handler: {display_name} 에디터 클래스가 없읍니다.")
                    return False
                
            return True
        return False



        

class Wid_table_품질경영_CS관리( Wid_table_Base_for_stacked ):

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_품질경영_CS관리(self)
        self.model = TableModel_품질경영_CS관리(self.view)
        self.delegate = TableDelegate_품질경영_CS관리(self.view)
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

