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

from modules.PyQt.User.tabbar import TabBar_Custom
# from modules.PyQt.Tabs.구매.dialog.ui.Ui_구매_form_main_현대 import Ui_Form_HY

from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly

# from modules.PyQt.Tabs.구매.dialog.widget.Wid_구매_main import Wid_구매_main
# from modules.PyQt.Tabs.구매.dialog.widget.Wid_구매_SPG  import Wid_구매_SPG
# from modules.PyQt.Tabs.구매.dialog.widget.Wid_구매_SPG_empty import Wid_구매_SPG_Empty

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

class Dialog_구매_MRP_Form( QDialog, Qwidget_Utils):
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
		self.ui_type : str = '현대'   ### ['현대', 'OTIS', 'TKE', '기타'] 중 1개

		self.mainName = '구매'
		self.tabs_config = {self.mainName: 'Wid_구매_main',
					  		'SPG' : 'Wid_구매_SPG' ,}
		self.tabs_Elms = {}
		self.tabs_made_List = []
		self.fixed_tabs = 2  # 처음 2개의 탭은 닫기 불가능하도록 설정
		self.tab_count = 0

		for k, v in kwargs.items():
			setattr ( self, k, v)

		self.UI()
		
		self.show()
		self.TriggerConnect()


	def UI(self):
		self.setMinimumSize(1200, 1200)
		
		if hasattr(self, 'layout_Main') :
			self.deleteLayout (self.layout_Main)
		self.layout_Main = QVBoxLayout(self)
		# self.layout_Main.setSpacing(16)

		self.init_UI_tabs()

		self.layout_Main.addWidget(self.tabWidgets)
		self.setLayout(self.layout_Main)

	def init_UI_tabs(self) -> None:		
		""" mainTab 1ea만 생성함"""
		self.tabWidgets = QTabWidget(self)
		tabbar_wid = TabBar_Custom(self)
		tabbar_wid.signal_delete.connect(self.slot_delete_tab)
		self.tabWidgets.setTabBar( tabbar_wid) 
		for name, className in self.tabs_config.items():
			self.tab_count += 1
			if name == self.mainName:
				wid = eval(f"{className}(self, **self.kwargs)")
				# wid:Wid_생지_main|Wid_생지_spg
				# setattr( self, name, wid )
				self.tabs_Elms[name] = wid
				self.tabWidgets.addTab(wid, name)
				self.tabWidgets.setCurrentWidget(wid)
				wid.signal_save.connect( self.slot_signal_save )
			else:
				for spg_fk in self.dataObj.get('spg_fks', [-1] ):
					wid = eval(f"{className}(self, **self.kwargs, spg_fk=spg_fk )")
					# wid:Wid_생지_main|Wid_생지_spg
					# setattr( self, name, wid )
					self.tabs_Elms[name] = wid
					self.tabWidgets.addTab(wid, name)
					self.tabWidgets.setCurrentWidget(wid)
			self.tabWidgets.setTabsClosable(False)
		self.mainTabWid :QWidget= self.tabs_Elms[self.mainName]
		self.tabWidgets.setCurrentIndex(0)
		self.tabWidgets.tabCloseRequested.connect(self.slot_close_tab)  # 탭 닫기 이벤트 연결

		if 'tab_made_fks' in self.dataObj and ( tab_made_fks := self.dataObj['tab_made_fks'] ):
			self.tab_made_fks = tab_made_fks
			for ID in tab_made_fks:
				_isOk, _json = APP.API.getObj( INFO.URL_TAB_MADE, id=ID )
				if _isOk:
					self.slot_createTab ( **_json )
				else:
					Utils.generate_QMsg_critical(self)

	# def init_UI_tabs(self) -> None:		
	# 	self.tabWidgets = QTabWidget(self)
	# 	for name, className in self.tabs_config.items():
	# 		wid = eval(f"{className}(self, **self.kwargs )")
	# 		# setattr( self, name, wid )
	# 		self.tabs_Elms[name] = wid
	# 		self.tabWidgets.addTab(wid, name)
	# 		# wid.run()
	# 		self.tabWidgets.setCurrentWidget(wid)
	# 		if name == self.mainName:
	# 			wid: Wid_작지_main
	# 			wid.signal_textChanged.connect(self.slot_textChanged)
	# 			wid.signal_save.connect( self.slot_signal_save )
	# 			wid.signal_cancel.connect ( self.close  )

		# self.tabWidgets.setCurrentIndex(0)

	def clear_tabs_wo_main(self) -> None:
		while self.tabWidgets.count() > 1:
			totla_tabs = self.tabWidgets.count()
			for index in range( 1, totla_tabs ):
				# if index == 0 : continue
				self.tabWidgets.removeTab(index)
				self.tabWidgets.setCurrentIndex(0)
	
		### tab delete
	@pyqtSlot(int)
	def slot_delete_tab(self, curTabIndex:int):
		self.tabWidgets.removeTab(curTabIndex)
			
	def TriggerConnect(self):
		wid_mainTab = self.tabs_Elms[self.mainName]
		if isinstance( wid_mainTab, Wid_구매_main ):
			# wid_mainTab.signal_PB_save_clicked.connect(self.func_save)
			# wid_mainTab.signal_PB_cancel_clicked.connect(self.close)
			wid_mainTab.signal_PB_CreateTab_clicked.connect(self.slot_createTab)

			# wid_mainTab.signal_textChanged.connect(self.slot_textUpdate_spgTabs)
			# wid_mainTab.signal_Domyun_No.connect(self.slot_Domyun_No)
			# wid_mainTab.signal_Hogi_No.connect(self.slot_Hogi_No)
			# wid_mainTab.signal_JAMB.connect(self.slot_update_JAMB_FK)

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

	@pyqtSlot()
	def slot_createTab(self, **kwargs ):
		ic( kwargs )
		self.tab_count += 1
		wid =  Wid_구매_SPG_Empty(self, **kwargs )
		self.tabWidgets.addTab(wid, kwargs.get('title', 'Tab_New' ) )
		self.tabs_made_List.append( wid )
		
		# 각 탭별로 닫기 버튼 상태 설정
		for i in range(self.tabWidgets.count()):
			if i < self.fixed_tabs:
				self.tabWidgets.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
			else:
				# fixed_tabs 이후의 탭들에만 닫기 버튼 표시
				if self.tabWidgets.tabBar().tabButton(i, QTabBar.ButtonPosition.RightSide) is None:
					close_button = QToolButton()
					close_button.setText('x')
					close_button.clicked.connect(lambda checked, index=i: self.slot_close_tab(index))
					self.tabWidgets.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)

		# 탭 더블클릭으로 제목 변경 가능하게 설정
		self.tabWidgets.tabBarDoubleClicked.connect(self.slot_rename_tab)

	@pyqtSlot(int)
	def slot_close_tab(self, index:int):
		# fixed_tabs 이상의 탭만 닫을 수 있도록 수정
		if index >= self.fixed_tabs:
			self.tabWidgets.removeTab(index)
			if self.tabWidgets.count() == 0:
				self.tab_count = 0

	@pyqtSlot(int)
	def slot_rename_tab(self, index):
		current_text = self.tabWidgets.tabText(index)
		new_text, ok = QInputDialog.getText(self, "탭 이름 변경", 
										  "새로운 탭 이름을 입력하세요:", 
										  QLineEdit.EchoMode.Normal,  # 여기를 수정
										  current_text)
		if ok and new_text:
			self.tabWidgets.setTabText(index, new_text)

	@pyqtSlot(dict)
	def slot_signal_save (self, sendData:dict):
		if self.tabs_made_List :
			tab_made_fks = []
			for tabs_made in self.tabs_made_List:				
				tabs_made : Wid_구매_SPG_Empty
				for i in range ( self.tabWidgets.count() ):
					tab = self.tabWidgets.widget(i)
					if tab == tabs_made :
						# ic ( tabs_made._getValue() )		 {'image': <PyQt6.QtGui.QPixmap object at 0x7fded0125850>,
                        #                              'source': '/home/kkt/N23418_00_NO.3.4_금산젬월드_랜더링_전망용.jpg',
                        #                              'type': 'file'}
						# ic ( {'title':self.tabWidgets.tabText(i)} )
						valueDict = tabs_made._getValue()
						ic ( valueDict )
						if valueDict['type'] == 'url':
							is_ok, _json = APP.API.Send ( INFO.URL_TAB_MADE, {'id':valueDict.pop('id')}, sendData={'title':self.tabWidgets.tabText(i)} )
						elif valueDict['type'] == 'file':
							is_ok, _json = APP.API.Send ( INFO.URL_TAB_MADE, {'id':valueDict.pop('id')}, sendData={'title':self.tabWidgets.tabText(i)}, sendFiles=[ ('file',  open( valueDict['source'], 'rb') )])	
						elif valueDict['type'] in ['clipboard', 'pilImage']:
							byte_array = QByteArray()
							buffer = QBuffer(byte_array)
							buffer.open(QBuffer.OpenModeFlag.WriteOnly)
							valueDict['image'].save(buffer, 'PNG')
							# files = {'file': ('image.png', byte_array.data(), 'image/png')}
							is_ok, _json = APP.API.Send ( INFO.URL_TAB_MADE, {'id':valueDict.pop('id')}, sendData={'title':self.tabWidgets.tabText(i)}, sendFiles=[ ('file',  ('image.png', byte_array.data(), 'image/png') )])	


						if is_ok:
							tab_made_fks.append( _json.get('id'))
						else:
							Utils.generate_QMsg_critical(self)

			sendData['tab_made_fks'] = tab_made_fks

		ic ( sendData )
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
			if name == '구매':
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



# class Form_구매_관리자용( Form_구매):
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
