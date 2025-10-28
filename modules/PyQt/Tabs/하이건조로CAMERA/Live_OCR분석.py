from base64 import urlsafe_b64decode
from modules.common_import_v3 import *

from modules.PyQt.Tabs.하이건조로CAMERA.view.liveview import LiveView
from modules.PyQt.compoent_v2.table_v3.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2
from modules.PyQt.Tabs.plugins.BaseTab_V3 import BaseTab_V3

			
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
			self.mapping_name_to_widget['LiveView'] = LiveView(self)
	
class Live_OCR분석__for_Tab(BaseTab_V3):

    def _init_by_child(self):
        pass

    def _create_wid_search(self) -> QWidget:
        """ 필요시 오버라이드"""
        try:
            if hasattr(self, 'lazy_attrs') and self.lazy_attrs.get('is_no_search_create', False):
                return None
            self.wid_search = QWidget(self)
            hlayout = QHBoxLayout(self.wid_search)
            hlayout.addStretch()
            self.pb_refresh = QPushButton("설정 가져오기")
            hlayout.addWidget(self.pb_refresh)
            self.pb_refresh.clicked.connect(
                lambda: self.event_bus.publish ( f"AppID:{self.id}_{GBus.SEARCH_REQUESTED}", {'page_size':0, 'is_active':True}) 
                )
            
            return self.wid_search
        except Exception as e:
            logger.error(f"create_wid_search 오류: {e}")

            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='create_wid_search 오류', text=f"{e}<br>{trace}")
            return None


    def _create_container_main(self) -> QWidget:
        container_main = QWidget()
        v_layout = QVBoxLayout(container_main)
        self._create_select_main_widget()
        if self.wid_select_main:
            v_layout.addWidget(self.wid_select_main)

        self.mainWidget = MainWidget(self)
        v_layout.addWidget(self.mainWidget)
        return container_main

    def simulate_search_pb_click(self):
        """ search pb 클릭 시 호출되는 함수 : self.ui.wid_search.ui.PB_Search.click() """
        try:
            self.pb_refresh.click()
        except Exception as e:
            logger.error(f"simulate_search_pb_click: {e}")

    def slot_fetch_finished(self, msg):
        is_ok, pagination, api_datas = super().slot_fetch_finished(msg)
        if self.api_datas:
            wid_LiveView : LiveView = self.mainWidget.mapping_name_to_widget['LiveView']
            wid_LiveView.load_plot_data(self.api_datas)
            
        else:
            Utils.generate_QMsg_critical(self, title="API 조회 자료가 없읍니다.", text="API 조회 자료가 없읍니다.")

        return is_ok, pagination, api_datas

    def run(self):
        super().run()
        self.check_ws()

    def check_ws(self):
        if not getattr(self, 'ws_url', None):
            self.ws_url_name = self.lazy_attrs.get('ws_url_name', None)
            if not self.ws_url_name:
                raise ValueError(f"ws_url_name 이 없습니다. {self.ws_url_name}")
            self.set_ws_url(self.ws_url_name)

        if not self.ws_url:
            raise ValueError(f"ws_url 이 없습니다. {self.ws_url}")
        
        if self.ws_url not in INFO.WS_TASKS:
            ws_manager = APP.get_WS_manager()
            connect_msg = self.kwargs.get('ws_handler_kwargs', {}).get('connect_msg', {})
            ws_manager.add(self.ws_url, connect_msg=connect_msg)
        self.subscribe_gbus_for_ws()

    def subscribe_gbus_for_ws(self):
        if not self.ws_url:
            logger.error(f"ws_url 이 없습니다. {self.ws_url}")
            return
        self.event_bus.subscribe( self.ws_url, self.on_ws_data_changed)

    def unsubscribe_gbus(self):
        try:    
            super().unsubscribe_gbus()
            self.event_bus.unsubscribe( self.ws_url, self.on_ws_data_changed)
        except Exception as e:
            logger.error(f"Error unsubscribing from gbus: {e}")

    def on_ws_data_changed(self, data: dict):
 
        if not isinstance(data, dict) or not data.get('message', {}):
            logger.error(f"on_ws_data_changed: {data} is not dict")
            return
        wid_LiveView : LiveView = self.mainWidget.mapping_name_to_widget['LiveView']
        # wid_LiveView.set_data(copy.deepcopy(data))
        wid_LiveView.set_data_via_base64(copy.deepcopy(data))





    def check_ws_handler(self):
        #### 검증 처리
        if not self.ws_url:
            self.set_ws_url(self.ws_url_name)

        if not self.ws_url:
            logger.error(f"ws_url 이 없습니다. {self.ws_url}")
            return
        
        if self.ws_handler is None and not isinstance(self.ws_handler_cls, type):
            logger.error(f"ws_handler_cls 가 없거나 올바르지 않습니다. {self.ws_handler_cls}")
            return
        
        #### 처리  : 만약 handler가 없으면 생성
        if self.ws_url not in INFO.WS_TASKS:
            self.ws_handler = self.ws_handler_cls(self.ws_url, **self.kwargs.get('ws_handler_kwargs', {}))
            INFO.WS_TASKS[self.ws_url] = self.ws_handler


    def set_ws_url(self, ws_url_name:str=None):
        self.ws_url_name = ws_url_name or self.ws_url_name
        self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)
