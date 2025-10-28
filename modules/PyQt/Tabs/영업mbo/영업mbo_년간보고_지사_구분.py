from __future__ import annotations
from modules.common_import_v2 import *

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

from modules.PyQt.Tabs.영업mbo.tables.Wid_table_영업mbo_년간보고 import Wid_table_영업mbo_년간보고 as Wid_Table
from modules.PyQt.Tabs.영업mbo.graph.wid_chart_지사_구분 import Wid_Chart_지사_구분 as Chart


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
			self.mapping_name_to_widget['Chart'] = Chart(self)
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)

from modules.PyQt.Tabs.영업mbo.mixin_년간보고 import YearSearchMixin
class 년간보고_지사_구분__for_Tab(BaseTab_V2, YearSearchMixin):
	
	def _create_wid_search(self) -> QWidget:
		""" override 함 : self._create_wid_pagination(self) 는 lazy_attr 속성 'is_no_pagination_create' 가 True 에 의해 생성안됨 """
		return self.mixin_create_year_search()


	# def _create_wid_search(self) :
	# 	return None
	
	# def _create_wid_pagination(self):
	# 	return None

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)


		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main

	def run(self):
		"""필수 실행 루틴"""
		if INFO.IS_DEV:
			logger.info(f"{self.__class__.__name__} : run")
			logger.info(f"self.table_name: {self.table_name if hasattr(self, 'table_name') else 'table_name not set'}")
			logger.info(f"self.url: {self.url if hasattr(self, 'url') else 'url not set'}")
		self.subscribe_gbus()
		if hasattr(self, 'is_auto_api_query') and self.is_auto_api_query:
			QTimer.singleShot( 0, lambda: self.pb_query.click() )
