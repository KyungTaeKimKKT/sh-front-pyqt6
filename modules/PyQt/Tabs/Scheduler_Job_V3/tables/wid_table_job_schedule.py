from modules.common_import_v2 import *

from cron_descriptor import get_description

class JobConfigDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data or {}
        self.setWindowTitle("Job Configuration")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # job_info 선택 버튼
        self._text_pb_select_job_info = "필수: Job Info"
        self.pb_select_job_info = QPushButton(self._text_pb_select_job_info)
        self.pb_select_job_info.clicked.connect(self.on_select_job_info)
        form_layout.addRow("Job Info:", self.pb_select_job_info)

        self.lb_job_name = QLabel()
        form_layout.addRow("Job Name:", self.lb_job_name)

        form_layout.addRow("주의사항:", QLabel("Job type에 따라 필수 항목이 달라집니다.<br> interval - job_interval, cron - cron_expression"))
        
        # job_type combo
        self.cb_job_type = QComboBox()
        self.cb_job_type.addItems(["미선택","interval", "cron"])
        self.cb_job_type.setCurrentIndex(0)
        self.cb_job_type.currentTextChanged.connect(self.on_job_type_changed)
        form_layout.addRow("Job Type:", self.cb_job_type)

        # job_interval (integer)
        self.sb_job_interval = QSpinBox()
        self.sb_job_interval.setMinimum(1)
        form_layout.addRow("Job Interval(초)):", self.sb_job_interval)

        # cron_expression (char)
        self.le_cron_expression = QLineEdit()
        self.le_cron_expression.textChanged.connect(self.on_cron_expression_changed)
        form_layout.addRow("Cron Expression:", self.le_cron_expression)

        # cron validation
        self.lb_cron_validation = QLabel()
        form_layout.addRow("Cron Validation:", self.lb_cron_validation)

        # cron_description
        self.lb_cron_description = QLabel()
        form_layout.addRow("Cron Description:", self.lb_cron_description)        

        # timeout_seconds
        self.sb_timeout = QSpinBox()
        self.sb_timeout.setMaximum(86400)
        form_layout.addRow("Timeout Seconds:", self.sb_timeout)

        # is_active
        self.chk_is_active = QCheckBox("Is Active")
        form_layout.addRow(self.chk_is_active)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.pb_ok = QPushButton("OK")
        self.pb_ok.setEnabled(False)
        self.pb_cancel = QPushButton("Cancel")
        self.pb_ok.clicked.connect(self.accept)
        self.pb_cancel.clicked.connect(self.reject)

        button_layout.addWidget(self.pb_ok)
        button_layout.addWidget(self.pb_cancel)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.populate_data()

    def populate_data(self):
        if self.data.get('id', -1) < 1:
            self.cb_job_type.setCurrentText('미선택')
        else:
            self.cb_job_type.setCurrentText(self.data.get('job_type', '미선택'))
            job_info = self.data.get('job_info')
            if isinstance(job_info, dict):
                self.lb_job_name.setText(job_info.get('name', ''))

        self.sb_job_interval.setValue(self.data.get('job_interval', 1))
        self.le_cron_expression.setText(self.data.get('cron_expression', ''))
        self.sb_timeout.setValue(self.data.get('timeout_seconds', 300))
        self.chk_is_active.setChecked(self.data.get('is_active', False))

        

    def on_job_type_changed(self, job_type):
        if job_type == 'interval':
            self.sb_job_interval.setEnabled(True)
            self.le_cron_expression.setEnabled(False)
            self.sb_job_interval.setFocus()
        else:
            self.sb_job_interval.setEnabled(False)
            self.le_cron_expression.setEnabled(True)
            self.le_cron_expression.setText("")
            self.le_cron_expression.setPlaceholderText("예) 0 0 * * *")
            self.le_cron_expression.setFocus()
        self.check_ok_button_enable()

    def on_select_job_info(self):
        dlg = Dialog_JOB_INFO_선택(self)
        if dlg.exec():
            job_info = dlg.get_selected_job_info()
            if job_info:
                self.data['job_info'] = job_info['id']
                self.lb_job_name.setText(job_info.get('name', ''))
                self.pb_select_job_info.setText(f"{self._text_pb_select_job_info} : {job_info['id']}")
        self.check_ok_button_enable()

    def check_ok_button_enable(self) -> None:
        _checklist = [
            bool(self.data.get('job_info', None)),
            bool(self.cb_job_type.currentText() != '미선택'),
            bool(self.lb_cron_validation.text() == "유효한 Cron Expression" if self.cb_job_type.currentText() == 'cron' else True),
        ]
        if all(_checklist):
            self.pb_ok.setEnabled(True)
        else:
            self.pb_ok.setEnabled(False)

    def on_cron_expression_changed(self):
        if self.cb_job_type.currentText() != 'cron':
            return 
        style = {
            True: "background-color: green; color: white;",
            False: "background-color: red; color: white;",
        }
        cron_exp = self.le_cron_expression.text().strip()
        if cron_exp:
            is_valid = self.validate_cron_expression(cron_exp)
            if is_valid:
                self.lb_cron_validation.setText("유효한 Cron Expression")
                self.lb_cron_validation.setStyleSheet(style[True])
                try:
                    desc = get_description(cron_exp)
                except Exception as e:
                    desc = f"설명 분석 실패: {e}"
                self.lb_cron_description.setText( desc )
                self.lb_cron_description.setStyleSheet(style[True])
            else:
                self.lb_cron_validation.setText("잘못된 Cron Expression")
                self.lb_cron_validation.setStyleSheet(style[False])
                self.lb_cron_description.setText("")
                self.lb_cron_description.setStyleSheet(style[False])
        else:
            self.lb_cron_validation.setText("")

        self.check_ok_button_enable()

    def get_data(self):
        cron_exp = self.le_cron_expression.text()
        if self.cb_job_type.currentText() == 'cron' and not self.validate_cron_expression(cron_exp):
            raise ValueError("Invalid Cron Expression")
        update_data = {
            'job_info': self.data.get('job_info', {}),
            'job_type': self.cb_job_type.currentText(),
            'job_interval': self.sb_job_interval.value(),
            'cron_expression': cron_exp,
            'timeout_seconds': self.sb_timeout.value(),
            'is_active': self.chk_is_active.isChecked()
        }
        self.data.update(update_data)
        return self.data

    @staticmethod
    def validate_cron_expression(expr) -> bool: 
        # Very basic cron format validation: 5 fields separated by space
        return bool(re.match(r'^([\*\d\/,-]+\s){4}[\*\d\/,-]+$', expr.strip()))

