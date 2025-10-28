from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


import json, os, io, copy
import platform
from datetime import datetime
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class SliderEditor(QWidget):
    valueChanged = pyqtSignal(int)  # 슬라이더 내부 시그널

    def __init__(self, step=20, max_score=5.0, parent=None):
        super().__init__(parent)
        self.환산 = int(step / max_score)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(step)
        self.slider.setSingleStep(1)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.label = QLabel("0.0")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.valueChanged.connect(self._on_value_changed)
        self.setStyleSheet("background-color: lightyellow;")



    def _on_value_changed(self, val):
        float_val = val / self.환산
        self.label.setText(f"{float_val:.1f}")
        self.valueChanged.emit(val)

    def set_value(self, float_val: float):
        self.slider.setValue(int(float_val * self.환산))

    def get_value(self) -> float:
        return self.slider.value() / self.환산
    

class 평가TableModel(QAbstractTableModel):
    def __init__(self, data: list[dict], parent=None):
        super().__init__(parent)
        self.headers = ['구분', '항목', '정의', '평가점수']
        self._data = data
        self.is_submit = False

    def set_data(self, data: list[dict]):
        if not isinstance(data, list):
            raise TypeError("data must be a list of dicts")
        self._data = data
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        항목_data = self._data[row]['항목_data']

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return 항목_data['구분']
            elif col == 1:
                return 항목_data['항목_이름']
            elif col == 2:
                return 항목_data['정의']
            elif col == 3:
                return f"{self._data[row]['평가점수']:.1f}"

        if role == Qt.ItemDataRole.EditRole and col == 3:
            return self._data[row]['평가점수']

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole and index.column() == 3:
            try:
                self._data[index.row()]['평가점수'] = float(value)
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
                return True
            except ValueError:
                return False
        return False

    def flags(self, index):        
        if self.is_submit:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        if index.column() == 3:
            return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def set_Editable(self, is_submit:bool):
        self.is_submit = is_submit
        self.layoutChanged.emit()

class SliderDelegate(QStyledItemDelegate):
    valueChanged = pyqtSignal(float, QModelIndex)

    MAX_STEP = 50
    MAX_SCORE = 5.0
    환산 = int(MAX_STEP / MAX_SCORE)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slider = None
        self._current_index = None

    def createEditor(self, parent, option, index):
        # editor 직접 생성 안함
        return None

    def editorEvent(self, event, model, option, index):

        if model.is_submit:
            return False

        if self.hide_slider(index):
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            # 이미 슬라이더가 있으면 이전 것은 숨김
            if self._slider:
                self._slider.hide()

            # 슬라이더 생성 또는 재사용
            if not self._slider:
                self._slider = SliderEditor(
                    parent=option.widget,
                    step=self.MAX_STEP,
                    max_score=self.MAX_SCORE
                    )  # 최상위 윈도우로 부모 지정
                self._slider.valueChanged.connect(lambda val: self.on_slider_value_changed(val, self._current_index, model))

            # 현재 클릭한 인덱스 저장
            self._current_index = index

            # 슬라이더 크기와 위치 지정
            slider_width = 120
            slider_height = option.rect.height()
            x = option.rect.right() + 5  # 오른쪽 5px 띄움
            y = option.rect.top()

            # option.widget은 QTableView일 가능성이 높으므로
            # 절대좌표 변환 필요 (mapToGlobal 등)
            table = option.widget
            global_pos = table.viewport().mapToGlobal(option.rect.topRight())
            # 슬라이더 부모도 윈도우라서 global_pos -> 윈도우 좌표 변환
            window_pos = self._slider.parent().mapFromGlobal(global_pos)

            self._slider.setGeometry(window_pos.x() + 5, window_pos.y(), slider_width, slider_height)
            self._slider.show()
            self._slider.raise_()

            # 현재 값 세팅
            current_value = model.data(index, Qt.ItemDataRole.EditRole)
            if current_value is None:
                current_value = 0.0
            self._slider.set_value(float(current_value))

            self._slider.setFocus()

            return True
        return False

    def on_slider_value_changed(self, value, index, model):
        value = value / self.환산
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        self.valueChanged.emit(value, index)

    def hide_slider(self, index:QModelIndex):
        if index.column() != 3:
            # 다른 컬럼 클릭 시 슬라이더 숨기기
            if self._slider:
                self._slider.hide()
                self._current_index = None
        return index.column() != 3
    
class 점수_Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        from modules.PyQt.compoent_v2.custom_상속.custom_spinbox import Custom_DobleSpinBox
        editor = Custom_DobleSpinBox(parent)
        editor.setRange(0, 5)
        editor.setSingleStep(0.01)
        return editor

