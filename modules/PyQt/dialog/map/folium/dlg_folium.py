from __future__ import annotations  
from typing import Optional

import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QLineEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import folium
from html import escape

from geopy.geocoders import Nominatim
import modules.user.utils as Utils

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class FoliumWidget(QWidget):
    TIMEOUT = 10

    def __init__(self, parent, address=None, **kwargs):
        super().__init__(parent)
        self.setMinimumSize( 600, 400 )
        self.layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        if address:
            self.show_map(address)
    
    def get_location(self, address):
        geolocator = Nominatim(user_agent="my_app")
        
        # 전체 주소로 먼저 시도
        location = geolocator.geocode(address, timeout=self.TIMEOUT)
        if location:
            return [location.latitude, location.longitude]
        
        # 주소를 공백으로 분할
        address_parts = address.split()
        
        # 주소를 점진적으로 줄여가며 검색
        for i in range(len(address_parts), 0, -1):
            partial_address = ' '.join(address_parts[:i])
            location = geolocator.geocode(partial_address, timeout=self.TIMEOUT)
            if location:
                return [location.latitude, location.longitude]
    
        # 모든 시도 실패시 서울 좌표 반환
        return [37.5665, 126.9780]  # 기본값: 서울

    
    def show_map(self, address):
        location = self.get_location(address)
        map_object = folium.Map(location=location, zoom_start=15)
        folium.Marker(
            location, 
            popup= self.get_popup_address(address)
            ).add_to(map_object)
        
        self.direct_html_load(map_object)
        ### 생성은 권한 등 문제로 인해 :L is not defined 오류는 Leaflet.js가 제대로 로드되지 않아서 발생한 것입니다.
        # self.create_html_and_load(map_object)

    def direct_html_load( self, map_object: folium.Map ):
        # HTML을 직접 데이터로 전달
        html_data = map_object.get_root().render()
        self.web_view.setHtml(html_data)

    def create_html_and_load( self, map_object: folium.Map ):
        html_data = map_object.get_root().render()

        # 파일 저장 경로
        map_path = os.path.join(Utils.get_app_temp_dir(), "map.html")
        map_object.save(map_path)

        abs_map_path = os.path.abspath(map_path)

        # baseUrl 지정해줘야 외부 JS 로딩 가능
        self.web_view.setHtml(html_data, baseUrl=QUrl.fromLocalFile(abs_map_path))

    def get_popup_address( self, address:str ):
        cleaned_address = escape(address)
        popup_html = f"<div style='white-space: nowrap;'>{cleaned_address}</div>"
        popup = folium.Popup(popup_html, max_width=300)
        return popup
       

class Dialog_Folium_Map(QDialog):
    def __init__(self, parent, address=None, **kwargs ):
        super().__init__(parent)
        self.setWindowTitle("지도 보기")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 주소 입력 필드
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("주소를 입력하세요")
        self.address_input.returnPressed.connect(lambda: self.update_map(self.address_input.text()))
        layout.addWidget(self.address_input)
        
        # 지도 위젯
        self.map_widget = FoliumWidget(self)
        layout.addWidget(self.map_widget)
        
        if address:
            self.address_input.setText(address)
            self.map_widget.show_map(address)
    
        self.show()
        
    def update_map(self, address:Optional[str]=None):
        if address is None: 
            address = self.address_input.text()
        if address:
            self.map_widget.show_map(address)
