from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import inspect
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
# from modules.PyQt.compoent_v2.table_v2.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
# from modules.PyQt.compoent_v2.table_v2.Base_Table_View import Base_Table_View
# from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model
# from modules.PyQt.compoent_v2.table_v2.Base_Delegate import Base_Delegate

# from modules.PyQt.Tabs.plugins.ui.Wid_config_mode import Wid_Config_Mode
# from modules.PyQt.Tabs.plugins.ui.Wid_header import Wid_Header

# from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode
# from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton

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

    def __init__(self, parent=None, table_config:dict=None, **kwargs ):
        super().__init__(parent)
        self.table_config = table_config
        self.table_config_api_datas = table_config['_table_config_api_datas']
        self.table_config_api_datas_original = copy.deepcopy( self.table_config_api_datas)
        self.map_display_name_to_obj:Optional[dict[str,dict]] = None

        self.init_basic_config()
        self.setupConfigHeader()

        self.set_table_config(self.table_config)
        self.set_table_config_api_datas(self.table_config_api_datas)

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
        if INFO.IS_DEV:
            logger.debug(f"set_table_config : {self.table_config}")


    def set_table_config_api_datas(self, table_config_api_datas:list[dict]):
        self.table_config_api_datas = table_config_api_datas
        self.map_display_name_to_obj = { obj['display_name']: obj for obj in table_config_api_datas }
        self.table_config_api_datas_original = copy.deepcopy(table_config_api_datas)



    def setup_menus(self):
        return 

    def run(self, table_config:dict=None, table_config_api_datas:list[dict]=None):
        if table_config:
            self.set_table_config(table_config)
        if table_config_api_datas:
            self.set_table_config_api_datas(table_config_api_datas)

        if not table_config or not table_config_api_datas:
            Utils.generate_QMsg_critical(None, title="테이블 설정 오류", text="테이블 설정 오류")
            return
        
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
        if INFO.IS_DEV:
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
        if INFO.IS_DEV:
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
            obj['is_hidden'] = not obj['is_hidden']

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
            if INFO.IS_DEV:
                for _obj현재, _obj원본 in zip(sorted_현재, sorted_원본):
                    logger.debug(f"get_changed_api_datas : {_obj현재['is_hidden']} , {_obj원본['is_hidden']}, {_obj현재['is_hidden'] != _obj원본['is_hidden']}")

            changed_api_datas = [ _obj현재 for _obj현재, _obj원본 in zip(sorted_현재, sorted_원본) 
                                 if _obj현재 != _obj원본 ]
            if INFO.IS_DEV:
                logger.info(f"변경된 API 데이터: {changed_api_datas}")

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

    def __init__(self, parent=None, table_config:dict=None, api_datas:list[dict]=None):
        super().__init__(parent)
        self.table_config = table_config
        self.api_datas = api_datas

        self._headers :list[str] = []
        self._data :list[any] = []
        self.display_to_attr_cache: dict[str, str] = {}  # <-- 추가

        self.set_table_config(table_config)
        self.set_api_datas(api_datas)

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
        view : TableView_TableConfigMode = self.parent()
        obj = view.map_display_name_to_obj[display_name]
        return obj['column_name']
        # return self.table_config['_mapping_display_to_attr'][display_name]
    
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
 

# class Wid_Header( QWidget):
#     """ parent가 명확하므로 lazy_attr_names 사용하지 않음 
#         table_name 은 부모에서 set_APP_ID 함수에서 설정됨.
#     """
#     on_save_clicked = pyqtSignal()
#     # lazy_attr_names = ['table_name']
#     def __init__(self, parent:Optional[QWidget]=None):
#         super().__init__(parent)

#         self.map_menu_urls = {
#             'row': f"config/v_header_menus/?page_size=0",
#             'col': f"config/h_header_menus/?page_size=0",
#             'cell': f"config/cell_menus/?page_size=0",
#         }
#         self.map_menu_urls_bulk = {
#             'row': f"config/table_v_header_link/bulk/",
#             'col': f"config/table_h_header_link/bulk/",
#             'cell': f"config/table_cell_menu_link/bulk/",
#         }
#         # self.connect_signals()
#         # self.run_lazy_attr()

