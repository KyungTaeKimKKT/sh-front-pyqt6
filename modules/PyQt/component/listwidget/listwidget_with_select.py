from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import json

from modules.PyQt.component.listwidget.ui.Ui_listwidget_with_select import Ui_Form
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ListWidget_With_Select(QWidget):
    signal_selected = pyqtSignal(int)

    def __init__(self, parent , **kwargs):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.PB_Select.clicked.connect ( lambda: self.signal_selected.emit( self.ui.listWidget.currentRow()) )


        self._update(**kwargs)
    

    def _update ( self, **kwargs ):
        """
          kwargs['_data'] ==> list[dict] , list[str] 2 type
        """

        if ( _datas := kwargs.get('_data', False) ) and len(_datas) > 0:
            self._datas = _datas
            if isinstance ( _datas[0], (str, ) ):
                self.ui.listWidget.addItems( self._datas)
            elif isinstance ( _datas[0], ( dict, ) ):
                self.ui.listWidget.addItems ( [json.dumps(obj, ensure_ascii=False) + '\n' for obj in self._datas])

        