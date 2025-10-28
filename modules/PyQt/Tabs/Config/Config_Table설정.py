from modules.common_import_v2 import *

from modules.PyQt.Tabs.Config.tables.Wid_table_Config_Table import Wid_table_Config_Table as Wid_table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

class Dialog_Table_선택(QDialog):
	""" kwargs:
		title: str = '테이블 선택'
		search_placeholder: str = '테이블 이름 검색...'
		list_name_key: str = 'table_name'
		base_auto_fetch: bool = True : 상속받는 부모의 auto_fetch 여부
	"""
	def __init__(self, parent:QWidget, url:str, **kwargs):
		super().__init__(parent)
		self.kwargs = kwargs
		self.url = url or 'config/table_only_name/?page_size=0'
		self.table_list:list[dict] = []
		self.filtered_table_list:list[dict] = []
		self.is_init_ui = False

		if self.kwargs.get('base_auto_fetch', True):
			self.init_ui()               # UI 먼저 초기화 (search_input 등 생성)
			self.fetch_table_list()      # 그 후 데이터 불러오기 및 필터 갱신

			if not self.table_list:
				self.close()

	def fetch_table_list(self):
		is_ok, _json = APP.API.getlist(url=self.url)
		if is_ok:
			self.table_list = _json
			self.filtered_table_list = self.table_list.copy()
			if self.is_init_ui:
				self.update_filter(self.search_input.text())  # 🔹 검색어 유지하면서 갱신
		else:
			Utils.generate_QMsg_critical(None, title=f'{self.kwargs.get("title", "테이블 선택")} 실패', text=f'{self.kwargs.get("title", "테이블 선택")} 실패: <br>{_json}')

	def init_ui(self):
		self.setWindowTitle(f'{self.kwargs.get("title", "테이블 선택")}')
		self.setMinimumSize(400, 300)
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setModal(True)

		layout = QVBoxLayout(self)
		#### refresh button 추가
		self.pb_refresh = CustomPushButton(self, 'Refresh')
		self.pb_refresh.clicked.connect(self.fetch_table_list)
		layout.addWidget(self.pb_refresh)

		# 검색창
		self.search_input = Custom_LineEdit(self)
		self.search_input.setPlaceholderText(f"{self.kwargs.get('search_placeholder', '테이블 이름 검색...')}")
		self.search_input.textChanged.connect(self.update_filter)
		layout.addWidget(self.search_input)

		# 리스트
		self.list_widget = QListWidget(self)
		self.populate_list()
		layout.addWidget(self.list_widget)

		# 버튼
		btn_layout = QHBoxLayout()
		self.btn_ok = QPushButton("확인")
		self.btn_cancel = QPushButton("취소")
		self.btn_ok.clicked.connect(self.accept_selection)
		self.btn_cancel.clicked.connect(self.reject)

		btn_layout.addStretch()
		btn_layout.addWidget(self.btn_ok)
		btn_layout.addWidget(self.btn_cancel)
		layout.addLayout(btn_layout)

		self.is_init_ui = True

	def populate_list(self):
		self.list_widget.clear()
		for item in self.filtered_table_list:
			self.list_widget.addItem(item[ self.kwargs.get('list_name_key', 'table_name') ])

	def update_filter(self, text: str):
		keyword = text.strip().lower()
		self.filtered_table_list = [
			item for item in self.table_list if keyword in item[self.kwargs.get('list_name_key', 'table_name')].replace('appID', '').lower()
		]
		self.populate_list()

	def accept_selection(self):
		current_row = self.list_widget.currentRow()
		if current_row >= 0:
			self.selected_table = self.filtered_table_list[current_row]
			self.accept()
		else:
			QMessageBox.warning(self, "선택 오류", "테이블을 선택하세요.")

	def get_selected_table(self) -> dict:
		return self.selected_table

	def get_selected_name(self) -> str:
		return self.selected_table
	

class MainWidget(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_table(self)

class Table설정__for_Tab(BaseTab_V2):

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main


	def on_select_table(self):
		dlg = Dialog_Table_선택(self, url='config/table_only_name/?page_size=0')
		if dlg.exec():
			selected_table = dlg.get_selected_table()
			if selected_table:
				table_name = selected_table['table_name']
				self.param = {'table_name': table_name, 'page_size': 0}
				self.slot_search_for(param=self.param)

	def on_delete_table(self):		
		pass


	def on_WS_Trigger(self):        
		try:
			if not Utils.QMsg_question(
				None,
				title='모든 사용자에게 전송',
				text=(
					'<span style="font-size:12pt;">'
					'<b style="color:#007ACC;">모든 사용자에게 설정 전송</b>을 요청합니다.<br><br>'
					'⚠️ <span style="color:#D35400;"><b>이 작업은 다소 시간이 소요될 수 있습니다.</b></span><br><br>'
					'<span style="color:#2C3E50;">정말로 <b>전송 요청</b>하시겠습니까?</span>'
					'</span>'
				)
			):
				return
			action_url = 'request_ws_redis_publish'
			url = f"{self.url}/{action_url}?table_name={self.table_name}".replace('//', '/')
			is_ok, _json = APP.API.getlist(url=url)
			if is_ok:
				Utils.generate_QMsg_Information(None, title='모든 사용자에게 전송', text='모든 사용자에게 설정을 즉시 전송 요청 완료 하였읍니다..<br>', autoClose=1000)
			else:
				Utils.generate_QMsg_critical(None, title='모든 사용자에게 전송', text='모든 사용자에게 설정을 즉시 전송 요청 실패<br> {json.dumps(_json, ensure_ascii=False)}')
		except Exception as e:
			logger.error(f"on_fileview 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			trace = traceback.format_exc().replace('\n', '<br>')
			_text = f"on_WS_Trigger 오류: {e}<br> {trace}<br> {json.dumps( _json, ensure_ascii=False )}"
			Utils.generate_QMsg_critical(None, title='모든 사용자에게 전송', text=_text)

