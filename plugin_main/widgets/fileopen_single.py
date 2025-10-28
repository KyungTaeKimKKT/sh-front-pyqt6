from __future__ import annotations
from typing import Optional, Union, List
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus

from PyQt6.QtWidgets import QFileDialog, QWidget
from PyQt6.QtCore import pyqtSignal
from pathlib import Path

class FileOpenSingle(QWidget):
    file_selected = pyqtSignal(str)

    FILE_FILTERS = {
        "all": "All Files (*.*)",
        "zip": "ZIP Files (*.zip)",
        "pdf": "PDF Files (*.pdf)",
        "txt": "Text Files (*.txt)",
        "image": "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        "html": "HTML Files (*.html)",
        "doc": "Word Documents (*.doc *.docx)",
        "excel": "Excel Files (*.xls *.xlsx)",
        "ppt": "PowerPoint Files (*.ppt *.pptx)",
        "audio": "Audio Files (*.mp3 *.wav *.m4a)",
        "video": "Video Files (*.mp4 *.avi *.mkv)",
    }

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        default_dir: Optional[str] = str(Path.home()),
        file_filter: Union[str, List[str]] = "all",
        on_complete_channelName: Optional[str] = None,
        **kwargs    
    ):
        super().__init__(parent)
        self.event_bus = event_bus
        self.on_complete_channelName = on_complete_channelName
        self.default_dir = default_dir or str(Path.home())
        self.file_filter_keys = [file_filter] if isinstance(file_filter, str) else file_filter

        self.file_path:Optional[str] = None

        self.kwargs = kwargs

    def open_file_dialog(self) -> str:
        file_filter = self._build_file_filter_string()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            self.default_dir,
            file_filter
        )
        if file_path:
            self.file_path = file_path
            self.file_selected.emit(file_path)
            self.publish_complete_event(file_path)
            return file_path
        return ''
    
    def publish_complete_event(self, file_path: str):
        if self.on_complete_channelName:
            self.event_bus.publish(self.on_complete_channelName, 
                                   { 'index': self.kwargs.get('index', None),
                                     'value': file_path })

    def _build_file_filter_string(self) -> str:
        """file_filter_keys를 실제 파일 필터 문자열로 변환"""
        filters = []
        for key in self.file_filter_keys:
            filter_str = self.FILE_FILTERS.get(key.lower())
            if filter_str:
                filters.append(filter_str)
        return ';;'.join(filters) if filters else "All Files (*.*)"
    
    def get_file_path(self):
        return self.file_path