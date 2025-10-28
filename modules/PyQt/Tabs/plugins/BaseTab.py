from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from functools import partial

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from config import Config as APP
from info import Info_SW as INFO
from modules.utils.api_response_분석 import handle_api_response

import modules.user.utils as Utils
import traceback
import time
import copy
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

module_postfix = __name__.split('.')[-1].split('__')[-1]


class Mixin_PB_Info:
    def __init__(self):
        self._default_map_pb_to_generate_info = {
            'PB_New':           {'title': '신규 생성', 
                                 'tooltip': '첫번째 줄에 신규 생성합니다.',
                                 'slot_factory' : lambda ctx : lambda: self.on_new_row(ctx),
                                 'disable_not_selected': False
                                 },
            'PB_copy_new_row':  {'title': '복사 생성', 
                                 'tooltip': '선택한 줄에 복사 상단에 신규 생성합니다.',
                                 'slot_factory' : lambda ctx : lambda: self.on_copy_new_row(ctx),
                                 'disable_not_selected': True
                                 },
            'PB_User_Select': {'title': '사용자 선택', 
                                 'tooltip': '사용자 선택',
                                 'slot_factory' : lambda ctx : lambda: self.on_user_select(ctx),
                                'disable_not_selected': True
                                 },
            'PB_Delete': {'title': '삭제', 
                                 'tooltip': '삭제',
                                 'slot_factory' : lambda ctx : lambda: self.on_delete_row(ctx),
                                 'disable_not_selected': True
                                 },
            '파일다운로드':  {'title': 'Claim 파일다운로드', 
                    'tooltip': 'Claim 파일다운로드',
                    'slot_factory' : lambda ctx : lambda: self.on_file_download(ctx), 
                    'disable_not_selected': True
                    },
            '파일보기':  {'title': 'Claim 파일보기', 
                    'tooltip': 'Claim 파일보기',
                    'slot_factory' : lambda ctx : lambda: self.on_file_view(ctx), 
                    'disable_not_selected': True
                    },
            '지도보기':  {'title': '지도보기', 
                    'tooltip': '지도보기',
                    'slot_factory' : lambda ctx : lambda: self.on_map_view(ctx), 
                    'disable_not_selected': True
                    },
            'Excel_Export_User':  {'title': 'Excel 내보내기', 
                    'tooltip': 'Excel 내보내기',
                    'slot_factory' : lambda ctx : lambda: self.on_excel_export(ctx), 
                    'disable_not_selected': True
                    },
            'Excel_Export_Admin':  {'title': 'Excel 내보내기', 
                    'tooltip': 'Excel 내보내기(관리자) ✅조회된 모든 data를 내보냅니다.',
                    'slot_factory' : lambda ctx : lambda: self.on_excel_export(ctx), 
                    'disable_not_selected': True
                    },
            
        }
        # self._map_pb_to_generate_info = {}
    @property
    def _map_pb_to_generate_info(self) -> dict:
        return self._default_map_pb_to_generate_info

    def create_pb_info(self, pb_names:list[str]) -> dict:
        return { pb_name: self._map_pb_to_generate_info[pb_name] for pb_name in pb_names if pb_name in self._map_pb_to_generate_info }

    def update_pb_info(self, pb_info:dict) -> dict:
        self._map_pb_to_generate_info.update(pb_info)

    def get_map_pb_to_generate_info(self) -> dict:
        return self._map_pb_to_generate_info


    def on_new_row(self):
        pass

    def on_copy_new_row(self):
        pass

    def on_user_select(self):
        pass

    def on_delete_row(self):
        pass

    def on_file_download(self):
        # lambda: Utils.file_download_multiple(urls=self.selected_dataObj['claim_files_url']),
        pass

    def on_file_view(self):
        # lambda: Utils.file_view(urls=self.selected_dataObj['claim_files_url']),
        pass

    def on_map_view(self):
        # lambda: Utils.map_view(address=self.selected_dataObj['현장주소']),
        pass

    def on_excel_export(self):
        # lambda: Utils.file_download_multiple(urls=self.selected_dataObj['claim_files_url']),
        pass



