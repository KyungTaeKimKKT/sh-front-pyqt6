from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Any
from modules.global_event_bus import event_bus
from modules.PyQt.Tabs.plugins.ui.Ui_table_config import Ui_Wid_Table_Config

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin

import config
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import time, json

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
if TYPE_CHECKING:
    from modules.PyQt.compoent_v2.table.Wid_table_Base import Wid_table_Base


class TableConfigDialog(QDialog):
    def __init__(self, parent=None, full_data: list[dict]=[], selected_ids: list[int] = []):
        super().__init__(parent)
        self.setWindowTitle("테이블 설정")
        self.resize(600, 400)

        self.full_data = {item["id"]: item for item in full_data if item.get("id") is not None and item.get('name') != 'seperator'}
        self.seperator_data = { 'id':item['id'] for item in full_data if item.get("id") is not None and item.get('name') == 'seperator'}
        self.selected_ids = set(selected_ids or [])
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        # 왼쪽: 전체 항목
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        main_layout.addWidget(self.available_list)

        # 중간 버튼
        button_layout = QVBoxLayout()
        self.btn_add = QPushButton("→")
        self.btn_remove = QPushButton("←")
        self.btn_separator = QPushButton("＋ 구분선")
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_remove)
        button_layout.addWidget(self.btn_separator)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 오른쪽: 선택된 항목
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        main_layout.addWidget(self.selected_list)

        # 하단: 저장/취소
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)

        self.populate_lists()

        # 연결
        self.btn_add.clicked.connect(self.move_to_selected)
        self.btn_remove.clicked.connect(self.move_to_available)
        self.btn_separator.clicked.connect(self.insert_separator)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def populate_lists(self):
        self.available_list.clear()
        self.selected_list.clear()

        for id_, item in self.full_data.items():
            if id_ in self.selected_ids:
                self.selected_list.addItem(self.create_item(item))
            else:
                self.available_list.addItem(self.create_item(item))

    def create_item(self, item: dict):
        text = f"{item['title']} ({item['name']})"
        list_item = QListWidgetItem(text)
        list_item.setData(Qt.ItemDataRole.UserRole, item["id"])
        list_item.setData(Qt.ItemDataRole.UserRole + 1, "menu")
        return list_item

    def insert_separator(self):
        sep_item = QListWidgetItem("─── 구분선 ───")
        sep_item.setFlags(sep_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        sep_item.setData(Qt.ItemDataRole.UserRole, None)
        sep_item.setData(Qt.ItemDataRole.UserRole + 1, "separator")
        self.selected_list.addItem(sep_item)

    def move_to_selected(self):
        for item in self.available_list.selectedItems():
            self.available_list.takeItem(self.available_list.row(item))
            self.selected_list.addItem(item)

    def move_to_available(self):
        for item in self.selected_list.selectedItems():
            # separator는 삭제 불가
            if item.data(Qt.ItemDataRole.UserRole + 1) == "separator":
                continue
            self.selected_list.takeItem(self.selected_list.row(item))
            self.available_list.addItem(item)

    def get_selected_items(self):
        result = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            item_type = item.data(Qt.ItemDataRole.UserRole + 1)
            if item_type == "separator":
                result.append( self.seperator_data)
            else:
                result.append({"id": item.data(Qt.ItemDataRole.UserRole)})
        return result


class Wid_Config_Mode( QWidget):
    """ parent가 명확하므로 lazy_attr_names 사용하지 않음 
        table_name 은 부모에서 set_APP_ID 함수에서 설정됨.
    """
    on_save_clicked = pyqtSignal()
    # lazy_attr_names = ['table_name']
    def __init__(self, parent:Optional[Wid_table_Base]=None):
        super().__init__(parent)

        self.is_connected = False

        self.event_bus = event_bus
        self.ui = Ui_Wid_Table_Config()
        self.ui.setupUi(self)
        self.hide()        

        self.map_menu_urls = {
            'row': f"config/v_header_menus/?page_size=0",
            'col': f"config/h_header_menus/?page_size=0",
            'cell': f"config/cell_menus/?page_size=0",
        }
        self.map_menu_urls_bulk = {
            'row': f"config/table_v_header_link/bulk/",
            'col': f"config/table_h_header_link/bulk/",
            'cell': f"config/table_cell_menu_link/bulk/",
        }
        # self.connect_signals()
        # self.run_lazy_attr()

    def set_APP_ID(self, APP_ID:str):
        self.table_name = Utils.get_table_name(APP_ID)
        if self.is_connected:
            self.disconnect_signals()
        self.connect_signals()
    
    def connect_signals(self):
        try :
            logger.info(f"connect_signals : {self.table_name}")
            self.ui.PB_Row.clicked.connect( self.slot_PB_Row_Menu )
            self.ui.PB_Col.clicked.connect( self.slot_PB_Col_Menu )
            self.ui.PB_Cell.clicked.connect( self.slot_PB_Cell_Menu )
            self.ui.PB_save.clicked.connect( self.slot_PB_save )
            self.is_connected = True
        except Exception as e:
            logger.error(f"connect_signals 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def disconnect_signals(self):
        try :
            self.ui.PB_Row.clicked.disconnect()
            self.ui.PB_Col.clicked.disconnect()
            self.ui.PB_Cell.clicked.disconnect()
            self.ui.PB_save.clicked.disconnect()
            self.is_connected = False
        except Exception as e:
            logger.error(f"disconnect_signals 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def fetch_menu_items(self, url):
        logger.debug(f"fetch_menu__items : url: {url}")
        s = time.perf_counter()
        _isok, _items = APP.API.fetch_fastapi(url)
        e = time.perf_counter()
        logger.debug(f"fetch_menu__items : 소요시간: {(e-s)*1000:.2f}msec")
        if _isok:
            logger.info(f"fetch_h_menu__items 완료 : {_items}")
            return _items
        else:
            logger.error(f"fetch_h_menu__items 실패 : {_items}")
            return []

    def get_menus_from_info(self):
        """ 현재 테이블의 메뉴 정보를 가져온다. """
        
        for item in INFO.ALL_TABLE_TOTAL_CONFIG:
            if item['table_name'] == self.table_name:
                self.menus = item.get('menus', {} )
                if self.menus:
                    self.v_menus = self.menus.get( 'v_header', [] )
                    self.h_menus = self.menus.get( 'h_header', [] )
                    self.cell_menus = self.menus.get( 'cell_header', [] )
                else:
                    self.v_menus = []
                    self.h_menus = []
                    self.cell_menus = []
                break
        

    def run(self):
        """ 작동하지 않음.==> set_APP_ID 에서 CONNECT_SIGNAL => SLOT 동작시, API 호출 동작함.
            정리되면, INFO.ALL_TABLE_TOTAL_CONFIG 에서 메뉴 정보를 가져오는 함수를 만들어야 함.
        """
        if self.parent() and hasattr(self.parent(), 'table_name')   :
            self.table_name = self.parent().table_name
            logger.info(f"Wid_Config_Mode 초기화 완료 : TableName: {self.table_name}")
            self.get_menus_from_info()
            logger.debug (f" {self.table_name} 의 메뉴 정보 : {self.menus}")
        else:
            logger.error("Wid_Config_Mode 초기화 실패 : parent 가 없거나 table_name 이 없읍니다.")
        self.connect_signals()

    def api_send_menu_items(self, url:str,sendData:dict):
        """ 각 모델에 bulk 업데이트 요청 """
        _isok, _data = APP.API.post( url, data= sendData )
        if _isok:
            Utils.generate_QMsg_Information(self, title="메뉴 설정 완료", text="메뉴 설정 완료", autoClose= 1000)
        else:
            Utils.generate_QMsg_critical(self, title="메뉴 설정 실패", text="메뉴 설정 실패")
    
    def get_menu_ids(self, _type:str):
        """ 현재 테이블의 메뉴 정보를 가져온다. """
        _menu_list = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_Menus', [])
        if not _menu_list:
            return []
        
        logger.warning(f"get_menu_ids : _menu_list: {_menu_list}")
        
        _menu_list_row = _menu_list.get('v_header', [])
        _menu_list_col = _menu_list.get('h_header', [])
        _menu_list_cell = _menu_list.get('cell_header', [])
        match _type:
            case 'row':
                if not _menu_list_row :
                    return []
                ids = []
                for _obj in _menu_list_row:
                    ids.append( _obj.get('v_header').get('id') )
                return ids
            case 'col':
                if not _menu_list_col :
                    return []
                ids = []
                for _obj in _menu_list_col:
                    ids.append( _obj.get('h_header').get('id') )
                return ids
            case 'cell':
                if not _menu_list_cell :
                    return []
                ids = []
                for _obj in _menu_list_cell:
                    ids.append( _obj.get('cell_header').get('id') )
                return ids
            case _:
                return []

    def slot_PB_Row_Menu(self):
        logger.info("slot_PB_Row_Menu")
        items = self.fetch_menu_items(self.map_menu_urls['row'])

        dialog = TableConfigDialog (self, full_data=items, selected_ids = self.get_menu_ids('row') )
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_items()
            
            sendData = {
                "table_name": self.table_name,
                "ids": json.dumps(selected_ids, ensure_ascii=False),
            }
            self.api_send_menu_items(self.map_menu_urls_bulk['row'], sendData)

            logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")




    def slot_PB_Col_Menu(self):
        logger.info("slot_PB_Col_Menu")
        items = self.fetch_menu_items(self.map_menu_urls['col'])
        dialog = TableConfigDialog  (self, full_data=items, selected_ids = self.get_menu_ids('col') )
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_items()
            sendData = {
                "table_name": self.table_name,
                "ids": json.dumps(selected_ids, ensure_ascii=False),
            }
            self.api_send_menu_items(self.map_menu_urls_bulk['col'], sendData)
            logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

    def slot_PB_Cell_Menu(self):
        logger.info("slot_PB_Cell_Menu")
        items = self.fetch_menu_items(self.map_menu_urls['cell'])
        dialog = TableConfigDialog(self, full_data=items, selected_ids = self.get_menu_ids('cell') )
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_items()
            logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

    def slot_PB_save(self):
        self.on_save_clicked.emit()
        return 
        if hasattr ( self.parent(), 'is_no_config_initial' ) and self.parent().is_no_config_initial:
            api_datas = self.parent().view.get_table_config_api_datas_to_send_if_no_config_initial()
            print (f" if no config initial : api_datas: {api_datas}")
            self.send_api_datas(api_datas)

        elif hasattr(self.parent(), 'view') and hasattr(self.parent().view, 'get_changed_api_datas'):
            api_datas = self.parent().view.get_changed_api_datas()
            self.send_api_datas(api_datas)

        else:
            Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="프로그램 오류 발생")

    def send_api_datas(self, api_datas:list[dict]):
        if api_datas:
            sendData = {
                "table_name": self.table_name,
                "datas": json.dumps(api_datas, ensure_ascii=False),
            }
            isok, _data = APP.API.post(f"config/table_config/bulk/", data= sendData)
            if isok:
                Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 완료", text="테이블 설정 완료", autoClose= 1000)
                # self.event_bus.publish(f"{self.table_name}:table_config_mode", True)
            else:
                Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="DB 저장 실패")
        else:
            Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 ", text="테이블 설정 변경이 없읍니다.")
