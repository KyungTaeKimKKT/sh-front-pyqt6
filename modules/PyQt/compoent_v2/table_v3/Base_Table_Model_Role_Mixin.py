from __future__ import annotations
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from modules.envs.resources import resources

import datetime
import json
import urllib.parse
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from info import Info_SW as INFO

class CustomRoles:
    """사용자 정의 Role enum 정의"""
    DisplayRole = Qt.ItemDataRole.DisplayRole
    EditRole = Qt.ItemDataRole.EditRole
    BackgroundRole = Qt.ItemDataRole.BackgroundRole
    ForegroundRole = Qt.ItemDataRole.ForegroundRole
    FontRole = Qt.ItemDataRole.FontRole
    DecorationRole = Qt.ItemDataRole.DecorationRole
    TextAlignmentRole = Qt.ItemDataRole.TextAlignmentRole
    ToolTipRole = Qt.ItemDataRole.ToolTipRole
    CheckStateRole = Qt.ItemDataRole.CheckStateRole
    StatusTipRole = Qt.ItemDataRole.StatusTipRole
    WhatsThisRole = Qt.ItemDataRole.WhatsThisRole

    # Custom roles start from Qt.UserRole
    GetIDRole = Qt.ItemDataRole.UserRole + 1
    NoEditRole = Qt.ItemDataRole.UserRole + 2
    CustomTextRole = Qt.ItemDataRole.UserRole + 3
    RawDataRole = Qt.ItemDataRole.UserRole + 4

    _role_map = {
        DisplayRole: 'display',
        EditRole: 'edit',
        BackgroundRole: 'background',
        ForegroundRole: 'foreground',
        FontRole: 'font',
        DecorationRole: 'decoration',
        TextAlignmentRole: 'textAlignment',
        ToolTipRole: 'tooltip',
        CheckStateRole: 'checkState',
        StatusTipRole: 'statusTip',
        WhatsThisRole: 'whatsThis',

        GetIDRole: 'getID',
        NoEditRole: 'noEdit',
        CustomTextRole: 'customText',
        RawDataRole: 'rawData',
    }

    @classmethod
    def get_name(cls, role: int) -> str | None:
        return cls._role_map.get(role)

    @classmethod
    def get_roles(cls) -> dict[int, str]:
        return cls._role_map

    @classmethod
    def get_roles_bytes(cls) -> dict[int, bytes]:
        return {k: v.encode("utf-8") for k, v in cls._role_map.items()}
    

