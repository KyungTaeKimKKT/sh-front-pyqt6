from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import inspect
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import sip

from modules.PyQt.compoent_v2.table_v2.Base_Table_View import Base_Table_View
from modules.PyQt.compoent_v2.table_v2.Base_Table_Model import Base_Table_Model
from modules.PyQt.compoent_v2.table_v2.Base_Delegate import Base_Delegate

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
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

from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog


from modules.PyQt.compoent_v2.custom_상속.custom_PB import Custom_PB_Query
from modules.PyQt.compoent_v2.custom_상속.custom_combo import Combo_Select_Edit_Mode

from modules.PyQt.compoent_v2.mixin_admin_contextmenu import Mixin_AdminContextMenu_TableMenu

class Ui_Mixin:
        
    def get_disable_편집모드_변경(self) -> bool:
        if Utils.is_valid_attr_name(self, 'lazy_attrs', dict):
            return self.lazy_attrs.get('disable_편집모드_변경', False)
        return False
    
    def get_table_config_enabled(self) -> bool:
        if Utils.is_valid_attr_name(self, 'lazy_attrs', dict) and 'is_table_config_enabled' in self.lazy_attrs:
            return  INFO._get_is_table_config_admin() and self.lazy_attrs['is_table_config_enabled']
        return INFO._get_is_table_config_admin()
    
    def get_edit_mode(self) -> str:
        if Utils.is_valid_attr_name(self, 'lazy_attrs', dict) and 'edit_mode' in self.lazy_attrs:
            return self.lazy_attrs['edit_mode']
        return 'row'
    
    def _is_editable(self) -> bool:
        return self.get_edit_mode() != 'None'

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName("main_layout")
        self.setLayout(self.main_layout)


        self.wid_edit_mode = self.create_wid_edit_mode()
        self.main_layout.addWidget(self.wid_edit_mode)

        ### table_menus 가 없어도 레이아웃에 추가함.( wid_edit_mode 는 포함됨 )
        self.wid_table_menus = self.create_wid_table_menus()
        self.main_layout.addWidget(self.wid_table_menus)

        #### 25-8-14 테이블 헤더 추가 
        if getattr(self, 'create_custom_table_header', None) and callable(self.create_custom_table_header):
            self.wid_table_header = self.create_custom_table_header()
            self.main_layout.addWidget(self.wid_table_header)

        self.setup_table()
        if Utils.is_valid_attr_name(self, 'view', QTableView):
            self.main_layout.addWidget(self.view)
        else:
            raise ValueError("view is not valid")

    def setup_table(self, main_layout:QVBoxLayout):
        """ model, view, delegate 초기화 """
        raise NotImplementedError("setup_table 메서드는 상속 받은 클래스에서 구현해야 합니다.")

    def create_wid_edit_mode(self):
        self.wid_edit_mode = QWidget(self)
        h_layout = QHBoxLayout()
        self.wid_edit_mode.setObjectName("wid_edit_mode")
        self.wid_edit_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.wid_edit_mode.setFixedHeight(40)
        self.wid_edit_mode.setStyleSheet("background-color: lightgreen;")
        self.wid_edit_mode.setLayout(h_layout)

        lb_title = QLabel(self.wid_edit_mode)
        lb_title.setText('Data Update 시간: ')
        lb_title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        h_layout.addWidget(lb_title)

        self.label_update_time = QLabel(self.wid_edit_mode)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_update_time.sizePolicy().hasHeightForWidth())
        self.label_update_time.setSizePolicy(sizePolicy)
        self.label_update_time.setStyleSheet("background-color:yellow;font-weight:bold;padding:5px, 0px;")
        self.label_update_time.setAlignment( Qt.AlignmentFlag.AlignCenter)
        self.label_update_time.setObjectName("label_update_time")
        h_layout.addWidget(self.label_update_time)

        self.label_update_gap = QLabel(self.wid_edit_mode)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_update_gap.sizePolicy().hasHeightForWidth())
        self.label_update_gap.setSizePolicy(sizePolicy)
        self.label_update_gap.setStyleSheet("font-weight:bold")
        self.label_update_gap.setObjectName("label_update_gap")
        h_layout.addWidget(self.label_update_gap)
        spacerItem = QSpacerItem(120, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        h_layout.addItem(spacerItem)

        if self._is_editable():
            self.lb_edit_mode_title = QLabel(self.wid_edit_mode)
            self.lb_edit_mode_title.setText('편집모드: ')
            sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.lb_edit_mode_title.sizePolicy().hasHeightForWidth())
            self.lb_edit_mode_title.setSizePolicy(sizePolicy)
            self.lb_edit_mode_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h_layout.addWidget(self.lb_edit_mode_title)

            if self.get_disable_편집모드_변경():
                self.lb_edit_mode_content = QLabel(self.wid_edit_mode)
                self.lb_edit_mode_content.setText(f"   {self.get_edit_mode().capitalize()}   ")
                self.lb_edit_mode_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lb_edit_mode_content.setStyleSheet("font-weight: bold;color:yellow;background-color:black;")
                h_layout.addWidget(self.lb_edit_mode_content)
                h_layout.addStretch()
            else:
                self.comboBox_edit_mode = Combo_Select_Edit_Mode(self.wid_edit_mode)
                sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(self.comboBox_edit_mode.sizePolicy().hasHeightForWidth())
                self.comboBox_edit_mode.setSizePolicy(sizePolicy)
                self.comboBox_edit_mode.setObjectName("comboBox_edit_mode")
                self.comboBox_edit_mode.setCurrentText(self.get_edit_mode().capitalize())
                self.comboBox_edit_mode.currentTextChanged.connect(self.on_edit_mode_changed)
                h_layout.addWidget(self.comboBox_edit_mode)                

            if self.get_edit_mode() == 'cell' and self.get_disable_편집모드_변경():
                pass
            else:
                spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                h_layout.addItem(spacerItem1)
                self.PB_save = Custom_PB_Query(self.wid_edit_mode)
                self.PB_save.setText('Row 저장')
                sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(self.PB_save.sizePolicy().hasHeightForWidth())
                self.PB_save.setSizePolicy(sizePolicy)
                self.PB_save.setObjectName("PB_save")
                self.PB_save.clicked.connect(self.on_save_row)
                h_layout.addWidget(self.PB_save)
        else:
            h_layout.addStretch()

        return self.wid_edit_mode

    def get_default_Table_Menus(self) -> dict:
        base_dict = {
            'Excel export': {
                'title': '엑셀 내보내기',
                'tooltip': '조회된 Table을 엑셀로 내보내기',
                'slot_func': 'on_excel_export',
                'disable_not_selected' :False,
            }
        }
        if INFO._get_is_app_admin():
            base_dict.update({
                'Excel export(admin)': {
                    'title': 'Excel(APP관리자)',
                    'tooltip': '조회된 Table의 모든 원본 API DATA를 엑셀로 내보내기',
                    'slot_func': 'on_excel_export_admin',
                    'disable_not_selected' :False,
                }
            })
        return base_dict
    

    def create_wid_table_menus(self) -> QWidget:
        self.wid_table_menus = QWidget(self)
        h_layout = QHBoxLayout()
        self.wid_table_menus.setObjectName("wid_table_menus")
        self.wid_table_menus.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.wid_table_menus.setFixedHeight(40)
        self.wid_table_menus.setStyleSheet("background-color: lightgreen;")
        self.wid_table_menus.setLayout(h_layout)

        # -------------------------
        # context menu (admin만)
        # -------------------------
        if INFO._get_is_app_admin():  # 관리자인 경우 Mixin_AdminContextMenu_TableMenu 초기화
            self.init_admin_context_menu(self.wid_table_menus)

        if self.get_table_config_enabled():
            self.PB_TableConfigMode = self._create_PB_table_config()
            h_layout.addWidget(self.PB_TableConfigMode)
            h_layout.addStretch()
        
        if Utils.is_valid_attr_name(self, 'Table_Menus', dict) :
            ### 25-8-20 추가 :  메뉴가 있으면 table에서 선택된 row No 표시
            h_layout.addWidget ( QLabel('선택된 Row No: '))
            self.lb_selected_rowNo = QLabel(self.wid_table_menus)
            self.lb_selected_rowNo.setStyleSheet("font-weight:bold;color:black;")
            h_layout.addWidget ( self.lb_selected_rowNo )
            h_layout.addSpacing(10)
            for Name, PB_dict in self.Table_Menus.items():
                pb = self._create_table_menu_PB(PB_dict)
                self.map_menu_to_pb[Name] = pb
                # setattr ( self, Name, self._create_table_menu_PB(PB_dict) )                
                h_layout.addWidget(pb)

        if (default_dict:=self.get_default_Table_Menus() ):
            h_layout.addSpacing(16*2)
            for Name, PB_dict in default_dict.items():
                pb = self._create_table_menu_PB(PB_dict)
                self.map_menu_to_pb[Name] = pb
                # setattr ( self, Name, self._create_table_menu_PB(PB_dict) )                
                h_layout.addWidget(pb)
        return self.wid_table_menus

    def get_disable_table_config(self) -> bool:
        if Utils.is_valid_attr_name(self, 'lazy_attrs', dict) and 'disable_table_config' in self.lazy_attrs:
            return self.lazy_attrs['disable_table_config']
        return False

    def _create_PB_table_config(self) -> QPushButton:
        if self.lazy_attrs.get( "is_no_config_initial"):
            _pb_mode = "API"
        else:
            _pb_mode = "DB"
        PB_TableConfigMode = CustomPushButton(self, f"Table설정:{_pb_mode}")
        if self.get_disable_table_config():
            PB_TableConfigMode.setEnabled(False)
            PB_TableConfigMode.setToolTip("이 Table은 설정이 불가능합니다.")
        else:
            PB_TableConfigMode.setEnabled(True)
            PB_TableConfigMode.clicked.connect(self.on_table_config_mode)
            PB_TableConfigMode.setToolTip("Table설정으로 관리자만 가능")        
        # PB_TableConfigMode.setFixedWidth(120)
        return PB_TableConfigMode

    def _create_table_menu_PB(self, PB_dict:dict):
        pb = CustomPushButton(self, PB_dict['title'])
        objectName = PB_dict.get('objectName', None)
        if objectName :
            if isinstance(objectName, str):
                pb.setObjectName(objectName)
            elif isinstance(objectName,  dict):
                pb.setObjectName( f"json:{json.dumps(objectName, ensure_ascii=False)}")

        pb.setToolTip(PB_dict['tooltip'])
        pb.setEnabled( self._get_disable_not_selected( PB_dict ) )
        if not pb.isEnabled():
            self.pb_list_when_row_selected.append(pb)

        if Utils.is_valid_method( self, PB_dict['slot_func'] ):
            pb.clicked.connect( getattr(self, PB_dict['slot_func']) )
        else:
            raise ValueError(f" table_menu_PB: {PB_dict['title']}  -- slot_func is not valid: {PB_dict['slot_func']}")
        return pb
    
    def _get_disable_not_selected(self, PB_dict:dict) -> bool:
        return not PB_dict["disable_not_selected"] 
    
    def _check_MENU_by_selected_row(self, selected_rowNo:int) -> None:
        """ 선택된 행에 따라 활성/비활성 처리: self.validate_menu_pb 에서 호출됨  """
        pass
    
    def _check_MENU_by_not_selected(self) -> None:
        """ api_datas에 따라 "disable_not_selected": true 인 pb활성/비활성: self.validate_menu_pb 에서 호출됨  """
        pass

