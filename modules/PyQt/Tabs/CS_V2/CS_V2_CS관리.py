from modules.common_import_v2 import *
from functools import partial

from modules.PyQt.Tabs.CS_V2.tables.Wid_table_품질경영_CS관리 import Wid_table_품질경영_CS관리 as Wid_Table
# from modules.PyQt.Tabs.CS_V2.chart.gantt_chart import GanttMainWidget
from modules.PyQt.Tabs.CS_V2.chart.gantt_chart_v2 import CS_GanttMainWidget

from modules.PyQt.compoent_v2.table_v2.Base_Main_Widget import Base_MainWidget
from modules.PyQt.Tabs.plugins.BaseTab_V2 import BaseTab_V2

from modules.PyQt.compoent_v2.list_edit.list_edit import Dialog_list_edit
from modules.PyQt.compoent_v2.Wid_label_and_pushbutton import Wid_label_and_pushbutton

from modules.PyQt.compoent_v2.widget_manager import WidManager

from modules.PyQt.compoent_v2.base_form_dialog import Base_Form_Dialog


class CS_Project_Form(Base_Form_Dialog):
	minium_size = (600, 600)
	_url_list_for_label_pb = {
		'Elevator사': INFO.URL_CS_CLAIM_GET_ELEVATOR사,
		'부적합유형': INFO.URL_CS_CLAIM_GET_부적합유형,
	}

	el_info_fk:Optional[int] = None
	def __init__(self, parent=None, url:str='', win_title:str='', 
					inputType:dict={}, title:str='', dataObj:dict={}, 
					skip_generate:list=['id'], skip_save:list=[],order_attrNames:list=[],
					mode:str='edit', **kwargs):
		super().__init__(parent, url, win_title, inputType, title, dataObj, skip_generate, skip_save, order_attrNames, mode, **kwargs)
		self.default_inputType = {
			'현장명': 'CharField',
			'현장주소': 'CharField',
			'el수량': 'IntegerField',
			'운행층수': 'IntegerField',
			'Elevator사': 'CharField',
			'부적합유형': 'CharField',
			'불만요청사항': 'TextField',
			'고객명': 'CharField',
			'고객연락처': 'CharField',
			'차수': 'IntegerField',
			'claim_files': 'MultiFileField',
			'진행현황': 'CharField',                
			'완료요청일': 'DateField'
		}
		self.inputType = inputType or self.default_inputType
		self.validate_keys:list[str] = self.kwargs.get('validate_keys', [])
		self.defalut_value:dict[str, str] = self.kwargs.get('default_value', {})

		if not self.kwargs.get('activate_base_UI', True):
			self.UI()
			self.validate_send_data( is_init=True)
			if not self.is_readonly:
				for attrName, widget in self.inputDict.items():
					if isinstance(widget, QLineEdit):
						widget.textChanged.connect(self.validate_send_data)
					elif isinstance(widget, QDateEdit):
						widget.dateChanged.connect(self.validate_send_data)
					elif isinstance(widget, QComboBox):
						widget.currentTextChanged.connect(self.validate_send_data)
					elif isinstance(widget, QTextEdit):
						widget.textChanged.connect(self.validate_send_data)
					elif isinstance(widget, QSpinBox):
						widget.valueChanged.connect(self.validate_send_data)
					elif isinstance(widget, Wid_label_and_pushbutton ):
						widget.lb_textChanged.connect( lambda text: self.validate_send_data() )

	def _gen_inputWidget(self, attrName:str='', attrType:str='') -> QWidget:
		self.map_attrName_to_button_dict = {
			'Elevator사': {'button_dict':{'text':'선택', 'clicked':self.on_select_Elevator_Company}},
			'부적합유형': {'button_dict':{'text':'선택', 'clicked':self.on_select_NCR_Type}	},
			'현장명': {'button_dict':{'text':'검색', 'clicked':self.on_hyunjang_search}},
		}

		match attrName:
			case '진행현황':
				pass
			case 'Elevator사' | '부적합유형' :
				self.inputDict[attrName] = WidManager._create_label_and_pushbutton_widget(
					self, 
					self.dataObj.get(attrName, ''),
					is_readonly=self.is_readonly,
					**self.map_attrName_to_button_dict[attrName],
					default_text='선택 필수입니다.'
					)
				return self.inputDict[attrName]
			case '현장명':
				self.inputDict['현장명'] = WidManager._create_lineedit_and_pushbutton_widget(
					self, 
					self.dataObj.get(attrName, ''),
					is_readonly=self.is_readonly,
					**self.map_attrName_to_button_dict[attrName]
					)
				return self.inputDict[attrName]

			case 'claim_files':
				claim_files_url = self.dataObj.get( 'claim_files_url', [])
				if claim_files_url and isinstance(claim_files_url, list) :
					if claim_files_url[0].startswith('http://') or claim_files_url[0].startswith('https://'):
						pass
					else:
						claim_files_url = [ f'http://{INFO.API_SERVER}:{INFO.HTTP_PORT}' + item for item in claim_files_url ]
				claim_files = []
				for (id, url) in zip(self.dataObj.get('claim_files_ids', []), claim_files_url):
					claim_files.append( {'id':id, 'file':url} )

				self.inputDict['claim_files'] = WidManager._create_file_upload_list_widget(
					self, 
					claim_files,
					is_readonly=self.is_readonly,
					)
				return self.inputDict[attrName]

			case _:
				return super()._gen_inputWidget(attrName, attrType)
			
			
	def get_send_data(self):
		""" override """
		send_data, send_files = super().get_send_data()
		if self.el_info_fk:
			send_data['el_info_fk'] = self.el_info_fk
		# send_data['등록자_fk'] = INFO.USERID
		# send_data['등록자'] = INFO.USERNAME
		# send_data['등록일'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		### drf 와 연동되는 것으로, 파일 전송 시 파일 경로와 파일 아이디를 따로 보내야 함.
		keyNamesFile = 'claim_files'
		if keyNamesFile in send_data:
			send_files_dict_list = send_data.pop(keyNamesFile)
			file_paths = [ item.get('file') for item in send_files_dict_list  if item.get('type') == 'local']
			send_files = [
    			(keyNamesFile, (open(path, "rb"))) for path in file_paths
			]
			claim_files_ids = [ item.get('id') for item in send_files_dict_list  if item.get('type') == 'server']
			send_data['claim_files_ids'] = claim_files_ids
		logger.debug(f"send_data : {send_data}")
		
		return send_data, send_files
	
	def validate_send_data(self, is_init:bool=False):
		send_data, _ = self.get_send_data()

		필수항목_list_결과 = [ bool(send_data.get(key, self.defalut_value.get(key, '')) != self.defalut_value.get(key, '')) 
				  for key in self.validate_keys ]
		if not all ( 필수항목_list_결과 ):
			if not is_init:
				_text = f"<br>"
				for _key, _result in zip(self.validate_keys, 필수항목_list_결과):
					if not _result:
						_text += f"<b>{_key}, </b> "
				_text += "<br>필수 입력 항목을 확인하세요."
				Utils.generate_QMsg_critical(self, 
									title='경고', 
									text=_text)
			self.PB_save.setEnabled(False)
			return False

		self.PB_save.setEnabled(True)
		return True
			
	def on_hyunjang_search(self):
		현장명 =  WidManager.get_value( self.inputDict['현장명'] )

		try:

			app_dict = INFO.APP_권한_MAP_ID_TO_APP[61]
			from modules.PyQt.compoent_v2.dlg_dict_selectable_table import DictTableSelectorDialog	

			url = app_dict.get('api_uri') + app_dict.get('api_url') + f"?search={현장명}&page_size=100"
			_isOk, _json = APP.API.getlist(url)
			if _isOk:
				datas = _json.pop('results', [])
				pagination = _json
				if pagination.get('countTotal') > 100:
					Utils.generate_QMsg_critical(self, title='경고', text="검색 결과가 많읍니다. <br>검색 조건을 좁히세요.")
				else:
					dlg = DictTableSelectorDialog(
							None, 
							datas=datas, 
							attrNames= [ '건물명', '건물주소_찾기용','수량','운행층수','최초설치일자' ]
						)
					dlg.setMinimumSize(1200, 1200)
					if dlg.exec():
						selected_data = dlg.get_selected()
						if selected_data:
							WidManager.set_value(self.inputDict['현장명'], selected_data.get('건물명'))
							WidManager.set_value(self.inputDict['현장주소'], selected_data.get('건물주소_찾기용'))
							WidManager.set_value(self.inputDict['el수량'], selected_data.get('수량'))
							WidManager.set_value(self.inputDict['운행층수'], selected_data.get('운행층수'))
							self.el_info_fk = selected_data.get('id')

						logger.debug(f"선택된 데이터 : {selected_data}")
			else:
				raise ValueError(f"검색 실패 : {_json}")
		except Exception as e:
			Utils.generate_QMsg_critical(self, title='경고', text="검색 권한이 없읍니다. <br>관리자에게 문의바랍니다.")
			logger.error(f"on_search : {e}")
			logger.error(traceback.format_exc())
			return
		
	def on_select_Elevator_Company(self):
		""" PB_El_Company 클릭시 호출 , dialog 호출 후 선택된 값을 _update_El_company 호출 """
		self.handle_widget_for_label_pb('Elevator사')

	
	def on_select_NCR_Type(self):
		""" PB_NCR_Type 클릭시 호출 , dialog 호출 후 선택된 값을 _update_NCR_Type 호출 """
		self.handle_widget_for_label_pb('부적합유형')


	def handle_widget_for_label_pb(self, attrName:str):
		_isok, _list = APP.API.getlist(self._url_list_for_label_pb[attrName]+'?page_size=0')
		if _isok:
			dlg = Dialog_list_edit(self, title=f'{attrName} 선택', _list=_list, is_sorting=False)
			if dlg.exec():
				selected_item = dlg.get_value()
				WidManager.set_value(self.inputDict[attrName], selected_item)
		else:
			Utils.generate_QMsg_critical(self, '경고', f'{attrName} 선택 실패')
			return []


