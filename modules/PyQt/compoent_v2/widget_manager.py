from __future__ import annotations
from typing import Optional, Dict, Callable, Any, Type

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import date

# 커스텀 위젯 임포트
from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.my_spinbox import My_SpinBox
from modules.PyQt.component.my_dateedit import My_DateEdit

from modules.PyQt.component.combo_lineedit import Combo_LineEdit
from modules.PyQt.component.combo_lineedit_v2 import ComboLineEdit_V2
from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.imageViewer2 import ImageViewer2

from modules.PyQt.compoent_v2.Wid_label_and_pushbutton import Wid_label_and_pushbutton
from modules.PyQt.compoent_v2.Wid_lineedit_and_pushbutton import Wid_lineedit_and_pushbutton
from modules.PyQt.compoent_v2.FileListWidget.wid_fileUploadList import File_Upload_ListWidget

from modules.PyQt.compoent_v2.json_editor import Dialog_JsonEditor

from datetime import datetime, date, time

from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

CUSTOM_WIDGET_INSTANCE = (
	Wid_label_and_pushbutton, Wid_lineedit_and_pushbutton,
	File_Upload_ListWidget,
    Combo_LineEdit,
    ImageViewer, ImageViewer2,

)

class FieldTypes:
    """필드 타입 상수 정의"""
    CHAR = 'char'
    INTEGER = 'integer'
    FLOAT = 'float'
    TEXT = 'text'
    DATETIME = 'datetime'
    DATE = 'date'
    TIME = 'time'
    BOOLEAN = 'boolean'
    CHOICE = 'choice'

    MULTIFILE = 'multi_file'

    FILE_UPLOAD_LIST = 'file_upload_list'

    LABEL_AND_PUSHBUTTON = 'label_and_pushbutton'
    LINEEDIT_AND_PUSHBUTTON = 'lineedit_and_pushbutton'

    JSON = 'json'

