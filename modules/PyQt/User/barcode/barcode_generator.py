### pyinstaller --hidden-import=qrcode --hidden-import=PIL your_script.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtPrintSupport import *

import qrcode  # QR 코드 생성을 위한 라이브러리 추가
from PIL import Image
from barcode import Code128, Code39, EAN13, EAN8
from barcode.writer import ImageWriter  # 추가
import os
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class BarcodeGenerator( QObject ):
    def __init__(self, parent, serial:str, **kwargs ):
        super().__init__(parent)
        self.barcode_types = [ 'QR','Code128', 'Code39', 'EAN13', 'EAN8',]
        self.qr_sizes = ['작게', '보통', '크게']
        self.error_corrections = ['L (7%)', 'M (15%)', 'Q (25%)', 'H (30%)']

        self.default_type = self.barcode_types[0]
        self.default_error_correction = self.error_corrections[2]
        self.default_qr_size = self.qr_sizes[1]

        self.serial = serial

        # self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 입력 영역
        input_layout = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("바코드/QR코드 텍스트 입력")
        
        self.barcode_type = QComboBox()
        self.barcode_type.addItems(['Code128', 'Code39', 'EAN13', 'EAN8', 'QR'])

        # QR 코드 설정 추가
        self.qr_size = QComboBox()
        self.qr_size.addItems(['작게', '보통', '크게'])
        self.qr_size.setCurrentText('보통')
        self.qr_size.hide()  # 초기에는 숨김
        
        self.error_correction = QComboBox()
        self.error_correction.addItems(['L (7%)', 'M (15%)', 'Q (25%)', 'H (30%)'])
        self.error_correction.setCurrentText('M (15%)')
        self.error_correction.hide()  # 초기에는 숨김
        
        # 입력 컴포넌트들을 input_layout에 추가
        input_layout.addWidget(self.barcode_input)
        input_layout.addWidget(self.barcode_type)
        input_layout.addWidget(self.qr_size)
        input_layout.addWidget(self.error_correction)
        
        # input_layout을 메인 layout에 추가
        layout.addLayout(input_layout)

        # 바코드 타입 변경 시 QR 설정 표시/숨김
        self.barcode_type.currentTextChanged.connect(self.on_type_changed)
        
                # 바코드 표시 영역 추가
        self.barcode_label = QLabel()
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.barcode_label)
        
        # 생성 버튼
        generate_button = QPushButton('바코드 생성')
        generate_button.clicked.connect(self.generate_barcode)
        layout.addWidget(generate_button)

                # 프린트 버튼 추가
        print_button = QPushButton('바코드 프린트')
        print_button.clicked.connect(self.print_barcode)
        layout.addWidget(print_button)
        
        self.setLayout(layout)
        self.setWindowTitle('바코드 생성기')
        
    def on_type_changed(self, text):
        # QR 코드 선택 시 관련 설정 표시
        if text == 'QR':
            self.qr_size.show()
            self.error_correction.show()
        else:
            self.qr_size.hide()
            self.error_correction.hide()

    # 프린트 기능 추가
    def print_barcode(self):
        if not self.barcode_label.pixmap():
            QMessageBox.warning(self, '경고', '먼저 바코드를 생성해주세요.')
            return
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPrinterName("4B-2054N")  # 프린터 모델 설정
        
        # 용지 크기 설정 (100mm x 100mm)
        custom_size = QPageSize(QSizeF(100, 100), QPageSize.Unit.Millimeter)
        printer.setPageSize(custom_size)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter()
            painter.begin(printer)
            
            # 바코드 이미지 가져오기
            rect = painter.viewport()
            pixmap = self.barcode_label.pixmap()
            scaled_pixmap = pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            
            # 중앙 정렬하여 출력
            x = (rect.width() - scaled_pixmap.width()) // 2
            y = (rect.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
            painter.end()

    def generate_barcode(self, serial:str='') -> QPixmap|None:
        try:
            self.serial = serial if serial else self.serial
            if not self.serial:
                QMessageBox.warning(self, '경고', '텍스트를 입력해주세요.')
                return
                
            selected_type = self.default_type
            
            if selected_type == 'QR':
                # QR 코드 생성
                qr = qrcode.QRCode(
                    version=1,
                    error_correction={
                        'L (7%)': qrcode.constants.ERROR_CORRECT_L,
                        'M (15%)': qrcode.constants.ERROR_CORRECT_M,
                        'Q (25%)': qrcode.constants.ERROR_CORRECT_Q,
                        'H (30%)': qrcode.constants.ERROR_CORRECT_H,
                    }[self.default_error_correction],
                    box_size={
                        '작게': 6,
                        '보통': 10,
                        '크게': 14
                    }[ self.default_qr_size],
                    border=4,
                )
                qr.add_data(self.serial)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                # img.save('temp_barcode.png')
                # filename = 'temp_barcode.png'
                # PIL Image를 QPixmap으로 변환
                from PIL.ImageQt import ImageQt
                qimage = ImageQt(img)
                return  QPixmap.fromImage(qimage)

            else:
                # 일반 바코드 생성 로직 수정
                barcode_types = {
                    'Code128': Code128,
                    'Code39': Code39,
                    'EAN13': EAN13,
                    'EAN8': EAN8
                }
                
                if selected_type not in barcode_types:
                    QMessageBox.warning(self, '오류', '지원하지 않는 바코드 형식입니다.')
                    return
                    
                try:
                    barcode_class = barcode_types[selected_type]
                    barcode_instance = barcode_class(serial, writer=ImageWriter())
                    # BytesIO를 사용하여 메모리에서 이미지 생성
                    from io import BytesIO
                    buffer = BytesIO()
                    barcode_instance.write(buffer)
                    
                    # BytesIO에서 PIL Image 생성
                    buffer.seek(0)
                    pil_image = Image.open(buffer)
                    
                    # PIL Image를 QPixmap으로 변환
                    from PIL.ImageQt import ImageQt
                    qimage = ImageQt(pil_image)
                    pixmap = QPixmap.fromImage(qimage)
                    buffer.close()
                    return pixmap
                    # filename = barcode_instance.save('temp_barcode')
                except ValueError as e:
                    QMessageBox.warning(self, '오류', f'바코드 생성 실패: {str(e)}')
                    return None
            
            # 바코드 이미지 표시
            pixmap = QPixmap(filename)
            scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            self.barcode_label.setPixmap(scaled_pixmap)
            
            # 임시 파일 삭제
            os.remove(filename)
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'예기치 않은 오류가 발생했읍니다: {str(e)}')
            return None


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    barcode_widget = BarcodeGenerator()
    barcode_widget.show()
    sys.exit(app.exec())