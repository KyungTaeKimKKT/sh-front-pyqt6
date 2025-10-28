"""
애플리케이션 자동 업데이트 모듈
- 서버에서 최신 버전 정보를 확인하고 필요시 업데이트를 수행합니다.
- 상태 코드 기반 API 응답을 처리합니다.
"""

import os
import sys
import json
import time
import pathlib
import platform
import subprocess
import requests
from urllib.parse import unquote
from zipfile import ZipFile
import psutil

from PyQt6.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QProgressBar, QPushButton, QApplication,
                            QInputDialog, QLineEdit)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QEvent
from PyQt6.QtGui import QIcon

from modules.PyQt.User.toast import User_Toast
from modules.user.api import Api_SH_update
from info import Info_SW as INFO
from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

ST = StyleSheet()



class UpdateDialog(QDialog):
    """업데이트 진행 상황을 표시하는 다이얼로그"""
    
    def __init__(self, parent=None, latest_info=None, update_type='U'):
        super().__init__(parent)
        self.latest_info = latest_info or {}
        self.update_type = update_type
        self.skip_password = "123451q!"
        self.setup_ui()
        self.installEventFilter(self)  # 이벤트 필터 설치
        
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("업데이트 관리자")
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        
        # 버전 정보
        current_ver = INFO.Version
        new_ver = self.latest_info.get('버젼', '알 수 없음')
        
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel(f"현재 버전: {current_ver}"))
        version_layout.addWidget(QLabel(f"새 버전: {new_ver}"))
        layout.addLayout(version_layout)
        
        # 설명
        desc = self.latest_info.get('변경사항', '업데이트 정보가 없읍니다.')
        desc_label = QLabel(f"<b>업데이트 내용:</b><br>{desc}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 단축키 안내 (작은 글씨로)
        # shortcut_label = QLabel("<i>단축키: Ctrl+Alt+S를 누르면 관리자 스킵 옵션이 표시됩니다.</i>")
        # shortcut_label.setStyleSheet("color: gray; font-size: 9pt;")
        # layout.addWidget(shortcut_label)
        
        # 진행 상태
        self.status_label = QLabel("업데이트 준비 중...")
        layout.addWidget(self.status_label)
        
        # 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 업데이트 유형에 따른 버튼 구성
        if self.update_type == 'I':  # 강제 업데이트
            self.update_btn = QPushButton("업데이트 시작")
        else:  # 선택적 업데이트
            self.update_btn = QPushButton("업데이트")
            self.cancel_btn = QPushButton("취소")
            self.cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_btn)
        
        self.update_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.update_btn)
        
        layout.addLayout(button_layout)
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - 단축키 감지"""
        if event.type() == QEvent.Type.KeyPress:
            # Ctrl+Alt+S 단축키 감지
            if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and 
                event.modifiers() & Qt.KeyboardModifier.AltModifier and 
                event.key() == Qt.Key.Key_S):
                self.skip_update()
                return True
        return super().eventFilter(obj, event)
    
    def skip_update(self):
        """관리자 비밀번호로 업데이트 스킵"""
        password, ok = QInputDialog.getText(
            self, "관리자 인증", "관리자 비밀번호를 입력하세요:", 
            QLineEdit.EchoMode.Password
        )
        
        if ok and password == self.skip_password:
            logger.info("관리자 비밀번호로 업데이트 스킵")
            self.done(2)  # 스킵 결과 코드
        elif ok:
            QMessageBox.warning(self, "인증 실패", "비밀번호가 올바르지 않읍니다.")
    
    def update_progress(self, value, message):
        """진행 상황 업데이트"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)