class Wid_table_역량평가(QWidget):
    ROW_HEIGHT = 40
    
    def __init__(self, parent, 역량평가_api_datas:list[dict] = []):
        super().__init__(parent)
        self.역량평가_api_datas = 역량평가_api_datas
        self._is_initialized = False
        self.map_id_dict :dict[int, dict] = {}
        self.평가체계_dict = None
        self.is_submit = False

        if self.역량평가_api_datas:
            self.set_api_datas(self.역량평가_api_datas)

    def set_api_datas(self, api_datas:list[dict], 평가체계_dict:dict=None):
        self.역량평가_api_datas = api_datas
        self.평가체계_dict = 평가체계_dict
        self.is_submit = 평가체계_dict['is_submit'] 
        if not self._is_initialized:
            self.UI()

        self.model.set_data(api_datas)
        self.model.set_Editable( self.is_submit )

    def get_api_datas(self) -> list[dict]:
        return self.model._data

    def UI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.summary_layout = QHBoxLayout()
        # self.label_summary = QLabel("가중치 합은 100 이어야 합니다.")
        # self.summary_layout.addWidget(self.label_summary)
        # self.label_summary_value = QLabel("")
        # self.label_summary_value.setMinimumWidth( 160 )
        # self.label_summary_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.summary_layout.addWidget(self.label_summary_value)
        self.summary_layout.addStretch()
                        # 버튼
        # btn_layout = QHBoxLayout()
        # save_btn = QPushButton("저장")
        # save_btn.clicked.connect(self.on_save_clicked)
        # btn_layout.addWidget(save_btn)
        # self.summary_layout.addLayout(btn_layout)
        layout.addLayout(self.summary_layout)

        self.view = QTableView()
        layout.addWidget(self.view)

        self.model = 평가TableModel(self.역량평가_api_datas)
        self.view.setModel(self.model)

        # self.slider_delegate = SliderDelegate()
        # self.view.setItemDelegateForColumn(3, self.slider_delegate)
        # self.slider_delegate.valueChanged.connect(self.on_value_changed)

        self.점수_delegate = 점수_Delegate()
        self.view.setItemDelegateForColumn(3, self.점수_delegate)
        # self.점수_delegate.valueChanged.connect(self.on_value_changed)

        self.view.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)
        self.view.setAlternatingRowColors(True)
        self.view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.view.resizeColumnsToContents()

        # ID 저장
        self.id_score_map = {i: row['id'] for i, row in enumerate(self.역량평가_api_datas)}

        self.view.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        self.view.setAlternatingRowColors(True)
        self.view.setEditTriggers(QTableView.EditTrigger.DoubleClicked)

        self.view.clicked.connect(self.handle_table_clicked)
        self._is_initialized = True

    def handle_table_clicked(self, index):
        return 
        # 슬라이더 제거 요청
        self.slider_delegate.hide_slider(index)

    def on_save_clicked(self):
        if hasattr(self, 'url') and self.url:
            data = {'역량평가':json.dumps(list(self.map_id_dict.values()), ensure_ascii=False)}
            logger.info(f"저장 데이터 : {data}")
            is_ok, _json = APP.API.post_json(
                 self.url, 
                 data= data,
                 headers = {'Content-Type': 'application/json'}
                 )
            if is_ok:
                Utils.generate_QMsg_Information( self.parent(), title="저장 완료", text="저장 완료", autoClose=1000)
            else:
                Utils.generate_QMsg_critical( self.parent(), title="저장 실패", text="저장 실패")
        else:
            Utils.generate_QMsg_critical( self.parent(), title="저장 실패", text="저장 실패" )

       

    def on_value_changed(self, value: float, index: QModelIndex):
        return 
        row = index.row()
        id_ = self.id_score_map.get(row)
        self.map_id_dict[id_] = {'id': id_, '평가점수': value}


    def set_url(self, url:str):
        self.url = url