class BaseTab(QWidget, Mixin_PB_Info):
    """모든 탭의 기본 골격"""

    selected_rows:Optional[list[dict]] = None

    def __init__(self, parent: QWidget, **kwargs):
        super().__init__(parent)
        if 'APP_ID' in kwargs and kwargs['APP_ID']:
            self.APP_ID = kwargs['APP_ID']
            self.setObjectName(f"APP_ID_{kwargs['APP_ID']}")  # ✅ 여기서 지정
            if INFO.IS_DEV:
                print(f"BaseTab : __init__ : self.objectName: {self.objectName()}")
        # else:
        #     raise ValueError(f"{self.__class__.__name__} : APP_ID 없음")
        self.event_bus = event_bus
        self.kwargs = kwargs
        self.param = None
        self.api_datas = []
        self._init_kwargs(**kwargs)    # 먼저 값 초기화
        self.create_ui()               # 그 다음 UI 생성 (wid_table 생성됨)
        self.init_attributes()         # wid_table 이후 table_name 세팅
        # self.connect_signals()          # 그 이후 시그널 연결
    @property
    def is_no_config_initial(self) -> bool:
        """ ### default False, table config 없이 초기화 할 경우 True , 상속에서 관리"""
        return False

    
    def _init_kwargs(self, **kwargs):
        logger.debug(f"{self.__class__.__name__} : _init_kwargs")
        for key, value in kwargs.items():
            setattr(self, key, value)
        if hasattr(self, 'api_uri') and hasattr(self, 'api_url'):
            self.url = self.api_uri + self.api_url


    def create_ui(self):
        """UI를 생성하는 메서드 - 반드시 서브 클래스에서 구현"""
        raise NotImplementedError("서브 클래스에서 create_ui()를 구현해야 합니다.")
    
    @property
    def text_table_config_button(self) -> str:
        _text = {
            False : 'Table Config Model 적용',
            True : 'Api data 적용'
        }
        return _text[self.is_no_config_initial]
    
    def create_table_config_button(self):
        """ 테이블 설정 버튼 생성 """

        if INFO._get_is_table_config_admin():
            label_text = f"테이블 설정 ( Mode : {self.text_table_config_button})"
            self.pb_table_config = QPushButton(label_text)
            if hasattr(self, 'ui') and self.ui and hasattr(self.ui, 'v_table'):
                self.ui.v_table.addWidget(self.pb_table_config)
                self.pb_table_config.clicked.connect(self.slot_table_config)
            else:
                raise ValueError(f"{self.__class__.__name__} : ui 또는 ui.h_search가 없습니다.")

    def slot_table_config(self):
        if hasattr(self, 'stacked_table') and callable(self.stacked_table.apply_table_config_mode):
            mode:str = self.stacked_table.apply_table_config_mode(True)
            if mode == 'config table':
                self.pb_table_config.setText(f'테이블 설정 취소 ( Mode : {self.text_table_config_button})')
            else:
                self.pb_table_config.setText(f'테이블 설정 ( Mode : {self.text_table_config_button})')
        else:
            raise ValueError(f"{self.__class__.__name__} : stacked_table 또는 apply_table_config_mode가 없습니다.")


    def init_attributes(self):
        """UI 생성 이후 필수 속성 초기화"""
        self.table_name = Utils.get_table_name(self.id)

        if not self.table_name:
            logger.warning(f"self.table_name : {self.table_name} 없음")
        else:
            logger.info(f"self.table_name : {self.table_name}")

    def subscribe_gbus(self):		
        self.event_bus.subscribe(f"AppID:{self.id}_{GBus.SEARCH_REQUESTED}", self.slot_search_for)
        self.event_bus.subscribe(f"AppID:{self.id}_{GBus.PAGINATION_CHANGED}", lambda pageNo : self.slot_search_for(f"page={pageNo}") )

    def unsubscribe_gbus(self):
        try:
            self.event_bus.unsubscribe(f"AppID:{self.id}_{GBus.SEARCH_REQUESTED}", self.slot_search_for)
            self.event_bus.unsubscribe( f"AppID:{self.id}_{GBus.PAGINATION_CHANGED}", self.on_pagination_changed )
            self.event_bus.unsubscribe(self.api_channel_name, self.slot_fetch_finished)
        except Exception as e:
            logger.error(f"Error unsubscribing from gbus: {e}")		

    def connect_signals(self):
        """공통 시그널 연결"""
        if hasattr(self, 'ui') and self.ui:
            self.ui.wid_search.search_requested.connect(lambda param: self.slot_search_for(param))
            self.ui.wid_pagination.current_page_changed.connect(lambda pageNo: self.slot_search_for(self.param + f"&page={pageNo}"))

    def run(self):
        """필수 실행 루틴"""
        if INFO.IS_DEV:
            logger.info(f"{self.__class__.__name__} : run")
            logger.info(f"self.table_name: {self.table_name if hasattr(self, 'table_name') else 'table_name not set'}")
            logger.info(f"self.url: {self.url if hasattr(self, 'url') else 'url not set'}")
        self.subscribe_gbus()
        if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
            QTimer.singleShot( 0, lambda: self.ui.wid_search.ui.PB_Search.click())



    def slot_search_for(self, param:Optional[str]=None, _additional_url:Optional[str]=None) :
        """
        결론적으로 main 함수임.        
        Wid_Search_for에서 query param를 받아서, api get list 후,
        table에 _update함.	
        ✅ 25-7-3 추가 파라미터 _additional_url 추가 ==> 존재하면 self.url 뒤에 추가하여 사용함.
        """		
        self.start_time = time.perf_counter()
        self.prev_param = copy.deepcopy(self.param)
        #### 분기점 : direct로 pub 하니,  page=xx 만 들어옴.
        if param :
            if 'page=' in param:
                parts = self.prev_param.split('&')
                parts = [p for p in parts if not p.startswith('page=')]
                parts.append(param)
                self.param = '&'.join(parts)
            else:
                self.param = param
        else:
            self.param = ''            
        if _additional_url:
            url = self.url + _additional_url + '?' + self.param 
        else:
            url = self.url + '?' + self.param 
        if INFO.IS_DEV:
            logger.info(f" {self.__class__.__name__} | slot_search_for | url: {url}")
        self.api_channel_name = f"fetch_{url}"

        self.on_fetch_start(url, self.api_channel_name, self.slot_fetch_finished)
    
    def on_fetch_start(self, url:str, subscribe_channel_name:str, slot_fetch_finished:callable):
        self.event_bus.subscribe(subscribe_channel_name, slot_fetch_finished)
        # self.event_bus.subscribe(self.api_channel_name, self.slot_fetch_finished)
        worker = Api_Fetch_Worker(url)
        worker.start()

        
    def slot_fetch_finished(self, msg) -> tuple[bool, dict, list[dict]]:
        copyed_msg = copy.deepcopy(msg)
        is_ok, pagination, api_datas = handle_api_response(copyed_msg)		
        if is_ok:
            if INFO.IS_DEV:
                logger.info(f"{self.__class__.__name__} : slot_fetch_finished: {len(api_datas)}")
            self.api_datas = copy.deepcopy(api_datas)
            구독자수=self.event_bus.publish( f"{self.table_name}:datas_changed", copy.deepcopy(api_datas) )
            self.event_bus.publish( f"AppID:{self.id}_{GBus.PAGINATION_INFO}", pagination )
        else:
            Utils.generate_QMsg_critical( self, title="서버 조회 오류", msg=msg if msg else "서버 조회 오류" )
        self.end_time = time.perf_counter()
        self.event_bus.publish_trace_time( 
                               { "action" : f"{self.table_name}:fetch_finished", 
                                "duration" : self.end_time - self.start_time ,
                                'description' : f"len(api_datas): {len(api_datas)}" if is_ok and len(api_datas) > 0 else "api fetch error"
                                } )
        if INFO.IS_DEV:
            logger.info(f"slot_fetch_finished: { int((self.end_time - self.start_time) * 1000) } msec")
        return is_ok, pagination, api_datas

    def simulate_search_pb_click(self):
        """ search pb 클릭 시 호출되는 함수 : self.ui.wid_search.ui.PB_Search.click() """
        try:
            self.ui.wid_search.ui.PB_Search.click()
        except Exception as e:
            logger.error(f"simulate_search_pb_click: {e}")

    def clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def close(self):
        self.event_bus.unsubscribe_prefix(f"AppID:{self.id}")
        self.event_bus.unsubscribe_prefix(f"{self.table_name}")
        self.clear_layout(self.layout())

        super().close()
