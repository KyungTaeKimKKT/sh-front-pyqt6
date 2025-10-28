from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from modules.utils.api_fetch_worker import Api_Fetch_Worker

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.widget_manager import WidManager      ### singleton으로 WidgetManager 생성된 것 import
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly

import modules.user.utils as Utils
from config import Config as APP
from info import Info_SW as INFO

import traceback, time
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Base_Form_Dialog(QDialog):
    """ param 설명
        url : API 호출 url
        win_title : 창 제목
        inputType : 입력 유형
        title : 창 제목
        dataObj : 데이터 객체
        skip_generate : 생성 제외 속성
        skip_save : 저장 제외 속성
        order_attrNames : 순서 속성
        mode : 모드 (edit, readOnly)
        no_api_send : API 호출 제외 여부
        activate_base_UI : BASE(부모) UI 실행 여부
    """
    default_spacing = 32
    minium_size = (400, 300)

    def __init__(self, parent=None, url:str='', win_title:str='', 
                    inputType:dict={}, title:str='', dataObj:dict={}, 
                    skip_generate:list=['id'], skip_save:list=[],order_attrNames:list=[],
                    mode:str='edit',
                    **kwargs):
        super().__init__(parent)
        self.url = url
        self.win_title = win_title
        self.inputType = inputType
        self.title_text = title
        self.dataObj = dataObj
        self.skip_generate:list = skip_generate
        self.skip_save:list = skip_save
        self.order_attrNames:list = order_attrNames
        self.mode:str = mode    #### 'edit' or 'readOnly'
        self.is_readonly:bool = bool( mode == 'readOnly' )
        self.kwargs = kwargs

        self.inputDict = {}
        self.api_send_result = None

        if self.kwargs.get('activate_base_UI', True):
            self.UI()
        
        logger.info(f"self.is_readonly : {self.is_readonly}")
    
    @property
    def no_api_send(self) -> bool:
        """ no_api_send 속성이 있고, 그값에 따라 return , 없으면 False """
        return self.kwargs.get('no_api_send', False) 

    @no_api_send.setter
    def no_api_send(self, value:bool):
        self.kwargs['no_api_send'] = value
        
        
    def UI(self):
        
        self.setWindowTitle(self.win_title)
        if self.minium_size and isinstance(self.minium_size, tuple):
            self.setMinimumSize(*self.minium_size)
        self.vlayout = QVBoxLayout()
        self.label_title = self._UI_title()
        self.vlayout.addWidget(self.label_title)
        self.vlayout.addSpacing ( self.default_spacing )

        self.form_container = self._UI_main_form()
        self.vlayout.addWidget(self.form_container)
        self.vlayout.addSpacing ( self.default_spacing )

        self.button_container = self._UI_button()
        self.vlayout.addWidget(self.button_container)

        self.setLayout(self.vlayout)


    def _UI_title(self):
        self.label_title = QLabel(self)
        self.label_title.setText(self.title_text)
        self.label_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setStyleSheet("font-size:32px;color:white;background-color:black;")
        return self.label_title


    def _UI_main_form(self):
        #### 필수항목 경고 메시지 생성
        #### main form 생성
        self.form_container = QWidget(self)
        self.formlayout = QFormLayout()
        self.form_container.setLayout(self.formlayout)
 
        if not self.inputType:
            raise ValueError("inputType is required")
        
        _generated_ordered_inputType = { attrName:self.inputType.get(attrName) for attrName in self.order_attrNames }
        for (attrName, attrType) in _generated_ordered_inputType.items():
            if attrName in self.skip_generate : 
                continue

            if not (attrName and attrType):
                logger.error(f"attrName: {attrName}, attrType: {attrType}")
                continue
            
            _label = self._gen_label(attrName)
            _inputWidget = self._gen_inputWidget(attrName, attrType)
            logger.info(f"attrName: {attrName}, attrType: {attrType}, _label: {_label}, _inputWidget: {_inputWidget}")
            logger.info(f"_label is not None  and _inputWidget is not None: {_label is not None  and _inputWidget is not None}")
            if  _label is not None  and _inputWidget is not None:
                logger.info(f"attrName: {attrName}, attrType: {attrType}, _label: {_label}, _inputWidget: {_inputWidget}")
                # 최소 높이 보정
                # _label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
                # _inputWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                # _label.setMinimumHeight(40)
                # _inputWidget.setMinimumHeight(40)

                # # Alignment 적용 (내부 텍스트를 중앙에 오게)
                # _label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                # if isinstance(_inputWidget, QLabel):  # QLabel은 직접 적용 가능
                #     _inputWidget.setAlignment(Qt.AlignmentFlag.AlignVCenter)

                self.formlayout.addRow(_label, _inputWidget)
                self.inputDict[attrName] = _inputWidget
        return self.form_container


    def _UI_button(self):
        #### 버튼 생성
        self.button_container = QWidget(self)
        self.hlayout = QHBoxLayout()
        self.hlayout.addStretch()
        if not self.is_readonly:
            self.PB_save = QPushButton('Save')        
            self.PB_cancel = QPushButton('Cancel')
            self.hlayout.addWidget(self.PB_save)
            self.hlayout.addWidget(self.PB_cancel)  
            self.PB_save.clicked.connect(self.on_save)
            self.PB_cancel.clicked.connect(self.on_cancel)
        else:
            self.PB_save = QPushButton('닫기')
            self.hlayout.addWidget(self.PB_save)
            self.PB_save.clicked.connect(self.on_cancel)

        self.button_container.setLayout(self.hlayout)
        return self.button_container

 

    def set_title(self, title:str):
        self.label_title.setText(title) 

    def _gen_label(self, attrName:str='') -> QLabel:
        label = QLabel(self)
        label.setText(attrName)
        return label

    def _gen_inputWidget(self, attrName:str='', attrType:str='') -> QWidget:
        """ 
            생성예시:
            match attrName:
                case 'attrName1':
                    pass
                case _:
                    widget = self._gen_default_inputWidget(attrType)
            return  widget
        """
        match attrName:
            case _:
                widget = WidManager.create_widget(
                    self, 
                    field_type=attrType, 
                    data=self.dataObj.get(attrName, None),
                    is_readonly=self.is_readonly
                    )
        return  widget
    
    # def _gen_default_inputWidget(self, attrName:str='', attrType:str='', mode:str='edit'):

    #     if mode == 'edit':
    #         if attrName in self.dataObj:    
    #             return WidManager.edit_widget(self, field_type=attrType, data=self.dataObj[attrName])
    #         else:
    #             return WidManager.create_widget(self, field_type=attrType)
    #     elif mode == 'readOnly':            
    #         return WidManager.readOnly_widget(self, field_type=attrType, data=self.dataObj.get(attrName, None))

    def on_save(self):
        if self.no_api_send:
            Utils.generate_QMsg_Information(None, title='no_api_send', text='no_api_send 모드로 저장 완료', autoClose=1000)
            self.api_send_result = self.get_send_data()
            self.accept()
            return

        if self.url and self.inputDict:
            sendData, sendFiles = self.get_send_data()
            if hasattr(self, 'validate_send_data') and callable(self.validate_send_data):
                if not self.validate_send_data(sendData):
                    return

            _isOk, _json = APP.API.Send(
                url=self.url, 
                dataObj = {'id': self.dataObj.get('id', -1)} if self.dataObj.get('id') else {'id': -1}, 
                sendData = sendData,
                sendFiles = sendFiles
                )
            if _isOk:
                Utils.generate_QMsg_Information(None, title='저장 완료', text='저장 완료', autoClose=1000)
                self.api_send_result = _json
                self.accept()
            else:
                logger.error(f"저장 실패: {_json}")
                QMessageBox.warning(self, "경고", "저장 실패")
        else:
            logger.error(f"저장 실패: {self.url}")
            QMessageBox.warning(self, "경고", "저장 실패")
 
    def on_cancel(self):
        self.reject()
 
    def get_send_data(self):
        send_data = {}
        send_files = None
        for attrName, attrType in self.inputType.items():
            if attrName in self.skip_save:
                continue
            try:
                if attrName not in self.inputDict :
                    if attrName in self.dataObj:
                        send_data[attrName] = self.dataObj[attrName]                        
                    continue
                else:
                    value = WidManager.get_value(self.inputDict[attrName])
                    if value is not None:
                        send_data[attrName] = value
            except Exception as e:
                logger.error(f"get_send_data error : {e}")
                logger.error(f"self.inputDict[attrName] : {self.inputDict[attrName]}")
                logger.error(f"attrName : {attrName}")
                logger.error(f"attrType : {attrType}")
        return send_data, send_files

    def get_api_result(self):
        return self.api_send_result