class Base_Table_Model_Role_Mixin:
    """Role 이름 매핑 및 처리 유틸리티"""
    Roles = None # 상속 class 에서 정의

    Boolean_Display_Map = {
        True: "예",
        False: "아니오",
    }
    MAX_DISPLAY_LENGTH = 40

    def roleNames(self):
        """모델에 등록된 role 이름을 바이트 맵핑으로 반환"""
        if hasattr(self, 'Roles'):
            return self.Roles.role_names()
        return super().roleNames() if hasattr(super(), 'roleNames') else {}
    
    def roleNames(self):
        """Qt 내부용: role:int → roleName:bytes"""
        if hasattr(self, "Roles") and self.Roles:
            return self.Roles.get_roles_bytes()
        return super().roleNames() if hasattr(super(), "roleNames") else {}

    def role_data(self, row: int, col: int, role: int, **kwargs) -> any:
        """역할에 따른 데이터를 자동으로 역할 메서드 호출로 연결"""
        if not hasattr(self, "Roles") or not self.Roles:
            return None
        
        name = self.Roles.get_name(role)
        if not name:
            return None

        method_name = f"_role_{name}"
        method = getattr(self, method_name, None)
        if method:
            return method(row, col, **kwargs)
        return None
    

    

    def _role_display( self, row:int, col:int, **kwargs) -> str:
        """표시 데이터 반환
        기본적으로 self._data 가 api_datas 인 list[dict] 인 경우 적용   
        """
        if not hasattr(self, '_data') or not self._data:
            return ''
        display_header_name = self._headers[col]
        attribute_name = self.table_config["_mapping_display_to_attr"][display_header_name] if self.table_config else display_header_name
        if attribute_name in self._data[row]:
            if self._data[row][attribute_name] is None:
                return ''
            return self._format_value_by_type(row, col)
        else:
            return ''

    
    def _role_edit( self, row:int, col:int, **kwargs) -> any:
        """표시 데이터 반환"""
        display_header_name = self._headers[col]
        attribute_name = self.table_config["_mapping_display_to_attr"][display_header_name] if self.table_config else display_header_name
        if attribute_name in self._data[row]:
            return self._data[row][attribute_name]
        else:
            return ''
    
    def _role_background( self, row:int, col:int, **kwargs) -> QColor:
        """배경색 반환"""
        if hasattr(self, '_edit_mode') and hasattr(self, '_modified_cells') and hasattr(self, '_modified_rows'):
            if self._edit_mode.lower() == 'cell' and (row, col) in self._modified_cells:
                return QColor('yellow')
            # 행 단위 변경 표시
            elif self._edit_mode.lower() == 'row' and row in self._modified_rows:
                return QColor('yellow')
            
    def _role_getID( self, row:int, col:int, **kwargs) -> int:
        """ID 반환"""
        id_dict = self.get_id_dict(row)
        return id_dict.get('id', -1)

    
    def _role_font( self, row:int, col:int, **kwargs) -> QFont:
        """폰트 반환"""
        if hasattr(self, '_edit_mode') and hasattr(self, '_modified_cells') and hasattr(self, '_modified_rows'):
            if (self._edit_mode.lower() == 'cell' and (row, col) in self._modified_cells) or \
                (self._edit_mode.lower() == 'row' and row in self._modified_rows):
                font = QFont()
                font.setBold(True)
                return font

    def _role_decoration( self, row:int, col:int, **kwargs) -> QPixmap:
        """기본 장식 규칙을 제공하는 메서드
		상속받은 클래스에서 오버라이드하여 사용할 수 있음
		
		Args:
			header_name: 컬럼 헤더 이름
			value: 셀 값
			index: 모델 인덱스
			
		Returns:
			QIcon 또는 None
		"""
        _type = self.get_header_types().get(self._headers[col], '')
        if _type in ['JSONField']:
            if len(self._role_display(row, col)) > 4:
                return resources.get_icon('json:icon')
        return None
    
    def _role_textAlignment( self, row:int, col:int, **kwargs) -> Qt.Alignment:
        """텍스트 정렬 반환"""
        return self.get_header_types_alignment_rule(row, col)
    
    def _role_tooltip( self, row:int, col:int, **kwargs) -> str:
        """툴팁 반환"""
        try:
            header_type = self.get_header_types().get(self._headers[col], '')

            if header_type == 'JSONField':
                display_header_name = self._headers[col]
                raw_value = self._data[row][self.get_attrName_from_display(display_header_name)]
                return json.dumps(raw_value, ensure_ascii=False, indent=2)
            return ''
        except Exception as e:
            if INFO.IS_DEV:
                logger.error(f"툴팁 오류: {e}")
                return ''
    
    def _role_checkState(self, row:int, col:int, **kwargs) -> Qt.CheckState:
        """체크 상태 반환"""
        if hasattr(self, 'is_check_column_no') and hasattr(self, 'CHECK_COLUMN_ATTR_NAME') and  hasattr(self, 'is_check_column_no') and callable(self.is_check_column_no) and self.is_check_column_no(col):
            return Qt.CheckState.Checked if self._data[row][self.CHECK_COLUMN_ATTR_NAME] else Qt.CheckState.Unchecked
        # return Qt.CheckState.Unchecked
    
    #### alias 선언
    _role_Display = _role_display
    _role_toolTip = _role_tooltip
    _role_Tooltip = _role_tooltip
    _role_Background = _role_background
    _role_Decoration = _role_decoration
    _role_Font = _role_font
    _role_TextAlignment = _role_textAlignment

    #### display role 포맷팅
    def _format_value_by_type(self, row:int, col:int) -> str:
        """데이터 타입에 따른 기본 포맷팅"""
        display_header_name = self._headers[col]
        attribute_name = self.table_config["_mapping_display_to_attr"][display_header_name] if self.table_config else display_header_name
        raw_value = self._data[row][attribute_name]
        if raw_value is None:
            return ""
            
        # 헤더 타입 확인
        header_type = self.table_config["_headers_types"].get(display_header_name, '') if self.table_config and '_headers_types' in self.table_config else ''
        if header_type:
            return self.get_role_display_by_header_type(row, col, header_type, raw_value)
        else:
            return self.get_role_display_by_value_type(row, col, raw_value)

    def get_role_display_by_value_type(self, row:int, col:int, raw_value:str) -> str:
        # 이미 Python 객체로 변환된 경우
        if isinstance(raw_value, datetime.datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(raw_value, datetime.date):
            return raw_value.strftime("%Y-%m-%d")
        elif isinstance(raw_value, bool):
            return "예" if raw_value else "아니오"
        elif isinstance(raw_value, (dict, list)):
            json_str = json.dumps(raw_value, ensure_ascii=False)
            if len(json_str) > 30:
                return json_str[:30] + "..."
            return json_str
        elif isinstance( raw_value, int):
            # 천 단위 구분 추가
            return "{:,}".format(raw_value)
        
        # 그 외의 경우 문자열로 변환
        return str(raw_value)

    def get_role_display_by_header_type(self, row:int, col:int, header_type:str, raw_value:str) -> str:
        # 문자열로 전달된 날짜/시간 데이터 처리

        # 헤더 타입이 날짜/시간 관련인 경우
        if header_type in ['DateField', 'DateTimeField', 'TimeField']:
            try:
                # ISO 형식 날짜/시간 문자열 처리 (예: "2023-04-15T14:30:45Z")
                if 'T' in raw_value : #and ('+' in raw_value or 'Z' in raw_value):
                    dt = datetime.datetime.fromisoformat(raw_value.replace('Z', '+00:00'))
                    if header_type == 'DateField':
                        return dt.strftime("%Y-%m-%d")
                    else:
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                
                # 날짜만 있는 경우 (예: "2023-04-15")
                elif '-' in raw_value and len(raw_value) <= 10:
                    dt = datetime.datetime.strptime(raw_value, "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                
                # 다른 날짜/시간 형식들도 필요에 따라 추가 가능
            except (ValueError, TypeError):
                # 변환 실패 시 원본 문자열 반환
                return raw_value
        
        # 불리언 값이 문자열로 전달된 경우
        elif header_type == 'BooleanField':
            return self.Boolean_Display_Map.get(raw_value, "아니오")

        
        # 파일 경로나 URL인 경우 파일명만 표시
        elif header_type in ['FileField', ] and raw_value:
            try:
                import urllib.parse
                
                # 데이터가 HTML 태그로 시작하거나 비정상적인 경우
                if '<' in raw_value or raw_value.startswith('p>'):
                    return "잘못된 데이터"
                
                # URL이나 파일 경로에서 마지막 부분(파일명)만 추출
                if '/' in raw_value or '\\' in raw_value:
                    # URL이나 경로의 마지막 부분 추출
                    file_name = raw_value.replace('\\', '/').split('/')[-1]
                    
                    # URL 인코딩된 문자열을 디코딩
                    decoded_name = urllib.parse.unquote(file_name)
                    
                    # 파일명이 너무 길면 축약
                    if len(decoded_name) > self.MAX_DISPLAY_LENGTH:
                        return f"{decoded_name[:self.MAX_DISPLAY_LENGTH]}..."
                        
                    return decoded_name
                
                # 경로 구분자가 없는 경우 그냥 디코딩
                return urllib.parse.unquote(raw_value)      
                
            except Exception as e:
                logger.error(f"파일명 변환 오류: {e}")
                return "파일"
        
        elif header_type in ['SerializerMethodField']:
            if isinstance(raw_value, str):
                return raw_value

            if isinstance(raw_value, (list, tuple, dict)):
                try:
                    return json.dumps(raw_value)[:self.MAX_DISPLAY_LENGTH]
                except Exception:
                    return str(raw_value)[:self.MAX_DISPLAY_LENGTH]

            # 그 외 타입은 fallback
            return str(raw_value)[:self.MAX_DISPLAY_LENGTH]
        
        elif header_type in ['JSONField']:
            return json.dumps(raw_value, ensure_ascii=False)[:self.MAX_DISPLAY_LENGTH]
        elif header_type in ['TextField']:
            return raw_value

        # 그 외의 경우 문자열로 변환
        return str(raw_value)



    #####
    def get_header_types_alignment_rule(self, row:int, col:int) -> any:
        """ self._header_types 를 기반으로 정렬 규칙을 반환
        
        header_type은 Python의 type().__name__ 속성을 기반으로 함
        - 기본값: 가로, 세로 중앙 정렬
        - 텍스트 필드: 좌측 정렬
        - 숫자 타입: 우측 정렬
        """
        try:
            # 기본 정렬은 가로, 세로 중앙 정렬
            default_alignment = Qt.AlignCenter
            display_header_name = self.get_headers()[col]
          
            # 헤더 타입이 지정된 경우
            if display_header_name in self.get_header_types():
                header_type = self.get_header_types()[display_header_name]
                return self.get_aligment_by_types(header_type)
            
            return default_alignment

        except Exception as e:
            logger.error(f"get_value_types_alignment_rul 오류: {e}")
            logger.error(f"header_name: {display_header_name}")
            logger.error(f"value: {self._data[row][col]}")
            logger.error(f"index: {QModelIndex(row, col, self)}")
            logger.error(f"{traceback.format_exc()}")
            return default_alignment
        
    def get_aligment_by_types(self, _typeName:str ) -> Qt.Alignment:
        if _typeName in ['IntegerField', 'FloatField', 'DecimalField', ]:
            return Qt.AlignRight | Qt.AlignVCenter
        elif _typeName in ['TextField']:
            return Qt.AlignLeft | Qt.AlignVCenter
        elif _typeName in ['CharField','BooleanField']:
            return Qt.AlignCenter
        return Qt.AlignCenter