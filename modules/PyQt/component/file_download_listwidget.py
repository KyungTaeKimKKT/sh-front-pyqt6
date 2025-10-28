import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6 import sip

import modules.user.utils as Utils

import urllib
import datetime
import json
from pathlib import Path
import urllib.parse

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()
# form_class = uic.loadUiType("listwidgetTest_1.ui")[0]

class File_Download_ListWidget(QWidget) :
	"""
		list widget에서 filedownload
		initial Data:예시
		modules/PyQt6/component/file_upload_listwidget.py
 		[{'id': 4, 'file': 'http://192.168.7.108:9999/media/%ED%92%88%EC%A7%88%EA%B2%BD%EC%98%81/%EC%B2%98%EB%A6%AC%ED%98%84%ED%99%A9/%EC%B2%A8%EB%B6%80%ED%8C%8C%EC%9D%BC/2024-7-26/9bcd8f98-46e3-4476-b387-249b00ae7759/testforapi.csv'}]
	"""
	
	signal = pyqtSignal(object)

	def __init__(self, parent:QWidget|None=None, initialData:list=[], key:str='file') :
		super().__init__(parent)
		self.initialData = initialData
		self._data = initialData
		self.urls:list = [ obj.get(key) for obj in self._data]
		self.is_ReadOnly = True
		self.key = key

		self.UI()

		if len(initialData) : self._render_initialData()
		self.TriggerConnect()

	def UI(self):            
		if hasattr( self, 'vLayout' ) : self.deleteLayout(self.mainLayout)

		self.mainLayout = QVBoxLayout(self)
		self.mainLayout.setObjectName(u"vLayout")

		self.listWidget = QListWidget(self)
		self.listWidget.setObjectName(u"listWidget_Test")
		self.listWidget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
		# self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
		self.listWidget.setWordWrap(False)

		self.mainLayout.addWidget(self.listWidget)

		hLayout = QHBoxLayout()
		hLayout.addStretch()
		self.pb_FileDownload = QPushButton(self)
		self.pb_FileDownload.setObjectName("pb_FileDownload")
		self.pb_FileDownload.setText("첨부파일 Download")
		self.pb_FileDownload.setEnabled(False)

		hLayout.addWidget(self.pb_FileDownload)

		self.mainLayout.addLayout(hLayout)

		self.setLayout(self.mainLayout)

	def _render_initialData(self):
		self._setValue(self.initialData)

	def TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.connect(self.chkItemClicked)
		self.listWidget.itemDoubleClicked.connect(self.chkItemDoubleClicked)
		self.listWidget.currentItemChanged.connect(self.chkCurrentItemChanged)

		#버튼에 기능 연결
		self.pb_FileDownload.clicked.connect(self.slot_pb_fileDownload_multiple)

	
	def No_TriggerConnect(self):
		#ListWidget의 시그널
		self.listWidget.itemClicked.disconnect()
		self.listWidget.itemDoubleClicked.disconnect()
		self.listWidget.currentItemChanged.disconnect()

		#버튼에 기능 연결
		self.pb_FileDownload.clicked.disconnect()


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
	
	def _setValue(self, file_fks:list) -> None:
		if not file_fks : return
		# self._data +=  file_fks
		self._displayValue()
	
	def _setReadOnly(self):
		self.pb_FileDownload.setDisabled(True)
		self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
		# self.No_TriggerConnect()

		
	def _displayValue(self):
		for idx, obj in enumerate(self._data):
			self.listWidget.addItem(f"{idx}  :{Utils.get_fName_from_url( obj.get(self.key))}")

	#ListWidget의 시그널에 연결된 함수들
	def chkItemClicked(self) :
		if self.listWidget.selectedItems() :
			self.pb_FileDownload.setEnabled(True)
		else:
			self.pb_FileDownload.setEnabled(False)

	def chkItemDoubleClicked(self) :
		pass

	def chkCurrentItemChanged(self) :
		pass

	

	#항목을 추가, 삽입하는 함수들
	def slot_pb_fileDownload_multiple(self):
		seletecItems = self.listWidget.selectedItems()
		for item in seletecItems:
			index = int((item.text().split(':')[0]).strip())
			Utils.func_filedownload ( url = self.urls[index])


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
		pass


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