class WidgetManager:
    """위젯 생성 및 관리를 담당하는 클래스"""

    custom_widget_instance = CUSTOM_WIDGET_INSTANCE
    
    def __init__(self):
        """위젯 매니저 초기화"""
        # 타입별 위젯 생성 함수 매핑
        self._widget_creators = {
            FieldTypes.CHAR: self._create_char_widget,
            FieldTypes.INTEGER: self._create_integer_widget,
            FieldTypes.FLOAT: self._create_float_widget,
            FieldTypes.TEXT: self._create_text_widget,
            FieldTypes.DATETIME: self._create_datetime_widget,
            FieldTypes.DATE: self._create_date_widget,
            FieldTypes.TIME: self._create_time_widget,
            FieldTypes.BOOLEAN: self._create_boolean_widget,
            FieldTypes.CHOICE: self._create_choice_widget,
            FieldTypes.MULTIFILE: self._create_multi_file_widget,

            FieldTypes.LABEL_AND_PUSHBUTTON: self._create_label_and_pushbutton_widget,
            FieldTypes.LINEEDIT_AND_PUSHBUTTON: self._create_lineedit_and_pushbutton_widget,
            FieldTypes.FILE_UPLOAD_LIST: self._create_file_upload_list_widget,
            FieldTypes.JSON: self._create_json_widget,
        }
        
        # 타입 매핑 정의
        self._type_mappings = {
            'char': FieldTypes.CHAR,
            'varchar': FieldTypes.CHAR,
            'text': FieldTypes.TEXT,
            'integer': FieldTypes.INTEGER,
            'biginteger': FieldTypes.INTEGER,
            'smallinteger': FieldTypes.INTEGER,
            'autofield': FieldTypes.INTEGER,
            'float': FieldTypes.FLOAT,
            'decimal': FieldTypes.FLOAT,
            'datetime': FieldTypes.DATETIME,
            'date': FieldTypes.DATE,
            'time': FieldTypes.TIME,
            'boolean': FieldTypes.BOOLEAN,
            'choice': FieldTypes.CHOICE,
            'foreignkey': FieldTypes.INTEGER,
            'MultiFileField': FieldTypes.MULTIFILE,

            'jsonfield': FieldTypes.JSON,


        }

        self._drf_type_mappings = {
            'CharField': FieldTypes.CHAR,
            'TextField': FieldTypes.TEXT,
            'IntegerField': FieldTypes.INTEGER,
            'FloatField': FieldTypes.FLOAT,
            'DateTimeField': FieldTypes.DATETIME,
            'DateField': FieldTypes.DATE,
            'TimeField': FieldTypes.TIME,
            'BooleanField': FieldTypes.BOOLEAN,
            'ChoiceField': FieldTypes.CHOICE,

            'MultiFileField': FieldTypes.MULTIFILE,
            'JSONField': FieldTypes.JSON,
        }

        self._set_value_handlers: Dict[Type[QWidget], Callable[[QWidget, Any], None]] = {
            QLineEdit: lambda w, v: w.setText(v or ''),
            QComboBox: lambda w, v: w.setCurrentText(v or ''),
            Choice_ComboBox: lambda w, v: w.setCurrentText(v or ''),
            QSpinBox: lambda w, v: w.setValue(int(v) if v is not None else 0),
            My_SpinBox: lambda w, v: w.setValue(int(v) if v is not None else 0),
            QDoubleSpinBox: lambda w, v: w.setValue(float(v) if v is not None else 0.0),
            # My_DoubleSpinBox: lambda w, v: w.setValue(float(v) if v is not None else 0.0),
            QCheckBox: lambda w, v: w.setChecked(bool(v)),
            QTextEdit: lambda w, v: w.setPlainText(v or ''),
            QPlainTextEdit: lambda w, v: w.setPlainText(v or ''),
            QDateEdit: lambda w, v: self.handler_set_date(w,v) , #w.setDate(v),
            My_DateEdit: lambda w, v: self.handler_set_date(w,v), #w.setDate(v),
            QDateTimeEdit: lambda w, v: w.setDateTime(v),
            Combo_LineEdit: lambda w, v: w.setValue(v),
            ImageViewer: lambda w, v: w.setValue(v),
            ImageViewer2: lambda w, v: w.setValue(v),

            QTextBrowser: lambda w, v: w.setHtml(v),
            QLabel: lambda w, v: w.setText(v),
            ### custom widget
            Wid_label_and_pushbutton: lambda w, v: w.set_value(v),
            Wid_lineedit_and_pushbutton: lambda w, v: w.set_value(v),
            File_Upload_ListWidget: lambda w, v: w.set_value(v),

            Dialog_JsonEditor: lambda w, v: w.set_value(v),
        }

        self._set_readonly_handlers: Dict[Type[QWidget], Callable[[QWidget], Any]] = {
            QLineEdit: lambda w: w.setReadOnly(True),
            QPlainTextEdit: lambda w: w.setReadOnly(True),
            QTextEdit: lambda w: w.setReadOnly(True),
            QComboBox: lambda w: w.setEnabled(False),  # QComboBox에는 setReadOnly 없음
            Choice_ComboBox: lambda w: w.setEnabled(False),
            QSpinBox: lambda w: w.setReadOnly(True),
            My_SpinBox: lambda w: w.setReadOnly(True),
            QDoubleSpinBox: lambda w: w.setReadOnly(True),
            QCheckBox: lambda w: w.setEnabled(False),
            QDateEdit: lambda w: w.setReadOnly(True),
            My_DateEdit: lambda w: w.setReadOnly(True),
            QDateTimeEdit: lambda w: w.setReadOnly(True),
            QTextBrowser: lambda w: w.setEnabled(False),  # 보통 읽기 전용임
            QLabel: lambda w: w.setEnabled(False),  # 보통 읽기 전용임
            Combo_LineEdit: lambda w: w.setReadOnly(True),
            ImageViewer: lambda w: w.setEnabled(False),  # 커스텀 위젯일 경우 접근 방법이 다를 수 있음
            ImageViewer2: lambda w: w.setEnabled(False),

            # Custom Widget 예시
            Wid_label_and_pushbutton: lambda w: w.setEnabled(False),
            Wid_lineedit_and_pushbutton: lambda w: w.set_readonly(True),
            File_Upload_ListWidget: lambda w: w.set_readonly(True),
            Dialog_JsonEditor: lambda w: w.set_readonly(True),
        }
        
        self._get_value_handlers: Dict[Type[QWidget], Callable[[QWidget], Any]] = {
            QLineEdit: lambda w: w.text(),
            QComboBox: lambda w: w.currentText(),
            QSpinBox: lambda w: w.value(),
            My_SpinBox: lambda w: w.value(),
            QDoubleSpinBox: lambda w: w.value(),
            QCheckBox: lambda w: w.isChecked(),
            QTextEdit: lambda w: w.toPlainText(),
            QPlainTextEdit: lambda w: w.toPlainText(),
            QDateEdit: lambda w: w.date().toPyDate(),
            My_DateEdit: lambda w: w.date().toPyDate(),
            QDateTimeEdit: lambda w: w.dateTime().toPyDateTime(),
            Combo_LineEdit: lambda w: w.getValue(),
            ImageViewer: lambda w: w._getValue(),
            ImageViewer2: lambda w: w._getValue(),

            QTextBrowser: lambda w: w.toPlainText(),
            QLabel: lambda w: w.text(),

            ### custom widget
            Wid_label_and_pushbutton: lambda w: w.get_value(),
            Wid_lineedit_and_pushbutton: lambda w: w.get_value(),
            File_Upload_ListWidget: lambda w: w.get_value(),
            Dialog_JsonEditor: lambda w: w.get_value(),
        }

        for custom in CUSTOM_WIDGET_INSTANCE:
            self._set_value_handlers[custom] = lambda w, v: w.set_value(v)
            self._get_value_handlers[custom] = lambda w: w.get_value()
    

    def get_data_type_from_drf_field(self, field_type: str) -> str:
        """
        Django 필드 타입에서 기본 데이터 타입을 추출합니다.
        
        Args:
            field_type: Django 필드 타입
            
        Returns:
            str: 기본 데이터 타입
        """
        data_type = self._drf_type_mappings.get(field_type, FieldTypes.CHAR)
        return data_type
    
    def set_value(self, widget: QWidget, value: Any):
        handler = self._set_value_handlers.get(type(widget))
        if handler:
            handler(widget, value)
        else:
            raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")
        
    def set_readonly(self, widget: QWidget):
        handler = self._set_readonly_handlers.get(type(widget))
        if handler:
            handler(widget)
        else:
            raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")

    def get_value(self, widget: QWidget) -> Any:
        handler = self._get_value_handlers.get(type(widget))
        if handler:
            return handler(widget)
        else:
            raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")
        
    def handler_set_date(self, widget:QWidget, value:Any):
        if isinstance ( value, str):
            value = QDate.fromString(value, 'yyyy-MM-dd')

        if isinstance( widget, QDateEdit):
            widget.setDate(value)
        else:
            widget.setDate(value)
    # def set_value(self, widget:QWidget, value:Any):
    #     if isinstance( widget, QLineEdit ):
    #         widget.setText(value)
    #     elif isinstance( widget, QComboBox ):
    #         widget.setCurrentText(value)
    #     elif isinstance( widget, QSpinBox ):
    #         widget.setValue(value)
    #     elif isinstance( widget, QCheckBox ):
    #         widget.setChecked(value)
    #     elif isinstance( widget, QTextEdit):
    #         widget.setPlainText(value)
    #     elif isinstance( widget, QPlainTextEdit):
    #         widget.setPlainText(value)
    #     elif isinstance( widget, QDoubleSpinBox):
    #         widget.setValue(value)
    #     elif isinstance( widget, QDateEdit ):
    #         widget.setDate(value)
    #     elif isinstance( widget, QDateTimeEdit ):
    #         widget.setDateTime(value)
    #     elif isinstance( widget, Combo_LineEdit):
    #         widget.setValue(value)
    #     elif isinstance( widget, ImageViewer):
    #         widget.setValue(value)
    #     elif isinstance( widget, ImageViewer2):
    #         widget.setValue(value)
    #     elif isinstance( widget, self.custom_widget_instance):
    #         widget.set_value(value)
    #     else:
    #         raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")
    
    # def get_value(self, widget:QWidget) -> Any:
    #     if isinstance( widget, QLineEdit ):
    #         return widget.text()
    #     elif isinstance ( widget, QComboBox ):
    #         return widget.currentText()
    #     elif isinstance ( widget, QSpinBox ):
    #         return widget.value()
    #     elif isinstance ( widget, QCheckBox ):
    #         return widget.isChecked()
    #     elif isinstance ( widget, QTextEdit):
    #         return widget.toPlainText()		
    #     elif isinstance (widget, QPlainTextEdit):
    #         return widget.toPlainText()
    #     elif isinstance (widget, QDoubleSpinBox):
    #         return widget.value()
        
    #     elif isinstance ( widget, QDateEdit ):
    #         return widget.date().toPyDate()
        
    #     elif isinstance ( widget, QDateTimeEdit ):
    #         return widget.dateTime().toPyDateTime()
        
    #     elif isinstance( widget, Combo_LineEdit):
    #         return widget.getValue()
        
    #     elif isinstance(widget, ImageViewer):
    #         return widget._getValue()
        
    #     elif isinstance(widget, ImageViewer2):
    #         return widget._getValue()
        
    #     elif isinstance( widget, QCheckBox):
    #         return widget.isChecked()
        
    #     elif isinstance ( widget, ComboLineEdit_V2):
    #         return widget.getValue()
        
    #     #### custom widget경우
    #     elif isinstance( widget, self.custom_widget_instance):
    #         return widget.get_value()
        
    #     else:
    #         raise ValueError(f"지원하지 않는 위젯 타입입니다: {type(widget)}")


    def readOnly_widget( self, parent:QWidget, field_type:str,  data:any, is_readonly:bool=True, **kwargs) -> QWidget:
        """
        읽기 전용 위젯을 생성합니다.
        """
        wid = self.create_widget(parent, field_type, data, is_readonly, **kwargs)
        return wid
    
    def edit_widget( self, parent:QWidget, field_type:str,  data:any, is_readonly:bool=False, **kwargs) -> QWidget:
        """
        위젯을 수정합니다.
        """
        wid = self.create_widget(parent, field_type, data, is_readonly, **kwargs)
        return wid
    
    def create_widget(self, parent: QObject, field_type: str, data:Optional[Any]=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """
        필드 타입에 맞는 위젯을 생성합니다.
        
        Args:
            parent: 부모 위젯
            field_type: 필드 타입 (drf or Pyqt6) 즉, Field면 drf, 아니면 Pyqt6
            
        Returns:
            QWidget: 생성된 위젯
        """
        if 'Field' in field_type:
            data_type = self.get_data_type_from_drf_field(field_type)
        else:
            data_type = self.get_data_type_from_field(field_type)
        logger.debug(f"create_widget: field_type: {field_type}, data_type: {data_type}")
        
        # 해당 타입의 위젯 생성 함수 호출
        creator = self._widget_creators.get(data_type, self._create_char_widget)
        logger.debug(f"creator: {creator}")
        wid = creator(parent, data, is_readonly, **kwargs)
        logger.debug(f"wid: {wid}")
        return wid
    
    def get_data_type_from_field(self, field_type: str) -> str:
        """
        Django 필드 타입에서 기본 데이터 타입을 추출합니다.
        
        Args:
            field_type: Django 필드 타입
            
        Returns:
            str: 기본 데이터 타입
        """
        if not field_type:
            return FieldTypes.CHAR
            
        field_type = field_type.lower()
        
        # 필드 타입에 매핑된 타입 찾기
        for key, value in self._type_mappings.items():
            if key in field_type:
                return value
        
        # 기본값 반환
        return FieldTypes.CHAR
    
    def _create_char_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """문자열 입력 위젯 생성"""
        widget = QLineEdit(parent)
        if data is not None and data:
            widget.setText(data)
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_integer_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """정수 입력 위젯 생성"""
        widget = My_SpinBox(parent) if 'My_SpinBox' in globals() else QSpinBox(parent)
        widget.setRange(0, 2_100_000_000)  # int32의 최대값
        if data is not None and isinstance(data, int):
            widget.setValue(data)
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_float_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """실수 입력 위젯 생성"""
        widget = QDoubleSpinBox(parent)
        widget.setRange(0, 1000000)
        widget.setDecimals(2)
        if data is not None and isinstance(data, float):
            widget.setValue(data)
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_text_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """텍스트 입력 위젯 생성"""
        widget = QPlainTextEdit(parent)
        widget.setMinimumHeight(96)
        if data is not None and data:
            widget.setPlainText(data)
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_datetime_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """날짜시간 입력 위젯 생성"""
        widget = My_DateEdit(parent) if 'My_DateEdit' in globals() else QDateTimeEdit(parent)
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("yy. M. d. hh:mm")
        widget.setTimeSpec(Qt.TimeSpec.LocalTime)
        if data is not None and data:
            widget.setDateTime(data)
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_date_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """날짜 입력 위젯 생성"""
        widget = My_DateEdit(parent) if 'My_DateEdit' in globals() else QDateEdit(parent)
        widget.setCalendarPopup(True)
        widget.setTimeSpec(Qt.TimeSpec.LocalTime)
        if data is not None and data:
            if isinstance(data, str):
                widget.setDate(datetime.strptime(data, '%Y-%m-%d').date())
            elif isinstance(data, datetime):
                widget.setDate(data.date())
            elif isinstance(data, date):                    
                widget.setDate(data)
            else:
                raise ValueError(f"지원하지 않는 날짜 타입입니다: {type(data)}")
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_time_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """시간 입력 위젯 생성"""
        widget = QTimeEdit(parent)
        widget.setDisplayFormat("hh:mm:ss")
        widget.setTimeSpec(Qt.TimeSpec.LocalTime)
        if data is not None and data:
            if isinstance(data, str):
                widget.setTime(datetime.strptime(data, '%H:%M:%S').time())
            elif isinstance(data, datetime):
                widget.setTime(data.time())
            elif isinstance(data, time):
                widget.setTime(data)
            else:
                raise ValueError(f"지원하지 않는 시간 타입입니다: {type(data)}")
        if is_readonly:
            widget.setReadOnly(True)
        return widget

    def _create_boolean_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """불리언 입력 위젯 생성"""
        widget = QCheckBox(parent)
        if data is not None and data and isinstance(data, bool):
            widget.setChecked(data)
        if is_readonly:
            widget.setEnabled(False)
        return widget

    def _create_choice_widget(self, parent: QObject, data:any=None, is_readonly:bool=False,choice_list:list[dict]=None, **kwargs) -> QWidget:
        """선택 입력 위젯 생성"""
        widget = QComboBox(parent)
        if choice_list:
            map_value_to_display = {item['value']: item['display'] for item in choice_list}
            widget.addItems( [item['display'] for item in choice_list] )
        else:
            map_value_to_display = {}
        
        if data is not None and data:
            if map_value_to_display:
                widget.setCurrentText(map_value_to_display.get(data, data))
            else:
                widget.setCurrentText(data)
        if is_readonly:
            widget.setEnabled(False)
        return widget
    
    def _create_multi_file_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """다중 파일 입력 위젯 생성"""
        widget = File_Upload_ListWidget(parent)
        if data is not None and data:
            widget.add_files(data)
        if is_readonly:
            widget.setEnabled(False)
        return widget
    
    def _create_label_and_pushbutton_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """라벨과 버튼 위젯 생성"""
        widget = Wid_label_and_pushbutton(parent, data, is_readonly, **kwargs)
        return widget


    def _create_lineedit_and_pushbutton_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """라인에디트와 버튼 위젯 생성"""
        widget = Wid_lineedit_and_pushbutton(parent, data, is_readonly, **kwargs)
        return widget
    
    def _create_file_upload_list_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """파일 업로드 리스트 위젯 생성"""
        widget = File_Upload_ListWidget(parent, data, is_readonly, **kwargs)
        # if is_readonly:
        #     widget.setEnabled(False)
        return widget

    def _create_json_widget(self, parent: QObject, data:any=None, is_readonly:bool=False, **kwargs) -> QWidget:
        """JSON 입력 위젯 생성"""
        widget = Dialog_JsonEditor(parent)
        if data is not None and data:
            widget.set_value(data)
        if is_readonly:
            widget.set_readonly(True)
        return widget


    # 싱글톤 인스턴스
    _instance = None
    
    @classmethod
    def instance(cls) -> WidgetManager:
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = WidgetManager()
        return cls._instance 
    
WidManager = WidgetManager.instance()