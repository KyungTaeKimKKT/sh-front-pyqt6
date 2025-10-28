from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from modules.PyQt.compoent_v2.custom_상속.custom_PB import HR평가_차수별_역량평가_PB
import json
from info import Info_SW as INFO
from modules.envs.api_urls import API_URLS
from config import Config as APP
import modules.user.utils as Utils

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class ListWidget_before_and_after(QWidget):
    selection_changed = pyqtSignal(int, list)  # 평가차수, 선택된 ID 목록


    def __init__(self, parent=None, 평가차수:int=0, all_db:list[dict]=[], selected_db:list[dict]=[]):
        super().__init__(parent)
        self.평가차수 = 평가차수
        self.all_db = all_db
        self.selected_db = selected_db  
        self.not_selected_db = [ obj for obj in self.all_db if obj not in self.selected_db ]

        self.UI()
        if self.all_db or self.selected_db:
            self.set_items()

        
    def UI(self):
        self.listWidget_before = QListWidget()
        self.listWidget_after = QListWidget()

        self.PB_Select = QPushButton("▶ Select ▶")
        self.PB_Unselect = QPushButton("◀ Unselect ◀")
        # self.PB_Save = QPushButton("Save")

        # 이벤트 연결
        self.PB_Select.clicked.connect(self.select_items)
        self.PB_Unselect.clicked.connect(self.unselect_items)
        # self.PB_Save.clicked.connect(self.save_selection)

        # 버튼 수직 레이아웃
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.PB_Select)
        button_layout.addWidget(self.PB_Unselect)
        button_layout.addStretch()
        # button_layout.addWidget(self.PB_Save)

        # 전체 수평 레이아웃
        layout = QHBoxLayout()
        layout.addWidget(self.listWidget_before)
        layout.addLayout(button_layout)
        layout.addWidget(self.listWidget_after)

        self.setLayout(layout)

    def set_items(self):
        self.listWidget_before.clear()
        self.listWidget_after.clear()
        #### before select

        for item in self.not_selected_db:
            label = f"{item['구분']} - {item['항목_이름']}"
            lw_item = QListWidgetItem(label)
            lw_item.setData(Qt.ItemDataRole.UserRole, item )  # 💡 dict 저장
            self.listWidget_before.addItem(lw_item)

        #### after select
        for item in self.selected_db:
            label = f"{item['구분']} - {item['항목_이름']}"
            lw_item = QListWidgetItem(label)
            lw_item.setData(Qt.ItemDataRole.UserRole, item )  # 💡 dict 저장
            self.listWidget_after.addItem(lw_item)

    def select_items(self):
        for item in self.listWidget_before.selectedItems():
            self.listWidget_before.takeItem(self.listWidget_before.row(item))
            self.listWidget_after.addItem(item)
        self.emit_selection()

    def unselect_items(self):
        for item in self.listWidget_after.selectedItems():
            self.listWidget_after.takeItem(self.listWidget_after.row(item))
            self.listWidget_before.addItem(item)
        self.emit_selection()

    def emit_selection(self):
        ids = [self.listWidget_after.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.listWidget_after.count())]
        self.selection_changed.emit(self.평가차수, ids)

    def save_selection(self):
        result = self.get_selected_items()
        print(f"선택된 항목: {result}")


    def get_selected_items(self):
        """선택된 항목을 {차수: [id, id, ...]} 형태로 반환"""
        _dicts = [self.listWidget_after.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.listWidget_after.count())]
        return {self.평가차수: _dicts}

