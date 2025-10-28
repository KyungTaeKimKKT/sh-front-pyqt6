from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import json

import modules.PyQt.Qthreads as QThs
from modules.user.async_api import Async_API_SH

from modules.PyQt.Tabs.scraping.ui.Ui_page_scraping_정부기관news_dashboard import Ui_Form

baseURL_WS = 'ws://mes.swgroup.co.kr:9998'
URL_WS_SCRAPING_GOVNEWS_STATUS = 'broadcast/webscraping_govnews_status/'

class 정부기관_NEWS_Dashboard__for_Tab(QWidget):
	def __init__(self, parent,  **kwargs):
		super().__init__(parent)
		self.stopCount = 0
		self.wsURL =  URL_WS_SCRAPING_GOVNEWS_STATUS

		for k, v in kwargs.items():
			setattr( self, k, v)
		

		self.ui = Ui_Form()
		self.ui.setupUi(self)

		self.wid_Dict = {
			'한국철강협회' : self.ui.widget_Chulgang,
			'안전보건공단' : self.ui.widget_Anjunbogun,
			'국토교통부' : self.ui.widget_Kukto,
			'한국소방안전원' : self.ui.widget_Sobang,
			'한국승강기안전공단' : self.ui.widget_Elevator,
			'대한산업안전협회' : self.ui.widget_SanyubAnjun,
			'고용노동부' : self.ui.widget_Goyong,
		}

		self.__init__WS(self.wsURL)

		self.timer_marque_TIME = 1000*60 ### 30초

		self.timer_marque = QTimer(self)
		self.timer_marque.timeout.connect(self.slot_render_marque )
		
		self.marque_index = 0
		self.marque_list = []
		
		self.__init__UI_marque()

	def __init__UI_marque(self):
		w = self.ui.label_Marquee
		w.setFixedSize(self.width(), 120 )
		# w.setMinimumWidth ( 1500 )
		w.setStyleSheet("background-color:black;color:yellow")
		f=QFont()
		f.setPointSize(64)
		f.setBold(True)
		f.setItalic(True)
		f.setFamily("Courier")
		w.setFont(f)

		w.signal_finished.connect (self.slot_render_marque)

	def __init__WS(self,  wsUrl:str):		
		self.ws = QThs.User_WS_Client(self, wsUrl)
		self.ws.signal_receive_message.connect(self.slot_WS_receive_message)
		self.ws.start()

	def closeEvent(self, event: QEvent):
		try:
			if hasattr(self, 'ws') : self.ws.close()
		except Exception as e:
			pass
			# import modules.user.utils as Utils
			# Utils.log_print(msg=" Page_Scraping_GovNews closing error:{e}")
		event.accept()

	def run(self):


	def render_marque(self, msg:str="test", mode:str="RL") -> None:
		""" mode :  or "RL" or "LR """
		w = self.ui.label_Marquee
		w.setText(msg, mode)

	# def resizeEvent(self, a0):
	# 	if self.stopCount < 500 :
	# 		self.ui.label_Marquee.setFixedSize( self.width(), 50 )
	# 		self.stopCount += 1
	# 	return super().resizeEvent(a0)

	@pyqtSlot(dict)
	def slot_WS_receive_message(self, msgDict:dict):
		match msgDict.get('type'):
			case 'login':
				pass
			case 'broadcast':
				message:list = msgDict.get('message') 
				if message :
					self.ui.label_time.setText(msgDict.get('send_time', 'T').replace('T', '  '))
					self.display_msg_to_marque(message)

					for ( key, wid) in self.wid_Dict.items():
						msgList =  [ dictObj for dictObj in message if dictObj.get('gov_name') ==  key ]
						wid.update_msg ( msgList = msgList )

	@pyqtSlot()
	def slot_render_marque(self):
		if len(self.marque_list) > 0:
			self.render_marque( f" No.{self.marque_index+1} {self.marque_list[self.marque_index]}", "RL" )
			self.marque_index += 1 if self.marque_index < len(self.marque_list)-1  else 0
		else:
			self.render_marque( f" 신규 등록건수가 없읍니다.", "RL" )


	def display_msg_to_marque(self, message:list) :

		# if self.timer_marque.isActive() :
		# 	self.timer_marque.stop()

		self.marque_index = 0
		self.marque_list = []
		for obj in message :
			obj:dict
			if obj.get('cnt_신규') >0 :
				for 신규항목 in obj.get('new_article'):
					self.marque_list.append ( f"[{신규항목.get('정부기관')}] - [{신규항목.get('구분')}] : {신규항목.get('제목')}")

		self.slot_render_marque()

		# self.timer_marque.start(self.timer_marque_TIME)
