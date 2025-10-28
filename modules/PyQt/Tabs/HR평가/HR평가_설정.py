from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from datetime import date, datetime, timedelta
import copy

### 😀😀 user : ui...
from modules.PyQt.Tabs.plugins.ui.Ui_tab_common_v2 import Ui_Tab_Common 
from modules.PyQt.Tabs.plugins.BaseTab import BaseTab
from modules.PyQt.compoent_v2.table.stacked_table import Base_Stacked_Table

from modules.PyQt.Tabs.HR평가.tables.Wid_table_HR평가_설정 import Wid_table_HR평가_설정 as Wid_table


import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

DEFAULT_VIEW = '테이블'

URL_평가설정_COPY_CREATE = '평가설정_copy_create'

class 설정__for_stacked_Table( Base_Stacked_Table ):
	default_view_name = DEFAULT_VIEW
	
	def create_active_table(self ):
		return Wid_table(self)


from modules.PyQt.compoent_v2.base_form_dialog import Base_Form_Dialog
class Form_차수별_점유(Base_Form_Dialog):
    minium_size = (300, 200)



class Form_차수별_유형(Base_Form_Dialog):
    minium_size = (300, 200)

def get_no_edit_columns_by_coding() -> list[str]:
	base_columns = ['id','평가참여자', '등록일','등록자_fk',]
	if INFO.USERID != 1:
		return base_columns +['is_시작', 'is_종료']
	return base_columns

