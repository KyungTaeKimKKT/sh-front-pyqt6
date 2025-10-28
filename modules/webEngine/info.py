import platform
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Info_SW:
    URI = 'http://192.168.7.108:9999/' 
    PARAM_NO_PAGE = '?page_size=0'

    APP_Name = 'Shinwoo APP'
     ### 'U': python source file : Update 용 ==> 배포되면 update 할 것인지 물어봄 :
     ### 'I' : windows EXE Install file ==> 배포되면 update함.
    종류 = 'U'     
    Version = 0.16
    PID_Update:int = None
    PID_Main:int = None

    ### googleMap api key
    GOOGLE_MAP_API_KEY = 'AIzaSyD2MaeSd0PSAjuK1zcnkEdyryVYdL6oGFA'
    공공DATA_serviceKey = "VOAgXeeBTZflpY2X2s%2BCzGoqgi2McJlHnzVYD1DGh%2Fux8X%2BIo1OjaglLPkLSLLKN4lE5kmZRA30XIBjzV5XTXA%3D%3D"

    ### JWT관련 
    SERVER_ACCESS_TOKEN_LIFETIME = 45 ### 분
    JWT_REFRESH_TIMER = 1000*60*10 ### MAIN TIMER로 구동 1000msec * 60초 * 분 
    REFRESH_기준 = int( JWT_REFRESH_TIMER  / 1000 *1.5)   # api.py에서 기준으로 사용
    AUTH_URL = URI +'api-auth/jwt/'
    REFRESH_URL = URI+'api-auth/jwt/refresh/'
    
    USERNAME = ''
    USERID = -1
    MAIL_ID = ''

    OS = platform.system()

    CONFIG_개인_FNAME = 'config_개인.json'
    # OS_choiceName = self._get_OS_choiceName()

    디자인의뢰_중요도 = 20
    작업지침서_중요도 = 20

    
    DateFormat = '%Y-%m-%d'
    DateFormat_short = '%y-%m-%d'
    TimeFormat = '%H:%M:%S'
    DateTimeFormat= DateFormat +'T'+TimeFormat

    ### URLS
    URL_사용자별_APP권한 = "api/users/app사용자/"
    API_Update_URL = "release/배포리스트/"
    Elevator_한국정보_URL = '/elevator-info/info/summary_wo설치일/'

    SPG_URL = '생산지시/spg/'
    SPG_FILE_URL = '생산지시/spg-file/'
    TAB_Made_file_URL = '생산지시/tab-made-file/'

    의장도_URL = '작업지침/의장도/'
    의장도_FILE_URL ='작업지침/의장도file/'

    작지배포_URL = '작업지침/배포/'
    NCR배포_URL = '품질경영/NCR배포/'

    #### Combo_lineEdit items
    고객사_Widget_items = ['현대','OTIS','TKE','기타']
    구분_Widget_items =  ['NE','MOD','기타']
    생산형태_Widget_items = ['정규생산','NCR','개발', '기타']
    Material_Widget_itmes = ['GI','POSMAC','SUS','해당없음','기타']
    Sample_소재Size_Widget_items = ['1.5T*150*150', '1.5T*300*300', '기타']	
    생산지시서_소재_Widget_items = ['GI','POSMAC','SUS', 'STS304 E/T', '해당없음','기타']
    생산지시서_치수_Widget_items = ['1.6T*1219*2550', '1.6T*1000*2550', '-', '기타']
    생산지시서_판금출하처_Widget_items = ['수신', '(판금업체)', '자사(판금)','기타']

    ### Combo Custom
    Combo_작지_dashboard_날짜_Items = ['납기일', '작성일']
    Combo_작지_dashboard_고객사_Items = ['All', '현대','OTIS','TKE','기타']
    Combo_작지_dashboard_구분_Items = ['All', 'NE','MOD']
    Combo_작지_dashboard_GraphType_Items = ['Line', 'Bar', 'Pie']

    # Combo_생지_form_생산형태_Items = ['정규', 'NCR', '개발', '기타']

    Combo_table_row_Items = ['25', '50', '75', '100']

    ###  FILE 확장자
    IMAGE확장자 = ['PNG','JPG','JPEG','GIF','BMP' ]
    PDF확장자 = ['PDF']
    EXCEL확장자 = ['xlsx', 'xls']

    STATUS_CODE = {
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

    def __init__(self) ->None:
        # self.OS = platform.system()
        self.OS_choiceName = self._get_OS_choiceName()
        self.STATUS_CODE = self._get_STATUS_CODE()

    def _get_username(self) ->str:
        return self.USERNAME
    
    def _get_userid(self) -> int:
        return self.USERID
    
    def _get_OS_choiceName(self) -> str:
        OS_dict = {
            'Windows':'W',
            'Linux':'L',
            'RPi' : 'R',
        }
        return OS_dict.get(self.OS)
    
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