class Dialog_역량평가관리(QDialog):
    def __init__(self, parent, 평가설정:dict = {},  url:str= INFO.URL_HR평가_역량평가_항목_DB):
        super().__init__(parent)
        self.all_db:list[dict] = []
        self.selected_db:list[dict] = []
        self.url = url
        self.selected_map : dict[int, list[dict]] = {}  # 차수: [id, id, ...]

        if 평가설정:
            self.총평가차수 = 평가설정['총평가차수']
            self.평가설정_fk = 평가설정['id']            
            self.api_fetch()




    def api_fetch(self):
        query_param = f"?평가설정_fk={self.평가설정_fk}&총평가차수={self.총평가차수}&page_size=0"
        query_url = f"{self.url}{query_param}".replace('//', '/')
        _isok, _json = APP.API.getlist( query_url )
        if _isok:
            self.all_db = _json 
            self.selected_map = self.get_selected_map()
            self.map_stacked_widget = {
                i : ListWidget_before_and_after(self, 
                                                평가차수=i, 
                                                all_db=[ obj for obj in self.all_db if obj['차수']==i ], 
                                                selected_db= self.selected_map[i]
                                                ) 
                    for i in range(0, self.총평가차수+1)
            }

            self.map_button = {
                i : HR평가_차수별_역량평가_PB(f"{i}차") for i in range(0, self.총평가차수+1)
            }
            self.UI()            

            for 차수, widget in self.map_stacked_widget.items():
                #### 초기화 표시
                self.handle_selection_change(차수, self.selected_map[차수])
                #### 이벤트 연결
                widget.selection_changed.connect(self.handle_selection_change)
            
            ### 초기화 click : 0차 선택
            QTimer.singleShot(100, lambda: self.on_pb_clicked(0))
        else:
            Utils.generate_QMsg_critical(self)

    def get_selected_map(self) -> dict[int, list[dict]]:
        if not self.all_db:
            logger.error(f"self.all_db 없음")
            return
        selected_map = {}
        for obj in self.all_db:
            차수 = obj.get('차수')
            if 차수 not in selected_map:
                selected_map[차수] = []

            obj_id = obj.get('id')
            if obj_id is None or obj_id == -1:
                continue

            selected_map[차수].append(obj)
        return selected_map


    def UI(self):
        v_layout = QVBoxLayout()

        ### 1. 요약 레이아웃
        summary_h_layout = QHBoxLayout()

        self.summary_label = QLabel("Summary")
        summary_h_layout.addWidget(self.summary_label)
        summary_h_layout.addStretch()

        self.PB_Save = QPushButton("Save")
        self.PB_Save.clicked.connect(self.save_selection)
        summary_h_layout.addWidget(self.PB_Save)
        v_layout.addLayout(summary_h_layout)

        ### 2. 버튼 레이아웃
        v_layout.addLayout(self.button_UI())

        ### 3. 스택 레이아웃
        self.stacked_container = QStackedWidget()
        for 차수, widget in self.map_stacked_widget.items():
            self.stacked_container.addWidget(widget)
            self.map_button[차수].clicked.connect( lambda _, idx=차수: self.on_pb_clicked (idx )) #stacked_container.setCurrentIndex(idx))
        
        v_layout.addWidget(self.stacked_container)
        self.setLayout(v_layout)

    def on_pb_clicked(self, idx:int):
        self.stacked_container.setCurrentIndex(idx)

        for 차수, widget in self.map_button.items():
            widget : HR평가_차수별_역량평가_PB
            if 차수 != idx:
                widget.set_released()
            else:
                widget.set_pressed()
        
    def button_UI(self):        
        h_layout = QHBoxLayout()
        for i in range(0, self.총평가차수+1):
            h_layout.addWidget(self.map_button[i])
        return h_layout
    
    def save_selection(self):
        bulk_send_data = []
        for 차수, widget in self.map_stacked_widget.items():
            result = widget.get_selected_items()
            bulk_send_data.extend(result[차수])
        
        #### 정의, 항목_이름, 구분 삭제 : sendData 형태로 변경
        for _dict in bulk_send_data:
            for key in ['정의', '항목_이름', '구분']:   
                del _dict[key]

        send_data = {
            '평가설정_fk': self.평가설정_fk,
            '_list': json.dumps(bulk_send_data, ensure_ascii=False)
        }
        url = f"{self.url}/bulk/".replace('//', '/')
        _isok, _json = APP.API.post_json(url, send_data, headers={'Content-Type': 'application/json'})
        if _isok:
            Utils.generate_QMsg_Information(self, title='저장 완료', text='정상적으로 저장되었읍니다.', autoClose=1000)
            self.accept()
        else:
            Utils.generate_QMsg_critical(self, title='저장 실패', text=f'확인 후 다시 저장바랍니다. <br> {json.dumps(_json, ensure_ascii=False)}')


    def handle_selection_change(self, 차수: int, id_list: list[int]):
        self.selected_map[차수] = id_list
        lines = []
        for 차수번호 in sorted(self.selected_map.keys()):
            lines.append(f"차수 {차수번호}: {len(self.selected_map[차수번호])} 항목")
        self.summary_label.setText("선택된 항목\n" + "\n".join(lines))