#     def set_APP_ID(self, APP_ID:str):
#         self.table_name = Utils.get_table_name(APP_ID)
#         if self.is_connected:
#             self.disconnect_signals()
#         self.connect_signals()
    
#     def connect_signals(self):
#         try :
#             logger.info(f"connect_signals : {self.table_name}")
#             self.ui.PB_Row.clicked.connect( self.slot_PB_Row_Menu )
#             self.ui.PB_Col.clicked.connect( self.slot_PB_Col_Menu )
#             self.ui.PB_Cell.clicked.connect( self.slot_PB_Cell_Menu )
#             self.ui.PB_save.clicked.connect( self.slot_PB_save )
#             self.is_connected = True
#         except Exception as e:
#             logger.error(f"connect_signals 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")

#     def disconnect_signals(self):
#         try :
#             self.ui.PB_Row.clicked.disconnect()
#             self.ui.PB_Col.clicked.disconnect()
#             self.ui.PB_Cell.clicked.disconnect()
#             self.ui.PB_save.clicked.disconnect()
#             self.is_connected = False
#         except Exception as e:
#             logger.error(f"disconnect_signals 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")

#     def fetch_menu_items(self, url):
#         logger.debug(f"fetch_menu__items : url: {url}")
#         s = time.perf_counter()
#         _isok, _items = APP.API.fetch_fastapi(url)
#         e = time.perf_counter()
#         logger.debug(f"fetch_menu__items : 소요시간: {(e-s)*1000:.2f}msec")
#         if _isok:
#             logger.info(f"fetch_h_menu__items 완료 : {_items}")
#             return _items
#         else:
#             logger.error(f"fetch_h_menu__items 실패 : {_items}")
#             return []

#     def get_menus_from_info(self):
#         """ 현재 테이블의 메뉴 정보를 가져온다. """
        
#         for item in INFO.ALL_TABLE_TOTAL_CONFIG:
#             if item['table_name'] == self.table_name:
#                 self.menus = item.get('menus', {} )
#                 if self.menus:
#                     self.v_menus = self.menus.get( 'v_header', [] )
#                     self.h_menus = self.menus.get( 'h_header', [] )
#                     self.cell_menus = self.menus.get( 'cell_header', [] )
#                 else:
#                     self.v_menus = []
#                     self.h_menus = []
#                     self.cell_menus = []
#                 break
        

#     def run(self):
#         """ 작동하지 않음.==> set_APP_ID 에서 CONNECT_SIGNAL => SLOT 동작시, API 호출 동작함.
#             정리되면, INFO.ALL_TABLE_TOTAL_CONFIG 에서 메뉴 정보를 가져오는 함수를 만들어야 함.
#         """
#         if self.parent() and hasattr(self.parent(), 'table_name')   :
#             self.table_name = self.parent().table_name
#             logger.info(f"Wid_Config_Mode 초기화 완료 : TableName: {self.table_name}")
#             self.get_menus_from_info()
#             logger.debug (f" {self.table_name} 의 메뉴 정보 : {self.menus}")
#         else:
#             logger.error("Wid_Config_Mode 초기화 실패 : parent 가 없거나 table_name 이 없읍니다.")
#         self.connect_signals()

#     def api_send_menu_items(self, url:str,sendData:dict):
#         """ 각 모델에 bulk 업데이트 요청 """
#         _isok, _data = APP.API.post( url, data= sendData )
#         if _isok:
#             Utils.generate_QMsg_Information(self, title="메뉴 설정 완료", text="메뉴 설정 완료", autoClose= 1000)
#         else:
#             Utils.generate_QMsg_critical(self, title="메뉴 설정 실패", text="메뉴 설정 실패")
    
#     def get_menu_ids(self, _type:str):
#         """ 현재 테이블의 메뉴 정보를 가져온다. """
#         _menu_list = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_Menus', [])
#         if not _menu_list:
#             return []
        
#         logger.warning(f"get_menu_ids : _menu_list: {_menu_list}")
        
