import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6 import sip

from pathlib import Path


# import user_defined compoent
from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit

from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly

from stylesheet import StyleSheet
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Win_Form(QDialog):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent=parent)
		
		### file drag and drop 관련 변수들 ##
		self.urls_Files = []
		self.url_File = None
		self.is_event_valid = True
		#########################################
		
		self.url = url        
		self.win_title = win_title
		self.title = title
		self.dataObj = dataObj
		self.ST = StyleSheet()
		self.skip = skip

		self.inputType = inputType
		self.title_text = title
		# self.login_info = None
		self.inputDict = {}
		self.result = {}
		self.result_files =[]
		
		self.win_W , self.win_H = 500, 600
		self.setWindowTitle(self.title)
		self.setGeometry(450, 150, self.win_W, self.win_H)
		self.setMinimumSize( QSize(self.win_W, self.win_H) )
		self._center()
		# self.setFixedSize(self.size())
		# self.setAcceptDrops(True)

		self.is_run = False

	def run(self):
		self.UI()        
		if bool(self.dataObj) : self.editMode()
		if not self.is_run : 
			self.TriggerConnect()
			self.is_run = True

	def readOnlyMode(self):
		if hasattr(self, 'PB_cancel'):
			self.PB_cancel.deleteLater()
		self.PB_save.setEnabled(True)
		self.PB_save.setText('확인')

		for key in self.inputType.keys():
			if key == 'id':continue
			inputObj = self.inputDict[key]
			Object_ReadOnly(input=inputObj, value = self.dataObj[key])
			inputObj.setStyleSheet(self.ST.edit_)

	def disableMode(self):
		self.PB_cancel.deleteLater()
		self.PB_save.setEnabled(True)
		self.PB_save.setText('확인')
		for key in self.inputType.keys():
			if key == 'id':continue
			inputObj = self.inputDict[key]
			Object_Diable_Edit(input=inputObj, value = self.dataObj[key])
			inputObj.setStyleSheet(self.ST.edit_)

	def UI(self):

		self.formlayout = QFormLayout()
		####
		self.title = QLabel(self)
		self.title.setText(self.title_text)
		self.title.setSizePolicy(QSizePolicy.Expanding, 0)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:64px;color:white;background-color:black;")
		self.formlayout.addRow(self.title)

		for (key, value) in self.inputType.items():
			if key in self.skip: continue
   
			match value:
				case 'file_upload':
					(_txt, self.file_upload_area) = self.gen_file_upload_element(key, value)
					if  _txt is not None  and _input is not None:
						self.formlayout.addRow(_txt, self.file_upload_area)
					hbox = QHBoxLayout()
					hbox.addStretch()
					self.pb_FileUpload = QPushButton("File Upload")
					hbox.addWidget(self.pb_FileUpload)
					self.pb_FileUpload.clicked.connect(self.func_fileupload)
					self.formlayout.addRow(self.pb_FileUpload)

				case _:
					(_txt, _input) = self._gen_element(key, value)
					if  _txt is not None  and _input is not None:
						self.formlayout.addRow(_txt, _input)

		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_save = QPushButton('Save')
		self.PB_save.setEnabled(False)
		self.PB_cancel = QPushButton('Cancel')
		hbox.addWidget(self.PB_save)
		hbox.addWidget(self.PB_cancel)
		self.formlayout.addRow(hbox)
		

		self.setLayout(self.formlayout)
		self.show()

	def TriggerConnect(self):
		self.PB_save.clicked.connect(self.func_save)
		self.PB_cancel.clicked.connect(self.func_cancel)

	def editMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == 'id':continue
			inputObj = self.inputDict[key]
			Object_Set_Value(input=inputObj, value = self.dataObj.get(key,'') )
	
	def viewMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == 'id':continue
			inputObj = self.inputDict[key]
			Object_ReadOnly(input=inputObj, value = self.dataObj.get(key,'') )
		
		self.PB_save.setVisible(False)
		self.PB_cancel.setText('확인')

	##### event filter 및 drag event #####


	# https://stackoverflow.com/questions/65974531/how-to-add-a-context-menu-to-a-context-menu-in-PyQt6
	def eventFilter(self, source, event:QEvent):

		if event.type() == QEvent.ContextMenu:
			
			menu = QMenu()

			action_delete = menu.addAction('Delete')

			action = menu.exec_(event.globalPos())

			if action == action_delete:

				if (idx:=self._get_Index_layout(self.formlayout, source) ) is not None:
					self.urls_Files.pop(idx)
				self.formlayout.removeWidget(source)
				source.deleteLater()
				source = None
		return super().eventFilter(source, event)
	


	def dragEnterEvent(self, event):
		if not isinstance(event, QDragEnterEvent): return

		### only 1 file
		mimeData = event.mimeData()
		if len( mimeData.urls() ) != 1 : 
			self.is_event_valid = False
			event.ignore()
			return None
		
		for url in mimeData.urls():
			self._check_file_type(url)
			if self.url_File == url : 
				self.is_event_valid = False
				event.ignore()
			else:
				self.url_File = url
				self.is_event_valid |= True
				event.accept()




	def dragMoveEvent(self, event):
		if not isinstance(event, QDragMoveEvent): return
		if not self.is_event_valid : return

		if self.is_event_valid: event.accept()
		else: event.ignore()
		
		# mimeData = event.mimeData()

		# for url in mimeData.urls():
		#     if url in self.urls:Files event.ignore()


	def dropEvent(self, event):

		if not isinstance(event, QDropEvent): return
		if not self.is_event_valid : return
		
		mimeData = event.mimeData()
		for url in mimeData.urls():
			if url not in self.urls_Files:
				self.urls_Files.insert(0, url)

		for index, url in enumerate(self.urls_Files):        
			if self.is_event_valid:
				event.setDropAction(Qt.CopyAction)               

				file_path = url.toLocalFile()
				self.file_upload_area.setText(file_path)
				self.is_event_valid = False
 
				event.accept()
			else:
				event.ignore()

	def _check_file_type(self, url):
		db = QMimeDatabase()
		mimetype = db.mimeTypeForUrl(url)

		# if mimetype.name() == "application/pdf":
			#     urls.append(url)


	##### Trigger Func. #####
	def func_fileupload(self):
		fileName, filter = QFileDialog.getOpenFileName(self, 'Open file', 
			str(Path.home() / "Downloads"), '*.*(*.*)')
		if fileName:
			self.file_upload_area.setText(fileName)

	def func_save(self):
		for (key, input) in self.inputType.items():
			if key in self.skip: continue
			self.result[key] = self._get_value(key)
		self.signal.emit({
			'id' : self.dataObj.get('id') if self.dataObj else -1,
			'save':self.result, 			
		})
		
	
	def func_cancel(self, is_send=False):
		# if not is_send :self.Signal.emit({'type':'close'})
		self.close()

	def _center(self):
		frameGm = self.frameGeometry()
		## pyqt5
		# screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		# centerPoint = QApplication.desktop().screenGeometry(screen).center()
		## pyqt6 : https://stackoverflow.com/questions/68037950/module-pyqt6-qtwidgets-has-no-attribute-qdesktopwidget
		centerPoint = QGuiApplication.primaryScreen().availableGeometry().center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())
 
	def _get_value(self, key:str):		
		input = self.inputDict[key]
		value =  Object_Get_Value(input)

		return value.get()

	############### element generate #########
	def gen_file_upload_element(self,key, value):
		setattr(self, key+'_label', QLabel() )
		label = getattr(self, key+'_label' )
		label.setText(key)

		upload_area = QLabel()
		upload_area.setAlignment(Qt.AlignCenter)
		upload_area.setText('\n\n Drop File Here\n (오직 file 1개만 가능합니다) \n\n')
		upload_area.setWordWrap(True)
		upload_area.setFixedHeight(96)
		upload_area.setStyleSheet('''
			QLabel{
				border: 4px dashed #aaa
			}
		''')

		return (label, upload_area)


	def _gen_element(self, key:str='', eval_Value:str=''):
		setattr(self, key+'_label', QLabel() )
		label = getattr(self, key+'_label' )
		label.setText(key)

		#### 🥲 각 tab app의 self.header_type 을 사용하기 위해 변형함 ㅜㅜ;; ###
		if '___' in eval_Value: eval_Value = eval_Value.replace('___','')
		if 'parent' in eval_Value: eval_Value = eval_Value.replace('parent', 'self')
		#######
		try:
			setattr(self, key+'_input', eval(eval_Value) if len(eval_Value) >2 else QLineEdit() )
		except:

			self.user_defined_gen_element(key, eval_Value )
		input = getattr(self, key+'_input' )

		return self._gen_by_key(key, eval_Value, label, input)

	### Hard-coding 😀😀
	def user_defined_gen_element(self, key:str='', eval_Value:str='' ) -> None:
		setattr(self, key+'_input', eval(eval_Value) )

	def _gen_by_key(self, key:str='', eval_Value:str='', label:object=None, input:object=None):
		match key:
			case 'Mail_ID':
				input.setPlaceholderText("사내 MAIL ID를 넣으세요")
				input.textChanged.connect(self.Mail_ID_changed)
			case 'Password':
				input.setPlaceholderText("비밀번호를 넣으세요")
				input.setEchoMode( QLineEdit.Password)
				input.textChanged.connect(self.PWD_changed)
			
			case _:
				pass
				
			
		self.inputDict[key] = input

		return (label, input)
	
	def deleteLayout(self, cur_lay):
		# QtWidgets.QLayout(cur_lay)
		
		if cur_lay is not None:
			while cur_lay.count():
				item = cur_lay.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					self.deleteLayout(item.layout())
			sip.delete(cur_lay)


