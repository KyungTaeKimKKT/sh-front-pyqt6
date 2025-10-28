from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v3 import *
import cv2
import numpy as np

import mediapipe as mp

from plugin_main.menus.ai.face_register import MainImageLabel, Mixin_MediaPipe
from plugin_main.menus.ai.mixin_face import Mixin_Face
from modules.PyQt.compoent_v2.grid.container_lb_pixmap import Custom_Grid

from plugin_main.menus.ai.dlg_face_result import RecognitionResultDialog



if TYPE_CHECKING:
    from main_test  import WSClient

class ImagesLabel(QLabel):
    def __init__(self, parent=None, image:np.ndarray=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { background-color: #000000; }")
        if image is not None:
            self.set_image(image)
    
    def set_image(self, image:np.ndarray):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], rgb_image.shape[2]*rgb_image.shape[1], QImage.Format.Format_RGB888)
        qimg = qimg.scaled(self.width(), self.height())
        self.setPixmap(QPixmap.fromImage(qimg))
        

class Dlg_Status_Verify(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setWindowTitle("얼굴 인식 상태")
        # self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint)
        self.setFixedSize(600, 600)
        self.setup_ui()

        
    def setup_ui(self):     
        self.main_layout = QVBoxLayout(self)
        self.tb_status = QTextBrowser(self)
        self.tb_status.setAcceptRichText(True)
        self.tb_status.setOpenExternalLinks(True)
        self.tb_status.setText("Status: Ready")
        self.main_layout.addWidget(self.tb_status)
        self.images_layout = QHBoxLayout()
        self.images_layout.setContentsMargins(0, 0, 0, 0)
        self.images_layout.setSpacing(0)
        self.main_layout.addLayout(self.images_layout)
        self.setLayout(self.main_layout)

    def set_status(self, status:str):
        self.tb_status.setText(status)

    def add_status(self, status:str):
        current_text = self.tb_status.toPlainText()
        self.tb_status.setText(f"{current_text}\n{status}")

    def set_images(self, images:list[np.ndarray]):
        Utils.clearLayout(self.images_layout)
        for i, img in enumerate(images):
            label = ImagesLabel()
            label.set_image(img)
            self.images_layout.addWidget(label)


class FaceRecognizeDialog_with_grpc(QDialog, Mixin_MediaPipe, Mixin_Face):
    """
    - 열리자마자 Mediapipe로 자동 감지/표시
    - 버튼 1개: '인식 요청'
      > 짧게 N장 샘플 수집(중복 방지: 시간/움직임 게이트)
      > 서버 /verify/ 호출 (필드명은 프로젝트에 맞춰 조정)
    - lb_status에 결과 표시
    """
    def __init__(self, parent=None, verify_url:str="ai-face/user-face/recognize_via_rpc/", user_id:int=None, api_client=None,  is_hidden:bool=True,**kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.is_hidden = is_hidden
        self.is_hidden_dlg_status_verify = kwargs.get('is_hidden_dlg_status_verify', True)
        if self.is_hidden:
            self.hide()

        self.start_time = time.perf_counter()
        self.verify_url = verify_url  # 서버 엔드포인트 맞춰 수정
        self.user_id = user_id                                      # 필요 시 None 허용
        self.api = api_client                                       # APP.API 같은 래퍼 주입

        # 상태
        self.frame: np.ndarray = None
        self.probe_images: list[np.ndarray] = []
        self.last_bbox = None
        self.last_capture_time = 0.0

        # Mediapipe (근거리 웹캠이면 model_selection=0 권장)
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)

        self.workers:list[Worker_by_signal] = []

        self.setup_ui()
        self.connect_signals()

        self.mixin_init_camera()

    def set_images(self, images:list[np.ndarray]):
        return 
        if not hasattr(self, 'grid_layout') : return

        widgets = [ ImagesLabel(image=image) for image in images ]
        self.grid_layout.set_widgets(widgets)

    def connect_signals(self):
        self.btn_verify.clicked.connect(self.on_click_verify)

    def disconnect_signals(self):
        try:
            self.btn_verify.clicked.disconnect(self.on_click_verify)
        except Exception as e:
            logger.error(f"disconnect_signals : {e}")

    def setup_ui(self):
        # UI
        self.setWindowTitle("Face Verify")
        self.image_label = MainImageLabel()
        self.lb_status = QLabel("Status: Ready")
        self.btn_verify = QPushButton("인식 요청")  # 한 개만

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.lb_status)
        layout.addWidget(self.btn_verify)

        self.sub_container = QWidget()
        self.grid_layout = Custom_Grid(self.sub_container)

        layout.addWidget(self.sub_container)

        self.setLayout(layout)



    # -------------------- 수집 로직 --------------------
    def should_keep(self, bbox, min_interval=0.1, min_movement=6) -> bool:
        """
        중복 방지:
        - min_interval: 최근 캡처 시각과 최소 간격(초)
        - min_movement: 이전 bbox 중심과의 최소 이동 픽셀
        """
        now = time.time()
        if (now - self.last_capture_time) < min_interval:
            return False

        if self.last_bbox is not None:
            (x1, y1, x2, y2) = bbox
            cx, cy = (x1 + x2)//2, (y1 + y2)//2
            (lx1, ly1, lx2, ly2) = self.last_bbox
            lcx, lcy = (lx1 + lx2)//2, (ly1 + ly2)//2
            dist = np.hypot(cx - lcx, cy - lcy)
            if dist < min_movement:
                return False

        return True

    def try_collect_probe(self, frame: np.ndarray, det, target_size=(160,160)) -> bool:
        """
        감지된 얼굴에서 160x160 crop 추출해 probe_images에 추가.
        - 성공 시 True.
        """
        x1, y1, x2, y2 = self.get_det_bbox(frame, det)

        if not self.should_keep((x1, y1, x2, y2)):
            return False

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return False

        crop = np.ascontiguousarray(cv2.resize(crop, target_size))
        self.probe_images.append(crop)
        self.last_capture_time = time.time()
        self.last_bbox = (x1, y1, x2, y2)
        return True

    # -------------------- 프레임 업데이트 --------------------
    def update_frame(self):
        if self.cap is None:
            return
        ok, frame = self.cap.read()
        if not ok:
            return

        self.frame = frame.copy()
        display_frame = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)

        if results.detections:
            # 표시용 오버레이
            display_frame, cropped_face = self.render_frame_by_mediapipe( frame, display_frame, results)
            # 수집은 자동으로 계속 하지는 않고, '인식 요청' 시에 한 번에 모음
        self.image_label.set_image(display_frame)

    # -------------------- 버튼: 인식 요청 --------------------
    def on_click_verify(self):
        """
            1) 잠깐 동안(N장 모을 때까지 or timeout) 자동 수집
            2) 서버에 업로드 → 결과 표시
        """
        if APP.get_DLG_LOADING() is not None:
            APP.get_DLG_LOADING().start_display(start_time=1000)
        self.lb_status.setText("Status: 수집 중...")
        # self.collect_burst_async(n=5, timeout=3.0)  # 필요 시 조정 (개수/시간)

        ########## 수집 중 ##########
        worker = Worker_by_signal(self.collect_burst, n=5, timeout=3.0)
        worker.signal.finished.connect(self.on_hanlde_collect)
        worker.start()
        self.workers.append(worker)


    def get_send_data_and_files(self) -> tuple[dict, list]:
        files = []
        for i, img in enumerate(self.probe_images):
            files.append(("images", self.ndarray_to_file(img, f"probe_{i}.jpg")))
        data = {}
        if self.user_id is not None:
            data["user_id"] = self.user_id            
        data['ws_url'] = getattr(self, 'ws_url', '')
        return data, files

    def send_verify(self):
        # APP.get_DLG_LOADING().start_display(start_time=1000)
        try:
            data, files = self.get_send_data_and_files()
            worker = Worker_by_signal(APP.API.Send, url=self.verify_url, dataObj={'id': -1}, sendData=data, sendFiles=files)
            worker.signal.finished.connect(self.on_hanlde_verify)
            worker.start()
            self.workers.append(worker)

        except Exception as e:
            self.lb_status.setText(f"Status: 예외 - {e}")
        finally:
            # 다음 요청 대비 초기화
            self.probe_images.clear()
            self.last_bbox = None
            self.last_capture_time = 0.0

    def on_hanlde_collect(self, worker:Worker_by_signal, is_ok:bool, response:any):
        self.workers.remove(worker)
        if is_ok:
            self.start_time = time.perf_counter()
            QTimer.singleShot(0, lambda: self.show_probe_images_and_send_verify(response))
            # self.send_verify()
        else:
            self.lb_status.setText(f"Status: 수집 실패 (얼굴 부족)")

    def show_probe_images_and_send_verify(self, images):
        self.probe_images = images
        if INFO.IS_DEV:
            os.makedirs("./debug", exist_ok=True)
            for i, img in enumerate(images):
                cv2.imwrite(f"./debug/probe_image_{i}.jpg", img)
            # cv2.waitKey(0)
        self.lb_status.setText(f"Status: {len(images)} 수집 완료")
        self.send_verify()

    def on_hanlde_verify(self, worker:Worker_by_signal, is_ok:bool, response:any):
        print (f"on_hanlde_verify: {worker} {is_ok} {len(response)} ")
        _isok, _json = response ##: tuple[bool, any]
        if APP.get_DLG_LOADING() is not None:
            APP.get_DLG_LOADING().stop_display()
        if _isok:
            self.lb_status.setText(f"Status: {Utils.get_json_pretty(_json, delete_keys=['decision_images'])}")
            dlg_face_result = RecognitionResultDialog(self, result_data=_json)
            if dlg_face_result.exec():
                pass
            else:
                pass

        else:
            self.lb_status.setText(f"Status: 실패 - {_json}")

        self.workers.remove(worker)


    def collect_burst(self, n=5, timeout=3.0) -> list[np.ndarray]:
        self.probe_images.clear()
        self.last_bbox = None
        self.last_capture_time = 0.0

        t0 = time.time()
        while len(self.probe_images) < n and (time.time() - t0) < timeout:
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.frame = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb)
            if results.detections:
                self.try_collect_probe(frame, results.detections[0])
            # cv2.waitKey(1)  # 너무 빠른 루프 방지
        return self.probe_images

    def collect_burst_async(self, n=5, timeout=3.0):
        self.probe_images.clear()
        self.last_bbox = None
        self.last_capture_time = 0.0

        t0 = time.time()
        def try_capture():
            if len(self.probe_images) >= n or (time.time() - t0) > timeout:
                self.timer_capture.stop()
                return
            if self.frame is not None:
                rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                results = self.face_detector.process(rgb)
                if results.detections:
                    self.try_collect_probe(self.frame, results.detections[0])
        
        self.timer_capture = QTimer()
        self.timer_capture.timeout.connect(try_capture)
        self.timer_capture.start(30)  # 30ms마다 시도

    # -------------------- 종료 --------------------
    def closeEvent(self, e):
        print (f"closeEvent: {self}")
        try:
            if getattr(self, 'timer_capture', None):
                self.timer_capture.stop()
                self.timer_capture = None
            if getattr(self, 'timer', None):
                self.timer.stop()
                self.timer = None

            if hasattr(self, 'cap') and self.cap is not None:
                if self.cap.isOpened():
                    self.cap.release()
                self.cap = None

            # 🔑 장치 캐시 클리어 (특히 리눅스)
            if getattr(self, 'cam_index', None):
                cv2.VideoCapture(self.cam_index).release()

            if getattr(self, 'ws_manager', None) and hasattr(self.ws_manager, 'remove'):
                self.ws_manager.remove(self.ws_url)

        finally:
            super().closeEvent(e)

    def done(self, r):
        """
        exec() → accept()/reject() 로 끝날 때는 closeEvent() 자동 호출이 안 될 수 있음

        따라서 done() 오버라이드하거나, finished 시그널에서 close() 를 강제로 호출하는 게 맞음
        exec() 는 내부적으로 QDialog.accept() / QDialog.reject() 로 종료합니다.

        이 경우 실제 closeEvent() 가 트리거되지 않을 수 있음 (특히 Qt6부터).

        즉, close() 로 닫을 때만 closeEvent() 가 보장 호출돼요
        """
        print("done() called", r)
        self.close()   # 여기서 강제 close() 호출
        super().done(r)


