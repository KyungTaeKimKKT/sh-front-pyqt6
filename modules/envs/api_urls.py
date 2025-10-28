from __future__ import annotations
from modules.envs.base_urls_single_tone import Base_URLS_Single_Tone
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class API_URLS(Base_URLS_Single_Tone):

    ### 현재 default URLS
    URL_API_SERVER_CHECK_NO_AUTH = 'api/users/connection-to-no-auth/'
    URL_API_SERVER_CHECK_AUTH = 'api/users/connection-to-auth/'
    
    #### RESOCRCES
    URL_RESOURCES_LOGIN_LOGO = 'config/resources/login-logo/'

    URL_UserInfo_by_Request = 'api/users/user-info-by-requestUser/'
    URL_User_ALL = 'api/users/users/'
    URL_User_PWD_Init= 'api/users/reset-user-password/'

    URL_Company = 'api/users/company/'

    URL_APP개발자 = "api/users/app권한-개발자/"
    URL_사용자별_APP권한 = "api/users/app권한-사용자별-권한/"

    APP권한_사용자_M2M = "api/users/app권한-사용자-m2m/"
    APP권한_사용자_M2M_Bulk = "api/users/app권한-사용자-m2m/bulk-generate/"

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


    URL_영업수주_금액_Summary_Api = '영업수주/영업수주_금액_Summary_Api/'

    URL_영업수주_관리 = '영업수주/관리/'

    URL_영업수주_일정 = '영업수주/일정관리/'
    URL_영업수주_일정_EXCEL_UPLOAD_BULK = '영업수주/일정관리/excel-upload-bulk/'
    URL_영업수주_금액 = '영업수주/금액관리/'
    URL_영업수주_금액_EXCEL_UPLOAD_BULK = '영업수주/금액관리/excel-upload-bulk/'

    URL_영업수주_자재내역_의장_Mapping = '영업수주/금액관리/자재내역_To_의장_Mapping/'
    URL_영업수주_자재내역_To_의장_Mapping_DB = '영업수주/자재내역_To_의장_Mapping_DB/'
    URL_DB_Field_영업수주_자재내역_To_의장_Mapping_DB = '영업수주/db-field-영업수주_자재내역_To_의장_Mapping_DB_View/'

    URL_Elevator_한국정보 = '/elevator-info/info/summary_wo설치일/'
    Elevator_한국정보_URL = '/elevator-info/info/summary_wo설치일/'
    URL_Elevator_한국정보_DOWNLOAD = '/elevator-info/info/summary-wo설치일-download/'
    URL_Elevator_승강기협회_DOWNLOAD = '/elevator-info/info/승강기협회-download/'

    ### db fileds view URL
    URL_DB_Field_Api_App권한_View = 'api/users/db-field-Api-App권한-View/'
    URL_DB_Field_User_View = 'api/users/db-field-User-View/'
    URL_DB_Field_공지사항_관리_View = '공지요청사항/db-field-공지사항_관리-View/'
    URL_DB_Field_요청사항_DB_View = '공지요청사항/db-field-요청사항_DB-View/'

    URL_DB_Field_요청사항_DB_View = '공지요청사항/db-field-요청사항_DB-View/'

    ##3 일일업무
    URL_DB_Field_개인_리스트_DB_View = '일일보고/db-field-개인_리스트_DB_View/'

    ### 영업MBO
    URL_영업MBO_사용자마감 = '영업mbo/사용자마감_apiview/'
    URL_영업MBO_관리자마감 = '영업mbo/관리자마감_apiview/'
    URL_영업MBO_Create_YEAR_GOAL = '영업mbo/년간목표생성_apiview/'

    ### HR평가
    URL_HR평가_평가설정DB = '/HR평가/평가설정_DB/'
    URL_HR평가_평가체계DB = '/HR평가/평가체계_DB/'
    URL_HR평가_CREATE_평가체계 = '/HR평가/평가체계_db_create/'
    URL_HR평가_COPY_CREATE_평가설정 = '/HR평가/평가설정_DB_Copy_Create/'

    URL_HR평가_역량평가사전_DB = '/HR평가/역량평가사전_DB/'
    URL_HR평가_역량항목_DB = '/HR평가/역량항목_DB/'
    URL_HR평가_평가시스템_구축 ='/HR평가/평가시스템_구축/'
    URL_HR평가_역량_평가_DB = '/HR평가/역량_평가_DB/'
    URL_HR평가_성과_평가_DB = '/HR평가/성과_평가_DB/'
    URL_HR평가_특별_평가_DB = '/HR평가/특별_평가_DB/'
    URL_HR평가_상급자평가_DB = '/HR평가/상급자평가_DB/'
    URL_HR평가_평가결과_DB = '/HR평가/평가결과_DB/'

    URL_HR평가_평가설정DB_Old = '/HR평가/평가설정DB_Old/'

    URL_HR평가_상급자평가_INFO = '/HR평가/상급자평가_DB_API_View/'
    URL_HR평가_CHECK_평가점수 = '/HR평가/check_평가점수/'
    
    URL_DB_Field_역량_평가_DB = '/HR평가/db-field-역량_평가_DB_View/'
    URL_DB_Field_성과_평가_DB = '/HR평가/db-field-성과_평가_DB_View/'
    URL_DB_Field_특별_평가_DB = '/HR평가/db-field-특별_평가_DB_View/'

    URL_DB_Field_상급자평가_개별 = '/HR평가/db-field-상급자평가_개별_DB_View/'
    URL_DB_Field_상급자평가_종합 = '/HR평가/db-field-상급자평가_종합_DB_View/'

    URL_차량관리_기준정보 = '/차량관리/차량관리_기준정보/'
    URL_차량관리_차량LIST_BY_USER = '/차량관리/차량관리_차량번호_사용자_API_View/'

    ### 샘플관리
    URL_샘플관리_PROCESS_DB = '/샘플관리/샘플관리-process/'
    URL_DB_Field_샘플관리_PROCESS_DB = '/샘플관리/db-field-샘플관리_Process_View/'

    URL_샘플관리_첨부FILE = '/샘플관리/샘플관리-첨부file/'
    URL_샘플관리_완료FILE = '/샘플관리/샘플관리-완료file/'

    ### 작업지침
    URL_작업지침_이력조회 = '/작업지침/이력조회/'
    URL_작업지침_PROCESS_DB = '/작업지침/작업지침-process/'

    URL_작업지침_RENDERING_FILE = '/작업지침/rendering-file/'
    URL_작업지침_첨부_FILE = '/작업지침/첨부-file/'
    URL_작업지침_의장도 = '/작업지침/의장도/'

    URL_DB_Field_작업지침_PROCESS_DB = '/작업지침/db-field-작업지침_의장table_View/'

    #### 생산지시서
    URL_일일보고_휴일 = '/일일보고/휴일등록/'
    URL_생산지시_HTM_Table = '/생산지시서/HTM-table/'
    URL_생산지시_도면정보_Table = '/생산지시서/도면정보-table/'

    URL_생산지시_SPG = '생산지시서/spg/'
    URL_SPG_TABLE = '생산지시서/spg-table/'
    URL_TAB_MADE = '생산지시서/tab-made-file/'

    URL_DB_Field_HTM_Table = '/생산지시서/db-field-생산지시_의장table_View/'
    URL_DB_Field_도면정보_Table = '/생산지시서/db-field-생산지시_도면정보table_View/'
    URL_DB_Field_SPG_Table = '/생산지시서/db-field-생산지시_spg_table_View/'

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

    URL_CS_CLAIM_GET_ELEVATOR사 = '품질경영/CS관리/get_Elevator사/'
    URL_CS_CLAIM_GET_부적합유형 = '품질경영/CS관리/get_부적합유형/'

    URL_DB_Field_CS_ACTIVITY = '품질경영/db-field-CS_Activity_View/'

    




api_urls = API_URLS()