class UpdateManager(QObject):
    """애플리케이션 업데이트 관리 클래스"""
    
    # 업데이트 상태 시그널
    update_available_signal = pyqtSignal(dict)  # 업데이트 가능 시그널 (최신 버전 정보)
    update_progress_signal = pyqtSignal(int, str)  # 진행률, 메시지
    update_complete_signal = pyqtSignal(str)  # 업데이트 완료 시그널 (실행 파일 경로)
    update_error_signal = pyqtSignal(str)  # 오류 시그널 (오류 메시지)
    
    def __init__(self, url:str = INFO.API_Update_Check_URL, parent=None):
        super().__init__(parent)
        self.api = Api_SH_update()
        self.url = url
        self.latest_info = {}
        self.download_path = './download'
        self.update_file_path = ''
        self.parent = parent
        
        # 다운로드 디렉토리 생성
        pathlib.Path(self.download_path).mkdir(parents=True, exist_ok=True)
        
        # 시그널 연결
        self.update_progress_signal.connect(self._handle_progress)
        self.update_error_signal.connect(self._handle_error)
    
    def _handle_progress(self, value, message):
        """진행 상황 처리"""
        logger.debug(f"업데이트 진행: {value}% - {message}")
    
    def _handle_error(self, message):
        """오류 처리"""
        logger.error(f"업데이트 오류: {message}")
        if self.parent:
            QMessageBox.critical(self.parent, "업데이트 오류", message)
    
    def check_for_updates(self) -> str:
        """
        업데이트 확인 및 처리를 수행하는 메인 함수
        
        Returns:
            str: 업데이트 파일 경로 (업데이트 필요 없으면 빈 문자열)
        """
        try:
            # 업데이트 확인
            if not self._check_update_available():
                return ''
            
            # 사용자 확인 (필요한 경우)
            if not self._confirm_update():
                return ''
            
            # 업데이트 파일 다운로드
            if not self._download_update():
                return ''
            
            # 업데이트 파일 경로 반환
            return self.update_file_path
            
        except Exception as e:
            error_msg = f"업데이트 확인 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return ''
    
    def _check_update_available(self) -> bool:
        """
        서버에 현재 버전 정보를 보내고 업데이트 필요 여부를 확인
        
        Returns:
            bool: 업데이트가 필요하면 True, 아니면 False
        """
        try:
            self.update_progress_signal.emit(10, "업데이트 확인 중...")
            
            # API 호출
            response = self.api.check_update(
                url=self.url,
                app_name=INFO.APP_Name,
                os=INFO.OS_CHOICES[platform.system()],
                종류 = INFO.종류,
                current_version=INFO.Version
            )
            
            # 응답 처리
            if response.status_code == 204:  # 업데이트 필요 없음
                logger.info("업데이트가 필요하지 않읍니다.")
                self.update_progress_signal.emit(100, "최신 버전입니다.")
                return False
                
            elif response.status_code == 200:  # 업데이트 필요
                self.latest_info = response.json().get('result')
                logger.info(f"새 버전 발견: {self.latest_info.get('버젼')}")
                self.update_available_signal.emit(self.latest_info)
                self.update_progress_signal.emit(20, "새 버전 발견")
                return True
                
            else:  # 기타 오류
                error_msg = f"업데이트 서버 응답 오류: {response.status_code}"
                logger.error(error_msg)
                self.update_error_signal.emit(error_msg)
                
                # 서버 통신 오류 메시지 표시 및 애플리케이션 종료
                if self.parent:
                    msgBox = QMessageBox()
                    msgBox.setWindowTitle("서버 연결 오류")
                    msgBox.setText("서버와의 통신이 원활하지 않읍니다.\n애플리케이션을 종료합니다.")
                    msgBox.setStyleSheet(ST.sw_upgrade_msgbox)
                    msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msgBox.exec()
                
                # 애플리케이션 종료
                sys.exit(1)
                return False
                
        except Exception as e:
            error_msg = f"업데이트 확인 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False
    
    def _confirm_update(self) -> bool:
        """
        사용자에게 업데이트 여부 확인
        
        Returns:
            bool: 업데이트를 진행하면 True, 취소하면 False
        """
        try:
            # 업데이트 다이얼로그 생성
            update_dialog = UpdateDialog(
                parent=self.parent,
                latest_info=self.latest_info,
                update_type=INFO.종류
            )
            
            # 진행 상황 시그널 연결
            self.update_progress_signal.connect(update_dialog.update_progress)
            
            # 다이얼로그 표시 및 결과 처리
            result = update_dialog.exec()
            
            # 시그널 연결 해제
            self.update_progress_signal.disconnect(update_dialog.update_progress)
            
            if result == QDialog.DialogCode.Accepted:  # 업데이트 진행
                self.update_progress_signal.emit(30, "업데이트 준비 중...")
                return True
            elif result == 2:  # 관리자 스킵
                self.update_progress_signal.emit(0, "관리자 권한으로 업데이트 건너뜀")
                return False
            else:  # 취소
                self.update_progress_signal.emit(0, "업데이트 취소됨")
                return False
            
        except Exception as e:
            error_msg = f"업데이트 확인 대화상자 표시 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False
    
    def _download_update(self) -> bool:
        """
        업데이트 파일 다운로드
        
        Returns:
            bool: 다운로드 성공 시 True, 실패 시 False
        """
        try:
            self.update_progress_signal.emit(40, "업데이트 파일 다운로드 중...")
            
            # 다운로드 URL 확인
            download_url = self.latest_info.get('file')
            if not download_url:
                error_msg = "다운로드 URL이 없읍니다."
                logger.error(error_msg)
                self.update_error_signal.emit(error_msg)
                return False
            
            # 파일 다운로드
            response = requests.get(download_url, stream=True)
            if not response.ok:
                error_msg = f"다운로드 오류: {response.status_code}"
                logger.error(error_msg)
                self.update_error_signal.emit(error_msg)
                return False
            
            # 파일 크기 확인
            total_size = int(response.headers.get('content-length', 0))
            
            # 파일명 추출
            filename = self._extract_filename_from_response(response, download_url)
            self.update_file_path = os.path.join(self.download_path, filename)
            
            # 파일 저장
            downloaded = 0
            with open(self.update_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 진행률 업데이트 (40~80%)
                        if total_size > 0:
                            progress = 40 + int((downloaded / total_size) * 40)
                            self.update_progress_signal.emit(progress, "다운로드 중...")
            
            self.update_progress_signal.emit(80, "다운로드 완료")
            logger.info(f"업데이트 파일 다운로드 완료: {self.update_file_path}")
            
            # 다운로드 완료 신호 발생
            self.update_complete_signal.emit(self.update_file_path)
            return True
            
        except Exception as e:
            error_msg = f"업데이트 파일 다운로드 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False
    
    def _extract_filename_from_response(self, response, url) -> str:
        """
        응답 헤더에서 파일명 추출
        
        Args:
            response: 요청 응답 객체
            url: 다운로드 URL
            
        Returns:
            str: 파일명
        """
        # Content-Disposition 헤더에서 파일명 추출 시도
        if 'Content-Disposition' in response.headers:
            content_disposition = response.headers['Content-Disposition']
            
            if 'utf-8' in content_disposition:
                raw_fname = content_disposition.split("filename*=")[1]
                return unquote(raw_fname.replace("utf-8''", ""))
                
            elif "filename=" in content_disposition:
                raw_fname = content_disposition.split("filename=")[1]
                return raw_fname.replace('"', '')
        
        # URL에서 파일명 추출
        return os.path.basename(url)
    
    def install_update(self, file_path) -> bool:
        """
        업데이트 파일 설치
        
        Args:
            file_path: 업데이트 파일 경로
            
        Returns:
            bool: 설치 성공 시 True, 실패 시 False
        """
        try:
            self.update_progress_signal.emit(90, "업데이트 설치 중...")
            
            # 파일 확장자에 따른 처리
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.zip':
                # ZIP 파일 압축 해제
                self._extract_zip(file_path)
                self.update_progress_signal.emit(100, "업데이트 완료")
                return True
                
            elif ext.lower() == '.exe':
                # 실행 파일은 main.py에서 처리
                self.update_progress_signal.emit(100, "업데이트 파일 준비 완료")
                return True
                
            else:
                error_msg = f"지원되지 않는 파일 형식: {ext}"
                logger.error(error_msg)
                self.update_error_signal.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"업데이트 설치 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False
    
    def _extract_zip(self, zip_path) -> bool:
        """
        ZIP 파일 압축 해제
        
        Args:
            zip_path: ZIP 파일 경로
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        try:
            application_path = os.path.dirname(os.path.realpath(__file__))
            
            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(application_path)
            
            logger.info(f"ZIP 파일 압축 해제 완료: {zip_path}")
            return True
            
        except Exception as e:
            error_msg = f"ZIP 파일 압축 해제 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False
    
    def restart_application(self, file_path=None) -> bool:
        """
        애플리케이션 재시작
        
        Args:
            file_path: 실행할 파일 경로 (None이면 현재 애플리케이션 재시작)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        try:
            # 현재 프로세스 종료 준비
            if INFO.PID_Main and psutil.pid_exists(INFO.PID_Main):
                process = psutil.Process(INFO.PID_Main)
                process.terminate()
            
            # 새 프로세스 시작
            if file_path and file_path.endswith('.exe'):
                # Windows EXE 파일 실행
                subprocess.Popen(file_path)
                logger.info(f"새 실행 파일 시작: {file_path}")
                return True
                
            else:
                # 현재 애플리케이션 재시작
                if INFO.OS == 'Windows':
                    if getattr(sys, 'frozen', False):
                        # PyInstaller로 패키징된 경우
                        subprocess.Popen([sys.executable])
                    else:
                        # 스크립트로 실행된 경우
                        subprocess.Popen([sys.executable, 'main.py'])
                else:
                    # Linux/macOS
                    subprocess.Popen(['python3', 'main.py'])
                
                logger.info("애플리케이션 재시작")
                return True
                
        except Exception as e:
            error_msg = f"애플리케이션 재시작 중 오류 발생: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.update_error_signal.emit(error_msg)
            return False


class Update_V2:
    """
    기존 코드와의 호환성을 위한 래퍼 클래스
    """
    def __init__(self, url:str = INFO.API_Update_Check_URL, parent=None):
        self.url = url
        self.manager = UpdateManager(url, parent)
        self.fName = ""
        self.is_Run = True
    
    def update_routine(self) -> str:
        """
        업데이트 루틴을 실행하고 업데이트가 필요한 경우 파일 경로를 반환
        
        Returns:
            str: 업데이트 파일 경로 (업데이트 필요 없으면 빈 문자열)
        """
        if file_path := self.manager.check_for_updates():
            self.fName = file_path
            return file_path
        return ""
    
    def run(self):
        """레거시 호환성 메서드"""
        while self.is_Run:
            self.update_routine()
            time.sleep(3600)  # 1시간마다 확인
    
    def stop(self):
        """레거시 호환성 메서드"""
        self.is_Run = False
        return True
    
    def upgrade_processing(self) -> str:
        """레거시 호환성 메서드"""
        return self.update_routine()
    
    def extract(self, path):
        """레거시 호환성 메서드"""
        if path:
            self.manager.install_update(path)
    
    def check_stop_this_process_running(self):
        """레거시 호환성 메서드"""
        if INFO.PID_Main and psutil.pid_exists(INFO.PID_Main):
            return self.kill_pid(INFO.PID_Main)
        return True
    
    def kill_pid(self, pid):
        """레거시 호환성 메서드"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            logger.info(f"프로세스 종료: {pid}")
            return True
        except Exception as e:
            logger.error(f"프로세스 종료 실패: {pid}, 오류: {e}")
            return False
    
    def restart_Main_App(self):
        """레거시 호환성 메서드"""
        return self.manager.restart_application(self.fName)


# 테스트용 메인 함수
def main():
    """테스트용 메인 함수"""
    app = QApplication(sys.argv)
    
    # 테스트용 업데이트 정보
    test_update_info = {
        "버젼": "2.0.0",
        "설명": "1. 새로운 기능 추가\n2. 버그 수정\n3. 성능 개선",
        "file": "https://example.com/update.zip"
    }
    
    # 테스트 모드 선택
    test_mode = QMessageBox.question(
        None, 
        "테스트 모드 선택", 
        "테스트 모드를 선택하세요:\n\n'예' - 강제 업데이트(I)\n'아니오' - 선택적 업데이트(U)",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    # 테스트 모드에 따라 INFO.종류 설정
    if test_mode == QMessageBox.StandardButton.Yes:
        INFO.종류 = 'I'  # 강제 업데이트
    else:
        INFO.종류 = 'U'  # 선택적 업데이트
    
    # 업데이트 다이얼로그 직접 테스트
    dialog = UpdateDialog(latest_info=test_update_info, update_type=INFO.종류)
    
    # 진행 상황 시뮬레이션
    def simulate_progress():
        for i in range(0, 101, 10):
            dialog.update_progress(i, f"테스트 진행 중... {i}%")
            time.sleep(0.5)
    
    # 진행 버튼 클릭 시 진행 상황 시뮬레이션
    dialog.update_btn.clicked.disconnect()
    dialog.update_btn.clicked.connect(simulate_progress)
    
    dialog.exec()
    
    sys.exit(0)


if __name__ == "__main__":
    main()