from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable, Tuple, Union, TYPE_CHECKING

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import traceback, copy, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class TableConfigMixin:

    _table_name :Optional[str] = None
    _table_config_api_datas :Optional[list[dict]] = None
    _headers :list[str] = []
    _headers_types :Optional[dict[str:str]] = {}
    _mapping_headers :Optional[dict[str:str]] = {}	### { 'column_name': 'display_name' }	
    _mapping_reverse_headers :Optional[dict[str:str]] = {}	### { 'display_name': 'column_name' }
    _hidden_columns:Optional[list[int]] = []
    _no_edit_cols :Optional[list[int]] = []
    _column_types :Optional[dict[str:str]] = {}
    _column_styles :Optional[dict[str:str]] = {}
    _column_widths : Optional[dict[str:int]] = {}
    _table_style :Optional[str] = None

    def on_table_config_refresh(self, is_refresh:bool=True):
        """ 테이블 설정 조회 시 호출 """
        # self.table_name = self._mixin_get_table_name()
        if is_refresh:
            self.load_table_config()
            self.apply_table_config()
            self.setup_menus()
            
            logger.info(f"slot_table_config_refresh : {is_refresh}")

    	
    def load_table_config(self) -> bool:
        logger.info(f"load_table_config : {self.table_name}")
        if not self.table_name:
            logger.critical("테이블 이름이 설정되지 않았읍니다")
            return False

        self.table_config_api_datas = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_TableConfigApiDatas', [])
        # self.table_config_api_datas = [ _obj for _obj in INFO.ALL_TABLE_CONFIG 
        #                             if _obj['table_name'] == self.table_name ]
        channel_name = f"{self.table_name}:table_config_api_datas"  
        # QTimer.singleShot(1000, lambda: self.event_bus.publish(channel_name, copy.deepcopy(self.table_config_api_datas) ) )
        # 구독자수 = self.event_bus.publish(channel_name, copy.deepcopy(self.table_config_api_datas) )
        # logger.warning(f"{self.__class__.__name__} | load_table_config | 구독자수: {구독자수} |  channel_name: {channel_name}")


        logger.info(f"load_table_config : {self.table_name} API {len(self.table_config_api_datas)} 로드 완료")
        if self.table_config_api_datas:
            self.table_config = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_TableConfig', {})
            for key, value in self.table_config.items():
                setattr(self, key, value)
            self.event_bus.publish(f"{self.table_name}:table_config", self.table_config)
            # self.process_table_config(self.table_config_api_datas)
            # if self.table_config:
            #     channel_name = f"{self.table_name}:table_config"
            #     # QTimer.singleShot(1000, lambda: self.event_bus.publish(channel_name, copy.deepcopy(self.table_config) ) )
            #     구독자수 = self.event_bus.publish(channel_name, copy.deepcopy(self.table_config) )
            #     logger.warning(f"{self.__class__.__name__} | load_table_config | 구독자수: {구독자수} |  channel_name: {channel_name}")
            # else:
            #     logger.critical(f"self.table_config is None")

        
        # 로컬 DB에서 시도
        # self.table_config_api_datas = self.load_table_config_from_local_db(self.table_name)
        # logger.info(f"load_table_config : {self.table_name} 로컬 DB : {len(self.table_config_api_datas)} 로드 완료")
        # if self.table_config_api_datas:
        # 	self.process_table_config(self.table_config_api_datas)
        # 	return True    
        else:
            logger.warning(f"테이블 설정을 찾을 수 없읍니다: {self.table_name}")
            return False

    def process_table_config(self, config_data):
        """API에서 받은 테이블 설정 처리"""
        if not config_data:
            logger.warning("처리할 테이블 설정 데이터가 없읍니다")
            return
            
        DBs = config_data
        표시명 = 'display_name'
        
        self.table_config = {
            '_table_name': self.table_name,
            '_table_config_api_datas': DBs,
            '_mapping_display_to_attr': {_obj.get('column_name'): _obj.get(표시명) for idx, _obj in enumerate(DBs)},
            '_mapping_attr_to_display': {_obj.get(표시명): _obj.get('column_name') for idx, _obj in enumerate(DBs)},
            '_headers': [_obj.get(표시명) for _obj in DBs],
            '_headers_types': {_obj.get(표시명): _obj.get('column_type') for _obj in DBs},
            '_hidden_columns': [idx for idx, _obj in enumerate(DBs) if _obj.get('is_hidden', False)],
            '_no_edit_cols': [idx for idx, _obj in enumerate(DBs) if not _obj.get('is_editable', True)],
            '_column_types': {_obj.get(표시명): _obj.get('column_type') for _obj in DBs},
            '_column_styles': {_obj.get(표시명): _obj.get('cell_style') for _obj in DBs},
            '_column_widths': {_obj.get(표시명): _obj.get('column_width', 0) for _obj in DBs},
            '_table_style': DBs[0].get('table_style') if DBs else None
        }


        logger.info(f"process_table_config : {self.table_name} 처리 완료")
        # logger.debug(f"self.table_config : {self.table_config}")

        for key, value in self.table_config.items():
            setattr(self, key, value)


        ### lazy 속성 초기화 로, 바로 가져옴..
        if hasattr(self, 'no_edit_columns_by_coding') :
            if 'ALL' in self.no_edit_columns_by_coding or 'All' in self.no_edit_columns_by_coding or 'all' in self.no_edit_columns_by_coding:
                self.no_edit_columns_by_coding = copy.deepcopy(self._headers)
                self.no_edit_columns_indexs_by_coding = [ i for i in range(len(self._headers)) ]
            else:
                self.no_edit_columns_by_coding = self.parent().no_edit_columns_by_coding
                self.no_edit_columns_indexs_by_coding = [ self._headers.index(self._mapping_headers.get(name, name)) for name in self.no_edit_columns_by_coding ]

        ### 코딩으로 편집 제한 -->  model flags 에서 사용
        # self.no_edit_columns_by_coding = []
        # if hasattr(self.parent(), 'no_edit_columns_by_coding') and self.parent().no_edit_columns_by_coding:
        #     if 'ALL' in self.parent().no_edit_columns_by_coding :
        #         self.no_edit_columns_by_coding = copy.deepcopy(self._headers)
        #         self.no_edit_columns_indexs_by_coding = [ i for i in range(len(self._headers)) ]
        #     else:
        #         self.no_edit_columns_by_coding = self.parent().no_edit_columns_by_coding
        #         self.no_edit_columns_indexs_by_coding = [ self._headers.index(self._mapping_headers.get(name, name)) for name in self.no_edit_columns_by_coding ]


    def load_table_config_from_local_db(self, table_name:str) ->list[dict]:
        """ 로컬 DB에서 테이블 설정 로드 """
        try:
            from local_db.models import Table_Config
            table_config_dict = Table_Config.objects.filter(table_name=table_name).values()
            return table_config_dict
        except Exception as e:
            logger.error(f"로컬 DB에서 테이블 설정 로드 실패: {e}")
            return []
    
    def apply_table_config(self):
        """테이블 설정 적용"""
        try:
            self.apply_hidden_columns()
            self.apply_column_widths()

            ##  강제로 레이아웃 변경 발생
            self.resizeRowsToContents()

        except Exception as e:
            logger.error(f"apply_table_config 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def apply_hidden_columns(self):
        """숨길 컬럼 적용 - 전체 초기화 후 설정"""
        col_count = self.model().columnCount()
        
        # 1. 모든 컬럼 보이게 초기화
        for col in range(col_count):
            self.setColumnHidden(col, False)
        
        # 2. 숨길 컬럼 설정
        logger.debug(f"apply_hidden_columns : _hidden_columns : {self._hidden_columns}")
        if '_hidden_columns' in self.table_config and self.table_config['_hidden_columns']:
            for col_idx in self.table_config['_hidden_columns']:
                self.setColumnHidden(col_idx, True)

    def apply_no_edit_cols(self):
        """편집 불가능한 컬럼 적용"""
        return
        if hasattr ( self, '_no_edit_cols' ):
            self.model().set_no_edit_cols(self._no_edit_cols)


    def apply_column_widths(self):
        """컬럼 너비 적용"""
        ### config 모드일 때는 적용하지 않음
        try:
            if '_column_widths' in self.table_config and self.table_config['_column_widths']:
                for col_name, width in self.table_config['_column_widths'].items():
                    if col_name not in self.table_config['_headers']:
                        continue
                    col_idx = self.table_config['_headers'].index(col_name)
                    # logger.debug(f"apply_column_widths : col_idx : {col_idx}")
                    if 0 <= col_idx < self.model().columnCount():
                    # 모든 컬럼은 사용자가 조정 가능하도록 Interactive 모드로 설정
                        self.horizontalHeader().setSectionResizeMode(
                            col_idx, QHeaderView.ResizeMode.Interactive)
                        
                        if width == 0:
                            # 초기 너비를 내용에 맞게 자동 조정
                            self.resizeColumnToContents(col_idx)
                        else:
                            # 지정된 초기 너비 설정
                            self.setColumnWidth(col_idx, width)
        except Exception as e:
            logger.error(f"apply_column_widths 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    

class TableMenuMixin:

    def setup_menus(self):
        """전체 메뉴 설정"""
        menus_dict = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_Menus', {})
        if not menus_dict:
            logger.warning(f"메뉴 설정을 찾을 수 없읍니다: {self._table_name}")
            return

        logger.debug(f"setup_menus : menus_dict : {type(menus_dict)}")
        logger.debug(f"setup_menus : menus_dict : {menus_dict}")
        for key,menu_list in menus_dict.items():
            setattr(self, f"{key}_menus", menu_list)
 

        if hasattr(self, 'cell_menu_by_coding'):
            self.cell_menus.extend(self.cell_menu_by_coding)
        if hasattr(self, 'v_header_menu_by_coding'):
            self.v_header_menus.extend(self.v_header_menu_by_coding)
        if hasattr(self, 'h_header_menu_by_coding'):
            self.h_header_menus.extend(self.h_header_menu_by_coding)
        logger.debug ( f"setup_menus : v_header_menus : {self.v_header_menus}")
        logger.debug ( f"setup_menus : h_header_menus : {self.h_header_menus}")
        logger.debug(f"setup_menus : cell_menus : {self.cell_menus}")
        if self.cell_menus:
            for menuObj in self.cell_menus:
                display_headers = self.model()._headers
                col_idx = display_headers.index( self.table_config['_mapping_display_to_attr'].get(menuObj['col_name'], menuObj['col_name']) )
                self.cell_menu_actions[col_idx] = menuObj['menus']
        ### sorting 관련 view 설정
        _sorting_enable = False
        for menuObj in self.h_header_menus:
            if 'sort' in menuObj.get('h_header', {}).get('name', '') and menuObj.get('visible', False):
                _sorting_enable = True
                break
        logger.debug(f"setup_menus : _sorting_enable : {_sorting_enable}")
        self.menu_handler.enable_sorting(_sorting_enable)
        
    def create_action(self, 
                    menu_item:dict, 
                    object_name_prefix:str='v_header', 
                    slot_prefix:str='slot_v_header',
                    **kwargs
                    ):
        """공통 QAction 생성 함수
            kwargs : rowNo, colNo 등 담아서 전달
        """
        ### {'id': 1, 'order': 1, 'visible': True, 'table': 1, 
        # 	'v_header': {'id': 1, 'name': 'add_row', 'title': '신규 Row 생성', 'tooltip': '현재 선택된 아래에 신규 Row를 생성합니다.'}}, 
        menu_obj = menu_item.get(object_name_prefix, {})
        if not menu_obj:
            logger.warning(f"menu_obj is None : {menu_item}")
            return
        title = menu_obj.get('title', '')
        # 구분선 추가 처리
        if title == 'seperator':
            action = QWidgetAction(self)  # QWidgetAction을 사용하여 구분선 추가
            action.setSeparator(True)
            return action      
        
        action = QAction(menu_obj['title'], self)
        action.setObjectName(f"{object_name_prefix}_{menu_obj['name']}")
        action.setToolTip(menu_obj['tooltip'])
        action.setEnabled(True)

        return self.on_menu_action(action, menu_obj, object_name_prefix, slot_prefix, **kwargs)

        raw_func = menu_obj.get('slot_func', None)
        slot_func = None

        if callable(raw_func):
            slot_func = raw_func  # e.g., self.on_user_select
            logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
        elif isinstance(raw_func, str):
            slot_name = f"{slot_prefix}__{raw_func}"
            slot_func = getattr(self.menu_handler, slot_name, self.menu_handler.default_slot)

        # kwargs에 row, col 등 담아서 전달
        if slot_func == self.menu_handler.default_slot:
            logger.warning(f"slot_func is default_slot : {slot_name}")
        action.triggered.connect(lambda: slot_func(**kwargs))
        return action
    
    def create_cell_action (self, 
                    menu_item:dict, 
                    object_name_prefix:str='v_header', 
                    slot_prefix:str='slot_v_header',
                    **kwargs ):
        """셀 메뉴 생성"""
        menu_obj = menu_item
        if not menu_obj:
            logger.warning(f"menu_obj is None : {menu_item}")
            return
        title = menu_obj.get('title', '')
        # 구분선 추가 처리
        if title == 'seperator':
            action = QWidgetAction(self)  # QWidgetAction을 사용하여 구분선 추가
            action.setSeparator(True)
            return action      
        
        action = QAction(menu_obj['title'], self)
        action.setObjectName(f"{object_name_prefix}_{menu_obj['name']}")
        action.setToolTip(menu_obj['tooltip'])
        action.setEnabled(True)
        # callable 인지, 또한 menu_handler 에 있는지 확인
        raw_func = menu_item.get('slot_func')
        slot_func = None

        return self.on_menu_action(action, menu_item, object_name_prefix, slot_prefix, **kwargs)

        # 타입에 따라 처리
        if callable(raw_func):
            slot_func = raw_func  # e.g., self.on_user_select
            logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
        elif isinstance(raw_func, str):
            handler_func_name = f"{slot_prefix}__{raw_func}"
            slot_func = getattr(self.menu_handler, handler_func_name, None)
            if slot_func is None:
                logger.warning(f"[Menu] No such menu_handler slot_func: {handler_func_name}, fallback to default_slot")
                slot_func = self.menu_handler.default_slot
        else:
            logger.warning(f"[Menu] slot_func is invalid type: {type(raw_func)}")
            slot_func = self.menu_handler.default_slot

        action.triggered.connect(lambda: slot_func(**kwargs))
        return action

    def on_menu_action(self, action:QAction, menu_item:dict, object_name_prefix:str='v_header', slot_prefix:str='slot_v_header', **kwargs):
        """ 메뉴 액션 처리 """
        logger.info(f"on_menu_action : {action}, {menu_item}, {kwargs}")
        raw_func = menu_item.get('slot_func')
        slot_func = None

        # 타입에 따라 처리
        if callable(raw_func):
            slot_func = raw_func  # e.g., self.on_user_select
            logger.debug(f"[Menu] Using direct method for {menu_item['name']}")
        else:
            raw_func = menu_item.get('name', None)
            logger.debug(f"[Menu] raw_func : {raw_func}")
            if raw_func and isinstance(raw_func, str):
                handler_func_name = f"{slot_prefix}__{raw_func}"
                slot_func = getattr(self.menu_handler, handler_func_name, None)
                logger.debug(f"[Menu] slot_func : {slot_func}")
                if slot_func is None:
                    logger.warning(f"[Menu] No such menu_handler slot_func: {handler_func_name}, fallback to default_slot")
                    slot_func = self.menu_handler.default_slot
            else:
                logger.warning(f"[Menu] slot_func is invalid type: {type(raw_func)}")
                slot_func = self.menu_handler.default_slot

        action.triggered.connect(lambda: slot_func(**kwargs))
        return action

    def show_v_header_context_menu(self, position):
        """수직 헤더 컨텍스트 메뉴 표시"""
        ### 현재 선택된 행 번호 가져오기
        selected_row = self.currentIndex().row()
        logger.debug(f"show_v_header_context_menu : {self.v_header_menus}, position : {position}")
        ###DEBUG - show_v_header_context_menu : init_basic_config
        # [{'id': 1, 'order': 1, 'visible': True, 'table': 1, 
        # 	'v_header': {'id': 1, 'name': 'add_row', 'title': '신규 Row 생성', 'tooltip': '현재 선택된 아래에 신규 Row를 생성합니다.'}}, 
        # {'id': 2, 'order': 2, 'visible': True, 'table': 1, 
        # 	'v_header': {'id': 2, 'name': 'del_row', 'title': '선택 Row 삭제', 'tooltip': '현재 선택된  Row를 삭제(db에서) 삭제합니다.'}}]
        menu = QMenu(self)
        for menuObj in self.v_header_menus:
            action = self.create_action(menuObj, 'v_header', 'slot_v_header', rowNo=selected_row)
            menu.addAction(action)
        menu.exec(self.viewport().mapToGlobal(position))

    def show_h_header_context_menu(self, position):
        """수평 헤더 컨텍스트 메뉴 표시"""
        ### 현재 선택된 행 번호 가져오기
        selected_col = self.currentIndex().column()
        logger.debug(f"show_h_header_context_menu : {self.h_header_menus}, position : {position}")
        menu = QMenu(self)
        for menuObj in self.h_header_menus:
            action = self.create_action(menuObj, 'h_header', 'slot_h_header', colNo=selected_col)
            menu.addAction(action)
                
        menu.exec(self.viewport().mapToGlobal(position))

    def show_cell_context_menu(self, position):
        """셀 컨텍스트 메뉴 표시"""
        ### 현재 선택된 행 번호 가져오기
        selected_row = self.currentIndex().row()
        selected_col = self.currentIndex().column()
        logger.debug(f"show_cell_context_menu : {self.cell_menu_actions}, position : {position}, selected_col in self.cell_menu_actions : {selected_col in self.cell_menu_actions}")
        if selected_col in self.cell_menu_actions:
            menu = QMenu(self)
            for menuObj in self.cell_menu_actions[selected_col]:
                action = self.create_cell_action(menuObj, 'cell_menu', 'slot_cell_menu', rowNo=selected_row, colNo=selected_col)
                menu.addAction(action)
            menu.exec(self.viewport().mapToGlobal(position))

