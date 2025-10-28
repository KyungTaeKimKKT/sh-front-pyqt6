from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import os
from datetime import datetime



from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class File_Upload_ListWidget(QWidget):
    def __init__(self, parent:QWidget, initial_files:Optional[list[str]]=None,  is_readonly:bool=False, **kwargs):
        super().__init__(parent)
        self.initial_files = initial_files
        self.is_readonly = is_readonly
        self.is_Editable = not is_readonly
        self.file_id_map:dict[str,int] = {} ### 파일 경로에 해당하는 'id' 맵핑
        # 아이콘 경로 설정
        self.icon_paths = {
            'server': os.path.join(os.path.dirname(__file__), 'icons', 'server-icon.png'),
            'local': os.path.join(os.path.dirname(__file__), 'icons', 'local-icon.png')
        }
        self.initUI(initial_files)

        # 컨텍스트 메뉴 설정 추가
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.update_kwargs(**kwargs) 

    def show_context_menu(self, position):
        menu = QMenu()
        preview_action = menu.addAction("파일 미리보기")
        action = menu.exec(self.list_widget.mapToGlobal(position))
        
        if action == preview_action:
            current_item = self.list_widget.itemAt(position)
            if current_item:
                self.show_file_preview(current_item.data(Qt.ItemDataRole.UserRole))

    def show_file_preview(self, file_path):
        preview_dialog = FilePreviewDialog(file_path, parent=self)
        preview_dialog.exec()

        # kwargs 업데이트 메소드 추가
    def update_kwargs(self, **kwargs):
        if 'files' in kwargs and kwargs.get('files'):
            self.set_initial_files(kwargs['files'])

        ic ( kwargs )
        if 'is_Editable' in kwargs:
            self.is_Editable = kwargs['is_Editable']

        self.list_widget.setAcceptDrops(self.is_Editable)
        self.list_widget.dragEnterEvent = self.dragEnterEvent
        self.list_widget.dropEvent = self.dropEvent        
        self.add_btn.setVisible(self.is_Editable)
        self.delete_btn.setVisible(self.is_Editable)

    # 드래그 앤 드롭 이벤트 핸들러 추가
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            self.add_item(file, 'local')

    def initUI(self, initial_files):
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 리스트 위젯 생성
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)


        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
    
        self.add_btn = QPushButton('파일 추가')
        self.add_btn.clicked.connect(self.add_files)
        
        # 삭제 버튼
        self.delete_btn = QPushButton('삭제')
        self.delete_btn.clicked.connect(self.delete_selected)
    
        # 버튼 레이아웃에 추가
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)       
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        
        # 초기 파일 목록 설정
        if initial_files is not None and initial_files:
            self.set_initial_files(initial_files)
    
    def set_initial_files(self, files):        
        for file_info in files:
            if isinstance(file_info, dict):             
                if 'file' in file_info:
                    filename = file_info['file']
                    self.file_id_map[filename] = file_info.get('id', -1)  # 'id'가 없으면 -1로 설정
                    if filename.startswith(('http://', 'https://')):
                        self.add_item(filename, 'server')
                    else:
                        self.add_item(filename, 'local')
            elif isinstance(file_info, str):
                if file_info.startswith(('http://', 'https://')):
                    self.add_item(file_info, 'server')
                else:
                    self.add_item(file_info, 'local')
            else:
                raise ValueError(f"지원하지 않는 파일 타입입니다: {type(file_info)}")
    
    def add_item(self, filename, icon_type):
        item = QListWidgetItem()
        if icon_type == 'server':
            item.setIcon(QIcon(':/listwidget/서버'))
            # URL에서 파일명 추출 및 한글 디코딩
            from urllib.parse import unquote
            basename = os.path.basename(unquote(filename))
        else:
            item.setIcon(QIcon(':/listwidget/local'))
            basename = os.path.basename(filename)
        item.setText(basename)
        item.setData(Qt.ItemDataRole.UserRole, filename)
        self.list_widget.addItem(item)
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "파일 선택", "", "All Files (*.*)")
        for file in files:
            self.add_item(file, 'local')
    
    def delete_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
    
    def getValue(self):
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            # 서버/로컬 파일 구분
            if file_path.startswith(('http://', 'https://')):
                file_type = 'server'
            else:
                file_type = 'local'
            # 파일 경로에 해당하는 'id' 가져오기
            file_id = self.file_id_map.get(file_path, -1)

            result.append({
                'file': file_path,
                'type': file_type,
                'id': file_id
            })
        return result
    
    def get_value(self):
        return self.getValue()

# FilePreviewDialog 클래스 추가
class FilePreviewDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('파일 미리보기')
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # 파일 경로 표시
        path_label = QLabel(f"파일 경로: {self.file_path}")
        layout.addWidget(path_label)
        
        # 파일 내용 표시
        content_area = QTextEdit()
        content_area.setReadOnly(True)
        
        try:
            if self.file_path.startswith(('http://', 'https://')):
                content_area.setText("원격 파일은 미리보기를 지원하지 않읍니다.")
            else:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_area.setText(content)
        except Exception as e:
            content_area.setText(f"파일을 열 수 없읍니다: {str(e)}")
        
        layout.addWidget(content_area)
        
        # 닫기 버튼
        close_btn = QPushButton('닫기')
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.initUI()
    
#     def initUI(self):
#         self.setWindowTitle('파일 업로드 위젯')
#         self.setGeometry(100, 100, 600, 400)
        
#         # 초기 파일 리스트 예시
#         initial_files = [
#             {'file': 'http://example.com/file1.txt'},
#             {'file': 'C:/local/file2.txt'}
#         ]
        
#         # FileUploadListWidget 생성 및 설정
#         self.file_widget = FileUploadListWidget(initial_files)
#         self.setCentralWidget(self.file_widget)


# from PyQt6.QtWidgets import QMainWindow, QApplication
# import traceback
# from modules.logging_config import get_plugin_logger

# # 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
# logger = get_plugin_logger()


# #from imageViewer import ImageViewer

# if __name__ == '__main__':
#     app = QApplication([])
#     window = MainWindow()
#     window.show()
#     app.exec()