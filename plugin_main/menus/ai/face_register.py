from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v3 import *
import cv2
import numpy as np

import mediapipe as mp
from plugin_main.widgets.dlg_user_select_by_grid import Dlg_User_Select_By_Grid

# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

class Mixin_ImageLabel:
    def set_image(self, image:np.ndarray):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], rgb_image.shape[2]*rgb_image.shape[1], QImage.Format.Format_RGB888)
        qimg = qimg.scaled(self.width(), self.height())
        self.setPixmap(QPixmap.fromImage(qimg))

    def clear_image(self):
        self.setPixmap(QPixmap())


class MainImageLabel(QLabel, Mixin_ImageLabel):
    def __init__(self, parent=None, text:str="camera feed", size:tuple[int, int]=(600, 480), image:np.ndarray=None):
        super().__init__(parent)
        self.setFixedSize(size[0], size[1])
        if image is  None:
            self.setText(text)
        else:
            self.set_image(image)




class SubImageLabel(QLabel, Mixin_ImageLabel):
    def __init__(self, parent=None, text:str="sub image", size:tuple[int, int]=(160, 160), image:np.ndarray=None):
        super().__init__(parent)
        self.setFixedSize(size[0], size[1])
        self.image = image
        if image is  None:
            self.setText(text)
        else:
            self.set_image(image)

class SubContainer(QWidget):
    def __init__(self, parent=None, item_size:int=160):
        super().__init__(parent)
        self.size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(self.size_policy)
        self.setMinimumWidth( item_size *8 + 10)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = Custom_Grid(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # 컨텍스트 메뉴 허용
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)



    def show_context_menu(self, pos):
        global_pos = self.mapToGlobal(pos)
        menu = QMenu()
        delete_action = menu.addAction("삭제")
        action = menu.exec(global_pos)
        if action == delete_action:
            self.delete_image_at(pos)

    def delete_image_at(self, pos):
        """
        pos: 컨텍스트 메뉴가 열린 위치 (SubContainer 좌표)
        해당 위치의 위젯을 찾아 삭제
        """
        widget = self.childAt(pos)
        if widget and widget != self.main_layout and isinstance(widget, SubImageLabel):  # layout 자체는 삭제하지 않음
            self.main_layout.remove_widget(widget)

    def add_image(self, image:np.ndarray):
        self.main_layout.add_widget(SubImageLabel(image=image))

    def get_images(self) -> list[np.ndarray]:
        images = []
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, SubImageLabel):
                images.append(widget.image)
        return images



