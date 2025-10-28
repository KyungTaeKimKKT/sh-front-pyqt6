from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import traceback
from modules.logging_config import get_plugin_logger



# https://stackoverflow.com/questions/8707457/pyqt-editable-qtabwidget-tab-text

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class TabBar_Custom(QTabBar):
	signal_delete = pyqtSignal(int)

	def __init__(self, parent):
		super().__init__(parent)
		self._editor = QLineEdit(self)
		self._editor.setWindowFlags(Qt.Popup)
		self._editor.setFocusProxy(self)
		self._editor.editingFinished.connect(self.handleEditingFinished)
		self._editor.installEventFilter(self)

	def eventFilter(self, widget, event):
		if ((event.type() == QEvent.MouseButtonPress and
			 not self._editor.geometry().contains(event.globalPos())) or
			(event.type() == QEvent.KeyPress and
			 event.key() == Qt.Key_Escape)):
			self._editor.hide()
			return True
		return super().eventFilter(widget, event)
	
	# 출처: https://freeprog.tistory.com/334 [취미로 하는 프로그래밍 !!!:티스토리]
	def contextMenuEvent(self, event):

		menu = QMenu(self)
		delete_action = menu.addAction("삭제하기")

		if self.currentIndex() :
			action = menu.exec_(self.mapToGlobal(event.pos()))
			if action == delete_action:
				self.signal_delete.emit(self.currentIndex())


	def mouseDoubleClickEvent(self, event):
		index = self.tabAt(event.pos())
		if index >= 0:
			self.editTab(index)

	def editTab(self, index):
		rect = self.tabRect(index)
		self._editor.setFixedSize(rect.size())
		self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
		self._editor.setText(self.tabText(index))
		if not self._editor.isVisible():
			self._editor.show()

	def handleEditingFinished(self):
		index = self.currentIndex()
		if index >= 0:
			self._editor.hide()
			self.setTabText(index, self._editor.text())
