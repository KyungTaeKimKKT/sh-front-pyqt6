import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import urllib
import datetime
import json, copy
from pathlib import Path


# import user_defined compoent
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly

from modules.PyQt.Tabs.작업지침서.dialog.widget.Wid_작업지침서_main import Wid_작지_main
from modules.PyQt.Tabs.작업지침서.dialog.widget.Wid_작업지침서_의장도  import Wid_작지_의장도

from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.combo_lineedit import Combo_LineEdit
from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_작업지침서_Form( QDialog, Qwidget_Utils):
	signal = pyqtSignal(dict)
	signal_refresh = pyqtSignal()

	def __init__(self,  parent,  **kwargs  ):
		super().__init__(parent)
		self.kwargs = kwargs
		self.validator_list = ['제목', ]	
		self.fNames = []
		self.현장명_fks = []
		self.process_app_DB_data = []
		self.is_editMode_only의장도 = False
		self.is_ECO = False

		self.mainName = '작업지침서'
		self.tabs_config = {self.mainName: 'Wid_작지_main',
					  		'의장도' : 'Wid_작지_의장도' ,}
		self.tabs_Elms = {}


		for k, v in kwargs.items():
			setattr ( self, k, v)

		self.UI()
		
		self.show()
		
	def UI(self):
		# self.setMinimumSize(1200, 1200)
		
		if hasattr(self, 'layout_Main') :
			self.deleteLayout (self.layout_Main)
		
		# 메인 레이아웃 설정
		mainLayout = QVBoxLayout(self)

		# 크기 조절 가능하도록 설정
		self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
		self.setSizeGripEnabled(True)  # QDialog의 크기 조절 활성화
		
		# 적절한 초기 크기 설정
		screen = QApplication.primaryScreen().geometry()
		self.resize(min(screen.width() * 0.8, 1200), min(screen.height() * 0.8, 800))

		# 스크롤 영역 생성
		scrollArea = QScrollArea()
		scrollArea.setWidgetResizable(True)
		scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		
		# 컨테이너 위젯 생성
		container = QWidget()
		self.layout_Main = QVBoxLayout(container)
		# self.layout_Main.setSpacing(16)

		self.init_UI_tabs()

		self.layout_Main.addWidget(self.tabWidgets)

		# 스크롤 영역에 컨테이너 설정
		scrollArea.setWidget(container)
		mainLayout.addWidget(scrollArea)
		# self.setLayout(mainLayout)
		# self.setLayout(self.layout_Main)


	def init_UI_tabs(self) -> None:		
		self.tabWidgets = QTabWidget(self)
		for name, className in self.tabs_config.items():
			wid = eval(f"{className}(self, **self.kwargs )")
			# setattr( self, name, wid )
			self.tabs_Elms[name] = wid
			self.tabWidgets.addTab(wid, name)
			# wid.run()
			self.tabWidgets.setCurrentWidget(wid)
			if name == self.mainName:
				wid: Wid_작지_main
				wid.signal_textChanged.connect(self.slot_textChanged)
				wid.signal_save.connect( self.slot_signal_save )
				wid.signal_cancel.connect ( self.close  )

		self.tabWidgets.setCurrentIndex(0)

	
			
	def TriggerConnect(self):
		self.tabs_Elms[self.mainName].PB_save.clicked.connect(self.func_save)
		self.tabs_Elms[self.mainName].PB_cancel.clicked.connect(self.close)

	def slot_textChanged(self, msg:dict) -> None:
		if not msg : return
		for key in msg.keys():
			for name, tab_Wid in self.tabs_Elms.items():
				if name == self.mainName: continue
				if ( inputWid := tab_Wid.displayDict.get(key, None) ):
					if isinstance( inputWid, QLineEdit ):
						inputWid.setText( msg.get(key, ''))
						inputWid.setStyleSheet(ST.edit_ )

	def run(self):
		return 

	@pyqtSlot(dict)
	def slot_signal_save (self, sendData:dict):
		### 1. 의장도 save
		wid: Wid_작지_의장도 = self.tabs_Elms['의장도']
		의장도list = wid._get_의장도_datas()
		ic (의장도list )

		if 의장도list:					
			threadingTargets = []
			for 의장도 in 의장도list:					
				if 'id' in 의장도 :
					threadingTargets.append( {'url':INFO.URL_작업지침_의장도 , 'dataObj':{ 'id': 의장도.pop('id')}, 'sendData':의장도,  }  )
				else:
					sendFiles = 의장도.pop('files')
					threadingTargets.append ( {'url':INFO.URL_작업지침_의장도 , 'dataObj':{ 'id': -1}, 'sendData':의장도, 'sendFiles': sendFiles }  )

			futures = Utils._concurrent_Job( APP.API.Send , threadingTargets )

			result = [ future.result()[0] for index,future in futures.items() ] ### 정상이면 [True, True, True] 형태
			if all(result):
				의장도_IDs = [ future.result()[1].get('id') for index,future in futures.items() ]
				sendData.update ( {'의장도_fks' : 의장도_IDs } )
			else:
				Utils.generate_QMsg_critical(self)

		### 2. 작지 send		
		if self.is_ECO:
			prev_작지 = self.dataObj.pop('id')
			tempSend = copy.deepcopy(self.dataObj)
			tempSend.update( sendData )
			sendData = tempSend
			sendData['prev_작지'] = prev_작지
			self.dataObj['id'] = -1
			ic(sendData )
		else:
			sendData['Rev'] = 1

		is_ok, _json = APP.API.Send ( self.url, self.dataObj, sendData)	
		if is_ok:
			self.signal_refresh.emit()
			self.close()
		else:
			Utils.generate_QMsg_critical(self)



	
	## 😀 form 의 save method에서 기본적으로 get_value ==> set_value로..
	def editMode(self):
		for name, tab_wid in self.tabs_Elms.items():
			tab_wid.dataObj = copy.deepcopy(self.dataObj)
			self.tabWidgets.setCurrentWidget(tab_wid)
			if name == '작업지침서':
				tab_wid.editMode()
			elif '의장도' in name:
				tab_wid.editMode_only의장도()
				self._render_tabText_by_의장도file수( self.tabWidgets.currentIndex() )
		
		self.tabWidgets.setCurrentIndex(0)

	## 😀 form 의 edit method에서 기본적으로 set_value 에서 readonly로
	#  Object_Set_Valuee ==> Object_ReadOnly로.. button setVisible(False)
	def viewMode(self):
		for name, tab_wid in self.tabs_Elms.items():
			tab_wid.dataObj = copy.deepcopy(self.dataObj)
			self.tabWidgets.setCurrentWidget(tab_wid)
			if '의장도' in name:
				tab_wid.editMode_only의장도(False)
				self._render_tabText_by_의장도file수( self.tabWidgets.currentIndex() )
			else:
				tab_wid.viewMode()

		self.tabWidgets.setCurrentIndex(0)

		self.tabs_Elms[self.mainName].PB_save.setVisible(False)
		self.tabs_Elms[self.mainName].PB_cancel.setText('확인')


	def _render_tabText_by_의장도file수(self, curIndex:int) ->None:
		tabName = self.tabWidgets.tabText(curIndex).split('(')[0] + f"({self._get_의장도_file수()})"
		self.tabWidgets.setTabText( curIndex, tabName )

	def _get_의장도_file수(self) -> int :
		if not self.dataObj: return 0

		count = 0
		for key, valueObj in self.dataObj.get('의장도_fk_datas', {}).items():
			if isinstance(valueObj, dict):
				if valueObj.get('file') :
					count +=1
		return count



# class Form_작업지침서_관리자용( Form_작업지침서):
# 	signal = pyqtSignal(dict)

# 	def __init__(self,  parent=None,  url:str='', win_title:str='', 
# 				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
# 				 ):
# 		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)
		
# 	def run(self):
# 		super().run()

# 		main_wid = self.tabs_Elms[self.mainName]
# 		main_wid.dateEdit_Nabgi.clearMinimumDate()
# 		main_wid.lineEdit_Jaksungja.setReadOnly(False)
# 		main_wid.dateEdit_Jaksung.clearMinimumDate()
# 		main_wid.dateEdit_Jaksung.setReadOnly(False)