class 설정__for_Tab( BaseTab ):
	no_edit_columns_by_coding = get_no_edit_columns_by_coding()

	edit_mode = 'row' ### 'row' | 'cell' | 'None'

	custom_editor_info = {
		'차수별_점유': Form_차수별_점유,
		'차수별_유형': Form_차수별_유형
	}
	is_no_config_initial = True		### table config 없음
	
	default_view_name = DEFAULT_VIEW

	def create_ui(self):
		start_time = time.perf_counter()
		self.ui = Ui_Tab_Common()
		self.ui.setupUi(self)

		self.stacked_table = 설정__for_stacked_Table(self)
		self.ui.v_table.addWidget(self.stacked_table)

		self.custom_ui()
		self.event_bus.publish_trace_time(
					{ 'action': f"AppID:{self.id}_create_ui", 
				'duration': time.perf_counter() - start_time })
		


	def custom_ui(self):
		self.PB_평가_신규생성 = QPushButton()
		self.PB_평가_신규생성.setText('평가 신규생성')
		self.PB_평가_신규생성.clicked.connect(self.on_new_evaluation)
		self.ui.h_search.addWidget(self.PB_평가_신규생성)

		self.PB_평가_copy_create = QPushButton()
		self.PB_평가_copy_create.setText('평가 복사 생성')
		self.PB_평가_copy_create.clicked.connect(self.on_copy_create_evaluation)
		self.PB_평가_copy_create.setDisabled(True)
		self.ui.h_search.addWidget(self.PB_평가_copy_create)
		#### 평가체계 구성
		self.PB_평가체계 = QPushButton()
		self.PB_평가체계.setText('평가체계 구성')
		self.PB_평가체계.clicked.connect(self.on_config_evaluation_system)
		self.PB_평가체계.setDisabled(True)
		self.ui.h_search.addWidget(self.PB_평가체계)
		#### 역량평가 구성
		self.PB_역량평가 = QPushButton()
		self.PB_역량평가.setText('역량평가 구성')
		self.PB_역량평가.clicked.connect(self.on_config_ability_evaluation)
		self.PB_역량평가.setDisabled(True)
		self.ui.h_search.addWidget(self.PB_역량평가)

		#### 평가 시작_종료 button : tooggle 개념
		self.PB_평가_시작_종료	 = QPushButton()
		self.PB_평가_시작_종료.setText('평가 시작')
		self.PB_평가_시작_종료.clicked.connect(self.on_start_end_evaluation)
		self.PB_평가_시작_종료.setDisabled(True)
		self.ui.h_search.addWidget(self.PB_평가_시작_종료)

	def get_txt_start_dialog(self, dataObj:dict) -> str:
		import json
		_txt = '평가를 시작하시겠습니까?<br>'
		for attr, value in dataObj.items():
			if attr in ['id', '평가참여자', '총평가차수', '점유_역량', '점유_성과', '점유_특별', '차수별_점유', '차수별_유형',]:
				value = f"{value}" if not isinstance(value, dict) else json.dumps(value, ensure_ascii=False)
				_txt += f"{attr} : {value}<br>"
		return _txt

	def on_start_end_evaluation(self):
		_pb_text = self.PB_평가_시작_종료.text()
		if _pb_text == '평가 시작' and hasattr(self, 'selected_rows') and self.selected_rows:
			dataObj = self.selected_rows[0]
			if dataObj['is_시작'] == False and dataObj['is_종료'] == False:

				dlg_button = QMessageBox.question(self, '평가 시작', self.get_txt_start_dialog(dataObj))
				if dlg_button == QMessageBox.StandardButton.Yes:
					is_ok, _json = APP.API.Send(url=self.url, dataObj=dataObj, sendData={'is_시작':True})
					if is_ok:
						Utils.generate_QMsg_Information(self, title='평가 시작', text='평가를 시작하였습니다.')
						self.PB_평가_시작_종료.setText('평가 종료')
			else:
				Utils.generate_QMsg_critical(self, title='평가 시작', text='평가가 이미 시작되었습니다.')

		elif _pb_text == '평가 종료' and hasattr(self, 'selected_rows') and self.selected_rows:
			dataObj = self.selected_rows[0]
			if dataObj['is_시작'] == True and dataObj['is_종료'] == False:
				dlg_button = QMessageBox.question(self, '평가 종료', '평가를 종료하시겠습니까?')
				if dlg_button == QMessageBox.StandardButton.Yes:
					is_ok, _json = APP.API.Send(url=self.url, dataObj=dataObj, sendData={'is_종료':True})
					if is_ok:
						Utils.generate_QMsg_Information(self, title='평가 종료', text='평가를 종료하였습니다.')
						self.PB_평가_시작_종료.setText('평가 종료됨')
					else:
						Utils.generate_QMsg_critical(self, title='평가 종료', text='확인 후 다시 종료바랍니다.' )
			else:
				Utils.generate_QMsg_critical(self, title='평가 종료', text='평가가 이미 종료되었습니다.')
		else : 
			Utils.generate_QMsg_critical(self, title='평가 종료', text='평가를 선택해주세요.')


	def on_new_evaluation(self):

		try:
			_question_text = f"""
			신규생성을 하시겠읍니까?
			각 설정을 모두 설정하여야 합니다.			
			"""
			dlg_button = Utils.generate_QMsg_question(self, title='평가 신규생성', text=_question_text, autoClose=1000)
			if dlg_button != QMessageBox.StandardButton.Ok:
				return
			
			sendData = {
				'id': -1,
				'제목': '신규생성',
				'is_시작': False,
				'is_종료': False,
				'시작': datetime.today().strftime('%Y-%m-%d'),
				'종료': (datetime.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
				'등록일': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				'등록자_fk': INFO.USERID,
			}
			is_ok, _json = APP.API.Send(url=self.url, dataObj={'id':-1}, sendData=sendData)
			if is_ok:
				self.api_datas.insert(0, _json)
				self.event_bus.publish(f"{self.table_name}:datas_changed", self.api_datas)
				Utils.generate_QMsg_Information(self, title='평가 신규생성', text='정상적으로 생성되었읍니다.', autoClose=1000)
			else:
				Utils.generate_QMsg_critical(self, title='평가 신규생성', text='확인 후 다시 생성바랍니다.' )
		except Exception as e:
			Utils.generate_QMsg_critical(self, title='평가 신규생성', text='확인 후 다시 생성바랍니다.' )
			logger.error(f"평가 신규생성 실패 : {e}")


	def on_copy_create_evaluation(self):
		if hasattr(self, 'selected_rows') and self.selected_rows:
			selected_row = self.selected_rows[0]
			selected_id = selected_row['id']
			logger.debug(f"selected_id : {selected_id}")
			### 평가 복사 생성
			_question_text = """
				<b>복사 생성을 하시겠습니까?</b><br><br>
				선택된 평가 설정을 그대로 사용합니다.<br>
				<span style="color:#d9534f;"><b>⚠ 주의:</b></span> <u>참여자 선택</u>을 꼭 확인하시기 바랍니다.
			"""
			dlg_button = Utils.generate_QMsg_question(self, title='평가 복사 생성', text=_question_text)
			if dlg_button != QMessageBox.StandardButton.Ok:
				print ('if 진입')
				return
			else:
				print ('else 진입')
			
			try:		
				if hasattr(self, 'url') and self.url:
					url = f"{self.url}/{str(selected_id)}/{URL_평가설정_COPY_CREATE}/".replace('//', '/')
					is_ok, _json = APP.API.getlist(url)
					if is_ok:
						logger.debug(f"평가 복사 생성 성공 : {_json}")
						self.api_datas.insert(0, _json)
						self.event_bus.publish(f"{self.table_name}:datas_changed", self.api_datas)
						Utils.generate_QMsg_Information(self, title='평가 복사 생성', text='정상적으로 생성되었읍니다.', autoClose=1000)
					else:
						Utils.generate_QMsg_critical(self, title='평가 복사 생성', text='확인 후 다시 생성바랍니다.' )
				else:
					raise ValueError('url 없음')
			except Exception as e:
				Utils.generate_QMsg_critical(self, title='평가 복사 생성', text='확인 후 다시 생성바랍니다.' )
				logger.error(f"평가 복사 생성 실패 : {e}")
		else:
			Utils.generate_QMsg_critical(self, title='평가 복사 생성', text='확인 후 다시 생성바랍니다.' )
			logger.error(f"평가 복사 생성 실패 : selected_rows 없음")


	def on_config_ability_evaluation(self):
		from modules.PyQt.Tabs.HR평가.dialog.dlg_역량평가관리 import Dialog_역량평가관리
		if hasattr(self, 'selected_rows') and self.selected_rows:
			selected_row = self.selected_rows[0]
			dlg = Dialog_역량평가관리(self, 평가설정=selected_row )
			dlg.exec()
		else:
			Utils.generate_QMsg_critical(self, title='역량평가 구성', text='확인 후 다시 생성바랍니다.' )


	def on_config_evaluation_system(self):
		if not (hasattr(self, 'selected_rows') and self.selected_rows):
			Utils.generate_QMsg_critical(self, title='평가체계 구성', text='확인 후 다시 생성바랍니다.' )
			return
		try:

			selected_row = self.selected_rows[0]
			selected_id = selected_row['id']
			logger.debug(f"selected_id : {selected_id}")
			### 평가체계 api 호출
			url = f"{INFO.URL_HR평가_평가체계DB}/?평가설정_fk={str(selected_id)}&page_size=0".replace('//', '/')
			is_ok, _json = APP.API.getlist(url)
			if is_ok:
				from modules.PyQt.Tabs.HR평가.tables.Wid_table_HR평가_평가체계도 import Dialog_평가체계도
				dlg = Dialog_평가체계도(self, past_data = _json, 평가설정_fk=selected_id)
				dlg.exec()
				logger.debug(f"평가체계 구성 성공 : {_json}")
				# dlg = QDialog(self)
				# dlg.setMinimumSize(1000, 800)
				# dlg.setWindowTitle('평가체계 구성')
				# v_layout = QVBoxLayout()
				# from modules.PyQt.Tabs.HR평가.tables.Wid_table_HR평가_평가체계도 import Wid_table_HR평가_평가체계도
				# wid_table = Wid_table_HR평가_평가체계도(self,
				# 				past_data =_json )
				# v_layout.addWidget(wid_table)
				# dlg.setLayout(v_layout)
				# dlg.exec()
			else:
				Utils.generate_QMsg_critical(self, title='평가체계 구성', text='확인 후 다시 생성바랍니다.' )
	
		except Exception as e:
			logger.error(f"평가체계 구성 실패 : {e}")
			Utils.generate_QMsg_critical(self, title='평가체계 구성', text='확인 후 다시 생성바랍니다.' )
			return


	


	def subscribe_gbus(self):
		super().subscribe_gbus()
		self.event_bus.subscribe(f"{self.table_name}:datas_changed", self.on_datas_changed)
		self.event_bus.subscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)


	def unsubscribe_gbus(self):
		self.event_bus.unsubscribe(f"{self.table_name}:selected_rows", self.on_selected_rows)

	def on_datas_changed(self, api_datas:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_datas_changed : {len(api_datas)}")
		self.selected_rows = None


	def on_selected_rows(self, selected_rows:list[dict]):
		logger.debug(f"{self.__class__.__name__} : on_selected_rows : {selected_rows}")
		logger.debug(f" api_datas : {self.api_datas}")
		if hasattr(self, 'selected_rows'):
			self.selected_rows = selected_rows
			self.PB_평가_copy_create.setDisabled(False)
			self.PB_역량평가.setDisabled(False)
			self.PB_평가체계.setDisabled(False)
			self.render_start_end_button(selected_rows[0])


	def render_start_end_button(self, dataObj:dict):
		""" self.selected_rows 에 따라 버튼 상태 변경 """
		def check_valid_start(dataObj:dict) -> bool:
			"""정상적이면 True, 아니면 False"""
			results = []
			results.append( sum ( [ dataObj['점유_역량'], dataObj['점유_성과'], dataObj['점유_특별'] ] )  == 100)
			results.append( dataObj['is_시작'] == False )
			results.append( dataObj['is_종료'] == False )
			results.append ( sum(dataObj['차수별_점유'].values()) == 100 )
			return all(results)

		if all ([dataObj['is_시작'], dataObj['is_종료']]):
			self.PB_평가_시작_종료.setText('평가 종료됨')
			self.PB_평가_시작_종료.setEnabled(False)
		else:
			if dataObj['is_시작']:
				self.PB_평가_시작_종료.setText('평가 종료')
				self.PB_평가_시작_종료.setDisabled(True)
			else:
				self.PB_평가_시작_종료.setText('평가 시작')
				self.PB_평가_시작_종료.setEnabled(check_valid_start(dataObj))

