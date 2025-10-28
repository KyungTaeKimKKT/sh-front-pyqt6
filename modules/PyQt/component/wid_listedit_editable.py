from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import json

from modules.PyQt.component.ui.Ui_listwidget_editable import Ui_Form
# from ui.Ui_listwidget_editable import Ui_Form
import modules.user.utils as Utils
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger


Sample_소재Size_Widget_items = ['1.5T*150*150', '1.5T*300*300', '기타']	


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_ListEditable_생지_치수(QWidget, Ui_Form):
	
	signal_Input = pyqtSignal(dict)

	def __init__(self,parent=None):
		super().__init__(parent)
		self.setupUi(self)
		# self.show()

	
	def _render(self, widget, index):
		self.widget = widget
		self.index = index
		if hasattr( self, 'vLayout') : Utils.deleteLayout(self.vLayout)
		self.setupUi(self)
		self.items = Sample_소재Size_Widget_items
		self.listWidget.addItems(self.items)
		self.listWidget.setWordWrap(True)
		self.listWidget.installEventFilter(self)

		# self._setDefault()  
		# self._setValidator()
		# self.line.hide()
		self.triggerConnect()

	def eventFilter(self, source, event:QEvent):
		# if (event.type() == QEvent.Type.ContextMenu and
		# 	source is self.listWidget):
		# 	menu = QMenu()
		# 	action_view = menu.addAction('view')
		
		# 	action = menu.exec(event.globalPos())
		return super().eventFilter(source, event)
	
	def triggerConnect(self):
		self.PB_Save.clicked.connect ( self.on_PB_Save_clicked )
		self.PB_Input.clicked.connect (self.on_PB_Input_clicked)
		self.PB_Delete.clicked.connect(self.on_PB_Delete_clicked)
		self.PB_Append.clicked.connect(self.on_PB_Append_clicked)
		#ListWidget의 시그널
		self.listWidget.itemClicked.connect(self.slot_itemClicked)
		self.listWidget.itemDoubleClicked.connect(self.slot_itemDoubleClicked)
		self.listWidget.currentItemChanged.connect(self.slot_currentItemChanged)

	# def dragEnterEvent(self, event:QDragEnterEvent):

	
	# 	if event.mimeData().hasUrls():
	# 		event.accept()
	# 	else:
	# 		event.ignore()

	# def dragMoveEvent(self, event:QDragMoveEvent):


	# 	if event.mimeData().hasUrls():
	# 		event.accept()
	# 	else:
	# 		event.ignore()

	# def dropEvent(self, event:QDropEvent):
	# 	""" dropEvent super method로 사용"""


	# 	# if event.mimeData().hasUrls():
	# 	# 	event.setDropAction(Qt.CopyAction)
	# 	# 	file_paths = [ url.toLocalFile() for url in event.mimeData().urls() ]
	# 	# 	event.accept()
	# 	# 	self._update_fNames( file_paths )
	# 	# else:
	# 	# 	event.ignore()

	@pyqtSlot()
	def on_PB_Input_clicked(self):
		self.signal_Input.emit( self._get_msg( self._get_Chisu() ) )
		self.close()

	@pyqtSlot()
	def on_PB_Append_clicked(self):
		new_item = self._get_Chisu()
		if new_item not in self.items:
			self.items.append(new_item )
			self.listWidget.addItem(new_item)

	@pyqtSlot()
	def on_PB_Delete_clicked(self):
		curRowNo:int = self.listWidget.currentRow()
		self.listWidget.takeItem(curRowNo )
		self.items.pop(curRowNo)

	@pyqtSlot()
	def on_PB_Save_clicked(self):		

		updateDict = {
			'list_items' : json.dumps( self.items, ensure_ascii=False ),
		}




	#ListWidget의 시그널에 연결된 함수들
	@pyqtSlot()
	def slot_itemClicked(self) :
		curItem = self.listWidget.currentItem()
		if curItem :
			self.PB_Delete.setEnabled(True)
		else:
			self.PB_Delete.setEnabled(False)

	@pyqtSlot()
	def slot_itemDoubleClicked(self) :
		curItem = self.listWidget.currentItem()
		self.signal_Input.emit( self._get_msg ( curItem.text()) )
		self.close()

	@pyqtSlot()
	def slot_currentItemChanged(self) :
		curItem = self.listWidget.currentItem()


	### methods
	def _get_Chisu(self) -> str:
		두께 = self.double_depth.value()
		가로 = self.spin_width.value()
		세로 = self.spin_height.value()
		return f"{두께:.2f}T*{가로}*{세로}"
							
	def _get_msg(self, 치수txt) -> dict:
		""" emit msg:dict { index: self.index, 치수:치수txt} 를 return"""
		return {
			'widget' : self.widget,
			'index' : self.index,
			'치수' :  치수txt,
		}


if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	w = Wid_ListEditable_생지_치수()
	w.show()
	sys.exit(app.exec())