from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config
class Wid_table_Base_V2( 
    QWidget, 
    LazyParentAttrMixin_V2, 
    Ui_Mixin,
    Mixin_Table_Config,
    Mixin_AdminContextMenu_TableMenu,
    ):

    # edit_mode = 'row' ### 'row' or 'cell' or 'None'

    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent)
        self.start_init_time = time.perf_counter()
        self.kwargs = kwargs or {}
        self.init_attributes()
        
        self.event_bus = event_bus
        # self.edit_mode = 'row' ### 'row' or 'cell'
        self.selected_rows:list[dict] = None
        self.selected_row:dict = None
        self.selected_row_with_rowNo:Optional[dict[int, dict]] = None   ### 최근것 25.7.3 부터 적용
        self.selected_rowNo:int = None
        self.selected_dataObj:dict = None
        self.map_pb_to_generate_info:dict[str, dict] = {}
        self.map_pb_widget_to_info:dict[QPushButton, dict] = {}
        self.map_menu_to_pb:dict[str, QPushButton] = {}

        self.pb_list_when_row_selected:list[QPushButton] = []

        self.table_config_init = None        

        # self.setup_table()
        # self.init_by_parent()
        if hasattr(self, '_init_by_child') and callable(self._init_by_child):
            self._init_by_child()

        self.is_api_datas_applied = False
        if  not self.kwargs.get('disable_lazy_attr', False):
            self.run_lazy_attr()

    def on_all_lazy_attrs_ready(self):		
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.setup_ui()
            super().mixin_on_all_lazy_attrs_ready(APP_ID=APP_ID )
            if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
                raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
            self.appDict =  copy.deepcopy(INFO.APP_권한_MAP_ID_TO_APP[APP_ID])
            self.table_name = Utils.get_table_name(APP_ID)
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)


            self.model.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs)
            self.view.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs)
            self.delegate.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs)            

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")

        
    def render_edit_mode(self):
        if 'edit_mode' in self.lazy_attrs :
            if self.lazy_attrs['edit_mode'] == 'None':
                self.wid_header.hide_modeCombo_and_saveButton()
            else:
                self.wid_header.set_ui_combo_edit_mode(str(self.lazy_attrs['edit_mode']).capitalize())
    
    def on_edit_mode_changed(self, mode:str):
        self.lazy_attrs['edit_mode'] = mode.lower()
        self.model.on_edit_mode(mode)
        if mode.lower() == 'row':
            self.PB_save.show()
        else:
            self.PB_save.hide()


    
    def closeEvent(self, event):
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def showEvent(self, event:QShowEvent):
        super().showEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} showEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(True)


    def hideEvent(self, event:QHideEvent):
        super().hideEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} hideEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(False)


    def init_attributes(self):
        self.last_update_time = None
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

    def validate_menu_pb(self, selected_rowNo:Optional[int]=None) -> None:
        """ 모두 tableview에서 호출됨. : ui 변경과 sync 처리
            self.api_datas 변경시 호출(tableview setModel에서 연결 )및 
            선택된 행에 따라 활성/비활성 처리 (tableview on_selected_row_data에서 호출됨.)
        """
        if selected_rowNo:
            self._check_MENU_by_selected_row(selected_rowNo)

        self._check_MENU_by_not_selected()
   
    # def on_request_pb_action(self):
    #     sender = self.sender()
    #     pb_info = self.map_pb_widget_to_info.get(sender)
    #     if not pb_info:
    #         if INFO.IS_DEV:
    #             print(f"[on_request_pb_action] Unknown sender: {sender}")
    #         return
        
    #     app_slot = pb_info.get('slot')
    #     if app_slot and callable(app_slot):
    #         try:
    #             app_slot(self.selected_dataObj)
    #         except Exception as e:
    #             Utils.generate_QMsg_critical(self, "Action 실패", str(e))
    #     else:
    #         if INFO.IS_DEV:
    #             print(f"[on_request_pb_action] No valid slot in pb_info: {pb_info}")

    #     self.selected_dataObj = None        
    #     self.disable_pb_list_when_Not_row_selected() # 혹은 self.reset_pb()

    def hide_wid_header_mode_and_save_button(self):
        self.wid_header.hide_modeCombo_and_saveButton()
        
    def hide_wid_header_all(self):
        self.wid_header.hide_all()


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")		

    def update_api_query_gap(self, time_str:Optional[str]=None):
        if not time_str:
            self.last_update_time = None
        try:
            now = QDateTime.currentDateTime()
            if self.last_update_time is not None:
                seconds = self.last_update_time.secsTo(now)
                if seconds < 60:
                    gap_text = f"(1분 미만)"
                elif seconds < 3600:
                    minutes = seconds // 60
                    gap_text = f"({minutes}분 전)"
                else:
                    hours = seconds // 3600
                    remaining_minutes = (seconds % 3600) // 60
                    gap_text = f"({hours}시간 {remaining_minutes}분 전)"
            else:
                gap_text = ' (방금 전) '
            ### wid_edit_mode의
            if time_str is None:
                self.label_update_time.setText(now.toString("HH:mm:ss"))
            self.label_update_gap.setText(gap_text)

            self.last_update_time = now
        except Exception as e:
            logger.critical(f"시간 차이 계산 중 오류 발생: {e}")


    def subscribe_gbus(self):

        self.event_bus.subscribe(GBus.TIMER_1MIN, self.update_api_query_gap )  ### 매 분:0초마다 호출함.
        self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
        self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
        if hasattr(self, 'on_selected_rows') and callable(self.on_selected_rows):
            self.event_bus.subscribe( f"{self.table_name}:selected_rows", self.on_selected_rows )
        if hasattr(self, 'on_selected_row_with_rowNo') and callable(self.on_selected_row_with_rowNo):
            self.event_bus.subscribe( f"{self.table_name}:selected_rows_with_rowNo", self.on_selected_row_with_rowNo )

    def on_selected_row_with_rowNo(self, selected_row_with_rowNo:dict[int, dict]):

        self.selected_row_with_rowNo = selected_row_with_rowNo
        if isinstance(self.selected_row_with_rowNo, dict):
            for rowNo, rowDict in self.selected_row_with_rowNo.items():
                self.selected_rowNo = int(rowNo)
                self.selected_dataObj = rowDict
                self.lb_selected_rowNo.setText(f"{self.selected_rowNo}")
                break
            # self.selected_rowNo, self.selected_dataObj = next(iter(self.selected_row_with_rowNo.items()))  
        self.enable_pb_list_when_row_selected()
    
    def on_selected_rows(self, selected_rows:list[dict]):
        # if INFO.IS_DEV: 
        #     print ( f"on_selected_rows: {selected_rows}")
        self.selected_rows = selected_rows
        self.enable_pb_list_when_row_selected()

    def reset_selected_row(self):
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()

    def clear_selected_row(self):
        self.lb_selected_rowNo.setText('없음')
        self.selected_rowNo = None
        self.selected_dataObj = None
        self.selected_row_with_rowNo = None
        self.selected_rows = None

    def enable_pb_list_when_row_selected(self):
        try:
            for pb in self.pb_list_when_row_selected:
                pb.setEnabled(True)
        except Exception as e:
            logger.error(f"enable_pb_list_when_row_selected 오류: {e}")
            logger.error(f"{traceback.format_exc()}") 

    def disable_pb_list_when_Not_row_selected(self):    
        try:
            for pb in self.pb_list_when_row_selected:
                pb.setEnabled(False)
        except Exception as e:
            logger.error(f"disable_pb_list_when_Not_row_selected 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
    
    def unsubscribe_gbus(self):
        try:
            self.event_bus.unsubscribe(GBus.TIMER_1MIN, self.update_api_query_gap )  ### 매 분:0초마다 호출함.
            self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
        except Exception as e:
            logger.error(f"unsubscribe_gbus 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            

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

    def simulate_double_click(self,index: QModelIndex ):
        """ view 가 없으면 자동으로 self.view 로 설정함. """

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
    
    def on_save_row(self):
        self.model.on_api_send_By_Row()


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
 
        self.prev_api_datas = copy.deepcopy(self.api_datas)
        self.api_datas = copy.deepcopy(api_datas)
        ids_list = [item.get('id', None) for item in self.api_datas]
        if all(ids_list):
            self.id_to_api_data = {item['id']:item for item in self.api_datas}
        else:
            self.id_to_api_data = {}

        self.update_api_query_gap(time_str=None)
        
        should_create_config = self.table_config_init is None and not self.mixin_check_config_data()

        if should_create_config:
            self.table_config, self.table_config_api_datas = self.mixin_create_config(copy.deepcopy(api_datas))
            self.table_config_init = True            
            self.on_table_config_refresh(False)

        
        if isinstance(self.model, Base_Table_Model):
            self.model.on_api_datas_received(self.api_datas)
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
        
        dlg = Dialog_TableConfigMode(
            self, 
            table_config=copy.deepcopy(self.table_config), 
            api_datas=copy.deepcopy(self.api_datas),
            is_no_config_initial=self.lazy_attr_values['is_no_config_initial']
            )


        dlg.exec()

    def on_new_row(self):     
        model: Base_Table_Model = self.model
        model.on_new_row_by_template(added_url='template/')
        if self.selected_rows:
            self.selected_rows.clear()        
            self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):        
        self.model.request_delete_row( rowNo=self.selected_rowNo)
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_fileview(self):        
        try:
            dlg = FileViewer_Dialog(self)
            dlg.add_file( self.selected_dataObj['file'])
            dlg.exec()
        except Exception as e:
            logger.error(f"on_fileview 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            _text = f"on_fileview 오류: {e}<br> {trace}"
            Utils.generate_QMsg_critical(None, title='파일보기 오류', text=_text)
        self.selected_rows.clear()        
        self.disable_pb_list_when_Not_row_selected()

    def on_file_download(self):
        try:
            objectName = self.sender().objectName()
            if objectName:
                file_path = self.selected_dataObj[objectName]
                if file_path:
                    Utils.func_filedownload(file_path)
                else:
                    Utils.generate_QMsg_critical(self, title='파일 다운로드 오류', text=f'파일 다운로드 오류<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='파일 다운로드 오류', text=f'파일 다운로드 오류<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_file_download 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_file_upload(self):        
        return 
        try:
            objectName = self.sender().objectName()
            if objectName:
                file_path = Utils.func_fileupload_single(objectName)
                if file_path:
                    Utils.func_fileupload(file_path)
                else:
                    Utils.generate_QMsg_critical(self, title='파일 업로드 오류', text=f'파일 업로드 오류<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='파일 업로드 오류', text=f'파일 업로드 오류<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_file_upload 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_excel_export(self):
        try:
            self.model.data_to_excel_only_visible_columns()
        except Exception as e:
            logger.error(f"on_excel_export 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_excel_export_admin(self):
        try:
            self.model.data_to_excel_raw_data()
        except Exception as e:
            logger.error(f"on_excel_export_admin 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def on_map_view(self):
        try:
            objectName = self.sender().objectName()
            print(f"objectName: {objectName}")
            return 
            if objectName:
                address = self.selected_dataObj['address']
                if address:
                    Utils.map_view(address)
                else:
                    Utils.generate_QMsg_critical(self, title='주소가 없읍니다.', text=f'주소가 없읍니다.<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='주소가 없읍니다.', text=f'주소가 없읍니다.<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_map_view 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_map_view 오류', text=f"{e}<br>{trace}")



from modules.PyQt.compoent_v2.table_v2.mixin_table_config import Mixin_Table_Config
class Wid_table_Base_V3( 
    QWidget, 
    LazyParentAttrMixin_V2, 
    Ui_Mixin,
    Mixin_AdminContextMenu_TableMenu,
    ):

    # edit_mode = 'row' ### 'row' or 'cell' or 'None'

    def __init__(self, parent:QWidget, **kwargs):
        super().__init__(parent)
        self.start_init_time = time.perf_counter()
        self.kwargs = kwargs or {}
        self.init_attributes()
        
        self.event_bus = event_bus
        # self.edit_mode = 'row' ### 'row' or 'cell'
        self.selected_rows:list[dict] = None
        self.selected_row:dict = None
        self.selected_row_with_rowNo:Optional[dict[int, dict]] = None   ### 최근것 25.7.3 부터 적용
        self.selected_rowNo:int = None
        self.selected_dataObj:dict = None
        self.map_pb_to_generate_info:dict[str, dict] = {}
        self.map_pb_widget_to_info:dict[QPushButton, dict] = {}
        self.map_menu_to_pb:dict[str, QPushButton] = {}

        self.pb_list_when_row_selected:list[QPushButton] = []

        self.table_config_init = None        

        # self.setup_table()
        # self.init_by_parent()
        if hasattr(self, '_init_by_child') and callable(self._init_by_child):
            self._init_by_child()

        self.is_api_datas_applied = False
        if  not self.kwargs.get('disable_lazy_attr', False):
            self.run_lazy_attr()

    def on_all_lazy_attrs_ready(self):		
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.setup_ui()
            # super().mixin_on_all_lazy_attrs_ready(APP_ID=APP_ID )
            if APP_ID not in INFO.APP_권한_MAP_ID_TO_APP :
                raise ValueError(f"APP_ID {APP_ID} 가 존재하지 않습니다.")
            self.appDict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            if self.appDict and 'api_uri' in self.appDict and 'api_url' in self.appDict	:
                self.url = Utils.get_api_url_from_appDict(self.appDict)

            model : Base_Table_Model = self.model
            view : Base_Table_View = self.view
            delegate : Base_Delegate = self.delegate

            model.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs)
            view.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs)
            delegate.on_all_lazy_attrs_ready(APP_ID=APP_ID, lazy_attr_values=self.lazy_attrs) 

            if self.table_name in INFO.ALL_TABLE_TOTAL_CONFIG:
                self.refresh_table_config()
                ### 나중에 self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh) 시 변경 유무 파악하기 위해
                self.prev_table_config = copy.deepcopy(self.table_config)

            self.subscribe_gbus()

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")

    def refresh_table_config(self):
        self.table_config = INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfig']
        self.table_config_api_datas = copy.deepcopy(INFO.ALL_TABLE_TOTAL_CONFIG[self.table_name]['MAP_TableName_To_TableConfigApiDatas'])
        self.model.set_table_config(self.table_config, self.table_config_api_datas)

        
    def render_edit_mode(self):
        if 'edit_mode' in self.lazy_attrs :
            if self.lazy_attrs['edit_mode'] == 'None':
                self.wid_header.hide_modeCombo_and_saveButton()
            else:
                self.wid_header.set_ui_combo_edit_mode(str(self.lazy_attrs['edit_mode']).capitalize())
    
    def on_edit_mode_changed(self, mode:str):
        self.lazy_attrs['edit_mode'] = mode.lower()
        self.model.on_edit_mode(mode)
        if mode.lower() == 'row':
            self.PB_save.show()
        else:
            self.PB_save.hide()


    
    def closeEvent(self, event):
        self.unsubscribe_gbus()
        super().closeEvent(event)

    def showEvent(self, event:QShowEvent):
        super().showEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} showEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(True)


    def hideEvent(self, event:QHideEvent):
        super().hideEvent(event)
        if INFO.IS_DEV:
            logger.debug(f" {self.__class__.__name__} hideEvent")
        if hasattr(self, 'view') and self.view and hasattr(self.view, 'setVisible'):
            self.view.setVisible(False)


    def init_attributes(self):
        self.last_update_time = None
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

    def validate_menu_pb(self, selected_rowNo:Optional[int]=None) -> None:
        """ 모두 tableview에서 호출됨. : ui 변경과 sync 처리
            self.api_datas 변경시 호출(tableview setModel에서 연결 )및 
            선택된 행에 따라 활성/비활성 처리 (tableview on_selected_row_data에서 호출됨.)
        """
        if selected_rowNo:
            self._check_MENU_by_selected_row(selected_rowNo)

        self._check_MENU_by_not_selected()
   


    def on_lazy_attr_not_found(self, attr_name: str):
        logger.critical(f"LazyParentAttrMixin: {attr_name} not found within {self.lazy_timeout} seconds")		

    def update_api_query_gap(self, time_str:Optional[str]=None):
        if not time_str:
            self.last_update_time = None
        try:
            now = QDateTime.currentDateTime()
            if self.last_update_time is not None:
                seconds = self.last_update_time.secsTo(now)
                if seconds < 60:
                    gap_text = f"(1분 미만)"
                elif seconds < 3600:
                    minutes = seconds // 60
                    gap_text = f"({minutes}분 전)"
                else:
                    hours = seconds // 3600
                    remaining_minutes = (seconds % 3600) // 60
                    gap_text = f"({hours}시간 {remaining_minutes}분 전)"
            else:
                gap_text = ' (방금 전) '
            ### wid_edit_mode의
            if time_str is None:
                self.label_update_time.setText(now.toString("HH:mm:ss"))
            self.label_update_gap.setText(gap_text)

            self.last_update_time = now
        except Exception as e:
            logger.critical(f"시간 차이 계산 중 오류 발생: {e}")


    def subscribe_gbus(self):
        try:
            self.event_bus.subscribe(GBus.TIMER_1MIN, self.update_api_query_gap )  ### 매 분:0초마다 호출함.
            self.event_bus.subscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
            self.event_bus.subscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
            if hasattr(self, 'on_selected_rows') and callable(self.on_selected_rows):
                self.event_bus.subscribe( f"{self.table_name}:selected_rows", self.on_selected_rows )
            if hasattr(self, 'on_selected_row_with_rowNo') and callable(self.on_selected_row_with_rowNo):
                self.event_bus.subscribe( f"{self.table_name}:selected_rows_with_rowNo", self.on_selected_row_with_rowNo )
        except Exception as e:
            logger.error ( f" subscribe error : {e}")

    def unsubscribe_gbus(self):
        try:
            self.event_bus.unsubscribe(GBus.TIMER_1MIN, self.update_api_query_gap )  ### 매 분:0초마다 호출함.
            self.event_bus.unsubscribe( f"{self.table_name}:datas_changed", self.apply_api_datas )
            self.event_bus.unsubscribe(f"{GBus.TABLE_TOTAL_REFRESH}", self.on_table_config_refresh)
            self.event_bus.unsubscribe( f"{self.table_name}:selected_rows", self.on_selected_rows )
            self.event_bus.unsubscribe( f"{self.table_name}:selected_rows_with_rowNo", self.on_selected_row_with_rowNo )
        except Exception as e:
            logger.error(f"unsubscribe_gbus 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def on_selected_row_with_rowNo(self, selected_row_with_rowNo:dict[int, dict]):

        self.selected_row_with_rowNo = selected_row_with_rowNo
        if isinstance(self.selected_row_with_rowNo, dict):
            for rowNo, rowDict in self.selected_row_with_rowNo.items():
                self.selected_rowNo = int(rowNo)
                self.selected_dataObj = rowDict
                self.lb_selected_rowNo.setText(f"{self.selected_rowNo}")
                break
            # self.selected_rowNo, self.selected_dataObj = next(iter(self.selected_row_with_rowNo.items()))  
        self.enable_pb_list_when_row_selected()
    
    def on_selected_rows(self, selected_rows:list[dict]):
        # if INFO.IS_DEV: 
        #     print ( f"on_selected_rows: {selected_rows}")
        self.selected_rows = selected_rows
        self.enable_pb_list_when_row_selected()

    def reset_selected_row(self):
        self.clear_selected_row()
        self.disable_pb_list_when_Not_row_selected()

    def clear_selected_row(self):
        self.lb_selected_rowNo.setText('없음')
        self.selected_rowNo = None
        self.selected_dataObj = None
        self.selected_row_with_rowNo = None
        self.selected_rows = None

    def enable_pb_list_when_row_selected(self):
        try:
            if not hasattr(self, "pb_list_when_row_selected") or not self.pb_list_when_row_selected:
                return  # 이미 cleanup된 인스턴스
            for pb in self.pb_list_when_row_selected:
                if sip.isdeleted(pb):  # 또는 try/except
                    continue
                pb.setEnabled(True)
        except Exception as e:
            logger.error(f"enable_pb_list_when_row_selected 오류: {e}")
            logger.error(f"{traceback.format_exc()}") 

    def disable_pb_list_when_Not_row_selected(self):    
        try:
            if not hasattr(self, "pb_list_when_row_selected") or not self.pb_list_when_row_selected:
                return  # 이미 cleanup된 인스턴스
            for pb in self.pb_list_when_row_selected:
                if sip.isdeleted(pb):  # 또는 try/except
                    continue
                pb.setEnabled(False)
        except Exception as e:
            logger.error(f"disable_pb_list_when_Not_row_selected 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
    

            

    # def connect_signals(self):
    #     """ init_by_parent 에서 호출되는 함수 """
    #     self.wid_header.edit_mode_changed.connect( lambda mode: self.model.on_edit_mode(mode) )
    #     self.wid_header.save_requested.connect( self.model.on_api_send_By_Row )



    def simulate_double_click(self,index: QModelIndex ):
        """ view 가 없으면 자동으로 self.view 로 설정함. """
        view : QTableView = self.view
        rect = view.visualRect(index)
        local_pos = QPointF(rect.center())  # <-- Fix: QPoint → QPointF
        global_pos = view.viewport().mapToGlobal(rect.center())
        global_pos_f = QPointF(global_pos)

        evt = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            local_pos,
            global_pos_f,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        QApplication.postEvent( view.viewport(), evt)
    
    def on_save_row(self):
        self.model.on_api_send_By_Row()


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
 
        self.prev_api_datas = copy.deepcopy(self.api_datas)
        self.api_datas = copy.deepcopy(api_datas)
        ids_list = [item.get('id', None) for item in self.api_datas]
        if all(ids_list):
            self.id_to_api_data = {item['id']:item for item in self.api_datas}
        else:
            self.id_to_api_data = {}

        self.update_api_query_gap(time_str=None)
        
        # should_create_config = self.table_config_init is None and not self.mixin_check_config_data()

        # if should_create_config:
        #     self.table_config, self.table_config_api_datas = self.mixin_create_config(copy.deepcopy(api_datas))
        #     self.table_config_init = True            
        #     self.on_table_config_refresh(False)

        model : Base_Table_Model = self.model
        model.on_api_datas_received(self.api_datas)
        model.layoutChanged.emit()


    def on_table_config_refresh(self, is_refresh:bool=True):
        model: Base_Table_Model = self.model
        self.refresh_table_config()
        print ( self.prev_table_config == self.table_config)
        if self.prev_table_config != self.table_config:
            model.layoutChanged.emit()
            if INFO._get_is_app_admin():
                Utils.generate_QMsg_Information ( self, title="Table 설정 변경", text = f"{self.table_name} 설정 변경", autoClose = 2000)
            self.prev_table_config = copy.deepcopy(self.table_config )

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
        dlg = Dialog_TableConfigMode(
            self, 
            table_config=copy.deepcopy(self.table_config), 
            api_datas=copy.deepcopy(self.api_datas),
            is_no_config_initial=self.lazy_attrs['is_no_config_initial']
            )


        dlg.exec()

    def on_new_row(self):     
        model: Base_Table_Model = self.model
        model.on_new_row_by_template(added_url='template/')
        if self.selected_rows:
            self.selected_rows.clear()        
            self.disable_pb_list_when_Not_row_selected()

    def on_delete_row(self):        
        self.model.request_delete_row( rowNo=self.selected_rowNo)
        self.selected_rows.clear()
        self.disable_pb_list_when_Not_row_selected()

    def on_fileview(self):        
        try:
            dlg = FileViewer_Dialog(self)
            dlg.add_file( self.selected_dataObj['file'])
            dlg.exec()
        except Exception as e:
            logger.error(f"on_fileview 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            _text = f"on_fileview 오류: {e}<br> {trace}"
            Utils.generate_QMsg_critical(None, title='파일보기 오류', text=_text)
        self.selected_rows.clear()        
        self.disable_pb_list_when_Not_row_selected()

    def on_file_download(self):
        try:
            objectName = self.sender().objectName()
            if objectName:
                file_path = self.selected_dataObj[objectName]
                if file_path:
                    Utils.func_filedownload(file_path)
                else:
                    Utils.generate_QMsg_critical(self, title='파일 다운로드 오류', text=f'파일 다운로드 오류<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='파일 다운로드 오류', text=f'파일 다운로드 오류<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_file_download 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_file_upload(self):        
        return 
        try:
            objectName = self.sender().objectName()
            if objectName:
                file_path = Utils.func_fileupload_single(objectName)
                if file_path:
                    Utils.func_fileupload(file_path)
                else:
                    Utils.generate_QMsg_critical(self, title='파일 업로드 오류', text=f'파일 업로드 오류<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='파일 업로드 오류', text=f'파일 업로드 오류<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_file_upload 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_excel_export(self):
        try:
            self.model.data_to_excel_only_visible_columns()
        except Exception as e:
            logger.error(f"on_excel_export 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def on_excel_export_admin(self):
        try:
            self.model.data_to_excel_raw_data()
        except Exception as e:
            logger.error(f"on_excel_export_admin 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def on_map_view(self):
        try:
            objectName = self.sender().objectName()
            print(f"objectName: {objectName}")
            return 
            if objectName:
                address = self.selected_dataObj['address']
                if address:
                    Utils.map_view(address)
                else:
                    Utils.generate_QMsg_critical(self, title='주소가 없읍니다.', text=f'주소가 없읍니다.<br>objectName: {objectName}')
            else:
                Utils.generate_QMsg_critical(self, title='주소가 없읍니다.', text=f'주소가 없읍니다.<br>objectName: {objectName}')
        except Exception as e:
            logger.error(f"on_map_view 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_map_view 오류', text=f"{e}<br>{trace}")
