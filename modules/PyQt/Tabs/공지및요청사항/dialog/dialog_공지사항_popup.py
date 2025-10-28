from modules.common_import_v2 import *



class Dialog_공지사항_Popup ( QDialog ):
    """ kwargs:
        _obj : 공지사항 dict
        view_type : 'preview' or 'notice' ==> preview : 미리보기, notice : 공지사항 팝업하여 리딩 확인까지
    """
    def __init__(self, parent, url:str|None=None, obj:dict|None=None, view_type:str='preview', **kwargs ):
        super().__init__(parent)
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.obj  = obj or {}
        self.url  = url or f"{INFO.URL_공지사항}{obj.get('id')}/reading-save/"
        self.widget_manager = WidgetManager()

        self.view_type = view_type

        self.setupUi()

        # self.ui.buttonBox.accepted.connect(lambda:self.signal_accepted.emit( self.ui.textEdit.toPlainText()  ))
        self.displayDict = {
            '제목' : self.label_Jemok,
            '공지내용' : self.textBrowser,
            'popup_시작일' : self.dateEdit_from,
            'popup_종료일' : self.dateEdit_To,
        }
        self.is_PB_Ok = False

        if self.obj:
            self._update_dialog( self.obj )

        self.PB_Ok.clicked.connect (self.slot_PB_Ok  )


    #### 4개의 getter
    def _get_제목_value(self) -> str:
        return self.obj.get('제목', '')
    def _get_공지내용_value(self) -> str:
        return self.obj.get('공지내용', '')
    def _get_popup_시작일_value(self) -> QDate:
        return QDate.fromString(self.obj.get('popup_시작일', ''), 'yyyy-MM-dd')
    def _get_popup_종료일_value(self) -> QDate:
        return QDate.fromString(self.obj.get('popup_종료일', ''), 'yyyy-MM-dd')

    def _update_dialog(self, obj:dict ) -> None:
        """
            obj ={'id': 1, '제목': '인트라넷 개발 및 open ☆☆', '시작일': '2024-10-01', '종료일': '2024-11-30', 
            '공지내용': '<p>지금까지 사용하고 있던 기존 인트라넷에서   <br><b style="background-color:black;color:yellow">framework를 변경, 개발하여 open</b>합니다.\n<br>\n<br>\n\n1. 장점\n속도 향상 ( Restful API framework 사용)\n확장성 및 안정성 높음\nUI 등 사용자 편의성 향상\n<br><br>\n \n2. 향후 진행 방향\n생산 전반에 인트라넷 도입을 통한 생산 효율 향상\n사무 업무에 효율성 강화\n<br><br>\n \n3.  개발 영역이 매우 넓은 만큼 충분한 사전 TEST가 되지 못하여, 사용중 오류가 발생할 수 있읍니다.\n    성남)관리팀 김동주 에게 연락주시면 바로 확인하여, 조치할 수 있도록 하겠읍니다.', 
            'is_Popup': True, 'popup_시작일': '2024-05-24', 'popup_종료일': '2024-05-30'}
        """
        for keyName, wid in self.displayDict.items():
            if (value := obj.get(keyName)) is not None:
                self.widget_manager.set_value(wid, value)
            #  Object_Set_Value(wid, obj.get(keyName))

    @pyqtSlot()
    def slot_PB_Ok(self):
        try:
            if self.view_type == 'notice':
                ### init 에서, url은 공지사항 읽음 저장 요청 주소 이미 만들었음.
                _isok, _json =  APP.API.getlist( url=self.url)
                if not _isok:
                    Utils.QMsg_Critical( self, title='공지사항 팝업 Reading 저장 실패', text=f'죄송합니다.<br>공지사항 팝업 Reading 저장 실패<br>{_json}<br>')
                else :
                    if INFO.IS_DEV:
                        print(f"slot_PB_Ok: {_json}")
            self.accept()
        except Exception as e:
            logger.error(f"slot_PB_Ok: {e}")
            traceback.print_exc()

    def closeEvent(self, event):
        if self.view_type == 'notice':
            if self.result() == QDialog.Accepted:
                event.accept()  # OK 버튼 통해 accept한 경우 허용
            else:
                event.ignore()  # 그 외엔 무시
        else:
            event.accept()

    def setupUi(self):
        def get_제목_font():
            font = QFont()
            font.setBold(True)
            font.setPixelSize(64)
            return font
        
        def get_제목_stylesheet():
            return "background-color:black;color:yellow;font-size:32px;font-weight:bold;"
        

        self.setWindowTitle('공지사항 팝업')
        self.resize(795, 953)
        self.main_vLayout = QVBoxLayout(self)
        self.setLayout(self.main_vLayout)

        if not self.obj.get('is_Popup', False):
            self.lb_not_popup = QLabel(' <span style="color: red; font-weight: bold;">⚠️</span> 팝업 공지사항이 아닙니다.', self)
            self.lb_not_popup.setStyleSheet('background-color:black;color:yellow;font-size:32px;font-weight:bold;')
            self.lb_not_popup.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_vLayout.addWidget(self.lb_not_popup)


        main_container = QWidget(self)
        form_layout = QFormLayout()
        main_container.setLayout( form_layout)
        #### 1. 제목
        self.lb_title = QLabel('제목', main_container)
        # self.lb_title.setStyleSheet( get_제목_stylesheet() )

        self.label_Jemok = QLabel( self._get_제목_value(),  main_container)
        self.label_Jemok.setStyleSheet( get_제목_stylesheet() )
        self.label_Jemok.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.label_Jemok.setFont(get_제목_font())
        form_layout.addRow(self.lb_title, self.label_Jemok)


        #### 2. 공지내용    
        self.lb_content = QLabel('공지내용',  main_container)
        self.textBrowser = QTextBrowser( main_container)
        self.textBrowser.setHtml( self._get_공지내용_value())
        form_layout.addRow(self.lb_content, self.textBrowser)

        #### 3. 팝업 기간
        self.lb_period = QLabel('팝업 기간',  main_container)
        container_period = QWidget(main_container)
        c_layout = QHBoxLayout()
        c_layout.setSpacing(10)
        container_period.setLayout( c_layout)
        c_layout.addWidget(QLabel('시작일',  main_container))
        self.dateEdit_from = QDateEdit( self._get_popup_시작일_value(),  main_container)
        c_layout.addWidget(self.dateEdit_from)
        c_layout.addWidget(QLabel(' ~ ',  main_container))
        c_layout.addWidget(QLabel('종료일',  main_container))
        self.dateEdit_To = QDateEdit( self._get_popup_종료일_value(),  main_container)
        c_layout.addWidget(self.dateEdit_To)
        container_period.layout().addStretch()
        form_layout.addRow(self.lb_period, container_period)

        self.main_vLayout.addWidget(main_container)

        #### 4. 확인 버튼
        btn_container = QWidget(main_container)
        btn_c_layout = QHBoxLayout()
        if self.view_type == 'notice':
            lb_notice = QLabel('', btn_container)
            lb_notice.setText("""
                              <span style="background-color:black; color:yellow;">공지사항 확인 후, 
                              <span style="color:red;font-weight:bold;font-size:24px;">[확인 버튼]</span>을 눌러야지만 종료됩니다.'</span>
                              """)
            lb_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_c_layout.addWidget(lb_notice)

        btn_c_layout.addStretch()
        self.PB_Ok = QPushButton('확인',  btn_container)
        btn_c_layout.addWidget(self.PB_Ok)
        btn_container.setLayout( btn_c_layout)

        self.main_vLayout.addWidget(btn_container)



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    test_obj = {'id': 1, '제목': '인트라넷 개발 및 open ☆☆', '시작일': '2024-10-01', '종료일': '2024-11-30', '공지내용': '<p>지금까지 사용하고 있던 기존 인트라넷에서   <br><b style="background-color:black;color:yellow">framework를 변경, 개발하여 open</b>합니다.\n<br>\n<br>\n\n1. 장점\n속도 향상 ( Restful API framework 사용)\n확장성 및 안정성 높음\nUI 등 사용자 편의성 향상\n<br><br>\n \n2. 향후 진행 방향\n생산 전반에 인트라넷 도입을 통한 생산 효율 향상\n사무 업무에 효율성 강화\n<br><br>\n \n3.  개발 영역이 매우 넓은 만큼 충분한 사전 TEST가 되지 못하여, 사용중 오류가 발생할 수 있읍니다.\n    성남)관리팀 김동주 에게 연락주시면 바로 확인하여, 조치할 수 있도록 하겠읍니다.', 'is_Popup': True, 'popup_시작일': '2024-05-24', 'popup_종료일': '2024-05-30'}
    ex = Dialog_공지사항_Popup(None, obj=test_obj)
    sys.exit(app.exec())

    
    
        
