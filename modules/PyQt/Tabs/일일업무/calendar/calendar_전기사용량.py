from modules.common_import_v2 import *

from urllib.request import urlretrieve

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
from modules.PyQt.dialog.hover.dlg_hover import Dlg_Hover


class UploadDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("전기사용량 파일 업로드")
		self.resize(450, 180)
		self.selected_files = {}

		layout = QVBoxLayout(self)

		self.label_info = QLabel("업로드할 파일을 선택하세요:")		
		layout.addWidget(self.label_info)

		layout.addSpacing(16)

		# --- 하이전기 파일 버튼 및 파일명 라벨
		self.btn_high = QPushButton("하이전기_file 선택")
		self.btn_high.clicked.connect(lambda: self.select_file("하이전기_file"))
		layout.addWidget(self.btn_high)

		self.label_high = QLabel("선택된 파일 없음")
		layout.addWidget(self.label_high)
		layout.addSpacing(16*2)
		# --- 폴리전기 파일 버튼 및 파일명 라벨
		self.btn_poly = QPushButton("폴리전기_file 선택")
		self.btn_poly.clicked.connect(lambda: self.select_file("폴리전기_file"))
		layout.addWidget(self.btn_poly)

		self.label_poly = QLabel("선택된 파일 없음")
		layout.addWidget(self.label_poly)

		layout.addSpacing(16*2)

		# --- OK/Cancel 버튼
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	def select_file(self, key):
		file_path, _ = QFileDialog.getOpenFileName(
			self,
			f"{key} 업로드 파일 선택",
			os.path.expanduser("~"),
			"Excel Files (*.xlsx);;All Files (*)",
			options=QFileDialog.Option.DontUseNativeDialog
		)
		if file_path:
			self.selected_files[key] = file_path
			file_name = os.path.basename(file_path)
			logger.debug(f"{key} 선택됨: {file_path}")
			if key == "하이전기_file":
				self.label_high.setText(f"선택: {file_name}")
			elif key == "폴리전기_file":
				self.label_poly.setText(f"선택: {file_name}")




