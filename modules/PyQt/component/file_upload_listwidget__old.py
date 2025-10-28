import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6 import sip

import urllib
import datetime
import json
from pathlib import Path
import urllib.parse

# form_class = uic.loadUiType("listwidgetTest_1.ui")[0]

class File_Upload_ListWidget(QWidget) :
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

		self.UI()

		if len(initialData) : self._render_initialData()
		self.TriggerConnect()
		self.newFiles_key = newFiles_key 

	def UI(self):            
		if hasattr( self, 'vLayout' ) : self.deleteLayout(self.mainLayout)

		self.mainLayout = QVBoxLayout(self)
		self.mainLayout.setObjectName(u"vLayout")

		self.listWidget = QListWidget(self)
		self.listWidget.setObjectName(u"listWidget_Test")
		self.listWidget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
		self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		# self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
		self.listWidget.setWordWrap(False)

		self.listWidget.installEventFilter(self)

		self.mainLayout.addWidget(self.listWidget)

		hLayout = QHBoxLayout()

		self.pb_FileUpload = QPushButton(self)
		self.pb_FileUpload.setObjectName("pb_FileUpload")
		self.pb_FileUpload.setText("첨부파일 Upload")
		self.pb_FileUpload.setAutoDefault(False)

		self.pb_DeleteList = QPushButton(self)
		self.pb_DeleteList.setObjectName("pb_DeleteList")
		self.pb_DeleteList.setText("첨부파일 Delete")
		self.pb_DeleteList.setEnabled(False)
		self.pb_DeleteList.setAutoDefault(False)

		hLayout.addWidget(self.pb_FileUpload)
		hLayout.addWidget(self.pb_DeleteList)

		self.mainLayout.addLayout(hLayout)

		self.setLayout(self.mainLayout)

	def _render_initialData(self):
		self._setValue(self.initialData)

	def eventFilter(self, source, event:QEvent):
		if (event.type() == QEvent.ContextMenu and
			source is self.listWidget):
			menu = QMenu()
			action_view = menu.addAction('view')
			if (curItemRowNo := self.listWidget.currentRow() ) < 0 :
				action_view.setVisible(False)

			action = menu.exec_(event.globalPos())
			if action == action_view:
				obj =  self._data[curItemRowNo]
				# from modules.PyQt.User.pdf.pdf_viewer_ import MainWindow as Pdf_Viewer
				from modules.PyQt.User.pdf_viewer import Pdf_Viewer				
				# curItemRowNo:int = self.listWidget.currentRow()
				if isinstance ( obj, dict ):
					pdf = Pdf_Viewer(self, {'url':obj.get('file')})
				elif isinstance ( obj, tuple):
					fName = str(self.listWidget.item(curItemRowNo).text()).split(':')[1].strip()
					pdf = Pdf_Viewer ( self, {'file' : fName })
			
		return super().eventFilter(source, event)

	def TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.connect(self.chkItemClicked)
		self.listWidget.itemDoubleClicked.connect(self.chkItemDoubleClicked)
		self.listWidget.currentItemChanged.connect(self.chkCurrentItemChanged)

		#버튼에 기능 연결
		self.pb_FileUpload.clicked.connect(self.slot_pb_fileupload_multiple)
		self.pb_DeleteList.clicked.connect(self.slot_pb_delete_attachfile)
	
	def No_TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.disconnect()
		self.listWidget.itemDoubleClicked.disconnect()
		self.listWidget.currentItemChanged.disconnect()

		#버튼에 기능 연결
		self.pb_FileUpload.clicked.disconnect()
		self.pb_DeleteList.clicked.disconnect()

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
		self.pb_FileUpload.setDisabled(True)
		self.pb_DeleteList.setDisabled(True)
		self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.No_TriggerConnect()

		
	def _displayValue(self, key:str='file'):
		for idx, obj in enumerate(self._data):
			fName = obj.get(key).split('/')[-1]
			self.listWidget.addItem(f"{idx}  :{urllib.parse.unquote(fName)}")

	#ListWidget의 시그널에 연결된 함수들
	def chkItemClicked(self) :
		if ( curItem := self.listWidget.currentItem() ):
			self.pb_DeleteList.setEnabled(True)
		else:
			self.pb_DeleteList.setEnabled(False)

	def chkItemDoubleClicked(self) :


	def chkCurrentItemChanged(self) :

	
	def func_fileupload_checkITemClicked(self):
		if (curItem := self.listWidget.currentItem() ):
			self.pb_DeleteList.setEnabled(True)
		else:
			self.pb_DeleteList.setEnabled(False)

	#항목을 추가, 삽입하는 함수들
	def slot_pb_fileupload_multiple(self):
		self.fNames, filter = QFileDialog.getOpenFileNames(self, 'Open file', 
			str(Path.home() / "Downloads"), '*.*(*.*)')
		if self.fNames:
			files_list=[]
			for idx, fName in enumerate(self.fNames):
				self.listWidget.addItem(f"{idx}  : {fName}")
			self._data += [(self.newFiles_key ,open(f,'rb') ) for f in self.fNames ]


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


	def printMultiItems(self) :
		#여러개를 선택했을 때, selectedItems()를 이용하여 선택한 항목을 List의 형태로 반환받읍니다.
		#그 후, for문을 이용하여 선택된 항목을 출력합니다.
		#출력할 때, List안에는 QListWidgetItem객체가 저장되어 있으므로, .text()함수를 이용하여 문자열로 변환해야 합니다.
		self.selectedList = self.listWidget.selectedItems()
		for i in self.selectedList :


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

	#####################################