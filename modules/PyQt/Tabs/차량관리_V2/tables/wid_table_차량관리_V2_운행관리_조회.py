from modules.common_import import *
from modules.PyQt.Tabs.차량관리_V2.tables.wid_table_차량관리_V2_운행관리_관리자 import (
    Wid_table_차량관리_V2_운행관리_관리자, 
    TableView_차량관리_V2_운행관리_관리자, 
    TableModel_차량관리_V2_운행관리_관리자, 
    TableDelegate_차량관리_V2_운행관리_관리자,
)

class InfoDialog_차량정보(QDialog):
    def __init__(self, parent: QWidget = None, data: dict = None):
        super().__init__(parent)
        self.setWindowTitle("🚗 차량 상세 정보")
        self.setMinimumWidth(480)
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(10)

        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)

        value_font = QFont()
        value_font.setPointSize(10)

        # 표시 순서 지정
        field_order = [
            '법인명', '차종', '차량번호', '타이어규격', '공급업체',
            '차량가격', '보증금', '대여료_VAT포함', '약정운행거리', '초과거리부담금',
            '시작일', '종료일', 'is_exist', '관리자수', '관리자_ids'
        ]

        for key in field_order:
            if key == '관리자_ids':
                label = QLabel(f"관리자")
                value = []
                for user_id in self.data.get('관리자_ids', []):
                    user_info = INFO._get_user_info(user_id)
                    value.append(user_info.get('user_성명', 'unknown') )
                value = ", ".join(value)
                value_label = QLabel(value)

            else:
                value = self.data.get(key, 'unknown')
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                elif isinstance(value, bool):
                    value = "✅ 있음" if value else "❌ 없음"

                label = QLabel(f"{key}:")
                value_label = QLabel(str(value))

            label.setFont(label_font)            
            value_label.setFont(value_font)
            value_label.setWordWrap(True)

            form_layout.addRow(label, value_label)

        layout.addLayout(form_layout)

        # 확인 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        button_box.setCenterButtons(True)
        layout.addWidget(button_box)

class TableView_차량관리_V2_운행관리_조회(TableView_차량관리_V2_운행관리_관리자):
    pass


class TableModel_차량관리_V2_운행관리_조회(TableModel_차량관리_V2_운행관리_관리자):
    pass


class TableDelegate_차량관리_V2_운행관리_조회(TableDelegate_차량관리_V2_운행관리_관리자):
    pass


class Wid_table_차량관리_V2_운행관리_조회( Wid_table_Base_for_stacked ):

    @property
    def map_index_to_widget(self):
        if not hasattr(self, 'widget_menu') or not isinstance(self.widget_menu, QWidget):
            self.widget_menu = self._create_widget_menu()
        return {
            1: self.widget_menu
        }

    @property
    def map_pb_to_generate_info(self):
        """ widget 버튼 접근은 self.key_name 으로 접근함. 
            즉, self.PB_New 로 접근함.
        """
        return {
            '차량정보':  {'title': '차량정보', 
                        'tooltip': '차량정보',
                        'slot' : self.on_info_car,
                        'disable_not_selected': True
                        },
        }
    
    def on_info_car(self):
        if self.selected_rowNo is None or self.selected_dataObj is None :
            return
        dlg = InfoDialog_차량정보(self, self.selected_dataObj['차량번호_data'])
        dlg.exec()
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()


    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()
        self.run()
    
    def setup_table(self):
        self.view = TableView_차량관리_V2_운행관리_조회(self)
        self.model = TableModel_차량관리_V2_운행관리_조회(self.view)
        self.delegate = TableDelegate_차량관리_V2_운행관리_조회(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()

    def init_attributes(self):
        super().init_attributes()

    def init_ui(self):
        super().init_ui()

    def subscribe_gbus(self):
        super().subscribe_gbus()
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        # if hasattr(self, 'table_name') and self.table_name:
        #     self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.api_datas_changed )
            
    def unsubscribe_gbus(self):
        try:
            super().unsubscribe_gbus()
            self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        except Exception as e:
            logger.error(f"unsubscribe_gbus error: {e}")


            
    def connect_signals(self):
        """ signal 연결 """
        super().connect_signals()


    def run(self):
        if not ( hasattr(self, 'url') and self.url):
            logger.error(f"url이 없읍니다.")

        if not ( hasattr(self, 'table_name') and self.table_name):
            logger.error(f"table_name이 없읍니다.")

        super().run()