class Win_Form_View( Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id']):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)

	def run(self):
		self.UI()
		self.TriggerConnect()
		self.readOnlyMode()
		# self.TriggerConnect()


	def UI(self):
	   
		self.formlayout = QFormLayout()
		####
		self.title = QLabel(self)
		self.title.setText(self.title_text)
		self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.title.setAlignment(Qt.AlignCenter)
		self.title.setStyleSheet("font-size:64px;color:white;background-color:black;")
		self.formlayout.addRow(self.title)

		for (key, value) in self.inputType.items():
			if key == 'id': continue

			(_txt, _input) = self._gen_element(key, value)
			if  _txt is not None  and _input is not None:
				self.formlayout.addRow(_txt, _input)



		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_save = QPushButton('Save')
		self.PB_save.setEnabled(True)
		hbox.addWidget(self.PB_save)
		self.formlayout.addRow(hbox)

		self.setLayout(self.formlayout)
		self.show()

	def TriggerConnect(self):
		self.PB_save.clicked.connect(self.close)

	def disableMode(self):
		for key in self.inputType.keys():
			if key == 'id':continue
			Object_Diable_Edit(input=self.inputDict[key], value = self.dataObj[key])

	def deleteLayout(self, cur_lay):
		# QtWidgets.QLayout(cur_lay)
		
		if cur_lay is not None:
			while cur_lay.count():
				item = cur_lay.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					self.deleteLayout(item.layout())
			sip.delete(cur_lay)

# class 공지사항_View_Form(Win_Form_View):
#     def __init__(self):
#         super.__in