class FaceRecognizeDialog(QDialog, Mixin_MediaPipe, Mixin_Face):
    """
    - 열리자마자 Mediapipe로 자동 감지/표시
    - 버튼 1개: '인식 요청'
      > 짧게 N장 샘플 수집(중복 방지: 시간/움직임 게이트)
      > 서버 /verify/ 호출 (필드명은 프로젝트에 맞춰 조정)
    - lb_status에 결과 표시
    """
    def __init__(self, parent=None, verify_url:str=None, user_id:int=None, api_client=None,  is_hidden:bool=True,**kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.is_hidden = is_hidden
        self.is_hidden_dlg_status_verify = kwargs.get('is_hidden_dlg_status_verify', True)
        if self.is_hidden:
            self.hide()

        self.start_time = time.perf_counter()
        self.verify_url = verify_url or "ai-face/user-face/recognize/"  # 서버 엔드포인트 맞춰 수정
        self.user_id = user_id                                      # 필요 시 None 허용
        self.api = api_client                                       # APP.API 같은 래퍼 주입

        # 상태
        self.frame: np.ndarray = None
        self.probe_images: list[np.ndarray] = []
        self.last_bbox = None
        self.last_capture_time = 0.0

        # Mediapipe (근거리 웹캠이면 model_selection=0 권장)
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)

        self.workers:list[Worker_by_signal] = []

        self.setup_ui()
        self.connect_signals()
        self.create_dlg_status_verify()

        self.mixin_init_camera()
        self.mixin_init_ws( ws_manager = kwargs.get('ws_manager', None),
                      ws_url_base = kwargs.get('ws_url_base', "broadcast/") 
                      )

    def create_dlg_status_verify(self):
        self.dlg_status_verify = Dlg_Status_Verify(self)




    def set_images(self, images:list[np.ndarray]):
        return 
        if not hasattr(self, 'grid_layout') : return

        widgets = [ ImagesLabel(image=image) for image in images ]
        self.grid_layout.set_widgets(widgets)

    def connect_signals(self):
        self.btn_verify.clicked.connect(self.on_click_verify)

    def disconnect_signals(self):
        try:
            self.btn_verify.clicked.disconnect(self.on_click_verify)
        except Exception as e:
            logger.error(f"disconnect_signals : {e}")

    def setup_ui(self):
        # UI
        self.setWindowTitle("Face Verify")
        self.image_label = MainImageLabel()
        self.lb_status = QLabel("Status: Ready")
        self.btn_verify = QPushButton("인식 요청")  # 한 개만

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.lb_status)
        layout.addWidget(self.btn_verify)

        self.sub_container = QWidget()
        self.grid_layout = Custom_Grid(self.sub_container)

        layout.addWidget(self.sub_container)

        self.setLayout(layout)



    # -------------------- 수집 로직 --------------------
    def should_keep(self, bbox, min_interval=0.1, min_movement=6) -> bool:
        """
        중복 방지:
        - min_interval: 최근 캡처 시각과 최소 간격(초)
        - min_movement: 이전 bbox 중심과의 최소 이동 픽셀
        """
        now = time.time()
        if (now - self.last_capture_time) < min_interval:
            return False

        if self.last_bbox is not None:
            (x1, y1, x2, y2) = bbox
            cx, cy = (x1 + x2)//2, (y1 + y2)//2
            (lx1, ly1, lx2, ly2) = self.last_bbox
            lcx, lcy = (lx1 + lx2)//2, (ly1 + ly2)//2
            dist = np.hypot(cx - lcx, cy - lcy)
            if dist < min_movement:
                return False

        return True

    def try_collect_probe(self, frame: np.ndarray, det, target_size=(160,160)) -> bool:
        """
        감지된 얼굴에서 160x160 crop 추출해 probe_images에 추가.
        - 성공 시 True.
        """
        x1, y1, x2, y2 = self.get_det_bbox(frame, det)

        if not self.should_keep((x1, y1, x2, y2)):
            return False

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return False

        crop = np.ascontiguousarray(cv2.resize(crop, target_size))
        self.probe_images.append(crop)
        self.last_capture_time = time.time()
        self.last_bbox = (x1, y1, x2, y2)
        return True

    # -------------------- 프레임 업데이트 --------------------
    def update_frame(self):
        if self.cap is None:
            return
        ok, frame = self.cap.read()
        if not ok:
            return

        self.frame = frame.copy()
        display_frame = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)

        if results.detections:
            # 표시용 오버레이
            display_frame, cropped_face = self.render_frame_by_mediapipe( frame, display_frame, results)
            # 수집은 자동으로 계속 하지는 않고, '인식 요청' 시에 한 번에 모음
        self.image_label.set_image(display_frame)

    # -------------------- 버튼: 인식 요청 --------------------
    def on_click_verify(self):
        """
        1) 잠깐 동안(N장 모을 때까지 or timeout) 자동 수집
        2) 서버에 업로드 → 결과 표시
        """
        APP.get_DLG_LOADING().start_display(start_time=1000)
        self.lb_status.setText("Status: 수집 중...")
        # self.collect_burst_async(n=5, timeout=3.0)  # 필요 시 조정 (개수/시간)

        ########## 수집 중 ##########
        worker = Worker_by_signal(self.collect_burst, n=5, timeout=3.0)
        worker.signal.finished.connect(self.on_hanlde_collect)
        worker.start()
        self.workers.append(worker)


    def get_send_data_and_files(self) -> tuple[dict, list]:
        files = []
        for i, img in enumerate(self.probe_images):
            files.append(("images", self.ndarray_to_file(img, f"probe_{i}.jpg")))
        data = {}
        if self.user_id is not None:
            data["user_id"] = self.user_id            
        data['ws_url'] = self.ws_url
        return data, files

    def send_verify(self):
        try:
            data, files = self.get_send_data_and_files()
            worker = Worker_by_signal(APP.API.Send, url=self.verify_url, dataObj={'id': -1}, sendData=data, sendFiles=files)
            worker.signal.finished.connect(self.on_hanlde_verify)
            worker.start()
            self.workers.append(worker)
        except Exception as e:
            self.lb_status.setText(f"Status: 예외 - {e}")
        finally:
            # 다음 요청 대비 초기화
            self.probe_images.clear()
            self.last_bbox = None
            self.last_capture_time = 0.0

    def on_hanlde_collect(self, worker:Worker_by_signal, is_ok:bool, response:any):
        self.workers.remove(worker)
        if is_ok:
            self.start_time = time.perf_counter()
            QTimer.singleShot(0, lambda: self.show_probe_images_and_send_verify(response))
            # self.send_verify()
        else:
            self.lb_status.setText(f"Status: 수집 실패 (얼굴 부족)")

    def show_probe_images_and_send_verify(self, images):
        self.probe_images = images
        if INFO.IS_DEV:
            os.makedirs("./debug", exist_ok=True)
            for i, img in enumerate(images):
                cv2.imwrite(f"./debug/probe_image_{i}.jpg", img)
            self.dlg_status_verify.set_images(images)
            # cv2.waitKey(0)
        self.lb_status.setText(f"Status: {len(images)} 수집 완료")
        self.send_verify()

    def on_hanlde_verify(self, worker:Worker_by_signal, is_ok:bool, response:any):
        print (f"on_hanlde_verify: {worker} {is_ok} {len(response)} ")
        _isok, _json = response ##: tuple[bool, any]
        if _isok:
            self.lb_status.setText(f"Status: {_json}")
            self.dlg_status_verify.add_status( f" result: {_json}")
            self.dlg_status_verify.add_status( f" request time: {Utils.get_소요시간(self.start_time) }")
        else:
            self.lb_status.setText(f"Status: 실패 - {_json}")

        if len(self.workers) == 0:
            self.dlg_status_verify.close()
        self.workers.remove(worker)
        APP.get_DLG_LOADING().stop_display()

    def on_ws_message(self, url: str, data: dict):
        """ mixin_face에서 호출함 """
        print (f"on_ws_message: {url} {data}")

        dlg_face_result = RecognitionResultDialog(self, result_data=data)
        if dlg_face_result.exec():
            pass
        else:
            pass
        # self.dlg_status_verify.add_status( json.dumps(data, indent=4) )
        # self.dlg_status_verify.add_status( f" 총 verify 소요시간: {Utils.get_소요시간(self.start_time) }")
        

    def collect_burst(self, n=5, timeout=3.0) -> list[np.ndarray]:
        self.probe_images.clear()
        self.last_bbox = None
        self.last_capture_time = 0.0

        t0 = time.time()
        while len(self.probe_images) < n and (time.time() - t0) < timeout:
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.frame = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb)
            if results.detections:
                self.try_collect_probe(frame, results.detections[0])
            # cv2.waitKey(1)  # 너무 빠른 루프 방지
        return self.probe_images

    def collect_burst_async(self, n=5, timeout=3.0):
        self.probe_images.clear()
        self.last_bbox = None
        self.last_capture_time = 0.0

        t0 = time.time()
        def try_capture():
            if len(self.probe_images) >= n or (time.time() - t0) > timeout:
                self.timer_capture.stop()
                return
            if self.frame is not None:
                rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                results = self.face_detector.process(rgb)
                if results.detections:
                    self.try_collect_probe(self.frame, results.detections[0])
        
        self.timer_capture = QTimer()
        self.timer_capture.timeout.connect(try_capture)
        self.timer_capture.start(30)  # 30ms마다 시도

    # -------------------- 종료 --------------------
    def closeEvent(self, e):
        print (f"closeEvent: {self}")
        try:
            if getattr(self, 'timer_capture', None):
                self.timer_capture.stop()
                self.timer_capture = None
            if getattr(self, 'timer', None):
                self.timer.stop()
                self.timer = None

            if hasattr(self, 'cap') and self.cap is not None:
                if self.cap.isOpened():
                    self.cap.release()
                self.cap = None

            # 🔑 장치 캐시 클리어 (특히 리눅스)
            if getattr(self, 'cam_index', None):
                cv2.VideoCapture(self.cam_index).release()

            if getattr(self, 'ws_manager', None) and hasattr(self.ws_manager, 'remove'):
                self.ws_manager.remove(self.ws_url)

        finally:
            super().closeEvent(e)

    def done(self, r):
        """
        exec() → accept()/reject() 로 끝날 때는 closeEvent() 자동 호출이 안 될 수 있음

        따라서 done() 오버라이드하거나, finished 시그널에서 close() 를 강제로 호출하는 게 맞음
        exec() 는 내부적으로 QDialog.accept() / QDialog.reject() 로 종료합니다.

        이 경우 실제 closeEvent() 가 트리거되지 않을 수 있음 (특히 Qt6부터).

        즉, close() 로 닫을 때만 closeEvent() 가 보장 호출돼요
        """
        print("done() called", r)
        self.close()   # 여기서 강제 close() 호출
        super().done(r)