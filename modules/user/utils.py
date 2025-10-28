from typing import Any, Optional
from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import qrcode.image.pil
from modules.PyQt.User.toast import User_Toast
from info import Info_SW as INFO

import platform
import time
import concurrent.futures
import re
import copy
from collections.abc import Sequence
import socket, datetime, json, sys, os
import random, pathlib
import requests
from urllib.parse import unquote, quote  

# from pyzbar import pyzbar
import qrcode
from PIL import Image
from pathlib import Path

import traceback


TCP_LIVE_START = 50000
TCP_lIVE_END = 65533
TCP_START = 40000
TCP_END   = 49999

File_Download_Result = tuple[str, bytes]

cache_dict = {}

import socket
import site, importlib
import numpy as np
import cv2
import base64


# def test_info_dialog(parent)->None:
# 	QTimer.singleShot(0, 
#             lambda: generate_QMsg_Information(parent, title='✅✅✅동적변경 test', text='✅✅✅동적변경 test입니다.', autoClose=5000 )
#         )

def get_json_pretty(_json:dict, delete_keys:list[str]=[]) -> str:
	_json = copy.deepcopy(_json)
	for key in delete_keys:
		_json.pop(key, None)
	return json.dumps(_json, indent=4, ensure_ascii=False)

def base64_to_image(base64_str:str) -> np.ndarray|None:
	try:
		img_bytes = base64.b64decode(base64_str)
		img_array = np.frombuffer(img_bytes, np.uint8)
		img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
		return img
	except Exception as e:
		print(f"base64_to_image 오류: {e}")
		return None



def clear_all_proj_modules() -> list[str]:
    """
    site-packages, stdlib 제외
    프로젝트 루트/modules/PyQt 경로 아래의 모듈만 제거
    """
    removed = []
    project_root = INFO.get_base_dir()
    target_root = os.path.join(project_root, "modules", "PyQt")
    # extra_file = os.path.join(project_root, "modules", "user", "utils.py")

    for name, module in list(sys.modules.items()):
        mod_path = getattr(module, "__file__", None)
        if not mod_path:
            continue

        try:
            abs_path = os.path.abspath(mod_path)

            # PyQt 하위 or utils.py 하나만 대상
            if abs_path.startswith(target_root) : # or abs_path == extra_file:
                # __init__.py 패키지는 남긴다
                if mod_path.endswith("__init__.py") or mod_path.endswith("__init__.pyc"):
                    continue
                sys.modules.pop(name, None)
                removed.append(name)

        except Exception:
            continue

    return removed

def pixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    qimg = pixmap.toImage().convertToFormat(QtGui.QImage.Format.Format_RGB888)
    width, height = qimg.width(), qimg.height()
    ptr = qimg.bits()
    ptr.setsize(height * width * 3)
    buffer = ptr.asstring()
    return Image.frombytes("RGB", (width, height), buffer)

def get_local_ip():
    try:
        # 외부와의 연결을 시도하지만 실제 연결하지 않음 (IP 조회용)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_ffmpeg_path() -> str:
    system = platform.system()
    cwd = os.getcwd()

    try:
        if system == "Windows":
            local_path = os.path.join(cwd, "ffmpeg", "ffmpeg.exe")
            if os.path.isfile(local_path):
                return local_path
            return "ffmpeg.exe"  # PATH 기반

        elif system == "Linux":
            local_path = os.path.join(cwd, "ffmpeg", "ffmpeg")
            if os.path.isfile(local_path):
                return local_path
            return "ffmpeg"

        elif system == "Darwin":  # macOS
            local_path = os.path.join(cwd, "ffmpeg", "ffmpeg")
            if os.path.isfile(local_path):
                return local_path
            return "ffmpeg"

    except Exception as e:
        print(f"[ffmpeg 경로 오류] {e}")
        return "ffmpeg"

    return "ffmpeg"

def is_valid_attr_name(cls, attr_name:str, instance_type) -> bool:
	""" cls 안에서 attr_name 이라는 이름의 속성이 instance_type 타입이며 유효한지 검사 """

	if not hasattr(cls, attr_name):
		return False
	value = getattr(cls, attr_name)
	if isinstance(value, (int, float)):
		return isinstance( value, instance_type) 
	return isinstance(value, instance_type) and bool(value)

def is_valid_method(cls, method_name:str) -> bool:
	""" cls 안에서 method_name 이라는 이름의 메서드가 존재하는지 검사 """

	if not hasattr(cls, method_name):
		return False
	value = getattr(cls, method_name)
	return callable(value)

def get_drf_field_type_by_value(value:Any) -> str:
	""" python 타입을 drf 필드 타입으로 변환 """

	python_type = type(value)

	python_type_to_drf_field = {
		int: "IntegerField",
		float: "FloatField",
		str: "CharField",
		bool: "BooleanField",
		dict: "JSONField",
		list: "ListField",
		type(None): "EmptyField",
	}
	return python_type_to_drf_field.get(python_type, "CharField")

def format_datetime_str_with_weekday(datetime_str: str, with_year: bool = False, with_weekday: bool = True, **kwargs) -> str:
    try:
        timestamp = datetime.datetime.fromisoformat(datetime_str)
        date_str = format_date_str_with_weekday(timestamp.strftime('%Y-%m-%d'), with_year, with_weekday)
        time_str = timestamp.strftime('%H:%M:%S')
        return f"{date_str} {time_str}"
    except Exception:
        return datetime_str

def format_date_str_with_weekday(date_str: str, with_year: bool = False, with_weekday: bool = True, **kwargs) -> str:
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
        day = dt.day
        month = dt.month
        year_2digit = dt.strftime('%y')  # ← 2자리 연도

        if with_year:
            _txt = f"{year_2digit}년 {month}월{day}일"
        else:
            _txt = f"{month}월{day}일"
        if with_weekday:
            if kwargs.get('is_weekday_newLine', False):
                return f"{_txt} \n({weekday_kr})"
            else:
                return f"{_txt} ({weekday_kr})"
        else:
            return _txt
    except Exception:
        return date_str

def get_api_url_from_appDict(appDict:dict) -> str:
	return appDict['api_uri'] + appDict['api_url']


def get_소요시간 (start_time:float) -> str:
	return f"{(time.perf_counter() - start_time)*1000:.2f} msec(밀리세컨드)"


def get_table_name( APP_ID:int ) -> str:
	if not ( isinstance(APP_ID, int) and APP_ID > 0 ):
		raise ValueError(f"APP_ID는 양의 정수여야 합니다. 현재 값: {APP_ID}")
	
	if not( APP_ID in INFO.APP_권한_MAP_ID_TO_APP ):
		raise ValueError(f"APP_ID: {APP_ID} 에 해당하는 App이 없습니다.")
	
	try:
		APP_INFO = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
		div = APP_INFO['div']
		name = APP_INFO['name']
		id = APP_INFO['id']
		return f"{div}_{name}_appID_{id}"
	except Exception as e:
		print (f"get_table_name 오류: {e}")
		return ''

	
	

def get_app_temp_dir():
    if getattr(sys, 'frozen', False):  # PyInstaller로 빌드된 경우
        base_dir = sys._MEIPASS  # PyInstaller에서 임시 디렉토리
    else:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))  # main.py 실행 위치 기준

    temp_dir = os.path.join(base_dir, 'app_temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def _sort_by_order_list( _orderList: list[str], _targetList: list[str]) -> list[str]:
    """
    _orderNameList의 요소를 포함하는 순서대로 _targetList를 정렬합니다.
    같은 요소를 포함하는 항목들은 오름차순으로 정렬됩니다.
    
    Args:
        _orderNameList (list[str]): 정렬 기준이 되는 문자열 리스트
        _targetList (list[str]): 정렬할 대상 리스트
    
    Returns:
        list[str]: 정렬된 리스트
    """
    def get_sort_key(item: str) -> tuple:
        # 각 항목이 _orderNameList의 어떤 요소를 포함하는지 확인
        for idx, order_name in enumerate(_orderList):
            if order_name in item:
                return (idx, item)  # (우선순위, 원래 문자열)
        return (len(_orderList), item)  # 포함된 요소가 없는 경우 마지막 우선순위
    
    return sorted(_targetList, key=get_sort_key)

def _get_Widget_Value(widget:QWidget) :
	"""
	다양한 PyQt 위젯의 값을 반환하는 함수
	
	Args:
		widget: PyQt 위젯 객체
	
	Returns:
		위젯의 현재 값
	"""
	if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit )):
		return widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()
	
	elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
		return widget.value()
	
	elif isinstance(widget, QComboBox):
		return widget.currentText()
	
	elif isinstance(widget, (QCheckBox, QRadioButton)):
		return widget.isChecked()
	
	elif isinstance(widget, QDateEdit):
		return widget.date().toPyDate()
	
	elif isinstance(widget, QDateTimeEdit):
		return widget.dateTime().toPyDateTime()

	else:
		raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")
	

def _concurrent_API_Job(job:callable, threadingTargets:list, **kwargs )->dict:
	""" job : callable funtion \n
		return { threadingTargets의  elemnet : future }\n
		reutnr 시, 사용법 for key, future in futures.items():... \n
		
	"""
	futures = {}
	with concurrent.futures.ThreadPoolExecutor() as executor:
		for url in threadingTargets:
			futures[url] = executor.submit (job , url )
	return futures


def _concurrent_Job(job:callable, threadingTargets:list[dict], **kwargs )->dict:
	""" job : callable funtion \n
		return { threadingTargets의  index : future }\n
		reutnr 시, 사용법 \n
		for key, future in futures.items(): \n
			future.result() \n		
	"""
	futures = {}
	with concurrent.futures.ThreadPoolExecutor() as executor:
		for idx, targetDict in enumerate(threadingTargets):
			
			futures[idx] = executor.submit (job , **targetDict )
	return futures


def generate_QMsg_Information(parent:QWidget, **kwargs) -> QMessageBox.StandardButton:
    """ kwargs 
        title= title if (title:=kwargs.get('title',False)) else _defaultTitle,
        text = text if (text:=kwargs.get('text',False)) else _defaultText,
        buttons = buttons if (buttons:=kwargs.get('buttons', False)) else _defaultButtons,
        defaultButton = defaultButton if (defaultButton:=kwargs.get('defaultButton', False)) else _defaultButton,
        autoClose = msec 단위임.integer,
    """
    _defaultTitle = "Information"
    _defaultText = '정보입니다.'
    _defaultButtons = QMessageBox.StandardButton.Ok
    _defaultButton = QMessageBox.StandardButton.Ok
    
    msgBox = QMessageBox(parent)
    msgBox.setIcon(QMessageBox.Icon.Information)
    msgBox.setWindowTitle(title if (title:=kwargs.get('title',False)) else _defaultTitle)
    msgBox.setText(text if (text:=kwargs.get('text',False)) else _defaultText)
    msgBox.setStandardButtons(buttons if (buttons:=kwargs.get('buttons',False)) else _defaultButtons)
    msgBox.setDefaultButton(defaultButton if (defaultButton:=kwargs.get('defaultButton',False)) else _defaultButton)

    if autoClose := kwargs.get('autoClose', False):
        QTimer.singleShot(autoClose, msgBox.accept)

    return msgBox.exec()

QMsg_Info = generate_QMsg_Information
generate_QMsg_information = generate_QMsg_Information

def generate_QMsg_question(parent:QWidget, **kwargs) -> QMessageBox.StandardButton:
	""" kwargs \n
		title= title if (title:=kwargs.get('title',False)) else _defaultTitle, \n
		text = text if (text:=kwargs.get('text',False)) else _defaultText, \n
		buttons = buttons if (buttons :=kwargs.get('buttons', False)) else _defaultButtons,\n
		defaultButton = defaultButton if (defaultButton :=kwargs.get('defaultButton', False)) else _defaultButton,\n
	"""
	_defaultTitle = "확인"
	_defaultText = '진행하시겠읍니까?'
	_defaultButtons = QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel
	_defaultButton = QMessageBox.StandardButton.Cancel

	return QMessageBox.question(
		parent, 
		title if (title:=kwargs.get('title',False)) else _defaultTitle,
		text if (text:=kwargs.get('text',False)) else _defaultText,
		buttons if (buttons :=kwargs.get('buttons', False)) else _defaultButtons,
		defaultButton if (defaultButton :=kwargs.get('defaultButton', False)) else _defaultButton,
	)

def QMsg_question ( parent:QWidget, **kwargs ) -> bool:
	dlg_res_button = generate_QMsg_question(parent, **kwargs)
	return dlg_res_button == QMessageBox.StandardButton.Ok


def generate_QMsg_critical(parent:QWidget, **kwargs) -> QMessageBox.StandardButton:
	""" kwargs \n
		title= title if (title:=kwargs.get('title',False)) else _defaultTitle, \n
		text = text if (text:=kwargs.get('text',False)) else _defaultText, \n
		buttons = buttons if (buttons :=kwargs.get('buttons', False)) else _defaultButtons,\n
		defaultButton = defaultButton if (defaultButton :=kwargs.get('defaultButton', False)) else _defaultButton,\n
	"""
	_defaultTitle = "오류 발생"
	_defaultText = '다시 시도해 주십시요'
	_defaultButtons = QMessageBox.StandardButton.Ok
	_defaultButton = QMessageBox.StandardButton.Ok

	return QMessageBox.critical(
		parent, 
		title if (title:=kwargs.get('title',False)) else _defaultTitle,
		text if (text:=kwargs.get('text',False)) else _defaultText,
		buttons if (buttons :=kwargs.get('buttons', False)) else _defaultButtons,
		defaultButton if (defaultButton :=kwargs.get('defaultButton', False)) else _defaultButton,
	)

QMsg_Critical = generate_QMsg_critical
QMsg_critical = generate_QMsg_critical

def get_dataType(_type:str) -> str:
	""" drf 의 Field type을 받아서
		return char, integer, float, DateTime, Date, Time, M2M, FK 등 lower로 RETURN
	"""
	typeList = [ 'char', 'integer', 'float', 'datetime','date','time', 'ManyToMany','text', 'boolean']
	
	for _typeName in typeList:
		if _typeName.lower() in _type.lower():
			return _typeName.lower()
		
	return 'None'

def _getOpenFileName_only1( wid:QWidget, **kwargs) -> str|None :
	""" 
		kwargs : \n
		options : QFileDialog.Option, default QFileDialog.Option.DontUseNativeDialog \n
		title : str , default 'File Upload' \n
		path : str , default str(pathlib.Path.home() ) \n
		filter : str , default 'ALL Files(*.*)'	\n
		initialFilter : str, default 'ALL Files(*.*)'\n
	"""
	options = options  if (options :=kwargs.get('options', False)) else QFileDialog.Option.DontUseNativeDialog
	title =  title  if (title :=kwargs.get('title', False)) else 'File Upload'
	path = path if (path:= kwargs.get('path', False)) else str(pathlib.Path.home() )
	filter = filter if (filter:= kwargs.get('filter', False)) else 'ALL Files(*.*)'
	initialFilter = initialFilter if (initialFilter:= kwargs.get('initialFilter', False)) else 'ALL Files(*.*)'

	### add initialFilter to filter
	if not kwargs.get('filter', False) and kwargs.get('initialFilter', False):
		filter += f';;{initialFilter}'

	fName , _ = QFileDialog.getOpenFileName( wid, caption=title, directory=path, filter=filter, initialFilter= initialFilter, options=options)
	
	return fName if fName else None

def _getOpenFileNames_multiple( parent:QWidget, **kwargs) -> list[str]:
	""" 
		kwargs : \n
		options : QFileDialog.Option, default QFileDialog.Option.DontUseNativeDialog \n
		title : str , default 'File Upload' \n
		path : str , default str(pathlib.Path.home() ) \n
		filter : str , default 'ALL Files(*.*)'	\n
		initialFilter : str, default 'ALL Files(*.*)'\n
	"""
	options = options  if (options :=kwargs.get('options', False)) else QFileDialog.Option.DontUseNativeDialog
	title =  title  if (title :=kwargs.get('title', False)) else 'File Upload'
	path = path if (path:= kwargs.get('path', False)) else str(pathlib.Path.home() )
	filter = filter if (filter:= kwargs.get('filter', False)) else 'ALL Files(*.*)'
	initialFilter = initialFilter if (initialFilter:= kwargs.get('initialFilter', False)) else 'ALL Files(*.*)'

	### add initialFilter to filter
	if not kwargs.get('filter', False) and kwargs.get('initialFilter', False):
		filter += f';;{initialFilter}'

	fNames , _ = QFileDialog.getOpenFileNames( parent, caption=title, directory=path, filter=filter, initialFilter= initialFilter, options=options)
	
	return fNames if fNames else []

def generate_QR_Code( code:str = '') -> qrcode.image.pil.PilImage:
	img = qrcode.make(code, box_size=5)

	return img

def read_QR_Code ( img ) :	   
	return   
	# read the image in numpy array using cv2 
	# img = cv2.imread(image) 
	   
	# Decode the barcode image 
	detectedBarcodes = pyzbar.decode(img, [pyzbar.ZBarSymbol.QRCODE]) 
	   
	# If not detected then print the message 
	if not detectedBarcodes: 
		pass
 
	else:         
		  # Traverse through all the detected barcodes in image 
		for barcode in detectedBarcodes:          
    
			# # Locate the barcode position in image 
			# (x, y, w, h) = barcode.rect               
			# # Put the rectangle in image using  
			# # cv2 to highlight the barcode 
			# # cv2.rectangle(img, (x-10, y-10), 
			# #               (x + w+10, y + h+10),  
			# #               (255, 0, 0), 2) 
			  
			if barcode.data!="":                 
			# Print the barcode data 
 
 
				return barcode
			else:
				return None
		
				  


def delete_괄호_all(txt:str) -> str:
	""" txt에서 괄호포함한 그 안의 모든 txt를 삭제한 후 return"""
	pattern = r'\([^)]*\)'
	return re.sub( pattern=pattern, repl='', string=txt)


def check_file확장자_view지원(fileName:str) ->str:
	""" fileName을 받아서, 확장자명에 따라서, 'PDF', 'IMG', 'EXCEL', ... 등으로 변환, 지원안하면 '' 로, """
	fName = str(fileName).strip()[-5:]     
	확장자 = fName.split('.')[-1].upper()

	if 확장자 in INFO.IMAGE확장자:		
		return 'IMG'
	elif 확장자 in INFO.PDF확장자:		
		return 'PDF'
	
	else:
		return ''


def get_Full_URL(url:str) -> str:
	return url if 'http' in url else INFO.URI+url
	
# def read_json_file(fName:str=INFO.CONFIG_개인_FNAME ) -> dict:
# 	try:
# 		with open(fName) as user_file:
# 			return json.load(user_file)
# 	except Exception as e:

# 		return {}
	
# def write_dict_to_json_file(dataDict:dict, fName:str=INFO.CONFIG_개인_FNAME ) -> None:
# 	try:
# 		_json = read_json_file(fName)
# 		_json.update(dataDict)
# 		with open(fName, 'w') as user_file:
# 			json.dump(_json, user_file)
# 	except Exception as e:

# 		return 

def count_strings_containing(string_list:list[str], search_str:str):
    return sum(1 for s in string_list if search_str in s)

def dict_to_string(data: dict) -> str:
    """
    딕셔너리를 문자열로 변환하여 각 아이템을 개별 행으로 반환합니다.
    
    Args:
        data (dict): 변환할 딕셔너리
    
    Returns:
        str: 변환된 문자열
    """
    result = []
    for key, value in data.items():
        result.append(f"{key}: {value}")
    return "\n".join(result)



def print_list(objList:list) -> None:
	if not objList: return
	for index, elm in enumerate(objList) :
		pass


def print_dict(objDict:dict) -> None:
	if not objDict: return
	for key, value in objDict.items():
		pass

def check_str_contains_listElements(string:str, checkList:list) -> str:
	""" string이 checklist의 element를 포함하면 그 element return"""
	for elm in checkList:
		if elm in string: return elm
	return ''

def get_int_from_string(string:str) -> int|None:
	try: 
		return int(re.search(r'\d+', string).group())
	except:
		return None


def get_fName_from_url(url:str) -> str:
	if not url : return
	fName = url.split('/')[-1]
	return unquote(fName)


def wrtie_app_DB_data_to_json(app_DB_data:list=[], fName:str='', is_Sample:bool=True) ->None:
	""" app_DB_data를 보기위해서 '/debug/fName' json file로 write"""
	if not app_DB_data or not fName : return 

	dirPath='./debug'
	makeDir(dirPath)
	pathFname = f"{dirPath}/{fName}"
	if is_Sample :
		with open( pathFname, 'w') as fp:
			json.dump(app_DB_data[0], fp, ensure_ascii=False,  sort_keys=True,  indent=4,  separators=(',', ': '))
	else:
		with open( pathFname, 'w') as fp:
			json.dump(app_DB_data, fp, ensure_ascii=False,  sort_keys=True,  indent=4,  separators=(',', ': '))
		


def get_base_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller 실행 파일
        return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        # 일반 Python 실행
        return INFO.get_base_dir()
        # return os.path.dirname(os.path.abspath(__file__))

def makeDir(path: str = "debug") -> str:
    base_dir = get_base_dir()
    full_path = os.path.join(base_dir, path)
    pathlib.Path(full_path).mkdir(parents=True, exist_ok=True)
    return full_path



def get_Obj_From_ListDict_by_subDict(targetList:list, subDict:dict) -> dict:
	""" list Dict에서 subDict를 포함하는 dict return
	https://stackoverflow.com/questions/30818694/test-if-dict-contained-in-dict """
	for obj in targetList:
		obj:dict

		if subDict.items() <= obj.items(): 
			return obj
	return {}

def get_Obj_From_ListDict_by_subCondition(targetList:list=[], subCondition:dict ={}) -> dict:
	""" list Dict에서 suCondition {key:value}에서 해당key가 value를 포함하는 dict return (작성중)
	https://stackoverflow.com/questions/30818694/test-if-dict-contained-in-dict """
	if not targetList or not subCondition: return
	for obj in targetList:
		obj:dict
		try:
			for key , value in subCondition.items():
				if ( target_value := obj.get(key , None) ): 
					if value in target_value:
						return obj
		except:
			pass
	return {}

def check_obj_contains_subCondition(targetObj:dict={}, subCondition:dict={}) -> bool:
	for key, value in subCondition.items():
		if (targetValue := targetObj.get(key, None) ):
			if check_contains_str(targetValue, value): 
				return True
	return False

def check_contains_str(targetStr:str, subStr:str) -> bool:
	""" 모두 lower하여 비교"""
	if subStr.lower() in targetStr.lower():
		return True
	return False


def getOnlyNumberFromString(targetStr:str) -> list[int|float]:
	return re.findall(r'\d+', targetStr)

def getList_From_dictList(targetList:list, keyName:str, delCondition:dict ={}, addCondition:dict={} ) -> list:
	""" targetList [ obj, obj,...] 에서  obj key의  value list만 return
	 	delCondition 은 { key: value } 형태로 해당 조건 만족시 제외, default:{}"""
	if not delCondition and not addCondition:
		return  [ obj.get(keyName, '')  for obj in targetList]
	elif delCondition and not addCondition:
		return  [ obj.get(keyName, '') if not check_obj_contains_subCondition(obj, delCondition)  else '' for obj in targetList]
	elif not delCondition and addCondition:
		return  [ obj.get(keyName, '') if check_obj_contains_subCondition(obj, addCondition)  else '' for obj in targetList]
	else:
		return [ obj.get(keyName, '') if not check_obj_contains_subCondition(obj, delCondition)  and  check_obj_contains_subCondition(obj, addCondition) else '' for obj in targetList]


def _conversion_to_api_field( change_key:str, original:list) -> list:
	"""
		😀change 아래의 tuple 1번째인 '첨부file_fks'를 
		original : [('첨부file_fks', <_io.BufferedReader name='/home/kkt/Downloads.xlsx'>)]
	"""
	result = []
	for item in original:
		temp = list(item)
		temp[0]  = change_key
		result.append(tuple(temp) )
	return result

def map_view(address:str, parent:QWidget=None) -> None:
	""" address을 통해서 지도 뷰어 다이얼로그 표시"""
	try:
		if 'folium' not in cache_dict:
			from modules.PyQt.dialog.map.folium.dlg_folium import Dialog_Folium_Map
			dlg = Dialog_Folium_Map(None, address=address)
		else:
			dlg = cache_dict['folium']
			dlg.update_map(address)
		dlg.exec()
	except Exception as e:
		print (f"map_view : {e}")
		print (traceback.format_exc())
		QMessageBox.warning(parent, "경고", "pc 설정이 지도보기를 지원하지 않읍니다.")

def file_view(urls:list[str]) -> None:
	""" urls을 통해서 파일 뷰어 다이얼로그 표시"""
	from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
	dlg = FileViewer_Dialog(None, files_list=urls)
	dlg.exec()

def file_download_multiple(urls:list[str]) -> None:
    """ urls을 통해서 find dowlnload, return은 fileName"""
    if not urls: return
    try:
        for url in urls:
            func_filedownload(url)
    except Exception as e:
        generate_QMsg_critical( None, title='file_download_multiple 오류', text=f"file_download_multiple 오류: {e}")

def func_filedownload( url :str, dirPath:str=None ) -> str:
    """ url을 통해서 find dowlnload, return은 fileName"""
    if not url.startswith(('http://', 'https://')):
        url = f"{INFO.URI}{url}"
    fName, contents = download_file_from_url(url)
	
    if not fName:
        User_Toast( parent=INFO.MAIN_WINDOW, title='File Download error',	text = 'File Download error', style='ERROR')
        return ''

    if dirPath:
        makeDir(dirPath)
        path = Path(dirPath, fName)
        with open(path, 'wb') as download:
            download.write(contents)
        return path

    else:
        # options =  QtWidgets.QFileDialog.Options()
        options =  QtWidgets.QFileDialog.Option.DontUseNativeDialog
        User_fName, _ = QtWidgets.QFileDialog.getSaveFileName(parent=None ,
                                            caption="Save File", 
                                            directory=str(pathlib.Path.home() / fName), 
                                            filter="*", 
                                            options = options)
        if User_fName:
            with open(User_fName, 'wb') as download:
                download.write(contents)
            return User_fName
        else:
            return ''
            



def compare_list(list1:list, list2:list) -> bool:
	"""
		2개의 list(1번은 보통 model data 를 받아 비교하여 bool return        
	"""
	copylist1 = copy.deepcopy(list1)
	copylist2 = copy.deepcopy(list2)

	if copylist1 == copylist2 : 
		return True

	return False

def compare_list_of_dicts_strict(list1, list2):
    # 길이부터 다르면 바로 False
    if len(list1) != len(list2):
        return False
    
    # 모든 요소를 순서에 맞춰 비교
    return list1 == list2

def compare_dict_lists(list1, list2, del_keys=[]):
	# 리스트 길이 비교
	if len(list1) != len(list2):
		return False
	copyed_list1 = copy.deepcopy(list1)
	copyed_list2 = copy.deepcopy(list2)

	# ID로 정렬
	sorted_list1 = sorted(copyed_list1, key=lambda x: x.get('id', 0))
	sorted_list2 = sorted(copyed_list2, key=lambda x: x.get('id', 0))
	
	# 전체 리스트 비교
	if sorted_list1 == sorted_list2:
		return True
	
	# 상세 비교 (key, value 비교)
	for dict1, dict2 in zip(sorted_list1, sorted_list2):
		if del_keys :
			for key in del_keys:
				del dict1[key]
		if dict1.keys() != dict2.keys():
			return False
		for key in dict1:
			if dict1[key] != dict2[key]:
				return False
	
	return True

def compare_dict(dict1:dict, dict2:dict) -> bool:
	"""
		2개의 dict(1번은 dataObj==> id포함)를 받아 비교하여 bool return        
	"""
	copyDict1 = copy.deepcopy(dict1)
	copyDict2 = copy.deepcopy(dict2)
	copyDict1.pop('id', None)

	if copyDict1 == copyDict2 : 
		return True

	return False

def compare_dict_completely(dict1:dict, dict2:dict) -> bool:
	"""
		2개의 dict를 받아 비교하여 bool return        
	"""
	copyDict1 = copy.deepcopy(dict1)
	copyDict2 = copy.deepcopy(dict2)
	if copyDict1 == copyDict2 : 
		return True
	return False

def compare_dict_contains(mother:dict, child:dict) -> bool:
	"""
		mother : mother dict(포함하는 dict) , child: child dict(포함되는 dict) 
	"""
	copyMother = copy.deepcopy(mother)
	copyChild = copy.deepcopy(child)


	if copyChild.items() <=  copyMother.items() : 
		return True
	return False


def deleteLayout( cur_lay ) ->None:
	""" layout에 내용을 초기화 """
	# QtWidgets.QLayout(cur_lay)
	try:
		if cur_lay is not None:
			while cur_lay.count():
				item = cur_lay.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					deleteLayout(item.layout())
			sip.delete(cur_lay)
	except Exception as e:
		print (f"deleteLayout 오류: {e}")


def clearLayout( cur_lay ) ->None:
	""" layout에 내용을 초기화 """
	# QtWidgets.QLayout(cur_lay)
	try:
		if cur_lay is not None:
			while cur_lay.count():
				item = cur_lay.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					deleteLayout(item.layout())
	except Exception as e:
		print (f"clearLayout 오류: {e}")

def get_dictKey_byValue(targetDict:dict={}, value:object|str = None ) -> object:
	"""
		targetDict에서 value 에 따라 key를 return 
		( 예로, Chilice Field 경우 에 적용)        
	"""
	return list(targetDict.keys())[list(targetDict.values()).index(value)]


def download_file_from_url (url:str=None) ->tuple[str, bytes]:
	if not url:
		return (None, None)
	try:
		if 'http' not in url:
			url = INFO.URI+url
		response = requests.get(url)
		if response.ok:
			if 'utf-8' in ( raw := response.headers.get("Content-Disposition") ) :
				raw_fname = raw.split("filename*=")[1]
				fName = unquote(raw_fname.replace("utf-8''", ""))
			else :
				raw_fname = raw.split("filename=")[1]
				fName = raw_fname.replace('"','' )
			return (fName, response.content )

		else:       
			generate_QMsg_critical(None, title='File Download error', text=f"File Download error: {response.text}")
			return (None, None)
	except Exception as e:
		print(f"download_file_from_url 오류: {e}")
		return (None, None)

def get_AbsolutePath(path):
	cur_dir = str(pathlib.Path(__file__).parent.absolute())
	return cur_dir+path

def get_IP_Hostname():
	try: 
		hostname = socket.gethostname()
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("192.168.10.249", 80))
		return ( s.getsockname()[0] , hostname , True)
	except Exception as e:

		return ( None, None, False)
		# return (ni.ifaddresses('eth0')[ni.AF_INET][0]['addr'], 'hostname')
   

def get_Now():
	return datetime.datetime.now()

def get_timestamp():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_data_from_jsonfile(fName):
	try:
		with open(fName, encoding='utf-8') as file:
			return json.load(file)    
	except Exception as e:

		return {}

def update_dict_to_json_file(dataDict:dict, fName:str=INFO.CONFIG_개인_FNAME ) -> None:
	try:
		_json = get_data_from_jsonfile(fName)
		_json.update(dataDict)
		with open(fName, 'w', encoding='utf-8') as user_file:
			json.dump(_json, user_file, ensure_ascii=False)
	except Exception as e:

		return 

def pprint(msg=None):
	strNow = get_Now().strftime("%Y-%m-%d %H:%M:%S")



def get_TCP_LIVE_Port(start=TCP_LIVE_START, end=TCP_lIVE_END ):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
	while True:
		tcp_port = random.choice(range(start, end, 2))
		result = sock.connect_ex(('127.0.0.1',tcp_port))
		if result : 
			sock.close()
			return tcp_port

def get_TCP_Port(start=TCP_START, end=TCP_END ):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
	while True:
		tcp_port = random.choice(range(start, end))
		result = sock.connect_ex(('127.0.0.1',tcp_port))
		if result : 
			sock.close()
			return tcp_port
		
def convert_str_to_date(date_str:str) -> datetime.date:
	try:
		if isinstance(date_str, str):
			return datetime.datetime.strptime(date_str, "%Y-%m-d%").date()
		elif isinstance(date_str, datetime.date):		
			return date_str
		else:
			print(f"convert_str_to_datetime 오류: {date_str}")
			return datetime.datetime.now().date()
	except Exception as e:
		print(f"convert_str_to_datetime 오류: {e}")
		return datetime.datetime.now().date()


def convert_date_from_datestr(date_str:Optional[str]) -> datetime.date:
	try:
		if isinstance(date_str, str):
			return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
		elif isinstance(date_str, datetime.datetime):
			return date_str.date()
		elif isinstance(date_str, datetime.date):
			return date_str
		elif isinstance ( date_str, None):
			return None
		else:	
			print(f"convert_date_from_datestr 오류: {date_str}")
			return datetime.datetime.now().date()
	except Exception as e:
		print(f"convert_date_from_datestr 오류: {e}")
		return datetime.datetime.now().date()
	
def convert_date_from_datetimestr(date_str:Optional[str]) -> datetime.date:
	try:
		if isinstance(date_str, str):	
			return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
		elif isinstance(date_str, datetime.datetime):
			return date_str.date()
		elif isinstance ( date_str, None):
			return None
		else:	
			print(f"convert_date_from_datetimestr 오류: {date_str}")
			return datetime.datetime.now().date()
	except Exception as e:
		print(f"convert_date_from_datetimestr 오류: {e}")
		return datetime.datetime.now().date()
	
def get_datetime_from_datetimestr(date_str:Optional[str]) -> datetime.datetime:
	try:
		return datetime.datetime.fromisoformat(date_str)
	except Exception as e:
		print(f"get_datetime_from_datetimestr 오류: {e}")
		return datetime.datetime.now()
	
def get_date_from_datestr(date_str:Optional[str]) -> datetime.date:
	try:
		return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
	except Exception as e:
		print(f"get_date_from_datestr 오류: {e}")
		return datetime.datetime.now().date()
