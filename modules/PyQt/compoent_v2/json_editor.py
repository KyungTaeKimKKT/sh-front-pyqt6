import json

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class Mixin_JsonEditor:
    def init_ui(self):
        self.setWindowTitle("JSON Editor")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        self.label_status = QLabel("JSON 설정을 입력하세요.")
        layout.addWidget(self.label_status)

        lb_json = QLabel("JSON 영역")
        layout.addWidget(lb_json)
        self.editor_json = QPlainTextEdit()
        self.editor_json.setFont(QFont("Courier", 10))
        self.editor_json.setPlaceholderText('{\n    "theme": "dark",\n    "refresh": true\n}')
        self.editor_json.textChanged.connect(self.validate_json)
        layout.addWidget(self.editor_json)
        ### spacing
        layout.addSpacing(16*2)

        lb_dict = QLabel("Dict 영역")
        layout.addWidget(lb_dict)

        self.editor_dict = QPlainTextEdit()
        self.editor_dict.setFont(QFont("Courier", 10))
        self.editor_dict.setPlaceholderText('{\n    "theme": "dark",\n    "refresh": true\n}')
        self.editor_dict.textChanged.connect(self.validate_json)
        layout.addWidget(self.editor_dict)

        btn_container = QWidget()   
        btn_layout = QHBoxLayout()
        btn_container.setLayout(btn_layout)

        self.btn_convert = QPushButton("Dict -> JSON")
        self.btn_convert.clicked.connect(self.on_btn_convert_dict_to_json)
        btn_layout.addWidget(self.btn_convert)

        self.btn_validate = QPushButton("유효성 검사")
        self.btn_validate.clicked.connect(self.validate_json)
        btn_layout.addWidget(self.btn_validate)

        self.btn_ok = QPushButton("Ok")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.on_btn_ok)
        btn_layout.addWidget(self.btn_ok)

        layout.addWidget(btn_container)

    def check_changed(self) -> bool:
        return self.get_value() != self.dict_data
    
    def on_btn_convert_dict_to_json(self):
        try:
            json_data = json.loads(self.editor_dict.toPlainText())
            self.editor_json.setPlainText(json.dumps(json_data, indent=4, ensure_ascii=False))
        except Exception as e:
            self.label_status.setText(f"❌ JSON 변환 에러: {e}")
            self.label_status.setStyleSheet("color: yellow;background-color: black;font-weight:bold;")
            self.is_validated = False
            self.btn_ok.setEnabled(False)


    def validate_json(self):
        try:
            json_data = json.loads(self.editor_json.toPlainText())
            self.label_status.setText("✅ 유효한 JSON입니다.")  
            self.is_validated = True
            self.btn_ok.setEnabled( self.check_changed() )
            self.label_status.setStyleSheet("background-color: white;color: black;")
        except json.JSONDecodeError as e:
            self.label_status.setText(f"❌ JSON 에러: {e}")
            self.label_status.setStyleSheet("color: yellow;background-color: black;font-weight:bold;")
            self.is_validated = False
            self.btn_ok.setEnabled(False)


    def get_value(self):
        return json.loads(self.editor_json.toPlainText())
    
    def set_value(self, value:dict):
        try:
            print(f"set_value: {value}")
            if isinstance(value, dict):
                self.editor_json.setPlainText(json.dumps(value, indent=4, ensure_ascii=False))
                self.editor_dict.setPlainText(json.dumps(value, indent=4, ensure_ascii=False))
            else:
                raise ValueError(f"set_value 오류: {type(value)}")
        except Exception as e:
            print(f"set_value 오류: {e}")


    def set_readonly(self, is_readonly:bool):
        self.editor_json.setReadOnly(is_readonly)
        self.editor_dict.setReadOnly(is_readonly)

    def on_btn_ok(self):
        self.accept()

    def submit_json(self):
        try:
            json_data = self.get_value()
        except json.JSONDecodeError as e:
            pass

        try:
            #### pass
            #### 서버에 전송 필요시 수정
            pass

        except Exception as e:
            pass

class Dialog_JsonEditor(QDialog, Mixin_JsonEditor):
    def __init__(self, parent:QWidget=None, api_url: str=None, _dict_data:dict=None, **kwargs):
        super().__init__(parent)
        self.api_url = api_url
        self.dict_data = _dict_data
        self.kwargs = kwargs
        self.init_ui()
        self.is_validated = False

        if self.dict_data:
            self.set_value(self.dict_data)


class QWidget_JsonEditor(QWidget, Mixin_JsonEditor):
    def __init__(self, parent:QWidget=None, api_url: str=None, _dict_data:dict=None, **kwargs):
        super().__init__(parent)
        self.api_url = api_url
        self.dict_data = _dict_data
        self.kwargs = kwargs
        self.init_ui()
        self.is_validated = False

        if self.dict_data:
            self.set_value(self.dict_data)
        
