from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import inspect
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.compoent_v2.table.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table.Base_Delegate import Base_Delegate

from modules.PyQt.Tabs.plugins.ui.Wid_config_mode import Wid_Config_Mode
from modules.PyQt.Tabs.plugins.ui.Wid_header import Wid_Header

from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode
from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton

import json, os,copy,time
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()


class RenameColumnDialog(QDialog):
    def __init__(self, current_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("컬럼 이름 변경")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # 설명 문구
        info_label = QLabel("새 이름을 입력하세요: <span style='color:red;'>(이름은 중복 불가입니다.)</span>")
        info_label.setTextFormat(Qt.TextFormat.RichText)  # HTML 해석 허용
        layout.addWidget(info_label)

        # 입력창
        self.line_edit = QLineEdit(self)
        self.line_edit.setText(current_text)
        layout.addWidget(self.line_edit)

        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_text(self):
        return self.line_edit.text().strip()
    

class TableView_TableConfigMode(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_config = None
        self.table_config_api_datas = None   ### 편집으로 사용
        self.table_config_api_datas_original = None  ### 원본 데이터 보존
        self.map_display_name_to_obj:Optional[dict[str,dict]] = None

        self.init_basic_config()
        self.setupConfigHeader()

    def init_basic_config(self):
        self.setEditTriggers( QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setVisible(True)
        self.verticalHeader().setVisible(True)

        # 수직 헤더에 번호 표시 설정
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        # 수직 헤더 너비 설정
        self.verticalHeader().setDefaultSectionSize(30)  # 행 높이
        self.verticalHeader().setMinimumWidth(30)  # 최소 너비
        # self.verticalHeader().setFixedWidth(60)  # 고정 너비
        self.verticalHeader().setMaximumWidth(80)  # 고정 너비


        self.installEventFilter(self)

        self.setMouseTracking(True)

    def set_table_config(self, table_config:dict):
        self.table_config = table_config
        self._headers = table_config['_headers']
        self._hidden_columns = table_config['_hidden_columns']
        logger.debug(f"set_table_config : {self.table_config}")

        logger.debug(f"set_table_config : {self.table_config['_hidden_columns']}")

    def set_table_config_api_datas(self, table_config_api_datas:list[dict]):
        self.table_config_api_datas = table_config_api_datas
        self.map_display_name_to_obj = { obj['display_name']: obj for obj in table_config_api_datas }
        self.table_config_api_datas_original = copy.deepcopy(table_config_api_datas)



    def setup_menus(self):
        return 

    def run(self):
        logger.debug(f"self.check_api_datas_available(): {self.check_api_datas_available()}")
        if self.check_api_datas_available():
            self.init_by_api_datas_model()
        else:
            self.copy_original_header()
        self.setupConfigHeader()
        self.render_all_visible()
    
    def copy_original_header(self):
        self.original_state = {
                'hidden_columns': copy.deepcopy(self._hidden_columns),
                'column_widths':  [self.horizontalHeader().sectionSize(i) for i in range(self.model().columnCount())],
                'column_order': [self.horizontalHeader().visualIndex(i) for i in range(self.model().columnCount())],
                'headers':  copy.deepcopy(self._headers),
                'table_config_api_datas': copy.deepcopy(self._table_config_api_datas),
                'api_datas_변경':   copy.deepcopy(self._table_config_api_datas),
            }
        self.table_config_api_datas = copy.deepcopy(self._table_config_api_datas)
        logger.debug(f"self.original_state: {self.original_state}")

    def apply_table_config(self ):
        try:
            self.apply_hidden_columns()
            self.apply_column_widths()

            ##  강제로 레이아웃 변경 발생
            self.model().layoutChanged.emit()

        except Exception as e:
            logger.error(f"apply_table_config 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def apply_hidden_columns(self):
        """숨길 컬럼은 모두 보이게 적용 - delegate에서 색상 처리"""
        col_count = self.model().columnCount()		
        # 1. 모든 컬럼 보이게 초기화
        for col in range(col_count):
            self.setColumnHidden(col, False)		


    # def _is_hidden_columns(self, colNo:int) -> bool:
    #     return colNo in self.table_config['_hidden_columns']

    def apply_column_widths(self):
        """컬럼 너비 적용"""
        ### config 모드일 때는 적용하지 않음
        try:
            if '_column_widths' in self.table_config and self.table_config['_column_widths']:
                for col_name, width in self.table_config['_column_widths'].items():
                    if col_name not in self.table_config['_headers']:
                        continue
                    col_idx = self.table_config['_headers'].index(col_name)
                    # logger.debug(f"apply_column_widths : col_idx : {col_idx}")
                    if 0 <= col_idx < self.model().columnCount():
                    # 모든 컬럼은 사용자가 조정 가능하도록 Interactive 모드로 설정
                        self.horizontalHeader().setSectionResizeMode(
                            col_idx, QHeaderView.ResizeMode.Interactive)
                        
                        if width == 0:
                            # 초기 너비를 내용에 맞게 자동 조정
                            self.resizeColumnToContents(col_idx)
                        else:
                            # 지정된 초기 너비 설정
                            self.setColumnWidth(col_idx, width)
        except Exception as e:
            logger.error(f"apply_column_widths 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def render_all_visible(self):
        try:
            # 1. 모든 숨겨진 컬럼 표시
            for i in range(self.model().columnCount()):
                self.setColumnHidden(i, False)  # self.setColumnHidden -> self.handler.setColumnHidden
            # self.render_header()  # 인자 제거 (self.model)           
            self.model().dataChanged.emit(
                self.model().index(0, 0), 
                self.model().index(self.model().rowCount() - 1, self.model().columnCount() - 1), 
                [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole]
                )

        except Exception as e:
            logger.error(f"render_all_visible 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def render_header(self):
        """헤더 렌더링"""
        try:
            # 2. 체크박스 + name 동시 표시
            txt_hidden , txt_visible =  '[V] ', '[ ] '
            display_name_with_checkbox = {
                col_idx: txt_hidden 
                + (self._headers[col_idx]).replace('[V] ', '').replace('[ ] ', '') if col_idx in self._hidden_columns else txt_visible 
                + (self._headers[col_idx]).replace('[V] ', '').replacesetupConfigHeader('[ ] ', '')
                for col_idx in range(self.model().columnCount())
            }

            for col_idx, display_name in display_name_with_checkbox.items():
                self.model().setHeaderData(col_idx, Qt.Orientation.Horizontal, display_name, Qt.ItemDataRole.DisplayRole)
            self.horizontalHeader().update()
        except Exception as e:
            logger.error(f"render_header 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def init_by_api_datas_model(self):
        """ api_datas 로 초기 설정 """
        model = self.model()
        column_count = model.columnCount()

        self._headers = [model.headerData(col, Qt.Horizontal) for col in range(column_count)]

        logger.info(f"init_by_api_datas_model : row_count : {model.rowCount()}, column_count: {column_count}")
        logger.info(f"init_by_api_datas_model : _data : {model._data}")
        logger.info(f"init_by_api_datas_model : api_datas : {model.api_datas}")
        logger.debug(f"init_by_api_datas_model : self.model() : {self.model()}")
        logger.debug(f"init_by_api_datas_model : self._headers : {self._headers}")
        logger.debug(f"init_by_api_datas_model : self.model().table_config : {self.model().table_config}")
        logger.debug(f"init_by_api_datas_model : self.model()._headers : {self.model()._headers}")
        self.table_config_api_datas = []
        self.original_state = {}
        for header in self._headers:
            _dict = {}
            _dict['id'] = -1
            _dict['table_name'] = self.table_name
            _dict['column_name'] = header
            _dict['display_name'] = header
            _dict['order'] = self._headers.index(header)
            _dict['column_width'] = 0
            _dict['is_hidden'] = False
            self.table_config_api_datas.append(_dict)
        logger.debug( f" init_by_api_datas_model : {self.table_config_api_datas}")
    
    def setupConfigHeader(self):
        """설정 모드용 커스텀 헤더 설정"""
        try:
            header = self.horizontalHeader()        
            # 헤더 설정
            header.setSectionsMovable(True)  # 드래그 앤 드롭으로 order 변경 가능
            header.setSectionsClickable(True)
            header.sectionDoubleClicked.connect(self.onHeaderSectionDoubleClicked)
            if self.horizontalHeader().contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            header.customContextMenuRequested.connect(self.showHeaderContextMenu)
            header.sectionMoved.connect(self.onHeaderSectionMoved)
            header.sectionResized.connect(self.onColumnResized)
        except Exception as e:
            logger.error(f"setupConfigHeader 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onColumnResized(self, column_index, old_width, new_width):
        """컬럼 너비가 변경되었을 때 호출되는 메서드"""
        try:
            obj = self.get_obj_by_column_index(column_index)
            obj['column_width'] = new_width

            # 툴팁으로 너비 표시
            header = self.horizontalHeader()
            pos = header.sectionPosition(column_index)
            global_pos = header.mapToGlobal(QPoint(pos + new_width // 2, 0))
            QToolTip.showText(global_pos, f"{obj['display_name']}: {new_width}px", header)
            
        except Exception as e:
            logger.error(f"onColumnResized 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onHeaderSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        """헤더 섹션이 이동되었을 때 호출되는 메서드"""
        try:
            # 모든 컬럼에 대해 order 업데이트
            for i in range(self.model().columnCount()):
                obj = self.get_obj_by_column_index(i)
                obj['order'] = self.horizontalHeader().visualIndex(i)
            self.model().layoutChanged.emit()
        except Exception as e:
            logger.error(f"onHeaderSectionMoved 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onColumnSizeInit(self, logicalIndex:int):
        """컬럼 너비 자동조정"""
        try:
            obj = self.get_obj_by_column_index(logicalIndex)
            obj['column_width'] = 0
            self.resizeColumnToContents(logicalIndex)
        except Exception as e:
            logger.error(f"onColumnSizeInit 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onHeaderSectionDoubleClicked(self, logicalIndex:int):
        """헤더 섹션 더블 클릭 시 이름 변경 다이얼로그 표시"""
        try:
            obj = self.get_obj_by_column_index(logicalIndex)
            current_text = obj['display_name']
            # 입력 다이얼로그 표시
            # new_text, ok = QInputDialog.getText(
            #     self, 
            #     "컬럼 이름 변경", 
            #     "새 이름을 입력하세요:", 
            #     QLineEdit.EchoMode.Normal, 
            #     str(current_text)
            # )
            dialog = RenameColumnDialog( obj['display_name'], self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_text = dialog.get_text()
                if new_text and self.validate_header_name(new_text):
                    obj['display_name'] = new_text
                    self.map_display_name_to_obj[new_text] = obj
                    del self.map_display_name_to_obj[current_text]

                    self.model().setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.DisplayRole)
                else:
                    Utils.generate_QMsg_critical(self, title="컬럼 이름 변경", text=f"{new_text} 은 사용할 수 없는 이름(중복금지)입니다.")
                    logger.error(f"onHeaderSectionDoubleClicked : {new_text} is not valid")
                # self.render_header()
        except Exception as e:
            logger.error(f"onHeaderSectionDoubleClicked 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onToggleColumnVisibility(self, logical_index:int):
        """컬럼 숨김 상태 토글"""
        try:
            obj = self.get_obj_by_column_index(logical_index)
            ### toggle
            logger.debug(f"onToggleColumnVisibility 변경 전 : {obj['is_hidden']}")
            obj['is_hidden'] = not obj['is_hidden']
            logger.debug(f"onToggleColumnVisibility 변경 후 : {obj['is_hidden']}")

            # logger.debug(f"toggleColumnVisibility : {self._hidden_columns}")
            # self.model().dataChanged.emit(self.model().index(0, logical_index), 
            #                               self.model().index(self.model().rowCount() - 1, logical_index), 
            #                               [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole])
            self.model().layoutChanged.emit()
        except Exception as e:
            logger.error(f"toggleColumnVisibility 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
    
    def validate_header_name(self, new_text:str) -> bool:
        """ 컬럼 이름 유효성 검사 , 유효하면(중복이 없으면 ) True 반환"""
        return new_text not in list(self.map_display_name_to_obj.keys())
    
    def is_hidden_column(self, column_index:int) -> bool:
        """컬럼 숨김 여부 반환"""
        return self.get_obj_by_column_index(column_index)['is_hidden']

    def get_obj_by_column_index(self, column_index:int) -> dict:
        """컬럼 인덱스에 해당하는 obj 반환"""
        return self.map_display_name_to_obj[self.model().headerData(column_index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)]
        
    def showHeaderContextMenu(self, pos:QPoint):
        """헤더 컨텍스트 메뉴 표시"""
        try:
              
            logical_index = self.horizontalHeader().logicalIndexAt(pos)
            obj = self.get_obj_by_column_index(logical_index)
            
            if logical_index >= 0:
                menu = QMenu(self)
                
                # 이름 변경 액션
                rename_action = menu.addAction("이름 변경")
                rename_action.triggered.connect(lambda: self.onHeaderSectionDoubleClicked(logical_index))
                
                # 숨김 토글 액션
                hide_text = "표시하기" if obj['is_hidden'] else "숨기기"
                hide_action = menu.addAction(hide_text)
                hide_action.triggered.connect(lambda: self.onToggleColumnVisibility(logical_index))

                ### 너비 초기화(0으로 변경 ==> 자동 조정)
                if obj['column_width'] == 0:
                    width_action = menu.addAction("너비 자동조정 상태임")
                    width_action.setEnabled(False)
                else:
                    width_action = menu.addAction("너비 자동조정")
                    width_action.triggered.connect(lambda: self.onColumnSizeInit(logical_index))
                
            menu.exec(self.horizontalHeader()  .mapToGlobal(pos))
        except Exception as e:
            logger.error(f"showHeaderContextMenu 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def get_table_config_api_datas_to_send_if_no_config_initial(self) -> list[dict]:
        """ is_no_config_initial 일 때 전송할 데이터 반환 """
        return list(self.map_display_name_to_obj.values())
        
    def get_changed_api_datas(self):
        """원본 API 데이터와 비교하여 변경된 데이터만 반환"""
        try:

            sorted_원본 = sorted(self.table_config_api_datas_original, key=lambda x: x['id'])
            sorted_현재 = sorted( list(self.map_display_name_to_obj.values()), key=lambda x: x['id'])

            for _obj현재, _obj원본 in zip(sorted_현재, sorted_원본):
                logger.debug(f"get_changed_api_datas : {_obj현재['is_hidden']} , {_obj원본['is_hidden']}, {_obj현재['is_hidden'] != _obj원본['is_hidden']}")

            changed_api_datas = [ _obj현재 for _obj현재, _obj원본 in zip(sorted_현재, sorted_원본) 
                                 if _obj현재 != _obj원본 ]
            logger.info(f"변경된 API 데이터: {changed_api_datas}")
            # if self.check_api_datas_available():
            #     return self.table_config_api_datas
            # else:
            #     if not hasattr(self, 'original_state'):
            #         return []
                
            # current_api_datas = self.table_config_api_datas
            # if hasattr(self, 'original_state') and self.original_state:
            #     original_api_datas = self.original_state.get('table_config_api_datas', [])
            # else:
            #     original_api_datas = []
                
            # changed_api_datas = [ _obj1 for _obj1, _obj2 in zip(current_api_datas, original_api_datas) 
            #                      if _obj1 != _obj2 ]
            # logger.info(f"변경된 API 데이터: {changed_api_datas}")

            return changed_api_datas
            
        except Exception as e:
            logger.error(f"get_changed_api_datas 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return []


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    items = []
    if not isinstance(d, dict):
        return {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # 리스트는 JSON 문자열로 처리해 표시만 (복구는 필요 시 직접 처리)
            items.append((new_key, json.dumps(v, ensure_ascii=False)))
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d: dict, sep: str = '.') -> dict:
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        try:
            # JSON 문자열이면 복원 시도
            if isinstance(v, str) and v.startswith('['):
                v = json.loads(v)
        except Exception:
            pass
        target[parts[-1]] = v
    return result
		


class TableModel_TableConfigMode(QAbstractTableModel):
    KEY_Attr_to_Display = '_mapping_attr_to_display'
    KEY_Display_to_Attr = '_mapping_display_to_attr'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_config = None
        self.api_datas = None

        self._headers :list[str] = []
        self._data :list[any] = []
        self.display_to_attr_cache: dict[str, str] = {}  # <-- 추가

    def set_table_config(self, table_config:dict):
        self.table_config = table_config
        if self.table_config and '_headers' in self.table_config:
            self._headers = self.table_config['_headers']
        if self.KEY_Display_to_Attr in self.table_config:
            self.display_to_attr_cache = self.table_config[self.KEY_Display_to_Attr].copy()

        self.layoutChanged.emit()

    def set_api_datas(self, api_datas:list[dict]):
        self.api_datas = api_datas
        self._data = [ flatten_dict(row) for row in api_datas]

        ### 우선순위를 self.table_config 에서 가져오기
        if not(self.table_config and '_headers' in self.table_config):
            all_keys = set()
            for row in self._data:
                all_keys.update(row.keys())
    
            self._headers = list(all_keys)
        # self._headers = sorted(all_keys)  # 컬럼 순서 일관성 있게
        self.layoutChanged.emit()

    def get_restored_data(self) -> list[dict]:
        return [ unflatten_dict(row) for row in self._data ]

    def get_data(self):
        return self._data
    
    def get_headers(self):
        return self._headers

    # QAbstractTableModel 필수 메서드 구현
    def rowCount(self, parent:QModelIndex=None):
        return len( self.get_data() )
        
    def columnCount(self, parent:QModelIndex=None):
        return len( self.get_headers() )

    def headerData(self, section:int, orientation:Qt.Orientation, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Vertical:
                return str(section+1)
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.get_headers()):
                    return self.get_headers()[section]
                
        if role == Qt.ItemDataRole.ToolTipRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._headers):
                    try:
                        display_name = self._headers[section]
                        db_attr_name = self.get_attrName_from_display(display_name)
                        return db_attr_name
                    except Exception as e:
                        logger.error(f"headerData 오류: {e}")
                        logger.error(f"{traceback.format_exc()}")
                        return f"오류 : {display_name}"
        
        return None
    
    def get_attrName_from_display(self, display_name:str) -> str:
        return self.table_config['_mapping_display_to_attr'][display_name]
    
    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> bool:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                old_display_name = self._headers[section]
                attr_name = self.display_to_attr_cache.get(old_display_name, old_display_name)

                self._headers[section] = value
                self.display_to_attr_cache[value] = attr_name  # 새로운 display_name으로 매핑 유지
                if old_display_name in self.display_to_attr_cache:
                    del self.display_to_attr_cache[old_display_name]

                self.headerDataChanged.emit(Qt.Orientation.Horizontal, section, section)
                return True
        return False
    
    def data(self, index:QModelIndex, role:Qt.ItemDataRole=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            display_name = self.get_headers()[index.column()]
            attribute_name = self.display_to_attr_cache.get(display_name, display_name)
            return self.get_data()[index.row()].get(attribute_name, "")
        return None

    

    

class ConfigTableDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, hidden_columns=None):
        super().__init__(parent)
        self.hidden_columns = hidden_columns or []

    def paint(self, painter, option, index):
        model = index.model()
        tableview = model.parent() if isinstance(model.parent(), QTableView) else self.parent()
        is_hidden_col = False
        if hasattr(tableview, 'is_hidden_column') and callable(tableview.is_hidden_column):
            is_hidden_col = tableview.is_hidden_column(index.column())
        else:
            logger.error(f"tableview._is_hidden_columns 가 없습니다.")


        if is_hidden_col:
            # 🔽 배경 먼저 직접 칠함
            painter.save()
            painter.fillRect(option.rect, QColor('#535353'))  # 진한 회색
            painter.restore()

        super().paint(painter, option, index)

        
        # 초기화는 부모 클래스에서 처리
 

        
from modules.PyQt.compoent_v2.table.mixin_create_config import Mixin_Create_Config
class Wid_TableConfigMode(LazyParentAttrMixin, QWidget, Mixin_Create_Config):

    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent, **kwargs)
        self.start_init_time = time.perf_counter()
        self.lazy_attr_names = ['APP_ID', 'is_no_config_initial']
        self.lazy_ready_flags = {}
        self.lazy_attr_values = {}
        self.lazy_ws_names = []

        self.event_bus = event_bus
        self.edit_mode = 'None' ### 'row' or 'cell'

        self.view:Optional[TableView_TableConfigMode] =  TableView_TableConfigMode(self)
        self.model:Optional[TableModel_TableConfigMode] = TableModel_TableConfigMode(self.view)

        self.delegate:Optional[ConfigTableDelegate] = ConfigTableDelegate(self)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)
        # self.model().set_table_view(self.view)

        self.is_api_datas_applied = True
        self.no_edit_columns_by_coding = [ 'ALL']

        self.init_attributes()
        self.init_ui()

        self.run_lazy_attr()

    def showEvent(self, event:QShowEvent):
        super().showEvent(event)
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(True)
        if hasattr(self, 'wid_config') and self.wid_config and hasattr(self.wid_config, 'setVisible'):
            self.wid_config.setVisible(True)

    def hideEvent(self, event:QHideEvent):
        super().hideEvent(event)
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(False)
        if hasattr(self, 'wid_config') and self.wid_config and hasattr(self.wid_config, 'setVisible'):
            self.wid_config.setVisible(False)


    def init_attributes(self):
        # super().init_attributes()
        if hasattr(self, 'kwargs'):
            for key, value in self.kwargs.items():
                setattr(self, key, value)


    def init_ui(self):
        self.layout = QVBoxLayout()

        self.wid_config = Wid_Config_Mode(self)

        self.wid_config.ui.label.setStyleSheet("""
            QLabel {
                color: #FFD700;  /* 강조 색 (예: 금색) */
                font-size: 16px;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #FFD700;
                border-radius: 6px;
                background-color: #2b2b2b;  /* 진회색 배경, 텍스트 대비 좋음 */
            }
        """)
        self.layout.addWidget(self.wid_config)

        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)

    def on_all_lazy_attrs_ready(self):
        logger.info(f"{self.__class__.__name__} : All lazy attributes are ready! : {self.lazy_attr_values}")
        APP_ID = self.lazy_attr_values['APP_ID']
        try:
            self.table_name = Utils.get_table_name(APP_ID)
            self.is_no_config_initial = self.lazy_attr_values['is_no_config_initial']
            self.on_table_config(True)

            self.subscribe_gbus()
            #### wid_config run()과 같음
            self.wid_config.set_APP_ID(APP_ID)

        except Exception as e:
            logger.error(f"{self.parent().__class__.__name__} : on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")



    def subscribe_gbus(self):
        from modules.envs.global_bus_event_name import global_bus_event_name as GBus 
        self.event_bus.subscribe( f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config )
        self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.on_api_datas_changed )

    def connect_signals(self):
        """ signal 연결 """
        return 
    
    def on_table_config(self, is_refresh:bool):
        if not (is_refresh and hasattr(self, 'table_name') and self.table_name  in INFO.ALL_TABLE_TOTAL_CONFIG): 
            return
        
        #### is_no_config_inital 경우, 종료하고, api_datas 받은 것으로 table_config 설정        
        if self.is_no_config_initial:
            return 


        self.table_config = INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig']
        self.table_config_api_datas = INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas']
        self.apply_table_config()

    def apply_table_config(self):
        self.view.set_table_config(self.table_config)
        self.view.set_table_config_api_datas( copy.deepcopy(self.table_config_api_datas) )
        self.model.set_table_config(self.table_config)

    def on_api_datas_changed(self, api_datas:list[dict]):
        logger.debug(f"{self.__class__.__name__} : on_api_datas_changed : {api_datas}")

        ### 초기화 없이 초기화 할 경우 종료하고, api_datas 받은 것으로 table_config 설정
        if self.is_no_config_initial:
            self.table_config, self.table_config_api_datas = self.mixin_create_config(api_datas) 
            self.apply_table_config()

        self.model.set_api_datas(api_datas)




    def run(self):
        return 
 

    def clear_layout(self):
        """레이아웃 초기화"""
        try:
            if self.layout:
                Utils.deleteLayout(self.layout)
        except Exception as e:
            logger.error(f"레이아웃 초기화 중 오류 발생: {e}")

    

