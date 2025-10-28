from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pandas as pd
import urllib
from datetime import date, datetime

import pathlib
import typing
import copy
import json
import math

# import user module
# from modules.PyQt.Tabs.생산지시서.dialog.table.table_생산지시서_도면정보_header import Wid_Table_for_생산지시서_도면정보_Header
# from modules.PyQt.Tabs.생산지시서.dialog.table.table_생산지시서_도면정보_body import Wid_Table_for_생산지시서_도면정보_Body
from modules.PyQt.User.table.My_Table_Model import My_TableModel
from modules.PyQt.User.table.My_tableview import My_TableView
from modules.PyQt.User.table.My_Table_Delegate import My_Table_Delegate
from modules.PyQt.User.table.handle_table_menu import Handle_Table_Menu

from modules.PyQt.User.object_value import Object_Set_Value, Object_Diable_Edit, Object_ReadOnly, Object_Get_Value

from modules.PyQt.User.toast import User_Toast
from config import Config as APP
import modules.user.utils as Utils


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

TABLE_NAME = '생산지시서_도면정보'
HOVER_LIST = []

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()

class TableModel_생산지시서_도면정보(My_TableModel):
	signal_data_changed = pyqtSignal(dict)
	signal_isChamro_changed = pyqtSignal(dict)
	signal_sum_changed = pyqtSignal(int)

	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)		
		self.parentWid = parent
		
	def rowCount(self, parent):		
		# The length of the outer list.
		return len(self._data) 

	def columnCount(self, parent):
		if not len(self._data): return 0
		# The following takes the first sub-list, and returns
		# the length (only works if all rows are an equal length)
		return len(self.header)
	
	### 😀😀😀type에 따라서 변경해야 함. hard-coding ###
	def user_defined_data(self, index:QModelIndex, role, value) :
		"""
			self.header_type 예.. \n
			{'id': 'BigAutoField', '평가체계_fk': 'ForeignKey', '피평가자_평가체계_fk': 'ForeignKey', \n
			'is_submit': 'BooleanField', 'ability_m2m': 'ManyToManyField', 'perform_m2m': 'ManyToManyField', 'special_m2m': 'ManyToManyField',
			'차수별_점유': 'JSONField' } \n
		"""
		colNo = index.column()
		headerName = self.header[colNo] 
		
		# 합계 행인 경우
		ic ( index.row() , headerName )
		if index.row() == len(self._data) -1 :
			if '수량' in headerName:
				_valueSum = math.ceil( sum( [ row[colNo] for row in self._data[4:-1]])  )
				self._data[index.row()][colNo] = _valueSum
				# self.calculateSum()
				return _valueSum
			
		match self.header_type.get(headerName, ''):
			case 'ManyToManyField':
				return str(value)
			case 'JSONField':
				return json.dumps(value, ensure_ascii=False)
			case 'DateTimeField':
				if isinstance( value, datetime.datetime) :
					return value 
				if  isinstance( value, str) and '.' in value:
					return value.split('.')[0]
				return value

			case _:
				return value

	### 😀 No API SEND ==> ORIGINAL임
	def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
		if role == Qt.ItemDataRole.EditRole:
			# 유효한 인덱스인지 확인
			if not index.isValid():
				return False
			
			# 데이터 수정
			self._data[index.row()][index.column()] = value

			if index.row() != len(self._data) -1 and '수량' in self.header[index.column()]:
				ic ()
				self.calculateSum()
			# 데이터가 변경되었음을 알림
			self.dataChanged.emit(index, index)
			return True
		return False


	def calculateSum(self):
		### 마지막 합계행만 계산
		ic ( self._data[-1] )
		total_sum = sum( [ value for colNo, value in enumerate(self._data[-1]) if '수량2' in self.header[colNo]])
		ic ( total_sum)
		# self.layoutChanged.emit()
		self.signal_sum_changed.emit(total_sum)
		return 
		# 4번째부터 마지막 -2 까지 포함하는 slicing
		self._calucrated_data = self._data[4:-1]
		
		total_sum = 0
		for colNo, headerName in enumerate(self.header):
			## 😀 '수량2'에 대해서만
			if '수량2' in headerName :
				value_sum = sum(row[colNo] for row in self._calucrated_data if isinstance(row[colNo], (int, float)))
				self._data[-1][colNo] = value_sum
				total_sum += value_sum

		self.layoutChanged.emit()

		ic(total_sum)
		self.signal_sum_changed.emit(total_sum)


