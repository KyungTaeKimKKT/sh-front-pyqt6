from modules.common_import_v2 import *

class TableView_App설정_User관리(Base_Table_View):
    pass

class TableModel_App설정_User관리(Base_Table_Model):
    pass


class TableDelegate_App설정_User관리(Base_Delegate):
    pass

        

class Wid_table_App설정_User관리( Wid_table_Base_V2 ):

    def on_all_lazy_attrs_ready(self):
        super().on_all_lazy_attrs_ready()

    def setup_table(self):
        self.view = TableView_App설정_User관리(self)
        self.model = TableModel_App설정_User관리(self.view)
        self.delegate = TableDelegate_App설정_User관리(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def on_new_row(self):    
        _text = (
            "신규 생성 하시겠습니까?<br><br>"
            "<b>주의사항:</b><br>"
            "1. <b>mail_ID</b>는 중복되면 안됩니다.<br>"
            "2. 저장 시 <b>is_active</b>는 반드시 <b>True</b>로 설정해야 합니다.<br>"
            "3. 신규 생성 시 <b>비밀번호</b>는 임시 비밀번호로 생성됩니다.<br>"
        )
        if Utils.QMsg_question(self, title='신규 생성', text=_text):
            self.model.on_new_row_by_template()

    def on_delete_row(self):        
        self.model.request_delete_row( rowObj=self.selected_dataObj)
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_reset_pwd(self):        
        try:
            isOk, _json = APP.API.getlist( self.url + f'{self.selected_dataObj["id"]}/reset-password/' )
            if isOk:
                Utils.generate_QMsg_Information(self, title='비밀번호 초기화', text='비밀번호 초기화 성공', autoClose= 1000)
            else:
                Utils.generate_QMsg_critical(self, title='비밀번호 초기화 실패', text= json.dumps( _json, ensure_ascii=False ) )
        except Exception as e:
            logger.error(f"on_fileview 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            _text = f" 오류 : {e} <br>오류원인 :{trace} <br> json : {json.dumps( _json, ensure_ascii=False )}<br>"
            Utils.generate_QMsg_critical(None, title='PWD Reset 오류', text=_text)
        self.selected_rows.clear()       
        self.disable_pb_list_when_Not_row_selected()


