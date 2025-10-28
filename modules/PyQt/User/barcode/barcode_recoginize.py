from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import cv2
import zxingcpp
import numpy as np
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class BarcodeRecognizer(QObject):
    barcode_detected = pyqtSignal(str, str)  # type, data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.formats = {
            'QR Code': zxingcpp.BarcodeFormat.QRCode,
            'Code 128': zxingcpp.BarcodeFormat.Code128,
            'Code 39': zxingcpp.BarcodeFormat.Code39,
            'EAN-13': zxingcpp.BarcodeFormat.EAN13,
            'EAN-8': zxingcpp.BarcodeFormat.EAN8
        }
        
    def decode_image(self, image, format_name='QR Code'):
        try:
            selected_format = self.formats.get(format_name)
            if selected_format is None:

                return None, None
            
            # OpenCV 이미지를 grayscale로 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # zxingcpp에 전달할 때 이미지 품질 향상
            gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
                        
            results = zxingcpp.read_barcodes(gray, formats=selected_format)
            
            for result in results:
                if result.valid:
                    # 원본 이미지 크기에 맞게 position 조정
                    position = result.position
                    points = []
                    for point in [position.top_left, position.top_right, 
                                position.bottom_right, position.bottom_left]:
                        points.append((int(point.x/2), int(point.y/2)))  # 2.0 스케일 보정
                    return str(result.format), result.text, points
            return None, None, None
        
        except Exception as e:

            return None, None, None

