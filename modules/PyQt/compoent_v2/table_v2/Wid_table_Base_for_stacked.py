from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import inspect
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from modules.PyQt.compoent_v2.table_v2.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table_v2.Base_Delegate import Base_Delegate
from modules.mixin.lazyparentattrmixin import LazyParentAttrMixin
from modules.PyQt.Tabs.plugins.ui.Wid_config_mode import Wid_Config_Mode
from modules.PyQt.Tabs.plugins.ui.Wid_header import Wid_Header

from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode
from modules.PyQt.compoent_v2.custom_상속.custom_PB import CustomPushButton

from functools import partial
import json, os, copy, time
from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
from info import Info_SW as INFO
from config import Config as APP
import modules.user.utils as Utils
import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.PyQt.compoent_v2.table_v2.Wid_table_config_mode import Dialog_TableConfigMode

class Mixin_PB_Info:
    def __init__(self):
        self._default_map_pb_to_generate_info = {
            'PB_New':           {'title': '신규 생성', 
                                 'tooltip': '첫번째 줄에 신규 생성합니다.',
                                 'slot' : self.on_new_row,
                                 'disable_not_selected': False
                                 },
            'PB_copy_new_row':  {'title': '복사 생성', 
                                 'tooltip': '선택한 줄에 복사 상단에 신규 생성합니다.',
                                 'slot' : self.on_copy_new_row,
                                 'disable_not_selected': True
                                 },
            'PB_User_Select': {'title': '사용자 선택', 
                                 'tooltip': '사용자 선택',
                                 'slot' : self.on_user_select,
                                'disable_not_selected': True
                                 },
            'PB_Delete': {'title': '삭제', 
                                 'tooltip': '삭제',
                                 'slot' : self.on_delete_row,
                                 'disable_not_selected': True
                                 },
            '파일다운로드':  {'title': 'Claim 파일다운로드', 
                    'tooltip': 'Claim 파일다운로드',
                    'slot' : self.on_file_download, 
                    'disable_not_selected': True
                    },
            '파일보기':  {'title': 'Claim 파일보기', 
                    'tooltip': 'Claim 파일보기',
                    'slot' : self.on_file_view, 
                    'disable_not_selected': True
                    },
            '지도보기':  {'title': '지도보기', 
                    'tooltip': '지도보기',
                    'slot' : self.on_map_view, 
                    'disable_not_selected': True
                    },
            'Excel_Export_User':  {'title': 'Excel 내보내기', 
                    'tooltip': 'Excel 내보내기',
                    'slot' : self.on_excel_export, 
                    'disable_not_selected': True
                    },
            'Excel_Export_Admin':  {'title': 'Excel 내보내기', 
                    'tooltip': 'Excel 내보내기(관리자) ✅조회된 모든 data를 내보냅니다.',
                    'slot' : self.on_excel_export, 
                    'disable_not_selected': True
                    },
            
        }

    def create_pb_info(self, pb_names:list[str]) -> dict:
        return { pb_name: self._default_map_pb_to_generate_info[pb_name] for pb_name in pb_names if pb_name in self._default_map_pb_to_generate_info }

    def update_pb_info(self, pb_info:dict) -> dict:
        self.map_pb_to_generate_info.update(pb_info)


    def on_new_row(self):
        pass

    def on_copy_new_row(self):
        pass

    def on_user_select(self):
        pass

    def on_delete_row(self):
        pass

    def on_file_download(self):
        # lambda: Utils.file_download_multiple(urls=self.selected_dataObj['claim_files_url']),
        pass

    def on_file_view(self):
        # lambda: Utils.file_view(urls=self.selected_dataObj['claim_files_url']),
        pass

    def on_map_view(self):
        # lambda: Utils.map_view(address=self.selected_dataObj['현장주소']),
        pass

    def on_excel_export(self):
        # lambda: Utils.file_download_multiple(urls=self.selected_dataObj['claim_files_url']),
        pass



