from modules.common_import_v3 import *

from plugin_main.menus.ai.image_roi_editor import Dlg_Image_ROI_Editor


class TableView_Camera설정(Base_Table_View):
    pass

class TableModel_Camera설정(Base_Table_Model):
    def on_api_send_By_Row(self, send_type:str='json'):
        super().on_api_send_By_Row(send_type)

class TableDelegate_Camera설정(Base_Delegate):
    pass

        

class Wid_table_Camera설정( Wid_table_Base_V2 ):

    def setup_table(self):        
        self.view = TableView_Camera설정(self)
        self.model = TableModel_Camera설정(self.view)
        self.delegate = TableDelegate_Camera설정(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)


    def on_disactive(self):
        _isok, _json = APP.API.Send (self.url, {'id':self.selected_dataObj['id'] }, {'is_active':False})
        if _isok:
            self.model.update_row_data(self.selected_rowNo, _json)
            Utils.generate_QMsg_Information(self, title='Camera설정 비활성화', text='Camera설정 비활성화 완료', autoClose= 1000)
        else:
            Utils.generate_QMsg_critical(self, title='Camera설정 비활성화 실패', text='Camera설정 비활성화 실패' )

    def on_rtsp_edit_dialog(self):
        """ system menu 를 click 하는것과 동일하게 처리함 """
        # menu_name = f"AI:Live HI 영상 설정(RTSP)"
        # if menu_name in INFO.MAP_MENU_TO_ACTION:
        #     INFO.MAP_MENU_TO_ACTION[menu_name].trigger()

        if not Utils.QMsg_question( self, title="Live HI 영상 설정(RTSP)", 
            text="""
            Live HI 영상 설정(RTSP)을 진행하시겠습니까?<br>
            Server AI Service 의 설정을 변경하는 것이므로, <br> 
            필히 개발자와 사전에 확인 바랍니다. <br> 
            1:1 scale 이므로 영상이 큽니다. <br>
            
            """
            ):
            return

        editor = self.create_dlg_image_roi_editor()
        editor.exec()

    def on_rtsp_live_view(self):
        if not Utils.QMsg_question( self, title="Live HI 영상 설정(RTSP)", 
            text="""
            Live HI 영상 설정(RTSP)을 진행하시겠습니까?<br>
            Server AI Service 의 설정을 변경하는 것이므로, <br> 
            필히 개발자와 사전에 확인 바랍니다. <br> 
            1:1 scale 이므로 영상이 큽니다. <br>
            
            """
            ):
            return

        editor = Dlg_Image_ROI_Editor(parent=None, api_url= self.url, api_data= copy.deepcopy(self.selected_dataObj))
        editor.exec()




    
    def on_connect_ai_detection_model(self):
        _json = self.base_on_connect_ai_model(task_type='감지')
        if _json:
            dlg = DictTableSelectorDialog(self, datas= _json, attrNames= list( _json[0].keys() ) )
            if dlg.exec():
                dlg_data = dlg.get_selected()
                self.selected_dataObj['detection_model'] = dlg_data['id']
                self.selected_dataObj['detection_model_data'] = dlg_data
                self.model.update_row_data(self.selected_rowNo, self.selected_dataObj)
                self.model._mark_row_as_modified(self.selected_rowNo)

    def on_connect_ai_recognition_model(self):
        _json = self.base_on_connect_ai_model(task_type='인식')
        if _json:
            dlg = DictTableSelectorDialog(self, datas= _json, attrNames= list( _json[0].keys() ) )
            if dlg.exec():
                dlg_data = dlg.get_selected()
                self.selected_dataObj['recognition_model'] = dlg_data['id']
                self.selected_dataObj['recognition_model_data'] = dlg_data
                self.model.update_row_data(self.selected_rowNo, self.selected_dataObj)
                self.model._mark_row_as_modified(self.selected_rowNo)

    def base_on_connect_ai_model(self, task_type:str) -> Optional[list[dict]]:
        ai_model_url = INFO.get_API_URL( app_info = { 'div':'AI', 'name':'AI_Model'})
        if not ai_model_url:
            Utils.generate_QMsg_critical(self, title='AI 모델 연결 실패', text='AI 모델 연결 실패<br> AI 모델 url이 없읍니다.<br>' )
            return None
        
        _isok, _json = APP.API.getlist(f"{ai_model_url}?is_active=True&task_type={task_type}&page_size=0")
        if _isok:
            if _json:
                return _json
            else:
                Utils.generate_QMsg_critical(self, title='AI 모델 연결 실패', text='AI 모델 연결 실패<br> AI 모델 데이터가 없읍니다.<br>' )
                return None
        else:
            Utils.generate_QMsg_critical(self, title='AI 모델 연결 실패', text=f'AI 모델 연결 실패<br> {_json}' )            
            return None

    def on_disconnect_ai_detection_model(self):
        object_name = self.sender().objectName()
        _json = self.base_on_disconnect_ai_model(task_type='감지', object_name= object_name)


    def on_disconnect_ai_recognition_model(self):
        object_name = self.sender().objectName()
        _json = self.base_on_disconnect_ai_model(task_type='인식', object_name= object_name)

    def base_on_disconnect_ai_model(self, task_type:str , object_name:str) -> Optional[dict]:
        """ 예시로, object_dict: {'type': 'fk', 'added_url': 'disconnect_model', 'db_attr_name': 'recognition_model'}
        """

        object_dict = self._parse_objectName(object_name)
        print ( f"object_dict: {object_dict}")
        if not isinstance(object_dict, dict):
            raise ValueError(f"object_name is not valid : Not Dict : {object_name} ---> {object_dict}")

        added_url = object_dict.get('added_url', None)
        dataObj = {'id':self.selected_dataObj.get('id', -1)}
        if object_dict.get('type', None) == 'fk':
            sendData = { object_dict.get('db_attr_name'): None}
        else:
            raise ValueError(f"object_dict type is not valid : {object_dict.get('type', None)}")

        _isok, _json = APP.API.Send_json_with_detail (self.url, added_url=added_url, detail=True, dataObj=dataObj, sendData=sendData)
        if _isok:
            self.model.update_row_data(self.selected_rowNo, _json)
            Utils.generate_QMsg_Information(self, title='AI 모델 비활성화', text=f'AI 모델 비활성화 완료: {task_type}', autoClose= 1000)
            return _json
        else:
            Utils.generate_QMsg_critical(self, title='AI 모델 비활성화 실패', text=f'AI 모델 비활성화 실패: {task_type}<br> {json.dumps( _json, ensure_ascii=False )}' )
            return None