class Wid_Barcode( QWidget ):   
    signal_barcode_scanned = pyqtSignal(str)

    def __init__(self, parent=None, recognition_cooldown=10, max_retries=10, frame_update_time=100):
        super().__init__(parent)
        self.recognizer = BarcodeRecognizer()
        self.recognition_cooldown = recognition_cooldown
        self.max_retries = max_retries
        self.frame_update_time = frame_update_time
        self.last_successful_scan = None
        self.scanned_barcodes = set()
        self.current_retry_count = 0
        self.result_image = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("바코드 스캐너")
        self.setMinimumSize(800, 600)
        
        # 메인 레이아웃을 GridLayout으로 변경
        main_layout = QGridLayout()
        
        # 1행: 제목 레이블들
        camera_title = QLabel("실시간 카메라 영상")
        barcode_title = QLabel("인식된 바코드")
        for label in [camera_title, barcode_title]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; padding: 10px; }")
        main_layout.addWidget(camera_title, 0, 0)
        main_layout.addWidget(barcode_title, 0, 1)
        
        # 2행: 이미지 표시 영역
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(400, 300)
        self.result_image_label = QLabel()
        self.result_image_label.setMinimumSize(400, 300)
        main_layout.addWidget(self.camera_label, 1, 0)
        main_layout.addWidget(self.result_image_label, 1, 1)
        
        # 3행: 포맷 선택과 결과 내용
        format_container = QWidget()
        format_layout = QHBoxLayout(format_container)
        format_layout.addWidget(QLabel("바코드 형식:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.recognizer.formats.keys())
        format_layout.addWidget(self.format_combo)
        
        self.result_content = QLabel()
        self.result_content.setWordWrap(True)
        self.result_content.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        
        main_layout.addWidget(format_container, 2, 0)
        main_layout.addWidget(self.result_content, 2, 1)
        
        # 4행: 스캔 목록과 시간 정보
        scan_list_container = QWidget()
        scan_list_layout = QVBoxLayout(scan_list_container)
        self.scanned_barcodes_label = QLabel("인식된 바코드 목록:")
        self.scanned_barcodes_content = QLabel()
        self.scanned_barcodes_content.setWordWrap(True)
        self.scanned_barcodes_content.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        scan_list_layout.addWidget(self.scanned_barcodes_label)
        scan_list_layout.addWidget(self.scanned_barcodes_content)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(scan_list_container, 3, 0, 1, 1)
        main_layout.addWidget(self.time_label, 3, 1)
        
        # 열 비율 설정
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        
        self.setLayout(main_layout)
        
        # 카메라 설정
        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(self.frame_update_time)  # ms 간격으로 프레임 업데이트
        
        # 시그널 연결
        self.recognizer.barcode_detected.connect(self.on_barcode_detected)
        
    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        current_time = QDateTime.currentDateTime()

        # 결과 이미지 초기화
        self.result_image = None  # 여기에 추가
        
        # 쿨다운 체크
        if self.last_successful_scan is not None:
            elapsed = self.last_successful_scan.secsTo(current_time)
            if elapsed < self.recognition_cooldown:
                remaining = self.recognition_cooldown - elapsed
                self.result_content.setText(f"다음 스캔까지 대기 중... ({remaining}초)")
                self.time_label.setText(f"마지막 성공 스캔: {self.last_successful_scan.toString('yyyy-MM-dd hh:mm:ss')}")
                self._update_camera_display(frame)
                return

        # 바코드 인식 시도
        format_name = self.format_combo.currentText()
        barcode_type, barcode_data, position = self.recognizer.decode_image(frame, format_name)


        if barcode_type == "FOUND_BUT_UNREADABLE":
            self.result_content.setText("바코드가 감지되었으나 읽을 수 없읍니다.")
            self.result_content.setStyleSheet("QLabel { background-color: #fff3e6; padding: 10px; }")
        elif barcode_type == "NO_BARCODE":
            self.result_content.setText("화면에서 바코드를 찾을 수 없읍니다.")
            self.result_content.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        elif barcode_data and position:
            # 바코드 영역 표시
            result_frame = frame.copy()
            points = np.array(position, np.int32)
            points = points.reshape((-1,1,2))
            cv2.polylines(result_frame, [points], True, (0,255,0), 2)
                        # 바코드 중심에 텍스트 추가
            center = np.mean(points, axis=0).astype(int)
            cv2.putText(result_frame, barcode_data, (center[0][0], center[0][1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            # 결과 이미지 저장 및 즉시 표시
            self.result_image = result_frame.copy()  # .copy() 추가
            self._update_camera_display(result_frame)  # 즉시 화면 업데이트

            self.current_retry_count = 0
            self.last_successful_scan = current_time
            
            if barcode_data in self.scanned_barcodes:
                self.result_content.setText(f"이미 인식된 바코드입니다.\n타입: {barcode_type}\n데이터: {barcode_data}")
                self.result_content.setStyleSheet("QLabel { background-color: #fff3e6; padding: 10px; }")
            else:
                self.scanned_barcodes.add(barcode_data)
                self.recognizer.barcode_detected.emit(barcode_type, barcode_data)
                self.result_content.setText(f"신규 바코드 인식 성공!\n타입: {barcode_type}\n데이터: {barcode_data}")
                self.result_content.setStyleSheet("QLabel { background-color: #e6ffe6; padding: 10px; }")
            
            self.time_label.setText(f"마지막 성공 스캔: {current_time.toString('yyyy-MM-dd hh:mm:ss')}")
            self.time_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.current_retry_count += 1
            if self.current_retry_count >= self.max_retries:
                self.current_retry_count = 0
                self.last_successful_scan = None  # 실패 시 쿨다운 적용 제거
                self.result_content.setText(f"바코드 인식 실패 (최대 재시도 횟수 초과)")
                self.result_content.setStyleSheet("QLabel { background-color: #ffe6e6; padding: 10px; }")
            else:
                self.result_content.setText(f"바코드 인식 시도 중... ({self.current_retry_count}/{self.max_retries})")
                self.result_content.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
            
            self.time_label.setText(f"마지막 시도: {current_time.toString('yyyy-MM-dd hh:mm:ss')}")
            self.time_label.setStyleSheet("QLabel { color: red; }")

        # 화면 업데이트
        display_frame = self.result_image if self.result_image is not None else frame
        self._update_camera_display(display_frame)
    
    def _update_camera_display(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # 카메라 화면 업데이트
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.camera_label.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio))
            
        # 결과 이미지가 있는 경우 결과 이미지도 업데이트
        if self.result_image is not None:
            result_rgb = cv2.cvtColor(self.result_image, cv2.COLOR_BGR2RGB)
            h, w, ch = result_rgb.shape
            bytes_per_line = ch * w
            result_qt_image = QImage(result_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.result_image_label.setPixmap(QPixmap.fromImage(result_qt_image).scaled(
                self.result_image_label.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio))

    @pyqtSlot(str, str)
    def on_barcode_detected(self, barcode_type, barcode_data):
        self.result_content.setText(f"상태: 성공\n타입: {barcode_type}\n데이터: {barcode_data}")
        self.result_content.setStyleSheet("QLabel { background-color: #e6ffe6; padding: 10px; }")

            # 스캔된 바코드 목록 업데이트
        barcode_list = "\n".join([f"- {code}" for code in self.scanned_barcodes])
        self.scanned_barcodes_content.setText(barcode_list)
        self.signal_barcode_scanned.emit( barcode_data)

    def closeEvent(self, event):
        self.camera.release()
        self.timer.stop()
        super().closeEvent(event)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    wid_barcode = Wid_Barcode (
        recognition_cooldown=10,  # 10초 쿨다운
        max_retries=10,          # 최대 10회 재시도
        frame_update_time=100    # 100ms 프레임 업데이트
        )
    wid_barcode.setWindowFlags( Qt.Window  | Qt.WindowStaysOnTopHint 
                            | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint )
    wid_barcode.setWindowModality(Qt.WindowModal)  # 창 모달
    wid_barcode.show()
    sys.exit(app.exec())