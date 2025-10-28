from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
import platform
import traceback
from config import Config as APP

import datetime

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow
    from PyQt6.QtGui import QAction


class Info_SW_Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    종류 = 'I'     
    Version = "0.56"

    PRELOAD_LIBS =  [
            "numpy",
            "pandas",
            "matplotlib",
            # "scikit-learn",
            # "tensorflow",
            # "torch",
            "cv2",  # opencv-python 대신 실제 임포트 이름인 cv2 사용
            "PIL",  # pillow 대신 실제 임포트 이름인 PIL 사용
            "requests",
            # "beautifulsoup4",
            # "nltk",
            # "spacy",
            # "transformers",
            'PyQt6.QtCore',
            'PyQt6.QtGui',
            'PyQt6.QtWidgets',
            # 'PyQt6.QtWebEngine',      ## t삭제함.
            'PyQt6.QtWebEngineWidgets',
            'PyQt6.QtWebEngineCore',
            'folium',
            'geopy',
            'cryptography',
            'fitz',
            'openpyxl',
            'pathlib',
            'pathlib2',
            'psutil',
            'websockets',
            'urllib3',
            'django',
            'django.conf',
            'django.core',
            'django.db',
            #### 사용자 모듈
            'modules.global_event_bus',
            'modules.envs.global_bus_event_name',
            'modules.logging_config',

        ]
    IC_ENABLE = False
    IS_DebugMode = False
    IS_DEV = True
    MAIN_WINDOW:QMainWindow|None = None
    # API_SERVER = 'mes.swgroup.co.kr'
    # API_SERVER = '192.168.7.129'
    API_SERVER = '192.168.7.108'
    
    FASTAPI_PORT = 9997
    # WS_SERVER = 'mes.swgroup.co.kr'
    # WS_SERVER = '192.168.7.129'
    WS_SERVER = '192.168.7.108'
    IP_SOCKET_SERVER = '127.0.0.1'
    PORT_SOCKET_SERVER = 50000
    HTTP_PORT = 9999
    WS_PORT = 9998
    WS_EnableTrace = False
    TEMP = None
    

    WS_TASKS : dict[str, Any] = {}

    OS_CHOICES = {
        'Windows': 'W',
        'Linux': 'L',
        'RaspberryPi': 'R',
    }

    URI = f'http://{API_SERVER}:{HTTP_PORT}/' 
    PARAM_NO_PAGE = '?page_size=0'
    URI_FASTAPI = f'http://{API_SERVER}:{FASTAPI_PORT}/fastapi/'

    URI_WS = f'ws://{WS_SERVER}:{WS_PORT}/'

    APP_Name = 'Shinwoo APP'
    CURRENT_APP_FK :int = -1
    PREV_APP_FK :int = -1
     ### 'U': python source file : Update 용 ==> 배포되면 update 할 것인지 물어봄 :
     ### 'I' : windows EXE Install file ==> 배포되면 update함.

    PID_Update:int = 0
    PID_Main:int = 0

    ### googleMap api key
    GOOGLE_MAP_API_KEY = 'AIzaSyD2MaeSd0PSAjuK1zcnkEdyryVYdL6oGFA'
    공공DATA_serviceKey = "VOAgXeeBTZflpY2X2s%2BCzGoqgi2McJlHnzVYD1DGh%2Fux8X%2BIo1OjaglLPkLSLLKN4lE5kmZRA30XIBjzV5XTXA%3D%3D"

    ### JWT관련 
    SERVER_ACCESS_TOKEN_LIFETIME = 45 ### 분
    JWT_REFRESH_TIMER = 1000*60*10 ### MAIN TIMER로 구동 1000msec * 60초 * 분 
    REFRESH_기준 = int( JWT_REFRESH_TIMER  / 1000 *1.5)   # api.py에서 기준으로 사용
    AUTH_URL = URI +'api-auth/jwt/'
    REFRESH_URL = URI+'api-auth/jwt/refresh/'
    
    ### APP 권한
    APP_권한_TOTAL : list[dict] = []
    APP_권한_TOTAL_MAP_ID_TO_APP : dict[int, dict] = {}
    APP_권한 : list[dict] = []
    APP_권한_MAP_ID_TO_APP : dict[int, dict] = {}
    APP_MAP_ID_TO_AppWidget : dict[int, Any] = {}
    LOADED_APP_CLASSES : dict[str, type] = {}
    USER_INFO = {}
    USERNAME = ''
    USERID = -1
    MAIL_ID = ''

    BASE_DIR = None

    HOLIDAYS : None|list[datetime.date] = None
    #### USER 관련
    ALL_USER : list[dict] = []
    MBO_사용자: list[dict] = []
    USER_MAP_ID_TO_USER : dict[int, dict] = {}
    USER_MAP_NAME_TO_USER : dict[str, dict] = {}
    # ALL_TABLE_CONFIG : list[dict] = []
    # ALL_TABLE_MENUS : list[dict] = []
    ALL_TABLE_TOTAL_CONFIG : dict[str,dict[str,Any]] = {}
    # MAP_TableName_To_TableConfig : dict[str, list[dict]] = {}
    # MAP_TableName_To_Menus : dict[str, list[dict]] = {}
    ALL_RESOURCES : list[dict] = []
    IS_TABLE_CONFIG_ADMIN :Optional[bool] = None
    IS_APP_ADMIN :Optional[bool] = None
    ### 로깅
    URL_ERROR_LOG = 'api/users/error-log/'

    OS = platform.system()
    #### CPU, RAM 사용률 표시 
    MAX_CPU_PERCENT = 90
    MAX_RAM_PERCENT = 90

    #### 테이블 관련
    TABLE_LAZY_ATTR_NAMES = ['APP_ID', 'is_no_config_initial', 'no_edit_columns_by_coding', 'edit_mode','custom_editor_info']
    Table_View_Lazy_Attr_Names = ['APP_ID', 'is_no_config_initial']
    Table_Model_Lazy_Attr_Names = ['APP_ID', 'no_edit_columns_by_coding', 'edit_mode', 'is_no_config_initial']
    Table_Delegate_Lazy_Attr_Names = ['APP_ID', 'custom_editor_info', 'no_edit_columns_by_coding', 'is_no_config_initial']

    CONFIG_개인_FNAME = 'config_개인.json'
    # OS_choiceName = self._get_OS_choiceName()

    디자인의뢰_중요도 = 20
    작업지침서_중요도 = 20

    
    DateFormat = '%Y-%m-%d'
    DateFormat_short = '%y-%m-%d'
    TimeFormat = '%H:%M:%S'
    DateTimeFormat= DateFormat +'T'+TimeFormat

    ### menu dict
    MAP_MENU_TO_ACTION : dict[str, QAction] = {}

    ### WS URL
    WS_URLS:Optional[list[dict]] = None    #### 서버에서 받아온 원본 정보
    WS_MAP_NAME_TO_URL:Optional[dict[str, str]] = None    #### 변환한 정보


    WS_APP권한_CHANGED = 'broadcast/app_changed/'
    WS_작업지침_배포 = 'broadcast/work_instruction/'
    WS_PING = 'ping/'
    WS_CS_CLAIM_CHANGED = 'broadcast/cs_claim_changed/'
    WS_ERROR_LOG = 'broadcast/error_log_created/'
    WS_APP권한 = 'broadcast/app_authority/'
    WS_USERS_ACTIVE = 'broadcast/users_active/'
    WS_MAIN_URLS = [
        WS_APP권한_CHANGED,
        WS_작업지침_배포,
        WS_PING,
        WS_CS_CLAIM_CHANGED,
        WS_ERROR_LOG,
        WS_APP권한,
        WS_USERS_ACTIVE,
    ]

    ### 영업수주_금액
    WS_SALES_ORDER_AMOUNT_CHANGED = 'broadcast/sales_order_amount_changed/'

    ### URLS
    URL_API_SERVER_CHECK_NO_AUTH = 'api/users/connection-to-no-auth/'
    URL_API_SERVER_CHECK_AUTH = 'api/users/connection-to-auth/'
    

    URL_UserInfo_by_Request = 'api/users/user-info-by-requestUser/'
    URL_User_ALL = 'api/users/users/'
    URL_User_PWD_Init= 'api/users/reset-user-password/'

    URL_Company = 'api/users/company/'

    URL_APP개발자 = "api/users/app권한-개발자/"
    URL_사용자별_APP권한 = "api/users/app권한-사용자별-권한/"

    URL_CONFIG_TABLENAME = "config/table_config/"
    URL_CONFIG_TABLE_BULK_UPDATE = "config/table_config/bulk_update/"

    URL_PASSWORD_CHANGE = "api/users/user-password-change/"

    API_Update_URL = "release/배포리스트/"      ### old : list
    API_Update_Check_URL = "release/배포관리/get_latest_release/"  ### new : check_update
    URL_공지사항 = "공지요청사항/공지사항/"

    URL_공지사항_MODAL = "공지요청사항/공지사항-modal/"
    URL_공지사항_Reading = "공지요청사항/공지사항-reading/"    

    URL_요청사항_FILE = "공지요청사항/요청사항-file/"

    ### 영업수주
    URL_영업수주_등록ApiProcess = '영업수주/영업수주_등록_ApiProcess/'
    WS_영업수주_등록_ApiProcess = 'broadcast/sales_order_register_api_progress/'

    URL_영업수주_금액_Summary_Api = '영업수주/영업수주_금액_Summary_Api/'

    URL_영업수주_관리 = '영업수주/관리/'

    URL_영업수주_일정 = '영업수주/일정관리/'
    URL_영업수주_일정_EXCEL_UPLOAD_BULK = '영업수주/일정관리/excel-upload-bulk/'
    URL_영업수주_금액 = '영업수주/금액관리/'
    URL_영업수주_금액_EXCEL_UPLOAD_BULK = '영업수주/금액관리/excel-upload-bulk/'

    URL_영업수주_자재내역_의장_Mapping = '영업수주/금액관리/자재내역_To_의장_Mapping/'
    URL_영업수주_자재내역_To_의장_Mapping_DB = '영업수주/자재내역_To_의장_Mapping_DB/'

    URL_Elevator_한국정보 = '/elevator-info/info/summary_wo설치일/'
    Elevator_한국정보_URL = '/elevator-info/info/summary_wo설치일/'
    URL_Elevator_한국정보_DOWNLOAD = '/elevator-info/info/summary-wo설치일-download/'
    URL_Elevator_승강기협회_DOWNLOAD = '/elevator-info/info/승강기협회-download/'


    ### 영업MBO
    URL_영업MBO_사용자마감 = '영업mbo/사용자마감_apiview/'
    URL_영업MBO_관리자마감 = '영업mbo/관리자마감_apiview/'
    URL_영업MBO_Create_YEAR_GOAL = '영업mbo/년간목표생성_apiview/'

    ### HR평가
    URL_HR평가_평가설정DB = '/HR평가_V2/평가설정_DB/'
    URL_HR평가_평가체계DB = '/HR평가_V2/평가체계_DB/'
    URL_HR평가_CREATE_평가체계 = '/HR평가_V2/평가체계_db_create/'
    URL_HR평가_COPY_CREATE_평가설정 = '/HR평가_V2/평가설정_DB_Copy_Create/'

    URL_HR평가_역량평가_항목_DB = '/HR평가_V2/역량평가_항목_DB/'

    URL_HR평가_역량평가사전_DB = '/HR평가_V2/역량평가사전_DB/'
    URL_HR평가_역량항목_DB = '/HR평가_V2/역량항목_DB/'
    URL_HR평가_평가시스템_구축 ='/HR평가_V2/평가시스템_구축/'
    URL_HR평가_역량_평가_DB = '/HR평가_V2/역량_평가_DB/'
    URL_HR평가_성과_평가_DB = '/HR평가_V2/성과_평가_DB/'
    URL_HR평가_특별_평가_DB = '/HR평가_V2/특별_평가_DB/'
    URL_HR평가_상급자평가_DB = '/HR평가_V2/상급자평가_DB/'
    URL_HR평가_평가결과_DB = '/HR평가_V2/평가결과_DB/'

    URL_HR평가_평가설정DB_Old = '/HR평가_V2/평가설정DB_Old/'

    URL_HR평가_상급자평가_INFO = '/HR평가_V2/상급자평가_DB_API_View/'
    URL_HR평가_CHECK_평가점수 = '/HR평가_V2/check_평가점수/'
    

    URL_차량관리_기준정보 = '/차량관리/차량관리_기준정보/'
    URL_차량관리_차량LIST_BY_USER = '/차량관리/차량관리_차량번호_사용자_API_View/'

    ### 샘플관리
    URL_샘플관리_PROCESS_DB = '/샘플관리/샘플관리-process/'

    URL_샘플관리_첨부FILE = '/샘플관리/샘플관리-첨부file/'
    URL_샘플관리_완료FILE = '/샘플관리/샘플관리-완료file/'

    ### 작업지침
    URL_작업지침_이력조회 = '/작업지침/이력조회/'
    URL_작업지침_PROCESS_DB = '/작업지침/작업지침-process/'

    URL_작업지침_RENDERING_FILE = '/작업지침/rendering-file/'
    URL_작업지침_첨부_FILE = '/작업지침/첨부-file/'
    URL_작업지침_의장도 = '/작업지침/의장도/'


    #### 생산지시서
    URL_일일보고_휴일 = '/일일보고/휴일등록/'
    URL_생산지시_HTM_Table = '/생산지시서/HTM-table/'
    URL_생산지시_도면정보_Table = '/생산지시서/도면정보-table/'

    URL_생산지시_SPG = '생산지시서/spg/'
    URL_SPG_TABLE = '생산지시서/spg-table/'
    URL_TAB_MADE = '생산지시서/tab-made-file/'

    URL_생산지시서_관리 = '생산지시서/관리/'
    

    ####
    SPG_URL = '생산지시서/spg/'
    SPG_TABLE_URL = '생산지시서/spg-table/'
    SPG_FILE_URL = '생산지시서/spg-file/'
    TAB_Made_file_URL = '생산지시서/tab-made-file/'

    생산지시_도면정보_Table_URL = '생산지시서/도면정보-table/'
    생산지시_HTM_Table_URL = '생산지시서/HTM-table/'

    JAMB_FILE_URL = '생산지시서/JAMB-file/'
    JAMB_발주정보_URL = '생산지시서/JAMB-발주정보/'


    작지배포_URL = '작업지침/배포/'
    NCR배포_URL = '품질경영/NCR배포/'

    ### 생산관리
    URL_생산계획_Schedule_By_Type = '생산관리/생산계획-schedule-by-types/'

    URL_생산계획_공정상세 = '생산관리/생산계획-공정상세/'

    URL_생산계획_DDAY = '생산관리/생산계획-dday/'
    URL_생산계획_ProductionLine = '생산관리/생산계획-productionline/'

    URL_생산계획_생산실적 = '생산관리/생산실적/'

    URL_생산계획_제품완료 = '생산관리/생산관리-제품완료/'

    URL_생산관리_판금처DB = '생산관리/생산관리-판금처DB/'

    ### 재고관리
    URL_재고관리_창고DB = '재고관리/warehouse/'
    # URL_생산계획대기 = '생산지시/생산지시-배포-생산계획대기/'
    # URL_생산계획확정 = '생산관리/생산계획관리/'
    # URL_생산계획_History = '생산관리/history/'
    # URL_생산계획_DDay = '생산관리/생산계획-dday/'
    # URL_생산계획_확정_branch = '생산관리/생산계획-확정-branch/'
    # URL_생산계획_확정_branch_wo_fks = '생산관리/생산계획-확정-branch-wo-fks/'

    URL_SERIAL_DB ='serial/serial-model/'
    URL_SERIAL_HISTORY = 'serial/serial-history/'

    URL_SERIAL_개별이력조회 = 'serial/serial-history/개별이력조회/'

    # URL_Serial_Generate_Bulk = 'serial/generate-bulk/'
    # URL_Serial조회_by_Serial = 'serial/조회-by-barcode/'

    URL_망관리_관리 = '망관리/관리/'

    ### 품질경영
    URL_CS_ACTIVITY = '품질경영/CS활동/'
    URL_CS_CLAIM_FILE = '품질경영/CS클레임파일/'
    URL_CS_ACTIVITY_FILE = '품질경영/CS활동파일/'

    #### CS_V2 : 25-08-01 추가
    URL_CS_V2_CS_ACTIVITY = 'CS_V2/CS-Activity/'

    URL_CS_CLAIM_GET_ELEVATOR사 = '품질경영/CS관리/get_Elevator사/'
    URL_CS_CLAIM_GET_부적합유형 = '품질경영/CS관리/get_부적합유형/'


    #### Combo_lineEdit items
    고객사_Widget_items = ['현대','OTIS','TKE','기타']
    구분_Widget_items =  ['NE','MOD','기타']
    생산형태_Widget_items = ['정규생산','NCR','개발', '기타']
    Material_Widget_itmes = ['GI','POSMAC','SUS','해당없음','기타']
    Sample_소재Size_Widget_items = ['1.5T*150*150', '1.5T*300*300', '기타']	
    생산지시서_소재_Widget_items = ['GI','POSMAC','SUS', 'STS304 E/T', '해당없음','기타']
    생산지시서_치수_Widget_items = ['1.6T*1219*2550', '1.6T*1000*2550', '-', '기타']
    생산지시서_판금출하처_Widget_items = ['수신', '(판금업체)', '자사(판금)','기타']
    생산지시서_JAMB발주사_Widget_items = ['(주)이앤엠', '기타']

    Widget_망관리_의장종료_items = ['STM','CUBIC','GEN','일반','기타']
    Widget_망관리_할부치수_items = ['200mm','150mm','100mm','50mm','20mm','10mm','0','기타']
    Widget_망관리_품명_items = ['C/W','R/C','S/C','H/D','C/D','H/D,C/D','기타']
    Widget_망관리_망사_items = ['80','100','200','250','기타']
    Widget_망관리_사용구분_items = ['A-M(하이)','B-M(폴리)', '기타']

    ### Combo Custom
    Combo_작지_dashboard_날짜_Items = ['납기일', '작성일']
    Combo_작지_dashboard_고객사_Items = ['All', '현대','OTIS','TKE','기타']
    Combo_작지_dashboard_구분_Items = ['All', 'NE','MOD']
    Combo_작지_dashboard_GraphType_Items = ['Line', 'Bar', 'Pie']

    Combo_망관리_고객사_Items = ['All', '현대EL','OTIS','TKE','기타']
    Combo_망관리_의장종류_Items = ['All'] + Widget_망관리_의장종료_items
    # Combo_생지_form_생산형태_Items = ['정규', 'NCR', '개발', '기타']

    Combo_table_row_Items = ['25', '50', '75', '100']

    Combo_요청사항_구분_Items = ['오류 및 Bug','개선 및 성능향상','신규개발','기타']

    ###  FILE 확장자
    IMAGE확장자 = ['PNG','JPG','JPEG','GIF','BMP' ]
    PDF확장자 = ['PDF']
    EXCEL확장자 = ['xlsx', 'xls']


    ### hover 위치
    NO_CONTROL_POS = 30
    CONTROL_POS = 10

    ### 이벤트 버스 타입
    EVENT_BUS_TYPE_LOGIN = 'login'
    EVENT_BUS_TYPE_CPU_RAM_MONITOR = 'cpu_ram_monitor'
    EVENT_BUS_TYPE_WS_STATUS = 'ws_status'
    EVENT_BUS_TYPE_API_STATUS = 'api_status'

    EVENT_BUS_TYPE_MENU_SYSTEM_PASSWORD_CHANGE = 'system:password_change_requested'



    def __init__(self) ->None:
        if not self._initialized:
            # self.OS = platform.system()
            self.OS_choiceName = self._get_OS_choiceName()
            self.STATUS_CODE = self._get_STATUS_CODE()
            self._initialized = True

    @property
    def URI(self):
        return f'http://{self.API_SERVER}:{self.HTTP_PORT}/'    
    

    @property
    def URI_FASTAPI(self):
        return f'http://{self.API_SERVER}:{self.FASTAPI_PORT}/fastapi/'

    @property
    def URI_WS(self):
        return f'ws://{self.WS_SERVER}:{self.WS_PORT}/'
    
    def set_APP_권한_TOTAL(self, app_권한:list[dict]) -> None:
        self.APP_권한_TOTAL = app_권한
        self.APP_권한_TOTAL_MAP_ID_TO_APP = { obj.get('id'): obj for obj in self.APP_권한_TOTAL }
        self.APP_권한_TOTAL_MAP_DIV_NAME_TO_APP = { f"{obj.get('div')}:{obj.get('name')}" : obj for obj in self.APP_권한_TOTAL }

    def get_API_URL( self, app_ID:Optional[int]=None , app_info:Optional[dict[str,str]]=None ) -> Optional[str]:
        """ app_ID 또는 app_inf {'div':str, 'name':str} 가 포함된 dict를 받아서,  API URL을 반환 """
        def _get_url(app_dict:dict) -> str:
            url = f"{app_dict.get('api_uri')}{app_dict.get('api_url')}"
            if url.startswith('/'):
                url = url[1:]
            return url
        
        if app_ID is not None:
            app_dict = self.APP_권한_TOTAL_MAP_ID_TO_APP.get(app_ID, {})
            return _get_url(app_dict)
        elif app_info is not None:
            app_dict = self.APP_권한_TOTAL_MAP_DIV_NAME_TO_APP.get(f"{app_info.get('div')}:{app_info.get('name')}", {})
            return _get_url(app_dict)
        else:
            return None


    def set_APP_권한(self, app_권한:list[dict]) -> None:
        self.APP_권한 = app_권한
        self.APP_권한_MAP_ID_TO_APP = { obj.get('id'): obj for obj in self.APP_권한 }
        self._set_is_app_admin()
        self._set_is_table_config_admin()
        

    def set_base_dir(self, base_dir:str) -> None:
        self.BASE_DIR = base_dir

    def get_base_dir(self) -> str:
        return self.BASE_DIR
    
    def get_is_send_app_access_log(self) -> bool:
        """ ws로 app access log 전송 여부 """
        return True
        return not all( [ bool(self.USERID == 1)] )

    def _update_UserInfo(self, info:dict) :
        self.USERNAME = info.get('user_성명','')
        self.USERID = info.get('id',-1)
        self.MAIL_ID = info.get('user_mailid','')
        self.USER_INFO = info

    def _update_SERVER(self, server_url:str, port:str):
        self.API_SERVER = server_url
        self.WS_SERVER = server_url
        self.HTTP_PORT = port
        self.WS_PORT = str(int(port)-1)
        self.FASTAPI_PORT = str(int(port)-2)

    def _get_all_user(self) ->list[dict]:
        return self.ALL_USER
    
    def _get_user_info_by_name(self, user_성명) -> dict:
        for userinfo in self._get_all_user():
            if ( user_성명 == userinfo.get('user_성명') ):
                return userinfo
        return {}
    
    def _get_user_info(self, pk:int) -> dict:
        for userinfo in self._get_all_user():
            if ( pk == userinfo.get('id') ):
                return userinfo
        return {}
    
   

    def _get_username(self, id:Optional[int]=None) ->str:
        if id is None:
            return self.USERNAME
        else:
            return self._get_user_info(id).get('user_성명', '')
    
    def _get_userid(self) -> int:
        return self.USERID
    
    def _get_OS_choiceName(self) -> str:
        OS_dict = {
            'Windows':'W',
            'Linux':'L',
            'RPi' : 'R',
        }
        return OS_dict.get(self.OS)
    
    def _set_is_table_config_admin(self, is_table_config_admin:bool=None) -> bool:
        if is_table_config_admin is not None:
            self.IS_TABLE_CONFIG_ADMIN = is_table_config_admin
            return self.IS_TABLE_CONFIG_ADMIN
        for obj in self.APP_권한:
            if obj.get('div').lower() == 'config' and obj.get('name').lower() == 'table설정':
                self.IS_TABLE_CONFIG_ADMIN = True
                return
        self.IS_TABLE_CONFIG_ADMIN = False

    def _get_is_table_config_admin(self) -> bool:
        if self.IS_TABLE_CONFIG_ADMIN is None:
            self._set_is_table_config_admin()
        return self.IS_TABLE_CONFIG_ADMIN
    
    def _set_is_app_admin(self, is_app_admin:bool=None) -> bool:
        if is_app_admin is not None:
            self.IS_APP_ADMIN = is_app_admin
            return self.IS_APP_ADMIN
        for obj in self.APP_권한:

            if (obj.get('div').lower() == 'app설정' and 'app설정' in obj.get('name').lower()) or self.USERID == 1:
                self.IS_APP_ADMIN = True
                print ( "IS_APP_ADMIN : True" )
                return
        print ( "IS_APP_ADMIN : False" )
        self.IS_APP_ADMIN = False
    
    def _get_is_app_admin(self) -> bool:
        if self.IS_APP_ADMIN is None:
            self._set_is_app_admin()
        print ( "IS_APP_ADMIN : ", self.IS_APP_ADMIN )
        return self.IS_APP_ADMIN

    
    def _get_디자인의뢰_중요도(self):
        return 20
    
    def _get_작업지침서_중요도(self):
        return 10
    
    def _get_DateTimeFormat(self):
        return 'yyyy-MM-ddThh:mm:ss'
    
    def _get_DateFormat(self):
        return 'yyyy-mm-dd'
    
    def _get_TimeFormat(self):        
        return 'hh:mm:ss'
    
    def _get_HOLIDAYS(self) -> list[datetime.date]:
        if self.HOLIDAYS is None:
            self._set_HOLIDAYS(self._fetch_HOLIDAYS())
        return self.HOLIDAYS
    
    def _is_holiday(self, date:datetime.date) -> bool:
        return date in self._get_HOLIDAYS()

    def _set_HOLIDAYS(self, holidays:list[datetime.date]):
        self.HOLIDAYS = holidays
    
    def _fetch_HOLIDAYS(self) -> list[datetime.date]:
        _isok, _json = APP.API.getlist(f"{self.URL_일일보고_휴일}?page_size=0")
        if _isok:
            holidays = [datetime.datetime.strptime(obj.get('휴일'), '%Y-%m-%d').date() for obj in _json]
            return holidays
        else:
            print (f"Failed to fetch holidays: {_json}")
            return []
    
    def _get_URL_EL_INFO_한국정보(self) -> tuple[str, str, str]:
        """ return (api_uri, api_url, db_field_url)"""
        findedObj ={}
        for obj in self.APP_권한:
            if obj.get('div') == 'Elevator_Info' and obj.get('name') == '한국정보':
                findedObj = obj
                break
        return ( findedObj.get('api_uri'), findedObj.get('api_url') , findedObj.get('db_field_url') )
    

    def set_WS_URLS(self, ws_info:list[dict]) -> None:
        self.WS_URLS = ws_info
        self.WS_MAP_NAME_TO_URL = { ws.get('name'): f"{ws.get('group')}/{ws.get('channel')}/" for ws in ws_info }

    def get_WS_URLS(self) -> Optional[list[dict]]:
        return self.WS_URLS

    def get_WS_URL_by_name(self, name:str) -> Optional[str]:
        return self.WS_MAP_NAME_TO_URL.get(name, None)
    
    def get_WS_URLS_Init_Names(self) -> list[str]:
        return [ ws.get('name') for ws in self.WS_URLS if ws.get('is_init', False) ]
    
    def get_WS_URLS_Init_URLs(self) -> list[str]:
        return [ self.WS_MAP_NAME_TO_URL.get(ws.get('name')) 
                for ws in self.WS_URLS if ws.get('is_init', False) ]
    

    def set_menu_to_action(self, div:str, name:str, action:QAction):
        self.MAP_MENU_TO_ACTION[f"{div}:{name}"] = action

    def get_menu_to_action(self, div:str, name:str) -> QAction:
        return self.MAP_MENU_TO_ACTION.get(f"{div}:{name}", None)

    def _get_STATUS_CODE(self) -> dict:
        return  {
                100 : "CONTINUE",
                101 : "SWITCHING_PROTOCOLS",
                102 : "PROCESSING",
                103 : "EARLY_HINTS",
                200 : "OK",
                201 : "CREATED",
                202 : "ACCEPTED",
                203 : "NON_AUTHORITATIVE_INFORMATION",
                204 : "NO_CONTENT",
                205 : "RESET_CONTENT",
                206 : "PARTIAL_CONTENT",
                207 : "MULTI_STATUS",
                208 : "ALREADY_REPORTED",
                226 : "IM_USED",
                300 : "MULTIPLE_CHOICES",
                301 : "MOVED_PERMANENTLY",
                302 : "FOUND",
                303 : "SEE_OTHER",
                304 : "NOT_MODIFIED",
                305 : "USE_PROXY",
                306 : "RESERVED",
                307 : "TEMPORARY_REDIRECT",
                308 : "PERMANENT_REDIRECT",
                400 : "BAD_REQUEST",
                401 : "UNAUTHORIZED",
                402 : "PAYMENT_REQUIRED",
                403 : "FORBIDDEN",
                404 : "NOT_FOUND",
                405 : "METHOD_NOT_ALLOWED",
                406 : "NOT_ACCEPTABLE",
                407 : "PROXY_AUTHENTICATION_REQUIRED",
                408 : "REQUEST_TIMEOUT",
                409 : "CONFLICT",
                410 : "GONE",
                411 : "LENGTH_REQUIRED",
                412 : "PRECONDITION_FAILED",
                413 : "REQUEST_ENTITY_TOO_LARGE",
                414 : "REQUEST_URI_TOO_LONG",
                415 : "UNSUPPORTED_MEDIA_TYPE",
                416 : "REQUESTED_RANGE_NOT_SATISFIABLE",
                417 : "EXPECTATION_FAILED",
                421 : "MISDIRECTED_REQUEST",
                422 : "UNPROCESSABLE_ENTITY",
                423 : "LOCKED",
                424 : "FAILED_DEPENDENCY",
                425 : "TOO_EARLY",
                426 : "UPGRADE_REQUIRED",
                428 : "PRECONDITION_REQUIRED",
                429 : "TOO_MANY_REQUESTS",
                431 : "REQUEST_HEADER_FIELDS_TOO_LARGE",
                451 : "UNAVAILABLE_FOR_LEGAL_REASONS",
                500 : "INTERNAL_SERVER_ERROR",
                501 : "NOT_IMPLEMENTED",
                502 : "BAD_GATEWAY",
                503 : "SERVICE_UNAVAILABLE",
                504 : "GATEWAY_TIMEOUT",
                505 : "VERSION_NOT_SUPPORTED",
                506 : "VARIANT_ALSO_NEGOTIATES",
                507 : "INSUFFICIENT_STORAGE",
                508 : "LOOP_DETECTED",
                509 : "BANDWIDTH_LIMIT_EXCEEDED",
                510 : "NOT_EXTENDED",
                511 : "NETWORK_AUTHENTICATION_REQUIRED",
            }
    

Info_SW = Info_SW_Singleton()