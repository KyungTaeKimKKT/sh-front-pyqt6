from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from PyQt6.QtCore import QAbstractTableModel
from PyQt6.QtWidgets import QStyledItemDelegate, QTableView

# from modules.PyQt.compoent_v2.table_v2.Base_Table_View import Base_Table_View
# from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model
# from modules.PyQt.compoent_v2.table_v2.Wid_table_Base_for_stacked import Wid_table_Base_for_stacked
import modules.user.utils as Utils
from info import Info_SW as INFO
import copy
import traceback
from modules.logging_config import get_plugin_logger

logger = get_plugin_logger()

class Mixin_Table_Config:
       
    def mixin_check_config_data(self) -> bool:
        """ config data가 있으면 True, 없으면 False """
        if Utils.is_valid_attr_name(self, 'lazy_attrs', dict):
            self.lazy_attr_values = self.lazy_attrs
            if 'is_no_config_initial' in self.lazy_attrs :
                return not self.lazy_attrs['is_no_config_initial']
            return False
        elif Utils.is_valid_attr_name(self, 'lazy_attr_values', dict):
            self.lazy_attrs = self.lazy_attr_values
            if 'is_no_config_initial' in self.lazy_attr_values :
                return not self.lazy_attr_values['is_no_config_initial']
            return False
        else:
            raise ValueError(f"{self.__class__.__name__} : lazy_attrs or lazy_attr_values 가 없습니다.")

    def mixin_create_config(self, api_datas:list[dict]) -> tuple[dict, list[dict]]:
        """ 반환값으로, self.table_config , self.table_config_api_datas  """
        DBs = self.mixin_create_config_api_datas(api_datas)
        표시명 = 'display_name'
        table_config = {
            '_table_name': self.table_name,
            '_table_config_api_datas': DBs,
            '_mapping_attr_to_display': {
                _obj.get('column_name'): _obj.get(표시명) for _obj in DBs
            },
            '_mapping_display_to_attr': {
                _obj.get(표시명): _obj.get('column_name') for _obj in DBs
            },
            '_headers': [_obj.get(표시명) for _obj in DBs],
            '_headers_types': {
                _obj.get(표시명): _obj.get('column_type') for _obj in DBs
            },
            '_hidden_columns': [
                idx for idx, _obj in enumerate(DBs) if _obj.get('is_hidden', False)
            ],
            '_no_edit_cols': [
                idx for idx, _obj in enumerate(DBs) if not _obj.get('is_editable', True)
            ],
            '_column_types': {
                _obj.get(표시명): _obj.get('column_type') for _obj in DBs
            },
            '_column_styles': {
                _obj.get(표시명): _obj.get('cell_style') for _obj in DBs
            },
            '_column_widths': {
                _obj.get(표시명): _obj.get('column_width', 0) for _obj in DBs
            },
            '_table_style': DBs[0].get('table_style') if DBs else None
        }
        return table_config, DBs
    
    def mixin_create_config_api_datas(self, api_datas:list[dict]) -> list[dict]:
        obj = self.mixin_get_sample_obj(api_datas)
        DBs = []
        for index, (key, value) in enumerate(obj.items()):
            DB = {}
            DB['id'] = -1
            DB['table_name'] = self.table_name
            DB['column_name'] = key
            DB['display_name'] = key
            DB['column_type'] = Utils.get_drf_field_type_by_value(value)
            DB['column_width'] = 0
            DB['is_hidden'] = False
            DB['order'] = index
            DBs.append(DB)

        return DBs
    
    def mixin_get_sample_obj(self, api_datas: list[dict]) -> dict:
        if not api_datas:
            return {}

        # 모든 dict가 동일한 key set인지 확인
        first_keys = set(api_datas[0].keys())
        if all(set(d.keys()) == first_keys for d in api_datas[1:]):
            return api_datas[0]

        # 아니면 key 수가 가장 많은 dict 반환
        return max(api_datas, key=lambda d: len(d.keys()))
    
    	
    def mixin_on_all_lazy_attrs_ready(self, APP_ID:Optional[int] = None, **kwargs):		
        try:
            if APP_ID is None:
                return 

            self._initialize_from_kwargs(**kwargs)
            if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
                raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
            self.appDict =  copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
            self.table_name = Utils.get_table_name(APP_ID)
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)

            if self.mixin_check_config_data():
                self.table_config = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig'])
                self.table_config_api_datas = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas'])
                self.on_table_config_refresh(False)            
            self.subscribe_gbus()

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            Utils.generate_QMsg_critical(None, title="서버 조회 오류", text="on_all_lazy_attrs_ready 오류" )
            # raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")

    
    def mixin_on_table_config_refresh(self, is_refresh:bool=True):
        """ table_config 적용 : is_refresh가 True => ws로 새로운 config 받은 것. """
        try:
            if isinstance( self, QStyledItemDelegate):
                return 
            if is_refresh:
                if not self.mixin_check_table_config_changed():
                    return
                else:
                    if INFO._get_is_table_config_admin():
                        Utils.QMsg_Info( None, title='table config 변경 적용 ', text=f"table_name:{self.table_name}"    )                    
                    self.table_config = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig'])
                    self.table_config_api_datas = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas'])
            
            self.set_table_config()

        except Exception as e:
            logger.error(f"on_table_config 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_table_config 오류: {e}")
        
    def set_table_config(self):
        if isinstance( self.model, QAbstractTableModel):
            self.model.set_table_config(self.table_config, self.table_config_api_datas)
        if isinstance( self.view,  QTableView):
            self.view.set_table_config(self.table_config, self.table_config_api_datas)

        if isinstance( self.model, QAbstractTableModel):
            self.model.layoutChanged.emit()

    def mixin_check_table_config_changed(self):
        """ table_config 변경 시 True 반환 """
        if self.table_config != INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig']:
            return True
        if self.table_config_api_datas != INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas']:
            return True
        return False