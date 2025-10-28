# remote_server.py (혹은 다른 이름)
import Pyro5.api
import io, base64
import pyautogui
from PIL import Image
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

import modules.user.utils as Utils
from info import Info_SW as INFO

DEFAULT_NAME_SERVER = {
    'IP': "192.168.7.108",
    'PORT': 9990
}
DEFAULT_LOOKUP_NAME = "remote.control.server"

class RemoteStatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 60)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel("🖥️ 원격 제어 연결 중")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #007bff;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(label)

    def show_near_bottom_right(self, parent: QWidget):
        if parent is not None:
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            self.move(pos.x() - self.width() - 20, pos.y() - self.height() - 40)
        self.show()


@Pyro5.api.expose
class RemoteControl:
    def get_screenshot(self):
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def press_key(self, key: str):
        pyautogui.press(key)
        return f"Key {key} pressed"

    def press_combo(self, keys: list[str]):
        try:
            pyautogui.hotkey(*keys)
            return f"Hotkey {'+'.join(keys)} pressed"
        except Exception as e:
            return f"Hotkey press failed: {e}"

    def move_mouse(self, x: int, y: int):
        pyautogui.moveTo(x, y)
        return f"Mouse moved to {x}, {y}"

    def click_mouse(self, button="left"):
        pyautogui.click(button=button)
        return f"Mouse {button} clicked"

    def get_client_info(self) -> dict:
        return {
            'ip': Utils.get_local_ip(),
            'user': INFO.USERID
        }

# def start_server():
#     host_ip = Utils.get_local_ip()
#     daemon = Pyro5.api.Daemon(host=host_ip)

#     try:
#         ns = Pyro5.api.locate_ns()
#     except Pyro5.errors.NamingError:
#         ns = Pyro5.api.locate_ns(
#             host=DEFAULT_NAME_SERVER["IP"], port=DEFAULT_NAME_SERVER["PORT"])

#     uri = daemon.register(RemoteControl)
#     from Pyro5.core import URI
#     uri_obj = URI(uri)
#     uri_obj.host = host_ip
#     fixed_uri = uri_obj
#     ns.register(DEFAULT_LOOKUP_NAME, fixed_uri)

#     print(f"[Remote Server Started] {fixed_uri}")
#     daemon.requestLoop()

from PyQt6.QtCore import QThread
class RemoteServer_Request_Thread(QThread):
    def __init__(self, parent=None, lookup_name:str|None = DEFAULT_LOOKUP_NAME):
        super().__init__(parent)
        self._running = True  # 루프 종료 플래그
        self.lookup_name = lookup_name

    def run(self):
        try:
            self._start_server()
        except Exception as e:
            print(f"[원격 서버 오류] {e}")

    def stop(self):
        self._running = False

    def _start_server(self):
        import Pyro5.api
        host_ip = Utils.get_local_ip()
        daemon = Pyro5.api.Daemon(host=host_ip)

        try:
            ns = Pyro5.api.locate_ns(
                host=DEFAULT_NAME_SERVER["IP"], port=DEFAULT_NAME_SERVER["PORT"])
        except Pyro5.errors.NamingError:
            print("Pyro5.errors.NamingError 실패: !!!")
            ns = None

        if ns is None:
            return 

        uri = daemon.register(RemoteControl)
        from Pyro5.core import URI
        uri_obj = URI(uri)
        uri_obj.host = host_ip
        ns.register(self.lookup_name, uri_obj)

        print(f"[Remote Server Started] {uri_obj}")

        # while self._running:
        #     daemon.handleRequests(timeout=1.0)  # 🔁 안전한 루프
        # 🔁 이 부분이 핵심
        daemon.requestLoop(loopCondition=lambda: self._running)