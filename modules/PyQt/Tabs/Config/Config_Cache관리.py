from modules.common_import_v2 import *

from modules.PyQt.Tabs.Config.tables.Wid_table_Config_Cache관리 import Wid_table_Config_Cache관리 as Wid_table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
			
class MainWidget(Base_Stacked_Table):
	def create_active_table(self):
		return Wid_table(self)	


class Cache관리__for_Tab(BaseTab_V2):
	def _init_by_child(self):
		pass

	def _create_container_main(self) -> QWidget:
		container_main = MainWidget(self)
		return container_main
	
	def _create_wid_search(self) -> QWidget:
		""" ✅ Ui_Base_Tab_V2 에서 오버라이드"""
		return None
	
	def _create_wid_pagination(self) -> QWidget:
		""" ✅ Ui_Base_Tab_V2 에서 오버라이드"""
		return None


	def simulate_search_pb_click(self):
		""" wid_search 에서 검색버튼 이나, 현재는 제외하였으므로, on_refresh 호출 """
		self.on_refresh()

	def on_clear_all(self):
		""" cache clear 처리 """
		_text = f"""
			⚠️ 서버 캐시를 삭제하시겠습니까?<br><br>
			이 작업은 <b>현재 서버에서 사용 중인 모든 캐시</b>를 삭제합니다.<br>
			일부 설정 또는 데이터가 초기화되어 <b>일시적으로 느려질 수 있습니다</b>.<br><br>
			계속하시겠습니까?
			"""
		if Utils.QMsg_question( self, title='Server cache clear', text=_text):
			action_url = 'clear_all'
			_isok = APP.API.delete( url= f"{self.url}{action_url}")
			if _isok:
				Utils.QMsg_Info( self, title='Server cache clear 성공', text='캐시가 삭제되었습니다.' , autoClose=1000)
				self.on_refresh()
			else:
				Utils.QMsg_Critical( self, title='Server cache clear', text=f'캐시 삭제 실패')


	def on_refresh(self):
		self.slot_search_for(param={})