class CS_Claim_Accept_Form(Base_Form_Dialog):
	def __init__(self, parent=None, url:str='', win_title:str='', 
					inputType:dict={}, title:str='', dataObj:dict={}, 
					skip_generate:list=['id'], skip_save:list=[],order_attrNames:list=[],
					mode:str='edit', **kwargs):
		super().__init__(parent, url, win_title, inputType, title, dataObj, skip_generate, skip_save, order_attrNames, mode, **kwargs)
		self.default_inputType = {
			'진행계획': 'TextField',
			'완료목표일': 'DateField',
			'완료요청일': 'DateField'
		}
		self.inputType = inputType or self.default_inputType
		self.validate_keys:list[str] = self.kwargs.get('validate_keys', [])
		self.defalut_value:dict[str, str] = self.kwargs.get('default_value', {})

		self.data:dict = {}

		if not self.kwargs.get('activate_base_UI', True):
			self.UI()
			self.validate_send_data( is_init=True)
			if not self.is_readonly:
				for attrName, widget in self.inputDict.items():
					if isinstance(widget, QLineEdit):
						widget.textChanged.connect(self.validate_send_data)
					elif isinstance(widget, QDateEdit):
						widget.dateChanged.connect(self.validate_send_data)
					elif isinstance(widget, QComboBox):
						widget.currentTextChanged.connect(self.validate_send_data)
					elif isinstance(widget, QTextEdit):
						widget.textChanged.connect(self.validate_send_data)
					elif isinstance(widget, QSpinBox):
						widget.valueChanged.connect(self.validate_send_data)
					elif isinstance(widget, Wid_label_and_pushbutton ):
						widget.lb_textChanged.connect( lambda text: self.validate_send_data() )
			WidManager.set_value(self.inputDict['완료목표일'], self.dataObj.get('완료요청일', datetime.now().date()))
			WidManager.set_value(self.inputDict['완료요청일'], self.dataObj.get('완료요청일', datetime.now().date()))
			WidManager.set_readonly(self.inputDict['완료요청일'])

	def _UI_button(self):
        #### 버튼 생성
		self.button_container = QWidget(self)
		self.hlayout = QHBoxLayout()
		self.hlayout.addStretch()
		if not self.is_readonly:
			self.PB_accept = QPushButton('접수완료')        
			self.PB_reject = QPushButton('접수거절')

			self.PB_cancel = QPushButton('취소')
			self.hlayout.addWidget(self.PB_accept)
			self.hlayout.addWidget(self.PB_reject)  
			self.hlayout.addWidget(self.PB_cancel)  
			self.PB_accept.clicked.connect(self.on_claim_accept)
			self.PB_reject.clicked.connect(self.on_claim_reject)
			self.PB_cancel.clicked.connect(self.on_cancel)
		else:
			self.PB_cancel = QPushButton('닫기')
			self.hlayout.addWidget(self.PB_cancel)
			self.PB_cancel.clicked.connect(self.on_cancel)

		self.button_container.setLayout(self.hlayout)
		return self.button_container
	
	def on_claim_accept(self):
		send_data, _ = self.get_send_data()
		self.data = send_data
		self.data['진행현황'] = '접수'
		self.accept()

	def on_claim_reject(self):
		text, ok = QInputDialog.getText(self, "반려사유", "반려사유를 입력하세요:")
		if ok and text:
			self.data['반려사유'] = text
			self.data['진행현황'] = '반려'
			self.accept()

	def get_value(self):
		return self.data

	def validate_send_data(self, is_init:bool=False):
		send_data, _ = self.get_send_data()

		필수항목_list_결과 = [ bool(send_data.get(key, self.defalut_value.get(key, '')) != self.defalut_value.get(key, '')) 
				  for key in self.validate_keys ]
		if not all ( 필수항목_list_결과 ):
			if not is_init:
				_text = f"<br>"
				for _key, _result in zip(self.validate_keys, 필수항목_list_결과):
					if not _result:
						_text += f"<b>{_key}, </b> "
				_text += "<br>필수 입력 항목을 확인하세요."
				Utils.generate_QMsg_critical(self, 
									title='경고', 
									text=_text)
			self.PB_accept.setEnabled(False)
			self.PB_reject.setEnabled(False)
			return False

		self.PB_accept.setEnabled(True)
		self.PB_reject.setEnabled(True)
		return True


