import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import copy
from datetime import datetime
from config import Config as APP

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.Tabs.생산지시서.dialog.ui.Ui_생산지시서_form_spg_현대 import  Ui_Form as Ui_생산지시서_SPG 
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly

import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Wid_생산지시서_SPG(QWidget, Qwidget_Utils ):
	def __init__(self, parent, **kwargs ):
		super().__init__(parent)
		self.is_ECO = False
		self.kwargs = {}
		self.kwargs.update(kwargs)
		self.is_Edit = True
		self.url = ''
		self.dataObj = {}
		self.skip = []
		self._api_datas:list[dict] =[]

		for k, v in self.kwargs.items():
			setattr(self, k, v)

		self.url = INFO.URL_생산지시_SPG
		self.ui = Ui_생산지시서_SPG()
		self.ui.setupUi(self)	

		# ic(self.kwargs)
		self.user_defined_UI()
		
		self.init_InputDict()

		if hasattr(self, 'dataObj') :
			if self.dataObj['id'] > 0:
				self._render_from_DataObj()
			elif hasattr(self, 'is_update_By_Jakji') and self.is_update_By_Jakji:
				self._render_from_작업지침_obj()
			else:
				self._render_from_DataObj()

		self.triggerConnect()
		self.show()


	def init_InputDict(self):
		self.inputDict = {
			'호기' : self.ui.plainTextEdit_Hogi,
			'비고' : self.ui.textEdit_SPG_Bigo,
			'도면번호' : self.ui.lineEdit_Domyun,
			'job_name' : self.ui.lineEdit_SPG_hyunjang,
			'proj_No' : self.ui.lineEdit_SPG_proj_No,
		}
		self.imageViewerDict = {
			'file1' : self.ui.widget_ImageViewer_1,
			'file2' : self.ui.widget_ImageViewer_2,
		}


	def _find_obj_in_list(self, targetList, condition:tuple[str,str,str,str]) -> dict:
		부품 = condition[0].lower()
		패널 = condition[1].lower()
		품번 = condition[2]
		
		for obj in targetList:
			if 부품 in obj.get('적용부품', '').lower() and  패널 in obj.get('적용패널','').lower():
				_obj = copy.deepcopy(obj)
				_obj['품번'] = 품번
				return _obj

		return {}

	def _render_from_작업지침_obj(self):
		#### 😀 Process_fks : 즉, HTM_Table
		process_fks =  self.작업지침_obj.get('process_fks', []) 
		if len(process_fks) > 0:
			param = f"?ids={(',').join( [str(id) for id in process_fks] )}&page_size=0"
			is_ok, _json = APP.API.getlist(INFO.URL_작업지침_PROCESS_DB + param )
			if is_ok:
				ic(_json )
				for item in _json:
					# id 값을 old_id로 복사하고 id를 -1로 설정
					item['작지Process_fk'] = item.pop('id')
					item['id'] = -1
				
				표시순서_maping = [
					('FRONT','FRONT','#1, #11번'),('SIDE', 'SIDE','#2,10번'),( 'SIDE','SIDE','#4,8번'),
					('REAR','SIDE','#5번'),('REAR','SIDE','#7번'),
					('SIDE','CENTER','#3,9번'), ('REAR','CENTER','#6번'),
				   ]

				변환된List = []
				for idx, tuple_str in enumerate(표시순서_maping) :
					obj = self._find_obj_in_list ( _json, tuple_str )
					obj['표시순서'] = idx
					변환된List.append( obj)

				self._spg_table_Datas = 변환된List

				### 😀if self.is_ECO 시, table_api_datas의 id를 모두 -1로 변환
				if self.is_ECO:
					for obj in self._spg_table_Datas:
						obj['id'] = -1 

			else:
				Utils.generate_QMsg_critical(self)
		else:
			self._spg_table_Datas = []

		_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_SPG_Table )
		if _isOk:
			if not self.is_Edit:
				db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
			self.ui.wid_table_SPG._update_data(
				api_data = self._spg_table_Datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
				url = INFO.URL_SPG_TABLE,
				**db_fields,
			)		
		else:
			Utils.generate_QMsg_critical(self)



	def _render_from_DataObj(self):

		# if not self.is_Edit:
		# 	for key, wid in self.inputDict.items():
		# 		if 'title' in key : 
		# 			wid:QLineEdit
		# 			wid.setEnabled( self.is_Edit)
		# 		if 'image' in key:
		# 			wid.update_kwargs(is_Edit=self.is_Edit )

		keysList = list (self.inputDict.keys() )
		self._api_datas = {'id': -1 }
		if hasattr(self, 'dataObj') and self.spg_fk > 0:
			_isOk, _apiData = APP.API.getObj( INFO.URL_생산지시_SPG, id= self.spg_fk )
			if _isOk:
				# _apiData: {'file1_URL': '/media/%EC%83%9D%EC%82%B0%EC%A7%80%EC%8B%9C/spg%EC%83%9D%EC%82%B0%EC%A7%80%EC%8B%9C/2024-8-8/b0f8cb59-152a-4711-85aa-97a6a4f21db9/%EB%8C%80%EB%A6%BC%ED%9C%B4%EB%A8%BC%EB%B9%8CSPG_1.png',
				# 'file1_fk': 79,
				# 'file2_URL': '/media/%EC%83%9D%EC%82%B0%EC%A7%80%EC%8B%9C/spg%EC%83%9D%EC%82%B0%EC%A7%80%EC%8B%9C/2024-8-8/b0f8cb59-152a-4711-85aa-97a6a4f21db9/%EB%8C%80%EB%A6%BC%ED%9C%B4%EB%A8%BC%EB%B9%8CSPG_1.png',
				# 'file2_fk': 80,
				# 'id': 54,
				# 'job_name': '대림휴먼빌아파트',
				# 'proj_No': 'N24975',
				# 'spg_table_fks': [93, 94, 95, 96, 97, 98, 99],
				# '도면번호': '32210947G07',
				# '비고': '',
				# '호기': 'L01,L02,L03,L04,L05,L06'}

				self._api_datas = _apiData
				# ic (_apiData )
			else:
				Utils.generate_QMsg_critical(self)
		

		### normal data Update
		for key, value in self._api_datas.items():
			try:
				if self.is_Edit:
					Object_Set_Value( self.inputDict[key], value)
				else:
					Object_ReadOnly (self.inputDict[key], value )
			except Exception as e:
				ic (str(e))

		#### imageViewer Update
		for keyName , widImageViewer in self.imageViewerDict.items():
			fk_str = f"{keyName}_fk"
			URL_str = f"{keyName}_URL"
			if fk_str in self._api_datas and self._api_datas.get(fk_str, -1) > 0 and ( URL:= self._api_datas.get( URL_str,'') ):
				widImageViewer.update_kwargs(url= INFO.URI + URL , is_Edit=self.is_Edit )

		### spg_table_fks : spg_table
		self._spg_table_Datas = []
		if 'spg_table_fks' in self._api_datas and ( spg_table_fks := self._api_datas.get('spg_table_fks', []) ):
			param = ','.join( [ str(id) for id in spg_table_fks ])
			_isOk, _spg_table_Datas = APP.API.getlist( INFO.URL_SPG_TABLE+ f"?ids={param}&page_size=0")
			self._spg_table_Datas = _spg_table_Datas
			# ic(_spg_table_Datas )

		_isOk, db_fields = APP.API.getlist(INFO.URL_DB_Field_SPG_Table )
		if _isOk:
			if not self.is_Edit:
				db_fields['table_config']['no_Edit_cols'] = db_fields['table_config']['table_header']
			self.ui.wid_table_SPG._update_data(
				api_data = self._spg_table_Datas, ### 😀😀없으면 db에서 만들어줌.  if len(self.api_datas) else self._generate_default_api_data(), 
				url = INFO.URL_SPG_TABLE,
				**db_fields,
			)		
		else:
			Utils.generate_QMsg_critical(self)




	def user_defined_UI(self):
		return 




	def run(self):
		return 
		if hasattr(self, 'vLayout_main') : Utils.deleteLayout(self.vLayout_main)
		self.ui.setupUi(self)
		self.user_defined_UI()
		self.show()

		self.init_InputDict()

		self.triggerConnect()
	
	def triggerConnect(self):
		return


	def handle_PB_AppendRow(self):
		if self.ui.lineEdit_title5.isHidden():
			self.ui.lineEdit_title5.show()
			self.ui.lineEdit_title6.show()
			self.ui.imageView_5.show()
			self.ui.imageView_6.show()
			return
		if self.ui.lineEdit_title7.isHidden():
			self.ui.lineEdit_title7.show()
			self.ui.lineEdit_title8.show()
			self.ui.imageView_7.show()
			self.ui.imageView_8.show()
			return

	def _get_의장도_datas(self):
		의장도_datas:list[dict] = []
		for i in range(1,9):
			obj = {}
			edit : QLineEdit = self.inputDict[f"title{i}"]
			obj['title'] = edit.text()
			imageViewer = self.inputDict[f"image{i}"]
			obj['image_result'] = imageViewer.getValue()
			obj['순서'] = i
			의장도_datas.append ( obj )

		for index, 의장도_data in enumerate(의장도_datas, 1):				
			files ={}
			image_result:dict|None = 의장도_data.get('image_result')
			if image_result:
				ic ( image_result )
				match image_result.get('type'):
					case 'file':
						files = { 'file': open(image_result['source'], 'rb') }
						의장도_data['files'] = files
					case 'clipboar'|'pilImage':
						# 클립보드나 PIL 이미지인 경우
						# QPixmap을 바이트로 변환
						byte_array = QByteArray()
						buffer = QBuffer(byte_array)
						buffer.open(QBuffer.OpenModeFlag.WriteOnly)
						image_result['image'].save(buffer, 'PNG')
						fName = title if len(title:= 의장도_data.get('title') ) > 0 else f'의장도_{str(index)}'
						files = {'file': (f"{fName}.png", byte_array.data(), 'image/png')}
						의장도_data['files'] = files
					case 'url':
						의장도_data['id']= Utils.get_Obj_From_ListDict_by_subDict( self._api_datas, {'file':image_result['source']} ).get('id')
		
		ic ( 의장도_datas )

		return [  data for data in 의장도_datas if 'files' in data or 'id' in data ] 


	
	# def _get_의장도_obj(self) -> dict:
	# 	if not self.dataObj : return { 'id': -1}
	# 	if ( id := self.dataObj.get('의장도_fk', -1) ):
	# 		if isinstance( id, int): return {'id':id}
	# 		else : return {'id':-1}
	# 	return { 'id':  -1}

	# def _get_의장도file_obj(self, index:int) -> dict:
	# 	if not self.dataObj : return {}
	# 	if ( 의장도obj := self.dataObj.get('의장도_fk_datas', {})):
	# 		return 의장도obj.get(f"의장도_{index}_data", {})
	# 	else:
	# 		return {}

	# def editMode_only의장도(self, isEdit:bool=True):
	# 	if isEdit :
	# 		self.editMode()
	# 	else:
	# 		self.viewMode()
			
	# 	for key, inputWid in self.displayDict.items():
	# 		inputWid.setReadOnly(True)

	# 	try:
	# 		fileURL = self.dataObj.get('의장도_fk_datas').get('의장도_5_data').get('file')
	# 		if fileURL:
	# 			self.frame_row3.show()
	# 	except:
	# 		pass
	# 	try:
	# 		fileURL = self.dataObj.get('의장도_fk_datas').get('의장도_7_data').get('file')
	# 		if fileURL:
	# 			self.frame_row4.show()
	# 	except:
	# 		pass


	#### Qwidget_Utils Override
	def _mode_for_inputDict(self, isEditMode:bool=True) ->None:
		if not hasattr(self, 'inputDict') : return
		if not self.inputDict: return 

		의장도data:dict = self.dataObj.get('의장도_fk_datas')
		for (keyName, title, image) in zip(self.의장도_keyNames, self.titlesName, self.imagesName):			
			try:
				obj:dict = 의장도data.get(keyName)
				url = obj.get('file')
				if url is not None :
					if 'http' not in url: 	url = INFO.URI + url
					self.inputDict[image]._setURL( url )		
					if not isEditMode : self.inputDict[image].readOnly()

				if isEditMode : 
					Object_Set_Value(self.inputDict[title], obj.get('title', ''))
				else :
					Object_ReadOnly(self.inputDict[title], obj.get('title', '') )
						
			except Exception as e:
				ic ( f'mode_for_inputDict: {e}')

