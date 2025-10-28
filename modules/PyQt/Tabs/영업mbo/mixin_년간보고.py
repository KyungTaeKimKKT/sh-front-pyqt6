from __future__ import annotations
from modules.common_import_v2 import *

DEFAULT_URL_YEAR = '영업mbo/get-매출년도list/' 

class YearSearchMixin:
    def mixin_create_year_search(self) -> QWidget:
        wid_search = QWidget(self)		
        wid_search.setFixedHeight(60)
        wid_search.setStyleSheet("background-color: #4caf50;")
        h_layout = QHBoxLayout(wid_search)

        h_layout.addWidget(QLabel('매출년도 선택: '))

        self.url_year = self.lazy_attrs.get('url_year', DEFAULT_URL_YEAR)
        self.cb_selected_year = Custom_Combo_with_fetch(self, url=self.url_year)
        self.cb_selected_year.setFixedSize(100, 30)
        self.cb_selected_year.run(self.url_year)
        h_layout.addWidget(self.cb_selected_year)

        h_layout.addStretch()

        self.pb_query = CustomPushButton(wid_search, text='조회')
        h_layout.addWidget(self.pb_query)
        self.pb_query.clicked.connect(
            lambda: self.slot_search_for({'매출_year': self.cb_selected_year.currentText()})
        )

        return wid_search