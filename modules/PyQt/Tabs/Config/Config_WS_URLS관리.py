from modules.common_import_v2 import *

from modules.PyQt.Tabs.Config.tables.Wid_table_Config_WS_URLS관리 import Wid_table_Config_WS_URLS관리 as Wid_Table
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget

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
						self.mapping_name_to_widget[name] = None
						raise ValueError(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : instance not created")
				else:
					print(f"{self.__class__.__name__} : create_mapping_name_to_widget : {cls_name} : {cls} not found")
		else:
			self.mapping_name_to_widget['Table'] = Wid_Table(self)
			# self.mapping_name_to_widget['Chart'] = CS_GanttMainWidget(self)
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)

	
class WS_URLS관리__for_Tab(BaseTab_V2):


	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
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