from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v2 import *

import cv2

import numpy as np
import torch

from modules.ai.hi_rtsp.AlarmPanelAnalyzer import AlarmPanelAnalyzer
from modules.ai.hi_rtsp.cnn_anaylizer import CNN_Analyzer
from modules.PyQt.compoent_v2.json_editor import Dialog_JsonEditor


class EditableLabel(QLabel):
    roi_changed = pyqtSignal(object)  # 꼭짓점 리스트 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    roi_named = pyqtSignal(str, list) # 이름 + 점 리스트

    def __init__(self, parent=None):
        super().__init__(parent)
        self.roi_setting_started = False
        self.roi_points = []  # 지금 그리고 있는 ROI
        self.roi_list = []    # main 에서 전달받는 ROI 전체
        self.roi_dict:dict[str, list[tuple[int, int]]] = {}

    def set_rois(self, roi_list: list[list[tuple[int, int]]]):
        """외부(main)에서 ROI 리스트를 주입받음"""
        self.roi_list = roi_list
        self.update()

    def set_rois_by_dict(self, roi_dict: dict[str, list[tuple[int, int]]]):
        """외부(main)에서 ROI 리스트를 주입받음"""
        self.roi_dict = roi_dict
        self.update()

    def start_roi(self, start: bool):
        """ROI 모드 on/off"""
        self.roi_setting_started = start
        if not start:
            self.roi_points = []   # 중간에 stop → 초기화
        self.update()
        

    def mousePressEvent(self, event):
        if self.roi_setting_started and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self.roi_points.append((pos.x(), pos.y()))
            self.update()

            # 점이 4개 찍히면 자동 종료
            if len(self.roi_points) == 4:
                self.roi_setting_started = False
                # self.roi_changed.emit(self.roi_points)

                # === ROI 이름 입력 다이얼로그 ===
                name, ok = QInputDialog.getText(self, "ROI 이름 입력", "ROI 이름(Unique한 이름)을 입력하세요:")
                if ok and name:
                    print (f"ROI 이름 입력: {name}, {self.roi_points}")
                    self.roi_named.emit(name, self.roi_points.copy())


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # === 1. 지금 입력 중인 ROI 그리기 ===
        if self.roi_points:
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)

            for (x, y) in self.roi_points:
                painter.drawEllipse(QPoint(x, y), 4, 4)

            if len(self.roi_points) > 1:
                for i in range(len(self.roi_points) - 1):
                    painter.drawLine(
                        QPoint(*self.roi_points[i]), QPoint(*self.roi_points[i + 1])
                    )
            if len(self.roi_points) == 4:
                painter.drawLine(QPoint(*self.roi_points[3]), QPoint(*self.roi_points[0]))

        # === 2. 기존 ROI dict 전체 그리기 : 우선순위 높음. ===
        if self.roi_dict:
            pen = QPen(QColor(0, 255, 0), 2)  # 초록색으로 표시
            painter.setPen(pen)
            for name, roi in self.roi_dict.items():
                # 꼭짓점 원
                for (x, y) in roi:
                    painter.drawEllipse(QPoint(x, y), 3, 3)
                # 사각형 연결
                for i in range(4):
                    painter.drawLine(QPoint(*roi[i]), QPoint(*roi[(i + 1) % 4]))
                # 이름 표시 (좌상단 꼭짓점 기준)
                x_min = min([p[0] for p in roi])
                y_min = min([p[1] for p in roi])
                painter.drawText(QPoint(x_min + 2, y_min - 2), f"ROI: {name}")
            

        # === 3. 기존 ROI 리스트 전체 그리기 ===
        elif self.roi_list:
            pen = QPen(QColor(0, 255, 0), 2)  # 초록색으로 표시
            painter.setPen(pen)
            for roi in self.roi_list:
                # 꼭짓점 원
                for (x, y) in roi:
                    painter.drawEllipse(QPoint(x, y), 3, 3)
                # 사각형 연결
                for i in range(4):
                    painter.drawLine(QPoint(*roi[i]), QPoint(*roi[(i + 1) % 4]))

        painter.end()