class TableView_생산지시서_도면정보(My_TableView):
	signal_hover = pyqtSignal(bool, int, str, QPoint)
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	#### 도면정보 table head span 적용
	def head_row_span(self, colNo:int):
		""" row span 적용"""
		my_data = copy.deepcopy(self.model._data)
		table = self.table
					# rows =len(my_data)
		row_span_cnt = 0
		for idx, row in enumerate(my_data):
			if idx == 4: break
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
				
	def _userDefined_Col_Span(self):
		my_data = copy.deepcopy(self.model()._data)
		
		for rowNo in range(2):
			for idx, headerName in enumerate(self.table_header):
				if '수량1' in headerName:
					search_str = str(headerName).replace('수량1', '')
					self.setSpan( rowNo, self.table_header.index(headerName), 1, len([s for s in self.table_header if search_str in s] ) )
			# elif idx ==2 or idx ==3 :
			# 	pass
			# elif idx == len(my_data) -1:
			# 	self.setSpan( idx, self.header.index('공사번호'), 1, 11)
			# else :
			# 	pass

	def _clear_합계Row_span(self):
		self.setSpan( len( self.model()._data)-1, self.table_header.index('공사번호'), 1, 1 )

	def _set_합계Row_span(self):
		self.setSpan( len( self.model()._data)-1, self.table_header.index('공사번호'), 1, 11 )

	# def _set_Row_Span(self, headerName:str='' , **kwargs):
	# 	my_data = copy.deepcopy( self.model()._data )
	# 	colNo = self.table_header.index(headerName)
	# 	subHeader = subHeader if ( subHeader:= kwargs.get('subHeader', False) ) else ''

	# 	startRowNo = kwargs['startRowNo'] if 'startRowNo' in kwargs else 0
	# 	endRowNo = kwargs['endRowNo'] if 'endRowNo' in kwargs else -1
	# 	targetDatas = my_data[startRowNo:endRowNo]

	# 	if not subHeader:
	# 		row_span_cnt = 0

	# 		for idx, row in enumerate(targetDatas):
	# 			if idx < row_span_cnt: continue
	# 			my_item_count = 0
	# 			my_label = row[colNo]
	# 			for row_rest in targetDatas[idx:]:
	# 				if row_rest[colNo] == my_label:
	# 					my_item_count += 1
	# 				else: break
	# 			if my_item_count != 1:
	# 				self.setSpan(startRowNo+ idx, colNo, my_item_count, 1)
	# 				row_span_cnt += my_item_count
		
	# 	else:
	# 		sub_col_no = self.table_header.index(subHeader)
	# 		row_span_cnt = 0
	# 		for idx, row in enumerate(targetDatas):
	# 			if idx < row_span_cnt: continue
	# 			my_item_count = 0
	# 			my_label = row[colNo] + row[sub_col_no]
	# 			for row_rest in targetDatas[idx:]:
	# 				if (row_rest[colNo]+row_rest[sub_col_no]) == my_label:
	# 					my_item_count += 1
	# 				else: break
	# 			if my_item_count != 1:
	# 				self.setSpan(startRowNo+idx, colNo, my_item_count, 1)
	# 				row_span_cnt += my_item_count


