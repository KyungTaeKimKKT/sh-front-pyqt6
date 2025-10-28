from modules.common_import import *

class SliderEditor(QWidget):
    valueChanged = pyqtSignal(int)  # 슬라이더 내부 시그널

    def __init__(self, step=20, max_score=5.0, parent=None):
        super().__init__(parent)
        self.환산 = int(step / max_score)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(step)
        self.slider.setSingleStep(1)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.label = QLabel("0.0")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.valueChanged.connect(self._on_value_changed)
        self.setStyleSheet("background-color: lightyellow;")



    def _on_value_changed(self, val):
        float_val = val / self.환산
        self.label.setText(f"{float_val:.1f}")
        self.valueChanged.emit(val)

    def set_value(self, float_val: float):
        self.slider.setValue(int(float_val * self.환산))

    def get_value(self) -> float:
        return self.slider.value() / self.환산
    

class 특별평가TableModel(QAbstractTableModel):
    def __init__(self, data: list[dict], parent=None):
        super().__init__(parent)
        self.headers = ['구분', '성과', '가중치', '평가점수']
        self._data = data
        self.is_submit = False
    def set_data(self, data: list[dict]):
        if not isinstance(data, list):
            raise TypeError("data must be a list of dicts")
        self._data = data
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        key = self.headers[col]
        item = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return item.get(key, "")

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole:
            key = self.headers[index.column()]
            self._data[index.row()][key] = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
            return True
        return False
    
    def set_Editable(self, is_submit:bool):
        self.is_submit = is_submit
        self.layoutChanged.emit()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if self.is_submit:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        col = index.column()
        if col == 7:  # 등록일
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def insertRow(self, position: int, parent=QModelIndex()) -> bool:
        self.beginInsertRows(parent, position, position)
        new_row = {
            'id': -1,
            '구분': '',
            '성과': '',
            '가중치': 0,
            '평가점수': 0.0,
            '등록일': QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
            '특별평가_fk': self._data[0].get('특별평가_fk'),
        }
        self._data.insert(position, new_row)
        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent=QModelIndex()) -> bool:
        if row < 0 or row >= len(self._data):
            return False
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        return True

class TextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.model().is_submit:
            return None
        editor = QPlainTextEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setPlainText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SpinBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.model().is_submit:
            return None
        spin = QSpinBox(parent)
        spin.setRange(0, 100)  # 예시 범위
        return spin

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setValue(int(value) if value else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SpinDoubleBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.model().is_submit:
            return None
        spin = QDoubleSpinBox(parent)
        spin.setRange(0, 5.0)  # 예시 범위
        return spin

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setValue(int(value) if value else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SliderDelegate(QStyledItemDelegate):
    valueChanged = pyqtSignal(float, QModelIndex)

    MAX_STEP = 50
    MAX_SCORE = 5.0
    환산 = int(MAX_STEP / MAX_SCORE)

    COLUMN_평가점수 = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slider = None
        self._current_index = None

    def createEditor(self, parent, option, index):
        # editor 직접 생성 안함
        return None

    def editorEvent(self, event, model, option, index):
        if self.hide_slider(index):
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            # 이미 슬라이더가 있으면 이전 것은 숨김
            if self._slider:
                self._slider.hide()

            # 슬라이더 생성 또는 재사용
            if not self._slider:
                self._slider = SliderEditor(
                    parent=option.widget.window(),
                    step=self.MAX_STEP,
                    max_score=self.MAX_SCORE
                    )  # 최상위 윈도우로 부모 지정
                self._slider.valueChanged.connect(lambda val: self.on_slider_value_changed(val, self._current_index, model))

            # 현재 클릭한 인덱스 저장
            self._current_index = index

            # 슬라이더 크기와 위치 지정
            slider_width = 120
            slider_height = option.rect.height()
            x = option.rect.right() + 5  # 오른쪽 5px 띄움
            y = option.rect.top()

            # option.widget은 QTableView일 가능성이 높으므로
            # 절대좌표 변환 필요 (mapToGlobal 등)
            table = option.widget
            global_pos = table.viewport().mapToGlobal(option.rect.topRight())
            # 슬라이더 부모도 윈도우라서 global_pos -> 윈도우 좌표 변환
            window_pos = self._slider.parent().mapFromGlobal(global_pos)

            self._slider.setGeometry(window_pos.x() + 5, window_pos.y(), slider_width, slider_height)
            self._slider.show()
            self._slider.raise_()

            # 현재 값 세팅
            current_value = model.data(index, Qt.ItemDataRole.EditRole)
            if current_value is None:
                current_value = 0.0
            self._slider.set_value(float(current_value))

            self._slider.setFocus()

            return True
        return False

    def on_slider_value_changed(self, value, index, model):
        value = value / self.환산
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        self.valueChanged.emit(value, index)

    def hide_slider(self, index:QModelIndex):
        if index.column() != self.COLUMN_평가점수:
            # 다른 컬럼 클릭 시 슬라이더 숨기기
            if self._slider:
                self._slider.hide()
                self._current_index = None
        return index.column() != self.COLUMN_평가점수

class 구분DelegateDialog(QDialog):
    def __init__(self, parent=None, default_options=None):
        super().__init__(parent)
        self.setWindowTitle("구분 선택")
        self.setModal(True)

        self.selected_value = None
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        if default_options is None:
            default_options = ['품질', '제품 생산성', '사무 생산성']
        self.list_widget.addItems(default_options)
        layout.addWidget(self.list_widget)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("최대 15자까지 입력")
        self.line_edit.setMaxLength(15)  # <- 여기가 추가된 부분
        layout.addWidget(self.line_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_value(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].text()
        elif self.line_edit.text().strip():
            return self.line_edit.text().strip()[:15]
        return None

class 구분_Delegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:
        return None
        dialog = 구분DelegateDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            value = dialog.get_selected_value()
            if value:
                self.commitData.emit(parent)
                self.closeEditor.emit(parent)
                index.model().setData(index, value, Qt.ItemDataRole.EditRole)
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        # Optional: no data needs to be pushed into dialog
        pass

    def setModelData(self, editor: QWidget, model, index: QModelIndex):
        # Optional: already handled during dialog accept
        pass

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            dialog = 구분DelegateDialog(option.widget)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                value = dialog.get_selected_value()
                if value:
                    model.setData(index, value, Qt.ItemDataRole.EditRole)
            return True  # 편집기로 넘어가지 않도록 막음
        return False


class Wid_table_특별평가(QWidget):
    data_changed = pyqtSignal()

    MIN_CELL_HEIGHT = 96
    MIN_CELL_WIDTH = 120
    # 예: 각 컬럼별 최소 너비 설정
    min_column_widths = {
        0: 16*15,  # 구분
        1: 16*30,  # 성과
        2: 16*15,  # 가중치
        3: 16*5,   # 평가점수
        # 4: 16*15,  # 등록일
    }

    API_DATA_KEY = '특별평가'

    def __init__(self, parent=None, data: list[dict] = None):
        super().__init__(parent)
        self.data = data or []
        self._is_initialized = False
        self.가중치_합_flag = False
        self.평가체계_dict = None
        self.is_submit = False

        if self.data:
            self.set_api_datas(self.data)
    
    def set_api_datas(self, api_datas:list[dict], 평가체계_dict:dict=None):
        self.평가체계_dict = 평가체계_dict
        self.is_submit = 평가체계_dict['is_submit'] 
        self.data = api_datas
        self.특별평가_fk = api_datas[0].get('특별평가_fk', None)
        if not self._is_initialized:
            self.init_ui()

        self.model.set_data(api_datas)
        self.model.set_Editable( self.is_submit )

        if  self.is_submit:
            self.add_btn.setVisible(False)
            self.del_btn.setVisible(False)
            self.label_summary.setVisible(False)
            self.label_summary_value.setVisible(False)
        else:
            self.render_summary()
            self.add_btn.setVisible(True)
            self.del_btn.setVisible(True)
            self.label_summary.setVisible(True)
            self.label_summary_value.setVisible(True)

    def get_api_datas(self) -> list[dict]:
        return self.model._data

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.summary_layout = QHBoxLayout()
        self.label_summary = QLabel("가중치 합은 100 이어야 합니다.")
        self.summary_layout.addWidget(self.label_summary)
        self.label_summary_value = QLabel("")
        self.label_summary_value.setMinimumWidth( 160 )
        self.label_summary_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_layout.addWidget(self.label_summary_value)
        self.summary_layout.addStretch()
                # 버튼
        self.btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("특별성과 추가")
        self.del_btn = QPushButton("특별성과 삭제")
        # save_btn = QPushButton("저장")
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_row)
        # save_btn.clicked.connect(self.on_save_clicked)
        self.btn_layout.addWidget(self.add_btn)
        self.btn_layout.addWidget(self.del_btn)
        # btn_layout.addWidget(save_btn)
        self.summary_layout.addLayout(self.btn_layout)
        layout.addLayout(self.summary_layout)

        self.table = QTableView()
        self.model = 특별평가TableModel(self.data)
        self.table.setModel(self.model)
        self.model.dataChanged.connect(self.on_data_changed)

        # Delegate 설정
        self.구분_delegate = 구분_Delegate()
        self.table.setItemDelegateForColumn(0, self.구분_delegate)
        self.성과_delegate = TextEditDelegate()
        self.table.setItemDelegateForColumn(1, self.성과_delegate)
        self.가중치_delegate = SpinBoxDelegate()
        self.table.setItemDelegateForColumn(2, self.가중치_delegate)

        self.평가점수_delegate = SpinDoubleBoxDelegate()
        self.table.setItemDelegateForColumn(3, self.평가점수_delegate)

        # self.table.setItemDelegateForColumn(5, SpinBoxDelegate())   # 가중치
        # self.table.setItemDelegateForColumn(6, SliderDelegate())    # 평가점수

        layout.addWidget(self.table)

        self.table.setAlternatingRowColors(True)
        self.resize_to_contents()

        self._is_initialized = True

     
    def on_data_changed(self, topLeft, bottomRight, roles):
        self.render_summary()
        self.resize_to_contents()
        self.data_changed.emit()

    def render_summary(self):
        가중치_합 = sum([row.get('가중치', 0) for row in self.model._data])
        self.label_summary_value.setText(f"{가중치_합}")
        if 가중치_합 != 100:
            self.label_summary_value.setStyleSheet("color: white; background-color: red;")
            self.가중치_합_flag = False
        else:
            self.label_summary_value.setStyleSheet("color: white; background-color: green;")
            self.가중치_합_flag = True


    def resize_to_contents(self):
        if not self.table or self.model.columnCount(QModelIndex()) == 0:
            return 

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.verticalHeader().setMinimumSectionSize(self.MIN_CELL_HEIGHT)
        self.table.horizontalHeader().setMinimumSectionSize(self.MIN_CELL_WIDTH)

        header = self.table.horizontalHeader()
        for col, width in self.min_column_widths.items():
            if col < self.model.columnCount(QModelIndex()):  # 방어 코드
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                header.resizeSection(col, width)
            


    def add_row(self):
        self.model.insertRow(self.model.rowCount())
        self.resize_to_contents()

    def delete_row(self):
        selected = self.table.selectionModel().currentIndex()
        if selected.isValid():
            self.model.removeRow(selected.row())
        self.resize_to_contents()

    def on_save_clicked(self):
        if hasattr(self, 'url') and self.url:
            data = {self.API_DATA_KEY:json.dumps(self.get_api_send_data(), ensure_ascii=False)}
            logger.info(f"저장 데이터 : {data}")
            is_ok, _json = APP.API.post_json(
                 self.url, 
                 data = data,
                 headers = {'Content-Type': 'application/json'}
                 )
            if is_ok:
                Utils.generate_QMsg_Information( self.parent(), title="저장 완료", text="저장 완료", autoClose=1000)
                self.model.set_data(_json.get(f'{self.API_DATA_KEY}_api_datas', []))
                self.render_summary()
    
            else:
                Utils.generate_QMsg_critical( self.parent(), title="저장 실패", text="저장 실패")
        else:
            Utils.generate_QMsg_critical( self.parent(), title="저장 실패", text="저장 실패" )

    def get_api_send_data(self) -> list[dict]:
        send_data = []
        for row in self.model._data:
            send_data.append({
                'id': -1 if row.get('id') is None else row.get('id'),
                '구분': row.get('구분', ''),
                '성과': row.get('성과', ''),
                '가중치': int(row.get('가중치', 0)),
                '평가점수': float(row.get('평가점수', 0.0)),
                '등록일': row.get('등록일'),
                '특별평가_fk': self.특별평가_fk
            })
        return send_data
    
    def set_url(self, url:str):
        self.url = url

    # def on_score_changed(self, value, index):
    #     print("평가점수 변경:", value, index.row())
    #     self.map_id_dict[index.row()] = {'id': index.row(), '평가점수': value}


if __name__ == '__main__':
    특별평가_api_datas= [{'id': 181, '구분': '', '성과': '', '가중치': 0, '평가점수': 0.0, '등록일': '2025-05-28T13:43:52.595051', '특별평가_fk': 353}]

    app = QApplication([])
    main_window = QMainWindow()
    main_window.setMinimumSize(1800, 800)
    wid_table = Wid_table_특별평가(main_window, 특별평가_api_datas)
    main_window.setCentralWidget(wid_table)
    main_window.show()
    app.exec()