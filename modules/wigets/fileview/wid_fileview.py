from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
import mimetypes
from urllib.parse import unquote, urlparse
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_FileViewer(QWidget):
    """
    파일 뷰어 위젯
    kwargs : 
        paths : 파일 경로 리스트    
    """
    def __init__(self, paths: list, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths

        # 스크롤 영역 생성
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        
        # 컨테이너 위젯 생성
        self.container = QWidget()
        self.vlayout = QVBoxLayout(self.container)
        
        # 스크롤 영역에 컨테이너 설정
        self._scroll.setWidget(self.container)
        
        # 메인 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._scroll)
        
        self._init_ui()
    
    def _init_ui(self):
        for path in self.paths:
        # 파일 이름 추출 및 한글 디코딩
            file_name = Path(unquote(path)).name
            
            # 파일 타입 확인
            file_type = self._get_file_type(path)
            
            # 파일명 레이블 생성
            name_label = QLabel(file_name)
            name_label.setStyleSheet("background-color:black;color:yellow;font-weight: bold; padding: 5px;border:None;") 
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 중앙 정렬 추가            
            
            # 뷰어 생성
            viewer = self._create_viewer(path, file_type)
            
            # 파일명과 뷰어를 담을 컨테이너
            file_container = QWidget()
            file_container.setObjectName("fileContainer")  # 컨테이너 식별자 추가
            file_container.setStyleSheet("""
                #fileContainer {
                    border: 3px solid #cccccc;
                    border-radius: 5px;
                    background-color: #ffffff;
                    margin: 5px;
                }
                #fileContainer > QWidget {
                    border: none;
                    background-color: transparent;
                }
            """)
            
            # 컨테이너 레이아웃
            container_layout = QVBoxLayout(file_container)
            container_layout.addWidget(name_label)
            if viewer:
                # if file_type == 'cad':
                #     self.finished.connect ( lambda viewer : self.cleanup(viewer))
                container_layout.addWidget(viewer)
            
            # 메인 레이아웃에 추가
            self.vlayout.addWidget(file_container)
        
        # 남은 공간을 위쪽으로 정렬
        self.vlayout.addStretch()

    def cleanup(self, viewer:QWidget):
        viewer.makeCurrent()
        viewer.doneCurrent()
    
    def _get_file_type(self, path):
        # URL인 경우
        if path.startswith(('http://', 'https://')):
            # 파일 확장자로 타입 추측
            ext = Path(path).suffix.lower()
        else:
            # 로컬 파일인 경우
            mime_type, _ = mimetypes.guess_type(path)
            if mime_type:
                return mime_type.split('/')[0]
            
        return self._get_type_from_extension(Path(path).suffix.lower())
    
    def _get_type_from_extension(self, ext):
        ext_map = {
            '.pdf': 'pdf',
            '.ai': 'vector',
            '.dwg': 'cad',
            '.dxf': 'cad',
            '.xls': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.jpg': 'image',
            '.png': 'image',
            '.txt': 'text',
            '.mp4': 'video',
            '.avi': 'video',
            '.mov': 'video',
            '.wmv': 'video',
            '.mkv': 'video',
            # 필요한 확장자 추가
        }
        return ext_map.get(ext, 'unknown')
    
    def _get_display_name(self, path):
        """경로에서 파일 이름을 추출하고 한글로 디코딩"""
        if path.startswith(('http://', 'https://')):
            # URL에서 파일명 추출
            parsed = urlparse(path)
            filename = Path(parsed.path).name
        else:
            # 로컬 경로에서 파일명 추출
            filename = Path(path).name
        
        # URL 인코딩된 문자열을 디코딩
        return unquote(filename)

    def _create_viewer(self, path, file_type):
        # 파일 타입에 따른 적절한 뷰어 위젯 생성
        viewers = {
            'pdf': self._create_pdf_viewer,
            'vector': self._create_vector_viewer,
            'cad': self._create_cad_viewer,
            'spreadsheet': self._create_spreadsheet_viewer,
            'image': self._create_image_viewer,
            'text': self._create_text_viewer,
            'video': self._create_video_viewer,
        }
        
        viewer_func = viewers.get(file_type)
        if viewer_func:
            return viewer_func(path)
        return QLabel(f"지원하지 않는 파일 형식: {self._get_display_name(path)}")
    
    # 각 파일 타입별 뷰어 생성 메서드
    def _create_pdf_viewer(self, path) -> QWidget:
        from modules.PyQt.compoent_v2.pdfViwer.pdfviewer_pymupdf import PDFViewer
        return PDFViewer(self, path)

    
    def _create_vector_viewer(self, path):
        from modules.PyQt.compoent_v2.imageViewer.imageviwer import ImageViewer
        return ImageViewer(self, url=path, is_Edit=False )
    
    def _create_cad_viewer(self, path):
        return QLabel(f"캐드 뷰어 구현 필요: {self._get_display_name(path)}")

        # DWG 파일 뷰어 구현
        from modules.PyQt.compoent_v2.cadview.cad_viewer import CADViewer
        dlg = QDialog(self)
        vlayout = QVBoxLayout()
        vlayout.addWidget (  CADViewer(self, url=path ) )
        dlg.setLayout(vlayout)
        dlg.show()

        return None
    
    def _create_spreadsheet_viewer(self, path):
        # Excel 파일 뷰어 구현
        return QLabel(f"Spreadsheet 뷰어 구현 필요: {self._get_display_name(path)}")
    
    def _create_image_viewer(self, path):
        from modules.PyQt.compoent_v2.imageViewer.imageviwer import ImageViewer
        return ImageViewer(self, url=path, is_Edit=False )

    
    def _create_text_viewer(self, path):
        # 텍스트 뷰어 구현
        return QLabel(f"텍스트 뷰어 구현 필요: {self._get_display_name(path)}")
    
    def _create_video_viewer(self, path):
        from modules.PyQt.compoent_v2.movie_player.movie_player_vlc import MoviePlayer
        return MoviePlayer(self, url=path, auto_play=True )