from modules.PyQt.component.combo_lineedit_v2 import 샘플의뢰_Table_소재종류, 샘플의뢰_Table_소재Size
from modules.PyQt.component.textedit.textedit_with_contextmenu import TextEdit_ContextMenu
class Delegate_생산지시서_도면정보(My_Table_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)
		self._items = {
			'Material' :  ['GI', 'POSMAC', 'SUS', '해당사항 없음','기타'], 
		}

	def user_defined_creatorEditor_설정(self, widget:object, **kwargs) -> object:
		match kwargs['key']:
			# case '작업형태'|'제작형태'|'단위':
			# 	widget = QComboBox( kwargs['parent'])
			# 	widget.addItems ( self._items[ kwargs['key'] ])
			case 'Material':
				widget = 샘플의뢰_Table_소재종류( kwargs['parent'], items= self._items[ kwargs['key'] ])
			# case '소재Size':
			# 	widget = 샘플의뢰_Table_소재Size( kwargs['parent'], items= self._items[ kwargs['key'] ])
			case '상세Process' :
				widget = TextEdit_ContextMenu( kwargs['parent'] )

		return widget
	
	def setModelData(self, editor, model:QAbstractItemModel, index:QModelIndex):
		prevValue = model.data(index, Qt.ItemDataRole.DisplayRole)
		value = Object_Get_Value(editor).get()
		model.setData(index, value, Qt.ItemDataRole.EditRole)

		if 'Material' == self.table_header[index.column()] and value == '해당사항 없음':
			for keyName in ['대표Process','상세Process']:
				next_index = model.index ( index.row(), self.table_header.index( keyName) )
				model.setData( next_index, value )
		
		if prevValue == '해당사항 없음' and value != prevValue:
			for keyName in ['대표Process','상세Process']:
				next_index = model.index ( index.row(), self.table_header.index( keyName) )				
				if model.data(next_index , Qt.ItemDataRole.DisplayRole) == prevValue:
					model.setData( next_index, '' )


