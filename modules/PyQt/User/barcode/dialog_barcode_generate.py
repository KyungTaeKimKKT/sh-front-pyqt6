### pyinstaller --hidden-import=qrcode --hidden-import=PIL your_script.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtPrintSupport import *

from modules.PyQt.User.barcode.barcode_generator import BarcodeGenerator
from modules.PyQt.User.barcode.printer_4B_2054N import Printer_4B_2054N

import qrcode  # QR 코드 생성을 위한 라이브러리 추가
from PIL import Image
from barcode import Code128, Code39, EAN13, EAN8
from barcode.writer import ImageWriter  # 추가
import os
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_Barcode_Generate ( QDialog ):
    # 클래스 속성 추가
    TABLE_WIDTH = 360
    TABLE_ROW_HEIGHT = 40  # 40에서 50으로 증가
    TABLE_HEADER_HEIGHT = 40
    TABLE_FIRST_COLUMN_RATIO = 0.30  # 첫 번째 열의 비율을 20%에서 30%로 증가
    CONTAINER_HEIGHT = 360
    BARCODE_TARGET_WIDTH = 150
    LAYOUT_MARGIN = 5
    LAYOUT_SPACING = 20
    PREVIEW_MIN_SIZE = 400
    DIALOG_MIN_SIZE = 600
    TABLE_FONT_SIZE = 12
    TABLE_HEADER_FONT_SIZE = 16  # 헤더 폰트 크기 속성 추가
    TABLE_CELL_PADDING = 2  # 셀 패딩 속성 추가
    TABLE_GRID_WIDTH = 1
    TABLE_BORDER_WIDTH = 1

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.initUI()

        if (serial := kwargs.get('_data', {'serial': ''}).get('serial')):
            if (pixmap := BarcodeGenerator(self, serial).generate_barcode()):
                self.obj = kwargs.get('_data', {'obj': ''}).get('obj')
                # 프린트 위젯 설정 및 인쇄 실행
                QTimer.singleShot(100, lambda: self._print_document(pixmap))

        self.show()

    def initUI(self):
        self.setMinimumSize(self.DIALOG_MIN_SIZE, self.DIALOG_MIN_SIZE)
        layout = QVBoxLayout()
        
        # 프린트 미리보기 위젯만 생성
        self.print_preview = QLabel()
        self.print_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.print_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.print_preview.setMinimumSize(self.PREVIEW_MIN_SIZE, self.PREVIEW_MIN_SIZE)
        layout.addWidget(self.print_preview)
        
        self.setLayout(layout)
        self.setWindowTitle('바코드 프린트 미리보기')

    def _create_print_table(self):
        # 테이블 생성 및 설정
        print_table = QTableWidget()
        print_table.setColumnCount(2)
        
        # 테이블 데이터 준비
        display_items = ['고객사', 'Proj_No', 'Job_Name', '설비', '설비명', '공정명','수량']
        table_data = [[key, self.obj.get(key, '')] for key in display_items if key in self.obj]        
        
        print_table.setRowCount(len(table_data))
        print_table.setHorizontalHeaderLabels(['항목', '내용'])
        
        # 테이블 스타일 및 설정
        self._setup_table_style(print_table)
        self._populate_table_data(print_table, table_data)
        
        return print_table

    def _setup_table_style(self, table):
        # 테이블 스타일 설정
        table.setStyleSheet(f"""
            QTableWidget::item {{
                padding: {self.TABLE_CELL_PADDING}px;  
                padding-right: {self.TABLE_CELL_PADDING}px;
                font-size: 8pt;
                border-right: {self.TABLE_BORDER_WIDTH}px solid black;
                border-bottom: {self.TABLE_BORDER_WIDTH}px solid black;
                border-left: {self.TABLE_BORDER_WIDTH}px solid black;
                border-top: {self.TABLE_BORDER_WIDTH}px solid black;
            }}
            QTableWidget {{ 
                border: {self.TABLE_BORDER_WIDTH}px solid black;
                gridline-color: black;
            }}
            QHeaderView::section {{ 
                background-color: white;
                font-size:  {self.TABLE_HEADER_FONT_SIZE}pt;  # 헤더 폰트 크기 적용
                padding: {self.TABLE_CELL_PADDING}px;
                gridline-color: black;
                border-right: {self.TABLE_BORDER_WIDTH}px solid black;
                border-bottom: {self.TABLE_BORDER_WIDTH}px solid black;
                border-left: {self.TABLE_BORDER_WIDTH}px solid black;
                border-top: {self.TABLE_BORDER_WIDTH}px solid black;
            }}
        """)
        
        # 스크롤바 완전히 제거
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        
        # 크기 설정
        total_width = self.TABLE_WIDTH
        table.setFixedWidth(total_width)
        table.setColumnWidth(0, int(total_width * self.TABLE_FIRST_COLUMN_RATIO ))
        table.setColumnWidth(1, int(total_width * (1 - self.TABLE_FIRST_COLUMN_RATIO)) - 2)
        
        # 동적 높이 계산 수정
        row_height = self.TABLE_ROW_HEIGHT
        header_height = self.TABLE_HEADER_HEIGHT
        total_height = header_height + (row_height * table.rowCount())
        
        # 테이블 전체 높이 설정
        table.setFixedHeight(total_height)
        
        # 각 행의 높이를 자동 조절되도록 설정
        for row in range(table.rowCount()):
            table.setRowHeight(row, row_height)
        
        # 헤더 설정
        header = table.horizontalHeader()
        header.setFixedHeight(header_height)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        
        # 테두리 설정
        table.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        table.setLineWidth(1)

    def _populate_table_data(self, table, data):
        for row, (key, value) in enumerate(data):
            for col, text in enumerate([key, str(value)]):
                item = QTableWidgetItem(text)
                font = item.font()
                font.setPointSize(self.TABLE_FONT_SIZE)
                font.setBold(True)
                item.setFont(font)
                # 텍스트 정렬 설정 (세로 중앙 정렬만 유지)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                # 자동 줄바꿈 활성화
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                table.setItem(row, col, item)  
        
        # 내용에 따라 행 높이 자동 조절
        table.resizeRowsToContents()

    def _create_table_image(self):
        # 테이블 생성
        table = self._create_print_table()
        
        # 테이블을 이미지로 변환
        image = QImage(table.size(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        table.render(painter)
        painter.end()
        
        return image

    def _print_document(self, pixmap:QPixmap):
        # 프린트 위젯 생성
        self.print_widget = QWidget()
        print_layout = QVBoxLayout(self.print_widget)
        print_layout.setContentsMargins(self.LAYOUT_MARGIN, self.LAYOUT_MARGIN, 
                                      self.LAYOUT_MARGIN, self.LAYOUT_MARGIN)
        print_layout.setSpacing(self.LAYOUT_SPACING)

        # 테이블과 바코드를 1:1 비율로 설정
        container_height = self.CONTAINER_HEIGHT
        section_height = container_height // 2  # 각 섹션의 높이는 동일하게

        self.print_widget.setFixedSize(container_height, container_height)

        # 테이블 라벨 설정
        table_label = QLabel()
        table_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        table_label.setFixedHeight(section_height)
        table_label.setFixedWidth(container_height - 10)  # 여백을 고려한 너비 설정
        table_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 테이블 이미지 생성 및 스케일링
        table_image = self._create_table_image()
        table_pixmap = QPixmap.fromImage(table_image)

        
        # 테이블 이미지를 label 크기에 맞게 스케일링하되, 가로 비율 무시
        scaled_table = table_pixmap.scaled(table_label.width(), section_height,
                                        #  Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                         Qt.AspectRatioMode.IgnoreAspectRatio,  # 비율 무시
                                         Qt.TransformationMode.SmoothTransformation)
        table_label.setPixmap(scaled_table)
        # table_label.setPixmap(table_pixmap)
        
        print_layout.addWidget(table_label)

        # 바코드 이미지 추가
        barcode_label = QLabel()

        scaled_pixmap = self._trim_and_scale_pixmap(pixmap, self.BARCODE_TARGET_WIDTH, section_height)
        barcode_label.setPixmap(scaled_pixmap)
        barcode_label.setFixedHeight(section_height)
        barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        print_layout.addWidget(barcode_label)

        # 이미지 생성 및 프린트
        image = self._create_print_image()
        self._update_preview(image)
        self._send_to_printer(image)



    def _trim_and_scale_pixmap(self, pixmap: QPixmap, target_width: int, target_height: int) -> QPixmap:
        # 이미지에서 투명/흰색 여백 찾기
        img = pixmap.toImage()
        width = img.width()
        height = img.height()
        
        left = width
        right = 0
        top = height
        bottom = 0
        
        # 실제 내용이 있는 영역 찾기
        for y in range(height):
            for x in range(width):
                color = QColor(img.pixel(x, y))
                if color.alpha() > 0 and color != QColor(Qt.GlobalColor.white):
                    left = min(left, x)
                    right = max(right, x)
                    top = min(top, y)
                    bottom = max(bottom, y)
        
        # 여백이 없는 영역 추출
        if left < right and top < bottom:
            trimmed = pixmap.copy(left, top, right - left + 1, bottom - top + 1)
        else:
            trimmed = pixmap
        
        # 목표 크기에 맞게 스케일링
        return trimmed.scaled(target_width, target_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)


    def _create_print_image(self):
        image = QImage(self.print_widget.size(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.print_widget.render(painter)
        painter.end()
        return image

    def _update_preview(self, image:QImage):
        preview_pixmap = QPixmap.fromImage(image)
        # 프리뷰 위젯의 크기에 맞게 스케일링
        preview_size = self.print_preview.size()
        trimmed_and_scaled = self._trim_and_scale_pixmap(
            preview_pixmap,
            preview_size.width(),
            preview_size.height()
        )
        
        self.print_preview.setPixmap(trimmed_and_scaled)

    def _send_to_printer(self, image):
        self.prt = Printer_4B_2054N(self,
                                   size_label=QSizeF(4, 4),
                                   margins=QMarginsF(0.2, 0.2, 0.2, 0.2),
                                   scale_x=1.0,
                                   scale_y=1.0)
        self.prt.signal_prt_end.connect(self._on_prt_completed)
        self.setModal(True)
        self.prt.print_image(image)

    @pyqtSlot()
    def _on_prt_completed(self):

        return 
        # self.done(0)  # close() 대신 done() 사용
        QTimer.singleShot(1000, self.accept)

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

    def generate_barcode(self):
        try:
            text = self.barcode_input.text()
            if not text:
                QMessageBox.warning(self, '경고', '텍스트를 입력해주세요.')
                return
                
            selected_type = self.barcode_type.currentText()
            
            if selected_type == 'QR':
                # QR 코드 생성
                qr = qrcode.QRCode(
                    version=1,
                    error_correction={
                        'L (7%)': qrcode.constants.ERROR_CORRECT_L,
                        'M (15%)': qrcode.constants.ERROR_CORRECT_M,
                        'Q (25%)': qrcode.constants.ERROR_CORRECT_Q,
                        'H (30%)': qrcode.constants.ERROR_CORRECT_H,
                    }[self.error_correction.currentText()],
                    box_size={
                        '작게': 6,
                        '보통': 10,
                        '크게': 14
                    }[self.qr_size.currentText()],
                    border=4,
                )
                qr.add_data(text)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save('temp_barcode.png')
                filename = 'temp_barcode.png'
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
                    barcode_instance = barcode_class(text, writer=ImageWriter())
                    filename = barcode_instance.save('temp_barcode')
                except ValueError as e:
                    QMessageBox.warning(self, '오류', f'바코드 생성 실패: {str(e)}')
                    return
            
            # 바코드 이미지 표시
            pixmap = QPixmap(filename)
            scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            self.barcode_label.setPixmap(scaled_pixmap)
            
            # 임시 파일 삭제
            os.remove(filename)
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'예기치 않은 오류가 발생했읍니다: {str(e)}')


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    barcode_widget = BarcodeGenerator()
    barcode_widget.show()
    sys.exit(app.exec())