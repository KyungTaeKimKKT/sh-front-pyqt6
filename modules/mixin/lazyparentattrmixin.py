from __future__ import annotations
from typing import Optional, Any
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
# import threading, time
import time
import modules.user.utils as Utils
from info import Info_SW as INFO

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class LazyParentAttrMixin:
    # lazy_attr_names: list[str] = []
    # lazy_ws_names = [] #['ALL_TABLE_CONFIG']
    # lazy_ready_flags: dict[str, bool] = {}
    # lazy_attr_values: dict[str, Any] = {}

    lazy_timeout: float = 5.0
    lazy_check_interval: float = 50  # ms
    # lazy_ready_flags: dict[str, bool] = {}
    # def __init__(self, *args, **kwargs):        
    #     super().__init__(*args, **kwargs)
    #     self.lazy_ready_flags: dict[str, bool] = {}
    #     self._lazy_start_time = QTime.currentTime()

    
    def run_lazy_attr(self):
        """ flag를 선언하여 시작을 하지 않도록 추가함."""
        
        self._lazy_ready_flags: dict[str, bool] = {}
        self._lazy_start_time = QTime.currentTime()
        ### ✅ 25-7-7 추가 : widget 찾은 후 바로 속성가져오기
        t0 = time.perf_counter()
        self._lazy_source_widget = self._find_attr_parent_widget()
        # t1 = time.perf_counter()
        # print(f"{self.__class__.__name__} : _find_attr_parent_widget_depth : {(1000*(t1 - t0)):.2f}ms")
        if self._lazy_source_widget:
            self._check_lazy_attrs_from_widget(self._lazy_source_widget)
            if INFO.IS_DEV:
                print(f"{self.__class__.__name__} : _check_lazy_attrs_from_widget : {(1000*(time.perf_counter() - t0)):.2f}ms")
        else:
            raise ValueError(f"{self.__class__.__name__}: lazy source widget not found")

        # self._check_lazy_attrs()

    ### ✅ 25-7-7 추가 : parent widget 찾기
    def _find_attr_parent_widget(self) -> Optional[QWidget]:
        parent = self._get_parent_widget(self)
        depth = 0
        while parent:
            obj_name = parent.objectName() if hasattr(parent, 'objectName') else ""
            if obj_name.startswith("APP_ID"):
                return parent  # ✅ APP 기준 위젯
            parent = self._get_parent_widget(parent)
            depth += 1
            if depth > 10:
                break
        return None

    ### ✅ 25-7-7 추가 : 찾은 widget에서  속성가져오기
    def _check_lazy_attrs_from_widget(self, source_widget: QWidget):
        #### ✅ 25-7-11 추가 : lazy_attrs 처리
        #### source_widget에서 lazy_attrs variable(app권한에 추가함) 이 있으면 우선 적용
        all_found = True

        if hasattr(source_widget, 'lazy_attrs') and isinstance(source_widget.lazy_attrs, dict) and source_widget.lazy_attrs:
            self.lazy_ready_flags = {'APP_ID': True}
            self.lazy_attr_values = {'APP_ID': source_widget.APP_ID}
            for attr_name, attr_value in source_widget.lazy_attrs.items():
                self.lazy_ready_flags[attr_name] = True
                self.lazy_attr_values[attr_name] = attr_value
            if INFO.IS_DEV:
                print(f"{self.__class__.__name__} : lazy_attrs ready -- by app권한(server) : {self.lazy_attr_values}")
            self.on_all_lazy_attrs_ready()
            return
        for attr_name in self.lazy_attr_names:
            if attr_name in self._lazy_ready_flags:
                continue
            if hasattr(source_widget, attr_name):
                value = getattr(source_widget, attr_name)
                self._lazy_ready_flags[attr_name] = True
                QTimer.singleShot(0, lambda v=value, n=attr_name: self.on_lazy_attr_ready(n, v))
            else:
                all_found = False

        if not all_found:
            if self._lazy_start_time.msecsTo(QTime.currentTime()) < self.lazy_timeout * 1000:
                QTimer.singleShot(self.lazy_check_interval, lambda: self._check_lazy_attrs_from_widget(source_widget))
            else:
                for attr_name in self.lazy_attr_names:
                    if attr_name not in self._lazy_ready_flags:
                        QTimer.singleShot(0, lambda n=attr_name: self.on_lazy_attr_not_found(n))
        else:
            if INFO.IS_DEV:
                print(f"{self.__class__.__name__}: All lazy attributes ready from {source_widget.objectName()}")

    # def _check_lazy_attrs(self):
    #     all_found = True
    #     for attr_name in self.lazy_attr_names:
    #         if attr_name in self._lazy_ready_flags:
    #             continue
    #         value = self._find_attr_recursively(attr_name)
    #         if value is not None:
    #             self._lazy_ready_flags[attr_name] = True
    #             # setattr(self, attr_name, value)
    #             QTimer.singleShot(0, lambda v=value, n=attr_name: self.on_lazy_attr_ready(n, v))
    #         else:
    #             all_found = False

    #     if not all_found:
    #         if self._lazy_start_time.msecsTo(QTime.currentTime()) < self.lazy_timeout * 1000:
    #             QTimer.singleShot(self.lazy_check_interval, self._check_lazy_attrs)
    #         else:
    #             for attr_name in self.lazy_attr_names:
    #                 if attr_name not in self._lazy_ready_flags:
    #                     QTimer.singleShot(0, lambda n=attr_name: self.on_lazy_attr_not_found(n))
    #     else:
    #         logger.info(f"{self.__class__.__name__} : All lazy attributes are ready: {self._lazy_ready_flags}")

    def _find_attr_recursively(self, attr_name: str) -> Optional[Any]:
        parent = self._get_parent_widget(self)
        while parent:
            if hasattr(parent, attr_name):
                return getattr(parent, attr_name)
            parent = self._get_parent_widget(parent)
            if not isinstance(parent, QWidget):
                break

        return None
    
    def _get_parent_widget(self, widget: QWidget) -> QWidget:
        if hasattr(widget, 'parentWidget'):
            return widget.parentWidget()
        elif hasattr(widget, 'parent'):
            return widget.parent()
        else:
            return None

    # def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
    #     raise NotImplementedError("Subclass must implement on_lazy_attr_ready")
    
    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        if self.lazy_ready_flags.get(attr_name):
            return  # 이미 처리된 attr이면 무시
        self.lazy_ready_flags[attr_name] = True
        self.lazy_attr_values[attr_name] = attr_value
        
        if all(self.lazy_ready_flags.get(name, False) for name in self.lazy_attr_names + self.lazy_ws_names):
            print(f" {self.parent().__class__.__name__}  {self.__class__.__name__} all lazy attrs ready : 소요시간 : {Utils.get_소요시간(self.start_init_time)}")
            self.on_all_lazy_attrs_ready()
        else:
            not_ready = [name for name in self.lazy_attr_names + self.lazy_ws_names if not self.lazy_ready_flags.get(name, False)]


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.warning(f"{self.parent().__class__.__name__}  {self.__class__.__name__} LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")

    def on_all_lazy_attrs_ready(self):
        raise NotImplementedError("Subclass must implement on_all_lazy_attrs_ready")

    # def run_lazy_attr(self):
    #     # QTimer.singleShot(0, self._check_lazy_attrs)  # 첫 실행

    #     for attr_name in self.lazy_attr_names:
    #         threading.Thread(
    #             target=self._wait_for_lazy_attr, 
    #             daemon=True, 
    #             args=(attr_name,)
    #             ).start()
            
    # def _check_lazy_attrs(self):
    #     all_found = True
    #     for attr_name in self.lazy_attr_names:
    #         if attr_name in self.lazy_ready_flags:
    #             continue
    #         value = self._find_attr_recursively(attr_name)
    #         if value is not None:
    #             self.lazy_ready_flags[attr_name] = True
    #             self.on_lazy_attr_ready(attr_name, value)
    #         else:
    #             all_found = False

    #     # 아직 못 찾은 attr이 있으면, 다시 확인
    #     if not all_found:
    #         if self._lazy_start_time.msecsTo(QTime.currentTime()) < self.lazy_timeout * 1000:
    #             QTimer.singleShot(self.lazy_check_interval, self._check_lazy_attrs)
    #         else:
    #             for attr_name in self.lazy_attr_names:
    #                 if attr_name not in self.lazy_ready_flags:
    #                     self.on_lazy_attr_not_found(attr_name)

    # def _wait_for_lazy_attr(self, attr_name: str):
    #     t0 = time.time()
    #     while time.time() - t0 < self.lazy_timeout:
    #         value = self._find_attr_recursively(attr_name)
    #         # logger.debug(f"{self.__class__.__name__} : _wait_for_lazy_attr : {attr_name} : {value}")
    #         if value is not None:
    #             setattr(self, attr_name, value)
    #             # self.on_lazy_attr_ready(attr_name, value)
    #             QMetaObject.invokeMethod(
    #                 self,
    #                 lambda: self.on_lazy_attr_ready(attr_name, value),
    #                 Qt.ConnectionType.QueuedConnection
    #             )
    #             return
    #         time.sleep(0.05)
    #     logger.warning(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")
    #     # self.on_lazy_attr_not_found(attr_name)
    #     QMetaObject.invokeMethod(
    #         self,
    #         lambda: self.on_lazy_attr_not_found(attr_name),
    #         Qt.ConnectionType.QueuedConnection
    #     )

    # def _find_attr_recursively(self, attr_name: str) -> Optional[Any]:
    #     parent = self.parent()
    #     while parent:
    #         # logger.debug(f"{self.__class__.__name__} : _find_attr_recursively : {attr_name} : {parent}")
    #         if hasattr(parent, attr_name):
    #             return getattr(parent, attr_name)
    #         parent = parent.parent()
    #     return None

    # def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
    #     raise NotImplementedError("Subclass must implement on_lazy_attr_ready")

    # def on_lazy_attr_not_found(self, attr_name: str):
    #     logger.warning(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")
    #     # raise NotImplementedError("Subclass must implement on_lazy_attr_not_found")