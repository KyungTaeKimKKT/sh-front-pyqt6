from __future__ import annotations
from modules.common_import_v2 import *

import Pyro5.api
from PIL import Image
from PIL.ImageQt import ImageQt  # ✅ 추가
import base64

from modules.mixin.recording_mixin import RecordingMixin

DEFAULT_NAME_SERVER = {
    'IP': "192.168.7.108",
    'PORT': 9990
}
LOOKUP_NAME = "remote.control.server"

class RemoteControlClient:
    def __init__(self, name_server:dict=None, lookup_name:str=None):
        self.name_server = name_server or DEFAULT_NAME_SERVER
        self.lookup_name = lookup_name or LOOKUP_NAME
        try:
            ns = Pyro5.api.locate_ns(
                host=self.name_server["IP"],
                port=self.name_server["PORT"]
            )
            uri = ns.lookup(self.lookup_name)
            print(f"조정자 lookup URI: {uri}")
            self.remote = Pyro5.api.Proxy(uri)    
        except Pyro5.errors.NamingError:
            print("Pyro5.errors.NamingError 실패: !!!")   


    def get_client_info(self) -> dict:
        print(f"get_client_info: {self.remote.get_client_info()}")
        return self.remote.get_client_info()


    def get_screenshot(self) -> bytes:
        img_str = self.remote.get_screenshot()
        return base64.b64decode(img_str)
    
    def send_mouse_move(self, x: int, y: int):
        return self.remote.move_mouse(x, y)

    def send_mouse_click(self, button: str = "left"):
        return self.remote.click_mouse(button)

    def send_key(self, key: str):
        if "+" in key:
            keys = key.split("+")  # 예: "ctrl+s" → ["ctrl", "s"]
            print(f"[복합키 입력] {keys}")
            self.remote.press_combo(keys)
        else:
            print(f"[단일키 입력] {key}")
            self.remote.press_key(key)
    
