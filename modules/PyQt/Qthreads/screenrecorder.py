import cv2
import numpy as np
import time, os
from mss import mss
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ScreenRecorder(QThread):
    """
    QThread를 상속받은 화면 녹화 클래스
    지정된 QWidget의 화면을 캡처하여 비디오로 저장합니다.
    """
    finished = pyqtSignal(str)  # 녹화 완료 시 output_file 경로를 전달하는 시그널

    def __init__(self, target_window: QWidget, output_file: str='recording.avi',  parent=None, **kwargs):
        """
        초기화 함수
        
        kwargs:            
            target_window (QWidget): 녹화할 대상 윈도우
            output_file (str): 녹화 파일 경로
            parent: 부모 객체
            fps: 프레임 속도
        """
        super().__init__(parent)
        self.output_file = output_file
        self.target_window = target_window
        self.is_recording = False
        self.fps = kwargs.get('fps', 10)
        # self.sct = mss()
        # fourcc 변수 초기화 추가
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.frames = []
        self.max_frames = self.fps * 30  # 30초 분량의 최대 프레임 수

    
    def run(self):
        """스레드 실행 시 호출되는 메서드. 화면 녹화를 수행합니다."""
        self.is_recording = True
        # 스레드 내에서 mss 인스턴스 생성
        self.sct = mss()

        # 초기 모니터 설정
        self.update_monitor_info()   

        self.out = cv2.VideoWriter(self.output_file, self.fourcc, self.fps, 
                        (self.monitor['width'], self.monitor['height']))   
       
        try:
            
            while self.is_recording:
                if len(self.frames) > self.max_frames:

                    self.frames.pop(0)
                # 윈도우 위치가 변경되었는지 확인하고 모니터 정보 업데이트
                self.update_monitor_info()

                sct_img = self.sct.grab(self.monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # 프레임 저장
                self.frames.append(frame)

                self.msleep(5)  # 5ms 대기
        except Exception as e:
            logger.error(f"화면 녹화 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def update_monitor_info(self):
        """타겟 윈도우의 현재 위치에 따라 모니터 정보를 업데이트합니다."""
        if self.target_window:
            # 타겟 윈도우의 전역 위치 가져오기
            geometry = self.target_window.geometry()
            global_pos = self.target_window.mapToGlobal(geometry.topLeft())
            
            # 모든 모니터 확인
            for i, monitor in enumerate(self.sct.monitors[1:], 1):  # 0번은 전체 화면이므로 1번부터 시작
                if (monitor["left"] <= global_pos.x() < monitor["left"] + monitor["width"] and
                    monitor["top"] <= global_pos.y() < monitor["top"] + monitor["height"]):
                    # 타겟 윈도우가 있는 모니터 찾음
                    self.monitor = monitor
                    return
                    
            # 타겟 윈도우가 어떤 모니터에도 없으면 기본 모니터 사용
            screen = QApplication.primaryScreen()
            rect = screen.availableGeometry()
            self.monitor = {
                'left': rect.x(),
                'top': rect.y(),
                'width': rect.width(),
                'height': rect.height()
            }
        else:
            # 타겟 윈도우가 없으면 기본 모니터 사용
            self.monitor = self.sct.monitors[1]  # 기본 모니터
                
        # self.finished.emit(self.output_file)

    # def run(self):
    #     """스레드 실행 시 호출되는 메서드. 화면 녹화를 수행합니다."""
    #     self.is_recording = True
        
    #     # 대상 윈도우가 있는 모니터 찾기
    #     geometry = self.target_window.geometry()
    #     global_pos = self.target_window.mapToGlobal(geometry.topLeft())
        
    #     # 화면 캡처 도구 초기화
    #     sct = mss()
        
    #     # # 타겟 윈도우가 있는 모니터 찾기
    #     # target_monitor = None
    #     # for i, monitor in enumerate(sct.monitors[1:], 1):  # 0번은 전체 화면이므로 1번부터 시작
    #     #     if (monitor["left"] <= global_pos.x() < monitor["left"] + monitor["width"] and
    #     #         monitor["top"] <= global_pos.y() < monitor["top"] + monitor["height"]):
    #     #         target_monitor = monitor
    #     #         break
        
    #     # # 타겟 모니터를 찾지 못했다면 기본 모니터(1번) 사용
    #     # if target_monitor is None:
    #     #     target_monitor = sct.monitors[1]
        
    #     # # 모니터 크기 가져오기
    #     # width, height = target_monitor["width"], target_monitor["height"]
        
    #     # 비디오 설정
    #     fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #     out = cv2.VideoWriter(self.output_file, fourcc, self.fps, (width, height))
        
    #     # 녹화 시작 시간
    #     start_time = time.time()
        
    #     try:
    #         # 녹화 루프
    #         while self.is_recording:
    #             # 30초마다 파일 다시 쓰기
    #             current_time = time.time()
    #             if current_time - start_time > 30:
    #                 out.release()
    #                 out = cv2.VideoWriter(self.output_file, fourcc, self.fps, (width, height))
    #                 start_time = current_time
                
    #             # 화면 캡처 (전체 모니터)
    #             sct_img = sct.grab(target_monitor)
    #             frame = np.array(sct_img)
                
    #             # BGR로 변환 (mss는 BGRA 형식으로 캡처)
    #             frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
    #             # 프레임 저장
    #             out.write(frame)
                
    #             # 약간의 딜레이 (CPU 사용량 감소)
    #             self.msleep(int(1000/self.fps))
                
    #     finally:
    #         # 녹화 종료 시 자원 해제
    #         out.release()
    #         self.finished.emit(self.output_file)
    
    def _get_file(self) -> str:
        """녹화를 중지하고 파일 경로를 반환합니다."""

        return self.output_file

    def stop(self) -> str:
        """녹화를 중지합니다."""
        self.is_recording = False
        # 녹화가 완전히 종료될 때까지 잠시 대기
        self.wait(1000)
        if self.frames:  # 프레임이 있는 경우에만 저장

            for _cnt, frame in enumerate(self.frames):
                self.out.write(frame)
                
        self.out.release()
        self.set_permission()
        return self.output_file

    def set_permission(self):
        # 파일 권한 설정 (모든 사용자가 읽고 쓸 수 있도록)
        import os
        import platform
        import stat
        
        try:
            if os.path.exists(self.output_file):
                if platform.system() == 'Windows':
                    # Windows에서는 icacls 명령어 사용
                    os.system(f'icacls "{self.output_file}" /grant Everyone:F')
                else:
                    # Linux/Unix 시스템에서는 chmod 사용
                    os.chmod(self.output_file, 
                             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |  # 소유자 권한
                             stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |  # 그룹 권한
                             stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)   # 기타 사용자 권한
        except Exception as e:
            logger.error(f"파일 권한 설정 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
