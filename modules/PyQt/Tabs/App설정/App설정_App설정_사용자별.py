from modules.common_import_v2 import *

from modules.PyQt.Tabs.App설정.tables.Wid_table_App설정_App설정_사용자별 import Wid_table_App설정_App설정_사용자별 as Wid_table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
			
class MainWidget(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_table(self)	
	
class App설정_사용자별__for_Tab(BaseTab_V2):
	def _init_by_child(self):
		pass

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main


	def _create_wid_search(self) -> QWidget:
		""" ✅ Ui_Base_Tab_V2 에서 오버라이드"""
		self.wid_search = QWidget(self)
		h_layout = QHBoxLayout(self.wid_search)
		self.PB_user_select = CustomPushButton( self,'사용자선택')
		self.PB_user_select.setToolTip('사용자 선택')
		self.PB_user_select.setEnabled(True)
		h_layout.addWidget(self.PB_user_select)

		self.lb_selected_user = QLabel(self)
		self.lb_selected_user.setText('사용자선택을 먼저 해야 합니다.')
		self.lb_selected_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lb_selected_user.setStyleSheet("font-weight: bold;color:yellow;background-color:black;")
		h_layout.addWidget(self.lb_selected_user)

		h_layout.addStretch()

		self.PB_refresh = CustomPushButton( self,'새로고침')
		self.PB_refresh.setToolTip('새로고침')
		self.PB_refresh.setEnabled(False)
		h_layout.addWidget(self.PB_refresh)
		
		self.PB_user_select.clicked.connect(self.slot_user_select)
		self.PB_refresh.clicked.connect(self.slot_refresh)
		return self.wid_search

	def slot_user_select(self):

		dlg = Dlg_User_선택_Only_Table_No_Api(parent=self)
		if dlg.exec():
			selected_users = dlg.get_checked_user_ids()
			logger.debug(f"{self.__class__.__name__} : slot_user_select : {selected_users}")
			self.selected_user_id = selected_users[0]
			self.selected_user = INFO.USER_MAP_ID_TO_USER[self.selected_user_id]
			_lb_text = f"선택된 사용자 : {self.selected_user['id']} - {self.selected_user['user_성명']} / {self.selected_user['기본조직1']}"
			self.lb_selected_user.setText(_lb_text)
			self.PB_refresh.setEnabled(True)
			self.param = {'user_id':self.selected_user_id,'page_size':0}
			self.slot_search_for(param=self.param)

	def slot_refresh(self):
		_lb_text = self.lb_selected_user.text()
		if not _lb_text:
			Utils.QMsg_critical( None, title='사용자 선택 오류', text='사용자를 선택해야 합니다.')
			self.PB_refresh.setEnabled(False)
			return
		self.slot_search_for(param=self.param)


