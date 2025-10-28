from modules.common_import_v2 import *

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2


class QCalendar_휴일( LazyParentAttrMixin_V2, QCalendarWidget):

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

		self.setGridVisible(True)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.cell_default = QTextCharFormat()
		self.cell_default.setBackground( QColor("white"))

		self.cell_changed = QTextCharFormat()
		self.cell_changed.setBackground( QColor("yellow"))


		self.clicked.connect(self.slot_clicked)
		self.currentPageChanged.connect(self.slot_current_page_changed )

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
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_api_datas_changed)

	def on_api_datas_changed(self, api_datas:list[dict]):
		if not api_datas:
			self.api_datas = None
			return
		self.api_datas = copy.deepcopy(api_datas)
		self.api_datas_dict = { obj.get('휴일'): obj for obj in self.api_datas }
		# 조회된 월 기록
		# for obj in self.api_datas:
		# 	d = obj.get("휴일")  # 'YYYY-MM-DD'
		# 	if d:
		# 		y, m = d.split("-")[0:2]
		# 		ym_key = f"{y}-{m}"
		# 		self.api_datas_month_dict[ym_key] = True

		self._update_data()

	def contextMenuEvent(self, event):
		return 
	

	def _update_data(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
		self.events = self._get_event_dates()
		self.updateCells()

	def _delete_event(self, date_str:str):
		try:
			qdate = QDate.fromString(date_str, Qt.DateFormat.ISODate)
			if qdate in self.events:
				self.events.pop(qdate)
				self.updateCell(qdate)
			else:
				raise ValueError(f"{self.__class__.__name__} : _delete_event : {qdate} not found")
		except Exception as e:
			logger.error(f"{self.__class__.__name__} : _delete_event : {e}")
			logger.error(f"{self.__class__.__name__} : _delete_event : {traceback.format_exc()}")
			raise ValueError(f"{self.__class__.__name__} : _delete_event : {e}")

	def _add_event(self, date_str:str, obj:dict):
		try:
			qdate = QDate.fromString(date_str, Qt.DateFormat.ISODate)
			if qdate not in self.events:
				self.events[qdate] = obj.get('id', -1)
				self.updateCell(qdate)
			else:
				raise ValueError(f"{self.__class__.__name__} : _add_event : {qdate} already exists")
		except Exception as e:
			logger.error(f"{self.__class__.__name__} : _add_event : {e}")
			logger.error(f"{self.__class__.__name__} : _add_event : {traceback.format_exc()}")
			raise ValueError(f"{self.__class__.__name__} : _add_event : {e}")
		

	def _get_event_dates(self) -> dict[QDate, int]:
		events = {}
		for obj in self.api_datas:
			date_str = obj.get('휴일')
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
		return
	    #### 25-7-22 추가 : 월 변경시 조회 처리 =>
		#### drf 에서 cache 형태로 전체를 받기 때문에 더이상 재조회 안함.
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
				combined = {obj['휴일']: obj for obj in self.api_datas} if self.api_datas else {}
				for obj in _json:
					combined[obj['휴일']] = obj

				self.api_datas = list(combined.values())
				self.api_datas_dict = {obj['휴일']: obj for obj in self.api_datas}
				self.api_datas_month_dict[ym_key] = True  # 조회 완료 처리
				self._update_data()
			else:
				Utils.generate_QMsg_critical(self, title="휴일 조회 실패", text="휴일이 조회되지 않았읍니다.")
		except Exception as e:
			logger.error(f"{self.__class__.__name__} : slot_current_page_changed : {e}")
			logger.error(f"{self.__class__.__name__} : slot_current_page_changed : {traceback.format_exc()}")
			Utils.generate_QMsg_critical(self, title="휴일 조회 실패", text="휴일이 조회되지 않았읍니다.")


	@pyqtSlot(QDate)
	def slot_clicked(self, qDate:QDate):
		# self._gen_hover_dlg()
		휴일_str = qDate.toString( Qt.DateFormat.ISODate )
		if qDate < QDate.currentDate():
			Utils.generate_QMsg_critical(self, title="휴일 변경 오류", text="오늘 이전 날짜는 휴일 변경 처리 불가")
			return

		if 휴일_str in self.api_datas_dict:
			index = self.api_datas.index(self.api_datas_dict[휴일_str])
			is_ok = APP.API.delete( self.url+f"{self.api_datas_dict[휴일_str]['id']}" )
			if is_ok:
				self.api_datas.pop(index)
				self.api_datas_dict.pop(휴일_str)
				self._delete_event( 휴일_str)
			else:
				Utils.generate_QMsg_critical(self, title="휴일 삭제 실패", text=f"휴일이 삭제되지 않았읍니다")
		else:
			is_ok, _json = APP.API.post( self.url,  { "휴일":휴일_str } )
			if is_ok:
				self.api_datas.append(_json)
				self.api_datas_dict[휴일_str] = _json
				self._add_event( 휴일_str, _json)
			else:
				Utils.generate_QMsg_critical(self, title="휴일 등록 실패", text=f"휴일이 등록되지 않았읍니다.<br> {json.dumps(_json, ensure_ascii=False)}")



	def paintCell(self, painter:QPainter, rect:QRect, date:QDate):
		super().paintCell(painter, rect, date)

		has_event = date in self.events.keys()
		if has_event:		
		
			# 테두리 강조
			pen = QPen(QColor("red"))
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(rect.adjusted(1, 1, -1, -1))	

			### 등록표시
			painter.setBrush(Qt.GlobalColor.yellow)
			painter.drawEllipse(rect.topLeft() + QPoint(20, 20), 16, 16)
			painter.setPen ( QColor(0,0,0))
			rect_hi = QRect( rect.topLeft(),QSize(40,40))


			painter.drawText( rect_hi, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, "휴일") 


		### text 출력
		painter.setPen(QColor("black"))
		font = QFont()
		font.setWeight(QFont.Weight.Bold if has_event else QFont.Weight.Normal)
		painter.setFont(font)
		_text = str(date.day()) 
		painter.drawText(rect, Qt.TextFlag.TextSingleLine|Qt.AlignmentFlag.AlignCenter, _text )
		self.setDateTextFormat( date, self.cell_changed if has_event else self.cell_default )

