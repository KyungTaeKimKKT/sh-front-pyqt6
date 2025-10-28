from modules.common_import import *

from modules.PyQt.Tabs.App설정.tables.Wid_table_App설정_App설정_개발자 import (
    TableModel_App설정_App설정_개발자, 
    TableView_App설정_App설정_개발자, 
    TableDelegate_App설정_App설정_개발자,
    Wid_table_App설정_App설정_개발자
)

class TableView_App설정_App설정_관리자(TableView_App설정_App설정_개발자):
    pass


class TableModel_App설정_App설정_관리자(TableModel_App설정_App설정_개발자):
    pass


class TableDelegate_App설정_App설정_관리자(TableDelegate_App설정_App설정_개발자):
    pass



        

class Wid_table_App설정_App설정_관리자( Wid_table_App설정_App설정_개발자 ):   


    def setup_table(self):
        self.model = TableModel_App설정_App설정_관리자(self)
        self.view = TableView_App설정_App설정_관리자(self)
        self.delegate = TableDelegate_App설정_App설정_관리자(self.view)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

    def init_by_parent(self):
        self.init_attributes()
        self.init_ui()
        self.connect_signals()


    # def init_by_parent(self):
    #     self.init_attributes()
    #     self.init_ui()
    #     self.connect_signals()
    #     self.subscribe_gbus()

    # def init_attributes(self):
    #     super().init_attributes()


    # def init_ui(self):
    #     super().init_ui()

    

    # def subscribe_gbus(self):
    #     self.event_bus.subscribe(GBus.TIMER_1MIN, 
    #                              self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
    # def connect_signals(self):
    #     """ signal 연결 """
    #     super().connect_signals()


    # def run(self):
    #     self.url = self.parent().url if hasattr(self.parent(), 'url') else None
    #     if not self.url:
    #         logger.error(f"url이 없읍니다.")

    #     self.table_name = self.objectName() or f"{self.parent().div}_{self.parent().name}_appID_{self.parent().id}"
    #     super().run()

    # def slot_table_config_mode(self, is_config:bool):
    #     super().slot_table_config_mode(is_config)

    # def gbus_timer_1min(self, time_str:str):
    #     """ 매 분:0초마다 호출되는 함수 """
    #     super().gbus_timer_1min(time_str)

    # def slot_api_send_By_Row(self):
    #     """편집 모드: row 일 때 save button 클릭 시 호출되는 함수
    #         bulk가 아니라,  row 단위로 처리함.
    #     """
    #     try:
    #         modified_data = self.model.get_modified_rows_data()
    #         logger.debug(f"modified_data: {modified_data}")
            
    #         # 데이터 준비
    #         data_list = []
    #         files_dict = {}
            
    #         for item in modified_data:
    #             item_copy = item.copy()
                
    #             # 파일 객체 처리
    #             if 'files' in item_copy:
    #                 files = item_copy.pop('files')
    #                 try:
    #                     if files and isinstance(files, dict)  \
    #                         and  isinstance ( files.get('file') , io.BufferedReader) :
    #                             # ID 필드 확인
    #                             item_id = item_copy.get('id') or item_copy.get('pk')
                                
    #                             for field_name, file_obj in files.items():
    #                                 # 파일 키 생성 (ID가 있으면 ID_필드명, 없으면 new_필드명)
    #                                 file_key = f"{field_name}" if field_name else f"new_{field_name}"
                                    
    #                                 # files 딕셔너리에 추가
    #                                 file_name = os.path.basename(file_obj.name)
    #                                 files_dict[file_key] = (file_name, file_obj, 'application/octet-stream')
    #                 except Exception as e:
    #                     logger.error(f"파일 처리 오류: {e}")
    #                     logger.error(f"{traceback.format_exc()}")
                
    #             is_ok, response = APP.API.post(self.url, item_copy, files_dict)
    #             # 파일 객체 닫기 (요청 후)
    #             for file_tuple in files_dict.values():
    #                 try:
    #                     file_tuple[1].close()
    #                 except:
    #                     pass
    #             if is_ok:
    #                 self.model.update_api_response(response)
    #             else:
    #                 logger.error(f"API 요청 실패: {response}")
    #                 QMessageBox.warning(self, "저장 실패", "데이터 저장에 실패했읍니다. 로그를 확인하세요.")
            
    #     except Exception as e:
    #         logger.error(f"slot_api_send_By_Row 오류: {e}")
    #         logger.error(f"{traceback.format_exc()}")
 

    # def slot_api_send_By_Cell(self, editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, _sendData:dict , files:object):
    #     """ 편집 모드: cell일 때, delegate 에서 바로 emit 시, handle(호출)되는 함수 """
    #     super().slot_api_send_By_Cell(editor, model, index,value, id_obj, _sendData , files)


    # def clear_layout(self):
    #     """레이아웃 초기화"""
    #     super().clear_layout()


    # ### apply method들은 run script 형태임
    # def apply_api_datas(self, api_datas:list[dict]):
    #     """ api fectch worker 처리 후 호출되는 함수 """        
    #     super().apply_api_datas(api_datas)


    # def compare_api_datas(self):
    #     """ self.prev_api_datas 와 self.api_datas 비교 하여 render 함"""
    #     super().compare_api_datas()

        

    # ### utils method
  


    # #### setters
    # def set_api_datas(self, api_datas:list[dict]):
    #     self.prev_api_datas = self.api_datas
    #     self.api_datas = api_datas

    # def set_model_datas(self, model_datas:list[list]):
    #     self.prev_model_datas = self.model_datas
    #     self.model_datas = model_datas

    # def set_update_time(self, time_str:Optional[str]=None):
    #     self.update_time_str = time_str or QDateTime.currentDateTime().toString("HH:mm:ss")

    # def set_tableConfigMode(self, is_tableConfigMode:bool):
    #     self.is_tableConfigMode = is_tableConfigMode

    # #### getters
    # def get_table_header(self) -> list[str]:
    #     """ table header 반환 """
    #     if not self.table_header:
    #         #### api_datas를 통해서 생성함
    #         self.table_header = list(self.api_datas[0].keys())
        
    #     return self.table_header
    


    # # def slot_api_send_By_Row(self):
    # #     """편집 모드: row 일 때 save button 클릭 시 호출되는 함수
    # #        bulk with files 로 구현됨.
    # #     """
    # #     modified_data = self.model.get_modified_rows_data()
    # #     logger.debug(f"modified_data: {modified_data}")
        
    # #     # 데이터 준비
    # #     data_list = []
    # #     files_dict = {}
        
    # #     for item in modified_data:
    # #         item_copy = item.copy()
            
    # #         # 파일 객체 처리
    # #         if 'files' in item_copy:
    # #             files = item_copy.pop('files')
    # #             if files:
    # #                 # ID 필드 확인
    # #                 item_id = item_copy.get('id') or item_copy.get('pk')
                    
    # #                 for field_name, file_obj in files.items():
    # #                     # 파일 키 생성 (ID가 있으면 ID_필드명, 없으면 new_필드명)
    # #                     file_key = f"{item_id}_{field_name}" if item_id else f"new_{field_name}"
                        
    # #                     # files 딕셔너리에 추가
    # #                     file_name = os.path.basename(file_obj.name)
    # #                     files_dict[file_key] = (file_name, file_obj, 'application/octet-stream')
            
    # #         # 데이터 리스트에 추가
    # #         data_list.append(item_copy)
        
    # #     # 요청 데이터 준비
    # #     data = {
    # #         'datas': json.dumps(data_list, ensure_ascii=False)
    # #     }
        
    # #     logger.debug(f"data: {data}")
    # #     logger.debug(f"files_dict: {files_dict}")
    # #     # API 요청 보내기
    # #     url = self.url + 'bulk_generate_with_files/'
    # #     is_ok, response = APP.API.post(url, data, files_dict)
        
    # #     # 파일 객체 닫기 (요청 후)
    # #     for file_tuple in files_dict.values():
    # #         try:
    # #             file_tuple[1].close()
    # #         except:
    # #             pass
        
    # #     if is_ok:
    # #         self.model.clear_all_modifications()
    # #     else:
    # #         logger.error(f"API 요청 실패: {response}")
    # #         QMessageBox.warning(self, "저장 실패", "데이터 저장에 실패했읍니다. 로그를 확인하세요.")


    # # def slot_api_send_By_Cell(self, editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, _sendData:dict , files:object):
    # #     """ 편집 모드: cell일 때, delegate 에서 바로 emit 시, handle(호출)되는 함수 """

    # #     if self.url:
    # #         logger.debug(f"files: {files}")
    # #         if files:
    # #             # filename = files.pop('filename')
    # #             # fieldname = files.pop('field_name')
    # #             is_ok, _json = APP.API.Send( self.url, id_obj , {}, files )
    # #         else:
    # #             is_ok, _json = APP.API.Send( self.url, id_obj , _sendData )

    # #         if is_ok:
    # #             try:
    # #                 logger.debug(f" cell update : index : {index} : value : {value}")
    # #                 self.delegate.force_close_editor(editor, model, index, value)
    # #             except Exception as e:
    # #                 logger.error(f"에디터 종료 오류: {e}")
    # #                 logger.error(f"{traceback.format_exc()}")
    # #         else:
    # #             logger.error(f"API 요청 실패: {_json}")
    # #     else:
    # #         logger.error(f"url이 없읍니다.")