if __name__ == '__main__':
    역량평가_api_datas= [{'id': 2857, '역량평가_fk': 353, '항목': 45, '평가점수': 0.0, '항목_data': {'id': 45, '평가설정_fk': 44, '항목': 6, '차수': 2, '항목_이름': '긍정성', '구분': '공통역량', '정의': '어떤 현안(주제, 방침, 업무, 관계 등)에 대해 이해, 인정, 수용 또는  개선/극복하려는 태도나 이를 표현하는 말과 행동을 보인다.'}}, {'id': 2858, '역량평가_fk': 353, '항목': 46, '평가점수': 0.0, '항목_data': {'id': 46, '평가설정_fk': 44, '항목': 2, '차수': 2, '항목_이름': '열정', '구분': '공통역량', '정의': '적극적이고 능동적인 자세로 업무를 수행하고 자신의 분야에서 최고가 된다는 열망을 가지고 노력한다.'}}, {'id': 2859, '역량평가_fk': 353, '항목': 47, '평가점수': 0.0, '항목_data': {'id': 47, '평가설정_fk': 44, '항목': 3, '차수': 2, '항목_이름': '원칙준수', '구분': '공통역량', '정의': '자신의 편의를 위해 편법을 동원하지 않고 정해진 규정과 지침, 절차를 이해하고 이에 따라 공정하고 투명하게 업무를 처리한다.'}}, {'id': 2860, '역량평가_fk': 353, '항목': 48, '평가점수': 0.0, '항목_data': {'id': 48, '평가설정_fk': 44, '항목': 8, '차수': 2, '항목_이름': '자기조절', '구분': '공통역량', '정의': '업무로 인한 스트레스를 경험하거나 부정적인 행동을 취하고 싶은 유혹에도 불구하고 자신의 감정을 조절하고 자제할 수 있다.'}}, {'id': 2861, '역량평가_fk': 353, '항목': 49, '평가점수': 0.0, '항목_data': {'id': 49, '평가설정_fk': 44, '항목': 7, '차수': 2, '항목_이름': '주인의식', '구분': '공통역량', '정의': '높은 공동체 의식과 투철한 직업정신(윤리)를 바탕으로 조직 전체의 목표를 달성하기 위해 적극적으로 참여하고 헌신할 수 있다.'}}, {'id': 2862, '역량평가_fk': 353, '항목': 50, '평가점수': 0.0, '항목_data': {'id': 50, '평가설정_fk': 44, '항목': 4, '차수': 2, '항목_이름': '팀워크', '구분': '공통역량', '정의': '주어진 업무를 수행함에 있어 업무를 적절히 분담하고, 긴밀한 협력을 통해 주어진 과제를 완수한다'}}, {'id': 2863, '역량평가_fk': 353, '항목': 51, '평가점수': 0.0, '항목_data': {'id': 51, '평가설정_fk': 44, '항목': 5, '차수': 2, '항목_이름': '프로정신', '구분': '공통역량', '정의': '자신이 하는 일에 대한 사명감과 자부심을 가지고, 어떠한 상황에서도 최고가 되기 위하여 자신을 관리한다.'}}, {'id': 2864, '역량평가_fk': 353, '항목': 52, '평가점수': 0.0, '항목_data': {'id': 52, '평가설정_fk': 44, '항목': 19, '차수': 2, '항목_이름': '결과', '구분': '리더십역량', '정의': '일에 대한 높은 관심과 동기가 있어 매우 과업지향적으로 행동한다.'}}, {'id': 2865, '역량평가_fk': 353, '항목': 53, '평가점수': 0.0, '항목_data': {'id': 53, '평가설정_fk': 44, '항목': 23, '차수': 2, '항목_이름': '설득', '구분': '리더십역량', '정의': '필요한 자원 확보나 지지 획득을 위해 내외부 관계자의 지지를 얻어내고 협력적 네트워크 관계를 구축한다.'}}, {'id': 2866, '역량평가_fk': 353, '항목': 54, '평가점수': 0.0, '항목_data': {'id': 54, '평가설정_fk': 44, '항목': 16, '차수': 2, '항목_이름': '육성', '구분': '리더십역량', '정의': '구성원 개개인에 대해 애정과 관심을 가지고 대하며, 개인의 능력과 적성을 고려하여 성장할 수 있도록 배려한다'}}, {'id': 2867, '역량평가_fk': 353, '항목': 55, '평가점수': 0.0, '항목_data': {'id': 55, '평가설정_fk': 44, '항목': 21, '차수': 2, '항목_이름': '점검', '구분': '리더십역량', '정의': '일의 진행 과정을 정확하게 파악하고 있으며, 구성원들이 주어진 업무를 정해진 시간 안에 수행하는지 점검한다.'}}, {'id': 2868, '역량평가_fk': 353, '항목': 56, '평가점수': 0.0, '항목_data': {'id': 56, '평가설정_fk': 44, '항목': 20, '차수': 2, '항목_이름': '주도', '구분': '리더십역량', '정의': '어려운 상황에서도 방향을 분명하게 결정하고 추진해 나가면서 구성원들을 이끈다.'}}, {'id': 2869, '역량평가_fk': 353, '항목': 57, '평가점수': 0.0, '항목_data': {'id': 57, '평가설정_fk': 44, '항목': 22, '차수': 2, '항목_이름': '체계', '구분': '리더십역량', '정의': '담당 조직의 역할을 명확히 하고, 조직 구조와 업무 프로세스를 지속적으로 점검 및 정비한다.'}}, {'id': 2870, '역량평가_fk': 353, '항목': 58, '평가점수': 0.0, '항목_data': {'id': 58, '평가설정_fk': 44, '항목': 17, '차수': 2, '항목_이름': '팀워크', '구분': '리더십역량', '정의': '구성원들의 갈등을 적극적으로 해소하고 구성원들의 참여와 결속을 다진다'}}, {'id': 2871, '역량평가_fk': 353, '항목': 59, '평가점수': 0.0, '항목_data': {'id': 59, '평가설정_fk': 44, '항목': 18, '차수': 2, '항목_이름': '혁신', '구분': '리더십역량', '정의': '기존의 관행이나 고정 관념을 탈피하여 발상을 전환하고, 혁신과 창의의 필요성과 바람직성을 구성원에게 확신시킨다'}}, {'id': 2872, '역량평가_fk': 353, '항목': 60, '평가점수': 0.0, '항목_data': {'id': 60, '평가설정_fk': 44, '항목': 10, '차수': 2, '항목_이름': '고객마인드', '구분': '직무역량(공통)', '정의': '조직의 내부 고객과 외부 고객의 요구를 만족시킬 수 있다.'}}, {'id': 2873, '역량평가_fk': 353, '항목': 61, '평가점수': 0.0, '항목_data': {'id': 61, '평가설정_fk': 44, '항목': 12, '차수': 2, '항목_이름': '분석적 사고', '구분': '직무역량(공통)', '정의': '주어진 상황/과제/문제를 보다 세부적인 단위로 분해하여 분석하고, 단계적인 방법으로 상황/과제/문제의 의미를 파악할 수 있다.'}}, {'id': 2874, '역량평가_fk': 353, '항목': 62, '평가점수': 0.0, '항목_data': {'id': 62, '평가설정_fk': 44, '항목': 15, '차수': 2, '항목_이름': '업무관리', '구분': '직무역량(공통)', '정의': '주어진 시간 내에 목표를 달성할 수 있도록 긴급성, 중요성 등을 감안하여 자신의 시간을 효율적으로 활용하는 역량'}}, {'id': 2875, '역량평가_fk': 353, '항목': 63, '평가점수': 0.0, '항목_data': {'id': 63, '평가설정_fk': 44, '항목': 14, '차수': 2, '항목_이름': '의사전달', '구분': '직무역량(공통)', '정의': '자신의 의견을 명확하게 전달하며, 자신의 견해를 확실하게 피력할 수 있다.'}}, {'id': 2876, '역량평가_fk': 353, '항목': 64, '평가점수': 0.0, '항목_data': {'id': 64, '평가설정_fk': 44, '항목': 11, '차수': 2, '항목_이름': '전략적 사고', '구분': '직무역량(공통)', '정의': '이슈 또는 문제를 명확히 인식하여 그 원인을 분석하고 최적의 대안을 도출하여 실행함으로써 바람직한 목표 수준에 도달하기 위해 노력할 수 있다.'}}, {'id': 2877, '역량평가_fk': 353, '항목': 65, '평가점수': 0.0, '항목_data': {'id': 65, '평가설정_fk': 44, '항목': 9, '차수': 2, '항목_이름': '전문지식', '구분': '직무역량(공통)', '정의': '자신의 업무와 관계된 최신 지식이나 정보를 빠르게 흡수하고 업무에 적용할 수 있다.'}}, {'id': 2878, '역량평가_fk': 353, '항목': 66, '평가점수': 0.0, '항목_data': {'id': 66, '평가설정_fk': 44, '항목': 13, '차수': 2, '항목_이름': '창의적 사고', '구분': '직무역량(공통)', '정의': '다양하고 독창적인 아이디어를 발상, 제안하고 이를 적용 가능한 아이디어로 발전시킬 수 있다.'}}]
    print ( type(역량평가_api_datas))
    print ( type(역량평가_api_datas[0]))
    print ( type(역량평가_api_datas[0]['항목_data']))
    print ( type(역량평가_api_datas[0]['평가점수']))
    app = QApplication([])
    main_window = QMainWindow()
    wid_table = Wid_table_역량평가(main_window, 역량평가_api_datas)
    main_window.setCentralWidget(wid_table)
    main_window.show()
    app.exec()