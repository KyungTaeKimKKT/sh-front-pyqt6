from __future__ import annotations
from modules.common_import_v3 import *

import requests
import base64

class WorkerSignals(QObject):
    finished = pyqtSignal(dict)

class ImageFetchWorker(QRunnable):
    def __init__(self,parent=None, rtsp_url:str=None, url:str=None):
        super().__init__()
        self.signals = WorkerSignals()
        self.url = self.get_url(url)
        self.rtsp_url = rtsp_url
        self.setAutoDelete(True)

    def get_url(self, url:str):
        if not url:
            raise ValueError("url is required")

        if 'http' not in url:
            return f"{INFO.URI}{url}"
        else:
            return url

    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            contents = response.content if response.ok else None
            self.signals.finished.emit({
                'rtsp_url': self.rtsp_url,
                'result': response.ok,
                'contents': contents,
                'error': None if response.ok else f"{response.status_code} {response.reason}"
            })
        except Exception as e:
            self.signals.finished.emit({'rtsp_url': self.rtsp_url, 'result': False, 'contents': None, 'error': str(e)})


class LiveView(QWidget):
    def __init__(self, parent=None, db_settings:list[dict] = [], **kwargs):
        super().__init__(parent)
        self.db_settings = db_settings
        self.map_url_to_label:dict[str, QLabel] = {}
        self.last_update:dict[str, datetime] = {}  # 마지막 업데이트 시간 저장
        self.period_no_data:int = kwargs.get('period_no_data', 5)

        self.active_workers:dict[str, ImageFetchWorker] = {}

        if self.db_settings:
            self.setup_ui()

        # 1초마다 체크하는 타이머
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_stale_data)
        self.check_timer.start(1000)  # 1초

    def load_plot_data(self, api_datas:list[dict]):
        self.db_settings = api_datas
        self.setup_ui()

    def setup_ui(self):
        if getattr(self, 'main_layout', None):  
            Utils.deleteLayout(self.main_layout)

        self.setWindowTitle("PyQt6 Multi LiveView")
        self.resize(1600, 900)

        self.main_layout = QGridLayout(self)

        # 채널별 QLabel 준비
        for i, setting_dict in enumerate(self.db_settings):
            lbl = QLabel(f"{setting_dict.get('name', 'Unknown')}", self)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: black; color: white;")
            lbl.setScaledContents(True)  # pixmap 크기에 맞춰 확장
            self.map_url_to_label[setting_dict.get('url', 'None')] = lbl
            self.main_layout.addWidget(lbl, i // 3, i % 3)

        self.update_grid()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, 'main_layout', None):
            self.update_grid()

    def closeEvent(self, event):
        for worker in self.active_workers.values():
            worker.close()
        self.active_workers.clear()
        self.check_timer.stop()
        super().closeEvent(event)

    def update_grid(self):
        """윈도우 크기에 따라 grid 열 수 변경"""
        width = self.width()
        if width < 1200:
            cols = 2
        elif width < 1800:
            cols = 3
        else:
            cols = 4

        # 레이아웃 리셋 후 다시 배치
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            self.main_layout.removeWidget(widget)

        for i, lbl in enumerate(self.map_url_to_label.values()):
            row, col = divmod(i, cols)
            self.main_layout.addWidget(lbl, row, col)

    def set_data(self, data:dict):
        # timestamp 파싱
        ts = None
        ts_str = data.get('timestamp')
        if ts_str:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


        for rtsp_url, _dict in data.get('message', {}).items():
            label = self.map_url_to_label.get(rtsp_url, None)
            if not label:
                continue

            self.last_update[rtsp_url] = ts

            fetch_url = _dict.get('file_path', None)
            worker = ImageFetchWorker(url= fetch_url, rtsp_url= rtsp_url)
            worker.signals.finished.connect(self.update_frame_from_content)
            self.active_workers[rtsp_url] = worker
            QThreadPool.globalInstance().start(worker)

    def set_data_via_base64(self, data:dict):
        # timestamp 파싱
        ts = None
        ts_str = data.get('timestamp')
        if ts_str:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

        for rtsp_url, _dict in data.get('message', {}).items():
            label = self.map_url_to_label.get(rtsp_url, None)
            if not label:
                continue
            self.last_update[rtsp_url] = ts

            base64_str= _dict.get('image', None)

            if not base64_str:
                continue
            img_bytes = base64.b64decode(base64_str)

            pixmap = QPixmap()
            if pixmap.loadFromData(img_bytes):
                # 원본 비율 유지 + 라벨 크기에 맞춤
                scaled_pixmap = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                label.setPixmap(scaled_pixmap)
            else:
                label.setText("Invalid Image")


    def update_frame_from_content(self, data:dict):
        rtsp_url = data.get('rtsp_url', None)
        if not rtsp_url:
            return
        
        #### 완료된 worker 제거
        self.active_workers.pop(rtsp_url, None)

        label = self.map_url_to_label.get(rtsp_url, None)
        if label is None:
            print (f"label not found: {rtsp_url}, {self.map_url_to_label.keys()}")
            return
        

        result = data.get('result', False)
        if not result:
            label.setText(f"Error: {data.get('error', 'Unknown error')}")
            return
    
        contents = data.get('contents', None)
        if contents:
            pixmap = QPixmap()
            if pixmap.loadFromData(contents):
                # 원본 비율 유지 + 라벨 크기에 맞춤
                scaled_pixmap = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                label.setPixmap(scaled_pixmap)
            else:
                label.setText("Invalid Image")
            # print(f"download_file_from_url 소요시간: {Utils.get_소요시간(s_time)}")

    def check_stale_data(self):
        """마지막 데이터가 5초 이상 오래되면 'NO data' 표시"""
        now = datetime.now()
        for url, label in self.map_url_to_label.items():
            last_ts = self.last_update.get(url)
            if not last_ts or (now - last_ts > timedelta(seconds=self.period_no_data)):
                label.setText(f"NO data (last update: {last_ts.strftime('%H:%M:%S') if last_ts else 'N/A'})")
            
    def update_frame_from_file(self, channel_id: int, file_path: str):
        """WS에서 받은 media 파일 경로를 QLabel에 표시"""
        label = self.map_id_to_label.get(channel_id, None)
        #### 1. 유효성 검증
        if not label:
            logger.error(f"Label not found for channel_id: {channel_id}")
            return
        
        if not os.path.exists(file_path):
            logger.error(f"Label not found for channel_id: {channel_id}")
            return

        #### 2. 파일 경로 유효성 검증
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            label.setText("Invalid Image")
            return

        #### 3. 최종 image 표시
        label.setPixmap(
            pixmap.scaled(
                label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )