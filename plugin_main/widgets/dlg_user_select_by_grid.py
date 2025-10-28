from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from modules.common_import_v3 import *
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


from modules.PyQt.compoent_v2.imageViewer.lb_with_qnetwork import Lbl_Image_with_QNetwork as Lbl_Image


DEFAULT_STYLE = """
                    border: 1px solid gray;
                    background-color: white;
                """
SELECTED_STYLE = """
                    border: 1px solid blue;
                    background-color: lightgreen;
                """

class Wid_Container_ImageViewer(QWidget):
    def __init__(self, parent:QWidget):
        super().__init__(parent)
        self.setMinimumWidth( 64*5 +20 )
        self.setStyleSheet(DEFAULT_STYLE)




class HeaderCell(QLabel):
    def __init__(self, parent:QWidget, header:str):
        super().__init__(parent)
        self.header = header
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            background-color: black;
            color: white;
            font-weight: bold;
            border: 1px solid gray;
        """)
        self.setFixedHeight(30)  # 고정 height
        self.setText(header if header else "")

class BodyCell(QLabel):
    def __init__(self, parent:QWidget, data:str, row:int, col:int, **kwargs):
        super().__init__(parent)
        self.data = data
        self.row = row
        self.col = col

        self.setStyleSheet( DEFAULT_STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(30)  # 고정 height
        self.setText(str(data) if data else "")

        self.parent_table = self.get_parent_table()
        if self.parent_table is None:
            print (f"parent_table is None")

    def get_parent_table(self) -> 'GridTable':
        wid_parent = self.parent()
        max_depth = 5
        while wid_parent :
            if isinstance( wid_parent, GridTable):
                if getattr(wid_parent, 'is_parent_table', False):
                    return wid_parent
            wid_parent = wid_parent.parent()
            max_depth -= 1
            if max_depth <= 0:
                break
        return None
    
    def mousePressEvent(self, event):
        if self.parent_table is None:
            print (f"parent_table is None")
            return
        # 부모(GridTable)에게 선택 알림
        self.parent_table.select_row(self.row, self.col)

# ----------------------------
# Model: 데이터 + widget factory
# ----------------------------
class Grid_Base_Model(QAbstractTableModel):

    def __init__(self, parent:QWidget , data:list[dict] , headers:list[str]=None):
        super().__init__(parent)
        
        self._data = data  or [] # list of dict
        self._headers = headers or list(data[0].keys()) if data else []

        print (f"Grid_Base_Model: {len(self._data)} {self._headers} ")
        if len(self._data) > 0:
            print (f"Grid_Base_Model: {self._data[0]}")
        print (f"Grid_Base_Model: {self.rowCount()} {self.columnCount()}")

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
        return None

    def data(self, row:int, col:int):
        """Widget factory: 해당 cell에 들어갈 widget 반환"""
        item = self._data[row]

        
        if self._headers[col] in ["images"]:
            # 분석용 이미지 여러개
            container = Wid_Container_ImageViewer(self.parent())


            layout = Custom_Grid(container)
            widgets = [ Lbl_Image( container, 
                                url=face_db_dict.get("image", ""), 
                                min_size=(64,64)
                                )
                        for face_db_dict in item.get("images", []) ]
            layout.set_widgets(widgets)
            # layout.setContentsMargins(0, 0, 0, 0)
            # layout.setSpacing(2)
            # for i, face_db_dict in enumerate(item.get("images", [])):
            #     lbl = Lbl_Image( container, 
            #                     url=face_db_dict.get("image", ""), 
            #                     fixed_size=(64,64)
            #                     )
            #     layout.addWidget(lbl, i // 5, i % 5)  # 5개씩 한 줄
            return container

        elif self._headers[col] in ["representative_image"]:
            return Lbl_Image(self.parent(), 
                            url=item.get("representative_image", ""), 
                            min_size=(160,160))
        
        else :
            data = item.get( self._headers[col], "unknown")
            return BodyCell(self.parent(), 
                            data=str(data), row=row, col=col,
                            item=item
                            )
        
 
    def set_data(self, data:list[dict]):
        self._data = data
        if len(data) == 0:
            top_left = bottom_right = QModelIndex()
        else:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(data)-1, self.columnCount()-1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def set_headers(self, headers:list[str]):
        self._headers = headers
        self.layoutChanged.emit()

    # 데이터 조작
    def add_row(self, item: dict):
        self._data.append(item)

    def remove_row(self, index: int):
        if 0 <= index < len(self._data):
            self._data.pop(index)


# ----------------------------
# GridTable: QGridLayout + scroll + dynamic update
# ----------------------------
class GridTable(QWidget):
    selection_changed = pyqtSignal(int, dict) ### rowNo 및 선택된 데이터


    def __init__(self, parent:QWidget=None, data:list[dict]=None):
        super().__init__(parent)
        self.is_parent_table = True
        self.data = data
        self.model = None
        self.selected_row = None
        self.rows_widgets: dict[int, list[QWidget]] = {}
        self.is_setup_ui_finished = False

        self.setup_ui()
        self.create_model()

    def create_model(self):
        # headers =  ['id', 'user_성명', 'user_직책', 'user_직급', '기본조직1', '기본조직2', '기본조직3', 'is_active', ]
        self.model = Grid_Base_Model(self, data=self.data )
        self.model.dataChanged.connect(self.update_grid)
        self.model.layoutChanged.connect(self.update_grid)

        self.model.layoutChanged.emit()


    def set_data(self, data:list[dict]):
        self.data = data
        self.model.set_data(data)
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(5)

        # scroll area
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(5)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        # control buttons
        self.btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Row")
        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove = QPushButton("Remove Last Row")
        self.btn_remove.clicked.connect(self.remove_last_row)
        self.btn_layout.addWidget(self.btn_add)
        self.btn_layout.addWidget(self.btn_remove)
        self.main_layout.addLayout(self.btn_layout)

        self.is_setup_ui_finished = True


    def clear_grid(self):
        """기존 grid widget 모두 제거"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def update_grid(self):
        """모델 기반으로 grid 재구성"""
        self.clear_grid()
        # header
        for col in range(self.model.columnCount()):
            lbl = HeaderCell( self.parent(), header= self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
            self.grid_layout.addWidget(lbl, 0, col)

        # data
        for row in range(self.model.rowCount()):
            self.rows_widgets[row] = []
            max_height = 0

            # 먼저 row 위젯 생성
            for col in range(self.model.columnCount()):
                widget = self.model.data(row, col)
                if widget:
                    self.rows_widgets[row].append(widget)
                    max_height = max(max_height, widget.sizeHint().height())

            # row 높이 맞추기
            for col, widget in enumerate(self.rows_widgets[row]):
                widget.setFixedHeight(max_height)
                self.grid_layout.addWidget(widget, row+1, col)

            
            # row 높이 강제 (tableview 느낌)                
            self.grid_layout.setRowMinimumHeight(row+1, max_height)
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def select_row(self, row:int, col:int):
        print (f"select_row: {row} {col} ")
        selected_CLS = ( BodyCell, Lbl_Image ) ## isinstance() arg 2 must be a type, a tuple of types, or a union

        # 이전 선택 row 원래 색으로 복원
        if self.selected_row is not None and self.selected_row in self.rows_widgets:
            for w in self.rows_widgets[self.selected_row]:
                if isinstance(w, selected_CLS):
                    w.setStyleSheet(DEFAULT_STYLE)

        # 새 row 선택
        if row in self.rows_widgets:
            for w in self.rows_widgets[row]:
                if isinstance(w, selected_CLS):
                    w.setStyleSheet( SELECTED_STYLE)
        self.selected_row = row
        self.selection_changed.emit(self.selected_row, self.model._data[self.selected_row])

    # ----------------------------
    # Example: 동적 추가/삭제
    # ----------------------------
    def add_row(self):
        # 테스트용 더미
        idx = self.model.rowCount() + 1
        self.model.add_row({
            "rep_image":"rep1.png",
            "analysis_images":["a1.png","a2.png","a3.png"]
        })
        self.update_grid()

    def remove_last_row(self):
        if self.model.rowCount() > 0:
            self.model.remove_row(self.model.rowCount()-1)
            self.update_grid()


class Dlg_User_Select_By_Grid(QDialog):
    def __init__(self, parent:QWidget, data:list[dict]=None):
        super().__init__(parent)
        self.setMinimumSize(1200, 800)
        self.data = data
        self.selected_row = None
        self.selected_data = None

        self.setup_ui()

    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(5)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        self.btn_ok = QPushButton("선택")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.on_ok_button_clicked)
        self.btn_layout.addWidget(self.btn_ok)
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_layout.addWidget(self.btn_cancel)
        self.main_layout.addLayout(self.btn_layout)

        self.grid_table = GridTable(self, data=self.data)
        self.main_layout.addWidget(self.grid_table)

        self.grid_table.selection_changed.connect(self.on_selection_changed)

    def on_ok_button_clicked(self):
        print (f"on_ok_button_clicked")
        print (f"selected_row: {self.grid_table.selected_row}")
        print (f"selected_data : {self.grid_table.model._data[self.grid_table.selected_row]}")
        # self.accept()
    
    def on_selection_changed(self, row:int, data:dict):
        self.selected_row = row
        self.selected_data = data
        print (f"on_selection_changed: {row} {data}")
        self.btn_ok.setEnabled(True)

    def get_selected_data(self) -> dict:
        return self.selected_data

    def update_grid(self):
        self.grid_table.update_grid()
        
    
    def set_model(self, model: Grid_Base_Model):
        self.grid_table.set_model(model)
        

# ----------------------------
# Run example
# ----------------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    sample_data = [
        {
            "id": 1,
            "user_id": 10,
            "user_name": "admin",
            "is_face_registered": True,
            "rep_image":"/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/person2.jpg", 
            "analysis_images":[
                "/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/augmented/admin_admin/face_0LFIPR9.jpg",
                "/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/augmented/admin_admin/face_2rjVywm_dark.jpg",
                "/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/augmented/admin_admin/face_2rjVywm_rot15.jpg"
                ]
        
        
        },
        {
            "id": 2,
            "user_id": 20,
            "user_name": "test-user",
            "is_face_registered": False,
            "rep_image":"/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/person3.jpg", 
            "analysis_images":[
                "/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/admin_admin/face_yJ2WUyT_bright.jpg",
                "/home/kkt/development/proj/intranet_sh/shapi/media/ai/faces/admin_admin/face_yJ2WUyT_dark.jpg"
                ]},
    ]


    window = GridTable()
    model = Grid_Base_Model(window, sample_data)
    window.set_model(model)
    window.resize(800,600)
    window.show()
    sys.exit(app.exec())