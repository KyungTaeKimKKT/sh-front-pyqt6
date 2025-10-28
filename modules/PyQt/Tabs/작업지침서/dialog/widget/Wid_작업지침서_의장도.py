import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from datetime import datetime
from config import Config as APP

from modules.PyQt.User.qwidget_utils import Qwidget_Utils
from modules.PyQt.Tabs.작업지침서.dialog.ui.Ui_작업지침서_의장도_tab import Ui_Form_ljang as Ui_작업지침서_의장도 
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

class Wid_작지_의장도(QWidget, Qwidget_Utils ):
	def __init__(self, parent, **kwargs ):
		super().__init__(parent)
		self.is_Edit = True
		self.url = ''
		self.dataObj = {}
		self.skip = []
		self._api_datas:list[dict] =[]

		for k, v in kwargs.items():
			setattr(self, k, v)

		self.ui = Ui_작업지침서_의장도()
		self.ui.setupUi(self)	

		ic(kwargs)
		self.user_defined_UI()
		
		self.init_InputDict()

		self.triggerConnect()

		self._render_from_DataObj()
		self.show()


	def init_InputDict(self):

		self.inputDict = {
			"title1" : self.ui.lineEdit_title1 ,
			"title2" : self.ui.lineEdit_title2 ,
			"title3" : self.ui.lineEdit_title3 ,
			"title4" : self.ui.lineEdit_title4 ,
			"title5" : self.ui.lineEdit_title5 ,
			"title6" : self.ui.lineEdit_title6 ,
			"title7" : self.ui.lineEdit_title7 ,
			"title8" : self.ui.lineEdit_title8 ,
			"image1" : self.ui.imageView_1,
			"image2" : self.ui.imageView_2,
			"image3" : self.ui.imageView_3,
			"image4" : self.ui.imageView_4,
			"image5" : self.ui.imageView_5,
			"image6" : self.ui.imageView_6,
			"image7" : self.ui.imageView_7,
			"image8" : self.ui.imageView_8,
		}

		self.titlesName = [ key for key in self.inputDict.keys() if 'title' in key  ] #['title1', 'title2', 'title3', 'title4']
		self.imagesName = [ key for key in self.inputDict.keys() if 'image' in key  ]
		self.의장도_keyNames = [ f"의장도_{index}_data" for index, _ in enumerate(self.titlesName ,1) ]
		# self.의장도_keyNames = ['의장도_1_data','의장도_2_data','의장도_3_data','의장도_4_data']
		self.displayDict = {
			'제목' : self.ui.lineEdit_Jemok,
			"proj_No" :  self.ui.lineEdit_ProjNo,
		}

	def _render_from_DataObj(self):
		if not self.is_Edit:
			self.ui.PB_AppendRow.hide()
			for key, wid in self.inputDict.items():
				if 'title' in key : 
					wid:QLineEdit
					wid.setEnabled( self.is_Edit)
				if 'image' in key:
					wid.update_kwargs(is_Edit=self.is_Edit )

		keysList = list (self.inputDict.keys() )
		if hasattr(self, 'dataObj') and (의장도_fks:= self.dataObj.get('의장도_fks', []) ):
			param = ','.join( [ str(id) for id in 의장도_fks])
			_isOk, _apiDatas = APP.API.getlist( INFO.URL_작업지침_의장도+ f"?ids={param}&page_size=0")
			if _isOk:
				self._api_datas = _apiDatas

				ic (_apiDatas )
				for obj in _apiDatas:
					순서:int = obj.get('순서')
					Object_Set_Value ( self.inputDict[f"title{순서}"], obj.get('title') )					
					self.inputDict[ f"image{순서}" ].update_kwargs(url = obj.get('file'), is_Edit=self.is_Edit )
					# self.inputDict[ f"image{순서}" ].resize(self.inputDict[ f"image{순서}" ].size())
					self.inputDict[f"title{순서}"].show()
					self.inputDict[ f"image{순서}" ].show()
			else:
				Utils.generate_QMsg_critical(self)


	def user_defined_UI(self):
		self.ui.label.hide()
		self.ui.lineEdit_Jemok.hide()
		self.ui.label_4.hide()
		self.ui.lineEdit_ProjNo.hide()

		self.ui.imageView_5.hide()
		self.ui.imageView_6.hide()
		self.ui.imageView_7.hide()
		self.ui.imageView_8.hide()
		self.ui.lineEdit_title5.hide()
		self.ui.lineEdit_title6.hide()
		self.ui.lineEdit_title7.hide()
		self.ui.lineEdit_title8.hide()

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
		self.ui.PB_AppendRow.clicked.connect(self.handle_PB_AppendRow)

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