class Wid_Table_for_생산지시서_도면정보(QWidget , Handle_Table_Menu):
	"""
		kwargs가 초기화 및 _update_data method를 통해서 update 할수 있으나,
		ui file을 만들면, _update_data로 할 것.
		tableView class의 signal은 Handle_Table_Menu에서 처리
	"""
	signal_appData_Changed = pyqtSignal(dict)
	signal_sum_changed = pyqtSignal(int)

	def __init__(self, parent,  **kwargs ):
		super().__init__( parent, **kwargs )		
		self.tableView:  TableView_생산지시서_도면정보		
		self.table_model : TableModel_생산지시서_도면정보		
		self.delegate : Delegate_생산지시서_도면정보		


	def UI(self):
		self.vLayout_main = QVBoxLayout()

		self.tableView = eval ( f"""TableView_{TABLE_NAME}(	parent = self)""")
		self.vLayout_main.addWidget(self.tableView)				
		# self.vLayout_main.setSpacing(0)  # 테이블 간 간격 제거
		# self.vLayout_main.setContentsMargins(0, 0, 0, 0)  # 여백 제거
		self.setLayout(self.vLayout_main)

	
	def _update_data(self, **kwargs):
		""" kwargs : 
			#😀 db data
			api_data = list[dict]
			url = str
			#😀 DB_Field에서 가져온것
			fields_model = { name: type },
			fields_append = { name: type }, 
			fields_delete = { name: type },
			table_config = {
				'table_header' : list if not db_fields.keys(),
				'no_Edit_cols : list[str] => str은 table_header 의 element name,
				'hidden_columns' : list[str],
				....

			}
		"""
		self.kwargs = kwargs

		self.api_data : list[dict]
		self.url : str 
		self.fields_model :dict[str:str]
		self.fields_append :dict[str:str]
		self.fields_delete :dict[str:str]
		self.table_config :dict

		for (key, value) in kwargs.items():
			setattr(self, key, value )

		self.info = INFO()

		### header_type 는 DB_FIELDS + SERIALIZER_APPEND
		self.header_type = copy.deepcopy(self.fields_model)
		self.header_type.update(self.fields_append)

		if  hasattr(self, 'table_config') and ( table_header:=self.table_config.get('table_header', None) ):			
			self.table_header =table_header
		else:
			self.table_header = list( self.header_type.keys() )

		self.run()

	def _resize_to_contents(self):
		self.tableView.resizeRowsToContents()

	def _search_in_model_data(self, search:str):
		if len(search) == 0 : 
			for rowNo, rowData in enumerate(self.model_data) :
				self.tableView.showRow(rowNo)

		search_rows:list[int] = []
		for rowNo, rowData in enumerate(self.model_data) :
			rowData : list
			for data in rowData:
				if search in str(data) and rowNo not in search_rows:
					search_rows.append ( rowNo )

		for rowNo, _ in enumerate(self.model_data):
			if rowNo in search_rows:
				self.tableView.showRow(rowNo)
			else:
				self.tableView.hideRow(rowNo)

	def _get_Model_data(self) -> list[dict]:
		sendData = []
		for rowNo, rowData in enumerate( self.model_data ):
			data = { headerName: rowData[index] for index, headerName in enumerate(self.table_header) }
			data['표시순서'] = rowNo
			sendData.append ( data )

		update_dict = self._get_sendData_by_header ( sendData[:4])

		finalSendData = []
		for index, item in enumerate(sendData[4:-1]):
			new_dict = item.copy()  # 기존 dict 복사
			new_dict.update(update_dict)  # sample_dict로 업데이트
			new_dict['표시순서'] = index  # 인덱스를 표시순서로 추가
			finalSendData.append(new_dict)

		ic( finalSendData)
		return finalSendData

	def _get_sendData_by_header(self, headerList:list[dict]) ->str:
		tailDict = {}
		for row, obj in enumerate(headerList):			
			match row:
				case 0 :
					for name, db_field in zip ( ['HD_기타층_수량1', 'HD_기준층_수량1','CD_수량1','CW_수량1', '상판_수량1'], ['HD_기타층_Type','HD_기준층_Type', 'CD_Type', 'CW_Type','상판_Type' ]):
						tailDict[db_field] = obj[name]
				case 1 :
					for name, db_field in zip ( ['HD_기타층_수량1', 'HD_기준층_수량1','CD_수량1','CW_수량1', '상판_수량1'], ['HD_기타층_도면번호','HD_기준층_도면번호', 'CD_도면번호', 'CW_도면번호','상판_도면번호' ]):
						tailDict[db_field] = obj[name]			
				case 2 :
					for name, db_field in zip ( ['HD_기타층_수량2', 'HD_기준층_수량2','CD_수량2','CW_수량2', '상판_수량2'], ['HD_기타층_소재','HD_기준층_소재', 'CD_소재', 'CW_소재','상판_소재' ]):
						tailDict[db_field] = obj[name]
				case 3 :
					for name, db_field in zip ( ['HD_기타층_수량2', 'HD_기준층_수량2','CD_수량2','CW_수량2', '상판_수량2'], ['HD_기타층_사양','HD_기준층_사양', 'CD_사양', 'CW_사양','상판_사양' ]):
						tailDict[db_field] = obj[name]
		return tailDict


	
	#### app마다 update 할 것.😄
	def run(self):
		if hasattr(self, 'vLayout_main'):

			Utils.deleteLayout(self.vLayout_main)
		self.UI()

		#### 2개의 table을 merge 한 것 처럼
		if len(self.api_data) == 0:
			self.api_data = self._generate_default_api_datas()

		self.model_data = self.gen_Model_data_from_API_data()

		###😀😀
		# self._modity_table_config()
		self.table_model = eval ( f"""TableModel_{TABLE_NAME}(
					parent = self,
					header_type = self.header_type,
					header = self.table_header,
					_data = self.model_data,
					**self.table_config,					
				)""")


		self.tableView.setModel ( self.table_model)
		self.tableView.setConfig ( **self.table_config  )
		self.delegate = eval ( f"""Delegate_{TABLE_NAME}(
						self, 
						header_type=self.header_type,  
						**self.table_config
						)""")
		self.tableView.setItemDelegate(self.delegate)

		###😀 tableheader에 대한 span적용 : row, col##############################
		for headerName in self.table_header:
			if headerName in ['id', '공사번호', '호기','현장명','사양','발주일','납기일_Door','납기일_Cage', '인승','JJ', 'CH', 'HH', ]:
				self.tableView._set_Row_Span( headerName, startRowNo=0, endRowNo=4)
			elif '_수량1' in headerName:
				self.tableView._set_Row_Span( headerName, startRowNo=2, endRowNo=4)
		self.tableView._userDefined_Col_Span()
		#########################################################################
		self.tableView._set_합계Row_span()		

		#### table delegate signal handler
		self.delegate.closeEditor.connect(self.slot_delegate_closeEditor)

		### tableView signal handler
		self.tableView.signal_vMenu.connect(self.slot_signal_vMenu )
		self.tableView.signal_hMenu.connect(self.slot_signal_hMenu )
		self.tableView.signal_cellMenu.connect(self.slot_signal_cellMenu)

		### tableModel signal handler
		self.table_model.signal_data_changed.connect( self.slot_signal_model_data_changed )
		self.table_model.signal_isChamro_changed.connect ( self.slot_model_isChamro_changed )
		# self.table_model.signal_sum_changed.connect ( lambda : ic()  )
		self.table_model.signal_sum_changed.connect ( lambda _sum: self.signal_sum_changed.emit(_sum) )


	def gen_Model_data_from_API_data(self, api_DB_data:list[dict]=[] ) ->list[list]:  		
		api_DB_data = api_DB_data if api_DB_data else self.api_data
		
		_data = []

		### 😀generate table header
		_data = self.generate_like_table_header(api_DB_data[0])

		### 이제 실제 data
		for obj in api_DB_data:
			_data.append ( self.get_table_row_data(obj) )
		
		### last 합계 row
		_data.append ( self._get_table_row_합계() )
		return _data
	
	def generate_like_table_header(self, api_data:dict):
		data_header = []
		for rowNo in range(4):
			data = []
			for head in self.table_header :
				data.append ( self._get_value_like_table_header( head, api_data, rowNo) )
			data_header.append( data)
		return data_header

	def _get_value_like_table_header(self, key:str, obj:dict, row:int) ->str:
		실제_dataObj = obj
		match row:
			case 0 :
				match key: 
					case 'HD_기타층_수량1': return 실제_dataObj.get('HD_기타층_Type', "HATCH DOOR\n(기타층,방화 TYPE)")
					case 'HD_기준층_수량1': return 실제_dataObj.get('HD_기준층_Type', "HATCH DOOR\n(기준층,방화 TYPE)")
					case 'CD_수량1' :		return 실제_dataObj.get('CD_Type', "CAR DOOR")
					case 'CW_수량1' :		return 실제_dataObj.get('CW_Type',"CAR WALL")
					case '상판_수량1' :		return 실제_dataObj.get('상판_Type', "상판")
					case _: 
						return key
			case 1 :
				match key :
					case 'HD_기타층_수량1': return 실제_dataObj.get('HD_기타층_도면번호', '')
					case 'HD_기준층_수량1': return 실제_dataObj.get('HD_기준층_도면번호', '')
					case 'CD_수량1' :		return 실제_dataObj.get('CD_도면번호', '')
					case 'CW_수량1' :		return 실제_dataObj.get('CW_도면번호', '')
					case '상판_수량1' :		return 실제_dataObj.get('상판_도면번호', '')
					case _: 
						return key
			case 2 : 
				match key :
					case 'HD_기타층_수량1': return '수량\n(층)'
					case 'HD_기타층_수량2': return 실제_dataObj.get('HD_기타층_소재', 'GI')
					case 'HD_기준층_수량1': return '수량\n(층)'
					case 'HD_기준층_수량2': return 실제_dataObj.get('HD_기준층_소재', 'GI')
					case 'CD_수량1' :		return '수량\n(대)'
					case 'CD_수량2' :		return 실제_dataObj.get('CD_소재', 'GI')
					case 'CW_수량1' :		return '수량\n(대)'
					case 'CW_수량2' :		return 실제_dataObj.get('CW_소재', 'GI')
					case '상판_수량1' :		return '수량\n(대)'
					case '상판_수량2' :		return 실제_dataObj.get('상판_소재', 'GI')
					case _: 
						return key
			case 3:
				match key :
					case 'HD_기타층_수량1': return '수량\n(층)'
					case 'HD_기타층_수량2': return 실제_dataObj.get('HD_기타층_사양', '')
					case 'HD_기준층_수량1': return '수량\n(층)'
					case 'HD_기준층_수량2': return 실제_dataObj.get('HD_기준층_사양', '')
					case 'CD_수량1' :		return '수량\n(대)'
					case 'CD_수량2' :		return 실제_dataObj.get('CD_사양', '')
					case 'CW_수량1' :		return '수량\n(대)'
					case 'CW_수량2' :		return 실제_dataObj.get('CW_사양', '')
					case '상판_수량1' :		return '수량\n(대)'
					case '상판_수량2' :		return 실제_dataObj.get('상판_사양', '')
					case _: 
						return key


	def get_table_row_data(self, obj:dict) -> list:
		return [ self._get_table_cell_value(key, obj) for key in self.table_header ]
		
	def _get_table_cell_value(self, key:str, obj:dict) ->str:
		""" """
		value = obj.get(key , None)
		return value
	
	def _get_table_row_합계(self):
		return [  0  if '수량' in key  else '합계'   for key in self.table_header ]
