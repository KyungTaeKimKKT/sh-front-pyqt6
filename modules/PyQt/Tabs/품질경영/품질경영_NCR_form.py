import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import urllib
import datetime
import json
from pathlib import Path


# import user_defined compoent
from modules.PyQt.Tabs.품질경영.품질경영_Qcost import QCost
from modules.PyQt.Tabs.품질경영.품질경영_부적합내용 import 부적합내용
from modules.PyQt.component.choice_combobox import Choice_ComboBox
from modules.PyQt.component.combo_lineedit import Combo_LineEdit

from modules.user.api import Api_SH
from modules.PyQt.User.object_value import Object_Get_Value, Object_Set_Value, Object_Diable_Edit, Object_ReadOnly



from modules.PyQt.sub_window.win_elevator_한국정보 import Elevator_한국정보
from modules.PyQt.sub_window.win_form import Win_Form, Win_Form_View

from modules.PyQt.component.image_view import ImageViewer
from modules.PyQt.component.file_upload_listwidget import File_Upload_ListWidget

import modules.user.utils as Utils
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from info import Info_SW as INFO
from stylesheet import StyleSheet as ST


class NumericDelegate(QStyledItemDelegate):
	def createEditor(self, parent, option, index):
		# if index.row() == 0 : return 
		editor = super(NumericDelegate, self).createEditor(parent, option, index)
		if isinstance(editor, QLineEdit):
			reg_ex = QRegExp("^[0-9]*$")
			validator = QRegExpValidator(reg_ex, editor)
			editor.setValidator(validator)
		return editor


