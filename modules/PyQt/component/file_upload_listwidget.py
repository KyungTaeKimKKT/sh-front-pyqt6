from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import sip

from modules.PyQt.User.drag_drop import Drag_Drop_Files
from modules.PyQt.component.ui.Ui_file_listwidget import Ui_Form
from modules.PyQt.User.file_viewer import FileViewer

import urllib
import datetime
import json
from pathlib import Path
import urllib.parse

import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class File_Upload_ListWidget(QWidget, Ui_Form, Drag_Drop_Files) :
	"""
		newFiles_key는 [('첨부file_fks', <_io.BufferedReader name='/home/kkt/Downloads.xlsx'>)] 에서
		'첨부file_fks'에 해당됨
	"""
	
	signal = pyqtSignal(object)

	def __init__(self, parent:QWidget|None=None, newFiles_key:str='첨부file_fks', initialData:list=[]) :
		super().__init__(parent)
		self.initialData = initialData
		self.displayData = []
		self._data = []
		self.is_ReadOnly = False
		self.newFiles_key = newFiles_key 
		self.drop_filePaths = []

		self.setupUi(self)

		if len(initialData) : self._render_initialData()
		self.TriggerConnect()
		self.setAcceptDrops(True)

	def _render_initialData(self):
		self._setValue(self.initialData)

	def eventFilter(self, source, event:QEvent):
		if (event.type() == QEvent.Type.ContextMenu and
			source is self.listWidget):
			menu = QMenu()
			action_view = menu.addAction('view')
			curItemRowNo = self.listWidget.currentRow()
			action_view.setVisible( bool( Utils.check_file확장자_view지원 (self.listWidget.item(curItemRowNo).text() )) )

			action = menu.exec(event.globalPos())
			if action == action_view:
				obj =  self._data[curItemRowNo]
				fileViewer = FileViewer(self, self.get_fileViewer_dataDict(obj, curItemRowNo ))
				fileViewer.run()
				# if not fileViewer.run():
				# 	QMessageBox.warning( self, '지원하지 않는 file형식', '지원하지 않는 file형식입니다.' )
			
		return super().eventFilter(source, event)
	def get_fileViewer_dataDict(self, obj:object, curItemRowNo:int ) -> dict:
		if isinstance ( obj, dict ):
			return {'url':obj.get('file')}
		elif isinstance ( obj, tuple):
			return {'file': str(self.listWidget.item(curItemRowNo).text()).split(':')[1].strip() }

	
	def dropEvent(self, event:QDropEvent):
		""" dropEvent super method로 사용"""
		file_paths = []
		if event.mimeData().hasUrls():
			event.setDropAction(Qt.CopyAction)
			file_paths = [ url.toLocalFile() for url in event.mimeData().urls() ]
			event.accept()
			self._update_fNames( file_paths )
		else:
			event.ignore()


	def TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.connect(self.chkItemClicked)
		self.listWidget.itemDoubleClicked.connect(self.chkItemDoubleClicked)
		self.listWidget.currentItemChanged.connect(self.chkCurrentItemChanged)

		#버튼에 기능 연결
		self.PB_Upload.clicked.connect(self.slot_PB_Upload_multiple)
		self.PB_Delete.clicked.connect(self.slot_pb_delete_attachfile)

		# 😀install EventFilter
		self.listWidget.installEventFilter(self)
	
	def No_TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.disconnect()
		self.listWidget.itemDoubleClicked.disconnect()
		self.listWidget.currentItemChanged.disconnect()

		#버튼에 기능 연결
		self.PB_Upload.clicked.disconnect()
		self.PB_Delete.clicked.disconnect()

	def _getValue(self) -> dict:
		list_contents = {}
		itemsTextList =  [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]
		for i, text in enumerate(itemsTextList):
			list_contents[i] = text

		exist_DB_id = []
		new_DB = []
		for item in self._data:
			if isinstance(item, dict):
				exist_DB_id.append( item.get('id'))
			elif isinstance(item, tuple) :
				new_DB.append( item )

		return {
			'exist_DB_id' : exist_DB_id,
			'new_DB' : new_DB
		}
	
	def _setValue(self, 첨부file_fks:list, key:str='file') -> None:
		""" list는 dict list, default key는 'file' """
		if not 첨부file_fks : return
		self._data +=  첨부file_fks
		self._displayValue(key)
	
	def _setReadOnly(self):
		self.PB_Upload.setDisabled(True)
		self.PB_Delete.setDisabled(True)
		self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.No_TriggerConnect()

		
	def _displayValue(self, key:str='file'):
		for idx, obj in enumerate(self._data):
			fName = obj.get(key).split('/')[-1]
			self.listWidget.addItem(f"{idx}  :{urllib.parse.unquote(fName)}")

	#ListWidget의 시그널에 연결된 함수들
	def chkItemClicked(self) :
		if ( curItem := self.listWidget.currentItem() ):
			self.PB_Delete.setEnabled(True)
		else:
			self.PB_Delete.setEnabled(False)

	def chkItemDoubleClicked(self) :
		return


	def chkCurrentItemChanged(self) :
		return 

	
	def func_fileupload_checkITemClicked(self):
		if (curItem := self.listWidget.currentItem() ):
			self.PB_Delete.setEnabled(True)
		else:
			self.PB_Delete.setEnabled(False)

	#항목을 추가, 삽입하는 함수들
	def slot_PB_Upload_multiple(self):
		self.fNames, filter = QFileDialog.getOpenFileNames(self, 'Open file', 
			str(Path.home() / "Downloads"), '*.*(*.*)')
		self._update_fNames( self.fNames)

	def _update_fNames(self, fNames:list=[]) -> None:
		if fNames:
			files_list=[]
			for idx, fName in enumerate(fNames):
				self.listWidget.addItem(f"{idx}  : {fName}")
			self._data += [(self.newFiles_key ,open(f,'rb') ) for f in fNames ]

	def slot_pb_delete_attachfile(self):
	   #ListWidget에서 현재 선택한 항목을 삭제할 때는 선택한 항목의 줄을 반환한 후, takeItem함수를 이용해 삭제합니다. 
		removeItemRow:int = self.listWidget.currentRow()
		self.listWidget.takeItem(removeItemRow )
		self.func_fileupload_checkITemClicked()
		self._data.pop(removeItemRow)



	def insertListWidget(self) :
		self.insertRow = self.spin_insertRow.value()
		self.insertText = self.line_insertItem.text()
		self.listWidget.insertItem(self.insertRow, self.insertText)

	def saveList(self):
		list_contents = {}
		itemsTextList =  [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]
		for i, text in enumerate(itemsTextList):
			list_contents[i] = text

		with open('data.json', 'w', encoding='utf-8') as fp:
			json.dump(list_contents, fp)

	#Button Function
	def upCurrentItem(self):
		currentRow = self.listWidget.currentRow()
		currentItem = self.listWidget.takeItem(currentRow)
		self.listWidget.insertItem(currentRow - 1, currentItem)
		self.listWidget.setCurrentItem(currentItem)

	def downCurrentItem(self):
		currentRow = self.listWidget.currentRow()
		currentItem = self.listWidget.takeItem(currentRow)
		self.listWidget.insertItem(currentRow + 1, currentItem)
		self.listWidget.setCurrentItem(currentItem)

	def printCurrentItem(self) :
		return


	def printMultiItems(self) :
		#여러개를 선택했을 때, selectedItems()를 이용하여 선택한 항목을 List의 형태로 반환받읍니다.
		#그 후, for문을 이용하여 선택된 항목을 출력합니다.
		#출력할 때, List안에는 QListWidgetItem객체가 저장되어 있으므로, .text()함수를 이용하여 문자열로 변환해야 합니다.
		self.selectedList = self.listWidget.selectedItems()
		for i in self.selectedList :
			pass


	def removeCurrentItem(self) :
		#ListWidget에서 현재 선택한 항목을 삭제할 때는 선택한 항목의 줄을 반환한 후, takeItem함수를 이용해 삭제합니다. 
		self.removeItemRow = self.listWidget.currentRow()
		self.listWidget.takeItem(self.removeItemRow)

	def clearItem(self) :
		self.listWidget.clear()


		###############################################################   
	def deleteLayout(self, cur_lay):
		# QtWidgets.QLayout(cur_lay)
		try:

			if cur_lay is not None:
				while cur_lay.count():
					item = cur_lay.takeAt(0)
					widget = item.widget()
					if widget is not None:
						widget.deleteLater()
					else:
						self.deleteLayout(item.layout())
				sip.delete(cur_lay)
		except Exception as e:
			logger.error(traceback.format_exc())
	#####################################