class QCalendar_전기사용량( LazyParentAttrMixin_V2, QCalendarWidget):

	def __init__(self, parent=None, **kwargs):
		super().__init__(parent)
		for k,v in kwargs.items():
			setattr(self, k, v)
		
		self.event_bus = event_bus
		self.api_datas:Optional[list[dict]] = None
		self.api_datas_dict:Optional[dict] = None
		self.api_datas_month_dict:Optional[dict] = {}
		self.table_name:Optional[str] = None
		self.url:Optional[str] = None

		self.events = {}
		self.date_rect_map = {}  # QDate -> QRect 매핑 저장

		self.setGridVisible(True)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.cell_default = QTextCharFormat()
		self.cell_default.setBackground( QColor("white"))

		self.cell_changed = QTextCharFormat()
		self.cell_changed.setBackground( QColor("yellow"))


		self.clicked.connect(self.slot_clicked)
		self.currentPageChanged.connect(self.slot_current_page_changed )
		self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.contextMenuEvent)

		self.run_lazy_attr()

	def on_all_lazy_attrs_ready(self):
		self.APP_ID = self.lazy_attrs['APP_ID']
		self.appDict =  copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[self.APP_ID])
		self.table_name = Utils.get_table_name(self.APP_ID)
		if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
			self.url = Utils.get_api_url_from_appDict(self.appDict)
		else:
			raise ValueError(f"{self.__class__.__name__} : on_all_lazy_attrs_ready : appDict or url not found")
		self.subscribe_gbus()


	def subscribe_gbus(self):
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_api_datas_changed)
		# self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_api_datas_changed )


	def on_api_datas_changed(self, api_datas:list[dict]):
		if not api_datas:
			self.api_datas = None
			return
		self.api_datas = copy.deepcopy(api_datas)
		self.api_datas_dict = { obj.get('일자'): obj for obj in self.api_datas }
		# 조회된 월 기록
		for obj in self.api_datas:
			d = obj.get("일자")  # 'YYYY-MM-DD'
			if d:
				y, m = d.split("-")[0:2]
				ym_key = f"{y}-{m}"
				self.api_datas_month_dict[ym_key] = True

		self._update_data()
		
	# def mousePressEvent(self, event):
	# 	print(f"mousePressEvent: {event.button()}")
	# 	if event.button() == Qt.MouseButton.RightButton:
	# 		clicked_date = self._date_from_pos(event.pos())
	# 		print(f"clicked_date: {clicked_date}")
	# 		if clicked_date:
	# 			self.setSelectedDate(clicked_date)
	# 			self._show_context_menu(event.globalPos(), clicked_date)
	# 	else:
	# 		super().mousePressEvent(event)

	def _date_from_pos(self, pos: QPoint):
		for date, rect in self.date_rect_map.items():
			if rect.contains(pos):
				return date
		return None

	def contextMenuEvent(self,  pos: QPoint):

		mouse_qDate = self._date_from_pos(pos)
		select_qDate = self.selectedDate()
		if mouse_qDate != select_qDate:
			select_qDate = mouse_qDate		
			_text = f"날짜: {select_qDate.toString(Qt.DateFormat.ISODate)} : 마우스 우클릭 기준일로 적용합니다."
		else:
			_text = f"날짜: {select_qDate.toString(Qt.DateFormat.ISODate)}"

		is_future_date = select_qDate > QDate.currentDate()
		is_today = select_qDate == QDate.currentDate()
		if is_future_date:
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 업로드 실패", text="미래 날짜는 선택할 수 없읍니다.")
			return  # 미래 날짜는 context menu 없음
		
		self.setSelectedDate(select_qDate)
		select_date_str = select_qDate.toString(Qt.DateFormat.ISODate)

		menu = QMenu()
		# Label로 날짜를 표시 (비활성화된 QAction)
		labelAction = QAction(_text, self)
		labelAction.setEnabled(False)  # 클릭 안 되도록 비활성화
		menu.addAction(labelAction)

		menu.addSeparator()  # 구분선 추가

		if is_today:
			# File Upload: 오늘만 활성화, 그 외는 비활성화
			uploadAction = QAction('File Upload', self)
			uploadAction.setEnabled(True)
			uploadAction.triggered.connect(lambda: self.on_file_upload(date_str=select_date_str))
			menu.addAction(uploadAction)

			if self._is_file_exist(select_date_str):
				deleteAction = QAction('File Delete', self)
				deleteAction.setEnabled(True)
				deleteAction.triggered.connect(lambda: self.on_file_delete(date_str=select_date_str))
				menu.addAction(deleteAction)

		if self._is_file_exist(select_date_str):
			# File Download: 파일이 있는 경우만 활성화
			downloadAction = QAction('File Download', self)
			downloadAction.setEnabled(True)
			downloadAction.triggered.connect(lambda: self.on_file_download(obj= self.api_datas_dict[select_date_str], date_str=select_date_str))
			menu.addAction(downloadAction)

		# 메뉴 표시
		if menu.actions():
			menu.exec(self.mapToGlobal(pos) )

	def on_file_delete(self, date_str:str):
		logger.debug(f"{self.__class__.__name__} : on_file_delete : {date_str}")
		if not self.url:
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 삭제 실패", text="URL이 없읍니다.")
			return
		
		index = self.api_datas.index(self.api_datas_dict[date_str])
		_isOk = APP.API.delete( f"{self.url}{self.api_datas_dict[date_str].get('id')}" )
		if _isOk:
			Utils.generate_QMsg_Information(self, title="전기사용량 파일 삭제 완료", text="파일이 정상적으로 삭제되었읍니다.", autoClose=1000)
			self.api_datas.pop(index)
			self.api_datas_dict.pop(date_str)
			self._update_data(api_datas=self.api_datas)
		else:
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 삭제 실패", text="파일이 삭제되지 않았읍니다.")


	def on_file_upload(self, date_str:str):
		logger.debug(f"{self.__class__.__name__} : on_file_upload : {date_str}")
		if not self.url:			
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 업로드 실패", text="URL이 없읍니다.")
			return
		
		dialog = UploadDialog(self)
		if dialog.exec():
			upload_result = dialog.selected_files
			logger.debug(f"선택된 파일들: {upload_result}")
			sendFiles = { key: open(fName, 'rb') for key, fName in upload_result.items() }
			if date_str in self.api_datas_dict:
				originalDict = { 'id': self.api_datas_dict[date_str].get('id')}
				sendData = {'id': self.api_datas_dict[date_str].get('id'), '일자': date_str}
				index = self.api_datas.index(self.api_datas_dict[date_str])
			else:
				originalDict = {'id': -1}
				sendData =  {'id': -1, '일자': date_str}
				index = None
			_isOk, _json = APP.API.Send( self.url, originalDict, 
						  sendData =sendData, sendFiles=sendFiles )
			try:
				for f in sendFiles.values():
					f.close()
			except Exception as e:
				logger.error(f"{self.__class__.__name__} : on_file_upload : 파일 닫기 실패: {e}")

			if _isOk:
				Utils.generate_QMsg_Information(self, title="전기사용량 파일 업로드 완료", text="모든 파일이 정상적으로 업로드되었읍니다.", autoClose=1000)
				if index is not None:
					self.api_datas[index] = _json
				else:
					self.api_datas.insert(0, _json)
				self.api_datas_dict[date_str] = _json
				self._update_data(api_datas=self.api_datas)

			else:
				Utils.generate_QMsg_critical(self, title="전기사용량 파일 업로드 실패", text="일부 파일이 업로드되지 않았읍니다.")

		else:
			logger.debug("파일 업로드 취소됨")

	def on_file_download(self, obj:dict, date_str:str):

		urls = [url for url in [obj.get("하이전기_file"), obj.get("폴리전기_file")] if url]
		if not urls:
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 다운로드 실패", text="파일이 없읍니다.")
			return
		Utils.file_download_multiple(urls)



	def _is_file_exist(self, date_str:str) -> bool:
		return bool( self.api_datas_dict and date_str in self.api_datas_dict )
			

	def _update_data(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
		self.events = self._get_event_dates()
		self.updateCells()  # <- 전체 달력 다시 그림
		

	def _get_event_dates(self) -> dict:
		events = {}
		for obj in self.api_datas:
			date_str = obj.get('일자')
			if not date_str:
				continue

			qdate = QDate.fromString(date_str, Qt.DateFormat.ISODate)
			if not qdate.isValid():
				logger.warning(f"잘못된 일자: {date_str}")
				continue

			events[qdate] = obj.get('id', -1)
		return events
	
	@pyqtSlot()
	def slot_current_page_changed( self ):
		year = self.yearShown()
		month = self.monthShown()
		ym_key = f"{year}-{month}"
		# 오늘이 포함된 월은 무조건 조회
		today = QDate.currentDate()
		if not (today.year() == year and today.month() == month):
			if self.api_datas_month_dict.get(ym_key):
				logger.debug(f"{ym_key} 이미 조회됨 → 생략")
				return

		param = f"?year={self.yearShown()}&month={self.monthShown()}&page_size=0"
		try:
			is_ok, _json = APP.API.getlist( self.url+param )
			if is_ok:
				combined = {obj['일자']: obj for obj in self.api_datas} if self.api_datas else {}
				for obj in _json:
					combined[obj['일자']] = obj

				self.api_datas = list(combined.values())
				self.api_datas_dict = {obj['일자']: obj for obj in self.api_datas}
				self.api_datas_month_dict[ym_key] = True  # 조회 완료 처리
				self._update_data()
			else:
				Utils.generate_QMsg_critical(self, title="전기사용량 파일 조회 실패", text="파일이 조회되지 않았읍니다.")
		except Exception as e:
			logger.error(f"{self.__class__.__name__} : slot_current_page_changed : {e}")
			logger.error(f"{self.__class__.__name__} : slot_current_page_changed : {traceback.format_exc()}")
			Utils.generate_QMsg_critical(self, title="전기사용량 파일 조회 실패", text="파일이 조회되지 않았읍니다.")

	@pyqtSlot(QDate)
	def slot_clicked(self, qDate:QDate):
		date_str = qDate.toString(Qt.DateFormat.ISODate)
		if self._is_file_exist( date_str ):
			self._gen_hover_dlg( obj= self.api_datas_dict[date_str] , date_str=date_str)


	def paintCell(self, painter:QPainter, rect:QRect, date:QDate):
		super().paintCell(painter, rect, date)
		# 좌표 매핑 저장
		self.date_rect_map[date] = QRect(rect)

		is_today = date == QDate.currentDate()
		has_event = date in self.events

		# 오늘 날짜 표시: 배경, 테두리
		if is_today:
			# 배경 칠하기
			painter.fillRect(rect, QColor(255, 220, 220))  # 연한 분홍			
			# 테두리 강조
			pen = QPen(QColor("red"))
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(rect.adjusted(1, 1, -1, -1))			

		if has_event:			
			### 등록표시
			painter.setBrush(Qt.GlobalColor.yellow)
			painter.drawEllipse(rect.topLeft() + QPoint(20, 20), 16, 16)
			painter.setPen ( QColor(0,0,0))
			rect_hi = QRect( rect.topLeft(),QSize(40,40))
			painter.drawText( rect_hi, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, str(self.events[date]) )

			######################
		### text 출력
		painter.setPen(QColor("black"))
		font = QFont()
		font.setWeight(QFont.Weight.Bold if is_today or has_event else QFont.Weight.Normal)
		painter.setFont(font)
		_text = str(date.day()) 
		if is_today:
			_text +=  ' :입력가능' if not has_event else ' :입력완료'
		painter.drawText(rect, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, _text )
		self.setDateTextFormat( date, self.cell_changed if has_event else self.cell_default )


	def _gen_hover_dlg(self, obj:dict, date_str:str):
		txt = ''
		dlgHover = Dlg_Hover(self)
		dlgHover.setWindowTitle ( date_str )
		for key, value in obj.items():
			txt += f" {key} : {value if not 'file' in key else Utils.get_fName_from_url(value)} \n"
		
		dlgHover.dlg_tb.setText ( txt )


# class Wid_Calendar_전기사용량(QWidget):
# 	def __init__(self, parent=None, **kwargs):
# 		super().__init__(parent)
# 		self.calendar = QCalendar_전기사용량(self)
# 		self.setLayout(QVBoxLayout(self))
# 		self.layout().addWidget(self.calendar)

# 	def get_menus(self) -> dict:
# 		return {
# 			'전기사용량 파일 업로드': self.calendar.on_file_upload,
# 			'전기사용량 파일 다운로드': self.calendar.on_file_download,
# 			'전기사용량 파일 삭제': self.calendar.on_file_delete,
# 		}

# 	def setup_ui(self):
# 		self.mani_layout = QVBoxLayout(self)
# 		self.mani_layout.addWidget(self.calendar)
