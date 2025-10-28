from PyQt6 import QtCore, QtGui, QtWidgets, QtPrintSupport, sip
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import pandas as pd
from pathlib import Path
import openpyxl
import copy

# import user module
from modules.PyQt.User.My_tableview import My_TableView
from modules.PyQt.ui.Ui_tabs import Ui_Tabs


from modules.PyQt.User.Tb_Model import Base_TableModel, Base_TableModel_Pandas
from modules.PyQt.User.Tb_Delegate import Base_Delegate

import modules.user.utils as utils

# from modules.PyQt.User.loading import LoadingDialog
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
# import sub window
from modules.PyQt.sub_window.win_search import Win_Search
from modules.PyQt.Tabs.Data import AppData as AppData

import inspect
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class App_TableModel(Base_TableModel):
	pass

class App_TableView(My_TableView):
	pass

class App_Delegate(Base_Delegate):
	pass

	
class Base_App(QtWidgets.QWidget):
	def __init__(self, parent:QtWidgets.QMainWindow=None, appFullName:str='', url:str='' ):
		super().__init__(parent)
		self.MainW = parent
		
		self.url = url
		self.appFullName = appFullName
		self.app_DB_data = []

		self.vlayout = QVBoxLayout()

		self.table_msg = {}
		self.header = None
		self.header_type = {}
		self.no_Edit = []

		self.search_msg = {}
		self.pageSize = 0
		self.suffix = self._get_url_suffix()

		self.defautlData = []
		# self._init_from_DataModule()

	# 😀😀😀 
	def _init_Attributes_from_DataModule(self):
		attributes = inspect.getmembers(self.appData, lambda a:not(inspect.isroutine(a)))
		attr_value_list = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
		for (attr, value) in attr_value_list:
			setattr(self, attr, value)


	def _get_app_DB_data(self, url, search_msg:dict=None):
		if not search_msg : search_msg = self.search_msg
		if search_msg:
			suffix = '?'
			for (key, value ) in search_msg.items():
				suffix += f"{key}={value}&"
			suffix += self._get_url_suffix()[1:]
		else:
			suffix = self._get_url_suffix()

		return APP.API.getlist(url+suffix)

	def _check_api_Result(self, search_msg:dict=None) -> bool:
		if self.pageSize :
			is_ok, self.app_query_result = self._get_app_DB_data(self.url, search_msg)
			if is_ok:

				self.app_DB_data = self.app_query_result.get('results')
				del self.app_query_result['results']
			# else:
			# 	User_Toast(self, text='server not connected', style='ERROR')
		else:
			is_ok, self.app_DB_data = self._get_app_DB_data(self.url, search_msg)
		return is_ok

	def _get_url_suffix(self) -> str:
		return f'?page_size={self.pageSize}'

	def get_api_and_model_table_generate(self) -> bool:
		if (is_api_ok := self._check_api_Result() ) :
			self.is_api_ok = is_api_ok

			if self.app_DB_data:
				self.model_data = self.gen_Model_data_from_API_data()

				self.model = App_TableModel( baseURL=self.url, data=self.model_data, header=self.header,
											header_type=self.header_type, no_Edit=self.no_Edit)

				tableView, vlayout = self._render_frame_MVC(App_TableView(self))
				self.table:App_TableView = self._gen_table(tableView )

				### setting table delegate
				self.delegate = App_Delegate(header=self.header, header_type=self.header_type, no_Edit=self.no_Edit)
				self.table.setItemDelegate(self.delegate)
				
				self._hide_hidden_column()

				return True
			else:
				return False
		else: 
			return False

	
	def _render_frame_MVC(self, tableView:App_TableView=None):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.vlayout.addWidget(tableView)		
		self.setLayout(self.vlayout)

		return (tableView,self.vlayout)
	
	def _render_Null_data(self):
		self.vlayout = QtWidgets.QVBoxLayout()
		self.no_data_hlayout = QtWidgets.QHBoxLayout()

		self.label = QtWidgets.QLabel('자료가 없읍니다.')
		self.no_data_hlayout.addStretch()
		self.no_data_hlayout.addWidget(self.label)
		self.no_data_hlayout.addStretch()
		self.vlayout.addLayout(self.no_data_hlayout)
		self.vlayout.addStretch()
		
		self.setLayout(self.vlayout)	


	def _hide_hidden_column(self):
		"""
			self.hidden_column 이 있으면 해당 column을
		"""
		if getattr(self, 'hidden_column', None) is None : return None

		for hidden_col_name in self.hidden_column:
			self.table.hideColumn( self.header.index(hidden_col_name))

	def _init_sub_Window(self):
		self.win_search = Win_Search(self)
		self.win_search.hide()
		self.win_search.signal.connect(lambda:self.slot_win_search())
			

	def editMode(self):
		# self.no_Edit = self.header
		self.run()

	def viewMode(self):
		self.run()
		if hasattr(self, 'model'):
			self.model.no_Edit = self.header


	def signal_Connect(self):
		self.model.sig_update.connect (self.slot_model_update)
	
	############################################
	#### slots
	@QtCore.pyqtSlot()
	def slot_model_update(self):
		self.table.resizeRowsToContents()

	###############################

	def _gen_table(self, table:App_TableView):
		table.setModel(self.model)
		if hasattr(self, 'table_col_width'):
			self.table = table
			self._resizeTable()

		else:
			table.resizeColumnsToContents()
			table.resizeRowsToContents()
		# https://stackoverflow.com/questions/38098763/pyside-pyqt-how-to-make-set-qtablewidget-column-width-as-proportion-of-the-a
		header = table.horizontalHeader()       
		# header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
		return table

	def _resizeTable(self):
		for colNo, headName in enumerate(self.header):
			if '수량' in headName: 
				self.table.setColumnWidth( colNo, self.table_col_width.get('수량') ) 
			else:
				if ( width:= self.table_col_width.get(headName, None) ) :
					self.table.setColumnWidth( colNo, width)
				else:
					self.table.resizeColumnToContents( colNo)
		self.table.resizeRowsToContents()
		# self.table.resizeColumnsToContents()


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
			logger.error(f"deleteLayout 오류: {e}")
			logger.error(f"{traceback.format_exc()}")



	#### table signal : self.signal.emit( {'action':'handle_new_form'})
	def slot_table_siganl(self,msg:dict):
		actionName = msg.get('action').lower()
		if ( data := msg.get('data', None) ):
			row = data.get('row', -1)
		match actionName:
			case 'form_edit'|'Form_Edit':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.handle_form_edit(row)	

			case 'form_view'|'Form_View':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.handle_form_view(row)				

			case 'new':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					self.insert_app_DB_data(row)					
					self.table.model().layoutChanged.emit()

			case 'delete':
				if isinstance( (row := msg.get('data').get('row') ) , int) :
					if ( ID := self._get_ID(row) ) >0:
						msgBox = QtWidgets.QMessageBox.warning(
										self, 'DB에서 삭제', "DB에서 영구히 삭제됩니다.", 
										QtWidgets.QMessageBox.Yes |  QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
										)
						if msgBox == QtWidgets.QMessageBox.Yes:
							is_ok = APP.API.delete(self.url+str(ID)+'/')		
							if is_ok:
								self.model_data.pop(row)
								self.table.model().layoutChanged.emit()
							else:
								pass						
						else:
							return
					else:
						self.model_data.pop(row)
						self.table.model().layoutChanged.emit()

			case 'set_row_span':
				if isinstance( (col := msg.get('data').get('col') ) , int) :					
					self.handle_row_span('set', col)			
			
			case 'reset_row_span':
				if isinstance( (col := msg.get('data').get('col') ) , int) :					
					self.handle_row_span('reset', col)

			case '작성완료':
				if isinstance( row , int) and row > -1 :
					if ( ID := self._get_ID(row) ) >0:
						reply = QMessageBox.question(
							self, actionName, '배포하시겠습니까?', QMessageBox.Yes |  QMessageBox.Cancel, QMessageBox.Cancel
						)
						if reply == QMessageBox.Yes:
							is_ok = APP.API.patch(
											url = self.url+str(ID)+'/', 
											data= { '진행현황':'배포',				  									
													'is_배포': True})		
							if is_ok:
								self.run()
							else:
								toast = User_Toast(self, text='server not connected', style='ERROR')						
						else:
							return
			case 'File첨부'|'file첨부':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_file첨부(self.selectedDataObj )
			case '완료처리':
				if isinstance( row , int) and row > -1 :
					self.selectedDataObj =  copy.deepcopy( self.app_DB_data[row])
					self.handle_완료처리(self.selectedDataObj )
			case 'mrp'|'MRP':
				rows_list = msg.get('data').get('rows')
				if isinstance(rows_list, list) :
					self.handle_MRP(  [self.app_DB_data[row] for row in rows_list ] )


			case _:
				self.user_defined_table_signal_handler( msg )
				
				
	def user_defined_table_signal_handler(self, msg:dict):
		actionName = msg.get('action').lower()
		match actionName:
			case _:
				eval(f"self.{actionName}()")


	### 사용자 변경 message 일 뿐 ####
	def slot_app_User_Management(self, msg:dict):
		if self._check_api_Result():
			self.model_data = self.gen_Model_data_from_API_data()
			self.model._data  = self.model_data
			self.table.model().layoutChanged.emit()
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')


	def slot_win_search(self, msg:dict):
		if self._check_api_Result(search_msg=msg):
			self.model_data = self.gen_Model_data_from_API_data()
			if self.model_data:
				self.model._data  = self.model_data
				self.table.model().layoutChanged.emit()
			else:
				msgBox = QtWidgets.QMessageBox.warning(
						self, '검색결과가 없읍니다.', "검색결과가 없읍니다.", 
						QtWidgets.QMessageBox.Yes
						)

		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')


	def handle_search(self):
		self.win_search = Win_Search(self)
		self.win_search.show()
		## base.py에 method로
		self.win_search.signal.connect(self.slot_win_search)


		########## Handlers ########
	def handle_row_span(self, action:str, col):
		self.my_span_checker(action, self.model_data, self.table, col)

	### hard coding 😀
	def getObj_from_appData(self, row) -> dict:
		curData_ID = int(self.model_data[row][0])
		for obj in self.app_DB_data:
			if int(obj.get('id')) == curData_ID:
				return obj


	def handle_print(self):
		dialog = QtPrintSupport.QPrintDialog()
		if dialog.exec_() == QtWidgets.QDialog.Accepted:
			pass
			# self.editor.document().print_(dialog.printer())

	def handle_print_preview(self):
		dialog = QtPrintSupport.QPrintPreviewDialog()
		dialog.paintRequested.connect(self.print_image)
		dialog.exec_()

	def handle_export_to_excel(self):
		# if not self.isWindowModified():
		# 	return
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		fName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
			"Save File", str(Path.home() / "Downloads"), 
			"Excel Files(*.xlxs)", options = options)

		if fName:

			self.save_to_excel(fName=fName+'.xlsx')


	#### functions
	def print_image(self, printer):
		painter = QtGui.QPainter()
		painter.begin(printer)
		painter.setPen(Qt.red)
		painter.drawPixmap(0, 0, self.capture_mainWindow() )
		painter.end()

	# https://stackoverflow.com/questions/51361674/is-there-a-way-to-take-screenshot-of-a-window-in-PyQt6-or-qt5
	# windows Ok???😀😀
	def capture_mainWindow(self):
		screen = QtWidgets.QApplication.primaryScreen()
		screenshot = screen.grabWindow( self.winId() )
		# screenshot.save('shot.jpg', 'jpg')
		return screenshot


	def save_to_excel(self, fName):
		df = pd.DataFrame(self.app_DB_data, columns=self.header)
		df = df.drop(columns=self.hidden_column)
		df.to_excel(fName, index=False)


	def open_link(self, url:str) -> None:
		if len(url) :			 
			QDesktopServices.openUrl(QUrl(url))


	def my_span_checker(self, action:str, my_data, table:App_TableView,colNo:int):
		match action:
			case 'set':
				# rows =len(my_data)
				row_span_cnt = 0
				for idx, row in enumerate(my_data):
					if idx < row_span_cnt: continue
					my_item_count = 0
					my_label = row[colNo]
					for row_rest in my_data[idx:]:
						if row_rest[colNo] == my_label:
							my_item_count += 1
						else: break
					if my_item_count != 1:
						table.setSpan(idx, colNo, my_item_count, 1)
						row_span_cnt += my_item_count

			case 'reset':
				for idx, row in enumerate(my_data):
					# QTableView::setSpan: single cell span won't be added
					table.setSpan(idx, colNo, 1, 1)


	def insert_app_DB_data(self, row) ->None:
		copyData:list = self.model_data[row]
		appendData = []
		for (key, value) in zip(self.header, copyData):
			appendData.append( self._gen_default_value(key, value))

		self.model_data.insert(row+1, appendData )

	def _gen_default_value(self, key, value):
		match key:
			case 'id':	return -1
			case 'name'| 'url'|'api_url' : return value
			case 'is_Active', 'is_Run' : return False
			case '순서' : return value+1
			# case 'user_pks': return [1]
			case _:
				return ''
			
	
	def gen_Model_data_from_API_data(self) ->list:  		
		self.header = self._get_header()
		_data = []
		for obj in self.app_DB_data:
			_data.append ( [ self._get_Name(key, obj) if key != 'file' else 'file' for key in self.header ] )
		return _data
			
	def _get_ID(self, row:int) ->int:
		col = self.header.index('id')
		return int(self.model_data[row][col])		
	
	def _get_header(self) ->list:
		if self.header is not None: return self.header
		data = self.app_DB_data
		if bool(self.header_type):
			return list(self.header_type.keys() )
		else:
			return list(data[0].keys() ) if len(data) else [] #if len(data) else self.defaultDict.keys()


	def _get_Name(self, key:str, obj:dict) ->str:
		""" key는 self.header , obj는 app_DB_data """
		value = obj.get(key , None)
		match key:
			# case 'OS':
			#     return self.OS_dict.get(value)
			# case '종류':
			#     return self.종류_dict.get(value)
			case _:
				return value
			
	def _gen_default_value(self, key, value):
		match key:
			case 'id':	return -1
			case '일자' : return value
			case _:
				return ''