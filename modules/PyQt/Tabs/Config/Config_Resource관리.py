from modules.common_import_v2 import *

from modules.PyQt.Tabs.Config.tables.Wid_table_Config_Resource관리 import Wid_table_Config_Resource관리 as Wid_table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2


class MainWidget(Base_Stacked_Table):

	def create_active_table(self):
		return Wid_table(self)

	
class Resource관리__for_Tab(BaseTab_V2):

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