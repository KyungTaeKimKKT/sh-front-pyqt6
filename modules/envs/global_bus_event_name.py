from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import traceback


class Global_Bus_Event_Name:
    _instance = None
    LOGIN = 'login'   ### bool, 로그인 시 발생하는 이벤트
    WS_STATUS = 'ws_status'   ### data:str, 웹소켓 상태 변경 시 발생하는 이벤트
    API_STATUS = 'api_status'   ### data:str, API 상태 변경 시 발생하는 이벤트
    CPU_RAM_MONITOR = 'cpu_ram_monitor'   ### data:str, CPU, RAM 모니터링 시 발생하는 이벤트

    SEARCH_REQUESTED = 'search_requested'   ### data:str, 검색 요청 시 발생하는 이벤트
    PAGINATION_INFO = 'pagination_info'   ### data:dict, 페이지 정보 발생하는 이벤트
    PAGINATION_CHANGED = 'pagination_changed'   ### data:dict, 페이지 변경 시 발생하는 이벤트
    PAGINATION_DOWNLOAD = 'pagination_download'   ### data:dict, 페이지 다운로드 시 발생하는 이벤트
    ### timer
    TIMER_1SEC = 'timer_1sec'   ### data:str, 1초마다 발생하는 이벤트
    TIMER_1MIN = 'timer_1min'   ### data:str, 매 1분:0초 마다 발생하는 이벤트
    TIMER_10MIN = 'timer_10min'   ### data:str, 10분:0초마다 발생하는 이벤트
    TIMER_1HOUR = 'timer_1hour'   ### data:str, 1시:0초마다 발생하는 이벤트


    TRACE_TIME = 'trace_time'   ### data:dict, 시간 측정 시 발생하는 이벤트
    TRACE_LOGGER = 'trace_logger'   ### data:dict, 로그 추적 시 발생하는 이벤트
    
    # APP_INITIALIZED = 'app_initialized'   ### data:str, 앱 초기화 시 발생하는 이벤트
    LIB_LOAD_STARTED = 'lib_load:started'   ### data:str, 라이브러리 로드 시작 시 발생하는 이벤트
    LIB_LOAD_COMPLETED = 'lib_load:completed'   ### data:str, 라이브러리 로드 완료 시 발생하는 이벤트
    LIB_LOAD_CANCELLED = 'lib_load:cancelled'   ### data:str, 라이브러리 로드 취소 시 발생하는 이벤트
    LIB_LOAD_FAILED = 'lib_load:failed'   ### data:str, 라이브러리 로드 실패 시 발생하는 이벤트
    
    
    APP_RELOAD = 'app_reload'       ### data:bool,  CTRL+F5 키 눌렀을 때 발생하는 이벤트
    TOOLBAR_MENU_CLICKED = 'toolbar_menu_clicked' ### data:dict, 툴바 메뉴 클릭 시 발생하는 이벤트

    API_DATA_REFRESH = 'data_refresh'   ### data:list[dict], 데이터 조회 시 발생하는 이벤트
    API_DATA_UPDATED = 'data_updated'   ### data:list[dict], 데이터 업데이트 시 발생하는 이벤트


    ### table
    TABLE_TOTAL_REFRESH = 'table_total_refresh'   ### data:list[dict], 테이블 전체 조회 시 발생하는 이벤트
    TABLE_CONFIG_REFRESH = 'table_config_refresh'   ### data:list[dict], 테이블 설정 조회 시 발생하는 이벤트
    TABLE_DATA_REFRESH = 'table_data_refresh'   ### data:list[dict], 데이터 조회 시 발생하는 이벤트
    TABLE_DATA_UPDATED = 'table_data_updated'   ### data:list[dict], 데이터 업데이트 시 발생하는 이벤트


    HOME_WIDGET_SHOW = 'home_widget_show'   ### data:None, 홈 위젯 표시 시 발생하는 이벤트

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Global_Bus_Event_Name, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 초기화 코드가 필요하면 여기에 추가
        pass

    def set_event_name(self, event_name:str, value:str):
        """ 이벤트 이름을 설정합니다. """
        setattr(self, event_name, value)


    def get_event_name(self, event_name:str) ->Optional[str]:
        """ 이벤트 이름을 반환합니다. """
        try:
            return getattr(self, event_name)
        except Exception as e:
            print(f"get_event_name 오류: {e}")
            return None
        
    def get_all_event_name(self) ->List[str]:
        """ 모든 이벤트 이름을 반환합니다. """
        return [attr for attr in dir(self) if not attr.startswith('__') and not callable(getattr(self, attr))]

global_bus_event_name = Global_Bus_Event_Name()