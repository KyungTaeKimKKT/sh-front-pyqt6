from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6 import sip
import numpy as np

import math
from enum import Enum


class Type_Cols(Enum):
    responsive = 'responsive'
    square = 'square'
    fixed = 'fixed'
    none = ''

class Custom_Grid(QGridLayout):
    """ 참조 : QGridLayout 은 자체적으로 resizeEvent 를 받지 않아요.
        따라서, 부모 위젯에서 resizeEvent 를 받아서 처리해야 해요.
    """
    def __init__(self, parent=None,  widgets:list[QWidget]=[], **kwargs):
        super().__init__(parent)
        self.widgets = widgets
        self.kwargs = {"item_size": 100, **kwargs}
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)


    def set_widgets(self, widgets:list[QWidget]):
        if self.widgets:
            for w in self.widgets:
                self.remove_widget(w)
            self.widgets.clear()

        self.widgets = widgets
        self.rebuild_grid()

    def rebuild_grid(self, cols=None):
        # 삭제된 객체는 제거
        self.widgets = [w for w in self.widgets if not sip.isdeleted(w)]
        self.clear_widgets()
        cols = self.calculate_cols()

        for i, widget in enumerate(self.widgets):
            row = i // cols
            col = i % cols
            self.addWidget(widget, row, col)

    def calculate_cols(self, _type:Type_Cols=Type_Cols.none):        
        if _type == Type_Cols.none:
            _type = self.kwargs.get('cols_type', Type_Cols.responsive)
        match _type:
            case Type_Cols.responsive:
                return self._calculate_cols_responsive()
            case Type_Cols.square:
                return self._calculate_cols_square()
            case Type_Cols.fixed:
                return self.kwargs.get('fixed_cols', 2)
            case _:
                return 1

    def _calculate_cols_responsive(self):
        print (f"calculate_cols_responsive: {len(self.widgets)}")
        item_size = self.widgets[0].sizeHint().width() if (self.widgets and self.widgets[0]) else self.kwargs["item_size"]
        parent = self.parentWidget()
        width = parent.width() if parent is not None else item_size * 4
        print (f"calculate_cols_responsive: {self.parentWidget()} {parent.width()} {width} {item_size} {width // item_size}")
        return max(1, width // item_size)

    def _calculate_cols_square(self):
        return math.ceil(math.sqrt(len(self.widgets)))

    def clear_widgets(self):
        """ 레이아웃만 비우고 widgets 리스트는 유지 """
        for i in reversed(range(self.count())):
            item = self.takeAt(i)
            w = item.widget()
            if w is not None and not sip.isdeleted(w):
                w.setParent(None)

    def add_widget(self, widget:QWidget):
        self.widgets.append(widget)
        self.rebuild_grid()

    def remove_widget(self, widget:QWidget):
        if widget in self.widgets:
            self.widgets.remove(widget)
            if not sip.isdeleted(widget):
                widget.setParent(None)
                widget.deleteLater()
            self.rebuild_grid()

class Container_LB_Pixmap(QWidget):
    def __init__(self, parent=None, image_paths:list[str]=[],  **kwargs):
        super().__init__(parent)
        self.grid = Custom_Grid(self)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.image_paths = image_paths


    def resizeEvent(self, event):
        self.grid.rebuild_grid()
        super().resizeEvent(event)

    # ✅ 동적 추가
    def add_widget(self, widget:QWidget):
        self.grid.add_widget(widget)

    # ✅ 동적 삭제
    def remove_widget(self, widget:QWidget):
        self.grid.remove_widget(widget)

    def clear_layout(self, layout=None):
        if layout is None:
            layout = self.grid
        self.grid.clear_layout(layout)
