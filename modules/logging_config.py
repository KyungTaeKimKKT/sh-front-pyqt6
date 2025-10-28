from __future__ import annotations
from typing import TYPE_CHECKING
import os
import sys
import logging
import logging.handlers
import traceback
import platform
from datetime import datetime
import pathlib

from info import Info_SW as INFO
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

if TYPE_CHECKING:
    from main import MainWindow

LOGGING_LEVEL = logging.ERROR
CONSOLE_LEVEL = logging.ERROR

class EventBusLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            event_bus.publish(GBus.TRACE_LOGGER, {
                'Level': record.levelname,
                'Action': getattr(record, 'action', record.getMessage()),  # action이 있으면, 없으면 message
                'Data': log_entry
            })
        except Exception as e:
            print(f"[EventBusLogHandler Error] {e}")

# ColoredFormatter 클래스 정의
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[91m\033[1m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.COLORS['RESET']}"

def get_base_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller 실행 파일
        return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        # 일반 Python 실행
        return INFO.get_base_dir()
        # return os.path.dirname(os.path.abspath(__file__))

def makeDir(path: str = "debug") -> str:
    base_dir = get_base_dir()
    full_path = os.path.join(base_dir, path)
    pathlib.Path(full_path).mkdir(parents=True, exist_ok=True)
    return full_path

def configure_app_logging(is_dev=False):
    """
    애플리케이션의 로깅 설정을 구성합니다.
    
    Args:
        is_dev (bool): 개발 모드 여부
    """
    try:
        print(f'로깅 설정 - 개발 모드: {is_dev}')
        
        # 로그 디렉토리 생성
        logs_dir = makeDir("logs")
            
        # 로그 파일 경로 설정
        error_log_file = os.path.join(logs_dir, 'error.log')
        app_log_file = os.path.join(logs_dir, 'app.log')
        
        # 포맷터 설정
        verbose_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s')
        colored_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s')
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.handlers = []  # 기존 핸들러 제거
        
        if is_dev:
            root_logger.setLevel(logging.DEBUG)
            
            # 파일 핸들러 (에러 로그)
            # error_file_handler = logging.FileHandler(error_log_file)
            # error_file_handler.setLevel(logging.ERROR)
            # error_file_handler.setFormatter(verbose_formatter)
            # root_logger.addHandler(error_file_handler)
            
            # # 파일 핸들러 (앱 로그)
            # app_file_handler = logging.handlers.TimedRotatingFileHandler(
            #     app_log_file, when='midnight', interval=1, backupCount=30)
            # app_file_handler.setLevel(logging.DEBUG)
            # app_file_handler.setFormatter(verbose_formatter)
            # root_logger.addHandler(app_file_handler)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(colored_formatter)
            root_logger.addHandler(console_handler)
            
            print(f'로깅 설정 완료: {logs_dir}')
        else:
            # 프로덕션 모드일 때: 에러만 기록
            root_logger.setLevel(logging.ERROR)
            
            # 파일 핸들러 (에러 로그)
            # error_file_handler = logging.FileHandler(error_log_file)
            # error_file_handler.setLevel(logging.ERROR)
            # error_file_handler.setFormatter(verbose_formatter)
            # root_logger.addHandler(error_file_handler)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_handler.setLevel(CONSOLE_LEVEL)
            console_handler.setFormatter(colored_formatter)
            root_logger.addHandler(console_handler)
            
        return True
    except Exception as e:
        print(f"로깅 설정 오류: {e}")
        # 기본 로깅 설정으로 폴백
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return False

# 플러그인 모듈을 위한 로거 생성 함수 개선
def get_plugin_logger(plugin_name=None):
    """
    플러그인 모듈을 위한 로거를 생성합니다.
    
    Args:
        plugin_name (str, optional): 플러그인 또는 모듈 이름. 
                                    None이면 호출한 모듈의 이름을 자동으로 사용합니다.
        
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    try:
        # 호출자 모듈 이름 자동 감지
        if plugin_name is None:
            import inspect
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            if module:
                # 모듈 전체 경로에서 파일 이름만 추출 (확장자 제외)
                plugin_name = os.path.splitext(os.path.basename(module.__file__))[0]
            else:
                plugin_name = "unknown_plugin"
        
        # 로그 디렉토리 확인
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # 플러그인 로그 파일 경로
        plugin_log_file = os.path.join(logs_dir, f'{plugin_name}.log')
        
        # 플러그인 로거 생성
        logger = logging.getLogger(plugin_name)
        
        # 이미 핸들러가 설정되어 있으면 추가하지 않음
        if logger.handlers:
            return logger
        
        # 개발 모드 확인 (INFO 모듈 사용)
        try:
            from info import Info_SW as INFO
            is_dev = INFO.IS_DEV
        except ImportError:
            is_dev = False  # 기본값
        
        # 로거 레벨 설정
        logger.setLevel(logging.DEBUG if is_dev else LOGGING_LEVEL)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 파일 핸들러 추가
        # file_handler = logging.handlers.TimedRotatingFileHandler(
        #     plugin_log_file, when='midnight', interval=1, backupCount=7)
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

        # 1. 로거에 EventBusHandler 추가
        event_bus_handler = EventBusLogHandler()
        event_bus_handler.setFormatter(logging.Formatter("%(message)s"))  # Data에 들어가는건 메시지 원본
        logger.addHandler(event_bus_handler)
        
        # 개발 모드에서는 콘솔 핸들러도 추가
        if is_dev:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(console_handler)
        
        else : 
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(console_handler)
        
        # 상위 로거로 전파하지 않음
        logger.propagate = False
        
        return logger
    except Exception as e:
        print(f"플러그인 로거 생성 오류: {e}")
        # 기본 로거 반환
        return logging.getLogger(plugin_name or "fallback_logger")

# 탭 모듈을 위한 로거 생성 함수
def get_tab_logger(div_name, app_name):
    """
    탭 모듈을 위한 로거를 생성합니다.
    
    Args:
        div_name (str): 탭 구분 이름
        app_name (str): 앱 이름
        
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    # 탭 이름 정규화
    tab_name = f"tab_{div_name}_{app_name}".replace(' ', '_').replace('(', '').replace(')', '')
    return get_plugin_logger(tab_name)

# 로그 레벨 문자열을 로깅 상수로 변환하는 함수
def get_log_level(level_str):
    """
    문자열 로그 레벨을 로깅 상수로 변환합니다.
    
    Args:
        level_str (str): 로그 레벨 문자열 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        
    Returns:
        int: 로깅 상수 값
    """
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

# 로그 파일 정리 함수
def clean_log_files(max_days=30):
    """
    오래된 로그 파일을 정리합니다.
    
    Args:
        max_days (int): 보관할 최대 일수
    """
    import glob
    import time
    
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        return
    
    # 현재 시간에서 max_days일 이전 시간 계산
    cutoff_time = time.time() - (max_days * 24 * 60 * 60)
    
    # 로그 파일 검색
    log_files = glob.glob(os.path.join(logs_dir, '*.log.*'))
    
    for log_file in log_files:
        try:
            # 파일 수정 시간 확인
            file_mod_time = os.path.getmtime(log_file)
            if file_mod_time < cutoff_time:
                os.remove(log_file)
                print(f"오래된 로그 파일 삭제: {log_file}")
        except Exception as e:
            print(f"로그 파일 정리 중 오류: {e}")

def get_platform_info():
    """시스템 플랫폼 정보를 반환합니다."""
    system = platform.system()
    version = platform.version()
    release = platform.release()
    architecture = platform.architecture()[0]
    return f"{system} {version} {release} {architecture}"

def send_error_to_server(error_message:str, traceback_str, file_name=None, **kwargs):
    """
    서버로 에러 메시지를 전송합니다.
    
    Args:
        error_message: 에러 메시지
        traceback_str: 에러 트레이스백
        file_name: 에러 관련 파일 이름 (옵션)
        **kwargs: 추가적인 키워드 인자
    """
    try:
        # 이 함수는 main.py에서 구현된 API 및 INFO 객체에 의존하므로
        # 런타임에 필요한 모듈을 임포트합니다
        from info import Info_SW as INFO
        from config import Config as APP
        
        send_data = { 
            'user_fk': INFO.USERID, 
            'error_message': error_message, 
            'app_fk': INFO.CURRENT_APP_FK if 'app_fk' not in kwargs else kwargs.get('app_fk'),
            'error_traceback': traceback_str, 
            'OS': get_platform_info(), 
            '버젼': INFO.Version if '버젼' not in kwargs else kwargs.get('버젼')
        }
        
        # 필요한 필드 검증
        if send_data['app_fk'] == -1:
            del send_data['app_fk']
        if send_data['user_fk'] is None or send_data['user_fk'] == -1:
            del send_data['user_fk']
        
        # 비디오 파일 처리
        send_files = None
        if file_name and os.path.exists(file_name):
            with open(file_name, 'rb') as video_file:
                send_files = {'file': video_file}
                _isOk, _json = APP.API.post(INFO.URL_ERROR_LOG, send_data, files=send_files)
                if _isOk:
                    logging.info(f"에러 비디오 파일 전송 완료: {file_name}")
                    # 파일 전송 후 삭제 : ==> app시작시 삭제로 변경
                    # try:
                    #     os.remove(file_name)
                    #     logging.info(f"에러 비디오 파일 삭제 완료: {file_name}")
                    # except Exception as e:
                    #     logging.error(f"에러 비디오 파일 삭제 실패: {file_name}, 오류: {e}")
        else:
            _isOk, _json = APP.API.post(INFO.URL_ERROR_LOG, send_data)
        
        if not _isOk:
            logging.error(f"Error sending error message to server: {_json}")
    except Exception as e:
        logging.error(f"Error sending error message to server: {e}")

def handle_screen_recorder(main_window, error_message, traceback_str):
    """
    스크린 레코더를 처리하고 에러를 서버로 전송합니다.
    
    Args:
        main_window: 메인 윈도우 객체
        error_message: 에러 메시지
        traceback_str: 에러 트레이스백
    """
    try:
        if main_window is not None and hasattr(main_window, 'screen_recorder') and main_window.screen_recorder is not None:
            fName = main_window.screen_recorder.stop()
            
            if fName is not None and os.path.exists(fName) and os.path.getsize(fName) > 0:
                send_error_to_server(error_message, traceback_str, file_name=fName)
            else:
                send_error_to_server(error_message, traceback_str)
        else:
            send_error_to_server(error_message, traceback_str)
    except Exception as e:
        logging.error(f"스크린 레코더 처리 중 오류 발생: {e}")
        send_error_to_server(error_message, traceback_str)


def handle_screen_recorder_V2(main_window:MainWindow|None=None, error_message:str|None=None, traceback_str:str|None=None):
    """
    스크린 레코더를 처리하고 에러를 서버로 전송합니다.
    
    Args:
        main_window: 메인 윈도우 객체
        error_message: 에러 메시지
        traceback_str: 에러 트레이스백
    """
    try:
        if main_window is not None:
            if ( _method := getattr(main_window, 'save_recording', None) ) and callable( _method ):
                # 녹화 저장 시도
                try:
                    main_window.save_recording()
                except Exception as e:
                    logging.error(f"save_recording 실행 중 예외 발생: {e}")

                # 녹화 파일 처리
                if (fName := getattr ( main_window, 'debug_recording_path', None )) is not None:
                    if fName and os.path.exists(fName) and os.path.getsize(fName) > 0:
                        send_error_to_server(error_message, traceback_str, file_name=fName)
                        # try:
                        #     os.remove(fName)
                        # except Exception as e:
                        #     logging.warning(f"crash 영상 삭제 실패: {e}")
                        return
        send_error_to_server(error_message, traceback_str)
    except Exception as e:
        logging.error(f"스크린 레코더 처리 중 오류 발생: {e}")
        send_error_to_server(error_message, traceback_str)

def log_exception(exc_type, exc_value, exc_traceback):
    """
    예외 발생 시 로깅합니다.
    
    Args:
        exc_type: 예외 타입
        exc_value: 예외 값
        exc_traceback: 예외 트레이스백
    
    Returns:
        tuple: (error_message, traceback_str)
    """
    error_message = f"{exc_type.__name__}: {exc_value}"
    traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"Error: {error_message}\nTraceback: {traceback_str}")
    return error_message, traceback_str