from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config
class Wid_table_Base_for_stacked( 
    QWidget, 
    LazyParentAttrMixin, 
    Mixin_Table_Config,
    Mixin_PB_Info,
    ):

    # edit_mode = 'row' ### 'row' or 'cell' or 'None'

    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent)
        Mixin_PB_Info.__init__(self)
        self.lazy_attr_names = INFO.TABLE_LAZY_ATTR_NAMES   ### ✅ 25-7.8 기준 5개
        self.lazy_ws_names = [] #['ALL_TABLE_CONFIG']
        self.lazy_ready_flags: dict[str, bool] = {}
        self.lazy_attr_values: dict[str, Any] = {}
        self.start_init_time = time.perf_counter()
        self.kwargs = kwargs
        self.event_bus = event_bus
        # self.edit_mode = 'row' ### 'row' or 'cell'
        self.selected_rows:list[dict] = None
        self.selected_row:dict = None
        self.selected_row_with_rowNo:Optional[dict[int, dict]] = None   ### 최근것 25.7.3 부터 적용
        self.selected_rowNo:int = None
        self.selected_dataObj:dict = None
        self.map_pb_to_generate_info:dict[str, dict] = {}
        self.map_pb_widget_to_info:dict[QPushButton, dict] = {}

        self.table_config_init = None        

        # self.setup_table()
        # self.init_by_parent()

        self.is_api_datas_applied = False
        self.run_lazy_attr()
    
    def create_map_pb_to_generate_info(self):
        """ init에서 선언되어 있으므로, 필수로 적용할 것"""
        raise NotImplementedError("create_map_pb_to_generate_info 메서드는 상속 받은 클래스에서 구현해야 합니다.")

    def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
        super().on_lazy_attr_ready(attr_name, attr_value)


    def on_all_lazy_attrs_ready(self):		
        if INFO.IS_DEV:
            print (f"{self.__class__.__name__} :on_all_lazy_attrs_ready: {len(self.lazy_attr_values)}:{self.lazy_attr_values}")
        try:
            APP_ID = self.lazy_attr_values['APP_ID']
            self.map_pb_to_generate_info = self.create_map_pb_to_generate_info()
            self.setup_table()
            self.init_by_parent()
            self.render_edit_mode()
            super().mixin_on_all_lazy_attrs_ready(APP_ID=APP_ID )
            self.model.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attr_values)
            self.view.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attr_values)
            self.delegate.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attr_values)            

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise ValueError(f"on_all_lazy_attrs_ready 오류: {e}")
        
    def render_edit_mode(self):
        if 'edit_mode' in self.lazy_attr_values :
            if self.lazy_attr_values['edit_mode'] == 'None':
                self.wid_header.hide_modeCombo_and_saveButton()
            else:
                self.wid_header.set_ui_combo_edit_mode(str(self.lazy_attr_values['edit_mode']).capitalize())
    
    def setup_table(self):
        """ model, view, delegate 초기화 """
        raise NotImplementedError("setup_table 메서드는 상속 받은 클래스에서 구현해야 합니다.")
    
    def closeEvent(self, event):
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def showEvent(self, event:QShowEvent):
        super().showEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} showEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(True)
        if hasattr(self, 'wid_header') and self.wid_header and hasattr(self.wid_header, 'setVisible'):
            self.wid_header.setVisible(True)

    def hideEvent(self, event:QHideEvent):
        super().hideEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} hideEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(False)
        if hasattr(self, 'wid_header') and self.wid_header and hasattr(self.wid_header, 'setVisible'):
            self.wid_header.setVisible(False)


    def init_by_parent(self):
        """ 이 method 는 상속 받은 class에서 필히 호출함lambda ctx : self.on_map_view(ctx),
            왜냐면 scope 문제, base에서 불필요한 초기화 제한.      
            보통, 3개 실시
            self.init_attributes()
            self.init_ui()
            self.connect_signals()      
        """
        raise NotImplementedError("init__by_parent 메서드는 상속 받은 클래스에서 구현해야 합니다.")


    # def resolve_calling_context(self):
    #     """자식 클래스가 init 호출한 모듈의 globals / module name 추출"""
    #     frame = inspect.currentframe()
    #     logger.debug(f"frame: {frame}")
    #     caller_frame = frame.f_back
    #     logger.debug(f"caller_frame: {caller_frame}")
    #     self.calling_globals = caller_frame.f_globals
    #     logger.debug(f"self.calling_globals: {self.calling_globals}")
    #     self.calling_module_name = self.calling_globals.get('__name__')
    #     logger.debug(f"self.calling_module_name: {self.calling_module_name}")
    #     return self.calling_globals, self.calling_module_name

    def init_attributes(self):
        """ init_by_parent 에서 호출되는 함수 """
        self.is_tableConfigMode = False
        self.update_time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.api_datas:Optional[list[dict]] = None
        self.model_datas:Optional[list[list]] = None
        self.table_header:Optional[list[str]] = None
        self.prev_api_datas:Optional[list[dict]] = None
        self.model_datas:Optional[list[list]] = None
        self._initialize_from_kwargs( **self.kwargs)

    def _initialize_from_kwargs(self, **kwargs):
        """ kwargs로부터 모델 속성 초기화 """
        if 'set_kwargs_to_attr' not in kwargs or kwargs['set_kwargs_to_attr']:
            for key, value in kwargs.items():
                setattr(self, key, value)

    
    def map_index_to_widget(self) -> dict[int, QWidget]:
        if not hasattr( self, 'wid_header'):
            self.wid_header = Wid_Header(self)
        if not hasattr( self, 'widget_menu'):
            self.widget_menu = self._create_widget_menu()

        return {
            0: self.wid_header,
            1: self.widget_menu,
        }

    def init_ui(self):
        """ init_by_parent 에서 호출되는 함수 """
        self.v_layout = QVBoxLayout()

        if hasattr(self, "map_index_to_widget") and callable(self.map_index_to_widget):
            for index, widget in sorted(self.map_index_to_widget().items()):
                if isinstance(widget, QWidget):
                    self.v_layout.addWidget( widget)

        self.v_layout.addWidget(self.view)
        self.setLayout(self.v_layout)
        # self.render_emptyLabel_table()

    def _create_widget_menu(self) -> QWidget:
        menu_title = '아래 Table에서 Row를 선택하면 메뉴들이 활성화됩니다.'
        self.widget_menu = QWidget()  
        # self.widget_menu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # self.widget_menu.setFixedHeight(40)  # or 적당한 높이 
        # self.widget_menu.setStyleSheet("background-color: lightgreen;")
        h_layout = QHBoxLayout()
        self.widget_menu.setLayout(h_layout)
        if INFO.IS_DEV:
            print(f"INFO._get_is_table_config_admin(): {INFO._get_is_table_config_admin()}")
        if INFO._get_is_table_config_admin():
            self.PB_TableConfigMode = CustomPushButton(self.widget_menu, "Table설정")
            self.PB_TableConfigMode.clicked.connect(self.on_table_config_mode)
            self.PB_TableConfigMode.setToolTip("Table설정으로 관리자만 가능")
            self.PB_TableConfigMode.setFixedWidth(120)
            h_layout.addWidget(self.PB_TableConfigMode)
            h_layout.addSpacing(16*3)

        self.lb_menu_title = QLabel(menu_title, self.widget_menu)
        h_layout.addWidget(self.lb_menu_title)
        h_layout.addSpacing(16*3)

        try:
            if not hasattr(self, 'map_pb_to_generate_info') or not isinstance(self.map_pb_to_generate_info, dict) or not self.map_pb_to_generate_info:
                if INFO.IS_DEV:
                    Utils.generate_QMsg_Information(None, title="map_pb_to_generate_info", text="map_pb_to_generate_info 가 없습니다.", autoClose=1000)
                return self.widget_menu
            
            for pb_name, pb_info in self.map_pb_to_generate_info.items():
                setattr(self, pb_name, CustomPushButton(self.widget_menu, pb_info['title']))
                pb:CustomPushButton = getattr(self, pb_name)
                pb.setToolTip(pb_info['tooltip'])
                #### 연결시 고정됨 , 따라서, self.selected_dataObj = None 으로만 설정됨
                # pb.clicked.connect( partial(pb_info['slot'], self.selected_dataObj) )
                # 클릭 시점에 self.selected_dataObj를 참조하게 만듦 (지연 평가)
                pb.clicked.connect(pb_info['local_slot'])
                self.map_pb_widget_to_info[pb]= pb_info
                h_layout.addWidget(pb)
        except Exception as e:
            logger.error(f"map_pb_to_generate_info 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return self.widget_menu

        self.disable_pb_list_when_Not_row_selected()
        
        return self.widget_menu
    
    def on_request_pb_action(self):
        sender = self.sender()
        pb_info = self.map_pb_widget_to_info.get(sender)
        if not pb_info:
            if INFO.IS_DEV:
                print(f"[on_request_pb_action] Unknown sender: {sender}")
            return
        
        app_slot = pb_info.get('slot')
        if app_slot and callable(app_slot):
            try:
                app_slot(self.selected_dataObj)
            except Exception as e:
                Utils.generate_QMsg_critical(self, "Action 실패", str(e))
        else:
            if INFO.IS_DEV:
                print(f"[on_request_pb_action] No valid slot in pb_info: {pb_info}")

        self.selected_dataObj = None        
        self.disable_pb_list_when_Not_row_selected() # 혹은 self.reset_pb()

    def hide_wid_header_mode_and_save_button(self):
        self.wid_header.hide_modeCombo_and_saveButton()
        
    def hide_wid_header_all(self):
        self.wid_header.hide_all()


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")		

    def subscribe_gbus(self):
        self.event_bus.subscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
        self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
        if hasattr(self, 'on_selected_rows') and callable(self.on_selected_rows):
            self.event_bus.subscribe( f"{self.table_name}:selected_rows", self.on_selected_rows )
        if hasattr(self, 'on_selected_row_with_rowNo') and callable(self.on_selected_row_with_rowNo):
            self.event_bus.subscribe( f"{self.table_name}:selected_rows_with_rowNo", self.on_selected_row_with_rowNo )

    def on_selected_row_with_rowNo(self, selected_row_with_rowNo:dict[int, dict]):
        if INFO.IS_DEV:
            print ( f"on_selected_row_with_rowNo: {selected_row_with_rowNo}")
        self.selected_row_with_rowNo = selected_row_with_rowNo
        if isinstance(self.selected_row_with_rowNo, dict):
            self.selected_rowNo, self.selected_dataObj = next(iter(self.selected_row_with_rowNo.items()))  
        self.enable_pb_list_when_row_selected()
    
    def on_selected_rows(self, selected_rows:list[dict]):
        if INFO.IS_DEV: 
            print ( f"on_selected_rows: {selected_rows}")
        self.selected_rows = selected_rows
        self.enable_pb_list_when_row_selected()

    def clear_selected_row(self):
        self.selected_rowNo = None
        self.selected_dataObj = None
        self.selected_row_with_rowNo = None
        self.selected_rows = None

    def enable_pb_list_when_row_selected(self):
        if hasattr(self, 'map_pb_to_generate_info'):
            for pb_name, pb_info in self.map_pb_to_generate_info.items():
                if pb_info['disable_not_selected']:
                    getattr(self, pb_name).setEnabled(True)
 

    def disable_pb_list_when_Not_row_selected(self):    
        try:
            if hasattr(self, 'map_pb_to_generate_info'):
                for pb_name, pb_info in self.map_pb_to_generate_info.items():
                    if pb_info['disable_not_selected']:
                        getattr(self, pb_name).setEnabled(False)
                    else:
                        getattr(self, pb_name).setEnabled(True)
        except Exception as e:
            logger.error(f"disable_pb_list_when_Not_row_selected 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
    
    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
                                 self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
        self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
            

    def connect_signals(self):
        """ init_by_parent 에서 호출되는 함수 """
        self.wid_header.edit_mode_changed.connect( lambda mode: self.model.on_edit_mode(mode) )
        self.wid_header.save_requested.connect( self.model.on_api_send_By_Row )
        # self.PB_add_row.clicked.connect( lambda: self.view.menu_handler.slot_v_header__add_row(0) )

        ### model data 변경시 slot_model_data_changed 호출
        # self.model.user_data_changed.connect( self.slot_model_data_changed )
        # self.view.signal_select_rows.connect( lambda rowList: self.set_selected_rows(rowList) )
        # self.view.signal_select_row.connect( lambda rowDict: self.set_selected_row(rowDict) )
        # self.delegate.commitEdit.connect( self.slot_api_send_By_Cell )

    def run(self):
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} : run")

    def simulate_double_click(self,index: QModelIndex, view: QTableView=None, ):
        """ view 가 없으면 자동으로 self.view 로 설정함. """
        if view is None:
            view = self.view
        rect = self.view.visualRect(index)
        local_pos = QPointF(rect.center())  # <-- Fix: QPoint → QPointF
        global_pos = self.view.viewport().mapToGlobal(rect.center())
        global_pos_f = QPointF(global_pos)

        evt = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            local_pos,
            global_pos_f,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        QApplication.postEvent(self.view.viewport(), evt)


    def slot_model_data_changed(self, is_changed:bool):
        if is_changed:
            self.wid_header.update_api_query_time()
        else:
            self.model.clear_modified_rows()
        self.wid_header.update_api_query_time()

    def gbus_timer_1min(self, time_str:str):
        """ 매 분:0초마다 호출되는 함수 """
        self.wid_header.update_api_query_gap(time_str)

    def slot_api_send_By_Row(self):
        """편집 모드: row 일 때 save button 클릭 시 호출되는 함수
           bulk with files 로 구현됨.
        """
        try:
            modified_data = self.model.get_modified_rows_data()
            logger.debug(f"modified_data: {modified_data}")
            
            # 데이터 준비
            data_list = []
            files_dict = {}
            
            for item in modified_data:
                item_rowNo = item.pop('rowNo', -1)  ### tableview에서 rowNo : int
                item_copy = item.copy()
                
                # 파일 객체 처리
                if 'files' in item_copy:
                    files = item_copy.pop('files')
                    if files:
                        # ID 필드 확인
                        item_id = item_copy.get('id') or item_copy.get('pk')
                        
                        for field_name, file_obj in files.items():
                            # 파일 키 생성 (ID가 있으면 ID_필드명, 없으면 new_필드명)
                            file_key = f"{item_id}_{field_name}" if item_id else f"new_{field_name}"
                            
                            # files 딕셔너리에 추가
                            file_name = os.path.basename(file_obj.name)
                            files_dict[file_key] = (file_name, file_obj, 'application/octet-stream')
                
                # 데이터 리스트에 추가
                data_list.append(item_copy)
            
            # 요청 데이터 준비
            data = {
                'datas': json.dumps(data_list, ensure_ascii=False)
            }
            
            logger.debug(f"data: {data}")
            logger.debug(f"files_dict: {files_dict}")
            # API 요청 보내기
            url = self.url + 'bulk_generate_with_files/'
            is_ok, response = APP.API.post(url, data, files_dict)
            
            # 파일 객체 닫기 (요청 후)
            for file_tuple in files_dict.values():
                try:
                    file_tuple[1].close()
                except:
                    pass
            
            if is_ok:
                self.model.update_api_response(response, rowNo=item_rowNo)
            else:
                logger.error(f"API 요청 실패: {response}")
                QMessageBox.warning(self, "저장 실패", "데이터 저장에 실패했읍니다. 로그를 확인하세요.")
        except Exception as e:
            logger.error(f"slot_api_send_By_Row 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def slot_api_send_By_Cell(self, editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, _sendData:dict , files:object):
        """ 편집 모드: cell일 때, delegate 에서 바로 emit 시, handle(호출)되는 함수 """

        if self.url:
            logger.debug(f"files: {files}")
            if files:
                # filename = files.pop('filename')
                # fieldname = files.pop('field_name')
                is_ok, _json = APP.API.Send( self.url, id_obj , {}, files )
            else:
                is_ok, _json = APP.API.Send( self.url, id_obj , _sendData )

            if is_ok:
                try:
                    logger.debug(f" cell update : index : {index} : value : {value}")
                    self.delegate.force_close_editor(editor, model, index, value)
                except Exception as e:
                    logger.error(f"에디터 종료 오류: {e}")
                    logger.error(f"{traceback.format_exc()}")
            else:
                logger.error(f"API 요청 실패: {_json}")
        else:
            logger.error(f"url이 없읍니다.")


    def clear_layout(self):
        """레이아웃 초기화"""
        try:
            if self.layout:
                Utils.deleteLayout(self.layout)
        except Exception as e:
            logger.error(f"레이아웃 초기화 중 오류 발생: {e}")

    ### apply method들은 run script 형태임
    def apply_api_datas(self, api_datas:list[dict]):
        """ api fectch worker 처리 후 호출되는 함수 """       
 
        self.prev_api_datas = self.api_datas
        self.api_datas = copy.deepcopy(api_datas)
        if self.prev_api_datas is None or self.prev_api_datas != self.api_datas:
            self.wid_header.update_api_query_time( QDateTime.currentDateTime().toString("HH:mm:ss") )
        else:
            self.wid_header.update_no_change_data()
        
        should_create_config = self.table_config_init is None and not self.mixin_check_config_data()

        if should_create_config:
            self.table_config, self.table_config_api_datas = self.mixin_create_config(api_datas)
            self.table_config_init = True            
            self.on_table_config_refresh(False)

        
        if isinstance(self.model, Base_Table_Model):
            self.model.on_api_datas_received(api_datas)
            # topLeft = self.model.index(0, 0)
            # bottomRight = self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1)
            # self.model.dataChanged.emit(topLeft, bottomRight)
            self.model.layoutChanged.emit()

    def on_table_config_refresh(self, is_refresh:bool=True):
        self.mixin_on_table_config_refresh(is_refresh)

    # def update_ui_query_time(self):
    #     self.wid_header.update_api_query_time(self.update_time_str)

    # def compare_api_datas(self):
    #     """ self.prev_api_datas 와 self.api_datas 비교 하여 render 함"""
    #     self.wid_header.update_api_query_time(self.update_time_str)
    #     self.model.clear_modified_rows()
    #     logger.debug(f"self.prev_api_datas: {self.prev_api_datas}")
    #     logger.debug(f"self.api_datas: {self.api_datas}")
    #     if self.prev_api_datas is None:
    #         self.model.apply_api_datas(self.api_datas)
    #     else:
    #         if not self.model.is_same_api_datas():                
    #             self.model.apply_api_datas(self.api_datas)
    #         else:
    #             self.wid_header.update_no_change_data()
    
    def get_model_rowNo_colNo_from_selected_row(self, attr_name:str, selected_rows:list[dict]=None):
        if selected_rows is None:
            selected_rows = self.selected_rows
        return self.model._data.index(selected_rows[0]), self.model.get_column_No_by_field_name(attr_name)


    def get_template(self):
        return 

    

    def on_table_config_mode(self):

        print (f"on_table_config_mode: {self.table_config}")
        
        dlg = Dialog_TableConfigMode(
            self, 
            table_config=copy.deepcopy(self.table_config), 
            api_datas=copy.deepcopy(self.api_datas),
            is_no_config_initial=self.lazy_attr_values['is_no_config_initial']
            )


        dlg.exec()



# class Wid_table_Base_for_stacked_without_Init( LazyParentAttrMixin, QWidget ):
#     """ 초기화에 setup_table, init_by_parent 호출 안함 
#         즉, 상속받은 곳에서 호출 필연
#     """

#     lazy_attr_names = ['table_name', 'url']
#     lazy_ws_names = []
    
#     def __init__(self, parent:QWidget, **kwargs):
#         super().__init__(parent, **kwargs)
#         self.start_init_time = time.perf_counter()
#         self.event_bus = event_bus
#         self.edit_mode = 'row' ### 'row' or 'cell'
#         self.selected_rows:list[dict] = None
#         self.selected_row:dict = None

#         self.is_api_datas_applied = False
    
#     def setup_table(self):
#         raise NotImplementedError("setup_table 메서드는 상속 받은 클래스에서 구현해야 합니다.")

#     def showEvent(self, event:QShowEvent):
#         super().showEvent(event)
#         logger.debug(f" {self.__class__.__name__} showEvent")
#         print(f" {self.__class__.__name__} showEvent")
#         if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
#             self.view.setVisible(True)
#         if hasattr(self, 'wid_header') and self.wid_header and hasattr(self.wid_header, 'setVisible'):
#             self.wid_header.setVisible(True)

#     def hideEvent(self, event:QHideEvent):
#         super().hideEvent(event)
#         logger.debug(f" {self.__class__.__name__} hideEvent")
#         print(f" {self.__class__.__name__} hideEvent")
#         if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
#             self.view.setVisible(False)
#         if hasattr(self, 'wid_header') and self.wid_header and hasattr(self.wid_header, 'setVisible'):
#             self.wid_header.setVisible(False)


#     def init_by_parent(self):
#         """ 이 method 는 상속 받은 class에서 필히 호출함
#             왜냐면 scope 문제, base에서 불필요한 초기화 제한.            
#         """
#         raise NotImplementedError("init__by_parent 메서드는 상속 받은 클래스에서 구현해야 합니다.")


#     def resolve_calling_context(self):
#         """자식 클래스가 init 호출한 모듈의 globals / module name 추출"""
#         frame = inspect.currentframe()
#         logger.debug(f"frame: {frame}")
#         caller_frame = frame.f_back
#         logger.debug(f"caller_frame: {caller_frame}")
#         self.calling_globals = caller_frame.f_globals
#         logger.debug(f"self.calling_globals: {self.calling_globals}")
#         self.calling_module_name = self.calling_globals.get('__name__')
#         logger.debug(f"self.calling_module_name: {self.calling_module_name}")
#         return self.calling_globals, self.calling_module_name

#     def init_attributes(self):
#         self.is_tableConfigMode = False
#         self.update_time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
#         self.api_datas:Optional[list[dict]] = None
#         self.model_datas:Optional[list[list]] = None
#         self.table_header:Optional[list[str]] = None
#         self.prev_api_datas:Optional[list[dict]] = None
#         self.model_datas:Optional[list[list]] = None

#         if hasattr(self, 'kwargs'):
#             for key, value in self.kwargs.items():
#                 setattr(self, key, value)

#         self.run_lazy_attr()

#     def init_ui(self):
#         self.layout = QVBoxLayout()
#         self.wid_header = Wid_Header(self)
#         self.layout.addWidget(self.wid_header)

#         self.layout.addWidget(self.view)
#         self.setLayout(self.layout)
#         # self.render_emptyLabel_table()

#     def on_lazy_attr_ready(self, attr_name: str, attr_value: Any):
#         match attr_name:
#             case 'table_name':
#                 logger.debug(f"{self.__class__.__name__} : on_lazy_attr_ready : {attr_name} : {attr_value}")
#                 self.lazy_ready_flags[attr_name] = True
#                 self.table_name = attr_value
#                 self.subscribe_gbus()
#             case 'url':
#                 logger.debug(f"{self.__class__.__name__} : on_lazy_attr_ready : {attr_name} : {attr_value}")
#                 self.lazy_ready_flags[attr_name] = True
#                 self.url = attr_value
#             case _:
#                 logger.warning(f"Unknown attribute: {attr_name}")
        
#         if all(self.lazy_ready_flags.get(name, False) for name in self.lazy_attr_names + self.lazy_ws_names):
#             self.on_all_lazy_attrs_ready()
#         else:
#             logger.warning(f"{self.__class__.__name__} : on_lazy_attr_ready not ready: {self.lazy_ready_flags}")


#     def on_all_lazy_attrs_ready(self):		
#         self.subscribe_gbus()
#         logger.info(f"{self.__class__.__name__} : All lazy attributes are ready!")
#         logger.info(f"{self.lazy_attr_names}")

#     def on_lazy_attr_not_found(self, attr_name: str):
#         logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")		

#     def subscribe_gbus(self):
#         self.event_bus.subscribe(GBus.TIMER_1MIN, 
#                                  self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
#         self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
    
#     def unsubscribe_gbus(self):
#         self.event_bus.unsubscribe(GBus.TIMER_1MIN, 
#                                  self.wid_header.update_api_query_gap )  ### 매 분:0초마다 호출함.
#         self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
            

#     def connect_signals(self):
#         """ signal 연결 """
#         self.wid_header.edit_mode_changed.connect(  lambda mode: self.on_edit_mode(mode) )
#         self.wid_header.save_requested.connect( self.on_save_requested )
#         # self.PB_add_row.clicked.connect( lambda: self.view.menu_handler.slot_v_header__add_row(0) )

#         ### model data 변경시 slot_model_data_changed 호출
#         self.model.user_data_changed.connect( self.slot_model_data_changed )
#         self.view.signal_select_rows.connect( lambda rowList: self.set_selected_rows(rowList) )
#         self.view.signal_select_row.connect( lambda rowDict: self.set_selected_row(rowDict) )
#         self.delegate.commitEdit.connect( self.slot_api_send_By_Cell )

#     def on_edit_mode(self, edit_mode:str):
#         self.model.set_edit_mode(edit_mode)

#     def on_save_requested(self):
#         self.model.on_api_send_By_Row()

#     def run(self):
#         logger.debug(f" {self.__class__.__name__} : run")


#     def slot_model_data_changed(self, is_changed:bool):
#         if is_changed:
#             self.wid_header.update_api_query_time()
#         else:
#             self.model.clear_modified_rows()
#         self.wid_header.update_api_query_time()

#     def gbus_timer_1min(self, time_str:str):
#         """ 매 분:0초마다 호출되는 함수 """
#         self.wid_header.update_api_query_gap(time_str)

#     def slot_api_send_By_Row(self):
#         """편집 모드: row 일 때 save button 클릭 시 호출되는 함수
#            bulk with files 로 구현됨.
#         """
#         try:
#             modified_data = self.model.get_modified_rows_data()
#             logger.debug(f"modified_data: {modified_data}")
            
#             # 데이터 준비
#             data_list = []
#             files_dict = {}
            
#             for item in modified_data:
#                 item_rowNo = item.pop('rowNo', -1)  ### tableview에서 rowNo : int
#                 item_copy = item.copy()
                
#                 # 파일 객체 처리
#                 if 'files' in item_copy:
#                     files = item_copy.pop('files')
#                     if files:
#                         # ID 필드 확인
#                         item_id = item_copy.get('id') or item_copy.get('pk')
                        
#                         for field_name, file_obj in files.items():
#                             # 파일 키 생성 (ID가 있으면 ID_필드명, 없으면 new_필드명)
#                             file_key = f"{item_id}_{field_name}" if item_id else f"new_{field_name}"
                            
#                             # files 딕셔너리에 추가
#                             file_name = os.path.basename(file_obj.name)
#                             files_dict[file_key] = (file_name, file_obj, 'application/octet-stream')
                
#                 # 데이터 리스트에 추가
#                 data_list.append(item_copy)
            
#             # 요청 데이터 준비
#             data = {
#                 'datas': json.dumps(data_list, ensure_ascii=False)
#             }
            
#             logger.debug(f"data: {data}")
#             logger.debug(f"files_dict: {files_dict}")
#             # API 요청 보내기
#             url = self.url + 'bulk_generate_with_files/'
#             is_ok, response = APP.API.post(url, data, files_dict)
            
#             # 파일 객체 닫기 (요청 후)
#             for file_tuple in files_dict.values():
#                 try:
#                     file_tuple[1].close()
#                 except:
#                     pass
            
#             if is_ok:
#                 self.model.update_api_response(response, rowNo=item_rowNo)
#             else:
#                 logger.error(f"API 요청 실패: {response}")
#                 QMessageBox.warning(self, "저장 실패", "데이터 저장에 실패했읍니다. 로그를 확인하세요.")
#         except Exception as e:
#             logger.error(f"slot_api_send_By_Row 오류: {e}")
#             logger.error(f"{traceback.format_exc()}")


#     def slot_api_send_By_Cell(self, editor:QWidget, model:QAbstractItemModel, index:QModelIndex,value:Any, id_obj:dict, _sendData:dict , files:object):
#         """ 편집 모드: cell일 때, delegate 에서 바로 emit 시, handle(호출)되는 함수 """

#         if self.url:
#             logger.debug(f"files: {files}")
#             if files:
#                 # filename = files.pop('filename')
#                 # fieldname = files.pop('field_name')
#                 is_ok, _json = APP.API.Send( self.url, id_obj , {}, files )
#             else:
#                 is_ok, _json = APP.API.Send( self.url, id_obj , _sendData )

#             if is_ok:
#                 try:
#                     logger.debug(f" cell update : index : {index} : value : {value}")
#                     self.delegate.force_close_editor(editor, model, index, value)
#                 except Exception as e:
#                     logger.error(f"에디터 종료 오류: {e}")
#                     logger.error(f"{traceback.format_exc()}")
#             else:
#                 logger.error(f"API 요청 실패: {_json}")
#         else:
#             logger.error(f"url이 없읍니다.")


#     def clear_layout(self):
#         """레이아웃 초기화"""
#         try:
#             if self.layout:
#                 Utils.deleteLayout(self.layout)
#         except Exception as e:
#             logger.error(f"레이아웃 초기화 중 오류 발생: {e}")

#     ### apply method들은 run script 형태임
#     def apply_api_datas(self, api_datas:list[dict]):
#         """ api fectch worker 처리 후 호출되는 함수 """        
#         logger.debug(f"{self.__class__.__name__} : apply_api_datas: {len(api_datas)}")
#         print(f"{self.__class__.__name__} : apply_api_datas: {(api_datas)}")
#         self.set_api_datas(copy.deepcopy(api_datas))
#         self.compare_api_datas()

#     def compare_api_datas(self):
#         """ self.prev_api_datas 와 self.api_datas 비교 하여 render 함"""
#         self.wid_header.update_api_query_time(self.update_time_str)
#         self.model.clear_modified_rows()
#         logger.debug(f"self.prev_api_datas: {self.prev_api_datas}")
#         logger.debug(f"self.api_datas: {self.api_datas}")
#         if self.prev_api_datas is None:
#             self.model.apply_api_datas(self.api_datas)
#         else:
#             if not self.model.is_same_api_datas():                
#                 self.model.apply_api_datas(self.api_datas)
#             else:
#                 self.wid_header.update_no_change_data()
        

#     ### utils method
#     def create_model_datas(self, api_datas:list[dict]) -> list[list]:
#         """ api_datas를 model_datas로 변환 """
#         if not api_datas:
#             return []
#         model_datas = []
#         for obj in api_datas:
#             model_datas.append(self.get_table_row_data(obj))
#         self.set_model_datas(model_datas)
#         self.model_datas = model_datas
#         return model_datas
    
#     def create_table_header_from_config(self ):
#         """ table config 를 이용 생성"""
#         pass

#     def create_table_header_from_api_datas(self):
#         """ api_datas를 이용 생성 """
#         if self.api_datas and len(self.api_datas) > 0:
#             return list(self.api_datas[0].keys())
#         else:
#             return []
        
#     ####
#     def get_selected_rows(self):
#         return self.selected_rows
    
#     def get_selected_row(self):
#         return self.selected_row
    
   
#     ####
        
#     def get_table_row_data(self, obj:dict) -> list:
#         """ obj를 table row data로 변환 """
#         return [ obj.get(key, '') for key in self.get_table_header() ]


#     #### setters
#     def set_api_datas(self, api_datas:list[dict]):
#         self.prev_api_datas = self.api_datas
#         self.api_datas = api_datas

#     def set_model_datas(self, model_datas:list[list]):
#         self.prev_model_datas = self.model_datas
#         self.model_datas = model_datas

#     def set_update_time(self, time_str:Optional[str]=None):
#         self.update_time_str = time_str or QDateTime.currentDateTime().toString("HH:mm:ss")

#     def set_tableConfigMode(self, is_tableConfigMode:bool):
#         self.is_tableConfigMode = is_tableConfigMode

#     def set_is_no_config_initial(self, is_no_config_initial:bool=False):
#         self.is_no_config_initial = is_no_config_initial
#         self.view.set_is_no_config_initial(is_no_config_initial)

#     def set_row_span(self, colName: str, subNames: list[str]=[]) -> None:
#         """ self.view에 대한 row span 설정
#             kwargs:
#                 colName: str
#                 subNames: list[str]
#         """
#         self.view.setRowSpan(colName, subNames)

#     def set_selected_rows(self, rowList:list[dict]):
#         self.selected_rows = rowList

#     def set_selected_row(self, rowDict:dict):
#         self.selected_row = rowDict

#     #### getters
#     def get_table_header(self) -> list[str]:
#         """ table header 반환 """
#         if not self.table_header:
#             #### api_datas를 통해서 생성함
#             self.table_header = list(self.api_datas[0].keys())
        
#         return self.table_header