class CS_Project_Activity_Form(Base_Form_Dialog):
	minium_size = (600, 600)

	def on_save(self):

		if self.url and self.inputDict:
			sendData, sendFiles = self.get_send_data()
			id = sendData.pop('id')
			_isOk, _json = APP.API.Send(
				url=self.url, 
				dataObj = {'id': id}, 
				sendData = sendData,
				sendFiles = sendFiles
				)
			if _isOk:
				Utils.generate_QMsg_Information(None, title='저장 완료', text='저장 완료', autoClose=1000)
				self.api_send_result = _json
				self.accept()
			else:
				logger.error(f"저장 실패: {_json}")
				QMessageBox.warning(self, "경고", "저장 실패")
		else:
			logger.error(f"저장 실패: {self.url}")
			QMessageBox.warning(self, "경고", "저장 실패")
			
	def get_send_data(self):
		""" override """
		send_data, send_files = super().get_send_data()
		send_data['id'] = -1
		send_data['claim_fk'] = self.dataObj.get('id')
		send_data['등록자_fk'] = INFO.USERID
		send_data['활동일'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		send_data['등록일'] = send_data['활동일']

		### drf 와 연동되는 것으로, 파일 전송 시 파일 경로와 파일 아이디를 따로 보내야 함.
		keyNamesFile = 'activity_files'
		if keyNamesFile in send_data:
			send_files_dict_list = send_data.pop(keyNamesFile)
			file_paths = [ item.get('file') for item in send_files_dict_list  if item.get('type') == 'local']
			send_files = [
    			(keyNamesFile, (open(path, "rb"))) for path in file_paths
			]
			claim_files_ids = [ item.get('id') for item in send_files_dict_list  if item.get('type') == 'server']
			send_data['claim_files_ids'] = claim_files_ids
		logger.debug(f"send_data : {send_data}")
		
		return send_data, send_files
	

class ActivityViewDialog(QDialog):
	def __init__(self, parent=None, dataObj:dict=None, detail_list:list[dict]=None):		
		super().__init__(parent)
		self.dataObj = dataObj 
		self.detail_list = detail_list
		if self.dataObj:
			self.activity_list = self.dataObj.get('activity_set', [])
			_title = f"{self.dataObj.get('현장명', '')}  : Claim 활동 기록 보기"
		elif self.detail_list:
			self.activity_list = self.detail_list
			_title = f"Claim 활동 기록 보기"
		else:
			raise ValueError(f"dataObj 또는 detail_list 중 하나는 필수입니다.")

		
		self.setWindowTitle(_title)
		self.resize(500, 400)

		main_layout = QVBoxLayout(self)

		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		content = QWidget()
		content_layout = QVBoxLayout(content)

		# 반복해서 activity 추가
		for idx, activity in enumerate(self.activity_list, start=1):
			group = self._create_activity_group(activity, idx)
			content_layout.addWidget(group)

		scroll.setWidget(content)
		main_layout.addWidget(scroll)


	def _create_activity_group(self, activity: dict, index: int) -> QGroupBox:
		_groupTxt = f"활동 #{index} " + (
			f" id: {activity.get('id')}" if INFO._get_is_app_admin() else ''
		)
		group = QGroupBox(_groupTxt)
		layout = QFormLayout(group)

		for key, value in activity.items():
			key, value = self._convert_key_value(key, value)

			if not INFO._get_is_app_admin() and self.is_skip_key(key):
				continue

			value_str = str(value)
			if '\n' in value_str or len(value_str) > 50:
				# 긴 텍스트는 QTextEdit으로 처리
				widget = QTextEdit()
				widget.setPlainText(value_str)
				widget.setReadOnly(True)
				widget.setMaximumHeight(100)
			else:
				widget = QLabel(value_str)
				widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

			layout.addRow(f"<b>{key}</b>", widget)
			layout.setAlignment(widget, Qt.AlignmentFlag.AlignTop)

		group.setStyleSheet("""
			QGroupBox {
				border: 1px solid #ccc;
				border-radius: 8px;
				margin-top: 10px;
			}
			QGroupBox::title {
				subcontrol-origin: margin;
				left: 10px;
				padding: 0 3px 0 3px;
			}
		""")
		return group
	
	def _convert_key_value(self, key:str, value:str) -> tuple[str, str]:
		match key:
			case '활동일' | '등록일':
				date_str = datetime.fromisoformat(value).strftime('%Y-%m-%d')
				return key, Utils.format_date_str_with_weekday( date_str, with_year=True, with_weekday=True)
			case '등록자_fk':
				return '등록자',  INFO._get_username(value)
			case _:
				return key, value
			
	def is_skip_key(self, key:str) -> bool:
		return key in ['id', 'claim_fk', '등록일']

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
			self.mapping_name_to_widget['Chart'] = CS_GanttMainWidget(self)
		self.valid_mapping_name_to_widget = [ name for name in self.mapping_name_to_widget.keys() if self.mapping_name_to_widget[name] is not None and name != 'empty']
		QTimer.singleShot(0, self.update_wid_select_main)


class CS관리__for_Tab( BaseTab_V2 ):

	skip_generate = [
		"id", "el_info_fk", "등록자_fk", "등록자", "등록일", "완료자_fk", "완료자", "완료일",
		"claim_file_수", "action_수", "claim_files_ids", "claim_files_url",
		"activty_files_ids", "activty_files_url", "activty_files_수",
	]

	def _create_container_main(self) -> QWidget:
		container_main = QWidget()
		v_layout = QVBoxLayout(container_main)
		self._create_select_main_widget()
		if self.wid_select_main:
			v_layout.addWidget(self.wid_select_main)

		self.mainWidget = MainWidget(self)
		v_layout.addWidget(self.mainWidget)
		return container_main
	
	def _get_inputType(self) -> dict:
		try:
			if hasattr(self, 'table_name') and self.table_name and self.table_name in INFO.ALL_TABLE_TOTAL_CONFIG.get('MAP_TableName_To_TableConfig', {}):

				table_config = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_TableConfig', {})
				inputType = table_config.get('_column_types')
				##### custom
				inputType['claim_files'] = 'MultiFileField'
				if not inputType:
					raise ValueError(f"inputType is not found in {self.table_name}")
			else:
				inputType = {}

		except Exception as e:
			logger.error(f"on_claim_project : {e}")
			logger.error(traceback.format_exc())
			return {}
	
	def _get_form_kwargs(self, dataObj:dict={}, mode:str='edit') -> dict:
		if mode == 'accept':
			validate_keys = ['진행계획', '완료목표일']
			return {
				'parent':self, 						
				'url': f"{self.url}/accept",
				'win_title': '고객불만_요청_관리',
				'inputType': self._get_inputType(), #self.appData._get_form_type(),
				'title': '고객불만_요청_관리 : CS 접수',		
				'dataObj': dataObj,
				'order_attrNames': ['진행계획', '완료목표일','완료요청일'],
				'mode': 'edit',
				'activate_base_UI':False,
			}

		return {
			'parent':self, 						
			'url': self.url,
			'win_title': '고객불만_요청_관리',
			'inputType': self._get_inputType(), #self.appData._get_form_type(),
			'title': '고객불만_요청_관리',		
			'dataObj': dataObj,
			'skip_generate':self.skip_generate,
			'order_attrNames': ['현장명', '현장주소', 'el수량','운행층수','Elevator사','부적합유형', '불만요청사항', '고객명','고객연락처','차수','claim_files','진행현황','완료요청일',],
			'mode': mode,
			'activate_base_UI':False,
			'validate_keys':['현장명', '현장주소', 'el수량','운행층수','Elevator사','부적합유형', '불만요청사항', '고객명','고객연락처','차수','완료요청일',],
			'default_value':{
				'Elevator사': '선택 필수입니다.',
				'부적합유형': '선택 필수입니다.',
			}
		}

	def handle_cs_project_form(self, dataObj:dict ={}, mode:str='edit'):
		s= time.perf_counter()
		form = CS_Project_Form( **self._get_form_kwargs(dataObj, mode) )
		e= time.perf_counter()
		print(f"handle_cs_project_form : {(e-s)*1000:.2f}ms")
		if form.exec():			
			resultObj = form.get_api_result()
			if resultObj:
				self.simulate_search_pb_click()

	def on_claim_new_project(self):
		### 클레임 프로젝트 신규 생성 Dialog 호출		
		self.handle_cs_project_form(dataObj={}, mode='new')

	def on_claim_edit_view(self, selected_dataObj:dict):

		진행현황  = selected_dataObj.get('진행현황', '')
		mode = 'readOnly' if bool(진행현황 == 'Open' or 진행현황 == 'Close') else 'edit'
		self.handle_cs_project_form(selected_dataObj, mode)



	def on_delete_row(self, selected_dataObj:dict):
		### 삭제 확인 다이얼로그 호출
		_text = f"""
		<b style="font-size:14pt; color:#d9534f;">{selected_dataObj['현장명']}</b><br><br>
		<b>정말 삭제하시겠습니까?</b><br><br>
		<span style="color:#d9534f;">삭제된 데이터는 <u>복구할 수 없습니다.</u></span><br>
		<br>
		<span style="color:#777;">
		삭제 후 <b>DB에서 다시 조회</b>됩니다. <br>
		잠시 기다려 주십시오.
		</span>
		"""
		if Utils.QMsg_question(self, title='삭제 확인', text=_text):
			is_ok = APP.API.delete(self.url+f"{selected_dataObj['id']}/" )
			if is_ok:
				self.simulate_search_pb_click()
			else:
				Utils.generate_QMsg_critical(self, title='삭제실패', text='삭제 실패하였읍니다.<br')


	def on_action_register(self, dataObj:dict):

		inputType = {
			'활동현황': 'TextField',
			'activity_files': 'MultiFileField',
		}
		
		form = CS_Project_Activity_Form(
			parent=self, 						
			url = INFO.URL_CS_V2_CS_ACTIVITY,
			win_title=f'{dataObj.get("현장명")} Claim 활동 등록' +  ( f'=> url: ({INFO.URL_CS_V2_CS_ACTIVITY})' if INFO._get_is_app_admin() else '')	,
			inputType= inputType, #self.appData._get_form_type(),
			title= f'{dataObj.get("현장명")} Claim 활동 등록',		
			dataObj = dataObj,
			skip_generate=self.skip_generate,
			order_attrNames= ['활동현황', 'activity_files',]
			)
		if form.exec():			
			resultObj = form.get_api_result()
			if resultObj:
				self.simulate_search_pb_click()
			else:
				Utils.generate_QMsg_critical(self, title='등록 실패', text='등록 실패하였읍니다.<br>다시 시도해 주십시오.<br>')

	def on_action_view(self, dataObj:dict):
		dlg = ActivityViewDialog(parent=self, dataObj=dataObj)
		dlg.exec()

	def on_activity_view_by_cell_menu(self, detail_list:list[dict]):
		dlg = ActivityViewDialog(parent=self, detail_list=detail_list)
		dlg.exec()

	def _api_update_진행현황(self, selected_dataObj:dict, sendData:dict):
		""" 클레임 진행현황 변경
		"""
		_isOk, _json = APP.API.Send_bulk(self.url,added_url="update_진행현황", detail=True, dataObj= selected_dataObj, sendData=sendData )
		return _isOk

	def on_request_claim_open(self, selected_dataObj:dict):
		""" 클레임 배포 
		 selected_dataObj 의 진행현황을 Open 으로 변경
		"""
		sendData = {'진행현황':'의뢰' }
		if self._api_update_진행현황( selected_dataObj, sendData ):
			Utils.generate_QMsg_Information(self, title='의뢰 완료', text='의뢰 완료하였읍니다.<br>잠시 후 다시 조회됩니다..<br>', auotClose=1000)
			self.simulate_search_pb_click()
		else:
			Utils.generate_QMsg_critical(self, title='배포 실패', text='배포 실패하였읍니다.<br>다시 시도해 주십시오.<br>')

	def on_request_claim_accept(self, selected_dataObj:dict):
		""" 클레임 수락
		"""
		dlg = CS_Claim_Accept_Form( **self._get_form_kwargs(dataObj=selected_dataObj, mode='accept') )
		if dlg.exec():
			sendData = dlg.get_value()
			title = sendData.get('진행현황', 'Unkown')
			if self._api_update_진행현황( selected_dataObj, sendData ):
				Utils.generate_QMsg_Information(self, title=f'{title} 완료', text=f'{title} 완료하였읍니다.<br>잠시 후 다시 조회됩니다..<br>', auotClose=1000)
				self.simulate_search_pb_click()
			else:
				Utils.generate_QMsg_critical(self, title=f'{title} 실패', text=f'{title} 실패하였읍니다.<br>다시 시도해 주십시오.<br>')


	def on_request_claim_close(self, selected_dataObj:dict):
		""" 클레임 종료
		 selected_dataObj 의 진행현황을 Close 로 변경
		"""
		sendData = {'진행현황':'완료' }
		if self._api_update_진행현황( selected_dataObj, sendData ):

			self.simulate_search_pb_click()
		else:
			Utils.generate_QMsg_critical(self, title='종료 실패', text='종료 실패하였읍니다.<br>다시 시도해 주십시오.<br>')


	def on_map_view(self, selected_dataObj:dict):
		""" 지도 보기
		"""
		Utils.map_view(address=selected_dataObj['현장주소'])

	def on_file_download_multiple(self, urls:list[str]):
		Utils.file_download_multiple(urls)

	def on_file_view(self, urls:list[str]):
		Utils.file_view(urls)
		