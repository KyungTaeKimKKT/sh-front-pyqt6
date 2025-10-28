from __future__ import annotations
from PyQt6.QtGui import QPixmap, QIcon, QMovie
from PyQt6.QtCore import QByteArray, QBuffer
import requests
import threading
from pathlib import Path
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Resources:
    _instance = None
    _initialized = False
 
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            try:
                ### 데이터베이스에서 데이터 로드가 우선순위임 : 
                ### 향후 server => ws 로 받으면 DB 저장
                ### DB 에서 로드 후 적요할 것임.
                self.apply_db_data_to_attributes()
            except Exception as e:
                logger.error(f"Error loading database data: {e}")
            return
        # 여기에 초기화 코드 작성
        self._initialized = True

        self._icons = {}
        self._pixmaps = {}
        self._movies = {}
        self._bytes:dict[str, bytes] = {}

    # -------------------- SETTERS --------------------

    def set_icon(self, name: str, icon: QIcon):
        self._icons[name] = icon

    def set_pixmap(self, name: str, pixmap: QPixmap):
        self._pixmaps[name] = pixmap

    def set_movie(self, name: str, movie: QMovie):
        self._movies[name] = movie

    # -------------------- GETTERS --------------------

    def get_icon(self, name: str) -> None|QIcon:
        return self._icons.get(name, None)

    def get_pixmap(self, name: str) -> None|QPixmap:
        return self._pixmaps.get(name, None)

    def get_movie(self, name: str) -> None|QMovie:
        return self._movies.get(name, None)
    
    def get_bytes(self, name: str) -> None|bytes:
        return self._bytes.get(name, None)

    def get_resources_url(self, name:str, base_uri:str=INFO.URI):
        for resource in self.resources_list:
            if resource.get('name') == name:
                return f"{base_uri}/media{resource.get('file')}"
        return None
    # -------------------- LOADER --------------------

    def load_all_resources(self, resource_list: list[dict], base_uri: str=INFO.URI):
        """멀티스레딩으로 전체 리소스 로드"""
        self.resources_list = resource_list
        def worker(resource: dict):
            name = resource.get('name')
            file = resource.get('file')
            if not name or not file:
                return
            try:
                url = f"{base_uri}/media{file}"
                response = requests.get(url)
                if response.status_code == 200:
                    ext = Path(file).suffix.lower()
                    data = response.content
                    self._apply_resource(name, data, ext)
            except Exception as e:
                logger.error(f"[Resource] Failed to load {name}: {e}")
                logger.error(traceback.format_exc())
        import time
        start_time = time.time()
        threads = []
        for r in resource_list:
            t = threading.Thread(target=worker, args=(r,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        end_time = time.time()
        logger.info(f"Resource {len(resource_list)} 개 로드 완료 : {int((end_time - start_time)*1000)} msec ")

    def _apply_resource(self, name: str, data: bytes, ext: str):
        if ext in ['.png', '.jpg', '.jpeg']:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(data))
            self.set_pixmap(name, pixmap)
            self.set_icon(name, QIcon(pixmap))
        elif ext == '.gif':
            # movie = QMovie()
            # buffer = QBuffer()
            # buffer.setData(QByteArray(data))
            # buffer.open(QBuffer.OpenModeFlag.ReadOnly)
            # movie.setDevice(buffer)
            # buffer.setParent(movie)  # 유지해야 GC 안됨
            # self.set_movie(name, movie)
            self._set_bytes(name, data, ext)
        else:
            logger.error(f"[Resource] Unsupported extension: {ext}")

    def _set_bytes(self, name: str, data: bytes, ext: str):
        self._bytes[name]= data

resources = Resources()