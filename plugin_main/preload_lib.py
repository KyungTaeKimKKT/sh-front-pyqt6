import threading
import concurrent.futures
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from typing import Dict, List, Callable, Any, Optional
import time

from info import Info_SW as INFO

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class PreloadLib:
    """백그라운드에서 라이브러리를 로드하는 클래스"""
    
    def __init__(self, preload_libs:list[str]=INFO.PRELOAD_LIBS):
        self.preload_libs = preload_libs
        self.executor = None
        self.futures = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.loaded_libs = {}  # 로드된 라이브러리 저장
    
    def start(self, libs_to_load: Optional[Dict[str, Callable]] = None):
        """라이브러리 로드 시작
        
        Args:
            libs_to_load: 라이브러리 이름과 로드 함수의 딕셔너리. None이면 preload_libs 사용
        """
        with self.lock:
            if self.is_running:
                return
            
            self.is_running = True
            self.executor = concurrent.futures.ThreadPoolExecutor()
            self.futures = {}
            
            # libs_to_load가 None이면 preload_libs에서 라이브러리 로드
            if libs_to_load is None:
                libs_to_load = {}
                for lib_name in self.preload_libs:
                    libs_to_load[lib_name] = lambda lib=lib_name: self._import_lib(lib)
            
            for lib_name, load_func in libs_to_load.items():
                self.futures[lib_name] = self.executor.submit(self._load_lib, lib_name, load_func)
    
    def _import_lib(self, lib_name: str):
        """문자열 이름으로 라이브러리 임포트
        
        Args:
            lib_name: 임포트할 라이브러리 이름
            
        Returns:
            임포트된 라이브러리 모듈
        """
        try:
            import importlib
            return importlib.import_module(lib_name)
        except ImportError as e:
            logger.error(f"라이브러리 '{lib_name}' 임포트 실패: {str(e)}")
            logger.error(f"{traceback.format_exc()}")
            raise ImportError(f"라이브러리 '{lib_name}' 임포트 실패: {str(e)}")

    def _load_lib(self, lib_name: str, load_func: Callable) -> Any:
        """라이브러리 로드 함수 실행 및 결과 저장
        
        Args:
            lib_name: 로드할 라이브러리 이름
            load_func: 라이브러리를 로드하는 함수
            
        Returns:
            로드된 라이브러리 객체
        """
        start_time = time.perf_counter()
        # logger.debug(f"라이브러리 '{lib_name}' 로드 시작")
        
        try:
            lib = load_func()
            self.loaded_libs[lib_name] = lib
            event_bus.publish_trace_time(                               
								{ 'action': f"lib_load_{lib_name} : LOADED", 
								'duration': time.perf_counter() - start_time }
                                )
            
            return lib
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"라이브러리 '{lib_name}' 로드 실패: {str(e)}, {elapsed_time:.2f}초 소요")
            logger.error(f"{traceback.format_exc()}")
                    
            raise
    
    def stop(self):
        """모든 라이브러리 로드 작업 중단"""
        with self.lock:
            if not self.is_running:
                return
            
            # 모든 미완료 작업 취소
            for lib_name, future in self.futures.items():
                if not future.done():
                    future.cancel()
            
            self.executor.shutdown(wait=False)
            self.is_running = False
    
    def get_status(self) -> Dict[str, str]:
        """각 라이브러리의 로드 상태 반환"""
        status = {}
        with self.lock:
            for lib_name, future in self.futures.items():
                if future.done():
                    try:
                        future.result()  # 예외 확인
                        status[lib_name] = "completed"
                    except Exception:
                        status[lib_name] = "failed"
                elif future.cancelled():
                    status[lib_name] = "cancelled"
                else:
                    status[lib_name] = "running"
        return status
    
    def wait_all(self, timeout: Optional[float] = 5.0) -> bool:
        """모든 라이브러리 로드가 완료될 때까지 대기
        
        Args:
            timeout: 최대 대기 시간(초). None이면 무한정 대기
            
        Returns:
            모든 작업이 성공적으로 완료되었는지 여부
        """
        if not self.is_running:
            return False
            
        start_time = time.perf_counter()
        all_done = False
        
        while not all_done:
            with self.lock:
                all_done = all(future.done() for future in self.futures.values())
            
            if all_done:
                break
                
            if timeout is not None and time.perf_counter() - start_time > timeout:
                completed_count = sum(1 for future in self.futures.values() if future.done())
                total_count = len(self.futures)
                logger.warning(f"라이브러리 로드 타임아웃: {timeout}초 초과 ({completed_count}/{total_count} 완료)")
                return False
                
            time.sleep(0.1)
        
        # 모든 작업이 성공적으로 완료되었는지 확인
        with self.lock:
            success_count = sum(1 for future in self.futures.values() 
                               if not future.cancelled() and future.exception() is None)
            total_count = len(self.futures)
            all_success = success_count == total_count
        
        # 총 소요 시간 계산 및 로깅
        total_time = time.perf_counter() - start_time
        event_bus.publish_trace_time(                               
							{ 'action': f"모든 라이브러리 로드 완료: {success_count}/{total_count} 성공", 
							'duration': total_time }
                            )
        
        return all_success