from __future__ import annotations
from typing import Optional, Any

from modules.PyQt.Tabs.plugins.ui.Ui_tab_info import Ui_Tab_Info
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import time, traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


from modules.wigets.fileview.wid_fileview import Wid_FileViewer
from info import Info_SW as INFO

class Wid_Info(QWidget, LazyParentAttrMixin):
    def __init__(self, parent=None, appID:Optional[int]=None):
        super().__init__(parent)
        self.lazy_attr_names = ['APP_ID', ]
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}

        self.start_init_time = time.perf_counter()
        self.ui = Ui_Tab_Info()
        self.ui.setupUi(self)

        self.run_lazy_attr()

    def update_ui(self):
        self.update_titles(
            title = f"{self.appDict['표시명_구분']} : {self.appDict['표시명_항목']}",
            sub=self.appDict['info_title']
            )
        self.update_help_page(self.appDict['help_page'])

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)

    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.table_name = Utils.get_table_name(APP_ID)
            ### 2025-06-11 12:33:01,257 - Wid_info - INFO - self.appDict: 
            # {'id': 153, 'div': 'App설정', 'name': 'App설정_개발자', 'url': '', 'api_url': 'app권한-개발자/', 
            # 'api_uri': '/api/users/', '표시명_구분': 'App설정', '표시명_항목': 'App설정_개발자', 'is_Active': False, 'is_Run': False, '순서': 0, 'is_dev': True, 'user_pks': [1]}
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            logger.info(f"self.appDict: {self.appDict}")
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)
            self.subscribe_gbus()

            self.update_ui()

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")


    def subscribe_gbus(self):
        """ 추후에 appDict가 바뀌면 update할 수 있도록 """
        pass

    def update_titles(self, title:str='', sub:str=''):
        """ title : 타이틀, sub : 부제목 """
        self.ui.label_title.setText(title)
        self.ui.label_sub.setText(sub)

    def update_help_page(self, url_file_path:str):
        """URL 정보 설정 (기본적인 검증만 수행)"""
        # 기본적인 URL 형식 확인 (INFO.URI 포함 여부)

        
        has_url = bool(url_file_path) and '/helppage/' in url_file_path
        
        # 버튼 활성화/비활성화 설정
        self.ui.pb_info.setEnabled(has_url)
        
        # 스타일 적용
        self._apply_help_button_style(has_url)
        
        # URL 저장
        self.help_url = f"{INFO.URI}media{url_file_path}" if has_url else None
        
        # 클릭 이벤트 연결 - try/except로 예외 처리
        if has_url:
            try:
                if self.ui.pb_info.receivers(self.ui.pb_info.clicked) > 0:
                    self.ui.pb_info.clicked.disconnect()
            except TypeError:
                pass  # 연결된 시그널이 없는 경우 예외 처리
            self.ui.pb_info.clicked.connect(self.on_help_button_clicked)

    def on_help_button_clicked(self):
        """버튼 클릭 시 실제 URL 유효성 검사 후 파일 뷰어 실행"""
        if not self.help_url:
            return
        
        # 클릭 시점에 URL 유효성 검사 (필요시)
        self.view_file(self.help_url)

    def _apply_help_button_style(self, is_active:bool):
        """도움말 버튼 스타일 적용"""
        if is_active:
            # 활성화 스타일
            self.ui.pb_info.setIcon(QIcon(":/icons/help.png"))
            self.ui.pb_info.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
        else:
            # 비활성화 스타일
            self.ui.pb_info.setIcon(QIcon(":/icons/help_disabled.png"))
            self.ui.pb_info.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)

    def view_file(self, url:str):
        """파일 뷰어 실행"""
        try:
            from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
            dlg = FileViewer_Dialog(self.parent())
            dlg.add_file(url)
            dlg.exec()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "오류", f"파일을 열 수 없읍니다: {str(e)}")
            # 로깅 추가
            logger.error(f"파일 뷰어 오류: {str(e)}")

    # def download_and_view_file(self, url:str):
    #     """URL에서 파일을 다운로드하고 뷰어로 표시"""
    #     import tempfile
    #     import os
    #     import requests
    #     import subprocess
    #     from PyQt6.QtWidgets import QMessageBox
        
    #     try:
    #         # 임시 파일 생성
    #         file_ext = os.path.splitext(url.split('/')[-1])[1]
    #         with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
    #             temp_filename = temp_file.name
            
    #         # 파일 다운로드
    #         response = requests.get(url, stream=True, timeout=5)
    #         if response.status_code == 200:
    #             with open(temp_filename, 'wb') as f:
    #                 for chunk in response.iter_content(chunk_size=8192):
    #                     f.write(chunk)
                
    #             # 파일 뷰어로 열기
    #             if os.name == 'nt':  # Windows
    #                 os.startfile(temp_filename)
    #             elif os.name == 'posix':  # macOS, Linux
    #                 if os.uname().sysname == 'Darwin':  # macOS
    #                     subprocess.call(('open', temp_filename))
    #                 else:  # Linux
    #                     subprocess.call(('xdg-open', temp_filename))
                    
    #             # 임시 파일 정리를 위한 코드 추가 (필요시)
    #             # 뷰어가 파일을 열고 난 후 일정 시간 후 삭제하는 로직 구현 가능
    #         else:
    #             QMessageBox.warning(self, "다운로드 실패", f"파일을 다운로드할 수 없읍니다. 상태 코드: {response.status_code}")
    #     except Exception as e:
    #         QMessageBox.warning(self, "오류", f"파일 다운로드 중 오류가 발생했읍니다: {str(e)}")
