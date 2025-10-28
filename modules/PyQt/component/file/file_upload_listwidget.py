from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import sip

from modules.PyQt.User.drag_drop import Drag_Drop_Files
from modules.PyQt.component.file.ui.Ui_file_listwidget import Ui_Form
from modules.PyQt.User.file_viewer import FileViewer

import urllib
import datetime
import json
from pathlib import Path
import urllib.parse

import modules.user.utils as Utils

import logging, traceback
logger = logging.getLogger(__name__)

class File_Upload_ListWidget(QWidget, Drag_Drop_Files) :
	"""
		list를 받아서, list 로 return
		parent widget에서 method _getValue()로 data 가져가서 처리함.
		*** old임: newFiles_key는 [('첨부file_fks', <_io.BufferedReader name='/home/kkt/Downloads.xlsx'>)] 에서
		'첨부file_fks'에 해당됨
	"""
	
	# signal = pyqtSignal(object)

	def __init__(self, parent, **kwargs ) : #newFiles_key:str='첨부file_fks', initialData:list=[]) :
		super().__init__(parent)
		self.is_ReadOnly:bool = False
		self.drop_filePaths = []
		self.display_dict :dict[int:str] = {}	## id : fName
		self.newCount = -1

		for key, value in kwargs.items():
			setattr(self, key, value )

		self.ui = Ui_Form()
		self.ui.setupUi(self)

		self.TriggerConnect()
		self.setAcceptDrops(True)

	def _update_attribute(self, **kwargs):
		for k, v in kwargs.items():
			setattr( self, k, v)
		if hasattr(self, 'display_dict') and self.display_dict:
			self._displayValue(dataList=self.display_dict.values())

	def eventFilter(self, source, event:QEvent):
		if (event.type() == QEvent.Type.ContextMenu and
			source is self.ui.listWidget):
			menu = QMenu()
			action_view = menu.addAction('view')
			curItemRowNo = self.ui.listWidget.currentRow()
			action_view.setVisible( bool( Utils.check_file확장자_view지원 (self.ui.listWidget.item(curItemRowNo).text() )) )

			action = menu.exec(event.globalPos())
			if action == action_view:
				obj =  self._data[curItemRowNo]
				fileViewer = FileViewer(self, self.get_fileViewer_dataDict(obj, curItemRowNo ))
				fileViewer.run()
				# if not fileViewer.run():
				# 	QMessageBox.warning( self, '지원하지 않는 file형식', '지원하지 않는 file형식입니다.' )
			
		return super().eventFilter(source, event)
	
	
	def dropEvent(self, event:QDropEvent):
		""" dropEvent super method로 사용"""
		file_paths = []
		if event.mimeData().hasUrls():
			event.setDropAction(Qt.DropAction.CopyAction)
			file_paths = [ url.toLocalFile() for url in event.mimeData().urls() ]
			event.accept()
			self._update_fNames( file_paths )
		else:
			event.ignore()


	def TriggerConnect(self):
		#ListWidget의 시그널
		self.ui.listWidget.itemClicked.connect(self.chkItemClicked)
		self.ui.listWidget.itemDoubleClicked.connect(self.chkItemDoubleClicked)
		self.ui.listWidget.currentItemChanged.connect(self.chkCurrentItemChanged)

		#버튼에 기능 연결
		self.ui.PB_Upload.clicked.connect(self.slot_PB_Upload_multiple)
		self.ui.PB_Delete.clicked.connect(self.slot_pb_delete_attachfile)

		# 😀install EventFilter
		self.ui.listWidget.installEventFilter(self)
	
	def No_TriggerConnect(self):
		#ListWidget의 시그널
		self.ui.listWidget.itemClicked.disconnect()
		self.ui.listWidget.itemDoubleClicked.disconnect()
		self.ui.listWidget.currentItemChanged.disconnect()

		#버튼에 기능 연결
		self.ui.PB_Upload.clicked.disconnect()
		self.ui.PB_Delete.clicked.disconnect()

	def _getValue(self) -> dict[int:str]:
		""" return 
				self.display_dict = {int:fName}  \n			
		"""
		return self.display_dict
	
	def _getValue_listWidgetContents(self) -> list[QListWidgetItem]:
		list_contents = {}
		return  [self.ui.listWidget.item(i) for i in range(self.ui.listWidget.count())]

	
	def _setValue(self, dataList:list[str], **kwargs) -> None:
		""" list는 dict list, default key는 'file' """
		if len(dataList) == 0 : return
		self._data +=  dataList
		self._displayValue(dataList=self._data)
	
	def _setReadOnly(self):
		self.ui.PB_Upload.setDisabled(True)
		self.ui.PB_Delete.setDisabled(True)
		self.ui.listWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
		self.No_TriggerConnect()

		
	def _displayValue(self, dataList:list[str], **kwargs):
		self.ui.listWidget.clear()
		if len(dataList) == 0 : return

		for idx, item in enumerate(dataList):		
			if item is None : continue	
			fName = item.split('/')[-1]
			self.ui.listWidget.addItem(f"{idx}  :{urllib.parse.unquote(fName)}")

	#ListWidget의 시그널에 연결된 함수들
	def chkItemClicked(self) :
		if ( curItem := self.ui.listWidget.currentItem() ):
			self.ui.PB_Delete.setEnabled(True)
		else:
			self.ui.PB_Delete.setEnabled(False)

	def chkItemDoubleClicked(self) :
		return


	def chkCurrentItemChanged(self) :
		return 

	
	def func_fileupload_checkITemClicked(self):
		if (curItem := self.ui.listWidget.currentItem() ):
			self.ui.PB_Delete.setEnabled(True)
		else:
			self.ui.PB_Delete.setEnabled(False)

	#항목을 추가, 삽입하는 함수들
	@pyqtSlot()
	def slot_PB_Upload_multiple(self):
		fNames, filter = QFileDialog.getOpenFileNames(self, 'Open file', 
			str(Path.home() / "Downloads"), '*.*(*.*)')
		if fNames:			
			for fName in fNames:
				self.display_dict.update ({ self.newCount : fName })
				self.newCount -= 1
			self._update_attribute( display_dict = self.display_dict  )


	@pyqtSlot()
	def slot_pb_delete_attachfile(self):
	   #ListWidget에서 현재 선택한 항목을 삭제할 때는 선택한 항목의 줄을 반환한 후, takeItem함수를 이용해 삭제합니다. 
		removeItemRow:int = self.ui.listWidget.currentRow()
		self.ui.listWidget.takeItem(removeItemRow )
		self.func_fileupload_checkITemClicked()

		remove_txt = list(self.display_dict.values())[removeItemRow]
		self.display_dict = {k:v for k,v in self.display_dict.items() if v != remove_txt}
		self._update_attribute(display_dict = self.display_dict )


	def insertListWidget(self) :
		self.insertRow = self.spin_insertRow.value()
		self.insertText = self.line_insertItem.text()
		self.ui.listWidget.insertItem(self.insertRow, self.insertText)

	def saveList(self):
		list_contents = {}
		itemsTextList =  [str(self.ui.listWidget.item(i).text()) for i in range(self.ui.listWidget.count())]
		for i, text in enumerate(itemsTextList):
			list_contents[i] = text

		with open('data.json', 'w', encoding='utf-8') as fp:
			json.dump(list_contents, fp)

	#Button Function
	def upCurrentItem(self):
		currentRow = self.ui.listWidget.currentRow()
		currentItem = self.ui.listWidget.takeItem(currentRow)
		self.ui.listWidget.insertItem(currentRow - 1, currentItem)
		self.ui.listWidget.setCurrentItem(currentItem)

	def downCurrentItem(self):
		currentRow = self.ui.listWidget.currentRow()
		currentItem = self.ui.listWidget.takeItem(currentRow)
		self.ui.listWidget.insertItem(currentRow + 1, currentItem)
		self.ui.listWidget.setCurrentItem(currentItem)

	def printCurrentItem(self) :
		return


	def printMultiItems(self) :
		#여러개를 선택했을 때, selectedItems()를 이용하여 선택한 항목을 List의 형태로 반환받읍니다.
		#그 후, for문을 이용하여 선택된 항목을 출력합니다.
		#출력할 때, List안에는 QListWidgetItem객체가 저장되어 있으므로, .text()함수를 이용하여 문자열로 변환해야 합니다.
		self.selectedList = self.ui.listWidget.selectedItems()
		for i in self.selectedList :
			logger.info(f"선택된 항목: {i.text()}")

	def removeCurrentItem(self) :
		#ListWidget에서 현재 선택한 항목을 삭제할 때는 선택한 항목의 줄을 반환한 후, takeItem함수를 이용해 삭제합니다. 
		self.removeItemRow = self.ui.listWidget.currentRow()
		self.ui.listWidget.takeItem(self.removeItemRow)

	def clearItem(self) :
		self.ui.listWidget.clear()


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
			logger.error(f"Error deleting layout: {traceback.format_exc()}")

	#####################################