class Dlg_ImageViewer(QDialog):
    def __init__(self, parent=None, pixmap:QPixmap=None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.pixmap = pixmap

        self.setup_ui()

        
    def setup_ui(self):
        self.h_layout = QVBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(0)
        
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        self.h_layout.addWidget(self.image_label)        
        
        self.setLayout(self.h_layout)
        
    def set_pixmap(self, pixmap:QPixmap):
        self.pixmap = pixmap
        self.image_label.setPixmap(pixmap)
        self.update()


from modules.PyQt.compoent_v2.dlg_dict_selectable_table import DictTableSelectorDialog	

class Dialog_DB_Load(DictTableSelectorDialog):
	def __init__(self, parent=None, datas: list[dict]=[], attrNames: list[str]=[], **kwargs):
		super().__init__(parent, datas, attrNames, **kwargs)

        

class Image_ROI_Editor(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.api_url = kwargs.get("api_url", "rtsp_cam/camera_settings/")
        default_data = {
            "name" : "건조로 camera",
            "url" : "rtsp://192.168.14.100",
            "port" : 10500,
            "rois" : {
                "default_name" :  [(10,20), (30,40), (50,60), (70,80)]
            },
            "settings" : {
                "7-segment" : "white",
                "bg" : "black",
                "desired_fps" : 1,

            },
            "is_active" : True,
        }
        self.api_data = kwargs.get("api_data", default_data)

        # --- 상태 변수 ---
        self.is_loaded = False
        self.image = None
        self.cap = None
        self.paused = False
        self.drawing = False

        self.roi_rect:list[tuple[int, int]] = None
        self.roi_list :list[list[tuple[int, int]]] = [] ### roi_rect 의 list

        self.roi_setting_started = False
        self.analyze_started = False

        self.edited_image:None|np.ndarray = None
        self.image :None|np.ndarray = None

        self.k1 = kwargs.get("k1", -0.1)   # 초기값 (barrel correction)
        self.k_step = kwargs.get("k_step", 1e-3)  # +, - 버튼 클릭 시 변화량

        ### map_analyze_type_to_analyzer
        self.map_analyze_type_to_analyzer = {
            "7-segment" : CNN_Analyzer(),
            "Alarm Panel" : AlarmPanelAnalyzer(),
            "분석안함" : None,
        }
        self.analyzer: None|AlarmPanelAnalyzer|CNN_Analyzer = None

        ### dlg 선언 : btn 누르면 생성함.
        self.dlg_original = None
        self.dlg_roi = None

        self.cnn_analyzer = CNN_Analyzer()

        self.prev_분석time = None

        title = kwargs.get("title", "ROI Editor (Local / RTSP)")
        self.setWindowTitle(title)
        self.setup_ui()
        self.connect_signals()

        self.error_count = 0
        self.last_saved_time = None

        if self.api_data:
            self.update_from_api_data()

    def setup_ui(self):
        self.h_layout = QVBoxLayout()
        self.h_layout.setContentsMargins(10, 0, 10, 0)
        self.h_layout.setSpacing(0)

        # --- 1. top widget ---
        self.top_widget = QWidget()
        self.top_layout = QHBoxLayout()
        self.top_widget.setLayout(self.top_layout)
        self.top_layout.setContentsMargins(10, 0, 10, 0)
        self.top_widget.setFixedHeight(30)
        self.h_layout.addWidget(self.top_widget)

        self.btn_drf_load = QPushButton("DB 설정 Load")
    
        
        self.cb_source_type = QComboBox()
        self.cb_source_type.addItems(["Local Image", "RTSP URL"])
        self.cb_analyze_type = QComboBox()
        self.cb_analyze_type.addItems(list(self.map_analyze_type_to_analyzer.keys()))
        self.input_path = QLineEdit()
        
        self.btn_load = QPushButton("Load Image/Start Stream")
        self.btn_analyze = QPushButton("분석시작")

        self.top_layout.addWidget(self.btn_drf_load)
        self.top_layout.addWidget(self.cb_source_type)
        self.top_layout.addWidget(self.input_path)
        self.top_layout.addWidget(self.cb_analyze_type)
        self.top_layout.addWidget(self.btn_load)
        self.top_layout.addWidget(self.btn_analyze)
        

        # --- 2. control widget ---
        self.control_widget = QWidget()
        self.control_layout = QHBoxLayout()
        self.control_widget.setLayout(self.control_layout)
        self.control_layout.setContentsMargins(10, 0, 10, 0)
        self.control_widget.setFixedHeight(30)
        self.h_layout.addWidget(self.control_widget)

        self.btn_original_view = QPushButton("Original View")

        self.roi_label = QLabel("ROI: None")

        self.btn_start_roi = QPushButton("Start ROI")
        self.btn_api_data_edit = QPushButton("API Data Edit")
        self.btn_save_api_data = QPushButton("Save API Data")

        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.angle_input = QSpinBox()
        self.angle_input.setRange(-180, 180)
        self.angle_input.setValue(0)
        self.angle_input.setFixedWidth(50)

        self.correct_plus = QPushButton("+")
        self.correct_minus = QPushButton("-")


        self.control_layout.addWidget(self.btn_original_view)
        self.control_layout.addWidget(self.roi_label)
        self.control_layout.addWidget(self.btn_start_roi)
        self.control_layout.addWidget(self.btn_api_data_edit)
        self.control_layout.addWidget(self.btn_save_api_data)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.btn_pause)
        self.control_layout.addWidget(self.btn_resume)
        self.control_layout.addWidget(QLabel("Rotate:"))
        self.control_layout.addWidget(self.angle_input)
        self.control_layout.addWidget(QLabel("Correction:"))
        self.control_layout.addWidget(self.correct_plus)
        self.control_layout.addWidget(self.correct_minus)


        # --- 3. main widget ---
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.h_layout.addWidget(self.main_widget)

        # self.image_label = QLabel()
        # self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.image_label.setStyleSheet("background-color: black;")

        self.edited_image_label = EditableLabel()
        self.edited_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edited_image_label.setStyleSheet("background-color: black;")

        # --- ScrollArea 추가 ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)   # 크기 변경 시 자동 반응
        self.scroll_area.setWidget(self.edited_image_label)
        self.scroll_area.setMinimumSize(1800, 1200)  # 원하는 기본 크기

        # self.main_layout.addWidget(self.image_label)
        self.main_layout.addWidget(self.scroll_area)

        self.setLayout(self.h_layout)

    def connect_signals(self):
        self.btn_drf_load.clicked.connect(self.load_from_db)
        self.cb_source_type.currentTextChanged.connect(self.set_input_type)
        self.cb_analyze_type.currentTextChanged.connect(self.set_analyze_type )
        self.input_path.textChanged.connect(self.set_input_type)
        self.btn_load.clicked.connect(self.toggle_load_source)
        self.btn_analyze.clicked.connect(self.toggle_analyze)
  
        # --- 시그널 ---
        self.btn_original_view.clicked.connect(self.show_original_view)
        self.btn_start_roi.clicked.connect(self.toggle_roi)
        self.btn_api_data_edit.clicked.connect(self.edit_api_data)
        self.btn_save_api_data.clicked.connect(self.save_api_data)


        self.btn_pause.clicked.connect(self.pause_stream)
        self.btn_resume.clicked.connect(self.resume_stream)
        self.angle_input.valueChanged.connect(self.rotate_image)
        self.correct_plus.clicked.connect(self.correct_distortion_plus)
        self.correct_minus.clicked.connect(self.correct_distortion_minus)

        # --- ROI 시그널 ---
        self.edited_image_label.roi_changed.connect(self.set_roi)
        self.edited_image_label.roi_named.connect(self.set_roi_name_and_points)

        # --- 타이머 ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def toggle_analyze(self):
        self.analyze_started = not self.analyze_started
        self.btn_analyze.setText("분석중지" if self.analyze_started else "분석시작")
        if self.analyze_started:
            if self.analyzer is None:
                self.set_analyze_type()



    def set_api_data(self, api_data:dict):
        self.api_data = api_data
        self.update_from_api_data()

    def set_analyze_type(self):
        analyze_type = self.cb_analyze_type.currentText()
        self.analyzer = self.map_analyze_type_to_analyzer[analyze_type]
        self.btn_analyze.setEnabled(self.analyzer is not None)
        


    def update_from_api_data(self):
        """self.api_data 값을 기반으로 화면 갱신"""
        # URL/Port 입력 박스 갱신
        url_text = self.input_path.text().strip()
        #### 중지함.
        if self.is_loaded:
            self.btn_load.click()

        #### 시작함.
        self.input_path.setText(f"rtsp://admin:1q2w3e4r5*!!@{self.api_data['url']}:{str(self.api_data['port'])}")
        self.cb_source_type.setCurrentText("RTSP URL")
        self.btn_load.click()

        # ROI 갱신
        # self.roi_list = list(self.api_data.get("rois", {}).values())
        self.edited_image_label.set_rois_by_dict(self.api_data.get("rois", {}))

        # Settings 반영 (예: 색상, 배경 등)
        settings = self.api_data.get("settings", {})
        self.apply_settings(settings)

        self.update_frame()

    def load_from_db(self):
        _isok, _json = APP.API.getlist(f"{self.api_url}?page_size=0")
        if _isok:
            datas = _json
            attrNames = list(_json[0].keys())
            dlg = Dialog_DB_Load(self, datas, attrNames=attrNames)
            if dlg.exec():
                self.api_data = dlg.get_selected()
                self.update_from_api_data()
        else:
            Utils.QMsg_Critical(self, title="DB 설정 Load 실패", text=f"DB 설정 Load 실패: {_json}")

    def apply_settings(self, settings:dict):
        pass

    def edit_api_data(self):
        dlg = Dialog_JsonEditor(self, self.api_url, _dict_data=self.get_current_data())
        if dlg.exec():
            self.api_data = dlg.get_value()
            # print ('api_data updated:', self.api_data)
            self.update_from_api_data()

    def get_current_data(self) -> dict:
        url_port = self.input_path.text().strip().split("@")[1]    
        url, port = url_port.split(":")
        # rois_dict = { f"roi{i}" : roi for i, roi in enumerate(self.roi_list) }
        # new_rois = dict(self.api_data["rois"])
        # if rois_dict:
        #     new_rois.pop("default_name", None)
        #     new_rois.update(rois_dict)
            
        data = {
            "id" : self.api_data.get("id", -1),
            "name" : self.api_data["name"],
            "url" : url,
            "port" : int(port),
            "rois" : self.api_data["rois"],
            "settings" : self.api_data["settings"],
            "is_active" : self.api_data["is_active"],
        }
        return data


    def save_api_data(self):
        if Utils.QMsg_question( self, 
            title="Save API Data", 
            text="API Data를 저장하시겠습니까?<br>저장 시 분석 Demon(Docker) 가 변경된 설정으로 분석됩니다.<br>",
        ):
            dataObj = {}
            dataObj['id'] = self.api_data.pop('id', -1)
            _isok, _json = APP.API.Send_json(self.api_url, dataObj, self.get_current_data())
            if _isok:
                Utils.QMsg_Info(self, title="API 저장완료", text="API 저장이 완료되었습니다.", autoClose= 1000 )
                self.api_data = _json
                self.update_from_api_data()
            else:
                Utils.QMsg_Critical(self, title="API 저장실패", 
                    text=f"API 저장에 실패하였습니다.<br>오류 메시지: {_json}")


    def toggle_roi(self):
        self.roi_setting_started = not self.roi_setting_started
        self.edited_image_label.start_roi(self.roi_setting_started)
        self.btn_start_roi.setText("Stop ROI" if self.roi_setting_started else "Start ROI")

    def show_original_view(self):
        if getattr(self, "dlg_original", None) is not None:
            self.dlg_original.set_pixmap(self.convert_to_pixmap(self.image))           
        else:
            self.dlg_original = Dlg_ImageViewer(self, self.convert_to_pixmap(self.image))
        self.dlg_original.show()

    def set_roi_name_and_points(self, name: str, roi_points: list[tuple[int, int]]):
        """
        name = ROI 이름
        roi_points = [(x1,y1), ..., (x4,y4)]
        """
        self.roi_dict = self.api_data["rois"]

        # 1. 기존 ROI 중 겹치는 위치 제거
        def is_overlapping(r1, r2):
            x1s, y1s = zip(*r1)
            x2s, y2s = zip(*r2)
            bb1 = (min(x1s), min(y1s), max(x1s), max(y1s))
            bb2 = (min(x2s), min(y2s), max(x2s), max(y2s))
            return not (bb1[2] < bb2[0] or bb1[0] > bb2[2] or bb1[3] < bb2[1] or bb1[1] > bb2[3])

        keys_to_remove = [k for k, v in self.roi_dict.items() if is_overlapping(v, roi_points)]
        for k in keys_to_remove:
            del self.roi_dict[k]

        # 2. 새 ROI 추가/업데이트
        self.roi_dict[name] = roi_points
        self.api_data["rois"] = self.roi_dict

        # 3. UI 반영
        self.edited_image_label.set_rois_by_dict(self.roi_dict)
        self.roi_label.setText(f"ROI: {name}")

        ## 4. roi start btn clock() : toggle로 종료시킴
        self.btn_start_roi.click()       




    def set_roi(self, roi_points: list[tuple[int, int]]):
        """roi_points = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]"""
        self.roi_rect = roi_points

        # === 1. ROI 중첩 제거 ===
        def is_overlapping(r1, r2):
            # 간단한 bounding box overlap check
            x1s, y1s = zip(*r1)
            x2s, y2s = zip(*r2)
            bb1 = (min(x1s), min(y1s), max(x1s), max(y1s))
            bb2 = (min(x2s), min(y2s), max(x2s), max(y2s))

            return not (bb1[2] < bb2[0] or bb1[0] > bb2[2] or
                        bb1[3] < bb2[1] or bb1[1] > bb2[3])

        # 기존 ROI와 겹치면 제거
        self.roi_list = [roi for roi in self.roi_list if not is_overlapping(roi, self.roi_rect)]

        # 새 ROI 추가
        self.roi_list.append(self.roi_rect)

        # === 2. x축 순서대로 정렬 ===
        self.roi_list.sort(key=lambda roi: min([p[0] for p in roi]))
        # === 3. roi_list로 모든 roi 그리기 ===
        self.edited_image_label.set_rois(self.roi_list)

        # === 4. label에 현재 선택된 roi 표시  ===
        self.roi_label.setText(f"ROI: {self.roi_rect}")
        self.btn_start_roi.click()

    def set_input_type(self):
        src_type = self.cb_source_type.currentText()
        if src_type == "Local Image":            
            self.input_path.setPlaceholderText("Image Path")
        elif src_type == "RTSP URL":
            self.input_path.setPlaceholderText("RTSP URL")

    def rotate_image(self):
        angle = self.angle_input.value()
        if self.edited_image is None:
            return
        image_center = tuple(np.array(self.edited_image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        result = cv2.warpAffine(self.edited_image, rot_mat, self.edited_image.shape[1::-1], flags=cv2.INTER_LINEAR)
        self.edited_image = result
        # self.show_image()


    def correct_distortion_plus(self):
        self.k1 -= self.k_step   # + 버튼 → 가장자리 앞으로


    def correct_distortion_minus(self):
        self.k1 += self.k_step   # - 버튼 → 가장자리 뒤로


    # ---------------------------
    # 소스 로드
    # ---------------------------
    def toggle_load_source(self):
        self.is_loaded = not self.is_loaded
        if self.is_loaded:
            self.btn_load.setText("Stop Stream")          
        else:
            self.btn_load.setText("Load Image/Start Stream")
            self.cap.release()
            self.timer.stop()
            return 

        src_type = self.cb_source_type.currentText()
        if src_type == "Local Image":
            #### FILE OPEN DIALOG
            fName = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif)")
            if not fName:
                return
            path = fName[0]
            if not path:
                return
            self.image = cv2.imread(path)
            if self.image is None:
                QMessageBox.critical(self, "오류", "이미지 로드 실패")
                return
            self.show_image()

        elif src_type == "RTSP URL":
            path = self.input_path.text().strip()
            self.cap = cv2.VideoCapture(path)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "오류", "RTSP 연결 실패")
                return
            self.timer.start(30)  # 30ms마다 update_frame 실행

    # ---------------------------
    # 프레임 업데이트
    # ---------------------------
    def update_frame(self):
        if self.cap and not self.paused:
            ret, frame = self.cap.read()
            if ret:
                self.image = frame
                self.edited_image = frame.copy()
                self.show_image()

    # ---------------------------
    # 프레임 표시
    # ---------------------------
    def show_image(self):
        if self.image is None:
            return
        ### 1. 원본 이미지 표시
        if getattr(self, "dlg_original", None) is not None:
            self.dlg_original.set_pixmap(self.convert_to_pixmap(self.image))


        ### 2. edited 이미지 표시
        h, w = self.image.shape[:2]
        self.edited_image_label.setFixedSize(w, h)


        edited_pixmap = self.get_edited_pixmap()
        self.edited_image_label.setPixmap(edited_pixmap)
        # print("PyQt 표시 (label):", self.edited_image_label.width(), self.edited_image_label.height())

        # 3. ROI Warp가 있으면, 보정된 ROI를 미니 윈도우로 보여줌
        s = time.perf_counter()
        if self.roi_rect:
            warped = self.warp_roi()
            if warped is not None:
                pixmap = self.roi_to_pixmap(warped)
                if getattr(self, "dlg", None) is None:
                    self.dlg = Dlg_ImageViewer(self, pixmap)
                else:
                    self.dlg.set_pixmap(pixmap)
                self.dlg.show()

        # 모든 ROI 분석 결과 overlay

        if self.analyze_started and self.analyzer:
            if isinstance(self.analyzer, CNN_Analyzer):
                pass
            elif isinstance(self.analyzer, AlarmPanelAnalyzer):
                time_start = time.perf_counter()  
                results = None
                if self.prev_분석time is None :
                    self.prev_분석time = time.perf_counter()
                    results = self.analyzer.run( image=self.edited_image, all_roi_dict=self.api_data["rois"])
                else:
                    if (time.perf_counter() - self.prev_분석time) > 1000:  # 초 단위 비교
                        self.prev_분석time = time.perf_counter()
                        results = self.analyzer.run( image=self.edited_image, all_roi_dict=self.api_data["rois"])

                if results:
                    start_time = time.perf_counter()
                    min = datetime.now().minute
                    if min % 10 == 0:
                        print( f"{datetime.now()} : {Utils.get_소요시간(start_time)} : {self.error_count} : 분석결과: {results} ")
                    if any( [ value_dict.get("ON", False) for value_dict in results.values()]):
                        self.btn_analyze.setStyleSheet("background-color: red;")
                        self.error_count += 1
                        cv2.putText(self.edited_image, f"{datetime.now()} : {self.error_count }", (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        self.save_if_needed(self.edited_image)
                        print( f"{datetime.now()} : 분석결과: {results}")
                    else:
                        self.btn_analyze.setStyleSheet("background-color: green;")

            else:
                raise ValueError(f"analyzer 타입 오류: {type(self.analyzer)}")

            # results = self.analyze_roi(self.edited_image)
            # print (f"analyze results: {results}")

        # for roi in self.roi_list:            
        #     warped_roi = self.warp_roi(roi)
        #     if warped_roi is None:
        #         continue
        #     results = self.analyze_roi(warped_roi)

        #     # ROI 좌표 기준으로 결과 텍스트 표시
        #     x, y = roi[0]
        #     cv2.putText(
        #         self.edited_image,
        #         f"{results}",
        #         (int(x), int(y) - 10),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (0, 0, 255),
        #         2,
        #         cv2.LINE_AA
        #     )

        pixmap = self.convert_to_pixmap(self.edited_image)
        self.edited_image_label.setPixmap(pixmap)

    def save_if_needed(self, image):
        now = datetime.now()

        # === 1. 시간대별 폴더 ===
        folder_name = now.strftime("%Y%m%d_%H")
        save_dir = os.path.join(INFO.BASE_DIR, "debug", folder_name)
        os.makedirs(save_dir, exist_ok=True)

        # === 2. 최근 저장 파일 확인 ===
        if self.last_saved_time:
            delta = (now - self.last_saved_time).total_seconds()
            if delta < 10:  # 최근 저장이 10초 이내 → skip
                return

        # === 3. 저장 ===
        fname = os.path.join(save_dir, f"error_{now.strftime('%Y%m%d%H%M%S')}.png")
        cv2.imwrite(fname, image)
        self.last_saved_time = now


    def apply_distortion_shift(self, image: None|np.ndarray = None) -> None : #np.ndarray:
        image = image if image is not None else self.edited_image
        h, w = image.shape[:2]

        distCoeff = np.zeros((4,1), np.float64)
        distCoeff[0,0] = self.k1  # radial distortion 계수
        distCoeff[1,0] = 0.0      # k2
        distCoeff[2,0] = 0.0      # p1
        distCoeff[3,0] = 0.0      # p2

        cam = np.eye(3, dtype=np.float32)
        cam[0,2] = w / 2.0
        cam[1,2] = h / 2.0
        cam[0,0] = w /2.0     # focal length x (해상도 비례)
        cam[1,1] = h /2.0      # focal length y (해상도 비례)

        self.edited_image = cv2.undistort(image, cam, distCoeff)



    def warp_roi(self, roi_rect:list[tuple[int, int]] = None):
        if not roi_rect or self.edited_image is None:
            return None

        # self.roi_rect = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        if len(roi_rect) != 4:
            print("ROI points not 4, got:", roi_rect)
            return None

        pts = np.array(roi_rect, dtype=np.float32)

        # 출력 사각형 크기 계산 (대략 bounding box 크기)
        (x_min, y_min) = pts.min(axis=0)
        (x_max, y_max) = pts.max(axis=0)
        w = int(x_max - x_min)
        h = int(y_max - y_min)

        if w <= 0 or h <= 0:
            print("⚠️ Invalid ROI size:", w, h)
            return None

        # 목적지 좌표 (평탄화된 직사각형)
        dst_pts = np.float32([
            [0, 0],
            [w - 1, 0],
            [w - 1, h - 1],
            [0, h - 1]
        ])

        # Perspective Transform
        M = cv2.getPerspectiveTransform(pts, dst_pts)
        warped = cv2.warpPerspective(self.edited_image, M, (w, h))

        return warped


    def get_edited_pixmap(self):
        if self.edited_image is None:
            return QPixmap()

        ### 1. 회전
        self.rotate_image()

        ### 2. 왜곡 보정
        # self.apply_distortion_shift()

        pixmap = self.convert_to_pixmap( self.edited_image)

        return pixmap

    def roi_to_pixmap(self, roi:np.ndarray) -> QPixmap:
        if roi is None:
            raise ValueError("roi is None")
        frame = cv2.resize(roi, (300, 200))  # (W, H)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        return pixmap


    def convert_to_pixmap(self, image:None|np.ndarray = None) -> QPixmap:
        # 원하는 해상도로 resize
        image = image if image is not None else self.image
        frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        return pixmap

    # ---------------------------
    # 분석  
    # ---------------------------


    def image_처리_bgr_to_gray(self, image:np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # 블러
        # blurred = cv2.GaussianBlur(enhanced, (3,3), 0)

        # 적응형 이진화 + 반전 (숫자=흰색, 배경=검정)
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 21,-25
        )
        # # Morph Opening (작은 점/노이즈 제거)
        binary_inv = cv2.bitwise_not(binary)
        blurred = cv2.GaussianBlur(binary_inv, (19,19), 0)
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        # binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        return thresh

    def crop_ROI_into_four(self, image, roi_index:int=0):
        """
        ROI_frame을 가로로 4등분하여 4개의 숫자 이미지를 반환
        """
        # 이미지의 가로 길이를 4등분
        height, width = image.shape[:2]
        segment_width = width // 4
        width_margin = 4
        ROI_frames = []

        map_index_to_start_x = {
            0: 0,
            1: 1*segment_width - width_margin,
            2: 2*segment_width - width_margin,
            3: 3*segment_width ,
        }
        map_index_to_end_x = {
            0: 1*segment_width + width_margin,
            1: 2*segment_width + 2*width_margin,
            2: 3*segment_width + 2*width_margin,
            3: width,
        }
        
        for i in range(4):
            # # 각 세그먼트의 시작 x 좌표
            # start_x = i * segment_width
            # # 마지막 세그먼트는 남은 픽셀을 모두 포함
            # if i == 3:
            # 	end_x = width
            # else:
            # 	end_x = (i + 1) * segment_width
            
            # 세그먼트 crop (전체 높이 유지)
            segment = image[:, map_index_to_start_x[i]:map_index_to_end_x[i]]
            
           
            ROI_frames.append(segment)
        
        return ROI_frames

    def analyze_roi(self, roi_image:np.ndarray) -> list[int]:
        if roi_image is None:
            return None
        results = []
        converted_ROI_Image = self.image_처리_bgr_to_gray(roi_image)
        for i, digit_image in enumerate(self.crop_ROI_into_four(converted_ROI_Image)):
            result = self.analyze_digit(digit_image)
            results.append(result)
        return results

    def analyze_digit(self, digit_image:np.ndarray) -> int:
        cnn_input, img_gray_for_cnn = self.preprocess_for_cnn_gray(digit_image.copy(), index=0)
        with torch.no_grad():
            output = self.cnn_analyzer.cnn(cnn_input)
            probs = torch.softmax(output, dim=1)
            conf, pred = torch.max(probs, dim=1)
            if conf < 0.9:  # threshold 조정
                cnn_result = -1
                # print(f"  ==> CNN 분석 결과 없음:  신뢰도{conf} : 분석결과{pred.item()}")
            else:
                cnn_result = pred.item()
            return cnn_result

    def preprocess_for_cnn_gray(self, img, index:int=0) -> tuple[torch.Tensor, np.ndarray]:
        """CNN 입력용 전처리 (RGB, resize, tensor 변환)"""
        img_resized = cv2.resize(img, (64, 64))

        # numpy → torch tensor, shape: (1, 1, 64, 64)
        img_tensor = torch.from_numpy(img_resized).float().unsqueeze(0).unsqueeze(0) / 255.0
        return img_tensor, img_resized

    # ---------------------------
    # 마우스 이벤트
    # ---------------------------
    # def mousePressEvent(self, event):
    #     if event.button() == Qt.MouseButton.LeftButton and self.edited_image is not None:
    #         pos = event.position().toPoint()
    #         if self.image_label.geometry().contains(pos):
    #             local_pos = pos - self.image_label.pos()
    #             self.drawing = True
    #             self.roi_start = (local_pos.x(), local_pos.y())
    #             self.roi_end = self.roi_start

    # def mouseMoveEvent(self, event):
    #     if self.drawing and self.edited_image is not None:
    #         pos = event.position().toPoint()
    #         local_pos = pos - self.image_label.pos()
    #         self.roi_end = (local_pos.x(), local_pos.y())
    #         # self.show_image()

    # def mouseReleaseEvent(self, event):
    #     if event.button() == Qt.MouseButton.LeftButton and self.drawing:
    #         self.drawing = False
    #         self.roi_rect = (
    #             min(self.roi_start[0], self.roi_end[0]),
    #             min(self.roi_start[1], self.roi_end[1]),
    #             abs(self.roi_end[0] - self.roi_start[0]),
    #             abs(self.roi_end[1] - self.roi_start[1]),
    #         )
    #         self.roi_label.setText(f"ROI: {self.roi_rect}")

    # ---------------------------
    # Pause / Resume
    # ---------------------------
    def pause_stream(self):
        self.paused = True

    def resume_stream(self):
        self.paused = False

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()


class Dlg_Image_ROI_Editor(QDialog):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("ROI Editor (Local / RTSP)")
        self.kwargs = kwargs

        self.setup_ui()


    def setup_ui(self):
        self.h_layout = QVBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(0)

        self.main_widget = Image_ROI_Editor(self, **self.kwargs)
        self.h_layout.addWidget(self.main_widget)

        self.setLayout(self.h_layout)


        

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     editor = Dlg_Image_ROI_Editor()
#     editor.resize(1200, 1000)
#     editor.show()
#     #### 테스트용
#     editor.main_widget.source_type.setCurrentText("RTSP URL")
#     editor.main_widget.input_path.setText("rtsp://admin:1q2w3e4r5*!!@192.168.14.100:10500")
#     editor.main_widget.btn_load.click()

#     ####
#     sys.exit(app.exec())