# #
# class BaseTab(QWidget):   
#     """모든 탭의 기본 클래스
        
    
#     """
#     def __init__(self, parent:QWidget,   **kwargs):
#         super().__init__( parent)



#     def _init_kwargs(self, **kwargs):
#         for key, value in kwargs.items():
#             setattr(self, key, value)
#         if hasattr( self, 'api_uri') and hasattr( self, 'api_url'):
#             self.url = self.api_uri + self.api_url

#     def init_attributes(self):
#         self.table_name = f"{self.div}_{self.name}_appID_{self.id}"
#         self.wid_table.setObjectName(self.table_name)
#         logger.debug(f"self.table_name: {self.table_name}")


#     def init_ui(self):
#         """ 탭의 기본 UI를 초기화함.  아래 사항 필요시 추가
#         self.wid_table = Wid_table_App설정_App설정_개발자(self)
#         self.wid_table.setObjectName(self.table_name)
#         self.ui.v_table.addWidget(self.wid_table) 
#         """
#         self.ui = Ui_Tab()
#         self.ui.setupUi(self)


#     def connect_signals(self):
#         """ 아래 2개는 Ui_Tab_Common 사용시 필수. """
#         self.ui.wid_search.search_requested.connect(lambda param: self.slot_search_for(param) )
#         self.ui.wid_pagination.current_page_changed.connect(lambda pageNo: self.slot_search_for( self.param +f"&page={pageNo}" ) )


#     #### app마다 update 할 것.😄
#     def run(self):
#         self.init_attributes()
#         if hasattr(self, 'wid_table') and self.wid_table:
#             self.wid_table.run()

#     def slot_search_for(self, param:Optional[str]=None) :
#         """
#         결론적으로 main 함수임.
#         Wid_Search_for에서 query param를 받아서, api get list 후,
#         table에 _update함.	
#         """		
#         logger.info(f"slot_search_for: {param}, {self.url}")
#         self.param = param
#         url = self.url + '?' + self.param
#         logger.debug(f" slot_search_for: url: {url}")
#         self.event_bus.subscribe(f"fetch_{url}", self.slot_fetch_finished)
#         worker = Api_Fetch_Worker(url)
#         worker.start()

#         # API 요청 후 페이지 파라미터 제거하여 self.param에 저장
#         if param and 'page=' in param:
#             parts = param.split('&')
#             parts = [p for p in parts if not p.startswith('page=')]
#             self.param = '&'.join(parts)

        
#     def slot_fetch_finished(self, msg):
#         is_ok, pagination, api_datas = handle_api_response(msg)
#         self.wid_table.apply_api_datas(api_datas)
#         self.ui.wid_pagination.update_page_info(pagination)









	