def setup_exception_handlers():
    """
    애플리케이션의 예외 처리기를 설정합니다.
    """
    def log_exception_handler(exc_type, exc_value, exc_traceback):
        """예외 발생 시 로깅하고 처리합니다."""
        print("log_exception_handler 함수가 호출되었읍니다!")  # 디버깅용
        
        # 로깅 설정 확인
        from info import Info_SW as INFO
        configure_app_logging(INFO.IS_DEV)
        
        # 예외 로깅
        error_message, traceback_str = log_exception(exc_type, exc_value, exc_traceback)
        
        # 개발 모드에서는 바로 종료
        if INFO.IS_DEV:
            sys.exit(1)
        
        # 스크린 레코더 처리 및 에러 전송
        handle_screen_recorder_V2 (INFO.MAIN_WINDOW, error_message, traceback_str)
        
        sys.exit(1)

    def qt_exception_hook(exctype, value, traceback):
        """Qt 예외 처리 훅"""
        print(f"Qt Exception Hook: {exctype.__name__}: {value}")
        log_exception_handler(exctype, value, traceback)
        sys.__excepthook__(exctype, value, traceback)

    # 예외 처리기 설정
    sys.excepthook = qt_exception_hook
    
    return qt_exception_hook  # 필요시 참조를 반환 