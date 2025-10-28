from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import modules.user.utils as Utils

class Mixin_Create_Config:
       
    def mixin_check_config_data(self) -> bool:
        """ config data가 있으면 True, 없으면 False """
        if 'is_no_config_initial' in self.lazy_attr_values :
            return not self.lazy_attr_values['is_no_config_initial']
        return False

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