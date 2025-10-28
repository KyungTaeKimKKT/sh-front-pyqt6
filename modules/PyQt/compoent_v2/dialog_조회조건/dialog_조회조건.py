from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

from functools import partial
import pandas as pd
import urllib
from datetime import date, datetime
import copy

import pathlib
import openpyxl
import typing

import concurrent.futures
import asyncio
import time


from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils

from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value

from modules.PyQt.QRunnable.work_async import Worker, Worker_Post

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

class Dialog_Base_조회조건(QDialog):
    """
        조회조건 설정 다이얼로그
        input_dict : 조회조건 설정 항목
        default_dict : 조회조건 설정 기본값
    """

    result_signal = pyqtSignal(dict)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("조회 조건 설정" if not hasattr(kwargs, 'title') else kwargs['title'])

        self.input_dict = kwargs.get('input_dict', {})
        self.default_dict = kwargs.get('default_dict', {})
        self.config_kwargs = kwargs.get('config_kwargs', {})

        self.created_widgets: dict[str, QWidget] = {}  # 생성된 위젯을 저장할 딕셔너리
        self.complicated_widgets: dict[str, list[QWidget]] = {}  # 복합 위젯을 저장할 딕셔너리
        self.button_groups = {}  # 라디오 버튼 그룹을 저장할 딕셔너리

        layout = QFormLayout(self)

        self.confirm_button = QPushButton('확인', self)
        self.confirm_button.clicked.connect(self._on_confirm_clicked)
        layout.addRow(self.confirm_button)

        self.result_dict = {}

        if 'input_dict' in kwargs:
            for key, widget_type in kwargs['input_dict'].items():
                widget = self._create_widget(widget_type, key)
                self.created_widgets[key] = widget
                if widget_type.startswith('Range'):
                    checkbox = QCheckBox(key, self)
                    checkbox.setChecked(False)
                    # 시그널 연결 부분 확인
                    checkbox.stateChanged.connect(lambda state, k=key: self._toggle_range_widget(k, state))
                    layout.addRow(checkbox, widget)
                    widget.setVisible(False)
                    widget.setEnabled(False)

                else:
                    layout.addRow(QLabel(key, self), widget)

        if 'default_dict' in kwargs:
            for key, value in kwargs['default_dict'].items():
                widget = self.created_widgets.get(key)
                if widget:
                    self._set_widget_value(widget, value, key)

        self.setLayout(layout)
        self.show()

    def _create_widget(self, widget_type, key: str) -> QWidget:
        match widget_type:
            case 'QLineEdit':
                return QLineEdit(self)
            case 'QComboBox':
                return QComboBox(self)
            case 'QCheckBox':
                return QCheckBox(self)
            case 'QDateEdit':
                dateedit = QDateEdit(self)
                dateedit.setCalendarPopup(True)
                return dateedit
            case 'QSpinBox':
                spinbox = QSpinBox(self)
                spinbox.setRange(0, 2**31 - 1)
                return spinbox
            case 'QDoubleSpinBox':
                spinbox = QDoubleSpinBox(self)
                spinbox.setRange(0, 1.7976931348623157e+308)
                return spinbox
            case 'QDateTimeEdit':
                datetimeedit = QDateTimeEdit(self)
                datetimeedit.setCalendarPopup(True)
                return datetimeedit
            case 'QRadioButton':
                button_group = QButtonGroup(self)
                self.button_groups[key] = button_group
                options = self.config_kwargs.get('radios', {}).get(key, [])
                layout = QHBoxLayout()
                for option in options:
                    radio_button = QRadioButton(option, self)
                    button_group.addButton(radio_button)
                    layout.addWidget(radio_button)
                container = QWidget(self)
                container.setLayout(layout)
                return container
            case 'Range_SpinBox':
                container = QFrame(self)
                layout = QVBoxLayout(container)
                spinbox_from = QSpinBox(container)
                spinbox_from.setRange(0, 2**31 - 1)
                spinbox_to = QSpinBox(container)
                spinbox_to.setRange(0, 2**31 - 1)
                layout.addWidget(spinbox_from)
                layout.addWidget(spinbox_to)
                container.setLayout(layout)
                self.complicated_widgets[key] = [spinbox_from, spinbox_to]
                return container
            case 'Range_DateEdit':
                container = QFrame(self)
                layout = QVBoxLayout(container)
                dateedit_from = QDateEdit(container)
                dateedit_from.setCalendarPopup(True)
                dateedit_to = QDateEdit(container)
                dateedit_to.setCalendarPopup(True)
                layout.addWidget(dateedit_from)
                layout.addWidget(dateedit_to)
                container.setLayout(layout)
                self.complicated_widgets[key] = [dateedit_from, dateedit_to]
                return container
            case _:
                raise ValueError(f"Unsupported widget type: {widget_type}")

    def _set_widget_value(self, widget, value, key: str):
        if key in self.complicated_widgets:
            from_widget, to_widget = self.complicated_widgets[key]
            Object_Set_Value(from_widget, value['From'])
            Object_Set_Value(to_widget, value['To'])
        else:
            match widget:
                case QLineEdit():
                    widget.setText(value)
                case QComboBox():
                    widget.setCurrentText(str(value))
                case QCheckBox():
                    widget.setChecked(value)
                case QDateEdit():
                    if isinstance(value, str):
                        value = QDate.fromString(value, Qt.ISODate)
                    widget.setDate(value)
                case QSpinBox() | QDoubleSpinBox():
                    widget.setValue(value)
                case QDateTimeEdit():
                    if isinstance(value, str):
                        value = QDateTime.fromString(value, Qt.ISODate)
                    widget.setDateTime(value)
                case QWidget():
                    for radio_button in widget.findChildren(QRadioButton):
                        if radio_button.text() == value:
                            radio_button.setChecked(True)
                            break
                case _:
                    raise ValueError(f"{key} : Unsupported widget type: {type(widget)}")

    def _get_widget_value(self, widget, key: str):
        if key in self.complicated_widgets:
            if widget.isVisible() and widget.isEnabled():
                from_widget, to_widget = self.complicated_widgets[key]
                return {'From': Object_Get_Value(from_widget).get(), 'To': Object_Get_Value(to_widget).get()}
            else:
                return None
        else:
            match widget:
                case QLineEdit():
                    return widget.text()
                case QComboBox():
                    return widget.currentText()
                case QCheckBox():
                    return widget.isChecked()
                case QDateEdit():
                    return widget.date().toString(Qt.ISODate)
                case QSpinBox() | QDoubleSpinBox():
                    return widget.value()
                case QDateTimeEdit():
                    return widget.dateTime().toString(Qt.ISODate)
                case QWidget():
                    for radio_button in widget.findChildren(QRadioButton):
                        if radio_button.isChecked():
                            return radio_button.text()
                case _:
                    return None

    @pyqtSlot(str, int)
    def _toggle_range_widget(self, key: str, state: int):
        ic(key, state)
        widget = self.created_widgets.get(key)
        ic(widget)
        if widget:
            is_checked = (Qt.CheckState(state) == Qt.Checked)  # state를 CheckState로 변환하여 비교
            ic(is_checked, state, Qt.Checked, Qt.Unchecked )
            widget.setVisible(is_checked)
            widget.setEnabled(is_checked)

    @pyqtSlot()
    def _on_confirm_clicked(self):
        result_dict = {}
        for key, widget in self.created_widgets.items():
            value = self._get_widget_value(widget, key)
            if value not in [None, '', 'all', 'All', 'ALL']:
                result_dict[key] = value
        self.result_signal.emit(result_dict)
        self.close()