from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import copy, traceback, logging

from modules.webEngine.googlemap.goolge_map_dialog import Google_Map_Dialog
from modules.PyQt.dialog.confirm.confirm import Dialog_Confirm

from config import Config as APP
from info import Info_SW as INFO
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Handle_Table_Menu:
	""" 
	tableview 에서 오는 signal 처리
	wid_table에 sub class로 상속처리
	signal은 세 종류로,
		signal_vMenu = QtCore.pyqtSignal(dict)
		signal_hMenu = QtCore.pyqtSignal(dict)
		signal_cellMenu = QtCore.pyqtSignal(dict)
	
	"""	

	def __init__(self, **kwargs): 
		pass

	@pyqtSlot(dict)
	def slot_signal_vMenu(self, msg:dict) -> None:
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : colNo, """
		
		actionName = msg.get('action')
		match actionName:

			
			case _:
				eval( f"self.menu__{actionName}(msg)")

	@pyqtSlot(dict)
	def slot_signal_hMenu(self, msg:dict) -> None:
		
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : colNo, 
		"""
		actionName = msg.get('action')

		match actionName:
			
			case _:
				eval( f"self.menu__{actionName}(msg)")
	
	@pyqtSlot(dict)
	def slot_signal_cellMenu(self, msg:dict) -> None:
		
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		actionName = msg.get('action')

		match actionName:
			
			case _:
				eval( f"self.menu__{actionName}(msg)")



	@pyqtSlot(dict)
	def slot_signal_model_data_changed(self, msg:dict) -> None:
		"""
		{
			'row' :row,
			'col' : col,
			'value' : value,
			'api_data' :api_data,
		}
		"""

		self.tableView : QTableView
		model_datas = self.tableView.model()._data
		api_data = msg.get('api_data')		
		if  model_datas[msg.get('row')][msg.get('col')] == msg.get('value'):
			return
		
		_isOk, _json = APP.API.Send( self.url, api_data , api_data)
		if _isOk:
			self.signal_refresh.emit()
			# self.tableView.model().beginResetModel()
			# # print ( model_datas)
			# model_datas[msg.get('row')] =  self.get_table_row_data(_json)
			# self.tableView.model().endResetModel()
		else:
			logger.error(f"Error updating row: ")

	def _get_datas_from_msg(self, msg:dict) -> tuple[int, int, str]:
		"""
			msg로 부터, [rowNo, colNo, headerName] return
		"""
		rowNo =  msg.get('row')
		colNo =  msg.get('col')
		headerName = self.table_header[colNo]
		return ( rowNo, colNo, headerName  )

	@pyqtSlot(QWidget)
	def slot_delegate_closeEditor(self, wid:QWidget):
		pass		
		# self.tableView.closeEditor( wid )
		# res = wid.close()



	#### Menus 관련
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, db update는 안함			
		"""
		row :int = msg.get('row')
		self.tableView : QTableView
		model_datas:list[list] = self.tableView.model()._data


		new_data = self._create_new(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

		# self.api_data:list
		# self.api_data.insert(row, { key:value for (key, value) in zip(self.header, new_data)})

	def menu__delete_row(self, msg:dict) -> None:
		self.tableView : QTableView
		model =  self.tableView.model()
		model_datas:list[list] = model._data

		def delete_model_data(model, model_datas, row : int):
			model.beginResetModel()
			model_datas.pop( row  )
			model.endResetModel()

		row :int = msg.get('row')
		ID = self._get_ID( model_datas[row] )
		if ID <= 0 :
			delete_model_data(model, model_datas, row)
			return
		
		dlg_kwargs = {
			'title' : '삭제 확인',
			'msgText' : '삭제하시겠읍니까? \n(db에서 복구할 수 없읍니다.)'
		}

		dlg =  Dialog_Confirm( self, **dlg_kwargs)
		if dlg.exec():
			# self.signal_refresh.emit()
			if APP.API.delete(self.url+ str(ID) ):
				self.signal_refresh.emit()
				# delete_model_data(model, model_datas, row)

			else:
				logger.error(f"Error deleting row:")
				logger.error(f"Error deleting row: {traceback.format_exc()}")


	### cell menu로 지도보기
	def menu__지도보기_google(self, msg:dict):
		"""	 msg는 
			'action' : actionName은 objectName().lower(),
			'col'  : logical_pos[0] , 
			'row'  :  logical_pos[1] ,
		"""
		obj:dict = self.api_data[msg.get('row')]
		# google_dialog = Google_Map_Dialog(self, location=obj.get('건물주소_찾기용'))

		from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
		dlg = Dialog_Folium_Map(self, address= obj.get('건물주소_찾기용'))
		dlg.setWindowTitle ('지도보기 ')


	### util methods
	def _update_model_data_from_Msg(self, msg:dict ):
		rowNo, colNo, headerName = self._get_datas_from_msg (msg)
		model_datas = self.tableView.model()._data
		self.tableView.model().beginResetModel()
		model_datas[rowNo][colNo] =  msg.get('value')
		self.tableView.model().endResetModel()

	def _get_ID_from_Msg(self, msg:dict) ->int:
		rowNo, colNo, headerName = self._get_datas_from_msg (msg)
		id_idx = self.table_header.index('id')
		model_datas = self.tableView.model()._data
		return model_datas[rowNo][id_idx]

	def _get_ID(self, data) -> int:
		id_idx = self.table_header.index('id')
		return data[id_idx]

	def _create_new(self, data:list) -> list:
		""" 
			app 마다 상이하므로, overwrite 할 것.
		"""
		copyed = []
		for index,elm in enumerate(data):
			if index == self.table_header.index('id'):
				copyed.append(-1)
				continue

			if isinstance(elm, str):
				copyed.append('')
			elif isinstance(elm, bool):
				copyed.append(False)
			elif isinstance(elm, (int,float)):
				copyed.append(0)
			else:
				copyed.append('')

		return copyed

	def _get_apiDict_by_ID(self, ID:int) -> dict:
		if ID == -1 :
			return {}
		
		for apiDict in self.api_data:
			if apiDict.get('id') == ID:
				return apiDict
		
		return {}
	
	def menu__select_row(self, msg:dict):
		rowNo = msg.get('row')
		apiDict = self.api_data[rowNo]
		self.signal_select_row.emit (apiDict)



	def _set_Row_Span(self, headerName:str , **kwargs):
		my_data = self.model_data
		colNo = self.table_header.index(headerName)
		table = self.tableView

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

	
	def _reset_Row_Span_All(self,  **kwargs):
		model = self.tableView.model()
		if not model:
			return
			
		for row in range(model.rowCount(None)):
			for col in range(model.columnCount(None)):
				self.tableView.setSpan(row, col, 1, 1)