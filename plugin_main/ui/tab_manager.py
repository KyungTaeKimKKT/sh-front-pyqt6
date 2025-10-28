from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.global_event_bus import event_bus
from PyQt6 import sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import time, importlib,sys

import modules.user.utils as utils
from info import Info_SW as INFO
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.PyQt.User.toast import User_Toast

import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

if TYPE_CHECKING:
    from main import MainWindow
    from plugin_main.websocket.handlers.client_app_access_log import ClientAppAccessLogHandler

class TabManager(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_wid:MainWindow = parent
        self.tab_containers = {}  # 표시명_구분 : QTabWidget
        self.current_container = None
        self.previous_container = None
        self.current_app_dict = None

        self.event_bus = event_bus
        self.register_events()

    def register_events(self):        
        self.event_bus.subscribe(GBus.TOOLBAR_MENU_CLICKED, self.app_load_requested)
        self.event_bus.subscribe(GBus.APP_RELOAD, self.app_reload_requested)
        self.event_bus.subscribe(GBus.HOME_WIDGET_SHOW, self.home_widget_show)

    def app_load_requested(self, msg:dict):
        """msg 형태 : {'menu': '표시명_구분', 'appObj': app_dict}"""
        try:
            if INFO.IS_DEV: 
                logger.info(f"app_load_requested: {msg}")
            request_menu = msg.get('menu')
            appObj = msg.get('appObj')
            appList = INFO.MENU_DICT.get(request_menu)
            current_idx = appList.index(appObj)

            #### 탭 컨테이너 생성
            if request_menu not in self.tab_containers:
                self.previous_container = self.current_container
                self.current_container  = self.create_tab_container( category = request_menu, app_list=appList)
                self.main_wid.vLayout_Main.addWidget(self.current_container)

            else:
                current_menu = self.current_container.objectName() # 현재 탭 컨테이너 이름
                if current_menu != request_menu:
                    self.previous_container = self.current_container
                    self.current_container = self.tab_containers[request_menu]['tab_container']

            self.current_container.setCurrentIndex(current_idx)
            self.current_container.show()
            if self.previous_container:
                self.previous_container.hide()
            
            #### 탭 클릭 이벤트 발생시켜  app 로드함.
            self._handle_tab_clicked(current_idx)
        
        except Exception as e:
            User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Branch Error", text=str(e), style='ERROR')
            logger.error(f"app_load_requested: {e}")
            logger.error(f"{traceback.format_exc()}")

    def app_reload_requested(self, isOk:bool):
        """ 앱 리로드 요청 처리 """
        try:
            if INFO.IS_DEV:
                logger.info(f"app_reload_requested: {isOk}")
            if self.current_container and hasattr(self, 'current_tab') and self.current_tab:
                # 기존 앱 정리
                if hasattr(self.current_tab, 'app_isLoaded') and self.current_tab.app_isLoaded :
                    try:    
                        if INFO.IS_DEV:
                            logger.warning(f"self.current_tab: {self.current_tab} cleanup")
                        self.auto_cleanup(self.current_tab)
                        self.current_tab.app_isLoaded = False
                        # self.current_tab = None                        
                    except Exception as e:
                        logger.error(f"app_reload_requested: {e}")
                        logger.error(f"{traceback.format_exc()}")
            
            # 기존 레이아웃 삭제
            if self.current_tab and hasattr(self.current_tab, 'layout') and self.current_tab.layout():
                utils.deleteLayout(self.current_tab.layout())

            if self.current_container and hasattr(self.current_container, 'currentIndex'):
                if INFO.IS_DEV: 
                    logger.warning(f"self.current_container: {self.current_container} currentIndex: {self.current_container.currentIndex()}")
                current_index = self.current_container.currentIndex()
                # 탭 클릭 이벤트 트리거하여 앱 리로드
                self._handle_tab_clicked(current_index)
                User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Reloaded", text="앱이 리로드되었읍니다.", style='INFORMATION')
            else:
                User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Reload Error", text="현재 탭이 없읍니다.", style='ERROR')
        except Exception as e:
            User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Reload Error", text=str(e), style='ERROR')
            logger.error(f"app_reload_requested: {e}")
            logger.error(f"{traceback.format_exc()}")
            
    def load_app_(self, parentWid:QWidget, app_dict:dict[str:str]) -> Optional[QWidget]:
        """ app을 load하여 return 하는 함수"""

        try:
            postfix = '__for_Tab'
            default_appName = f"App{postfix}"
            # 앱 로드 로직
            divName, appName = app_dict.get('div'), app_dict.get('name')
            수정divName = divName.replace('(','_').replace(')','_')
            수정appName = appName.replace('(','_').replace(')','_')
            
            app_class = self.dynamic_import(수정divName, f"{수정divName}_{수정appName}", f'{수정appName}{postfix}')
            
            app = None
            if app_class:
                app = app_class(parentWid, **app_dict, APP_ID=app_dict.get('id'))
                if INFO.IS_DEV:
                    print(f"appDict : {app_dict}")
            else:
                app_class = self.dynamic_import(수정divName, f"{수정divName}_{수정appName}", f'{default_appName}')
                if app_class:
                    app = app_class(parentWid, **app_dict, APP_ID=app_dict.get('id'))
                else:
                    User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Branch Error", 
                            text=f"app_class:{app_class} ==> {수정divName} - {수정appName}", style='ERROR')
            INFO.APP_MAP_ID_TO_AppWidget[app_dict.get('id')] = app

            return app
            
        except Exception as e:
            User_Toast(parent=INFO.MAIN_WINDOW, duration=5000, title="App Branch Error", text=str(e), style='ERROR')
            logger.error(f"load_app_: {e}")
            logger.error(f"{traceback.format_exc()}")

    # def dynamic_import(self, divName:str, module_name:str, class_name:str) :
    #         """
    #             module_name : 모듈 이름(.py)
    #             class_name : 클래스 이름
    #         """
    #         module_class = None
    #         try:                
    #             # 모듈 경로를 명시적으로 지정
    #             full_module_name = f"modules.PyQt.Tabs.{divName}.{module_name}"
    #             # 이미 로드된 모듈인지 확인
    #             if full_module_name in sys.modules:
    #                 if INFO.IS_DEV:
    #                     # 개발 모드일 때는 모듈을 강제 리로드
    #                     del sys.modules[full_module_name]
    #                     module = importlib.import_module(full_module_name)
    #                     importlib.reload(module)
    #                 else:
    #                     module = sys.modules[full_module_name]
                    
    #             else:
    #                 # 모듈 로드 시간 측정
    #                 module_load_start = time.time()
    #                 module = importlib.import_module(full_module_name)
    #                 module_load_time = time.time() - module_load_start

    #                 if module_load_time > 0.5:  # 0.5초 이상 걸리는 모듈 로깅
    #                     if INFO.IS_DEV:
    #                         logger.warning(f"모듈 로드 시간: {module_load_time}초, 모듈: {module_name}")
    #                 else:
    #                     if INFO.IS_DEV:
    #                         logger.warning(f"모듈 로드 시간: {module_load_time}초, 모듈: {module_name}")
    #             module_class = getattr(module, class_name)                

    #         except ImportError as e:	
    #             logger.error(f"모듈 로드 오류: {module_name}, {class_name}, {e}")
    #             logger.error(f"{traceback.format_exc()}")
    #         except AttributeError as e:
    #             logger.error(f"클래스 로드 오류: {module_name}, {class_name}, {e}")
    #             logger.error(f"{traceback.format_exc()}")
    #         except Exception as e:
    #             logger.error(f"예외 발생: {e}")
    #             logger.error(f"{traceback.format_exc()}")
            
    #         finally:
    #             return module_class

    def dynamic_import(self, divName: str, module_name: str, class_name: str):
        """
        25-9-2 수정 : divName_ prefix 제거된 것도 시도 
        동적 모듈/클래스 임포트
        - 우선 divName_ prefix 붙은 module_name 시도
        - 없으면 prefix 제거한 module_name 시도
        """
        module_class = None
        base_pkg = f"modules.PyQt.Tabs.{divName}"

        # prefix 제거 버전
        clean_module_name = module_name.replace(f"{divName}_", "", 1)

        # 우선순위: [원래 이름, prefix 제거 이름]
        candidate_modules = [
            f"{base_pkg}.{module_name}",
            f"{base_pkg}.{clean_module_name}" if clean_module_name != module_name else None
        ]
        candidate_modules = [m for m in candidate_modules if m]  # None 제거

        module = None

        try:
            for full_module_name in candidate_modules:
                try:
                    # 이미 로드된 모듈인지 확인
                    if full_module_name in sys.modules:
                        if INFO.IS_DEV:
                            del sys.modules[full_module_name]
                            module = importlib.import_module(full_module_name)
                            importlib.reload(module)
                        else:
                            module = sys.modules[full_module_name]
                    else:
                        module_load_start = time.time()
                        module = importlib.import_module(full_module_name)
                        module_load_time = time.time() - module_load_start
                        if INFO.IS_DEV:
                            logger.warning(f"모듈 로드 시간: {module_load_time:.3f}초, 모듈: {full_module_name}")

                    # 모듈을 성공적으로 가져왔으면 break
                    break

                except ModuleNotFoundError:
                    module = None
                    continue  # 다음 candidate 시도

            if not module:
                raise ImportError(f"모듈을 찾을 수 없음: {module_name}")

            # 클래스 가져오기
            module_class = getattr(module, class_name)

        except ImportError as e:
            logger.error(f"모듈 로드 오류: {module_name}, {class_name}, {e}")
            logger.error(f"{traceback.format_exc()}")
        except AttributeError as e:
            logger.error(f"클래스 로드 오류: {module_name}, {class_name}, {e}")
            logger.error(f"{traceback.format_exc()}")
        except Exception as e:
            logger.error(f"예외 발생: {e}")
            logger.error(f"{traceback.format_exc()}")

        return module_class


    def create_tab_container(self, category:str, app_list:list[dict]) -> QTabWidget:
        """
        탭 컨테이너(QTabWidget)를 생성하고 탭들을 추가합니다.
        self.tab_containers 에 저장됨.
        self.tab_containers[category] = {
            'tab_container': tab_container,
            'tabs' : tabs,
            # 'current_tab' : current_tab
        }
        
        Args:
            app_list: 동일한 표시명_구분을 가진 앱 목록
            current_app: 현재 선택된 앱 정보
            
        Returns:
            QTabWidget
        """
        if not app_list:
            return None, -1

        tab_container = QTabWidget()
        tab_container.setObjectName(category)
        
        # 탭 추가
        tabs = []
        for idx, app in enumerate(app_list):
            tab = self._create_tab(app)
            tab_container.addTab(tab, app.get('표시명_항목'))
            tabs.append(tab)
            # 일반 사용자의 경우 is_Run 속성에 따라 탭 활성화/비활성화
            if INFO.USERID != 1:
                tab_container.setTabEnabled(idx, app.get('is_Run', False))
        
        # 탭 클릭 이벤트 연결
        tab_container.tabBarClicked.connect(self._handle_tab_clicked)
        
        # 탭 컨테이너 저장
        self.tab_containers[category] = {
            'tab_container': tab_container,
            'tabs' : tabs,
            # 'current_tab' : current_tab
        }
        self.current_container = tab_container
        return tab_container

    def _create_tab(self, app_dict:dict):
        """
        개별 탭을 생성합니다.
        
        Args:
            app_dict: 앱 정보 딕셔너리
            
        Returns:
            QWidget: 생성된 탭 위젯
        """
        tab = QWidget()
        tab.setObjectName(f'Tab_APP_ID_{app_dict.get("id")}')
        tab.app_isLoaded = False  # 앱 참조를 저장할 속성
        tab.app_dict = app_dict  # 앱 정보 저장
        return tab

    def home_widget_show(self, is_show:bool=True):
        if is_show:
            if self.main_wid.home_widget.isVisible():
                return
            self.main_wid.home_widget.show()
            if self.current_container is not None :
                self.current_container.hide()

    def _handle_tab_clicked(self, index:int):
        """
        탭 클릭 이벤트 핸들러
        
        Args:
            index: 클릭된 탭의 인덱스
        """
        if INFO.IS_DEV:
            logger.warning(f"tab_clicked: {index}")
        if not self.current_container:
            self.main_wid.home_widget.show()
            return
        if self.main_wid.home_widget.isVisible():
            self.main_wid.home_widget.hide()
            
        self.current_tab = self.current_container.widget(index)
        if not self.current_tab or not self.current_tab.isEnabled():
            return
            
        # 탭 스타일 설정
        self._set_current_tab_style()

        if INFO.IS_DEV:
            logger.warning(f" self.current_tab: {self.current_tab} app_isLoaded: {self.current_tab.app_isLoaded}")
        if self.current_tab and hasattr(self.current_tab, 'app_isLoaded') and not self.current_tab.app_isLoaded:
            app = self.load_app_( parentWid= self.current_container, app_dict=self.current_tab.app_dict)
            if app:
                if INFO.IS_DEV:
                    logger.warning(f"app: {app} 로드 성공")
                ### tab 에 렌더 및 app 추가, 실행
                vLayout = QVBoxLayout()
                vLayout.addWidget(app)
                self.current_tab.setLayout(vLayout)
                ### app 실행
                self.current_tab.app_isLoaded = True
                app.run()
            else:
                if INFO.IS_DEV:
                    logger.warning(f"app: {app} 로드 실패")
                self.current_tab.app_isLoaded = False
                utils.generate_QMsg_critical(parent=INFO.MAIN_WINDOW, title="App Load Error", text=f"app:{app} 로드 실패")

        else:
            #### app_isLoaded 가 True 인 경우 앱 리로드
            pass

        ### 7-17 수정 : 탭 클릭 시, ws 로 log 전송
        ws :ClientAppAccessLogHandler = INFO.WS_TASKS.get(INFO.get_WS_URL_by_name('client_app_access_log'))
        if INFO.IS_DEV:
            print ('tab clicked : ', ws  )
        if ws:  
            ws.send_message( { 'status': 'running', 
                            'user_id': INFO.USERID, 
                            'app_fk_id': self.current_tab.app_dict.get('id') } )
        else:
            logger.error(f"ws: {ws} 없음")
    
        # 탭 클릭 시그널 발생
        self.event_bus.publish(
            'tab_clicked', 
            { 'appObj': self.current_tab.app_dict, 
             'menu': self.current_container.objectName(), 
             'action': self.current_tab.objectName() })

    def _set_current_tab_style(self):
        """현재 선택된 탭에 스타일을 적용합니다."""
        if self.current_container:
            self.current_container.setStyleSheet(
                """
                QTabBar::tab:selected {
                    background-color: #000000;
                    color: #FFFF00;
                    font-weight: bold;
                }
                """
            )


    def auto_cleanup(self, widget:QWidget):
        try:
            # 자식 QObject 전부 순회
            for obj in widget.findChildren(QObject):
                try:
                    if INFO.IS_DEV:
                        if hasattr( obj, 'subscribe_gbus' ) and not hasattr( obj, 'unsubscribe_gbus'):
                            logger.warning(f" sub존재하지만, unsub 존재 안함: {obj}")
                        if hasattr( obj, 'connect_signals' ) and not hasattr( obj, 'disconnect_signals'):
                            logger.warning(f" connect_signals 존재하지만, disconnect 존재 안함: {obj}")
                    if hasattr(obj, 'unsubscribe_gbus'):
                        obj.unsubscribe_gbus()
                    if hasattr(obj, 'disconnect_signals'):
                        obj.disconnect_signals()
                    
                    # 가능한 경우 disconnectAllSlots (Qt에는 없지만 비슷한 목적)
                    for signal_name in dir(obj):
                        signal_attr = getattr(obj, signal_name)
                        if callable(signal_attr) and hasattr(signal_attr, 'disconnect'):
                            try:
                                signal_attr.disconnect()
                            except Exception:
                                pass

                    if isinstance(obj, QTimer):
                        obj.stop()
                        obj.deleteLater()
                    elif isinstance(obj, QWidget):
                        if obj.layout():
                            utils.deleteLayout ( obj.layout() )
                        obj.close()
                        obj.setParent(None)
                        obj.deleteLater()
                except Exception as e:
                    print(f"cleanup error for {obj}: {e}")
            # 마지막으로 위젯 자신 삭제 예약
            utils.deleteLayout(widget.layout())
            # widget.deleteLater()
        except Exception as e:
            logger.error(f"auto_cleanup error: {e}")
            logger.error(f"{traceback.format_exc()}")

                


    def get_current_tab(self):
        """
        현재 선택된 탭을 반환합니다.
        
        Returns:
            tuple: (현재 탭 위젯, 앱 ID, 탭 인덱스) 또는 (None, None, None)
        """
        if not self.current_container:
            return None, None, None
            
        index = self.current_container.currentIndex()
        tab = self.current_container.widget(index)
        
        if not tab:
            return None, None, None
            
        app_id = tab.objectName().split('_')[-1]
        return tab, int(app_id), index

    def update_tab(self, app_dict, update_type='change', changes=None):
        """
        탭을 업데이트합니다 (추가/삭제/변경).
        
        Args:
            app_dict: 앱 정보 딕셔너리
            update_type: 'add', 'remove', 'change' 중 하나
            changes: 변경된 속성 정보 (update_type이 'change'일 때만 사용)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        category = app_dict.get('표시명_구분')
        if category not in self.tab_containers:
            return False
            
        container = self.tab_containers[category]
        
        if update_type == 'add':
            # 새 탭 추가
            tab = self._create_tab(app_dict)
            container.addTab(tab, app_dict.get('표시명_항목'))
            return True
            
        elif update_type == 'remove':
            # 탭 삭제
            for i in range(container.count()):
                if container.widget(i).objectName() == f'appid_{app_dict.get("id")}':
                    container.removeTab(i)
                    return True
            return False
            
        elif update_type == 'change' and changes:
            # 탭 속성 변경
            for i in range(container.count()):
                tab = container.widget(i)
                if tab.objectName() == f'appid_{app_dict.get("id")}':
                    self._apply_tab_changes(tab, container, i, app_dict, changes)
                    return True
            return False
            
        return False

    def _apply_tab_changes(self, tab, container, index, app_dict, changes):
        """탭 변경사항을 적용합니다."""
        for key, change in changes.items():
            value = change.get('new')
            
            if key == 'is_Active':
                pass  # 필요한 경우 구현
            elif key == 'is_Run':
                container.setTabEnabled(index, value)
            elif key == '표시명_항목':
                container.setTabText(index, value)
            elif key == 'help_page' or key == 'info_title':
                # 앱이 있는 경우 앱 속성 업데이트
                if hasattr(tab, 'app') and tab.app:
                    tab.app._init_kwargs(**app_dict)
                    if key == 'help_page':
                        tab.app._update_page_info(value)
                    elif key == 'info_title':
                        tab.app._set_info_title(value)
            
            # 앱 정보 업데이트
            tab.app_dict = app_dict

    def clear_all(self):
        """모든 탭 컨테이너를 제거합니다."""
        for container in self.tab_containers.values():
            if container.parent():
                container.parent().layout().removeWidget(container)
            container.deleteLater()
        
        self.tab_containers = {}
        self.current_container = None

    def load_app_in_tab(self, tab, app_dict):
        """탭에 앱 로드"""
        # 이 부분이 중요: MainWindow의 trigger_Branch 로직을 여기로 이동
        # 앱 로드 로직을 캡슐화
        
        # 기존 앱 정리
        if hasattr(tab, 'app') and tab.app:
            try:
                if not sip.isdeleted(tab.app):
                    tab.app.hide()
                    tab.app.deleteLater()
            except:
                pass
            tab.app = None
        
        # 기존 레이아웃 삭제
        if tab.layout():
            utils.deleteLayout(tab.layout())
        
        # 앱 로드 로직
        # 이 부분은 MainWindow의 trigger_Branch 메서드에서 가져옴
        # 실제 앱 로드 로직은 MainWindow에 위임
        
        # 앱 로드 완료 시그널 발생
        self.app_loaded.emit(tab, app_dict)
        
        return True
    
    def handle_app_state_changed(self, data):
        """앱 상태 변경 처리"""
        app_id = data.get('app_id')
        state = data.get('state')
        
        # 해당 앱이 있는 탭 찾기
        for container in self.tab_containers.values():
            for i in range(container.count()):
                tab = container.widget(i)
                if tab.objectName() == f'appid_{app_id}':
                    # 상태에 따른 처리
                    if state == 'reload':
                        # 앱 리로드
                        app_dict = tab.app_dict
                        self.load_app_in_tab(tab, app_dict)
                    elif state == 'disabled':
                        # 탭 비활성화
                        container.setTabEnabled(i, False)
                    elif state == 'enabled':
                        # 탭 활성화
                        container.setTabEnabled(i, True)
                    break