class NCR_Form(QMainWindow, Win_Form):
	signal = pyqtSignal(dict)

	def __init__(self,  parent=None,  url:str='', win_title:str='', 
				 inputType:dict={}, title:str='', dataObj:dict={}, skip:list=['id'],
				 ):
		super().__init__(parent, url, win_title, inputType, title, dataObj,skip)
		self.no_Edit =[]
		self.validator_list = ['현장명']
		self.appData = parent.appData
		self.현장명_fks = []	

		self.choices_combo ={
			'고객사' : ['현대', 'OTIS', 'TKE', '기타'],
			'소재'   : ['GI', 'POSMAC', 'SUS', '기타'],
			'단위'   : ['SET', 'EA', 'Sheet', '기타'],
		} 


	def _init_Input_Dict(self):
		""" UI 완료 후 초기화 진행 """
		self.groupBox_분류 = {
			self.radioButton_Gonjong :'공정품',
			self.radioButton_Wan     :'완제품',
			self.radioButton_Gogaek  :'고객불만',
		}
		self.groupBox_구분 = {
			self.radioButton_Sanae : '사내',
			self.radioButton_Saoi : '사외',
			self.radioButton_Claim  : 'claim',
		}

		self.groupBox_조치사항 = {
			self.radioButton_Singu : '신규재작업',
			self.radioButton_Gumto : '검토',
			self.radioButton_Bosu : '보수작업',
		}
		self.groupBox_Radio_Keys = ['구분', '조치사항', '분류']

		self.inputDict = {
			'제목' : self.lineEdit_Bujek,
			'귀책공정' : self.lineEdit_Guichak,
			'발행번호' : self.lineEdit_Balhaeng,
			'발생일자' : self.dateEdit_Balsang,
			'발견자' : self.lineEdit_Balgyun,
			'고객사' : self.comboBox_Gogaksa,
			'작성일자' : self.dateEdit_Jansung,
			'작성자' : self.lineEdit_Jansung,
			'현장명': self.lineEdit_Hyunjang,
			'소재' : self.comboBox_Sojae,
			'의장명' : self.lineEdit_Oijang,
			'OP'    : self.lineEdit_OP,
			'자재명' : self.lineEdit_Jajae,
			'수량' : self.spinBox_Surang,
			'단위' : self.comboBox_Danwi,
			'부적합내용' : self.tableWidget_Bujek,
			'부적합상세' : self.textEdit_Bujekhab,
			'임시조치방안': self.textEdit_ImsiJochi,
			'일정사항' : self.textEdit_Iljung,
			'품질비용' : self.tableWidget_Qcost,
		}
		self.groupBoxs = [self.groupBox_분류, self.groupBox_구분, self.groupBox_조치사항]
		self.combo_LineEdits = [self.comboBox_Gogaksa, self.comboBox_Sojae,self.comboBox_Danwi, ]
	
	def UI(self):
		self.setObjectName("NCR")
		self.resize(1080, 1261)
		self.centralwidget = QtWidgets.QWidget(self)
		self.centralwidget.setObjectName("centralwidget")
		self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
		self.verticalLayout_2.setObjectName("verticalLayout_2")
		self.frame_1 = QtWidgets.QFrame(self.centralwidget)
		self.frame_1.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame_1.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frame_1.setObjectName("frame_1")
		self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_1)
		self.horizontalLayout_2.setObjectName("horizontalLayout_2")
		self.label = QtWidgets.QLabel(self.frame_1)
		font = QtGui.QFont()
		font.setPointSize(24)
		font.setBold(True)
		font.setWeight(75)
		self.label.setFont(font)
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		self.label.setObjectName("label")
		self.horizontalLayout_2.addWidget(self.label)
		self.groupBox_Bunru = QtWidgets.QGroupBox(self.frame_1)
		self.groupBox_Bunru.setObjectName("groupBox_Bunru")
		self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_Bunru)
		self.horizontalLayout.setObjectName("horizontalLayout")
		self.radioButton_Gonjong = QtWidgets.QRadioButton(self.groupBox_Bunru)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Gonjong.setFont(font)
		self.radioButton_Gonjong.setObjectName("radioButton_Gonjong")
		self.horizontalLayout.addWidget(self.radioButton_Gonjong)
		self.radioButton_Wan = QtWidgets.QRadioButton(self.groupBox_Bunru)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Wan.setFont(font)
		self.radioButton_Wan.setObjectName("radioButton_Wan")
		self.horizontalLayout.addWidget(self.radioButton_Wan)
		self.radioButton_Gogaek = QtWidgets.QRadioButton(self.groupBox_Bunru)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Gogaek.setFont(font)
		self.radioButton_Gogaek.setObjectName("radioButton_Gogaek")
		self.horizontalLayout.addWidget(self.radioButton_Gogaek)
		self.horizontalLayout_2.addWidget(self.groupBox_Bunru)
		self.groupBox_Gubun = QtWidgets.QGroupBox(self.frame_1)
		self.groupBox_Gubun.setObjectName("groupBox_Gubun")
		self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.groupBox_Gubun)
		self.horizontalLayout_4.setObjectName("horizontalLayout_4")
		self.radioButton_Sanae = QtWidgets.QRadioButton(self.groupBox_Gubun)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Sanae.setFont(font)
		self.radioButton_Sanae.setObjectName("radioButton_Sanae")
		self.horizontalLayout_4.addWidget(self.radioButton_Sanae)
		self.radioButton_Saoi = QtWidgets.QRadioButton(self.groupBox_Gubun)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Saoi.setFont(font)
		self.radioButton_Saoi.setObjectName("radioButton_Saoi")
		self.horizontalLayout_4.addWidget(self.radioButton_Saoi)
		self.radioButton_Claim = QtWidgets.QRadioButton(self.groupBox_Gubun)
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.radioButton_Claim.setFont(font)
		self.radioButton_Claim.setObjectName("radioButton_Claim")
		self.horizontalLayout_4.addWidget(self.radioButton_Claim)
		self.horizontalLayout_2.addWidget(self.groupBox_Gubun)
		self.verticalLayout_2.addWidget(self.frame_1)
		self.frame_2 = QtWidgets.QFrame(self.centralwidget)
		self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frame_2.setObjectName("frame_2")
		self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_2)
		self.horizontalLayout_3.setObjectName("horizontalLayout_3")
		self.label_2 = QtWidgets.QLabel(self.frame_2)
		self.label_2.setObjectName("label_2")
		self.horizontalLayout_3.addWidget(self.label_2)
		self.lineEdit_Bujek = QtWidgets.QLineEdit(self.frame_2)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(2)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.lineEdit_Bujek.sizePolicy().hasHeightForWidth())
		self.lineEdit_Bujek.setSizePolicy(sizePolicy)
		self.lineEdit_Bujek.setObjectName("lineEdit_Bujek")
		self.horizontalLayout_3.addWidget(self.lineEdit_Bujek)
		self.label_3 = QtWidgets.QLabel(self.frame_2)
		self.label_3.setObjectName("label_3")
		self.horizontalLayout_3.addWidget(self.label_3)
		self.lineEdit_Guichak = QtWidgets.QLineEdit(self.frame_2)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(1)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.lineEdit_Guichak.sizePolicy().hasHeightForWidth())
		self.lineEdit_Guichak.setSizePolicy(sizePolicy)
		self.lineEdit_Guichak.setObjectName("lineEdit_Guichak")
		self.horizontalLayout_3.addWidget(self.lineEdit_Guichak)
		self.verticalLayout_2.addWidget(self.frame_2)
		self.frame_3 = QtWidgets.QFrame(self.centralwidget)
		self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frame_3.setObjectName("frame_3")
		self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_3)
		self.verticalLayout.setObjectName("verticalLayout")
		self.frame_3_1 = QtWidgets.QFrame(self.frame_3)
		self.frame_3_1.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.frame_3_1.setFrameShadow(QtWidgets.QFrame.Raised)
		self.frame_3_1.setObjectName("frame_3_1")
		self.gridLayout_2 = QtWidgets.QGridLayout(self.frame_3_1)
		self.gridLayout_2.setObjectName("gridLayout_2")
		self.label_17 = QtWidgets.QLabel(self.frame_3_1)
		self.label_17.setObjectName("label_17")
		self.gridLayout_2.addWidget(self.label_17, 4, 0, 1, 1)
		### Combo_LineEdit
		self.comboBox_Danwi = Combo_LineEdit(self.frame_3_1)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.comboBox_Danwi.sizePolicy().hasHeightForWidth())
		self.comboBox_Danwi.setSizePolicy(sizePolicy)
		self.comboBox_Danwi.setObjectName("comboBox_Danwi")
		self.gridLayout_2.addWidget(self.comboBox_Danwi, 4, 7, 1, 1)
		### Combo_LineEdit 
		self.comboBox_Sojae = Combo_LineEdit(self.frame_3_1)
		self.comboBox_Sojae.setObjectName("comboBox_Sojae")
		self.gridLayout_2.addWidget(self.comboBox_Sojae, 2, 6, 1, 2)
		self.lineEdit_Oijang = QtWidgets.QLineEdit(self.frame_3_1)
		self.lineEdit_Oijang.setObjectName("lineEdit_Oijang")
		self.gridLayout_2.addWidget(self.lineEdit_Oijang, 3, 2, 1, 3)
		self.label_6 = QtWidgets.QLabel(self.frame_3_1)
		self.label_6.setObjectName("label_6")
		self.gridLayout_2.addWidget(self.label_6, 0, 5, 1, 1)
		self.label_10 = QtWidgets.QLabel(self.frame_3_1)
		self.label_10.setObjectName("label_10")
		self.gridLayout_2.addWidget(self.label_10, 3, 5, 1, 1)
		self.label_9 = QtWidgets.QLabel(self.frame_3_1)
		self.label_9.setObjectName("label_9")
		self.gridLayout_2.addWidget(self.label_9, 1, 5, 1, 1)
		self.label_15 = QtWidgets.QLabel(self.frame_3_1)
		self.label_15.setObjectName("label_15")
		self.gridLayout_2.addWidget(self.label_15, 2, 5, 1, 1)
		self.label_5 = QtWidgets.QLabel(self.frame_3_1)
		self.label_5.setObjectName("label_5")
		self.gridLayout_2.addWidget(self.label_5, 0, 0, 1, 1)
		self.label_7 = QtWidgets.QLabel(self.frame_3_1)
		self.label_7.setObjectName("label_7")
		self.gridLayout_2.addWidget(self.label_7, 1, 0, 1, 1)
		self.dateEdit_Jansung = QtWidgets.QDateEdit(self.frame_3_1)
		self.dateEdit_Jansung.setObjectName("dateEdit_Jansung")
		self.gridLayout_2.addWidget(self.dateEdit_Jansung, 1, 4, 1, 1)
		### 고객사 combo : Combo_LineEdit
		self.comboBox_Gogaksa =  Combo_LineEdit(self.frame_3_1)
		self.comboBox_Gogaksa.setObjectName("comboBox_Gogaksa")
		self.gridLayout_2.addWidget(self.comboBox_Gogaksa, 1, 2, 1, 1)
		self.dateEdit_Balsang = QtWidgets.QDateEdit(self.frame_3_1)
		self.dateEdit_Balsang.setObjectName("dateEdit_Balsang")
		self.gridLayout_2.addWidget(self.dateEdit_Balsang, 0, 4, 1, 1)
		self.lineEdit_Hyunjang = QtWidgets.QLineEdit(self.frame_3_1)
		self.lineEdit_Hyunjang.setObjectName("lineEdit_Hyunjang")
		self.gridLayout_2.addWidget(self.lineEdit_Hyunjang, 2, 2, 1, 3)
		self.label_18 = QtWidgets.QLabel(self.frame_3_1)
		self.label_18.setObjectName("label_18")
		self.gridLayout_2.addWidget(self.label_18, 4, 5, 1, 1)
		self.lineEdit_OP = QtWidgets.QLineEdit(self.frame_3_1)
		self.lineEdit_OP.setObjectName("lineEdit_OP")
		self.gridLayout_2.addWidget(self.lineEdit_OP, 3, 6, 1, 2)
		self.label_4 = QtWidgets.QLabel(self.frame_3_1)
		self.label_4.setObjectName("label_4")
		self.gridLayout_2.addWidget(self.label_4, 0, 3, 1, 1)
		self.label_16 = QtWidgets.QLabel(self.frame_3_1)
		self.label_16.setObjectName("label_16")
		self.gridLayout_2.addWidget(self.label_16, 3, 0, 1, 1)
		self.lineEdit_Balhaeng = QtWidgets.QLineEdit(self.frame_3_1)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.lineEdit_Balhaeng.sizePolicy().hasHeightForWidth())
		self.lineEdit_Balhaeng.setSizePolicy(sizePolicy)
		self.lineEdit_Balhaeng.setObjectName("lineEdit_Balhaeng")
		self.gridLayout_2.addWidget(self.lineEdit_Balhaeng, 0, 2, 1, 1)
		self.label_14 = QtWidgets.QLabel(self.frame_3_1)
		self.label_14.setObjectName("label_14")
		self.gridLayout_2.addWidget(self.label_14, 2, 0, 1, 1)
		self.lineEdit_Jajae = QtWidgets.QLineEdit(self.frame_3_1)
		self.lineEdit_Jajae.setObjectName("lineEdit_Jajae")
		self.gridLayout_2.addWidget(self.lineEdit_Jajae, 4, 2, 1, 3)
		self.label_8 = QtWidgets.QLabel(self.frame_3_1)
		self.label_8.setObjectName("label_8")
		self.gridLayout_2.addWidget(self.label_8, 1, 3, 1, 1)
		self.spinBox_Surang = QtWidgets.QSpinBox(self.frame_3_1)
		self.spinBox_Surang.setMaximum(10000)
		self.spinBox_Surang.setObjectName("spinBox_Surang")
		self.gridLayout_2.addWidget(self.spinBox_Surang, 4, 6, 1, 1)
		self.lineEdit_Jansung = QtWidgets.QLineEdit(self.frame_3_1)
		self.lineEdit_Jansung.setObjectName("lineEdit_Jansung")
		self.gridLayout_2.addWidget(self.lineEdit_Jansung, 1, 6, 1, 2)
		self.lineEdit_Balgyun = QtWidgets.QLineEdit(self.frame_3_1)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.lineEdit_Balgyun.sizePolicy().hasHeightForWidth())
		self.lineEdit_Balgyun.setSizePolicy(sizePolicy)
		self.lineEdit_Balgyun.setObjectName("lineEdit_Balgyun")
		self.gridLayout_2.addWidget(self.lineEdit_Balgyun, 0, 6, 1, 2)
		self.verticalLayout.addWidget(self.frame_3_1)
		self.gridLayout_1 = QtWidgets.QGridLayout()
		self.gridLayout_1.setObjectName("gridLayout_1")
		self.label_19 = QtWidgets.QLabel(self.frame_3)
		self.label_19.setObjectName("label_19")
		self.gridLayout_1.addWidget(self.label_19, 0, 0, 1, 1)
		self.textEdit_Bujekhab = QtWidgets.QTextEdit(self.frame_3)
		self.textEdit_Bujekhab.setObjectName("textEdit_Bujekhab")
		self.gridLayout_1.addWidget(self.textEdit_Bujekhab, 3, 0, 1, 1)
		self.label_21 = QtWidgets.QLabel(self.frame_3)
		self.label_21.setObjectName("label_21")
		self.gridLayout_1.addWidget(self.label_21, 2, 0, 1, 1)

		#### import 부적합내용
		self.tableWidget_Bujek = 부적합내용(self.frame_3)
		self.tableWidget_Bujek.run()

		self.gridLayout_1.addWidget(self.tableWidget_Bujek, 1, 0, 1, 1)
		self.verticalLayout.addLayout(self.gridLayout_1)


		self.gridLayout_3 = QtWidgets.QGridLayout()
		self.gridLayout_3.setObjectName("gridLayout_3")
		self.textEdit_Iljung = QtWidgets.QTextEdit(self.frame_3)
		self.textEdit_Iljung.setObjectName("textEdit_Iljung")
		self.gridLayout_3.addWidget(self.textEdit_Iljung, 3, 0, 1, 1)
		self.textEdit_ImsiJochi = QtWidgets.QTextEdit(self.frame_3)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(2)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.textEdit_ImsiJochi.sizePolicy().hasHeightForWidth())
		self.textEdit_ImsiJochi.setSizePolicy(sizePolicy)
		self.textEdit_ImsiJochi.setObjectName("textEdit_ImsiJochi")
		self.gridLayout_3.addWidget(self.textEdit_ImsiJochi, 1, 0, 1, 1)
		self.groupBox_Jochi = QtWidgets.QGroupBox(self.frame_3)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
		sizePolicy.setHorizontalStretch(1)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.groupBox_Jochi.sizePolicy().hasHeightForWidth())
		self.groupBox_Jochi.setSizePolicy(sizePolicy)
		self.groupBox_Jochi.setObjectName("groupBox_Jochi")
		self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_Jochi)
		self.verticalLayout_3.setObjectName("verticalLayout_3")
		self.radioButton_Singu = QtWidgets.QRadioButton(self.groupBox_Jochi)
		self.radioButton_Singu.setObjectName("radioButton_Singu")
		self.verticalLayout_3.addWidget(self.radioButton_Singu)
		self.radioButton_Gumto = QtWidgets.QRadioButton(self.groupBox_Jochi)
		self.radioButton_Gumto.setObjectName("radioButton_Gumto")
		self.verticalLayout_3.addWidget(self.radioButton_Gumto)
		self.radioButton_Bosu = QtWidgets.QRadioButton(self.groupBox_Jochi)
		self.radioButton_Bosu.setObjectName("radioButton_Bosu")
		self.verticalLayout_3.addWidget(self.radioButton_Bosu)
		self.gridLayout_3.addWidget(self.groupBox_Jochi, 1, 1, 1, 1)
		self.label_23 = QtWidgets.QLabel(self.frame_3)
		self.label_23.setObjectName("label_23")
		self.gridLayout_3.addWidget(self.label_23, 2, 0, 1, 1)
		self.label_22 = QtWidgets.QLabel(self.frame_3)
		self.label_22.setObjectName("label_22")
		self.gridLayout_3.addWidget(self.label_22, 0, 0, 1, 1)

		# self.tableWidget_Qcost = QtWidgets.QTableWidget(self.frame_3)
		# self.tableWidget_Qcost.setObjectName("tableWidget_Qcost")
		# self.tableWidget_Qcost.setColumnCount(1)
		# self.tableWidget_Qcost.setRowCount(7)
		# item = QtWidgets.QTableWidgetItem()
		# font = QtGui.QFont()
		# font.setBold(True)
		# font.setWeight(75)
		# item.setFont(font)
		# item.setBackground(QtGui.QColor(249, 240, 107))
		# self.tableWidget_Qcost.setVerticalHeaderItem(0, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(1, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(2, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(3, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(4, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(5, item)
		# item = QtWidgets.QTableWidgetItem()
		# self.tableWidget_Qcost.setVerticalHeaderItem(6, item)
		# item = QtWidgets.QTableWidgetItem()
		# item.setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
		# self.tableWidget_Qcost.setHorizontalHeaderItem(0, item)

		self.tableWidget_Qcost = QCost(self)
		self.tableWidget_Qcost.run()
		self.gridLayout_3.addWidget(self.tableWidget_Qcost, 3, 1, 1, 1)

		self.label_11 = QtWidgets.QLabel(self.frame_3)
		self.label_11.setAlignment(QtCore.Qt.AlignCenter)
		self.label_11.setObjectName("label_11")
		self.gridLayout_3.addWidget(self.label_11, 2, 1, 1, 1)
		self.verticalLayout.addLayout(self.gridLayout_3)
		self.verticalLayout_2.addWidget(self.frame_3)

		### button 추가
		hbox = QHBoxLayout()
		hbox.addStretch()

		self.PB_save = QPushButton('Save')
		self.PB_save.setEnabled(False)
		self.PB_cancel = QPushButton('Cancel')
		hbox.addWidget(self.PB_save)
		hbox.addWidget(self.PB_cancel)
		self.verticalLayout.addLayout(hbox)
		### button 추가 완료

		self.setCentralWidget(self.centralwidget)


		self.menubar = QtWidgets.QMenuBar(self)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 1080, 28))
		self.menubar.setObjectName("menubar")
		self.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(self)
		self.statusbar.setObjectName("statusbar")
		self.setStatusBar(self.statusbar)

	def retranslateUi(self)	:
		self.setWindowTitle( "MainWindow")
		self.label.setText( "부적합 보고서(NCR)")
		self.groupBox_Bunru.setTitle( "분류")
		self.radioButton_Gonjong.setText( "공정품")
		self.radioButton_Wan.setText( "완제품")
		self.radioButton_Gogaek.setText( "고객불만")
		self.groupBox_Gubun.setTitle( "구분")
		self.radioButton_Sanae.setText( "사내")
		self.radioButton_Saoi.setText( "사외")
		self.radioButton_Claim.setText( " CLAIM")
		self.label_2.setText( "부적합 내용")
		self.label_3.setText( "귀책 공정")
		self.label_17.setText( "자재명")
		self.label_6.setText( "발견자")
		self.label_10.setText( "OP")
		self.label_9.setText( "작성자")
		self.label_15.setText( "소재")
		self.label_5.setText( "발행번호")
		self.label_7.setText( "고객사")
		self.label_18.setText( "수량")
		self.label_4.setText( "발생일자")
		self.label_16.setText( "의장명")
		self.label_14.setText( "현장명")
		self.label_8.setText( "작성일자")
		self.label_19.setText( "1. 부적합 내용")
		self.label_21.setText( "2. 부적합 상세")

		self.groupBox_Jochi.setTitle( "조치사항")
		self.radioButton_Singu.setText( "신규재작업")
		self.radioButton_Gumto.setText( "검토")
		self.radioButton_Bosu.setText( "보수작업")
		self.label_23.setText( "4. 재작업 및 교체 일정 사항 통보")
		self.label_22.setText( "3. 임시 조치방안(품질부서에서 불만 확인 후 임시조치사항을 기록합니다)")

		self.label_11.setText( "예상 품질비용 (실패비용: 단위 원)")

	def user_defined_ui_setting(self):

		# delegate = NumericDelegate(self.tableWidget_Qcost)
		# self.tableWidget_Qcost.setItemDelegate(delegate)

		for (key, input) in self.inputDict.items():
			if isinstance(input, QDateEdit ):
				if not self.dataObj : input.setDate(QDate.currentDate() )
			if isinstance(input, QSpinBox ):
				if not self.dataObj : input.setRange(0, 10000)
			if isinstance(input , Combo_LineEdit) :
				input.items = self.choices_combo[key]
				input._render()
				if key == '고객사' : input._setMaximumWidth(120)
				else : input._setMaximumWidth(60)

			if key in ['작성자', '작성일자']:
				if isinstance( input, QLineEdit ):
					input.setText(INFO.USERNAME)
				input.setReadOnly(True)
			if key in ['발생일자']:
				if isinstance ( input, QDateEdit):
					input.setMaximumDate(QDate.currentDate() )

		#### Radio button  초기값 설정
		self.radioButton_Gonjong.setChecked(True)
		self.radioButton_Sanae.setChecked(True)
		self.radioButton_Singu.setChecked(True)
		
		for key in self.no_Edit:
			inputObj = self.inputDict[key]
			Object_ReadOnly(input=inputObj, value = self.dataObj[key])
			

	def run(self):

		self.UI()  
		self.retranslateUi()      
		self._init_Input_Dict()
		self.user_defined_ui_setting()
		self.show()
		self.TriggerConnect()

		for key in self.validator_list:
			self.inputDict[key].textChanged.connect(self.check_validator)
	
	##### Trigger Func. #####
	def TriggerConnect(self):
		super().TriggerConnect()
		# self.tableWidget_Qcost.itemChanged.connect(self.slot_calculate_Qcost)
		pass

	#### 😀 구분 combo box change ==> gettext ==> if mod: elevator_info run()
	def slot_calculate_Qcost(self, index:QModelIndex):
		row, col = index.row(), index.column()
		합계 = 0
		for row in range (self.tableWidget_Qcost.rowCount() ):
			if row == 0 : continue
			txt = '' if (item:=self.tableWidget_Qcost.item(row, 0) ) is None else item.text()
			합계 += int(txt) if txt else 0


	def slot_changed_choices_GUBUN(self):
		if 'mod' in self.sender().currentText().lower():
			self.elevator_info = Elevator_한국정보(self)
			self.elevator_info.run()
			self.elevator_info.signal.connect(self.slot_elevator_info_siganl)
		else :
			if getattr(self, 'elevator_info',None) : 
				self.elevator_info.close()


	def slot_elevator_info_siganl(self, msg:dict):

		self.현장명_fks =[]
		value_건물명 = ''
		value_수량 = 0
		value_운행층수 = 0
		for info in msg.get('select'):			
			for (key, value) in info.items():
				match key :
					case '건물명': 
						value_건물명 += value
					case '수량':
						value_수량 += value						
					case '운행층수':
						value_운행층수 += value
					case 'id':
						self.현장명_fks.append(value)

		Object_Set_Value(input=self.inputDict['현장명'], value=value_건물명)	
		Object_Set_Value(input=self.inputDict['el수량'], value=value_수량 )
		Object_Set_Value(input=self.inputDict['운행층수'], value=value_운행층수 )


	def func_save(self):		
		for key in self.inputType.keys():
			match key:
				case 'id'|'의뢰파일':
					continue
				case '작성자_fk':
					self.result['작성자_fk'] = INFO.USERID
				### groubox radiobuttons
				case key if key in self.groupBox_Radio_Keys:
					self.result[key] = self._getValue_from_groupBox_radioButtons( getattr(self, f"groupBox_{key}") )

				case _:
					self.result[key] = self._get_value(key)
		
		# self.result['현장명_fk'] = self.현장명_fks if self.현장명_fks else []
		# self.result['등록일'] = QDateTime.currentDateTime().toString(INFO.DateTimeFormat )
		self.result_files = []
		self.result['품질비용_fk'] =  self.tableWidget_Qcost.get_Api_data() 
		self.result['부적합내용_fks'] =  self.tableWidget_Bujek.get_Api_data() 

		####😀 key는  API DATA에 따라서, 
		# if (의뢰file := self.wid_fileUpload._getValue() ):
		# 	exist_DB_ids:list = 의뢰file.get('exist_DB_id')
		# 	if len(exist_DB_ids):
		# 		self.result['의뢰file_fks_json'] = json.dumps( exist_DB_ids )
		# 	else:
		# 		self.result['의뢰file_삭제'] = True
				
		# 	if ( 의뢰file_fks := 의뢰file.get('new_DB') ):
		# 		#### 😀 change for api m2m field
		# 		self.result_files.extend( self._conversion_to_api_field( 
		# 									change_key ='의뢰file', original= 의뢰file_fks ) )
		if Utils.compare_dict(self.dataObj, self.result) :
			reply = QMessageBox.warning(self, "저장확인", "변경사항이 없읍니다.", QMessageBox.Yes, QMessageBox.Yes )
			return

		else:
			self.result['품질비용_fk'] = json.dumps( self.result['품질비용_fk'] )
			self.result['부적합내용_fks'] = json.dumps ( self.tableWidget_Bujek.get_Api_data() )
			is_ok, _ = APP.API.Send( self.url, self.dataObj, self.result, self.result_files)
			if is_ok:
				self.signal.emit({'action':'update'})
				self.close()

	def _getValue_from_groupBox_radioButtons(self, obj:dict) -> str:
		for (key, value) in obj.items():
			key:QRadioButton
			if key.isChecked():
				return value
			
	def _setValue_from_groupBox_radioButtons(self, obj:dict, dataValue:str, is_ReadOnly:bool=False) -> None:
		for (key, value) in obj.items():
			key:QRadioButton
			if value == dataValue:
				key.setChecked(True)
			else:
				if (is_ReadOnly) : key.setDisabled(True)
				
	
	def _conversion_to_api_field(self, change_key:str, original:list) -> list:
		"""
			😀change tuple value 
			original : [('첨부file_fks', <_io.BufferedReader name='/home/kkt/Downloads.xlsx'>)]
		"""
		result = []
		for item in original:
			temp = list(item)
			temp[0]  = change_key
			result.append(tuple(temp) )
		return result

	## 😀 form 의 save method에서 기본적으로 get_value ==> set_value로..
	def editMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == '작성자_fk': 				
				continue
			if key in self.groupBox_Radio_Keys :
				self._setValue_from_groupBox_radioButtons( getattr(self, f"groupBox_{key}"), 
											  self.dataObj.get(key) )
			try:
				Object_Set_Value(input=self.inputDict[key], value = self.dataObj[key])
			except Exception as e:

			# if isinstance(  inputObj, 고객사_Widget) :
			# 	inputObj.setValue(self.dataObj[key] )
		
		self.tableWidget_Bujek.app_DB_data = self.dataObj.get('contents_fks')
		self.tableWidget_Bujek.run()
		self.tableWidget_Qcost.app_DB_data = self.dataObj.get('품질비용')
		self.tableWidget_Qcost.run()
		###😀 api data에 따라서.
		if (fNames := self.dataObj.get('의뢰file_fks', None) ) :
			self.wid_fileUpload._setValue(fNames)
	
	## 😀 form 의 edit method에서 기본적으로 set_value 에서 readonly로
	#  Object_Set_Valuee ==> Object_ReadOnly로.. button setVisible(False)
	def viewMode(self):
		for key in self.inputType.keys():
			if key in self.skip: continue
			if key == '작성자_fk': 				
				continue
			if key in self.groupBox_Radio_Keys :
				self._setValue_from_groupBox_radioButtons( getattr(self, f"groupBox_{key}"), 
														self.dataObj.get(key) ,
														True)
			try:
				Object_ReadOnly(input=self.inputDict[key], value = self.dataObj[key])
			except Exception as e:


		self.tableWidget_Bujek.app_DB_data = self.dataObj.get('contents_fks')
		self.tableWidget_Bujek._setReadOnly()
		self.tableWidget_Bujek.run()

		self.tableWidget_Qcost.app_DB_data = self.dataObj.get('품질비용')
		self.tableWidget_Qcost._setReadOnly()
		self.tableWidget_Qcost.run()
		# if (fNames := self.dataObj.get('의뢰file_fks', None) ) :
		# 	self.wid_fileUpload._setValue(fNames)
		# self.wid_fileUpload._setReadOnly()
		
		self.PB_save.setVisible(False)
		self.PB_cancel.setText('확인')

			

	def api_send(self):
		if bool(self.dataObj):
			ID = self.dataObj.get('id', -1)

			if ID > 0:
				is_ok, res_json = APP.API.patch(url= self.url+ str(ID) +'/',
												data=self.result,
												files=self.result_files)
			else:
				is_ok, res_json = APP.API.post(url= self.url,
								data=self.result ,
								files= self.result_files)
		else:
			is_ok, res_json = APP.API.post(url= self.url,
											data=self.result ,
											files= self.result_files)
			
		if is_ok:
			self.signal.emit({'action':'update'})
			self.close()
		else:
			toast = User_Toast(self, text='server not connected', style='ERROR')

	### Hard-coding 😀😀
	def _gen_by_key(self, key:str='', value=None, label:object='', input:object=None):
		match key:
			case '현장명':
				if isinstance(input, QLineEdit ):
					input.setPlaceholderText("제목을 넣으세요(필수★)")
					# input.textChanged.connect(self.check_validator)
			# case '일자':
			# 	if isinstance(input, QtWidgets.QDateEdit ):
			# 		input.setDate(QDate.currentDate())
			
			case _:
				pass				
			
		self.inputDict[key] = input

		return (label, input)
	
	def check_validator(self) -> bool:
		for key in self.validator_list:
			if self._get_value( key ):
				self.inputDict[key].setStyleSheet(ST.edit_)
				self.PB_save.setEnabled(True)
				return True
		self.PB_save.setEnabled(False)
		return False
	


