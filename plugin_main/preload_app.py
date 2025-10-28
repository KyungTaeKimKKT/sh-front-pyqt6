from __future__ import annotations
import importlib
import sys
import time
import traceback
import threading
import os
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from copy import deepcopy
from info import Info_SW as INFO
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger("preload_app")

class AppPreloader:
    """ evnet bus로, app권한 url 구독함 (실제 data는 INFO.app에 저장되고, action:str만 보냄... app권한 초기화 시 발생)
    앱 모듈을 사전에 로드하여 캐싱하는 클래스
    """
    
    def __init__(self):
        logger.info(f"AppPreloader : __init__ :  앱 사전 로드 초기화")
        self.loaded_modules = {}  # 로드된 모듈 캐시
        self.loaded_classes:dict[str, type] = {}  # 로드된 클래스 캐시
        self.event_bus = event_bus
        self.event_bus.subscribe(
            INFO.get_WS_URL_by_name('app_권한'), 
            self._handle_app_event
        )
        # CPU 코어 수에 기반한 worker 수 설정 (I/O 바운드 작업이므로 코어 수의 2배)
        self.max_workers = max(4, os.cpu_count() * 2) if os.cpu_count() else 8
        logger.info(f"병렬 처리 worker 수: {self.max_workers}")

    def _handle_app_event(self, action:str):
        """이벤트 핸들러 - 별도 스레드에서 preload_apps 실행"""
        # UI 차단을 방지하기 위해 별도 스레드에서 실행
        threading.Thread(target=self.preload_apps, args=(action,), daemon=True).start()

    def preload_apps(self, action:str):
        """모든 메뉴에서 앱 목록을 가져와 사전 로드"""
        self.app권한 = deepcopy(INFO.APP_권한)
        logger.info(f"앱 사전 로드 시작 : {len(self.app권한)}개")
        start_time = time.time()
        
        total_apps = len(self.app권한)
        loaded_apps = 0
        no_module_errors = 0
        other_errors = 0
        
        # ThreadPoolExecutor를 사용하여 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 각 앱에 대한 Future 생성
            future_to_app = {}
            for app_dict in self.app권한:
                try:
                    divName, appName = app_dict.get('div'), app_dict.get('name')
                    수정divName = divName.replace('(','_').replace(')','_')
                    수정appName = appName.replace('(','_').replace(')','_')
                    
                    # 앱 클래스 로드 작업 제출
                    future = executor.submit(
                        self._preload_app_class, 
                        app_dict.get('id'), 
                        수정divName, 
                        수정appName
                    )
                    future_to_app[future] = app_dict
                except Exception as e:
                    # logger.error(f"앱 작업 제출 실패: {app_dict.get('표시명_항목')}, 오류: {str(e)}")
                    other_errors += 1
            
            # 완료된 작업 처리
            for future in as_completed(future_to_app):
                app_dict = future_to_app[future]
                try:
                    result, error_type = future.result()
                    if result:
                        loaded_apps += 1
                    elif error_type == "no_module":
                        no_module_errors += 1
                    else:
                        other_errors += 1
                except Exception as e:
                    # logger.error(f"앱 로드 결과 처리 실패: {app_dict.get('표시명_항목')}, 오류: {str(e)}")
                    other_errors += 1
        
        elapsed_time = time.time() - start_time
        logger.info(f"앱 사전 로드 완료: {loaded_apps}/{total_apps} 앱 로드됨, 총 소요 시간: {elapsed_time:.2f}초")
        logger.info(f"실패 내역: 모듈 없음 {no_module_errors}개, 기타 오류 {other_errors}개")
        
        # 로드된 클래스를 INFO에 저장
        INFO.LOADED_APP_CLASSES = self.loaded_classes
        
        # 로드 완료 이벤트 발행 (다른 컴포넌트가 이를 구독할 수 있음)
        self.event_bus.publish("app_preload_complete", {"loaded": loaded_apps, "total": total_apps})
    
    def _preload_app_class(self, app_id: int, divName: str, appName: str) -> tuple[bool, str]:
        """특정 앱 클래스를 사전 로드, 성공 시 (True, ""), 실패 시 (False, 오류유형) 반환"""
        postfix = '__for_Tab'
        default_appName = f"App{postfix}"
        
        # 모듈 이름 생성
        module_name = f"{divName}_{appName}"
        class_name = f'{appName}{postfix}'
        full_module_name = f"modules.PyQt.Tabs.{divName}.{module_name}"
        
        # 모듈 로드 시간 측정
        module_load_start = time.time()
        
        try:
            # 모듈 로드
            if full_module_name not in self.loaded_modules:
                module = importlib.import_module(full_module_name)
                self.loaded_modules[full_module_name] = module
            else:
                module = self.loaded_modules[full_module_name]
            
            # 클래스 로드
            class_key = f"AppID.{str(app_id)}"
            if class_key not in self.loaded_classes:
                try:
                    app_class = getattr(module, class_name)
                    self.loaded_classes[class_key] = app_class
                except AttributeError:
                    # 기본 앱 클래스 시도
                    default_class_key = f"{full_module_name}.{default_appName}"
                    if default_class_key not in self.loaded_classes:
                        app_class = getattr(module, default_appName)
                        self.loaded_classes[default_class_key] = app_class
            
            module_load_time = time.time() - module_load_start
            if module_load_time > 0.5:  # 0.5초 이상 걸리는 모듈 로깅
                if module_name == 'App설정_App설정_개발자':
                    logger.warning(f"모듈 로드 시간: {module_load_time:.2f}초, 모듈: {module_name}")
            
            return True, ""
            
        except Exception as e:
            module_load_time = time.time() - module_load_start
            error_type = "no_module" if 'No module named' in str(e) else "other"
            if module_name == 'App설정_App설정_개발자':
            
                logger.error(f"모듈 로드 실패: {full_module_name}, 시간: {module_load_time:.2f}초, 오류: {str(e)}")
                logger.error(traceback.format_exc())
                if error_type != "no_module":
                    logger.error(traceback.format_exc())
                
            return False, error_type
    
    def get_app_class(self, divName: str, appName: str) -> Optional[Any]:
        """캐시된 앱 클래스 반환"""
        postfix = '__for_Tab'
        default_appName = f"App{postfix}"
        
        # 모듈 이름 생성
        module_name = f"{divName}_{appName}"
        class_name = f'{appName}{postfix}'
        full_module_name = f"modules.PyQt.Tabs.{divName}.{module_name}"
        
        # 클래스 반환
        class_key = f"{full_module_name}.{class_name}"
        if class_key in self.loaded_classes:
            return self.loaded_classes[class_key]
        
        # 기본 앱 클래스 시도
        default_class_key = f"{full_module_name}.{default_appName}"
        if default_class_key in self.loaded_classes:
            return self.loaded_classes[default_class_key]
        
        # 캐시에 없으면 동적 로드 시도
        try:
            result, _ = self._preload_app_class(0, divName, appName)
            if result:
                return self.get_app_class(divName, appName)
            return None
        except Exception:
            return None

# # 싱글톤 인스턴스
# app_preloader = AppPreloader()

# def initialize_app_preloader():
#     """앱 프리로더 초기화 및 사전 로드 실행"""
#     app_preloader.preload_apps()

# def get_app_class(divName: str, appName: str) -> Optional[Any]:
#     """앱 클래스 가져오기"""
#     return app_preloader.get_app_class(divName, appName) 