#         _menu_list_row = _menu_list.get('v_header', [])
#         _menu_list_col = _menu_list.get('h_header', [])
#         _menu_list_cell = _menu_list.get('cell_header', [])
#         match _type:
#             case 'row':
#                 if not _menu_list_row :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_row:
#                     ids.append( _obj.get('v_header').get('id') )
#                 return ids
#             case 'col':
#                 if not _menu_list_col :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_col:
#                     ids.append( _obj.get('h_header').get('id') )
#                 return ids
#             case 'cell':
#                 if not _menu_list_cell :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_cell:
#                     ids.append( _obj.get('cell_header').get('id') )
#                 return ids
#             case _:
#                 return []

#     def slot_PB_Row_Menu(self):
#         logger.info("slot_PB_Row_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['row'])

#         dialog = TableConfigDialog (self, full_data=items, selected_ids = self.get_menu_ids('row') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
            
#             sendData = {
#                 "table_name": self.table_name,
#                 "ids": json.dumps(selected_ids, ensure_ascii=False),
#             }
#             self.api_send_menu_items(self.map_menu_urls_bulk['row'], sendData)

#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")




#     def slot_PB_Col_Menu(self):
#         logger.info("slot_PB_Col_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['col'])
#         dialog = TableConfigDialog  (self, full_data=items, selected_ids = self.get_menu_ids('col') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
#             sendData = {
#                 "table_name": self.table_name,
#                 "ids": json.dumps(selected_ids, ensure_ascii=False),
#             }
#             self.api_send_menu_items(self.map_menu_urls_bulk['col'], sendData)
#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

#     def slot_PB_Cell_Menu(self):
#         logger.info("slot_PB_Cell_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['cell'])
#         dialog = TableConfigDialog(self, full_data=items, selected_ids = self.get_menu_ids('cell') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

#     def slot_PB_save(self):
#         self.on_save_clicked.emit()
#         return 
#         if hasattr ( self.parent(), 'is_no_config_initial' ) and self.parent().is_no_config_initial:
#             api_datas = self.parent().view.get_table_config_api_datas_to_send_if_no_config_initial()
#             print (f" if no config initial : api_datas: {api_datas}")
#             self.send_api_datas(api_datas)

#         elif hasattr(self.parent(), 'view') and hasattr(self.parent().view, 'get_changed_api_datas'):
#             api_datas = self.parent().view.get_changed_api_datas()
#             self.send_api_datas(api_datas)

#         else:
#             Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="프로그램 오류 발생")

#     def send_api_datas(self, api_datas:list[dict]):
#         if api_datas:
#             sendData = {
#                 "table_name": self.table_name,
#                 "datas": json.dumps(api_datas, ensure_ascii=False),
#             }
#             isok, _data = APP.API.post(f"config/table_config/bulk/", data= sendData)
#             if isok:
#                 Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 완료", text="테이블 설정 완료", autoClose= 1000)
#                 # self.event_bus.publish(f"{self.table_name}:table_config_mode", True)
#             else:
#                 Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="DB 저장 실패")
#         else:
#             Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 ", text="테이블 설정 변경이 없읍니다.")
        

