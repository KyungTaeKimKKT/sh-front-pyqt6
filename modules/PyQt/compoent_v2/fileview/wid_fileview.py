from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import sys, subprocess, os
from pathlib import Path
import mimetypes
from urllib.parse import unquote, urlparse
from info import Info_SW as INFO

import modules.user.utils as Utils
import tempfile

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.custom_상속.custom_qstacked import Custom_QStackedWidget

class Stacked_FileViewer(Custom_QStackedWidget):

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.viewers:dict[str, callable] = {
            'pdf': self._create_pdf_viewer,
            'vector': self._create_vector_viewer,
            'cad': self._create_cad_viewer,
            # 'spreadsheet': self._create_spreadsheet_viewer,
            'image': self._create_image_viewer,
            'text': self._create_text_viewer,
            'video': self._create_video_viewer,

            # 외부 앱 실행 대상 확장자 예시
            'external_office': self._create_external_office_viewer,
            'external_zip': self._create_external_zip_viewer,
        }
        self.map_ext_to_type:dict[str, str] = {
            '.pdf': 'pdf',
            '.ai': 'vector',
            '.dwg': 'cad',
            '.dxf': 'cad',
            '.jpg': 'image',
            '.png': 'image',
            '.txt': 'text',
            '.mp4': 'video',
            '.avi': 'video',
            '.mov': 'video',
            '.wmv': 'video',
            '.mkv': 'video',

            # 외부 앱으로 실행할 확장자 지정
            '.ppt': 'external_office',
            '.pptx': 'external_office',
            '.doc': 'external_office',
            '.docx': 'external_office',
            '.zip': 'external_zip',
            '.rar': 'external_zip',
            '.xls': 'external_office',
            '.xlsx': 'external_office',
            # 필요에 따라 추가
            
        }

    def view_by_external_app(self, path) -> None:
        local_path = Utils.func_filedownload( path, "temp" )
        file_path = Path(local_path)
        if not file_path.exists():
            return Utils.QMsg_critical(None, title="외부프로그램으로 파일 열기 실패", text=f"파일이 존재하지 않습니다: {file_path}")
        
        try:
            match INFO.OS:
                case 'Windows':
                    ### ✅ os.startfile 는 Windows 전용 함수입니다.
                    os.startfile(str(file_path))  # 실패 시 OSError 발생
                case 'Linux':
                    subprocess.Popen(['xdg-open', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case 'Darwin':
                    subprocess.Popen(['open', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case _:
                    Utils.QMsg_critical(None, title="지원하지 않는 OS입니다.", text=f"지원하지 않는 OS입니다: {INFO.OS}")
            # 성공 시 메시지 위젯 없음

        except Exception as e:
            logger.warning(f"외부 프로그램으로 파일 실행 실패: {file_path} -> {e}")
            Utils.QMsg_critical(None, title="외부프로그램으로 파일 열기 실패", text=f"이 파일을 열 수 있는 프로그램이 설치되어 있지 않거나,\n실행 중 문제가 발생했습니다:\n\n{file_path}")
 

    def _create_external_zip_viewer(self, path):
        """ 외부 프로그램으로 파일 열기 """
        local_path = Utils.func_filedownload( path, "temp" )
        file_path = Path(local_path)
        if not file_path.exists():
            return QLabel(f"파일이 존재하지 않습니다: {file_path}")
        
        try:
            match INFO.OS:
                case 'Windows':
                    ### ✅ os.startfile 는 Windows 전용 함수입니다.
                    os.startfile(str(file_path))  # 실패 시 OSError 발생
                case 'Linux':
                    subprocess.Popen(['xdg-open', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case 'Darwin':
                    subprocess.Popen(['open', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case _:
                    return QLabel("지원하지 않는 OS입니다.")
            # 성공 시 메시지 위젯 없음
            return QLabel(f"{file_path.name} 파일을 외부 프로그램으로 실행했습니다.")
        except Exception as e:
            logger.warning(f"외부 프로그램으로 파일 실행 실패: {file_path} -> {e}")
            QMessageBox.warning(self, "파일 열기 실패", f"이 파일을 열 수 있는 프로그램이 설치되어 있지 않거나,\n실행 중 문제가 발생했습니다:\n\n{file_path}")
            return QLabel(f"외부 프로그램으로 열 수 없습니다: {file_path.name}")

            
    def _create_external_office_viewer(self, path):
        """ 외부 프로그램으로 파일 열기 """
        local_path = Utils.func_filedownload( path, "temp" )
        file_path = Path(local_path)
        if not file_path.exists():
            return QLabel(f"파일이 존재하지 않습니다: {file_path}")
        
        try:
            match INFO.OS:
                case 'Windows':
                    ### ✅ os.startfile 는 Windows 전용 함수입니다.
                    os.startfile(str(file_path))  # 실패 시 OSError 발생
                case 'Linux':
                    subprocess.Popen(['libreoffice', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case 'Darwin':
                    subprocess.Popen(['open', str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                case _:
                    return QLabel("지원하지 않는 OS입니다.")
            # 성공 시 메시지 위젯 없음
            return QLabel(f"{file_path.name} 파일을 외부 프로그램으로 실행했습니다.")
        except Exception as e:
            logger.warning(f"외부 프로그램으로 파일 실행 실패: {file_path} -> {e}")
            QMessageBox.warning(self, "파일 열기 실패", f"이 파일을 열 수 있는 프로그램이 설치되어 있지 않거나,\n실행 중 문제가 발생했습니다:\n\n{file_path}")
            return QLabel(f"외부 프로그램으로 열 수 없습니다: {file_path.name}")




    def add_file(self, path):
        file_name = Path(unquote(path)).name
        file_type = self._get_file_type(path)
        if not path.startswith(('http://', 'https://')):
            path = INFO.URI+path.replace('//', '/')   
        viewer = self._create_viewer(path, file_type)
        self.addWidget(file_name, viewer)
        self.setCurrentWidget(file_name)


    def remove_file(self, path):
        file_name = Path(unquote(path)).name
        self.removeWidget(file_name)

    def setCurrentByName(self, file_name):
        self.setCurrentWidget(file_name)

    def _get_file_type(self, path):
        ext = Path(path).suffix.lower()
        # 외부 앱 실행 대상 확장자 우선 체크
        value = self.map_ext_to_type.get(ext, "unknown")
        if value == "unknown":
            import mimetypes
            mime_type, _ = mimetypes.guess_type(path)
            if mime_type:
                return mime_type.split('/')[0]
            else:
                return 'unknown'
        return value
        
        if 'external' in value:
            return value
        else:
            # 기존 방식 유지
            if path.startswith(('http://', 'https://')) or path.startswith('/media/'):
                return self.map_ext_to_type.get(ext, 'unknown')
            else:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(path)
                if mime_type:
                    return mime_type.split('/')[0]
                else:
                    return 'unknown'


    
    def _get_display_name(self, path):
        """경로에서 파일 이름을 추출하고 한글로 디코딩"""
        if path.startswith(('http://', 'https://')):
            # URL에서 파일명 추출
            parsed = urlparse(path)
            filename = Path(parsed.path).name
        else:
            # 로컬 경로에서 파일명 추출QtWidget
            filename = Path(path).name
        
        # URL 인코딩된 문자열을 디코딩
        return unquote(filename)

    def _create_viewer(self, path:str, file_type:str):
        if INFO.IS_DEV:
            logger.debug(f"path: {path} : file_type: {file_type}")
            logger.debug(f"self._get_display_name(path):{self._get_display_name(path)}")
        viewer_func = self.viewers.get(file_type, None)
        if callable(viewer_func):
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

        from modules.PyQt.compoent_v2.imageViewer.imageviwer import ImageViewer_With_GraphicsView #ImageViewer
        wid = ImageViewer_With_GraphicsView(self, url=path, is_Edit=False )
        wid.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        wid.setMinimumSize(400, 400)
        return wid

    
    def _create_text_viewer(self, path):
        # 텍스트 뷰어 구현
        return QLabel(f"텍스트 뷰어 구현 필요: {self._get_display_name(path)}")
    
    def _create_video_viewer(self, path):
        # from modules.PyQt.compoent_v2.movie_player.movie_player_vlc import MoviePlayer
        # return MoviePlayer(self, url=path, auto_play=True )
        from modules.PyQt.compoent_v2.movie_player.movie_player_qt import MoviePlayer
        return MoviePlayer(self, url=path )

    



class FileViewer_Dialog(QDialog):
    """
    파일 뷰어 다이얼로그
    kwargs : 
        files_list : 파일 경로 리스트
    """
    def __init__(self, parent: QWidget = None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("파일 뷰어")
        self.setMinimumSize(1000, 1000)
        self.kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.mapping_files: dict[str, str] = {}
        self.file_list: list[str] = []
        self.current_index = -1

        self.init_ui()

        if self.kwargs and 'files_list' in self.kwargs:
            self.files_list = self.kwargs['files_list']
            if isinstance(self.files_list, list):
                for file_path in self.files_list:
                    self.add_file(file_path)
            elif isinstance(self.files_list, str):
                self.add_file(self.files_list)

    def init_ui(self):
        self.vlayout = QVBoxLayout(self)

        # 상단 컨트롤 패널
        control_widget = QWidget()
        control_layout = QHBoxLayout()

        self.btn_prev = QPushButton("←")
        self.btn_prev.clicked.connect(self.prev_file)
        control_layout.addWidget(self.btn_prev)

        self.combo_files = QComboBox()
        self.connect_combo_files()
        control_layout.addWidget(self.combo_files)

        self.btn_next = QPushButton("→")
        self.btn_next.clicked.connect(self.next_file)
        control_layout.addWidget(self.btn_next)

        self.label_page_info = QLabel("0 / 0")
        control_layout.addWidget(self.label_page_info)
        
        control_layout.addStretch()
        self.pb_open_by_localsetting = QPushButton("열기(PC에 설치된 프로그램)")
        self.pb_open_by_localsetting.clicked.connect(self.open_by_localsetting)
        control_layout.addWidget(self.pb_open_by_localsetting)

        control_widget.setLayout(control_layout)
        self.vlayout.addWidget(control_widget)

        self.stacked_file_viewer = Stacked_FileViewer(self)
        self.vlayout.addWidget(self.stacked_file_viewer)
        self.stacked_file_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resize(1000, 1000)
        self.setLayout(self.vlayout)

    def open_by_localsetting(self):
        def _index_valid(index:int):
            return 0 <= index < len(self.file_list)
        
        index = self.combo_files.currentIndex()
        if _index_valid(index):
            path = self.combo_files.itemData(index)
            self.stacked_file_viewer.view_by_external_app(path)


    def add_file(self, path:str):
        file_name = Path(unquote(path)).name
        if self.combo_files.findText(file_name) != -1:
            self.combo_files.setCurrentText(file_name)
            return
        self.disconnect_combo_files()
        self.mapping_files[file_name] = path
        self.file_list.append(file_name)
        self.combo_files.addItem(file_name, userData=path)
        self.stacked_file_viewer.add_file(path)
        self.combo_files.setCurrentText(file_name)
        self.stacked_file_viewer.setCurrentByName(file_name)
        self.update_ui_state()
        self.connect_combo_files()

        ### 도저히 최초 것이 적게 되는거 해결 못함.    
        QTimer.singleShot(0, lambda: self.btn_prev.click())
        QTimer.singleShot(100, lambda: self.btn_next.click())

    def disconnect_combo_files(self):
        try:
            self.combo_files.currentIndexChanged.disconnect()
        except Exception as e:
            logger.error(f"disconnect_combo_files: {e}")
    
    def connect_combo_files(self):
        try:
            self.combo_files.currentIndexChanged.connect(self.on_file_changed)
        except Exception as e:
            logger.error(f"connect_combo_files: {e}")

    def remove_file(self, path):
        file_name = Path(unquote(path)).name
        if file_name in self.mapping_files:
            index = self.file_list.index(file_name)
            self.combo_files.removeItem(index)
            self.file_list.pop(index)
            self.stacked_file_viewer.remove_file(path)
            del self.mapping_files[file_name]
            
            if self.file_list:
                self.combo_files.setCurrentIndex(min(index, len(self.file_list) - 1))
            else:
                self.current_index = -1
            self.update_ui_state()

    def on_file_changed(self, index):
        if 0 <= index < len(self.file_list):
            self.current_index = index
            file_name = self.file_list[index]
            self.stacked_file_viewer.setCurrentWidget(file_name)
            self.update_ui_state()
            

    def prev_file(self):
        if self.current_index > 0:
            self.combo_files.setCurrentIndex(self.current_index - 1)

    def next_file(self):
        if self.current_index < len(self.file_list) - 1:
            self.combo_files.setCurrentIndex(self.current_index + 1)

    def update_ui_state(self):
        total = len(self.file_list)
        self.btn_prev.setEnabled(total > 1 and self.current_index > 0)
        self.btn_next.setEnabled(total > 1 and self.current_index < total - 1)
        self.label_page_info.setText(f"{self.current_index + 1 if total else 0} / {total}")



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