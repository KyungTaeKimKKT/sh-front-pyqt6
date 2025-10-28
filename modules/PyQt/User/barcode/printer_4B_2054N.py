from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtPrintSupport import *


class Printer_4B_2054N(QObject):
	signal_prt_end = pyqtSignal()

	def __init__(self, parent, **kwargs):
		""" kwargs 
			size_label = QSizeF(4,4 ) 단위: Inches ==> priter 설정때에서 그렇게 보임. QSizeF(100,100 ) 단위: Milimeter에서 변경됨
			margins = QMarginsF(0,0,0,0), QPageLayout.Unit.Inch
			scale_x = 1.0
			scale_y = 1.0		
		"""
		super().__init__(parent)
		self.widParent = parent if parent else None

		self._update_kwargs(**kwargs)

		self.printer = QPrinter()		
		self.printer.setPrinterName(self.priterName)

		# 프린터 해상도 설정 추가
		self.printer.setResolution(1200)  # DPI 설정
	
		pageSize = QPageSize( self.size_label, QPageSize.Unit.Inch, "QR_Label")
		self.printer.setPageSize( pageSize )

		self.printer.setFullPage(True)
		self.printer.setPageMargins( self.margins, QPageLayout.Unit.Inch )
		self.printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)
	
	def _update_kwargs(self, **kwargs):
		self.priterName = kwargs.get('printerName', '4BARCODE_4B-2054N' )
		self.size_label =   kwargs.get( 'size_label', QSizeF(4,4) )
		self.margins  =  kwargs.get ('margins', QMarginsF(0,0,0,0) )
		self.scale_x =  kwargs.get( 'scale_x' ,  1.0 )
		self.scale_y =  kwargs.get( 'scale_y',  1.0	)

	def print_me(self, renderWid:QWidget, **kwargs):
		""" kwargs 
			scale_x = 1.0 
			scale_y = 1.0

		"""
		s_x = kwargs.get('scale_x', self.scale_x)
		s_y = kwargs.get('scale_y', self.scale_y)

		# dialog = QPrintDialog(self.printer, self.widParent)
		# if dialog.exec() == QPrintDialog.DialogCode.Accepted:
		# 	painter = QPainter()
		# 	painter.begin(self.printer)
			
		# 	renderWid.render(painter)
		# 	# # 바코드 이미지 가져오기
		# 	# rect = painter.viewport()
		# 	# pixmap = self.barcode_label.pixmap()
		# 	# scaled_pixmap = pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, 
		# 	# 							Qt.TransformationMode.SmoothTransformation)
			
		# 	# # 중앙 정렬하여 출력
		# 	# x = (rect.width() - scaled_pixmap.width()) // 2
		# 	# y = (rect.height() - scaled_pixmap.height()) // 2
		# 	# painter.drawPixmap(x, y, scaled_pixmap)
			
		# 	painter.end()
		
		# return 

		printer = self.printer
		painter = QPainter()  # printer 객체를 생성자에서 제거
		if painter.begin(printer):  # begin이 성공했을 때만 진행

			# 안티앨리어싱 설정 추가
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
			painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

			# 프린터 페이지 크기와 위젯 크기 가져오기
			printer_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
			widget_rect = renderWid.rect()

			# 스케일 계산 - 여유 공간을 두기 위해 0.8을 곱함
			scale_x = (printer_rect.width() * 0.8) / widget_rect.width()
			scale_y = (printer_rect.height() * 0.8) / widget_rect.height()
			scale = min(scale_x, scale_y)

			# 스케일 적용
			painter.scale(scale, scale)

			# 중앙 정렬을 위한 위치 계산 - 여백 고려
			x_offset = (printer_rect.width() / scale - widget_rect.width()) / 2
			y_offset = (printer_rect.height() / scale - widget_rect.height()) / 2

			# 위젯 렌더링 위치 조정
			painter.translate(x_offset, y_offset)



			renderWid.render(painter)
			painter.end()
			self.signal_prt_end.emit()
		else:


	def print_image(self, image: QImage):
		printer = self.printer
		painter = QPainter()
		
		if painter.begin(printer):
     # 디버깅용 이미지 저장 전 품질 개선
			debug_image = image.copy()
			debug_image.setDevicePixelRatio(2.0)  # 이미지 해상도 2배 증가

			# 디버깅용 이미지 저장
			debug_image.save("./debug/print_preview_before.png", "PNG", 100)  # 최대 품질로 저장

			# 렌더링 품질 향상을 위한 설정 강화
			painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
			painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
			painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
			# painter.setRenderHint(QPainter.RenderHint.HighQualityAntialiasing, True)

			# 프린터 페이지 크기 가져오기
			printer_rect = printer.pageRect(QPrinter.Unit.DevicePixel)

			# 이미지에서 실제 콘텐츠 영역 찾기 (여백 최적화)
			content_rect = self._get_content_rect(image)

			# 디버깅용 이미지 저장 (원본)
			image.save("./debug/original_image.png")
			
			# 새 이미지 생성 (프린터 해상도에 맞춤)
			final_image = QImage(int(printer_rect.width()), int(printer_rect.height()), 
							   QImage.Format.Format_ARGB32)
			final_image.fill(Qt.GlobalColor.white)
			
			# 임시 페인터로 최종 이미지 그리기
			temp_painter = QPainter(final_image)
			temp_painter.setRenderHints(painter.renderHints())
			
			# 스케일 계산 (여백을 고려)
			margin_factor = 0.95  # 5% 여백
			scale = min(printer_rect.width() * margin_factor / content_rect.width(),
					   printer_rect.height() * margin_factor / content_rect.height())
			
			# 중앙 정렬을 위한 위치 계산
			x_offset = (printer_rect.width() - content_rect.width() * scale) / 2
			y_offset = (printer_rect.height() - content_rect.height() * scale) / 2
			
			# 변환 적용
			temp_painter.translate(x_offset, y_offset)
			temp_painter.scale(scale, scale)
			
			# 실제 콘텐츠 영역만 그리기
			temp_painter.drawImage(0, 0, image, 
								 content_rect.x(), content_rect.y(),
								 content_rect.width(), content_rect.height())
			temp_painter.end()
			
			# 디버깅용 최종 이미지 저장
			final_image.save("./debug/final_print_image.png")
			
			# 프린터에 최종 이미지 그리기
			painter.drawImage(0, 0, final_image)
			painter.end()
			self.signal_prt_end.emit()
		else:



	def _get_content_rect(self, image: QImage) -> QRect:
		"""이미지에서 실제 콘텐츠가 있는 영역을 찾아 반환"""
		width = image.width()
		height = image.height()
		
		left = width
		right = 0
		top = height
		bottom = 0
		
		# 이미지 스캔하여 콘텐츠 영역 찾기
		for y in range(height):
			for x in range(width):
				if image.pixel(x, y) != qRgba(255, 255, 255, 255):  # 흰색이 아닌 픽셀 찾기
					left = min(left, x)
					right = max(right, x)
					top = min(top, y)
					bottom = max(bottom, y)
		
		# 여백 추가 (5픽셀)
		padding = 5
		left = max(0, left - padding)
		top = max(0, top - padding)
		right = min(width - 1, right + padding)
		bottom = min(height - 1, bottom + padding)
		
		return QRect(left, top, right - left + 1, bottom - top + 1)

	def _get_printer_scale(self) -> float:
		return 1.0
		return self.doubleSpinBox_scale.value()