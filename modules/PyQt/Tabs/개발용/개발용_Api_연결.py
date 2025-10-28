from modules.PyQt.Tabs.plugins.ui.v2.Wid_page_common import Wid_Page_Common
from modules.PyQt.Tabs.plugins.ui.v2.Wid_search_common import Wid_Search_Common
from modules.common_import_v2 import *

from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
from modules.PyQt.compoent_v2.json_editor import QWidget_JsonEditor
class Main_Display(QWidget):
	def __init__(self, parent, **kwargs):
		super().__init__(parent)
		self.UI()

	def UI(self):
		self.setMinimumSize(600, 400)
		self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)

		self.wid_receive = QTextEdit(self)
		self.wid_receive.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		layout.addWidget(self.wid_receive)

		self.wid_send = QWidget_JsonEditor(self)
		self.wid_send.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		layout.addWidget(self.wid_send)

	def set_receive_text(self, text:str):
		self.wid_receive.setText(text)

	def set_send_text(self, text:str):
		self.wid_send.setText(text)

	def get_receive_text(self) -> str:
		return self.wid_receive.toPlainText()

	def get_send_text(self) -> dict:
		try:
			return json.loads(self.wid_send.toPlainText())
		except:
			return {}


class MainWidget(Base_Stacked_Table):
	def create_active_table(self):
		self.main_display = Main_Display(self)
		return self.main_display
	



class Api_연결__for_Tab(  BaseTab_V2 ):

	def _create_container_main(self) -> QWidget:
		self.container_main = MainWidget(self)
		self.main_display = self.container_main.main_display
		self.container_main.setCurrentWidget('active table')
		return self.container_main
	
	def _create_wid_search(self) -> QWidget:
		wid = QWidget(self)
		layout = QHBoxLayout()
		wid.setLayout(layout)
		self.le_url = Custom_Search_LineEdit (parent=wid)
		self.le_url.setPlaceholderText("URL")		
		self.config_le_url()
		layout.addWidget(self.le_url)
	
		self.PB_json = QPushButton("JSON 설정", wid)
		layout.addWidget(self.PB_json)
		

		layout.addStretch()
		self.PB_get = QPushButton("GET", wid)
		layout.addWidget(self.PB_get)

		self.PB_post = QPushButton("POST", wid)
		layout.addWidget(self.PB_post)

		self.PB_delete = QPushButton("DELETE", wid)
		layout.addWidget(self.PB_delete)

		self.contorl_pb_list(False)

		self.le_url.textChanged.connect(lambda : self.contorl_pb_list( bool(len(self.get_url())) ))
		self.PB_json.clicked.connect(self.on_pb_json_clicked)
		self.PB_get.clicked.connect(self.on_pb_get_clicked)
		self.PB_post.clicked.connect(self.on_pb_post_clicked)
		self.PB_delete.clicked.connect(self.on_pb_delete_clicked)

		return wid
	
	def config_le_url(self):        
		self.le_url.set_completer(self.id)
		self.le_url.setFocus()
		self.le_url.setClearButtonEnabled(True)
		self.le_url.returnPressed.connect(self.on_pb_get_clicked)
	
	def _create_wid_pagination(self) -> QWidget:
		"""소요시간 정보로 표시함."""
		wid = QWidget(self)
		layout = QHBoxLayout()
		wid.setLayout(layout)
		lb = QLabel("검색 소요 시간	:", wid)
		layout.addWidget(lb)
		self.lb_search_time = QLabel("0.000", wid)
		self.lb_search_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lb_search_time.setStyleSheet("font-size:12pt;background-color:black;color:white;")
		layout.addWidget(self.lb_search_time)
		layout.addStretch()

		return wid
	
	def on_pb_json_clicked(self):
		pass
	
	def on_pb_get_clicked(self):		
		self.le_url.db_save_search_history()
		self.container_main.setCurrentWidget('active table')
		start_time = time.perf_counter()
		url = self.get_url()
		_isOk, _json = APP.API.getlist(url= url)
		end_time = time.perf_counter()
		self.lb_search_time.setText(self.get_search_time_str(start_time, end_time))
		_str = json.dumps(_json, indent=4, ensure_ascii=False)
		if INFO.IS_DEV:
			print(f"on_pb_get_clicked: {url}")
			print(f"on_pb_get_clicked: {_isOk}")
			print(f"on_pb_get_clicked: {_json}")
		if _isOk:
			self.main_display.set_receive_text(_str)
		else:
			self.main_display.set_receive_text(f"API 호출 실패<br><br> {_str}")

	def get_search_time_str(self, start_time:float, end_time:float) -> str:
		return f"{(end_time - start_time)*1000:.1f} msec"
	
	def on_pb_post_clicked(self):
		send_text = self.main_display.get_send_text()
		url = self.get_url()
		_isOk, _json = APP.API.post(url= url, data=send_text)
		if _isOk:
			self.main_display.set_receive_text(json.dumps(_json, indent=4, ensure_ascii=False))
		else:
			self.main_display.set_receive_text(f"API 호출 실패<br><br> {_json}")
	
	def on_pb_patch_clicked(self):
		send_text = self.main_display.get_send_text()
		id = self.main_display.get_id()
		url = f"{self.get_url()}/{id}".replace("//", "/")
		_isOk, _json = APP.API.patch(url= url, data=send_text)
		if _isOk:
			self.main_display.set_receive_text(json.dumps(_json, indent=4, ensure_ascii=False))
		else:
			self.main_display.set_receive_text(f"API 호출 실패<br><br> {_json}")
	
	def on_pb_delete_clicked(self):
		pass
	
	def get_url(self) -> str:
		return self.le_url.text().strip()

	def contorl_pb_list(self, _enable:bool=False):
		self.PB_json.setEnabled(_enable)
		self.PB_get.setEnabled(_enable)
		self.PB_post.setEnabled(_enable)
		self.PB_delete.setEnabled(_enable)


	

	
