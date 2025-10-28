from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
import sys

class DictTableSelectorDialog(QDialog):
    def __init__(self, parent=None, datas: list[dict]=[], attrNames: list[str]=[]):
        super().__init__(parent)
        self.setWindowTitle("항목 선택")
        self.setMinimumSize(600, 1200)

        self.datas = datas
        self.attrNames = attrNames
        self.selected_data = None

        self.UI()

    def UI(self):
        layout = QVBoxLayout(self)
        #### button 삽입
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        self.button_select = QPushButton("선택", self)
        self.button_select.clicked.connect(self.accept)
        self.button_select.setEnabled(False)
        hlayout.addWidget(self.button_select)
        layout.addLayout(hlayout)

        # 테이블 설정
        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.datas))
        self.table.setColumnCount(len(self.attrNames))
        self.table.setHorizontalHeaderLabels(self.attrNames)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 테이블에 데이터 삽입
        for row, item in enumerate(self.datas):
            for col, key in enumerate(self.attrNames):
                value = str(item.get(key, ''))
                self.table.setItem(row, col, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 행 선택 시 원본 dict 저장
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.table)
        self.setLayout(layout)


    def on_selection_changed(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.selected_data = self.datas[selected_row]
            self.button_select.setEnabled(True)

    def get_selected(self):
        return self.selected_data
