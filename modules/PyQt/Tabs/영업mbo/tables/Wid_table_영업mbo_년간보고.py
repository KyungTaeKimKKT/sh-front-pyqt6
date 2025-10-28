from __future__ import annotations
from modules.common_import_v2 import *


MONEY_UNIT_DICT = {
        '원': 1,
        '천원': 1000,
        '백만원': 1000000,
        '억': 100000000,
    }

class TableView_영업mbo_년간보고(Base_Table_View):
    pass

    


class TableModel_영업mbo_년간보고(Base_Table_Model):
    # money_formatting_col_list:Optional[list[str]] = None

    
    @property
    def money_formatting_col_list(self) -> list[int]:
        return [ self.get_column_no_from_attr_name(field_name) 
                                for field_name in ['합계'] + [ f'month_{i:02d}' for i in range(1, 13) ] ]

    def _role_display(self, row:int, col:int) -> str:
        """ 컬럼 이름 반환 """
        if col in self.money_formatting_col_list:
            attr_name = self.get_field_name_by_column_no(col)
            value = self._data[row][attr_name]
            return self.convert_by_money_unit(value)
        return super()._role_display(row, col)


    def set_money_unit(self, money_unit_str:str = '백만원' ):
        """ 금액 단위 설정 """
        self.money_unit:int = MONEY_UNIT_DICT[money_unit_str]
        self.layoutChanged.emit()
    
    def convert_by_money_unit(self, value:int|float) -> str:
        """ 금액 단위 변환 """
        if self.money_unit is None:
            self.money_unit =  MONEY_UNIT_DICT['백만원']

        match self.money_unit:
            case 1:
                return f"{value:,}"  # 천 단위 쉼표 추가
            case 1000:
                return f"{value/1000:,.0f}"  # 천원 단위, 소수점 없이
            case 1000000:
                return f"{value/1000000:,.0f}"  # 백만원 단위, 소수점 1자리
            case 100000000:
                return f"{value/100000000:,.2f}"  # 억 단위, 소수점 2자리
            case _:
                return str(value)


class TableDelegate_영업mbo_년간보고(Base_Delegate):
    pass
    


        

class Wid_table_영업mbo_년간보고( Wid_table_Base_V2 ):

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()

    def setup_table(self):
        self.view = TableView_영업mbo_년간보고(self)
        self.model = TableModel_영업mbo_년간보고(self.view )
        self.delegate = TableDelegate_영업mbo_년간보고(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

        self.model.set_money_unit(  money_unit_str = self.combo_money_unit.currentText() )

    
    def create_custom_table_header(self) -> QWidget:
        """ 이 widget은 테이블 생성전에 실행됨 """
        self.custom_table_header = QWidget()
        h_layout = QHBoxLayout( self.custom_table_header )

        h_layout.addWidget( QLabel('금액단위: ') )

        # 새로운 콤보박스 생성
        self.combo_money_unit = Custom_Combo(self)
        self.combo_money_unit.addItems(['원', '천원', '백만원', '억'])
        self.combo_money_unit.setCurrentIndex(2)
        h_layout.addWidget(self.combo_money_unit)

        h_layout.addStretch()
        ### lambda라 lazy connect 됨.
        self.combo_money_unit.currentIndexChanged.connect(
             lambda: self.model.set_money_unit(self.combo_money_unit.currentText())
        )
        return self.custom_table_header



 