class Dialog_JOB_INFO_선택(QDialog):
    """ kwargs:
        title: str = 'Scheduler JOB 선택'
        search_placeholder: str = 'JOB 이름 검색...'
        list_name_key: str = 'name'
        base_auto_fetch: bool = True : 상속받는 부모의 auto_fetch 여부
    """
    def __init__(self, parent:QWidget, url:Optional[str]=None, **kwargs):
        super().__init__(parent)
        self.kwargs = kwargs
        self.url = url or 'scheduler_job/job-names-only/?page_size=0'
        self._list:list[dict] = []
        self.filtered_list:list[dict] = []
        self.is_init_ui = False

        if self.kwargs.get('base_auto_fetch', True):
            self.init_ui()               # UI 먼저 초기화 (search_input 등 생성)
            self.fetch_table_list()      # 그 후 데이터 불러오기 및 필터 갱신

            if not self._list:
                self.close()

    def fetch_table_list(self):
        """ data 형태 : [
                {
                    "id": 9,
                    "name": "서버-리소스"
                },
            
                ]
        """
        is_ok, _json = APP.API.getlist(url=self.url)
        if is_ok:
            self._list = _json
            self.filtered_table_list = self._list.copy()
            if self.is_init_ui:
                self.update_filter(self.search_input.text())  # 🔹 검색어 유지하면서 갱신
        else:
            Utils.generate_QMsg_critical(None, 
                                title=f'{self.kwargs.get("title", "JOB INFO 선택")} 실패', 
                                text=f'{self.kwargs.get("title", "테이블 선택")} 실패: <br>{json.dumps(_json, ensure_ascii=False)}')

    def init_ui(self):
        self.setWindowTitle(f'{self.kwargs.get("title", "JOB INFO 선택")}')
        self.setMinimumSize(400, 300)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)

        layout = QVBoxLayout(self)
        #### refresh button 추가
        self.pb_refresh = CustomPushButton(self, 'Refresh')
        self.pb_refresh.clicked.connect(self.fetch_table_list)
        layout.addWidget(self.pb_refresh)

        # 검색창
        self.search_input = Custom_LineEdit(self)
        self.search_input.setPlaceholderText(f"{self.kwargs.get('search_placeholder', 'JOB 이름 검색...')}")
        self.search_input.textChanged.connect(self.update_filter)
        layout.addWidget(self.search_input)

        # 리스트
        self.list_widget = QListWidget(self)
        self.populate_list()
        layout.addWidget(self.list_widget)

        # 버튼
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("확인")
        self.btn_cancel = QPushButton("취소")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.is_init_ui = True

    def populate_list(self):
        self.list_widget.clear()
        for item in self.filtered_list:
            self.list_widget.addItem(item[ self.kwargs.get('list_name_key', 'name') ])

    def update_filter(self, text: str):
        keyword = text.strip().lower()
        self.filtered_list = [
            item for item in self._list if keyword in item[self.kwargs.get('list_name_key', 'name')].replace('appID', '').lower()
        ]
        self.populate_list()

    def accept_selection(self):
        self.selected_table = None  # 기본값
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.selected_table = self.filtered_list[current_row]
            self.accept()
        else:
            QMessageBox.warning(self, "선택 오류", "테이블을 선택하세요.")

    def get_selected_job_info(self) -> dict:
        """선택된 JOB INFO 반환. 없으면 None"""
        return getattr(self, 'selected_table', None)


class View_job_schedule(Base_Table_View):
    pass

class Model_job_schedule(Base_Table_Model):
    pass

class Delegate_job_schedule(Base_Delegate):
    pass

class Wid_table_job_schedule(Wid_table_Base_V2):

    def setup_table(self):
        self.view = View_job_schedule(self)
        self.model = Model_job_schedule(self.view)
        self.delegate = Delegate_job_schedule(self.view)

        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_new_row(self):
        is_ok, _json = APP.API.getlist(url=self.url+'template')
        if is_ok:
            dlg = JobConfigDialog(self, data=_json)
            if dlg.exec():
                _data = dlg.get_data()
                if _data:
                    print ( 'on_new_row : ', _data )
                    _isok, _json = APP.API.Send(url=self.url, dataObj=_data, sendData=_data )
                    if _isok:
                        self.model._data.insert(0, _json)
                        self.model.layoutChanged.emit()
                    else:
                        Utils.generate_QMsg_critical(None, 
                                title=f'{self.kwargs.get("title", "JOB INFO 선택")} 실패', 
                                text=f'{self.kwargs.get("title", "테이블 선택")} 실패: <br>{json.dumps(_json, ensure_ascii=False)}')

        if self.selected_rows:
            self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):
        self.model.on_delete_row(rowDict=self.selected_rows[0])
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()