class RemoteViewerDialog(QDialog, RecordingMixin):
    def __init__(self, parent:QWidget|None = None, client: RemoteControlClient|None = None , name_server:dict|None = DEFAULT_NAME_SERVER, lookup_name:str|None = None, **kwargs):
        super().__init__(parent)
        RecordingMixin.__init__(self)
        self.kwargs = kwargs
        self.setWindowTitle("원격 화면 보기")
        self.client = client or RemoteControlClient(name_server=name_server, lookup_name=lookup_name)

        self.remote_width = None
        self.remote_height = None
        self.pressed_modifiers = set()  # ⬅️ modifier 키 추적용
        # 원격 화면 크기 기억용
        self.current_pixmap_item = None

        self._is_first_update = True

        self.recording_modes = {
            'ffmpeg': '고화질(ffmpeg)',
            'cv2': '저화질(cv2)',

        }

        self.UI()
        self.init_timer()

        # 뷰에 마우스 이벤트 필터 설치
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view.setFocus()
        self.view.installEventFilter(self)

        self._record_seconds = 0
        self._record_timer = QTimer(self)
        self._record_timer.timeout.connect(self._update_record_time)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "current_pixmap_item") and self.current_pixmap_item:
            self.view.fitInView(self.current_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def _update_record_time(self):
        self._record_seconds += 1
        hours = self._record_seconds // 3600
        minutes = (self._record_seconds % 3600) // 60
        seconds = self._record_seconds % 60
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        self.lb_record_time.setText(f"녹화 시간: {time_str}")

    def UI(self):
        self.v_layout = QVBoxLayout()

        self.v_layout.addWidget(self._create_header_widget())

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        ### 최초 생성시 size
        self.view.setMinimumSize(1280, 720)
        self.v_layout.addWidget(self.view)
        self.setLayout(self.v_layout)

        # 👉 다이얼로그 크기 지정
        self.resize(1300, 800)

    def _create_header_widget(self) -> QWidget:
        self.header_widget = QWidget(self)
        self.header_layout = QHBoxLayout()
        #### 1. 녹화 모드 label
        self.header_layout.addWidget(QLabel("녹화모드 선택 : "))
        #### 2. 녹화 모드 콤보박스
        self.cb_recording_method = QComboBox()
        for method_key, display_text in self.recording_modes.items():
            self.cb_recording_method.addItem(display_text, userData=method_key)
        # 기본값 설정
        self.cb_recording_method.setCurrentIndex(0)
        self._record_method = self.cb_recording_method.currentData()
        # 연결  
        self.cb_recording_method.currentIndexChanged.connect(self.on_recording_method_changed)
        self.header_layout.addWidget(self.cb_recording_method)
        
        #### 3. 녹화 시간 label
        self.lb_record_time = QLabel("녹화 시간: 00:00:00")
        self.lb_record_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb_record_time.setStyleSheet("color: #007bff;")
        self.lb_record_time.setFont(QFont("Arial", 12))
        self.header_layout.addWidget(self.lb_record_time)
        #### 4. 녹화 시작 버튼
        self.header_layout.addStretch()

        self.pb_recording = QPushButton("녹화 시작")
        self.pb_recording.clicked.connect(self.on_pb_recording_clicked)
        #### 5. 녹화 중지 버튼
        self.pb_save_to_server = QPushButton("서버에 저장")
        self.pb_save_to_server.setEnabled(False)
        self.pb_save_to_server.clicked.connect(self.on_pb_save_to_server_clicked)
 
        self.header_layout.addWidget(self.pb_recording)
        self.header_layout.addWidget(self.pb_save_to_server)
        self.header_widget.setLayout(self.header_layout)

        return self.header_widget

    def on_recording_method_changed(self, index: int):
        method = self.cb_recording_method.itemData(index)
        if method:
            self._record_method = method
        else:
            print(f"[녹화 모드 파싱 실패] index: {index}")
            self._record_method = "cv2"

    def _disable_in_recording(self):
        self.cb_recording_method.setEnabled(False)
        self.pb_save_to_server.setEnabled(False)
        self.pb_recording.setText("녹화 중지")

    def _enable_for_recording(self):
        self.cb_recording_method.setEnabled(True)
        self.pb_save_to_server.setEnabled(True)
        self.pb_recording.setText("녹화 시작")
    
    def on_pb_recording_clicked(self):
        _text = self.sender().text()
        if _text == "녹화 시작":
            self._record_method = self.cb_recording_method.currentData()
            self._disable_in_recording()
            try:
                self.start_recording()

                self._record_seconds = 0
                self.lb_record_time.setText("녹화 시간: 00:00:00")
                self._record_timer.start(1000)

            except Exception as e:
                print(f"[녹화 모드 변경 오류: 녹화 시작] {e}")
                self._enable_for_recording()

        elif _text == "녹화 중지":
            self._enable_for_recording()
            try:
                self.stop_recording()
                self._record_timer.stop()
                self._record_seconds = 0
            except Exception as e:
                print(f"[녹화 모드 변경 오류: 녹화 중지] {e}")      


    def on_pb_save_to_server_clicked(self):
        Utils.generate_QMsg_Information(self, "녹화 저장", "서버에 저장")
        print("서버에 저장")
        print(" client_info: ", self.client.get_client_info() )  
        print(" record_path: ", self.get_record_path() )
        print(" record_method: ", self._record_method )
        print ("record_size: ", self._record_size )
        print ("record_fps: ", self._record_fps )



    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(self.kwargs.get('update_interval', 250))  # 250ms 주기

    def update_image(self):
        try:
            img_data = self.client.get_screenshot()
            pil_image = Image.open(io.BytesIO(img_data)).convert("RGB")

            if not self.remote_width or not self.remote_height:
                self.remote_width = pil_image.width
                self.remote_height = pil_image.height
            # 🔍 디버그 저장
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # pil_image.save(f"./debug/screenshot_{timestamp}.png")
            # print(f"이미지 저장: screenshot_{timestamp}.png")

            # ✅ 안전한 변환 방식
            image_qt = ImageQt(pil_image)  # ImageQt는 QImage 서브클래스
            pixmap = QPixmap.fromImage(image_qt)  # 직접 전달
            copyed_pixmap = pixmap.copy()

            ### 녹화추가
            # self.write_frame_by_pixmap(pixmap.copy())
            if self._recording:
                self.write_frame_by_pil_image(pil_image.copy())
            # pixmap 생성 후 저장 (디버깅용)
            # pixmap_path = f"./debug/pixmap_{timestamp}.png"
            # pixmap.save(pixmap_path, "PNG")
            # print(f"픽스맵 저장: {pixmap_path}")
            # reloaded_pixmap = QPixmap(pixmap_path)

            self.scene.clear()
            self.current_pixmap_item = self.scene.addPixmap(copyed_pixmap)
            self.view.setSceneRect(QRectF(copyed_pixmap.rect()))  # ✅ QRect → QRectF 변환

            if self._is_first_update:
                self._is_first_update = False
                # self.resize(copyed_pixmap.width() + 50, copyed_pixmap.height() + 50)
                self.view.fitInView(self.current_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

            # # ✅ 비율 유지하여 스케일링
            # scaled_pixmap = pixmap.scaled(
            #     self.image_label.width(),
            #     self.image_label.height(),
            #     Qt.AspectRatioMode.KeepAspectRatio,
            #     Qt.TransformationMode.SmoothTransformation
            # )
            # self.image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"[화면 업데이트 오류] {e}")
            self.timer.stop()

    def eventFilter(self, obj, event: QEvent):
        if obj is self.view:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    pos = event.position()
                    scene_pos = self.view.mapToScene(pos.toPoint())
                    x = scene_pos.x()
                    y = scene_pos.y()
                    if self.remote_width and self.remote_height:
                        remote_x = int(x * self.remote_width / self.current_pixmap_item.pixmap().width())
                        remote_y = int(y * self.remote_height / self.current_pixmap_item.pixmap().height())
                        print(f"[클릭] 원격 좌표: {remote_x}, {remote_y}")
                        try:
                            self.client.send_mouse_move(remote_x, remote_y)
                            self.client.send_mouse_click("left")
                        except Exception as e:
                            print(f"[클릭 오류] {e}")
                    return True

            elif event.type() == QEvent.Type.KeyPress:
                key_event: QKeyEvent = event
                key = self.qt_key_to_string(key_event)
                if key:
                    print(f"[키입력] {key}")
                    try:
                        self.client.send_key(key)
                    except Exception as e:
                        print(f"[키입력 오류] {e}")
                    return True

        return super().eventFilter(obj, event)

    def qt_key_to_string(self, event: QKeyEvent) -> str | None:
        """Qt 키 이벤트를 pyautogui에서 사용할 수 있는 문자열로 변환 (조합 키 포함)"""
        modifiers = []
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("win")  # macOS는 "command"로 바꿔도 됨

        key = event.key()

        key_map = {
            Qt.Key.Key_Enter: 'enter',
            Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Backspace: 'backspace',
            Qt.Key.Key_Tab: 'tab',
            Qt.Key.Key_Escape: 'esc',
            Qt.Key.Key_Space: 'space',
            Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Right: 'right',
            Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Down: 'down',
            Qt.Key.Key_Home: 'home',
            Qt.Key.Key_End: 'end',
            Qt.Key.Key_PageUp: 'pageup',
            Qt.Key.Key_PageDown: 'pagedown',
            Qt.Key.Key_Insert: 'insert',
            Qt.Key.Key_F1: 'f1',
            Qt.Key.Key_F2: 'f2',
            Qt.Key.Key_F3: 'f3',
            Qt.Key.Key_F4: 'f4',
            Qt.Key.Key_F5: 'f5',
            Qt.Key.Key_F6: 'f6',
            Qt.Key.Key_F7: 'f7',
            Qt.Key.Key_F8: 'f8',
            Qt.Key.Key_F9: 'f9',
            Qt.Key.Key_F10: 'f10',
            Qt.Key.Key_F11: 'f11',
            Qt.Key.Key_F12: 'f12',
            Qt.Key.Key_CapsLock: 'capslock',
            Qt.Key.Key_NumLock: 'numlock',
            Qt.Key.Key_ScrollLock: 'scrolllock',
            Qt.Key.Key_Print: 'printscreen',
        }

        key_str = key_map.get(key, None)

        # 🔥 핵심 추가: 일반 ASCII 문자 직접 변환
        if not key_str and 32 <= key <= 126:
            key_str = chr(key).lower()

        if not key_str:
            # fallback for special characters
            text = event.text()
            if text and text.isprintable():
                key_str = text.lower()
            else:
                return None
        print(f"key: {key} : key_str: {key_map.get(key, None)}  {[key_str]}; modifiers: {modifiers}")

        full_key = '+'.join(modifiers + [key_str]) if modifiers else key_str
        return full_key