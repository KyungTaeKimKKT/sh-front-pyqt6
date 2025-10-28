from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import modules.user.utils as utils


from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Ui_Toolbar:
    signal = pyqtSignal(object)

    def __init__(self, MainWindow:QMainWindow , app권한:list):
        self.MainWindow = MainWindow
        self.app권한 = app권한        
        self.tb = self.MainWindow.addToolBar("Tool Bar")
        self.tb.setToolButtonStyle( Qt.ToolButtonStyle.ToolButtonTextBesideIcon )

        self.render()


    def render(self):
        self.render_by_표시명()
        return 
        # self.divNames =list( set( [divName for appDict in self.app권한 if (divName:=appDict.get('div') ) ] ) )
        self.divNames = []
        self.표시명_구분s = []
        self.div = {}
        ### self.app권한이 순서대로 sorting되서 for loop 사용
        for appDict in self.app권한:
            appDict:dict
            if (div:=appDict.get('div')) in self.divNames:
                continue
            else: 
                self.divNames.append(div)

        for appDict in self.app권한:
            if (표시명_구분:=appDict.get('표시명_구분')) in self.표시명_구분s:
                continue
            else: 
                self.표시명_구분s.append(표시명_구분)   

        for div in self.divNames:
            # setattr(self, 
            #         f"Div_{div}", 
            #         QPushButton(
            #             icon=QIcon(f':/toolbar-icons/{div}'),
            #             text=div,  
            #             parent=self.MainWindow ) 
            #         )
            # obj:QPushButton = getattr(self, f"Div_{div}")
            # obj.setIconSize(QSize(16,16))
            # obj.setStyleSheet('border:none;background-color:black;color:white')
            # self.div[div] = obj

            # self.tb.addWidget(obj)


            obj = QToolButton(self.MainWindow)
            setattr(self, f"Div_{div}",QToolButton(self.MainWindow))
            obj : QToolButton = getattr( self, f"Div_{div}" )

            obj.setText(str(div))
            # obj.setIcon( QIcon(f':/toolbar-icons/{div}') )
            self.div[div] = obj
            # setattr(self, f"Div_{div}", obj)
            self.tb.addWidget(obj)

        for div in self.divNames:
            menu = QMenu()
            for appObj in self.app권한:
                if div == appObj['div'] and (appName:= appObj.get('name')) :
                    attrName = f"App___{div}___{appName}"
                    setattr(self, 
                            attrName,
                            QAction( 
                                icon=QIcon(f':/app-icons-{div}/{appName}'),
                                text=appName, 
                                parent=self.MainWindow 
                                ) )
                    qAct:QAction = getattr(self, attrName)
                    qAct.setObjectName(attrName)

                    ### ACTION TRIGGER
                    qAct.triggered.connect(self.MainWindow.slot_toolbar_menuClicked)
                    menu.addAction(qAct )

            # https://www.qtcentre.org/threads/54190-Change-the-background-color-for-the-QAction-s-of-QMenu
            menu.setStyleSheet("""
                                QMenu{
                                    background-color:gray;font-weight:bold;padding:2px 5px 2px 5px;
                                }
                                QMenu::item {
                                    spacing: 3px; /* spacing between menu bar items */
                                    padding: 10px 85px 10px 20px;
                                    background: transparent;
                                }
                                QMenu:selected{
                                    background-color:black;
                                    color:yellow;                                    
                                }                                    
                                """)
            qtoolbtn :QToolButton = self.div[div]
            qtoolbtn.setMenu(menu)
            qtoolbtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        return None
        # icon = QIcon(':/icons/window_icon.png')
        # PB_update = QToolButton(icon= QIcon(':/icons/window_icon.png'),
        #                                   text='Update',  parent=self.MainWindow )
        PB_update = QPushButton(icon=QIcon(':/icons/window_icon.png'),
                                          text='Update',  parent=self.MainWindow )
        PB_update.setIconSize(QSize(48,48))
        PB_update.setStyleSheet('border:none;background-color:black;color:white')
        # PB_update.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)



        
        ### add_SW
        self.add_SW = QAction( icon=QIcon(':/icons/add_SW.png'),
                                        text='Add', parent=self.MainWindow )
        
        self.getDB_SW = QAction(icon=QIcon(':/icons/get_DB.png'),
                                        text='DB list', parent=self.MainWindow )
        

        self.del_SW = QAction( icon= QIcon(':/icons/del_SW.png'),
                                        text='Delete', parent=self.MainWindow )
        
        # self.getDB_SW = QAction(icon=QIcon(utils.get_AbsolutePath(path='/assets/PyQt6/icons/add_SW.png')),
        #                                 text='DB list', parent=self.MainWindow )
        
        menu = QMenu()
        menu.addAction( self.add_SW )
        menu.addAction( self.getDB_SW )
        menu.addAction ( self.del_SW )
        PB_update.setMenu(menu)


        self.tb.addWidget(PB_update)
        # self.tb.addAction( self.add_SW )
        # self.tb.addAction( self.getDB_SW )
        # self.tb.addAction ( self.del_SW )


    

    def render_by_표시명(self):       

        # self.divNames =list( set( [divName for appDict in self.app권한 if (divName:=appDict.get('div') ) ] ) )
        self.divNames = []
        self.표시명_구분s = []
        self.divButtons = {}
        ### self.app권한이 순서대로 sorting되서 for loop 사용
        for appDict in self.app권한:
            appDict:dict
            if (div:=appDict.get('div')) in self.divNames:
                continue
            else: 
                self.divNames.append(div)

        for appDict in self.app권한:
            if (표시명_구분:=appDict.get('표시명_구분')) in self.표시명_구분s:
                continue
            else: 
                self.표시명_구분s.append(표시명_구분)   

        for 표시명_구분 in self.표시명_구분s:
            obj = QToolButton(self.MainWindow)
            attrName = f"표시명_구분_{표시명_구분}"
            setattr(self, attrName,QToolButton(self.MainWindow))
            obj : QToolButton = getattr( self, attrName )

            obj.setText(표시명_구분)
            # obj.setIcon( QIcon(f':/toolbar-icons/{div}') )
            self.divButtons[표시명_구분] = obj
            # setattr(self, f"Div_{div}", obj)
            self.tb.addWidget(obj)

        for 표시명_구분 in self.표시명_구분s:
            menu = QMenu()
            for appObj in self.app권한:
                if INFO.USERID != 1 and not appObj.get('is_Active'):
                    continue
                if 표시명_구분 == appObj['표시명_구분'] and ( 표시명_항목:= appObj.get('표시명_항목')) :
                    divName, appName = appObj['div'], appObj['name']
                    attrName = f"App___{divName}___{appName}"
                    setattr(self, 
                            attrName,
                            QAction( 
                                icon = QIcon(f':/app-icons-{divName}/{appName}'),
                                text = 표시명_항목, 
                                parent = self.MainWindow 
                                ) )
                    qAct:QAction = getattr(self, attrName)
                    qAct.setObjectName(f'appid_{appObj.get("id")}')
                    if INFO.USERID != 1 :
                        qAct.setEnabled( appObj.get('is_Run', False) )

                    ### ACTION TRIGGER
                    qAct.triggered.connect(self.MainWindow.slot_toolbar_menuClicked)
                    menu.addAction(qAct )

            # https://www.qtcentre.org/threads/54190-Change-the-background-color-for-the-QAction-s-of-QMenu
            menu.setStyleSheet("""
                                QMenu{
                                    background-color:gray;font-weight:bold;padding:2px 5px 2px 5px;
                                }
                                QMenu::item {
                                    spacing: 3px; /* spacing between menu bar items */
                                    padding: 10px 85px 10px 20px;
                                    background: transparent;
                                }
                                QMenu:selected{
                                    background-color:black;
                                    color:yellow;                                    
                                }                                    
                                """)
            qtoolbtn :QToolButton = self.divButtons[ 표시명_구분 ]
            qtoolbtn.setMenu(menu)
            qtoolbtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        return None
        # icon = QIcon(':/icons/window_icon.png')
        # PB_update = QToolButton(icon= QIcon(':/icons/window_icon.png'),
        #                                   text='Update',  parent=self.MainWindow )
        PB_update = QPushButton(icon=QIcon(':/icons/window_icon.png'),
                                          text='Update',  parent=self.MainWindow )
        PB_update.setIconSize(QSize(48,48))
        PB_update.setStyleSheet('border:none;background-color:black;color:white')
        # PB_update.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)



        
        ### add_SW
        self.add_SW = QAction( icon=QIcon(':/icons/add_SW.png'),
                                        text='Add', parent=self.MainWindow )
        
        self.getDB_SW = QAction(icon=QIcon(':/icons/get_DB.png'),
                                        text='DB list', parent=self.MainWindow )
        

        self.del_SW = QAction( icon= QIcon(':/icons/del_SW.png'),
                                        text='Delete', parent=self.MainWindow )
        
        # self.getDB_SW = QAction(icon=QIcon(utils.get_AbsolutePath(path='/assets/PyQt6/icons/add_SW.png')),
        #                                 text='DB list', parent=self.MainWindow )
        
        menu = QMenu()
        menu.addAction( self.add_SW )
        menu.addAction( self.getDB_SW )
        menu.addAction ( self.del_SW )
        PB_update.setMenu(menu)


        self.tb.addWidget(PB_update)
        # self.tb.addAction( self.add_SW )
        # self.tb.addAction( self.getDB_SW )
        # self.tb.addAction ( self.del_SW )


    

    # def triggerConnect(self):
    #     self.add_SW.triggered.connect(self.slot_add_SW)
    #     self.getDB_SW.triggered.connect( lambda:self.MainWindow.uiMainW.__get_DB() )

    # def slot_add_SW(self):
    #     # msg = 'add_SW'
    #     # self.signal.emit(msg)

        
        