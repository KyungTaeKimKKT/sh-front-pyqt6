from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class SearchDialog(QDialog):
    def __init__(self, parent=None, search_callback=None):
        super().__init__(parent)
        self.setWindowTitle("검색")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.search_callback = search_callback

        layout = QVBoxLayout(self)
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("검색어 입력: Enter가능 ( 미입력시 전체 선택됨 )")
        layout.addWidget(self.line_edit)

        button_layout = QHBoxLayout()
        btn_ok = QPushButton("검색")
        btn_cancel = QPushButton("취소")
        button_layout.addWidget(btn_ok)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)

        btn_ok.clicked.connect(self.do_search)
        btn_cancel.clicked.connect(self.reject)
        self.line_edit.returnPressed.connect(self.do_search)

    def do_search(self):
        keyword = self.line_edit.text()
        if self.search_callback:
            self.search_callback(keyword)
        self.accept()


class Mixin_Table_View:


    def mixin_open_search_dialog(self):
        dlg = SearchDialog(self, self.mixin_filter_rows)
        dlg.exec()

    def mixin_filter_rows(self, keyword: str):
        if not hasattr(self, 'setRowHidden'):
            raise TypeError("Mixin_Table_View는 QTableView와 함께 사용되어야 합니다.")
        
        model:QAbstractTableModel = self.model()
        if not model:
            return

        for row in range(model.rowCount()):
            # 검색어가 없으면 모두 표시
            if not keyword:
                self.setRowHidden(row, False)
                continue

            match_found = False
            for col in range(model.columnCount()):
                index = model.index(row, col)
                data = model.data(index, Qt.ItemDataRole.DisplayRole)
                if keyword in str(data).lower():
                    match_found = True
                    break

            self.setRowHidden(row, not match_found)

