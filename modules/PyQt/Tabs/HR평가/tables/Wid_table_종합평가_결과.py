from modules.common_import import *

from modules.PyQt.compoent_v2.table.mixin_table_view import Mixin_Table_View

DEFAULT_미제출_Color = QColor("#FFA000")
DEFAULT_제출_Color = QColor("#388E3C")

class 종합평가TableModel(QAbstractTableModel):
    header_split_char = '차:'

    def __init__(self, data: list[dict], parent=None):
        super().__init__(parent)
        self.api_data : list[dict] = []
        self._data:list[dict] = []
        self.set_data(data)
        self.headers = None
        self.map_평가차수_to_name = {
            0: '본인',
            1: '1차',
            2: '2차',
            3: '3차',
        }
        self._list_차수별 = ['평가자', 'is_submit', '역량', '성과', '특별','종합평가']
        self.get_headers()

    @property
    def bg_color_미제출 (self) -> QColor:
        return DEFAULT_미제출_Color
    
    @bg_color_미제출.setter
    def bg_color_미제출 (self, value:QColor):
        global DEFAULT_미제출_Color
        DEFAULT_미제출_Color = value

    @property
    def bg_color_제출 (self) -> QColor:
        return DEFAULT_제출_Color
    
    @bg_color_제출.setter
    def bg_color_제출 (self, value:QColor):
        global DEFAULT_제출_Color
        DEFAULT_제출_Color = value
    

    def get_headers(self):
        if self.headers is not None and self.headers:
            return self.headers
        
       
        headers = ['기본조직1','피평가자']
        api_data_dict = self._data[3]

        for 차수, _차수별_평가결과_dict in api_data_dict.items():
            if str(차수).isdigit():
                for key_name in self._list_차수별:                
                    headers.append(f'{차수}{self.header_split_char}{key_name}')
        # logger.info(f"headers: {headers}")
        logger.info(f"headers: {headers}")
        headers.append('최종종합평가')
        self.headers = headers
        return headers

    def set_data(self, data: dict[str,dict]):
        """ 받은 api data를 처리하여 테이블에 표시할 수 있도록 변환 """
        if not isinstance(data, dict):
            raise TypeError("data must be a list of dicts")
        self.api_data:dict[int,dict] = data.get('map_피평가자_to_결과', {})
        self.평가설정_data:dict = data.get('평가설정_data', {})
        if not ( isinstance(self.api_data, dict) and isinstance(self.평가설정_data, dict) ):
            raise TypeError("api_data and 평가설정_data must be a dict")

        self._data = copy.deepcopy([ obj for obj in self.api_data.values()])
        self.layoutChanged.emit()
        print(f"self._data: {self._data}")

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        headerName:str = self.get_headers()[col]
        item = self._data[row]

        if role == Qt.ItemDataRole.UserRole:
            return item
        
        if role == Qt.ItemDataRole.UserRole+1:
            차수 = int(headerName.split(self.header_split_char)[0])
            평가체계_fk_data = item.get(str(차수)).get('평가체계_fk_data')
            return 평가체계_fk_data

        if role == Qt.ItemDataRole.DisplayRole :
            피평가자_id =item.get('0').get('평가체계_fk_data').get('피평가자')
            피평가자_info = INFO.USER_MAP_ID_TO_USER.get(피평가자_id, {})
            match headerName:
                case '피평가자':
                    return 피평가자_info.get('user_성명')
                case '기본조직1':
                    return 피평가자_info.get('기본조직1')
                case '최종종합평가':
                    return f"{item.get('최종종합평가'):.2f}"
                
                case _ if any(name in headerName for name in self._list_차수별):
                    차수 = int(headerName.split(self.header_split_char)[0])
                    listName = headerName.split(self.header_split_char)[1]
                    if listName == '평가자':
                        평가자_id = item.get(str(차수)).get('평가체계_fk_data').get('평가자')
                        평가자_info = INFO.USER_MAP_ID_TO_USER.get(평가자_id, {})
                        return 평가자_info.get('user_성명')
                    match listName:
                        case 'is_submit':
                            _is_submit = item.get(str(차수)).get('평가체계_fk_data').get(listName)
                            return '제출' if _is_submit else '미제출'
                        case '역량'|'성과'|'특별':
                            keyName = f"{listName}평가"
                            return f"{item.get(str(차수)).get(keyName).get('평가점수'):.2f}"
                        case '종합평가':
                            return f"{item.get(str(차수)).get('평가체계_fk_data').get('종합평가'):.2f}"

                case _:
                    return item.get(headerName, "")
                
        if role == Qt.ItemDataRole.EditRole:
            if 'is_submit' in headerName:
                차수 = int(headerName.split(self.header_split_char)[0])
                return bool(item.get(str(차수)).get('평가체계_fk_data').get('is_submit'))
                
        if role == Qt.ItemDataRole.BackgroundRole:
            try:
                차수 = int(headerName.split(self.header_split_char)[0])
                _is_submit = item.get(str(차수)).get('평가체계_fk_data').get('is_submit')
                if _is_submit:
                    return self.bg_color_제출
                return self.bg_color_미제출
            except Exception as e:                
                return QColor(Qt.GlobalColor.white)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole:
            headerName = self.get_headers()[index.column()]
            차수 = int(headerName.split(self.header_split_char)[0])
            keyName = headerName.split(self.header_split_char)[1]
            평가체계_fk_data = self.data(index, Qt.ItemDataRole.UserRole+1)
            if 평가체계_fk_data:
                평가체계_fk_data[keyName] = value
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
                return True
        return False

    def flags(self, index):
        EDIT_FLAG = Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        NO_EDIT_FLAG = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if self.is_submit_editable(index):
            return EDIT_FLAG

        return NO_EDIT_FLAG
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """ display role 기준으로 정렬 """
        if not self._data:
            return
        super().mixin_sort_by_display_role(column, order)
    
    def is_submit_editable(self, index:QModelIndex) -> bool:
        """ 제출 해제만 editable"""
        headerName = self.get_headers()[index.column()]
        if 'is_submit' in headerName:
            return True
            평가체계_fk_data = self.data(index, Qt.ItemDataRole.UserRole+1)
            return 평가체계_fk_data.get('is_submit')
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.get_headers()[section]
        return None

    def insertRow(self, position: int, parent=QModelIndex()) -> bool:
        self.beginInsertRows(parent, position, position)
        new_row = {
            'id': -1,
            '구분': '',
            '성과': '',
            '가중치': 0,
            '평가점수': 0.0,
            '등록일': QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
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
    
    def get_summary(self) -> dict:
        차수별_제출현황: dict = {}
        for 차수 in range(self.평가설정_data.get('총평가차수') +1 ):
            제외_count = 0
            is_submit_count = 0
            미제출자_names: list[str] = []
            
            is_submit_headerName = f"{차수}{self.header_split_char}is_submit"
            is_submit_colNo = self.get_headers().index(is_submit_headerName)

            평가자_headerName = f"{차수}{self.header_split_char}평가자"
            평가자_colNo = self.get_headers().index(평가자_headerName)

            피평가자_headerName = f"피평가자"
            피평가자_colNo = self.get_headers().index(피평가자_headerName)

            for row in range(self.rowCount()):
                is_submit = self.data(self.index(row, is_submit_colNo), Qt.ItemDataRole.EditRole)
                if is_submit:
                    is_submit_count += 1
                else:
                    평가자_name = self.data(self.index(row, 평가자_colNo), Qt.ItemDataRole.DisplayRole)
                    if 차수 == 0 :
                        미제출자_names.append(평가자_name)
                    else:
                        피평가자_name = self.data(self.index(row, 피평가자_colNo), Qt.ItemDataRole.DisplayRole)
                        if 피평가자_name == 평가자_name:
                            제외_count += 1
                        else:
                            미제출자_names.append(평가자_name)    
                        

            차수별_제출현황[차수] = {
                'is_submit_count': is_submit_count,
                'no_submit_count': self.rowCount() - is_submit_count - 제외_count,
                '미제출자_names': list(set(미제출자_names))
            }

        logger.info(f"차수별_제출현황: {차수별_제출현황}")
        return 차수별_제출현황
    
    def data_to_excel_only_visible_columns(self):
        """ 데이터를 엑셀로 저장 """
        import pandas as pd

        path, _ = QFileDialog.getSaveFileName(
                None, "엑셀로 저장", "", "Excel Files (*.xlsx)"
            )
        if not path:
            return

        # 🔽 확장자 누락 시 추가
        if not path.endswith(".xlsx"):
            path += ".xlsx"
        logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export -> {path}")

        # Step 2: 숨겨지지 않은 열 인덱스 수집
        view = self.parent()
        if isinstance(view, QTableView):
            visible_columns = [
                col for col in range(self.columnCount())
                if not view.isColumnHidden(col)
            ]
        else:
            raise ValueError("view is not QTableView")
        # Step 3: 헤더 추출
        headers = [
            self.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            for col in visible_columns
        ]

        # Step 4: 데이터 추출
        data = []
        for row in range(self.rowCount()):
            row_data = [
                self.data(self.index(row, col), Qt.ItemDataRole.DisplayRole)
                for col in visible_columns
            ]
            data.append(row_data)

        # Step 5: DataFrame 생성 및 Excel 저장
        df = pd.DataFrame(data, columns=headers)
        try:
            df.to_excel(path, index=False)
            Utils.generate_QMsg_Information( None, title="엑셀 저장 성공", text=f" 파일 경로 및 이름: {path} <br>로 저장되었읍니다.!!!", autoClose=1000)

        except Exception as e:
            Utils.generate_QMsg_critical( None, title="엑셀 저장 실패", text=f" 파일 경로 및 이름: {path} <br>로 저장 실패!!!")
            logger.debug(f"{self.__class__.__name__} : on_request_excel_export: to_excel_export")
    

    def get_graph_data(self) -> dict[int,float]:
        """ { int : float 형태로 } { 피평가자_id: 최종종합평가 } return"""
        self.graph_data = {
            obj.get('0').get('평가체계_fk_data').get('피평가자') : obj['최종종합평가']
            for  obj in self._data

        }
        return self.graph_data

class 종합평가TableView(QTableView, Mixin_Table_View ):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortingEnabled(True)  # 🔹 정렬 가능하게 설정

    def keyPressEvent(self, event: QKeyEvent):           
        # Ctrl+F 누르면 검색 창 오픈
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            self.mixin_open_search_dialog()
        else:
            super().keyPressEvent(event)




class Dialog_종합평가_제출취소(QDialog):
    def __init__(self, parent=None, radio_group_config:dict[int,str]=None):
        super().__init__(parent)
        self.radio_group_config = radio_group_config
        if self.radio_group_config:
            self.UI()

    def UI(self):
        layout = QVBoxLayout(self)

        # 배타적 선택을 위한 라디오 버튼 그룹
        self.radio_group = QButtonGroup(self)
        for id, labelName in self.radio_group_config.items():
            setattr(self, f"radio_{labelName}", QRadioButton(labelName))
            radio:QRadioButton = getattr(self, f"radio_{labelName}")
            self.radio_group.addButton(radio, id=id)

            # 기본 선택값 (선택 안 하려면 생략)
            if id == 1:
                radio.setChecked(True)
            layout.addWidget(radio)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        self.PB_저장 = QPushButton("저장")
        self.PB_저장.clicked.connect(self.on_save_clicked)
        h_layout.addWidget(self.PB_저장)
        layout.addLayout(h_layout)

    def on_save_clicked(self):
        selected_action_id = self.get_selected_action()
        self.accept()

    def get_selected_action(self) -> Optional[int]:
        """
        선택된 라디오 버튼의 id를 반환
        :return: 1 | 2 | None
        """
        checked_id = self.radio_group.checkedId()
        if checked_id:
            return checked_id
        return None


class 종합평가TableDelegate(QStyledItemDelegate):

    radio_group_config:dict[int,str] = {
        1: '제출취소',
        2: '초기화 및 제출취소',
    }
    url_제출취소_dict = {
        1: 'action_제출취소',
        2: 'action_초기화_및_제출취소',
    }

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return None

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseButtonDblClick and model.is_submit_editable(index):
            평가체계_fk_data = index.model().data(index, Qt.ItemDataRole.UserRole+1)
            
            dlg = Dialog_종합평가_제출취소(self.parent(), radio_group_config=self.radio_group_config)
            if dlg.exec():
                sendData = copy.deepcopy(평가체계_fk_data)
                sendData['is_submit'] = False
                sendData['평가점수'] = 0.0
                selected_action_id = dlg.get_selected_action()
                selected_action_name = self.radio_group_config.get(selected_action_id, '선택안됨')  
                url = f"{INFO.URL_HR평가_평가체계DB}{평가체계_fk_data.get('id')}/{self.url_제출취소_dict.get(selected_action_id, '선택안됨')}"
                _isok, _json = APP.API.getlist( url )
                if _isok:
                    model.setData(index, False, Qt.ItemDataRole.EditRole)
                else:
                    Utils.generate_QMsg_critical( self.parent(), title="저장 실패", text="저장 실패")
                    return False
            return True
        return False





class Wid_table_종합평가(QWidget):
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

        if self.data:
            self.set_api_datas(self.data)
    
    def set_api_datas(self, api_datas:list[dict]):
        self.data = api_datas

        if not self._is_initialized:
            self.init_ui()
        else:
            self.model.set_data(api_datas)
        self.render_summary()

    def get_api_datas(self) -> list[dict]:
        return self.model._data

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.summary_layout = QHBoxLayout()
        self.pb_summary = QPushButton("現 제출현황")
        self.pb_summary.clicked.connect(self.on_summary_clicked)
        self.summary_layout.addWidget(self.pb_summary)
        self.pb_graph = QPushButton("그래프")
        self.pb_graph.clicked.connect(self.on_graph_clicked)
        self.summary_layout.addWidget(self.pb_graph)

        #### 설정
        self.pb_미제출_color_picker = QPushButton("미제출 배경색")
        self.pb_미제출_color_picker.clicked.connect(self.on_not_submit_color_picker_clicked)
        self.summary_layout.addWidget(self.pb_미제출_color_picker)
        self.pb_제출_color_picker = QPushButton("제출 배경색")
        self.pb_제출_color_picker.clicked.connect(self.on_submit_color_picker_clicked)
        self.summary_layout.addWidget(self.pb_제출_color_picker)

        self.summary_layout.addStretch()
        # 버튼
        btn_layout = QHBoxLayout()
        pb_excel_download    = QPushButton("Table EXCEL Download")
        pb_excel_download.clicked.connect(self.on_excel_download_clicked)
        btn_layout.addWidget(pb_excel_download)
        self.summary_layout.addLayout(btn_layout)
        layout.addLayout(self.summary_layout)

        self.table = 종합평가TableView(self)
        self.model = 종합평가TableModel(self.data, self.table)
        self.table.setModel(self.model)
        self.table.setItemDelegate( 종합평가TableDelegate(self.table) )


        # self.table.setItemDelegateForColumn(5, SpinBoxDelegate())   # 가중치
        # self.table.setItemDelegateForColumn(6, SliderDelegate())    # 평가점수

        layout.addWidget(self.table)

        self.table.setAlternatingRowColors(True)
        self.resize_to_contents()

        self._is_initialized = True

    def on_graph_clicked(self):
        graph_data = self.model.get_graph_data()
        logger.info(f"graph_data: {graph_data}")
        from modules.PyQt.Tabs.HR평가.dialog.dlg_histogram import HistogramDialog
        dlg = HistogramDialog(parent=self, data_dict=graph_data)
        dlg.exec()

    def on_not_submit_color_picker_clicked(self):
        color = QColorDialog.getColor(self.model.bg_color_미제출, self, "미제출 색상 선택")
        if color.isValid():
            self.model.bg_color_미제출 = color
            self.model.layoutChanged.emit()

    def on_submit_color_picker_clicked(self):
        color = QColorDialog.getColor(self.model.bg_color_제출, self, "제출 색상 선택")
        if color.isValid():
            self.model.bg_color_제출 = color
            self.model.layoutChanged.emit()


    def on_excel_download_clicked(self):
        self.model.data_to_excel_only_visible_columns()

     
    def on_data_changed(self, topLeft, bottomRight, roles):
        self.render_summary()
        self.resize_to_contents()
        self.data_changed.emit()

    def on_summary_clicked(self):
        제출현황_dict = self.model.get_summary()
        logger.info(f"제출현황_dict: {제출현황_dict}")

        dlg = QDialog(self)
        dlg.setMinimumSize(1000, 800)
        dlg.setWindowTitle("제출현황")
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title_label = QLabel("차수별 제출 현황 요약")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        for 차수, 차수별_제출현황_dict in 제출현황_dict.items():
            container = QFrame()
            container.setFrameShape(QFrame.StyledPanel)
            ### padding 제외padding: 15px;
            container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 10px;  
                }
            """)

            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(10)

            # 제목
            header = QLabel(f"■ 차수 {차수} 제출현황")
            header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2a2a2a;")
            container_layout.addWidget(header)

            # 요약
            summary = QLabel(
                f"제출자 수: {차수별_제출현황_dict['is_submit_count']} 건 / "
                f"미제출자 수: {차수별_제출현황_dict['no_submit_count']} 건( {len(차수별_제출현황_dict['미제출자_names'])}명)"
            )
            summary.setStyleSheet("font-size: 14px;")
            container_layout.addWidget(summary)

            # 미제출자 리스트
            미제출자_list = 차수별_제출현황_dict['미제출자_names']
            if 미제출자_list:
                list_label = QLabel("미제출자 명단:")
                list_label.setStyleSheet("font-weight: bold;")
                container_layout.addWidget(list_label)

                list_widget = QListWidget()
                list_widget.addItems(미제출자_list)
                list_widget.setStyleSheet("background-color: #f9f9f9;")
                container_layout.addWidget(list_widget)
            else:
                container_layout.addWidget(QLabel("모두 제출 완료"))

            layout.addWidget(container)

        dlg.exec()

    def render_summary(self):
        return 


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
        # self.table.verticalHeader().setMinimumSectionSize(self.MIN_CELL_HEIGHT)
        # self.table.horizontalHeader().setMinimumSectionSize(self.MIN_CELL_WIDTH)

        # header = self.table.horizontalHeader()
        # for col, width in self.min_column_widths.items():
        #     if col < self.model.columnCount(QModelIndex()):  # 방어 코드
        #         header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        #         header.resizeSection(col, width)           


    def add_row(self):
        self.model.insertRow(self.model.rowCount())
        self.resize_to_contents()

    def delete_row(self):
        selected = self.table.selectionModel().currentIndex()
        if selected.isValid():
            self.model.removeRow(selected.row())
        self.resize_to_contents()

    def on_save_clicked(self):
        return 
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
    api_datas= [
{96: {'0': {'평가체계_fk_data': {'id': 10426, '차수': 0, 'is_참여': True, '평가설정_fk': 44, '평가자': 96, '피평가자': 96}, '역량평가': {'id': 344, '평가체계_fk': 10426, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': [{'id': 1429, '역량평가_fk': 344, '항목': 1, '평가점수': 0.0, '항목_data': {'id': 1, '평가설정_fk': 44, '항목': 6, '차수': 0, '항목_이름': '긍정성', '구분': '공통역량', '정의': '어떤 현안(주제, 방침, 업무, 관계 등)에 대해 이해, 인정, 수용 또는  개선/극복하려는 태도나 이를 표현하는 말과 행동을 보인다.'}}, {'id': 1430, '역량평가_fk': 344, '항목': 2, '평가점수': 0.0, '항목_data': {'id': 2, '평가설정_fk': 44, '항목': 2, '차수': 0, '항목_이름': '열정', '구분': '공통역량', '정의': '적극적이고 능동적인 자세로 업무를 수행하고 자신의 분야에서 최고가 된다는 열망을 가지고 노력한다.'}}, {'id': 1431, '역량평가_fk': 344, '항목': 3, '평가점수': 0.0, '항목_data': {'id': 3, '평가설정_fk': 44, '항목': 3, '차수': 0, '항목_이름': '원칙준수', '구분': '공통역량', '정의': '자신의 편의를 위해 편법을 동원하지 않고 정해진 규정과 지침, 절차를 이해하고 이에 따라 공정하고 투명하게 업무를 처리한다.'}}, {'id': 1432, '역량평가_fk': 344, '항목': 4, '평가점수': 0.0, '항목_data': {'id': 4, '평가설정_fk': 44, '항목': 8, '차수': 0, '항목_이름': '자기조절', '구분': '공통역량', '정의': '업무로 인한 스트레스를 경험하거나 부정적인 행동을 취하고 싶은 유혹에도 불구하고 자신의 감정을 조절하고 자제할 수 있다.'}}, {'id': 1433, '역량평가_fk': 344, '항목': 5, '평가점수': 0.0, '항목_data': {'id': 5, '평가설정_fk': 44, '항목': 7, '차수': 0, '항목_이름': '주인의식', '구분': '공통역량', '정의': '높은 공동체 의식과 투철한 직업정신(윤리)를 바탕으로 조직 전체의 목표를 달성하기 위해 적극적으로 참여하고 헌신할 수 있다.'}}, {'id': 1434, '역량평가_fk': 344, '항목': 6, '평가점수': 0.0, '항목_data': {'id': 6, '평가설정_fk': 44, '항목': 4, '차수': 0, '항목_이름': '팀워크', '구분': '공통역량', '정의': '주어진 업무를 수행함에 있어 업무를 적절히 분담하고, 긴밀한 협력을 통해 주어진 과제를 완수한다'}}, {'id': 1435, '역량평가_fk': 344, '항목': 7, '평가점수': 0.0, '항목_data': {'id': 7, '평가설정_fk': 44, '항목': 5, '차수': 0, '항목_이름': '프로정신', '구분': '공통역량', '정의': '자신이 하는 일에 대한 사명감과 자부심을 가지고, 어떠한 상황에서도 최고가 되기 위하여 자신을 관리한다.'}}, {'id': 1436, '역량평가_fk': 344, '항목': 16, '평가점수': 0.0, '항목_data': {'id': 16, '평가설정_fk': 44, '항목': 10, '차수': 0, '항목_이름': '고객마인드', '구분': '직무역량(공통)', '정의': '조직의 내부 고객과 외부 고객의 요구를 만족시킬 수 있다.'}}, {'id': 1437, '역량평가_fk': 344, '항목': 17, '평가점수': 0.0, '항목_data': {'id': 17, '평가설정_fk': 44, '항목': 12, '차수': 0, '항목_이름': '분석적 사고', '구분': '직무역량(공통)', '정의': '주어진 상황/과제/문제를 보다 세부적인 단위로 분해하여 분석하고, 단계적인 방법으로 상황/과제/문제의 의미를 파악할 수 있다.'}}, {'id': 1438, '역량평가_fk': 344, '항목': 18, '평가점수': 0.0, '항목_data': {'id': 18, '평가설정_fk': 44, '항목': 15, '차수': 0, '항목_이름': '업무관리', '구분': '직무역량(공통)', '정의': '주어진 시간 내에 목표를 달성할 수 있도록 긴급성, 중요성 등을 감안하여 자신의 시간을 효율적으로 활용하는 역량'}}, {'id': 1439, '역량평가_fk': 344, '항목': 19, '평가점수': 0.0, '항목_data': {'id': 19, '평가설정_fk': 44, '항목': 14, '차수': 0, '항목_이름': '의사전달', '구분': '직무역량(공통)', '정의': '자신의 의견을 명확하게 전달하며, 자신의 견해를 확실하게 피력할 수 있다.'}}, {'id': 1440, '역량평가_fk': 344, '항목': 20, '평가점수': 0.0, '항목_data': {'id': 20, '평가설정_fk': 44, '항목': 11, '차수': 0, '항목_이름': '전략적 사고', '구분': '직무역량(공통)', '정의': '이슈 또는 문제를 명확히 인식하여 그 원인을 분석하고 최적의 대안을 도출하여 실행함으로써 바람직한 목표 수준에 도달하기 위해 노력할 수 있다.'}}, {'id': 1441, '역량평가_fk': 344, '항목': 21, '평가점수': 0.0, '항목_data': {'id': 21, '평가설정_fk': 44, '항목': 9, '차수': 0, '항목_이름': '전문지식', '구분': '직무역량(공통)', '정의': '자신의 업무와 관계된 최신 지식이나 정보를 빠르게 흡수하고 업무에 적용할 수 있다.'}}, {'id': 1442, '역량평가_fk': 344, '항목': 22, '평가점수': 0.0, '항목_data': {'id': 22, '평가설정_fk': 44, '항목': 13, '차수': 0, '항목_이름': '창의적 사고', '구분': '직무역량(공통)', '정의': '다양하고 독창적인 아이디어를 발상, 제안하고 이를 적용 가능한 아이디어로 발전시킬 수 있다.'}}]}, '성과평가': {'id': 344, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10426}, '특별평가': {'id': 344, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10426}}, '1': {'평가체계_fk_data': {'id': 10506, '차수': 1, 'is_참여': True, '평가설정_fk': 44, '평가자': 49, '피평가자': 96}, '역량평가': {'id': 421, '평가체계_fk': 10506, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': []}, '성과평가': {'id': 421, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10506}, '특별평가': {'id': 421, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10506}}}},
{10: {'0': {'평가체계_fk_data': {'id': 10428, '차수': 0, 'is_참여': True, '평가설정_fk': 44, '평가자': 10, '피평가자': 10}, '역량평가': {'id': 346, '평가체계_fk': 10428, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': [{'id': 1443, '역량평가_fk': 346, '항목': 23, '평가점수': 0.0, '항목_data': {'id': 23, '평가설정_fk': 44, '항목': 6, '차수': 1, '항목_이름': '긍정성', '구분': '공통역량', '정의': '어떤 현안(주제, 방침, 업무, 관계 등)에 대해 이해, 인정, 수용 또는  개선/극복하려는 태도나 이를 표현하는 말과 행동을 보인다.'}}, {'id': 1444, '역량평가_fk': 346, '항목': 24, '평가점수': 0.0, '항목_data': {'id': 24, '평가설정_fk': 44, '항목': 2, '차수': 1, '항목_이름': '열정', '구분': '공통역량', '정의': '적극적이고 능동적인 자세로 업무를 수행하고 자신의 분야에서 최고가 된다는 열망을 가지고 노력한다.'}}, {'id': 1445, '역량평가_fk': 346, '항목': 25, '평가점수': 0.0, '항목_data': {'id': 25, '평가설정_fk': 44, '항목': 3, '차수': 1, '항목_이름': '원칙준수', '구분': '공통역량', '정의': '자신의 편의를 위해 편법을 동원하지 않고 정해진 규정과 지침, 절차를 이해하고 이에 따라 공정하고 투명하게 업무를 처리한다.'}}, {'id': 1446, '역량평가_fk': 346, '항목': 26, '평가점수': 0.0, '항목_data': {'id': 26, '평가설정_fk': 44, '항목': 8, '차수': 1, '항목_이름': '자기조절', '구분': '공통역량', '정의': '업무로 인한 스트레스를 경험하거나 부정적인 행동을 취하고 싶은 유혹에도 불구하고 자신의 감정을 조절하고 자제할 수 있다.'}}, {'id': 1447, '역량평가_fk': 346, '항목': 27, '평가점수': 0.0, '항목_data': {'id': 27, '평가설정_fk': 44, '항목': 7, '차수': 1, '항목_이름': '주인의식', '구분': '공통역량', '정의': '높은 공동체 의식과 투철한 직업정신(윤리)를 바탕으로 조직 전체의 목표를 달성하기 위해 적극적으로 참여하고 헌신할 수 있다.'}}, {'id': 1448, '역량평가_fk': 346, '항목': 28, '평가점수': 0.0, '항목_data': {'id': 28, '평가설정_fk': 44, '항목': 4, '차수': 1, '항목_이름': '팀워크', '구분': '공통역량', '정의': '주어진 업무를 수행함에 있어 업무를 적절히 분담하고, 긴밀한 협력을 통해 주어진 과제를 완수한다'}}, {'id': 1449, '역량평가_fk': 346, '항목': 29, '평가점수': 0.0, '항목_data': {'id': 29, '평가설정_fk': 44, '항목': 5, '차수': 1, '항목_이름': '프로정신', '구분': '공통역량', '정의': '자신이 하는 일에 대한 사명감과 자부심을 가지고, 어떠한 상황에서도 최고가 되기 위하여 자신을 관리한다.'}}, {'id': 1450, '역량평가_fk': 346, '항목': 30, '평가점수': 0.0, '항목_data': {'id': 30, '평가설정_fk': 44, '항목': 19, '차수': 1, '항목_이름': '결과', '구분': '리더십역량', '정의': '일에 대한 높은 관심과 동기가 있어 매우 과업지향적으로 행동한다.'}}, {'id': 1451, '역량평가_fk': 346, '항목': 31, '평가점수': 0.0, '항목_data': {'id': 31, '평가설정_fk': 44, '항목': 23, '차수': 1, '항목_이름': '설득', '구분': '리더십역량', '정의': '필요한 자원 확보나 지지 획득을 위해 내외부 관계자의 지지를 얻어내고 협력적 네트워크 관계를 구축한다.'}}, {'id': 1452, '역량평가_fk': 346, '항목': 32, '평가점수': 0.0, '항목_data': {'id': 32, '평가설정_fk': 44, '항목': 16, '차수': 1, '항목_이름': '육성', '구분': '리더십역량', '정의': '구성원 개개인에 대해 애정과 관심을 가지고 대하며, 개인의 능력과 적성을 고려하여 성장할 수 있도록 배려한다'}}, {'id': 1453, '역량평가_fk': 346, '항목': 33, '평가점수': 0.0, '항목_data': {'id': 33, '평가설정_fk': 44, '항목': 21, '차수': 1, '항목_이름': '점검', '구분': '리더십역량', '정의': '일의 진행 과정을 정확하게 파악하고 있으며, 구성원들이 주어진 업무를 정해진 시간 안에 수행하는지 점검한다.'}}, {'id': 1454, '역량평가_fk': 346, '항목': 34, '평가점수': 0.0, '항목_data': {'id': 34, '평가설정_fk': 44, '항목': 20, '차수': 1, '항목_이름': '주도', '구분': '리더십역량', '정의': '어려운 상황에서도 방향을 분명하게 결정하고 추진해 나가면서 구성원들을 이끈다.'}}, {'id': 1455, '역량평가_fk': 346, '항목': 35, '평가점수': 0.0, '항목_data': {'id': 35, '평가설정_fk': 44, '항목': 22, '차수': 1, '항목_이름': '체계', '구분': '리더십역량', '정의': '담당 조직의 역할을 명확히 하고, 조직 구조와 업무 프로세스를 지속적으로 점검 및 정비한다.'}}, {'id': 1456, '역량평가_fk': 346, '항목': 36, '평가점수': 0.0, '항목_data': {'id': 36, '평가설정_fk': 44, '항목': 17, '차수': 1, '항목_이름': '팀워크', '구분': '리더십역량', '정의': '구성원들의 갈등을 적극적으로 해소하고 구성원들의 참여와 결속을 다진다'}}, {'id': 1457, '역량평가_fk': 346, '항목': 37, '평가점수': 0.0, '항목_data': {'id': 37, '평가설정_fk': 44, '항목': 18, '차수': 1, '항목_이름': '혁신', '구분': '리더십역량', '정의': '기존의 관행이나 고정 관념을 탈피하여 발상을 전환하고, 혁신과 창의의 필요성과 바람직성을 구성원에게 확신시킨다'}}, {'id': 1458, '역량평가_fk': 346, '항목': 38, '평가점수': 0.0, '항목_data': {'id': 38, '평가설정_fk': 44, '항목': 10, '차수': 1, '항목_이름': '고객마인드', '구분': '직무역량(공통)', '정의': '조직의 내부 고객과 외부 고객의 요구를 만족시킬 수 있다.'}}, {'id': 1459, '역량평가_fk': 346, '항목': 39, '평가점수': 0.0, '항목_data': {'id': 39, '평가설정_fk': 44, '항목': 12, '차수': 1, '항목_이름': '분석적 사고', '구분': '직무역량(공통)', '정의': '주어진 상황/과제/문제를 보다 세부적인 단위로 분해하여 분석하고, 단계적인 방법으로 상황/과제/문제의 의미를 파악할 수 있다.'}}, {'id': 1460, '역량평가_fk': 346, '항목': 40, '평가점수': 0.0, '항목_data': {'id': 40, '평가설정_fk': 44, '항목': 15, '차수': 1, '항목_이름': '업무관리', '구분': '직무역량(공통)', '정의': '주어진 시간 내에 목표를 달성할 수 있도록 긴급성, 중요성 등을 감안하여 자신의 시간을 효율적으로 활용하는 역량'}}, {'id': 1461, '역량평가_fk': 346, '항목': 41, '평가점수': 0.0, '항목_data': {'id': 41, '평가설정_fk': 44, '항목': 14, '차수': 1, '항목_이름': '의사전달', '구분': '직무역량(공통)', '정의': '자신의 의견을 명확하게 전달하며, 자신의 견해를 확실하게 피력할 수 있다.'}}, {'id': 1462, '역량평가_fk': 346, '항목': 42, '평가점수': 0.0, '항목_data': {'id': 42, '평가설정_fk': 44, '항목': 11, '차수': 1, '항목_이름': '전략적 사고', '구분': '직무역량(공통)', '정의': '이슈 또는 문제를 명확히 인식하여 그 원인을 분석하고 최적의 대안을 도출하여 실행함으로써 바람직한 목표 수준에 도달하기 위해 노력할 수 있다.'}}, {'id': 1463, '역량평가_fk': 346, '항목': 43, '평가점수': 0.0, '항목_data': {'id': 43, '평가설정_fk': 44, '항목': 9, '차수': 1, '항목_이름': '전문지식', '구분': '직무역량(공통)', '정의': '자신의 업무와 관계된 최신 지식이나 정보를 빠르게 흡수하고 업무에 적용할 수 있다.'}}, {'id': 1464, '역량평가_fk': 346, '항목': 44, '평가점수': 0.0, '항목_data': {'id': 44, '평가설정_fk': 44, '항목': 13, '차수': 1, '항목_이름': '창의적 사고', '구분': '직무역량(공통)', '정의': '다양하고 독창적인 아이디어를 발상, 제안하고 이를 적용 가능한 아이디어로 발전시킬 수 있다.'}}]}, '성과평가': {'id': 346, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10428}, '특별평가': {'id': 346, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10428}}, '1': {'평가체계_fk_data': {'id': 10697, '차수': 1, 'is_참여': True, '평가설정_fk': 44, '평가자': 127, '피평가자': 10}, '역량평가': {'id': 612, '평가체계_fk': 10697, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': []}, '성과평가': {'id': 612, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10697}, '특별평가': {'id': 612, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10697}}}},
{29: {'0': {'평가체계_fk_data': {'id': 10434, '차수': 0, 'is_참여': True, '평가설정_fk': 44, '평가자': 29, '피평가자': 29}, '역량평가': {'id': 352, '평가체계_fk': 10434, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': [{'id': 1465, '역량평가_fk': 352, '항목': 45, '평가점수': 0.0, '항목_data': {'id': 45, '평가설정_fk': 44, '항목': 6, '차수': 2, '항목_이름': '긍정성', '구분': '공통역량', '정의': '어떤 현안(주제, 방침, 업무, 관계 등)에 대해 이해, 인정, 수용 또는  개선/극복하려는 태도나 이를 표현하는 말과 행동을 보인다.'}}, {'id': 1466, '역량평가_fk': 352, '항목': 46, '평가점수': 0.0, '항목_data': {'id': 46, '평가설정_fk': 44, '항목': 2, '차수': 2, '항목_이름': '열정', '구분': '공통역량', '정의': '적극적이고 능동적인 자세로 업무를 수행하고 자신의 분야에서 최고가 된다는 열망을 가지고 노력한다.'}}, {'id': 1467, '역량평가_fk': 352, '항목': 47, '평가점수': 0.0, '항목_data': {'id': 47, '평가설정_fk': 44, '항목': 3, '차수': 2, '항목_이름': '원칙준수', '구분': '공통역량', '정의': '자신의 편의를 위해 편법을 동원하지 않고 정해진 규정과 지침, 절차를 이해하고 이에 따라 공정하고 투명하게 업무를 처리한다.'}}, {'id': 1468, '역량평가_fk': 352, '항목': 48, '평가점수': 0.0, '항목_data': {'id': 48, '평가설정_fk': 44, '항목': 8, '차수': 2, '항목_이름': '자기조절', '구분': '공통역량', '정의': '업무로 인한 스트레스를 경험하거나 부정적인 행동을 취하고 싶은 유혹에도 불구하고 자신의 감정을 조절하고 자제할 수 있다.'}}, {'id': 1469, '역량평가_fk': 352, '항목': 49, '평가점수': 0.0, '항목_data': {'id': 49, '평가설정_fk': 44, '항목': 7, '차수': 2, '항목_이름': '주인의식', '구분': '공통역량', '정의': '높은 공동체 의식과 투철한 직업정신(윤리)를 바탕으로 조직 전체의 목표를 달성하기 위해 적극적으로 참여하고 헌신할 수 있다.'}}, {'id': 1470, '역량평가_fk': 352, '항목': 50, '평가점수': 0.0, '항목_data': {'id': 50, '평가설정_fk': 44, '항목': 4, '차수': 2, '항목_이름': '팀워크', '구분': '공통역량', '정의': '주어진 업무를 수행함에 있어 업무를 적절히 분담하고, 긴밀한 협력을 통해 주어진 과제를 완수한다'}}, {'id': 1471, '역량평가_fk': 352, '항목': 51, '평가점수': 0.0, '항목_data': {'id': 51, '평가설정_fk': 44, '항목': 5, '차수': 2, '항목_이름': '프로정신', '구분': '공통역량', '정의': '자신이 하는 일에 대한 사명감과 자부심을 가지고, 어떠한 상황에서도 최고가 되기 위하여 자신을 관리한다.'}}, {'id': 1472, '역량평가_fk': 352, '항목': 52, '평가점수': 0.0, '항목_data': {'id': 52, '평가설정_fk': 44, '항목': 19, '차수': 2, '항목_이름': '결과', '구분': '리더십역량', '정의': '일에 대한 높은 관심과 동기가 있어 매우 과업지향적으로 행동한다.'}}, {'id': 1473, '역량평가_fk': 352, '항목': 53, '평가점수': 0.0, '항목_data': {'id': 53, '평가설정_fk': 44, '항목': 23, '차수': 2, '항목_이름': '설득', '구분': '리더십역량', '정의': '필요한 자원 확보나 지지 획득을 위해 내외부 관계자의 지지를 얻어내고 협력적 네트워크 관계를 구축한다.'}}, {'id': 1474, '역량평가_fk': 352, '항목': 54, '평가점수': 0.0, '항목_data': {'id': 54, '평가설정_fk': 44, '항목': 16, '차수': 2, '항목_이름': '육성', '구분': '리더십역량', '정의': '구성원 개개인에 대해 애정과 관심을 가지고 대하며, 개인의 능력과 적성을 고려하여 성장할 수 있도록 배려한다'}}, {'id': 1475, '역량평가_fk': 352, '항목': 55, '평가점수': 0.0, '항목_data': {'id': 55, '평가설정_fk': 44, '항목': 21, '차수': 2, '항목_이름': '점검', '구분': '리더십역량', '정의': '일의 진행 과정을 정확하게 파악하고 있으며, 구성원들이 주어진 업무를 정해진 시간 안에 수행하는지 점검한다.'}}, {'id': 1476, '역량평가_fk': 352, '항목': 56, '평가점수': 0.0, '항목_data': {'id': 56, '평가설정_fk': 44, '항목': 20, '차수': 2, '항목_이름': '주도', '구분': '리더십역량', '정의': '어려운 상황에서도 방향을 분명하게 결정하고 추진해 나가면서 구성원들을 이끈다.'}}, {'id': 1477, '역량평가_fk': 352, '항목': 57, '평가점수': 0.0, '항목_data': {'id': 57, '평가설정_fk': 44, '항목': 22, '차수': 2, '항목_이름': '체계', '구분': '리더십역량', '정의': '담당 조직의 역할을 명확히 하고, 조직 구조와 업무 프로세스를 지속적으로 점검 및 정비한다.'}}, {'id': 1478, '역량평가_fk': 352, '항목': 58, '평가점수': 0.0, '항목_data': {'id': 58, '평가설정_fk': 44, '항목': 17, '차수': 2, '항목_이름': '팀워크', '구분': '리더십역량', '정의': '구성원들의 갈등을 적극적으로 해소하고 구성원들의 참여와 결속을 다진다'}}, {'id': 1479, '역량평가_fk': 352, '항목': 59, '평가점수': 0.0, '항목_data': {'id': 59, '평가설정_fk': 44, '항목': 18, '차수': 2, '항목_이름': '혁신', '구분': '리더십역량', '정의': '기존의 관행이나 고정 관념을 탈피하여 발상을 전환하고, 혁신과 창의의 필요성과 바람직성을 구성원에게 확신시킨다'}}, {'id': 1480, '역량평가_fk': 352, '항목': 60, '평가점수': 0.0, '항목_data': {'id': 60, '평가설정_fk': 44, '항목': 10, '차수': 2, '항목_이름': '고객마인드', '구분': '직무역량(공통)', '정의': '조직의 내부 고객과 외부 고객의 요구를 만족시킬 수 있다.'}}, {'id': 1481, '역량평가_fk': 352, '항목': 61, '평가점수': 0.0, '항목_data': {'id': 61, '평가설정_fk': 44, '항목': 12, '차수': 2, '항목_이름': '분석적 사고', '구분': '직무역량(공통)', '정의': '주어진 상황/과제/문제를 보다 세부적인 단위로 분해하여 분석하고, 단계적인 방법으로 상황/과제/문제의 의미를 파악할 수 있다.'}}, {'id': 1482, '역량평가_fk': 352, '항목': 62, '평가점수': 0.0, '항목_data': {'id': 62, '평가설정_fk': 44, '항목': 15, '차수': 2, '항목_이름': '업무관리', '구분': '직무역량(공통)', '정의': '주어진 시간 내에 목표를 달성할 수 있도록 긴급성, 중요성 등을 감안하여 자신의 시간을 효율적으로 활용하는 역량'}}, {'id': 1483, '역량평가_fk': 352, '항목': 63, '평가점수': 0.0, '항목_data': {'id': 63, '평가설정_fk': 44, '항목': 14, '차수': 2, '항목_이름': '의사전달', '구분': '직무역량(공통)', '정의': '자신의 의견을 명확하게 전달하며, 자신의 견해를 확실하게 피력할 수 있다.'}}, {'id': 1484, '역량평가_fk': 352, '항목': 64, '평가점수': 0.0, '항목_data': {'id': 64, '평가설정_fk': 44, '항목': 11, '차수': 2, '항목_이름': '전략적 사고', '구분': '직무역량(공통)', '정의': '이슈 또는 문제를 명확히 인식하여 그 원인을 분석하고 최적의 대안을 도출하여 실행함으로써 바람직한 목표 수준에 도달하기 위해 노력할 수 있다.'}}, {'id': 1485, '역량평가_fk': 352, '항목': 65, '평가점수': 0.0, '항목_data': {'id': 65, '평가설정_fk': 44, '항목': 9, '차수': 2, '항목_이름': '전문지식', '구분': '직무역량(공통)', '정의': '자신의 업무와 관계된 최신 지식이나 정보를 빠르게 흡수하고 업무에 적용할 수 있다.'}}, {'id': 1486, '역량평가_fk': 352, '항목': 66, '평가점수': 0.0, '항목_data': {'id': 66, '평가설정_fk': 44, '항목': 13, '차수': 2, '항목_이름': '창의적 사고', '구분': '직무역량(공통)', '정의': '다양하고 독창적인 아이디어를 발상, 제안하고 이를 적용 가능한 아이디어로 발전시킬 수 있다.'}}]}, '성과평가': {'id': 352, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10434}, '특별평가': {'id': 352, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10434}}, '1': {'평가체계_fk_data': {'id': 10481, '차수': 1, 'is_참여': True, '평가설정_fk': 44, '평가자': 29, '피평가자': 29}, '역량평가': {'id': 398, '평가체계_fk': 10481, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': []}, '성과평가': {'id': 398, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10481}, '특별평가': {'id': 398, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10481}}}},
{1: {'0': {'평가체계_fk_data': {'id': 10435, '차수': 0, 'is_참여': True, '평가설정_fk': 44, '평가자': 1, '피평가자': 1}, '역량평가': {'id': 353, '평가체계_fk': 10435, 'is_submit': False, '평가종류': '개별', '평가점수': 2.9090909090909087, '역량평가_api_datas': [{'id': 2857, '역량평가_fk': 353, '항목': 45, '평가점수': 2.5, '항목_data': {'id': 45, '평가설정_fk': 44, '항목': 6, '차수': 2, '항목_이름': '긍정성', '구분': '공통역량', '정의': '어떤 현안(주제, 방침, 업무, 관계 등)에 대해 이해, 인정, 수용 또는  개선/극복하려는 태도나 이를 표현하는 말과 행동을 보인다.'}}, {'id': 2858, '역량평가_fk': 353, '항목': 46, '평가점수': 2.5, '항목_data': {'id': 46, '평가설정_fk': 44, '항목': 2, '차수': 2, '항목_이름': '열정', '구분': '공통역량', '정의': '적극적이고 능동적인 자세로 업무를 수행하고 자신의 분야에서 최고가 된다는 열망을 가지고 노력한다.'}}, {'id': 2859, '역량평가_fk': 353, '항목': 47, '평가점수': 3.5, '항목_data': {'id': 47, '평가설정_fk': 44, '항목': 3, '차수': 2, '항목_이름': '원칙준수', '구분': '공통역량', '정의': '자신의 편의를 위해 편법을 동원하지 않고 정해진 규정과 지침, 절차를 이해하고 이에 따라 공정하고 투명하게 업무를 처리한다.'}}, {'id': 2860, '역량평가_fk': 353, '항목': 48, '평가점수': 3.3, '항목_data': {'id': 48, '평가설정_fk': 44, '항목': 8, '차수': 2, '항목_이름': '자기조절', '구분': '공통역량', '정의': '업무로 인한 스트레스를 경험하거나 부정적인 행동을 취하고 싶은 유혹에도 불구하고 자신의 감정을 조절하고 자제할 수 있다.'}}, {'id': 2861, '역량평가_fk': 353, '항목': 49, '평가점수': 3.0, '항목_data': {'id': 49, '평가설정_fk': 44, '항목': 7, '차수': 2, '항목_이름': '주인의식', '구분': '공통역량', '정의': '높은 공동체 의식과 투철한 직업정신(윤리)를 바탕으로 조직 전체의 목표를 달성하기 위해 적극적으로 참여하고 헌신할 수 있다.'}}, {'id': 2862, '역량평가_fk': 353, '항목': 50, '평가점수': 2.7, '항목_data': {'id': 50, '평가설정_fk': 44, '항목': 4, '차수': 2, '항목_이름': '팀워크', '구분': '공통역량', '정의': '주어진 업무를 수행함에 있어 업무를 적절히 분담하고, 긴밀한 협력을 통해 주어진 과제를 완수한다'}}, {'id': 2863, '역량평가_fk': 353, '항목': 51, '평가점수': 3.4, '항목_data': {'id': 51, '평가설정_fk': 44, '항목': 5, '차수': 2, '항목_이름': '프로정신', '구분': '공통역량', '정의': '자신이 하는 일에 대한 사명감과 자부심을 가지고, 어떠한 상황에서도 최고가 되기 위하여 자신을 관리한다.'}}, {'id': 2864, '역량평가_fk': 353, '항목': 52, '평가점수': 2.8, '항목_data': {'id': 52, '평가설정_fk': 44, '항목': 19, '차수': 2, '항목_이름': '결과', '구분': '리더십역량', '정의': '일에 대한 높은 관심과 동기가 있어 매우 과업지향적으로 행동한다.'}}, {'id': 2865, '역량평가_fk': 353, '항목': 53, '평가점수': 2.7, '항목_data': {'id': 53, '평가설정_fk': 44, '항목': 23, '차수': 2, '항목_이름': '설득', '구분': '리더십역량', '정의': '필요한 자원 확보나 지지 획득을 위해 내외부 관계자의 지지를 얻어내고 협력적 네트워크 관계를 구축한다.'}}, {'id': 2866, '역량평가_fk': 353, '항목': 54, '평가점수': 3.5, '항목_data': {'id': 54, '평가설정_fk': 44, '항목': 16, '차수': 2, '항목_이름': '육성', '구분': '리더십역량', '정의': '구성원 개개인에 대해 애정과 관심을 가지고 대하며, 개인의 능력과 적성을 고려하여 성장할 수 있도록 배려한다'}}, {'id': 2867, '역량평가_fk': 353, '항목': 55, '평가점수': 2.7, '항목_data': {'id': 55, '평가설정_fk': 44, '항목': 21, '차수': 2, '항목_이름': '점검', '구분': '리더십역량', '정의': '일의 진행 과정을 정확하게 파악하고 있으며, 구성원들이 주어진 업무를 정해진 시간 안에 수행하는지 점검한다.'}}, {'id': 2868, '역량평가_fk': 353, '항목': 56, '평가점수': 3.4, '항목_data': {'id': 56, '평가설정_fk': 44, '항목': 20, '차수': 2, '항목_이름': '주도', '구분': '리더십역량', '정의': '어려운 상황에서도 방향을 분명하게 결정하고 추진해 나가면서 구성원들을 이끈다.'}}, {'id': 2869, '역량평가_fk': 353, '항목': 57, '평가점수': 2.4, '항목_data': {'id': 57, '평가설정_fk': 44, '항목': 22, '차수': 2, '항목_이름': '체계', '구분': '리더십역량', '정의': '담당 조직의 역할을 명확히 하고, 조직 구조와 업무 프로세스를 지속적으로 점검 및 정비한다.'}}, {'id': 2870, '역량평가_fk': 353, '항목': 58, '평가점수': 2.3, '항목_data': {'id': 58, '평가설정_fk': 44, '항목': 17, '차수': 2, '항목_이름': '팀워크', '구분': '리더십역량', '정의': '구성원들의 갈등을 적극적으로 해소하고 구성원들의 참여와 결속을 다진다'}}, {'id': 2871, '역량평가_fk': 353, '항목': 59, '평가점수': 2.7, '항목_data': {'id': 59, '평가설정_fk': 44, '항목': 18, '차수': 2, '항목_이름': '혁신', '구분': '리더십역량', '정의': '기존의 관행이나 고정 관념을 탈피하여 발상을 전환하고, 혁신과 창의의 필요성과 바람직성을 구성원에게 확신시킨다'}}, {'id': 2872, '역량평가_fk': 353, '항목': 60, '평가점수': 3.0, '항목_data': {'id': 60, '평가설정_fk': 44, '항목': 10, '차수': 2, '항목_이름': '고객마인드', '구분': '직무역량(공통)', '정의': '조직의 내부 고객과 외부 고객의 요구를 만족시킬 수 있다.'}}, {'id': 2873, '역량평가_fk': 353, '항목': 61, '평가점수': 3.3, '항목_data': {'id': 61, '평가설정_fk': 44, '항목': 12, '차수': 2, '항목_이름': '분석적 사고', '구분': '직무역량(공통)', '정의': '주어진 상황/과제/문제를 보다 세부적인 단위로 분해하여 분석하고, 단계적인 방법으로 상황/과제/문제의 의미를 파악할 수 있다.'}}, {'id': 2874, '역량평가_fk': 353, '항목': 62, '평가점수': 2.5, '항목_data': {'id': 62, '평가설정_fk': 44, '항목': 15, '차수': 2, '항목_이름': '업무관리', '구분': '직무역량(공통)', '정의': '주어진 시간 내에 목표를 달성할 수 있도록 긴급성, 중요성 등을 감안하여 자신의 시간을 효율적으로 활용하는 역량'}}, {'id': 2875, '역량평가_fk': 353, '항목': 63, '평가점수': 2.8, '항목_data': {'id': 63, '평가설정_fk': 44, '항목': 14, '차수': 2, '항목_이름': '의사전달', '구분': '직무역량(공통)', '정의': '자신의 의견을 명확하게 전달하며, 자신의 견해를 확실하게 피력할 수 있다.'}}, {'id': 2876, '역량평가_fk': 353, '항목': 64, '평가점수': 3.2, '항목_data': {'id': 64, '평가설정_fk': 44, '항목': 11, '차수': 2, '항목_이름': '전략적 사고', '구분': '직무역량(공통)', '정의': '이슈 또는 문제를 명확히 인식하여 그 원인을 분석하고 최적의 대안을 도출하여 실행함으로써 바람직한 목표 수준에 도달하기 위해 노력할 수 있다.'}}, {'id': 2877, '역량평가_fk': 353, '항목': 65, '평가점수': 2.9, '항목_data': {'id': 65, '평가설정_fk': 44, '항목': 9, '차수': 2, '항목_이름': '전문지식', '구분': '직무역량(공통)', '정의': '자신의 업무와 관계된 최신 지식이나 정보를 빠르게 흡수하고 업무에 적용할 수 있다.'}}, {'id': 2878, '역량평가_fk': 353, '항목': 66, '평가점수': 2.9, '항목_data': {'id': 66, '평가설정_fk': 44, '항목': 13, '차수': 2, '항목_이름': '창의적 사고', '구분': '직무역량(공통)', '정의': '다양하고 독창적인 아이디어를 발상, 제안하고 이를 적용 가능한 아이디어로 발전시킬 수 있다.'}}]}, '성과평가': {'id': 353, 'is_submit': False, '평가종류': '개별', '평가점수': 1.5, '평가체계_fk': 10435}, '특별평가': {'id': 353, 'is_submit': False, '평가종류': '개별', '평가점수': 3.1100000000000003, '평가체계_fk': 10435}}, '1': {'평가체계_fk_data': {'id': 10436, '차수': 1, 'is_참여': True, '평가설정_fk': 44, '평가자': 1, '피평가자': 1}, '역량평가': {'id': 354, '평가체계_fk': 10436, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '역량평가_api_datas': []}, '성과평가': {'id': 354, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10436}, '특별평가': {'id': 354, 'is_submit': False, '평가종류': '개별', '평가점수': 0.0, '평가체계_fk': 10436}}}},
        ]

    app = QApplication([])
    main_window = QMainWindow()
    main_window.setMinimumSize(1800, 800)
    wid_table = Wid_table_종합평가(main_window, api_datas)
    main_window.setCentralWidget(wid_table)
    main_window.show()
    app.exec()