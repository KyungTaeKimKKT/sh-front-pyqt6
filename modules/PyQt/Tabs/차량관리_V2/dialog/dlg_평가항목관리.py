from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from datetime import datetime

from modules.PyQt.Tabs.HR평가.dialog.ui.Ui_tab_HR평가_평가항목설정 import Ui_Tab
from modules.PyQt.User.qwidget_utils import Qwidget_Utils

from modules.PyQt.Tabs.HR평가.dialog.dlg_역량평가항목 import Dialog_역량평가

from config import Config as APP
import modules.user.utils as Utils
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST

from modules.PyQt.User.validator import 망등록_망번호_Validator

class Dialog_HR평가_평가항목설정(QDialog,   Qwidget_Utils):
    """ kwargs \n
        url = str,\n
        dataObj = {}
    """
    signal_data = pyqtSignal(dict)

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.app_Dict :dict
        self.총평가차수 : int
        self.역량평가사전_DB_All :list[dict] = []
        self.역량항목_DB_All :list[dict] = []
        self.평가항목_DB_구분_dict = { 0:'본인평가', 1:'1차평가',2:'2차평가', 3:'3차평가',4:'4차평가',5:'5차평가'}

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.ui = Ui_Tab()
        self.ui.setupUi(self)
        # self.ui.PB_Save.setEnabled(True)

        self._update_data_self()

        self.triggerConnect()

        self.show()

    def _update_data_self(self):
        _isOk0, self.역량평가사전_DB_All = APP.API.getlist(INFO.URL_HR평가_역량평가사전_DB+INFO.PARAM_NO_PAGE )
        _isOK1, self.역량항목_DB_All = APP.API.getlist(INFO.URL_HR평가_역량항목_DB+ f"?평가설정_fk={self.app_Dict.get('id')}&page_size=0")
        self.__init__default_setting()

        
        if not ( _isOk0 and _isOK1) :
            Utils.generate_QMsg_critical(self )

    def triggerConnect(self):
        self.ui.PB_0.clicked.connect(lambda : self.slot_PB(0) )
        self.ui.PB_1.clicked.connect(lambda : self.slot_PB(1) )
        self.ui.PB_2.clicked.connect(lambda : self.slot_PB(2) )
        self.ui.PB_3.clicked.connect(lambda : self.slot_PB(3) )
        self.ui.PB_4.clicked.connect(lambda : self.slot_PB(4) )

        for 차수 in range( 1, self.총평가차수+1):
            groupbox = getattr(self.ui , f"groupBox_{차수}_Gijun")
            for rb in groupbox.findChildren(QRadioButton):
                rb : QRadioButton
                rb.clicked.connect ( self.slot_rb_clicked )

    @pyqtSlot()
    def slot_rb_clicked(self):


    def slot_dlg_역량평가_IDs(self, wid:QDialog, IDs:list[int], sendData:dict):

        if len(IDs) > 0:
            sendData.update ({'item_fks': IDs} )
            _isOk, _json = APP.API.Send ( INFO.URL_HR평가_역량항목_DB, sendData, sendData )
            if _isOk:
                self._update_data_self()
                wid.close()
            else:
                Utils.generate_QMsg_critical(self)

    @pyqtSlot()
    def slot_PB(self, 구분No:int):
        obj = Utils.get_Obj_From_ListDict_by_subDict( self.역량항목_DB_All, { '구분': self.평가항목_DB_구분_dict[구분No] })

        dlg = Dialog_역량평가(self, 
                        DB_All= self.역량평가사전_DB_All ,
                        DB_Selected = obj.get('item_fks',[] ) ,
                        )
        sendData = { '평가설정_fk': self.app_Dict.get('id'), '구분': self.평가항목_DB_구분_dict[구분No], 'id' : obj.get('id', -1)  }
        dlg.signal_data.connect(lambda IDs: self.slot_dlg_역량평가_IDs( dlg, IDs, sendData))


    def __init__default_setting(self):      
 
        now = datetime.now()
        if hasattr(self, 'app_Dict') and self.app_Dict:
            총평가차수 = self.app_Dict.get('총평가차수')
            self.총평가차수 = 총평가차수
            for over_차수 in range( 총평가차수+1, 총평가차수+ 5):
                if hasattr(self.ui, f"frame_{over_차수}") :
                    getattr(self.ui, f"frame_{over_차수}").hide()
                if hasattr( self.ui, f"groupBox_{over_차수}_Gijun"):
                    getattr(self.ui, f"groupBox_{over_차수}_Gijun" ).hide()

            for 차수 in range(1,총평가차수+1) :
                if 차수 == 1:
                    if hasattr( self.ui, f'rb_{차수}_Gaebul') :
                        getattr( self.ui, f'rb_{차수}_Gaebul').setChecked(True)
                elif 차수 > 1:
                    if hasattr( self.ui, f'rb_{차수}_Jonghab') :
                        getattr( self.ui, f'rb_{차수}_Jonghab').setChecked(True)


        if len(self.역량항목_DB_All) > 0:
            for 차수 in range ( 총평가차수+1):

                if len(findList:= [ obj for obj in self.역량항목_DB_All if obj.get('구분') == self.평가항목_DB_구분_dict[차수] ]) > 0:
                    obj = findList[0]
                    getattr(self.ui, f"label_Hanmok_{차수}").setText( str(len(obj.get('item_fks',[])) ) )
                    항목list = [ Utils.get_Obj_From_ListDict_by_subDict( self.역량평가사전_DB_All, { 'id': id } )  for id in obj.get('item_fks',[]) ]
                    구분수 = len ( set([ obj.get('구분') for obj in 항목list ]) )
                    getattr(self.ui, f"label_Gubun_{차수}").setText( str(구분수))



    