###############################################################################################
	@pyqtSlot(dict)
	def slot_model_isChamro_changed(self, msg:dict):
		"""
			msg {'row': 111, 'col': 5, 'value': False, 'api_data': {'is_참여': False, 'id': 1644}}
		"""

		sendData :dict = msg['api_data']
		ID =sendData.pop('id')
		_isOK, _json = APP.API.Send ( url=self.url, dataObj={'id': ID}, sendData = sendData )
		if _isOK:
			model_datas = self.tableView.model()._data	
			model_datas[msg.get('row')][msg.get('col')] =  msg.get('value')
			self.tableView.model().endResetModel()
		else:
			Utils.generate_QMsg_critical(self)
	

	@pyqtSlot(dict)
	def slot_signal_model_data_changed(self, msg:dict):
		""" 
			msg = {'row': 0, 'col': 10, 'value': '20', 'api_data': {'1_평가자_ID': '20', 'id': 40}} 형태
			override : 변화된 것을 받아서, m2m filed 처럼 만들어서  api send			
		"""
		api_data = msg.get('api_data')
		평가자_ID:int = self._get_평가자ID(api_data)

		user_info = self.info._get_user_info( pk = 평가자_ID )	
		if not len(list(user_info.keys() )) > 0:
			Utils.generate_QMsg_critical( self, title='평가자 ID 오류', text =f'평가자 ID {str(평가자_ID)}는 존재하지 않읍니다' )
			return 

		model_datas = self.tableView.model()._data	
		성명_col_name = str( self.table_header[msg.get('col')] ).replace('_ID', '_성명')
		성명_col = self.table_header.index (성명_col_name)

		_isOK, _json = APP.API.Send ( url=self.url, dataObj=api_data, sendData={'평가자': 평가자_ID} )
		if _isOK:
			self.tableView.model().beginResetModel()

			model_datas[msg.get('row')][msg.get('col')] =  평가자_ID
			model_datas[msg.get('row')][성명_col] = user_info.get('user_성명')
			self.tableView.model().endResetModel()
			# self.signal_appData_Changed.emit(_json)
		else:




	#### Menus 관련
	def menu__new_row(self, msg:dict) -> None:
		"""
			copy msg.get('row') 하여 insert 함, db update는 안함			
		"""
		row :int = msg.get('row')

		self.tableView._clear_합계Row_span()	
		model_datas:list[list] = self.tableView.model()._data


		new_data = self._create_new(  model_datas[row] ) 
		new_data[self.table_header.index('id')] = -1

		self.tableView.model().beginResetModel()
		model_datas.insert( row+1, new_data )
		self.tableView.model().endResetModel()

		self.tableView._set_합계Row_span()
		# self.api_data:list
		# self.api_data.insert(row, { key:value for (key, value) in zip(self.header, new_data)})

	def menu__delete_row(self, msg:dict) -> None:
		self.tableView._clear_합계Row_span()
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
			self.tableView._set_합계Row_span()
			return
		
		dlg_kwargs = {
			'title' : '삭제 확인',
			'msgText' : '삭제하시겠읍니까? \n(db에서 복구할 수 없읍니다.)'
		}

		from modules.PyQt.dialog.confirm.confirm import Dialog_Confirm
		dlg =  Dialog_Confirm( self, **dlg_kwargs)
		if dlg.exec():
			# self.signal_refresh.emit()
			if APP.API.delete(self.url+ str(ID) ):
				self.signal_refresh.emit()
				# delete_model_data(model, model_datas, row)

			else:




	def _generate_default_api_datas(self) ->list[dict]:		
		table_header:list[str] = self.table_config['table_header']
		obj = {}
		for header in table_header:
			if header == 'id' : obj[header] = -1
			else:
				match self.fields_model.get(header, '').lower():
					case 'charfield'|'textfield':
						obj[header] = ''
					case 'integerfield'|'floatfield':
						obj[header] = 0
					case 'datetimefield':
						# return QDateTime.currentDateTime().addDays(3)
						obj[header] =  datetime.now()
					case 'datefield':
						# return QDate.currentDate().addDays(3)
						obj[header] =  datetime.now().date()
					case 'timefield':
						# return QTime.currentTime()
						obj[header] = datetime.now().time()
					case _:
						obj[header] = ''
		return [ obj ]