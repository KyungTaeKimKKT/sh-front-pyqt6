from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import datetime
from itertools import chain

from modules.PyQt.Tabs.HR평가.dialog.ui.Ui_dialog_역량평가 import Ui_Dialog_Yokyang
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from modules.PyQt.User.validator import 망등록_망번호_Validator
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Dialog_역량평가(QDialog,   Qwidget_Utils):
    """ kwargs \n
        url = str,\n
        dataObj = {}
    """
    signal_data = pyqtSignal(list)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.app_Dict :dict
        self.DB_All :list[dict]
        self.DB_Selected : list[int] ### model m2m item_fks 임
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.ui = Ui_Dialog_Yokyang()
        self.ui.setupUi(self)
        # self.ui.PB_Save.setEnabled(True)
        self.__init__default_setting()

        self.triggerConnect()
        
        self.show()

    def triggerConnect(self):
        self.ui.PB_Select.clicked.connect( self.slot_PB_Select )
        self.ui.PB_Unselect.clicked.connect( self.slot_PB_Unselect )

        self.ui.PB_Save.clicked.connect ( self.slot_PB_Save)

    @pyqtSlot()
    def slot_PB_Save(self):
        itemsTextList =  [str(self.ui.listWidget_after.item(i).text()) for i in range(self.ui.listWidget_after.count())]
        IDs = [ int( txt.split('-')[0].strip() )  for txt in itemsTextList ]
        self.signal_data.emit(IDs)

    @pyqtSlot()
    def slot_PB_Select(self):
        sel_items = self.ui.listWidget_before.selectedItems() 
        if not sel_items : return


        self.ui.listWidget_after.addItems ( [qItem.text()  for qItem in sel_items] )
        for item in sel_items:
            self.ui.listWidget_before.takeItem( self.ui.listWidget_before.row(item))

    @pyqtSlot()
    def slot_PB_Unselect(self):
        sel_items = self.ui.listWidget_after.selectedItems() 
        if not sel_items : return

        # for qItem in sel_items:
        #     self.ui.listWidget_before.addItem(qItem)
        self.ui.listWidget_before.addItems ( [qItem.text()  for qItem in sel_items] )
        for item in sel_items:
            self.ui.listWidget_after.takeItem( self.ui.listWidget_after.row(item))


    def __init__default_setting(self):      
        # for obj in self.DB_All:
        self.listItems_DB_All = [ f"{str(obj.get('id'))} - {obj.get('구분')} -{obj.get('항목')}" for obj in self.DB_All  ]

        self.listItems_Selected =  [ item for item in self.listItems_DB_All if int( item.split('-')[0].strip() ) in self.DB_Selected ]
        self.listItems_Unselected = [ item for item in self.listItems_DB_All if not item in self.listItems_Selected  ]
        self.ui.listWidget_before.addItems( self.listItems_Unselected )
        self.ui.listWidget_after.addItems( self.listItems_Selected )


    