class Mixin_MediaPipe:

    def get_det_bbox(self, frame: np.ndarray, det:mp.solutions.face_detection.FaceDetectionResult) -> tuple[int, int, int, int]:
        """ x1, y1, x2, y2 리턴 """
        bbox = det.location_data.relative_bounding_box
        h, w, _ = frame.shape
        x1 = max(0, int(bbox.xmin * w))
        y1 = max(0, int(bbox.ymin * h))
        x2 = min(w, int((bbox.xmin + bbox.width) * w))
        y2 = min(h, int((bbox.ymin + bbox.height) * h))
        return x1, y1, x2, y2

    def get_add_padding_bbox(self, frame:np.ndarray, bbox:tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """
        bbox에 패딩을 추가하여 리턴
        """
        h, w, _ = frame.shape
        x1, y1, x2, y2 = bbox
        pad_top = int(0.4 * (y2 - y1)) # 머리 위쪽 추가
        pad_side = int(0.2 * (x2 - x1)) # 좌우 여유
        pad_bottom = int(0.1 * (y2 - y1)) # 턱 아래 여유

        x1p = max(0, x1 - pad_side)
        y1p = max(0, y1 - pad_top)
        x2p = min(w, x2 + pad_side)
        y2p = min(h, y2 + pad_bottom)
        return x1p, y1p, x2p, y2p

    def render_frame_by_mediapipe(self, 
                                frame:np.ndarray, 
                                display_frame:np.ndarray, 
                                results:mp.solutions.face_detection.FaceDetectionResult
                                ) -> tuple[np.ndarray, np.ndarray]:
        """
        Mediapipe 얼굴 검출 결과를 화면에 표시 , 얼굴 영역 crop 리턴
        """
        h, w, _ = frame.shape
        for det in results.detections:
            # 1. 기본 bbox
            x1, y1, x2, y2 = self.get_det_bbox(frame, det)
            # 2. 패딩 추가 (머리 포함)
            x1p, y1p, x2p, y2p = self.get_add_padding_bbox(frame, (x1, y1, x2, y2))

            #  개발자용 화면 표시용 Circle: 얼굴 영역 표시
            if  INFO.IS_DEV:
                cx, cy = (x1 + x2)//2, (y1 + y2)//2
                radius = max(x2 - x1, y2 - y1)//2
                cv2.circle(display_frame, (cx, cy), radius, (255,0,0), 2)

            # Circle 표시
            cx, cy = (x1p + x2p) // 2, (y1p + y2p) // 2
            radius = max(x2p - x1p, y2p - y1p) // 2
            cv2.circle(display_frame, (cx, cy), radius, (0, 255, 0), 2)
            cropped_face = frame.copy()[y1p:y2p, x1p:x2p]
        return display_frame, cropped_face


    def ndarray_to_file(self, img:np.ndarray, filename: str = "face.jpg", ext: str = ".jpg"):
        """img가 ndarray가 아니면 변환 후 file-like object 리턴"""
        if not isinstance(img, np.ndarray):
            raise TypeError(f"Expected numpy.ndarray but got {type(img)}")

        success, buffer = cv2.imencode(ext, img)
        if not success:
            raise ValueError("cv2.imencode failed")

        file_bytes = io.BytesIO(buffer.tobytes())
        mimetype = "image/jpeg" if ext == ".jpg" else "image/png"
        return (filename, file_bytes, mimetype)


from modules.PyQt.compoent_v2.grid.container_lb_pixmap import Custom_Grid
from plugin_main.menus.ai.mixin_face import Mixin_Face
class FaceRegisterDialog(QDialog, Mixin_MediaPipe, Mixin_Face):
    def __init__(self, parent=None, url:str=None, **kwargs):
        super().__init__(parent)
        self.url = url or "ai-face/user-face/"
        self.frame:np.ndarray = None ### 현재 label에 표시되는 프레임
        self.is_auto_detect_face = False
        self.is_capture_face = False
        self.is_분석용_face = False
        self.captured_face:np.ndarray = None
        self.last_analysis_time = time.time()
        self.min_interval_analysis_face = 0.1

        self.대표얼굴_image = None
        self.분석용_images = []

        self.selected_user_dict = {}

        # Mediapipe Face Detection
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)


        self.text_toggle_auto_capture_face = {
            True : "중지 : 자동 얼굴 인식",
            False : "시작 : 자동 얼굴 인식",
        }
        self.text_toggle_capture_face = {
            True : "Live ",
            False : " Capture",
        }
        self.text_toggle_analyze_face = {
            True : "분석용 얼굴 중지",
            False : "분석용 얼굴 시작",
        }

        self.setWindowTitle("Face Register")
        self.setMinimumSize(1200, 1200)

        self.setup_ui()
        self.connect_signals()

        self.mixin_init_camera()
        self.mixin_init_ws( ws_manager = kwargs.get('ws_manager', None),
                      ws_url_base = kwargs.get('ws_url_base', "broadcast/") 
                      )



    def setup_ui(self):
        # 메인 레이아웃
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)  # 위젯 간 간격
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)  # 수평 중앙 정렬, 위에서부터 배치
        ### 0. 사용자 선택
        self.container_user_select = QWidget(self)
        self.container_user_select_layout = QHBoxLayout(self.container_user_select)
        self.container_user_select_layout.setContentsMargins(0, 0, 0, 0)
        self.container_user_select_layout.setSpacing(5)
        self.lb_current_user = QLabel("사용자: None")
        self.container_user_select_layout.addWidget(self.lb_current_user)
        self.container_user_select_layout.addStretch()
        self.btn_user_select = QPushButton("사용자 선택")
        self.container_user_select_layout.addWidget(self.btn_user_select)
        self.main_layout.addWidget(self.container_user_select, alignment=Qt.AlignmentFlag.AlignHCenter)

        ### 1. Camera image label
        self.lb_camera_image = MainImageLabel(self, text="Camera Feed", size=(640, 480))
        self.lb_camera_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb_camera_image.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.main_layout.addWidget(self.lb_camera_image, alignment=Qt.AlignmentFlag.AlignHCenter)

        ### 2. Sub image container : grid로 구현
        self.sub_container = SubContainer(self)
        self.sub_container_layout = self.sub_container.main_layout
        self.main_layout.addWidget(self.sub_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        ### 3. Control container
        self.control_container = QWidget(self)
        self.control_container_layout = QHBoxLayout(self.control_container)
        self.control_container_layout.setContentsMargins(0, 0, 0, 0)
        self.control_container_layout.setSpacing(5)
        self.control_container_layout.addStretch()
        self.btn_auto_capture_face = QPushButton(self.text_toggle_auto_capture_face[self.is_auto_detect_face])
        self.control_container_layout.addWidget(self.btn_auto_capture_face)
        self.btn_capture = QPushButton(self.text_toggle_capture_face[self.is_capture_face])
        self.control_container_layout.addWidget(self.btn_capture)
        self.btn_분석용 = QPushButton(self.text_toggle_analyze_face[self.is_분석용_face])
        self.btn_분석용.setEnabled(False)
        self.control_container_layout.addWidget(self.btn_분석용)
        self.control_container_layout.addStretch()
        self.btn_save = QPushButton("Save Face")
        self.btn_save.setEnabled(False)
        self.control_container_layout.addWidget(self.btn_save)
        self.main_layout.addWidget(self.control_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        ### 4. Status label
        self.lb_status = QLabel("Status: None")
        self.lb_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.lb_status, alignment=Qt.AlignmentFlag.AlignHCenter)   


    def connect_signals(self):
        # 버튼 이벤트
        self.btn_user_select.clicked.connect(self.select_user)
        self.btn_auto_capture_face.clicked.connect(self.toggle_auto_detect_face)
        self.btn_capture.clicked.connect(self.toggle_capture_face)
        self.btn_분석용.clicked.connect(self.toggle_analyze_face)

        self.btn_save.clicked.connect(self.save_face)


    def disconnect_signals(self):
        try:
            self.btn_auto_capture_face.clicked.disconnect(self.toggle_auto_detect_face)
            self.btn_capture.clicked.disconnect(self.toggle_capture_face)
            self.btn_분석용.clicked.disconnect(self.toggle_analyze_face)
            self.btn_save.clicked.disconnect(self.save_face)
        except Exception as e:
            pass

    def toggle_auto_detect_face(self):
        self.is_auto_detect_face = not self.is_auto_detect_face
        self.btn_auto_capture_face.setText(self.text_toggle_auto_capture_face[self.is_auto_detect_face])
        self.lb_status.setText(f"Status: {self.text_toggle_auto_capture_face[self.is_auto_detect_face]}")

    def toggle_capture_face(self):
        self.is_capture_face = not self.is_capture_face
        self.btn_capture.setText(self.text_toggle_capture_face[self.is_capture_face])
        self.lb_status.setText(f"Status: {self.text_toggle_capture_face[self.is_capture_face]}")

        # if self.is_capture_face == False:
        #     self.대표얼굴_image = None
        #     self.captured_face = None
        #     self.분석용_images = []
        #     self.sub_container.main_layout.clear_layout()
        #     self.btn_분석용.click()
            
        ### 다음 단계 btn 활성화
        self.btn_분석용.setEnabled(self.is_capture_face)
        self.btn_save.setEnabled(self.is_capture_face)


    def toggle_analyze_face(self):
        self.is_분석용_face = not self.is_분석용_face
        self.btn_분석용.setText(self.text_toggle_analyze_face[self.is_분석용_face])
        self.lb_status.setText(f"Status: {self.text_toggle_analyze_face[self.is_분석용_face]}")

        if not self.is_분석용_face:
            self.분석용_images = []

    def select_user(self):
        url = f"{self.url}/list_user_to_face/".replace("//", "/")
        params = {'page_size':0, 'is_active':True, 'user_id':'all'}
        _isok, _json = APP.API.getlist(url, params=params )
        if _isok:
            dlg = Dlg_User_Select_By_Grid(self, data= _json )
            if dlg.exec():
                selected_data = dlg.get_selected_data()
                self.selected_user_dict = selected_data
                self.selected_user_id = selected_data['id']
                self.selected_user_name = selected_data['user_성명']
                self.lb_current_user.setText(f"사용자: {self.selected_user_id} -- {self.selected_user_name}")
        else:
            Utils.QMsg_Critical(self, title="사용자 선택 실패", text=f"{_json}" )



    def add_analysis_face(self, face_crop: np.ndarray, bbox, 
                        min_interval: float = 0.5, min_movement: int = 15) -> bool:
        """
        분석용 이미지 추가 (중복 방지)
        - min_interval: 초 단위 최소 간격
        - min_movement: bbox 중심 이동 최소 픽셀
        """
        now = time.time()

        # 1. 시간 간격 체크
        if hasattr(self, "last_capture_time"):
            if now - self.last_capture_time < min_interval:
                return
        self.last_capture_time = now

        # 2. 움직임 체크
        if hasattr(self, "last_bbox"):
            (x1, y1, x2, y2) = bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            (lx1, ly1, lx2, ly2) = self.last_bbox
            lcx, lcy = (lx1 + lx2) // 2, (ly1 + ly2) // 2
            dist = np.sqrt((cx - lcx) ** 2 + (cy - lcy) ** 2)
            if dist < min_movement:
                return False
        self.last_bbox = bbox

        # # 3. 최종 추가
        # self.분석용_images.append(face_crop)
        return True


    def check_valid_face(self, frame:np.ndarray) -> tuple[bool, mp.solutions.face_detection.FaceDetectionResult]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)
        return bool(results.detections), results


    def update_frame(self):
        ### 1. 카메라 프레임 읽기
        ret, frame = self.cap.read()
        if not ret:
            return
        self.frame = frame.copy()
        display_frame = frame.copy()

        #### 2. 자동 검출 모드 처리
        if not self.is_auto_detect_face:
            self.lb_camera_image.set_image(image = display_frame)
            return
        else:
            is_valid, results = self.check_valid_face(frame)
            if is_valid:
                ### register 용
                if self.is_capture_face and self.대표얼굴_image is None:
                    self.대표얼굴_image = display_frame.copy()
                    self.sub_container_layout.add_widget(SubImageLabel(image=self.대표얼굴_image.copy()))
                marked_frame, cropped_face = self.render_frame_by_mediapipe(frame, display_frame, results)
                self.lb_camera_image.set_image(image = marked_frame)
            else:
                self.lb_camera_image.set_image(image = display_frame)
                return 
        
        #### 3. 분석용 검출 처리        
        if self.is_capture_face and self.is_분석용_face:
            for det in results.detections:
                #  기본 bbox 만, 
                x1, y1, x2, y2 = self.get_det_bbox(frame, det)
                face_crop = cv2.resize(frame[y1:y2, x1:x2], (160,160))
                if self.add_analysis_face(face_crop, (x1, y1, x2, y2)):
                    self.sub_container_layout.add_widget(SubImageLabel(image=face_crop))

    def on_ws_message(self, url: str, data: dict):
        """ mixin_face에서 호출함 """
        print (f"on_ws_message: {url} {data}")
        self.lb_status.setText(f"Status: {data}")

    def on_ws_error(self, url: str, err: str):
        print (f"on_ws_error: {url} {err}")

    def save_face(self):
        """ register는 늘 post로 함. 단순한 update 가 불가능하고, 첨부된 image로 
            poc에서 embed 계산 처리해야함 ==> 따라서 기존 등록 data는 다 drf에서 삭제함.
        """
        if Utils.QMsg_question(self, title="얼굴 저장", text="얼굴을 저장하시겠습니까?"):
            url = self.url + "register_via_rpc/"      
            files = []
            if self.대표얼굴_image is not None:
                files.append(("representative_image", self.ndarray_to_file(self.대표얼굴_image)))
                
            # 분석용 얼굴 (여러 장 가능)
            for idx, img in enumerate(self.sub_container.get_images()):
                if idx == 0:
                    continue
                files.append(("extra_images", self.ndarray_to_file(img)))
            
            is_ok, _json = APP.API.Send(url, 
                            dataObj={'id':-1}, 
                            sendData={'user_id':self.selected_user_dict.get('id', INFO.USERID)}, 
                            sendFiles=files
                            )
            if is_ok:                
                Utils.QMsg_Info(self, title="얼굴 저장", text=f"{_json}" )
            else:
                Utils.QMsg_Critical(self, title="얼굴 저장 실패", text=f"{_json}" )
            # self.close()
        

    def closeEvent(self, e):
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                if self.cap.isOpened():
                    self.cap.release()
                self.cap = None

            cv2.destroyAllWindows()  # OpenCV 창 해제

            if hasattr(self, 'ws_manager') and hasattr(self.ws_manager, 'remove'):
                self.ws_manager.remove(self.ws_url)

        finally:
            super().closeEvent(e)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dialog = FaceRegisterDialog()
    dialog.show()
    sys.exit(app.exec())