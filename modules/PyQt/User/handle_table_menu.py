from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

class Handle_Table_Menu:
    """ 
    tableview 에서 오는 signal 처리
    wid_table에 sub class로 상속처리
    signal은 세 종류로,
    	signal_vMenu = QtCore.pyqtSignal(dict)
	    signal_hMenu = QtCore.pyqtSignal(dict)
	    signal_contextMenu = QtCore.pyqtSignal(dict)
    
    """

    def __init__(self, **kwargs):
        pass

    @pyqtSlot(dict)
    def slot_signal_vMenu(self, msg:dict) -> None:


    @pyqtSlot(dict)
    def slot_signal_hMenu(self, msg:dict) -> None:


    
    @pyqtSlot(dict)
    def slot_signal_contextMenu(self, msg:dict) -> None:



