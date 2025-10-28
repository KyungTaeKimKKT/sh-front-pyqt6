import Pyro5.api
import base64
import io
import threading
import time
from PIL import Image

DEFAULT_NAME_SERVER = {
    'IP': "192.168.7.108",
    'PORT': 9990
}

LOOKUP_NAME = "remote.control.server"

class RemoteControlClient:
    def __init__(self):
        pass

    def _get_proxy(self):
        try:
            ns = Pyro5.api.locate_ns()
        except Pyro5.errors.NamingError:
            print("자동 브로드캐스트 실패: ===> 수동 찾기 중")
            ns = Pyro5.api.locate_ns(host=DEFAULT_NAME_SERVER["IP"], port=DEFAULT_NAME_SERVER["PORT"])
        uri = ns.lookup(LOOKUP_NAME)
        print(f"조정자 lookup URI: {uri}")
        proxy = Pyro5.api.Proxy(uri)
        return proxy

    def show_screenshot_loop(self):
        while True:
            try:
                proxy = self._get_proxy()
                img_str = proxy.get_screenshot()
                proxy._pyroRelease()  # Proxy 연결 닫기 (선택적)
                img_data = base64.b64decode(img_str)
                image = Image.open(io.BytesIO(img_data))                
                image.show()  # 이미지 뷰어 열기 (사용자 환경에 따라 다름)
                time.sleep(1)  # 1초마다 갱신
            except Exception as e:
                print(f"오류 발생: {e}")
                break

    def send_key(self, key):
        try:
            proxy = self._get_proxy()
            print(proxy.press_key(key))
            proxy._pyroRelease()
        except Exception as e:
            print(f"send_key 오류: {e}")

    def send_mouse_move(self, x, y):
        try:
            proxy = self._get_proxy()
            print(proxy.move_mouse(x, y))
            proxy._pyroRelease()
        except Exception as e:
            print(f"send_mouse_move 오류: {e}")

    def send_mouse_click(self, button="left"):
        try:
            proxy = self._get_proxy()
            print(proxy.click_mouse(button))
            proxy._pyroRelease()
        except Exception as e:
            print(f"send_mouse_click 오류: {e}")

def main():
    client = RemoteControlClient()

    # 화면 받기 쓰레드 시작 (실제로는 GUI에서 받아서 표시하는 게 좋음)
    t = threading.Thread(target=client.show_screenshot_loop, daemon=True)
    t.start()

    time.sleep(5)  # 5초 후 테스트 입력 전송
    client.send_key("enter")
    client.send_mouse_move(500, 300)
    client.send_mouse_click("left")

    t.join()

if __name__ == "__main__":
    main()