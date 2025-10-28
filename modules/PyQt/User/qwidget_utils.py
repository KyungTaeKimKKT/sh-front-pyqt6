from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import json
from PIL.ImageQt import ImageQt
import PIL.Image
import io

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.imageViewer2 import ImageViewer2

from modules.PyQt.component.combo_lineedit import Combo_LineEdit
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly
from config import Config as APP
from stylesheet import StyleSheet as ST
from info import Info_SW as INFO
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Qwidget_Utils:
	""" Qwidget에 관한 method 의 CLASS"""
	def __init__(self):
		self.inputDict : dict
		self.imageViewerDict : dict
		self.file_uploadDict : dict
		self.table_Dict : dict
		self.validator_list : list
		self.dataObj : dict

		self.api_send_datas:dict = {}
		self.api_send_datas_files:list = []

	def init_attributes(self, **kwargs) ->None:
		for key, value in kwargs.items():
			setattr( self, key, value)

	def triggerConnect(self):
		self.PB_save.clicked.connect(self.func_save )
		self.PB_cancel.clicked.connect(self.close)
	
	def trigger_style_inputDict_textChanged(self):
		for key, input in self.inputDict.items():
			if isinstance( input, (QLineEdit,  QPlainTextEdit ) ) :
				input.textChanged.connect(self.style_eidt_mode )
			elif isinstance( input, ( QDateEdit, QTimeEdit, QDateTimeEdit )):
				input.dateTimeChanged.connect( self.style_eidt_mode )
			elif isinstance ( input, (QSpinBox, QDoubleSpinBox) ):
				input.valueChanged.connect( self.style_eidt_mode )
			elif isinstance ( input, (QComboBox,Combo_LineEdit)):
				input.currentTextChanged.connect( self.style_eidt_mode )
	
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
	
	def _get_url_suffix(self) -> str:
		return f'?page_size={self.pageSize}'

	def _getValue_from_ImageView2 ( self, imageResult:dict, keyName:str='' , fileName:str='',url:str='' ):
		for key, value in imageResult.items():
			match key :
				case 'file':
					return ( keyName, open(value, 'rb'))
				case 'pilImage':
					byte_io = io.BytesIO()  # `BinaryIO` is essentially a file in memory
					value : PIL.Image
					value.save(byte_io,  'png' )  # Since there is no filename,
												# you need to be explicit about the format
					byte_io.seek(0)  # rewind the file we wrote into
					return ( keyName, (fileName, byte_io) )
				case 'pixMap':
					value : QPixmap
					buffer = QBuffer()
					buffer.open( QBuffer.ReadWrite)
					qImage = value.toImage()
					qImage.save( buffer, 'PNG')
					return (  keyName, (fileName, io.BytesIO(buffer.data() )))
				case 'url':
					return ( 'url' ,'')
				case 'DB삭제':
					return ( 'DB삭제', '')					
		


	def style_eidt_mode(self) -> None:
		wid = self.sender()
		if isinstance(wid, QWidget) :
			wid.setStyleSheet(ST.edit_)

	def _get_value_from_InputDict(self) -> dict:
		if hasattr(self, 'inputDict'):
			if not self.inputDict : return {}
		else:
			return {}
		
		result = {}
		for key, input in self.inputDict.items():
			result[key] = self._get_value(key)
		return result
	
	def _get_value(self, key:str) -> str|int|None:
		""" inputdict에 한해서 key에 따른  value return """
		obj = Object_Get_Value( self.inputDict[key] )
		return obj.get()


	def _get_value_from_ImageViewer(self) -> list[tuple]:
		if hasattr(self, 'imageViewerDict'):
			if not self.imageViewerDict : return []
		else:
			return []

		filesList = []
		for key, input in self.imageViewerDict.items():
			obj = Object_Get_Value(input)
			if ( file := obj.get(key)) :
				filesList.append ( file )
		return filesList
	


	def _get_value_from_fileUpload(self) -> tuple[ dict, list[tuple] ]:
		if hasattr(self, 'file_uploadDict'):
			if not self.file_uploadDict : return []
		else:
			return []

		result = {}
		filesList = []
		for key, input in self.file_uploadDict.items():
			if (첨부파일 := input._getValue() ):

				result[f'{key}_json'] = json.dumps( 첨부파일.get('exist_DB_id') )

				if ( 첨부file_fks := 첨부파일.get('new_DB') ):
					filesList.extend( 첨부file_fks )

		return (result, filesList)

	def _get_value_from_table(self) -> dict[str:list]:
		if hasattr(self, 'table_Dict'):
			if not self.table_Dict : return {}
		else:
			return {}

		result = {}
		for key, input in self.table_Dict.items():
			if ( process_fks := input.get_model_data() ):
				result[key] = process_fks
		return result
	
	def api_send(self):
		if bool(self.dataObj):
			is_ok, res_json = APP.API.patch(url= self.url+ str(self.dataObj.get('id')) +'/',
											data=self.api_send_datas,
											files=self.api_send_datas_files)
		else:
			is_ok, res_json = APP.API.post(url= self.url,
											data=self.api_send_datas ,
											files= self.api_send_datas_files)
			
		if is_ok:
			if hasattr(self, 'signal') : self.signal.emit({'action':'update'})
			self.close()

	def _enable_validator(self):
		self.PB_save.setEnabled(False)
		for key in self.validator_list:
			self.inputDict[key].textChanged.connect(self.check_validator)
	
	def check_validator(self) -> bool:
		result = []
		for key in self.validator_list:
			if self._get_value( key ):
				self.inputDict[key].setStyleSheet(ST.edit_)
				result.append(True)
			else:
				result.append(False)
		is_True = all( i for i in result )
		self.PB_save.setEnabled(is_True)
		return is_True
	

	def editMode(self):
		self.edit_view_Mode(isEditMode=True)
	
	def viewMode(self):
		self.edit_view_Mode(isEditMode=False)

	def edit_view_Mode(self, isEditMode:bool=True) ->None:
		if not self.dataObj : return 

		self._mode_for_inputDict(isEditMode)
		self._mode_for_tableDict(isEditMode)
		self._mode_for_imageViewerDict(isEditMode)
		self._mode_for_fileUploadDict(isEditMode)
		self._mode_for_imageViewerDict_fk(isEditMode)
		self._mode_for_imageViewerDict_fk_contents(isEditMode)

	def _mode_for_fileUploadDict(self, isEditMode:bool=True) ->None:		
		if not hasattr(self, 'file_uploadDict') : return
		if not self.file_uploadDict: return 
		for key, input in  self.file_uploadDict.items():
			if key in getattr(self, 'skip', [] ): continue
			if key == 'id':continue
			try:

				input._setValue( self.dataObj.get(key, []), 'file' )
				if not isEditMode:
					input._setReadOnly()
			except Exception as e:	
				logger.error(f"파일 업로드 오류: {e}")
				logger.error(f"{traceback.format_exc()}")



	def _mode_for_inputDict(self, isEditMode:bool=True) ->None:
		if not hasattr(self, 'inputDict') : return
		if not self.inputDict: return 
		for key, input in self.inputDict.items():
			if key in getattr(self, 'skip', [] ): continue
			if key == 'id':continue
			try:
				if isEditMode : Object_Set_Value(input=input, value = self.dataObj[key])
				else : Object_ReadOnly(input=input, value = self.dataObj.get(key,'' ) )
			except Exception as e:
				logger.error(f"inputDict 오류: {e}")
				logger.error(f"{traceback.format_exc()}")


	def _mode_for_tableDict(self, isEditMode:bool=True) ->None :
		if not hasattr(self, 'table_Dict') : return
		if not self.table_Dict : return

		for key, tableView in self.table_Dict.items():
			tableView.app_DB_data = self.dataObj.get(key, [])
			if isEditMode: 
				tableView.editMode()
			else : 
				tableView.viewMode()

	def _mode_for_imageViewerDict(self, isEditMode:bool=True) ->None :
		if not hasattr(self, 'imageViewerDict') : return
		if not self.imageViewerDict : return

		for key, imageView in self.imageViewerDict.items():
			try:
				url = self.dataObj.get(key, '')
				url = INFO.URI+url if 'http' not in url else url
				if isinstance( imageView, ImageViewer) :
					imageView._setURL ( url )
				elif isinstance(imageView, ImageViewer2):
					imageView.set_image_from_URL(url)
				if not isEditMode: 
					imageView.readOnly()
			except Exception as e:
				logger.error(f"이미지 뷰어 오류: {e}")
				logger.error(f"{traceback.format_exc()}")

	def _mode_for_imageViewerDict_fk(self, isEditMode:bool=True) ->None :
		if not hasattr(self, 'imageViewerDict_fk') : return
		if not self.imageViewerDict_fk : return

		for key, imageView in self.imageViewerDict_fk.items():
			try:
				url = self.dataObj.get(key).get(self.imageViewerDict_fk_keyName)
				url = INFO.URI+url if 'http' not in url else url
				if isinstance( imageView, ImageViewer) :
					imageView._setURL ( url )
				elif isinstance(imageView, ImageViewer2):
					imageView.set_image_from_URL(url)
				if not isEditMode: 
					imageView.readOnly()
			except Exception as e:
				logger.error(f"이미지 뷰어 오류: {e}")
				logger.error(f"{traceback.format_exc()}")

				
	def _mode_for_imageViewerDict_fk_contents(self, isEditMode:bool=True) ->None :
		if not hasattr(self, 'imageViewerDict_fk_contents') : return
		if not self.imageViewerDict_fk_contents : return

		for key, imageView in self.imageViewerDict_fk_contents.items():
			try:
				url = self.dataObj.get(key).get(self.imageViewerDict_fk_keyName)
				url = INFO.URI+url if 'http' not in url else url
				if isinstance( imageView, ImageViewer) :
					imageView._setURL ( url )
				elif isinstance(imageView, ImageViewer2):
					imageView.set_image_from_URL(url)
				if not isEditMode: 
					imageView.readOnly()
			except Exception as e:
				logger.error(f"이미지 뷰어 오류: {e}")
				logger.error(f"{traceback.format_exc()}")

	

	def _get_Bytes_from_pixmap(self, pixmap:QPixmap) :
		# https://stackoverflow.com/questions/57404778/how-to-convert-a-qpixmaps-image-into-a-bytes
		# convert QPixmap to bytes
		ba = QByteArray()
		buff = QBuffer(ba)
		buff.open(QIODevice.WriteOnly) 
		ok = pixmap.save(buff, "PNG")
		assert ok
		pixmap_bytes = ba.data()
		return pixmap_bytes
	

	def _qFileDialog_open_single(self, **kwargs) -> str:
		""" kwargs \n
			caption:str = "File Upload(Single)", \n
			directory: str = "Path.home()" \n
			filter : str = "ALL Files(*.*)" \n
			initialFilter:str = "ALL Files(*.*)" \n
			options : QFileDialog.Opion  = QFileDialog.Option.DontUseNativeDialog \n
						
		"""
		fName, _ = QFileDialog ( **kwargs )
		return fName