class Wid_TableConfigMode( QWidget ):

    def __init__(self, parent:QWidget, table_config:dict=None, api_datas:list[dict]=None, is_no_config_initial:Optional[bool]=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.table_config = table_config
        self.api_datas = api_datas
        self.is_no_config_initial = is_no_config_initial
        if all( [bool(is_no_config_initial), bool(table_config), bool(api_datas)] ):
            Utils.generate_QMsg_critical(None, title="오류", text="table_config 또는 api_datas 또는 is_no_config_initial 가 없습니다.")
            return
        self.start_init_time = time.perf_counter()


        self.view:Optional[TableView_TableConfigMode] =  TableView_TableConfigMode(self, table_config=self.table_config )
        self.model:Optional[TableModel_TableConfigMode] = TableModel_TableConfigMode(self.view, table_config=self.table_config, api_datas=self.api_datas)
        self.delegate:Optional[ConfigTableDelegate] = ConfigTableDelegate(self)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)
        # self.model().set_table_view(self.view)

        self.init_ui()


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
        self.v_layout = QVBoxLayout()

        self.wid_header_container = QWidget()
        h_layout = QHBoxLayout()
        self.wid_header_container.setLayout(h_layout)
        label = QLabel("환경설정모드")
        label.setStyleSheet("""
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
        h_layout.addWidget(label)
        h_layout.addStretch()
        self.PB_Row_Menu = QPushButton("행메뉴(현재 제외됨)")
        self.PB_Col_Menu = QPushButton("열메뉴(현재 제외됨)")
        self.PB_Cell_Menu = QPushButton("셀메뉴(현재 제외됨)")
        self.PB_Row_Menu.setEnabled(False)
        self.PB_Col_Menu.setEnabled(False)
        self.PB_Cell_Menu.setEnabled(False)
        self.PB_Save = QPushButton("저장")
        h_layout.addWidget(self.PB_Row_Menu)
        h_layout.addWidget(self.PB_Col_Menu)
        h_layout.addWidget(self.PB_Cell_Menu)
        h_layout.addWidget(self.PB_Save)
        self.v_layout.addWidget(self.wid_header_container)

        self.PB_Save.clicked.connect(self.slot_PB_Save)

        self.v_layout.addWidget(self.view)
        self.setLayout(self.v_layout)


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



    def run(self):
        return 
 

    def clear_layout(self):
        """레이아웃 초기화"""
        try:
            if self.layout:
                Utils.deleteLayout(self.layout)
        except Exception as e:
            logger.error(f"레이아웃 초기화 중 오류 발생: {e}")

    def slot_PB_Save(self):
        if self.is_no_config_initial:
            api_datas = self.view.get_table_config_api_datas_to_send_if_no_config_initial()
        else:
            api_datas = self.view.get_changed_api_datas()

        if api_datas:
            _text = f" 변경된 data 수 : {len(api_datas)} <br><br> 변경된 내용 :<br>"
            for obj in api_datas:
                _text += f"{json.dumps(obj, ensure_ascii=False)} <br>"

            if Utils.QMsg_question(None, title="환경저장", text=_text):
                self.send_api_datas(api_datas)
        else:
            Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 ", text="테이블 설정 변경이 없읍니다.")

        # if hasattr ( self.parent(), 'is_no_config_initial' ) and self.parent().is_no_config_initial:
        #     api_datas = self.parent().view.get_table_config_api_datas_to_send_if_no_config_initial()
        #     print (f" if no config initial : api_datas: {api_datas}")
        #     self.send_api_datas(api_datas)

        # elif hasattr(self.parent(), 'view') and hasattr(self.parent().view, 'get_changed_api_datas'):
        #     api_datas = self.parent().view.get_changed_api_datas()
        #     self.send_api_datas(api_datas)

        # else:
        #     Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="프로그램 오류 발생")

    def send_api_datas(self, api_datas:list[dict]):
        sendData = {
            "table_name": api_datas[0]['table_name'],
            "datas": json.dumps(api_datas, ensure_ascii=False),
        }
        isok, _data = APP.API.post(f"config/table_config/bulk/", data= sendData)
        if isok:
            Utils.generate_QMsg_Information(self.parent(), title="테이블  설정 DB저장 완료", text="변경된 테이블 설정은 필히, table config 에서 적용해야 합니다.", autoClose= 1000)
            # self.event_bus.publish(f"{self.table_name}:table_config_mode", True)
        else:
            Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="DB 저장 실패")

    

class Dialog_TableConfigMode(QDialog):
    def __init__(self, parent=None, table_config:dict=None, api_datas:list[dict]=None,  is_no_config_initial:Optional[bool]=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.table_config = table_config
        self.api_datas = api_datas
        self.is_no_config_initial = is_no_config_initial
        if not all( [ is_no_config_initial is not None,  bool(table_config), bool(api_datas)] ):
            Utils.generate_QMsg_critical(None, title="오류", text=f"table_config:{bool(table_config)}, api_datas:{bool(api_datas)}, is_no_config_initial:{is_no_config_initial} 또는 api_datas 또는 is_no_config_initial 가 없습니다.")
            self.close()
            return
        self.kwargs = kwargs

        self.setMinimumSize(1200, 800)
        self.setWindowTitle("Table 환경설정")
        self.init_ui()

    def init_ui(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.wid_table = Wid_TableConfigMode(self, table_config=self.table_config, api_datas=self.api_datas, is_no_config_initial=self.is_no_config_initial, **self.kwargs)
        self.v_layout.addWidget(self.wid_table)

        


# class TableConfigDialog(QDialog):
#     def __init__(self, parent=None, full_data: list[dict]=[], selected_ids: list[int] = []):
#         super().__init__(parent)
#         self.setWindowTitle("테이블 설정")
#         self.resize(600, 400)

#         self.full_data = {item["id"]: item for item in full_data if item.get("id") is not None and item.get('name') != 'seperator'}
#         self.seperator_data = { 'id':item['id'] for item in full_data if item.get("id") is not None and item.get('name') == 'seperator'}
#         self.selected_ids = set(selected_ids or [])
#         self.init_ui()

#     def init_ui(self):
#         layout = QVBoxLayout(self)
#         main_layout = QHBoxLayout()
#         layout.addLayout(main_layout)

#         # 왼쪽: 전체 항목
#         self.available_list = QListWidget()
#         self.available_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
#         main_layout.addWidget(self.available_list)

#         # 중간 버튼
#         button_layout = QVBoxLayout()
#         self.btn_add = QPushButton("→")
#         self.btn_remove = QPushButton("←")
#         self.btn_separator = QPushButton("＋ 구분선")
#         button_layout.addStretch()
#         button_layout.addWidget(self.btn_add)
#         button_layout.addWidget(self.btn_remove)
#         button_layout.addWidget(self.btn_separator)
#         button_layout.addStretch()
#         main_layout.addLayout(button_layout)

#         # 오른쪽: 선택된 항목
#         self.selected_list = QListWidget()
#         self.selected_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
#         main_layout.addWidget(self.selected_list)

#         # 하단: 저장/취소
#         self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
#         layout.addWidget(self.button_box)

#         self.populate_lists()

#         # 연결
#         self.btn_add.clicked.connect(self.move_to_selected)
#         self.btn_remove.clicked.connect(self.move_to_available)
#         self.btn_separator.clicked.connect(self.insert_separator)
#         self.button_box.accepted.connect(self.accept)
#         self.button_box.rejected.connect(self.reject)

#     def populate_lists(self):
#         self.available_list.clear()
#         self.selected_list.clear()

#         for id_, item in self.full_data.items():
#             if id_ in self.selected_ids:
#                 self.selected_list.addItem(self.create_item(item))
#             else:
#                 self.available_list.addItem(self.create_item(item))

#     def create_item(self, item: dict):
#         text = f"{item['title']} ({item['name']})"
#         list_item = QListWidgetItem(text)
#         list_item.setData(Qt.ItemDataRole.UserRole, item["id"])
#         list_item.setData(Qt.ItemDataRole.UserRole + 1, "menu")
#         return list_item

#     def insert_separator(self):
#         sep_item = QListWidgetItem("─── 구분선 ───")
#         sep_item.setFlags(sep_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
#         sep_item.setData(Qt.ItemDataRole.UserRole, None)
#         sep_item.setData(Qt.ItemDataRole.UserRole + 1, "separator")
#         self.selected_list.addItem(sep_item)

#     def move_to_selected(self):
#         for item in self.available_list.selectedItems():
#             self.available_list.takeItem(self.available_list.row(item))
#             self.selected_list.addItem(item)

#     def move_to_available(self):
#         for item in self.selected_list.selectedItems():
#             # separator는 삭제 불가
#             if item.data(Qt.ItemDataRole.UserRole + 1) == "separator":
#                 continue
#             self.selected_list.takeItem(self.selected_list.row(item))
#             self.available_list.addItem(item)

#     def get_selected_items(self):
#         result = []
#         for i in range(self.selected_list.count()):
#             item = self.selected_list.item(i)
#             item_type = item.data(Qt.ItemDataRole.UserRole + 1)
#             if item_type == "separator":
#                 result.append( self.seperator_data)
#             else:
#                 result.append({"id": item.data(Qt.ItemDataRole.UserRole)})
#         return result


# class Wid_Config_Mode( QWidget):
#     """ parent가 명확하므로 lazy_attr_names 사용하지 않음 
#         table_name 은 부모에서 set_APP_ID 함수에서 설정됨.
#     """
#     on_save_clicked = pyqtSignal()
#     # lazy_attr_names = ['table_name']
#     def __init__(self, parent:Optional[Wid_table_Base]=None):
#         super().__init__(parent)

#         self.is_connected = False

#         self.event_bus = event_bus
#         self.ui = Ui_Wid_Table_Config()
#         self.ui.setupUi(self)
#         self.hide()        

#         self.map_menu_urls = {
#             'row': f"config/v_header_menus/?page_size=0",
#             'col': f"config/h_header_menus/?page_size=0",
#             'cell': f"config/cell_menus/?page_size=0",
#         }
#         self.map_menu_urls_bulk = {
#             'row': f"config/table_v_header_link/bulk/",
#             'col': f"config/table_h_header_link/bulk/",
#             'cell': f"config/table_cell_menu_link/bulk/",
#         }
#         # self.connect_signals()
#         # self.run_lazy_attr()

#     def set_APP_ID(self, APP_ID:str):
#         self.table_name = Utils.get_table_name(APP_ID)
#         if self.is_connected:
#             self.disconnect_signals()
#         self.connect_signals()
    
#     def connect_signals(self):
#         try :
#             logger.info(f"connect_signals : {self.table_name}")
#             self.ui.PB_Row.clicked.connect( self.slot_PB_Row_Menu )
#             self.ui.PB_Col.clicked.connect( self.slot_PB_Col_Menu )
#             self.ui.PB_Cell.clicked.connect( self.slot_PB_Cell_Menu )
#             self.ui.PB_save.clicked.connect( self.slot_PB_save )
#             self.is_connected = True
#         except Exception as e:
#             logger.error(f"connect_signals 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")

#     def disconnect_signals(self):
#         try :
#             self.ui.PB_Row.clicked.disconnect()
#             self.ui.PB_Col.clicked.disconnect()
#             self.ui.PB_Cell.clicked.disconnect()
#             self.ui.PB_save.clicked.disconnect()
#             self.is_connected = False
#         except Exception as e:
#             logger.error(f"disconnect_signals 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")

#     def fetch_menu_items(self, url):
#         logger.debug(f"fetch_menu__items : url: {url}")
#         s = time.perf_counter()
#         _isok, _items = APP.API.fetch_fastapi(url)
#         e = time.perf_counter()
#         logger.debug(f"fetch_menu__items : 소요시간: {(e-s)*1000:.2f}msec")
#         if _isok:
#             logger.info(f"fetch_h_menu__items 완료 : {_items}")
#             return _items
#         else:
#             logger.error(f"fetch_h_menu__items 실패 : {_items}")
#             return []

#     def get_menus_from_info(self):
#         """ 현재 테이블의 메뉴 정보를 가져온다. """
        
#         for item in INFO.ALL_TABLE_TOTAL_CONFIG:
#             if item['table_name'] == self.table_name:
#                 self.menus = item.get('menus', {} )
#                 if self.menus:
#                     self.v_menus = self.menus.get( 'v_header', [] )
#                     self.h_menus = self.menus.get( 'h_header', [] )
#                     self.cell_menus = self.menus.get( 'cell_header', [] )
#                 else:
#                     self.v_menus = []
#                     self.h_menus = []
#                     self.cell_menus = []
#                 break
        

#     def run(self):
#         """ 작동하지 않음.==> set_APP_ID 에서 CONNECT_SIGNAL => SLOT 동작시, API 호출 동작함.
#             정리되면, INFO.ALL_TABLE_TOTAL_CONFIG 에서 메뉴 정보를 가져오는 함수를 만들어야 함.
#         """
#         if self.parent() and hasattr(self.parent(), 'table_name')   :
#             self.table_name = self.parent().table_name
#             logger.info(f"Wid_Config_Mode 초기화 완료 : TableName: {self.table_name}")
#             self.get_menus_from_info()
#             logger.debug (f" {self.table_name} 의 메뉴 정보 : {self.menus}")
#         else:
#             logger.error("Wid_Config_Mode 초기화 실패 : parent 가 없거나 table_name 이 없읍니다.")
#         self.connect_signals()

#     def api_send_menu_items(self, url:str,sendData:dict):
#         """ 각 모델에 bulk 업데이트 요청 """
#         _isok, _data = APP.API.post( url, data= sendData )
#         if _isok:
#             Utils.generate_QMsg_Information(self, title="메뉴 설정 완료", text="메뉴 설정 완료", autoClose= 1000)
#         else:
#             Utils.generate_QMsg_critical(self, title="메뉴 설정 실패", text="메뉴 설정 실패")
    
#     def get_menu_ids(self, _type:str):
#         """ 현재 테이블의 메뉴 정보를 가져온다. """
#         _menu_list = INFO.ALL_TABLE_TOTAL_CONFIG.get(self.table_name, {}).get('MAP_TableName_To_Menus', [])
#         if not _menu_list:
#             return []
        
#         logger.warning(f"get_menu_ids : _menu_list: {_menu_list}")
        
#         _menu_list_row = _menu_list.get('v_header', [])
#         _menu_list_col = _menu_list.get('h_header', [])
#         _menu_list_cell = _menu_list.get('cell_header', [])
#         match _type:
#             case 'row':
#                 if not _menu_list_row :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_row:
#                     ids.append( _obj.get('v_header').get('id') )
#                 return ids
#             case 'col':
#                 if not _menu_list_col :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_col:
#                     ids.append( _obj.get('h_header').get('id') )
#                 return ids
#             case 'cell':
#                 if not _menu_list_cell :
#                     return []
#                 ids = []
#                 for _obj in _menu_list_cell:
#                     ids.append( _obj.get('cell_header').get('id') )
#                 return ids
#             case _:
#                 return []

#     def slot_PB_Row_Menu(self):
#         logger.info("slot_PB_Row_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['row'])

#         dialog = TableConfigDialog (self, full_data=items, selected_ids = self.get_menu_ids('row') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
            
#             sendData = {
#                 "table_name": self.table_name,
#                 "ids": json.dumps(selected_ids, ensure_ascii=False),
#             }
#             self.api_send_menu_items(self.map_menu_urls_bulk['row'], sendData)

#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")




#     def slot_PB_Col_Menu(self):
#         logger.info("slot_PB_Col_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['col'])
#         dialog = TableConfigDialog  (self, full_data=items, selected_ids = self.get_menu_ids('col') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
#             sendData = {
#                 "table_name": self.table_name,
#                 "ids": json.dumps(selected_ids, ensure_ascii=False),
#             }
#             self.api_send_menu_items(self.map_menu_urls_bulk['col'], sendData)
#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

#     def slot_PB_Cell_Menu(self):
#         logger.info("slot_PB_Cell_Menu")
#         items = self.fetch_menu_items(self.map_menu_urls['cell'])
#         dialog = TableConfigDialog(self, full_data=items, selected_ids = self.get_menu_ids('cell') )
#         if dialog.exec_() == QDialog.DialogCode.Accepted:
#             selected_ids = dialog.get_selected_items()
#             logger.debug(f"slot_PB_Row_Menu : selected_ids: {selected_ids}")

#     def slot_PB_save(self):
#         if hasattr ( self.parent(), 'is_no_config_initial' ) and self.parent().is_no_config_initial:
#             api_datas = self.parent().view.get_table_config_api_datas_to_send_if_no_config_initial()
#             print (f" if no config initial : api_datas: {api_datas}")
#             self.send_api_datas(api_datas)

#         elif hasattr(self.parent(), 'view') and hasattr(self.parent().view, 'get_changed_api_datas'):
#             api_datas = self.parent().view.get_changed_api_datas()
#             self.send_api_datas(api_datas)

#         else:
#             Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="프로그램 오류 발생")

#     def send_api_datas(self, api_datas:list[dict]):
#         if api_datas:
#             sendData = {
#                 "table_name": self.table_name,
#                 "datas": json.dumps(api_datas, ensure_ascii=False),
#             }
#             isok, _data = APP.API.post(f"config/table_config/bulk/", data= sendData)
#             if isok:
#                 Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 완료", text="테이블 설정 완료", autoClose= 1000)
#                 # self.event_bus.publish(f"{self.table_name}:table_config_mode", True)
#             else:
#                 Utils.generate_QMsg_critical(self.parent(), title="테이블 설정 실패", text="DB 저장 실패")
#         else:
#             Utils.generate_QMsg_Information(self.parent(), title="테이블 설정 ", text="테이블 설정 변경이 없읍니다.")
