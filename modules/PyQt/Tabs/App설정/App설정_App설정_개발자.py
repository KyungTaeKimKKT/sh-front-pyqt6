from modules.common_import_v2 import *

from modules.PyQt.Tabs.App설정.tables.Wid_table_App설정_App설정_개발자 import Wid_table_App설정_App설정_개발자 as Wid_Table
from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

class SnapshotRestoreDialog(QDialog):
	def __init__(self, parent=None, url:str=None):
		super().__init__(parent )
		self.url = url
		self.setWindowTitle("권한 스냅샷 복원")
		self.resize(400, 300)
		self.init_ui()

		_isok, _json = APP.API.getlist(f"{self.url}?page_size=0".replace('//', '/'))
		if _isok:
			self.load_snapshots(_json)
		else:
			Utils.generate_QMsg_critical(None, title='사용자 스냅샷', text='사용자 스냅샷 실패')
			self.reject()
			

	def init_ui(self):
		layout = QVBoxLayout(self)

		self.label = QLabel("복원할 스냅샷을 선택하세요:")
		layout.addWidget(self.label)

		self.list_widget = QListWidget()
		layout.addWidget(self.list_widget)

		# 버튼 레이아웃
		btn_layout = QHBoxLayout()
		self.btn_restore = QPushButton("복원")
		self.btn_delete = QPushButton("삭제")
		self.btn_cancel = QPushButton("취소")
		btn_layout.addWidget(self.btn_restore)
		btn_layout.addWidget(self.btn_delete)
		btn_layout.addWidget(self.btn_cancel)

		layout.addLayout(btn_layout)

		# 이벤트 연결
		self.btn_restore.clicked.connect(self.restore_snapshot)
		self.btn_delete.clicked.connect(self.delete_snapshot)
		self.btn_cancel.clicked.connect(self.reject)

	def load_snapshots(self, _json:list[dict]):
		self.snapshots = _json
		for snap in self.snapshots:
			ts: str = snap['timestamp']
			try:
				dt = datetime.fromisoformat(ts)  # 깔끔하고 안전한 방식
			except ValueError:
				dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f')  # fallback
			text = f"ID: {snap['id']} | {dt.isoformat()}"
			item = QListWidgetItem(text)
			item.setData(Qt.ItemDataRole.UserRole, snap['id'])
			self.list_widget.addItem(item)

	def restore_snapshot(self):
		selected_items = self.list_widget.selectedItems()
		if not selected_items:
			QMessageBox.warning(self, "경고", "스냅샷을 선택해주세요.")
			return

		snapshot_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

		try:
			url = f"{self.url}/{snapshot_id}/restore/".replace('//', '/')
			_isok, _json = APP.API.getlist(url)
			if _isok:
				Utils.generate_QMsg_Information(None, title='사용자 스냅샷', text='사용자 스냅샷 Restore 완료', autoClose=1000)
				self.accept()
			else:
				Utils.generate_QMsg_critical(None, title='사용자 스냅샷', text='사용자 스냅샷 실패')
		except Exception as e:
			Utils.generate_QMsg_critical(None, title='사용자 스냅샷', text=f'사용자 스냅샷 실패: {e}')

	def delete_snapshot(self):
		selected_items = self.list_widget.selectedItems()
		if not selected_items:
			QMessageBox.warning(self, "경고", "스냅샷을 선택해주세요.")
			return
		snapshot_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
		url = f"{self.url}/{snapshot_id}".replace('//', '/')
		_isok = APP.API.delete(url)
		if _isok:
			Utils.generate_QMsg_Information(None, title='사용자 스냅샷', text='사용자 스냅샷 삭제 완료', autoClose=1000)
			self.reject()
		else:
			Utils.generate_QMsg_critical(None, title='사용자 스냅샷', text='사용자 스냅샷 삭제 실패')

			
class MainWidget(Base_MainWidget):	
	def update_mapping_name_to_widget(self):
		if self.lazy_config_mode:
			for name, cls_name in self.lazy_config.get('mapping_name_to_widget', {}).items():
				cls = globals().get(cls_name, None)
				if cls :
					kwargs = self.lazy_config.get('kwargs', {}).get(name, {})
					instance = cls( self, **kwargs)
					if instance:
						self.mapping_name_to_widget[name] = instance
					else:
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = Wid_Table(self)
	
class App설정_개발자__for_Tab(BaseTab_V2):

	def _init_by_child(self):
		pass

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main

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
			url = f"{self.url}/{action_url}".replace('//', '/')
			is_ok, _json = APP.API.getlist(url=url)
			if is_ok:
				Utils.generate_QMsg_Information(None, title='모든 사용자에게 전송', text='모든 사용자에게 설정을 즉시 전송 요청 완료 하였읍니다..<br>', autoClose=1000)
			else:
				Utils.generate_QMsg_critical(None, title='모든 사용자에게 전송', text='모든 사용자에게 설정을 즉시 전송 요청 실패')
		except Exception as e:
			logger.error(f"on_fileview 오류: {e}")
			logger.error(f"{traceback.format_exc()}")
			trace = traceback.format_exc().replace('\n', '<br>')
			_text = f"on_WS_Trigger 오류: {e}<br> {trace}<br> {json.dumps( _json, ensure_ascii=False )}"
			Utils.generate_QMsg_critical(None, title='모든 사용자에게 전송', text=_text)

	def on_user_snapshot(self):
		url =f"{self.url}/snapshot-app-users/".replace('//', '/')
		is_ok, _json = APP.API.getlist(url)
		if is_ok:
			Utils.generate_QMsg_Information(None, 
								   title='사용자 스냅샷', 
								   text=f'사용자 스냅샷 완료<br> {json.dumps(_json, indent=4)} <br>', 
								   autoClose=1000)
		else:
			Utils.generate_QMsg_critical(None, title='사용자 스냅샷', text='사용자 스냅샷 실패')


	def on_restore_user_snapshot(self):
		url = f"api/users/app권한-사용자-m2m-snapshot/"
		dlg = SnapshotRestoreDialog(self, url= url)
		if dlg.exec():
			Utils.generate_QMsg_Information(None, title='재조회', text='재조회 실시합니다.', autoClose=1000)
			self.simulate_search_pb_click()



