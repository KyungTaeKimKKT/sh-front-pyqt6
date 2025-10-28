from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6 import sip
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from info import Info_SW as INFO
import numpy as np

import math
from enum import Enum


DEFAULT_STYLE = """
                    border: 1px solid gray;
                    background-color: white;
                """
SELECTED_STYLE = """
                    border: 1px solid blue;
                    background-color: lightgreen;
                """

class Lbl_Image_with_QNetwork(QLabel):
    """QLabel 기반 이미지 표시 위젯"""
    def __init__(self, parent:QWidget, data:dict ={}, url:str=None, min_size:tuple[int, int]=(64,64)):
        super().__init__(parent)
        self.min_size = min_size
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setMinimumSize(self.min_size[0], self.min_size[1])
        self.setStyleSheet(DEFAULT_STYLE)

        self.data = data
        self.url = url 
        # 네트워크 매니저 초기화 (URL 로딩용)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_network_response)
        if url:
            self._load_from_url(url)

    def _load_from_url(self, url:str):
        """URL 로딩 오류 처리 개선"""        
        try:
            if url is None:
                self.setText("Image File 없음")
                return
            if not url.startswith(('http://', 'https://')):
                url = INFO.URI + url

            request = QNetworkRequest(QUrl(url))
            request.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
            )
            self.network_manager.get(request)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load URL: {str(e)}")
        
    def _handle_network_response(self, reply:QNetworkReply):
        """네트워크 응답 처리 개선"""
        if reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) != 200:
            error_details = {
                'error_code': reply.error(),
                'error_string': reply.errorString(),
                'http_status': reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute),
                'content_type': reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader),
                'raw_headers': str(reply.rawHeaderList())
            }
            
            error_message = f"""
            Error Code: {error_details['error_code']}
            Error Message: {error_details['error_string']}
            HTTP Status: {error_details['http_status']}
            Content Type: {error_details['content_type']}
            Headers: {error_details['raw_headers']}
            """
            
            QMessageBox.critical(self, "Error", error_message)
            return
            
        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        if not pixmap.isNull():
            self.current_image = pixmap
            self._update_display()
            
    def _update_display(self):
        if self.current_image:
            scaled_pixmap = self.current_image.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        else:
            # 이미지가 없을 때 안내 메시지 표시
            self.setText("Image File 없음")