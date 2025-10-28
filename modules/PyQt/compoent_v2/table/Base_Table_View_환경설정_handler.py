from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Callable
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
from modules.PyQt.User.toast import User_Toast
from datetime import datetime
from copy import deepcopy

import traceback
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

if TYPE_CHECKING:
    from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
    from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model


class Base_Table_View_환경설정_handler:
    """ 환경설정 모드 클래스 : 환경 설정 METHOD 정의 """

    def __init__(self, handler: Optional[Base_Table_View]):
        self.handler = handler
        self.model:Optional[Base_Table_Model] = handler.model()
        self.header = handler.horizontalHeader()
        self.config_mode_active = True



    def run(self):
        if self.handler.check_api_datas_available():
            self.init_by_api_datas_model()
            self.setupConfigHeader()
            self.render_수정모드_헤더()

        else:
            self.copy_original_header()
            self.setupConfigHeader()
            self.render_수정모드_헤더()

    def init_by_api_datas_model(self):
        """ api_datas 로 초기 설정 """
        self.handler._headers = deepcopy(self.handler.model()._headers)
        self.api_datas_변경 = []
        self.original_state = {}
        for header in self.handler._headers:
            _dict = {}
            _dict['id'] = -1
            _dict['table_name'] = self.handler.table_name
            _dict['column_name'] = header
            _dict['display_name'] = header
            _dict['order'] = self.handler._headers.index(header)
            _dict['column_width'] = 0
            _dict['is_hidden'] = False
            self.api_datas_변경.append(_dict)
        logger.debug( f" init_by_api_datas_model : {self.api_datas_변경}")

    
    def copy_original_header(self):
        self.model = self.handler.model()
        self.original_state = {
                'hidden_columns': deepcopy(self.handler._hidden_columns),
                'column_widths':  [self.header.sectionSize(i) for i in range(self.model.columnCount())],
                'column_order': [self.header.visualIndex(i) for i in range(self.model.columnCount())],
                'headers':  deepcopy(self.handler._headers),
                'table_config_api_datas': deepcopy(self.handler._table_config_api_datas),
                'api_datas_변경':   deepcopy(self.handler._table_config_api_datas),
            }
        # self.original_state = {
        #         'hidden_columns': [i for i in range(self.model.columnCount()) if self.handler.isColumnHidden(i)],
        #         'column_widths': [self.header.sectionSize(i) for i in range(self.model.columnCount())],
        #         'column_order': [self.header.visualIndex(i) for i in range(self.model.columnCount())],
        #         'headers': [ header for header in self.handler._headers ],
        #         'table_config_api_datas':self._get_table_config_api_datas(),
        #         'api_datas_변경': [ deepcopy(obj) for obj in self.handler._table_config_api_datas ],
        #     }
        
        logger.debug(f"self.original_state: {self.original_state}")
        
        #### 변경이록 기록 api_datas_변경 생성
        self.api_datas_변경 = deepcopy( self.original_state['table_config_api_datas'] )


    def setupConfigHeader(self):
        """설정 모드용 커스텀 헤더 설정"""
        try:
            header = self.header        
            # 헤더 설정
            header.setSectionsMovable(True)  # 드래그 앤 드롭으로 order 변경 가능
            header.setSectionsClickable(True)
            header.sectionDoubleClicked.connect(self.onHeaderSectionDoubleClicked)
            if self.header.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            header.customContextMenuRequested.connect(self.showHeaderContextMenu)
            header.sectionMoved.connect(self.onHeaderSectionMoved)
            header.sectionResized.connect(self.onColumnResized)
        except Exception as e:
            logger.error(f"setupConfigHeader 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def render_수정모드_헤더(self):
        try:
            # 1. 모든 숨겨진 컬럼 표시
            for i in range(self.model.columnCount()):
                self.handler.setColumnHidden(i, False)  # self.setColumnHidden -> self.handler.setColumnHidden
            self.render_header()  # 인자 제거 (self.model)

            # 사용자에게 설정 모드 알림
            User_Toast(INFO.MAIN_WINDOW, title="테이블 설정 모드", text="테이블 설정 모드가 활성화되었읍니다.", duration=3000, style='INFORMATION')
            self.header.viewport().update()
        except Exception as e:
            logger.error(f"render_수정모드_헤더 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def render_header(self):
        """헤더 렌더링"""
        try:
            # 2. 체크박스 + name 동시 표시
            txt_hidden , txt_visible =  '[V] ', '[ ] '
            display_name_with_checkbox = {
                col_idx: txt_hidden 
                + (self.handler._headers[col_idx]).replace('[V] ', '').replace('[ ] ', '') if col_idx in self.handler._hidden_columns else txt_visible 
                + (self.handler._headers[col_idx]).replace('[V] ', '').replace('[ ] ', '')
                for col_idx in range(self.model.columnCount())
            }

            for col_idx, display_name in display_name_with_checkbox.items():
                self.model.setHeaderData(col_idx, Qt.Orientation.Horizontal, display_name, Qt.ItemDataRole.DisplayRole)
            self.header.update()
        except Exception as e:
            logger.error(f"render_header 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

     


    def onColumnResized(self, column_index, old_width, new_width):
        """컬럼 너비가 변경되었을 때 호출되는 메서드"""
        try:
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return
                
            if not hasattr(self, 'original_state'):
                return
            
            # API 데이터에서 해당 컬럼 찾아 너비 업데이트
            for api_data in self.api_datas_변경:
                if api_data['order'] == column_index:
                    # 너비 업데이트
                    api_data['column_width'] = new_width
                    break

            
        except Exception as e:
            logger.error(f"onColumnResized 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def onHeaderSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        """헤더 섹션이 이동되었을 때 호출되는 메서드"""
        try:
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return
            
            # 모든 컬럼에 대해 order 업데이트
            for i in range(self.model.columnCount()):
                visual_index = self.header.visualIndex(i)
                column_header_text = self.model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                column_header_text = column_header_text.replace('[V] ', '').replace('[ ] ', '')
                
                for api_data in self.api_datas_변경:
                    if api_data['display_name'] == column_header_text:
                        api_data['order'] = visual_index
                        break
        except Exception as e:
            logger.error(f"onHeaderSectionMoved 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def cancel_table_config_mode(self):
        """테이블 설정 모드  cancel : 복원"""
        try:
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return
            
            # 1. 설정 모드 비활성화
            self.config_mode_active = False
            
            # 2. 시그널 연결 해제
            self.header.sectionDoubleClicked.disconnect(self.onHeaderSectionDoubleClicked)
            self.header.customContextMenuRequested.disconnect(self.showHeaderContextMenu)
            self.header.sectionMoved.disconnect(self.onHeaderSectionMoved)
            self.header.sectionResized.disconnect(self.onColumnResized)
            
            # 3. 헤더 설정 원래대로 복원
            self.header.setSectionsMovable(False)
            self.header.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
            
            # 4. 원본 상태 복원
            if hasattr(self, 'original_state'):
                # 4.1. 원본 헤더 텍스트 복원
                for i, header_text in enumerate(self.original_state['headers']):
                    self.model.setHeaderData(i, Qt.Orientation.Horizontal, header_text, Qt.ItemDataRole.DisplayRole)
                self.handler._headers = self.original_state['headers'].copy()
                
                # 4.2. 원본 컬럼 순서 복원
                for logical_index, visual_index in enumerate(self.original_state['column_order']):
                    current_visual_index = self.header.visualIndex(logical_index)
                    if current_visual_index != visual_index:
                        self.header.moveSection(current_visual_index, visual_index)
                
                # 4.3. 원본 컬럼 너비 복원
                for i, width in enumerate(self.original_state['column_widths']):
                    self.header.resizeSection(i, width)

                
                # 4.4. 원본 숨김 컬럼 복원
                for i in range(self.model.columnCount()):
                    self.handler.setColumnHidden(i, i in self.original_state['hidden_columns'])
                
                # 4.5. 모델의 hidden_columns 복원
                self.handler._hidden_columns = self.original_state['hidden_columns'].copy()
                
                # 4.6. 원본 API 데이터 복원
                self.handler._table_config_api_datas = [deepcopy(obj) for obj in self.original_state['table_config_api_datas']]
            
            # 5. 헤더 업데이트
            self.header.update()
            
            # 6. 사용자에게 알림
            User_Toast(INFO.MAIN_WINDOW, title="테이블 설정 모드 취소", text="테이블 설정 모드가 취소되었읍니다.", duration=3000, style='INFORMATION')
        
        except Exception as e:
            logger.error(f"cancel_table_config_mode 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
        
    
    def onHeaderSectionDoubleClicked(self, logicalIndex):
        """헤더 섹션 더블 클릭 시 이름 변경 다이얼로그 표시"""
        try:
            logger.debug(f"onHeaderSectionDoubleClicked : {logicalIndex}")
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return

            current_text = self.model.headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            current_text = current_text.replace('[V] ', '').replace('[ ] ', '')
            
            # 입력 다이얼로그 표시
            new_text, ok = QInputDialog.getText(
                self.handler, 
                "컬럼 이름 변경", 
                "새 이름을 입력하세요:", 
                QLineEdit.EchoMode.Normal, 
                str(current_text)
            )
            
            # 확인 버튼 클릭 시 이름 변경
            if ok and new_text:
                logger.debug(f"onHeaderSectionDoubleClicked : {new_text}")
                # self.model.setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.DisplayRole)
                logger.debug(f"onHeaderSectionDoubleClicked : {self.__get_obj_by_order(logicalIndex)}")
                if ( obj:=self.__get_obj_by_order(logicalIndex) ):
                    obj['display_name'] = new_text
                    self.handler._headers[logicalIndex] = new_text
                logger.debug(f"onHeaderSectionDoubleClicked : {obj}")
                self.render_header()
        except Exception as e:
            logger.error(f"onHeaderSectionDoubleClicked 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
        
        
    def showHeaderContextMenu(self, pos:QPoint):
        """헤더 컨텍스트 메뉴 표시"""
        try:
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return
              
            logical_index = self.header.logicalIndexAt(pos)
            
            if logical_index >= 0:
                menu = QMenu(self.handler)
                
                # 이름 변경 액션
                rename_action = menu.addAction("이름 변경")
                rename_action.triggered.connect(lambda: self.onHeaderSectionDoubleClicked(logical_index))
                
                # 숨김 토글 액션
                is_checked = bool ( logical_index in self.handler._hidden_columns )
                hide_text = "숨기기" if not is_checked else "표시하기"
                hide_action = menu.addAction(hide_text)
                hide_action.triggered.connect(lambda: self.toggleColumnVisibility(logical_index))
                
            menu.exec(self.header.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"showHeaderContextMenu 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
    

    def __get_obj_by_order(self, order):
        """order에 해당하는 obj 반환"""
        for obj in self.api_datas_변경:
            if obj['order'] == order:
                return obj
        return None
    
    def toggleColumnVisibility(self, logical_index):
        """컬럼 숨김 상태 토글"""
        try:
            if logical_index in self.handler._hidden_columns:
                self.handler._hidden_columns.remove(logical_index)
                if ( obj:=self.__get_obj_by_order(logical_index) ):    
                    obj['is_hidden'] = False
            else:
                self.handler._hidden_columns.append(logical_index)
                if ( obj:=self.__get_obj_by_order(logical_index) ):
                    obj['is_hidden'] = True

            self.render_header()
        except Exception as e:
            logger.error(f"toggleColumnVisibility 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

        
    def get_changed_api_datas(self):
        """원본 API 데이터와 비교하여 변경된 데이터만 반환"""
        try:
            logger.debug( f" get_changed_api_datas : {self.api_datas_변경}")
            if self.handler.check_api_datas_available():
                return self.api_datas_변경
            else:
                if not hasattr(self, 'original_state'):
                    return []
                
            current_api_datas = self.api_datas_변경
            if hasattr(self, 'original_state') and self.original_state:
                original_api_datas = self.original_state.get('table_config_api_datas', [])
            else:
                original_api_datas = []
                
            changed_api_datas = [ _obj1 for _obj1, _obj2 in zip(current_api_datas, original_api_datas) 
                                 if _obj1 != _obj2 ]
            logger.info(f"변경된 API 데이터: {changed_api_datas}")

            return changed_api_datas
            
        except Exception as e:
            logger.error(f"get_changed_api_datas 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            return []
        


# class Header_설정_View(QHeaderView):
#     def __init__(self, table_view:QTableView, header_info: dict):
#         super().__init__(Qt.Orientation.Horizontal, table_view)
#         self.table_view = table_view
#         self.model = table_view.model()



        
#         # 딕셔너리에서 헤더 설정 적용
#         self.applyHeaderSettings(header_info)

#         # 설정 모드에 필요한 설정 변경
#         self.setSectionsClickable(True)
#         self.setSectionsMovable(True)

#         # 컨텍스트 메뉴 설정
#         self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
#         self.customContextMenuRequested.connect(self.showContextMenu)


#         # 명시적으로 업데이트 요청
#         QTimer.singleShot(100, self.update)
    
#     def applyHeaderSettings(self, header_info: dict):
#         """ 딕셔너리에서 헤더 설정 적용 """
#         # 기본 헤더 설정 적용
#         self.setSectionResizeMode(header_info['section_resize_mode'])
#         self.setDefaultSectionSize(header_info['default_section_size'])
#         self.setMinimumSectionSize(header_info['minimum_section_size'])
#         self.setDefaultAlignment(header_info['default_alignment'])
#         self.setHighlightSections(header_info['highlight_sections'])
#         self.setStretchLastSection(header_info['stretch_last_section'])

#         # 섹션 크기 적용
#         for i, size in enumerate(header_info['section_sizes']):
#             self.resizeSection(i, size)
        
#         # 설정 모드에서는 모든 컬럼 표시
#         for i in range(header_info['column_count']):
#             self.setSectionHidden(i, False)
        
#         # 정렬 표시기 적용
#         sort_section, sort_order = header_info['sort_indicator']
#         self.setSortIndicator(sort_section, sort_order)
        

#     def copyHeaderSettings(self, original_header:QHeaderView):
#         """ 기본 헤더의 설정을 복사하여 동일한 View 유지 """
#         self.setSectionResizeMode(original_header.sectionResizeMode(0))
#         self.setDefaultSectionSize(original_header.defaultSectionSize())
#         self.setMinimumSectionSize(original_header.minimumSectionSize())
#         self.setDefaultAlignment(original_header.defaultAlignment())
#         self.setHighlightSections(original_header.highlightSections())
        

                
#         # 중요: 헤더 길이 설정 - 이 부분이 누락되어 문제 발생
#         self.setStretchLastSection(original_header.stretchLastSection())

#         # 원본 헤더의 섹션 크기와 숨김 상태 복사
#         for i in range(self.model.columnCount()):
#             # 섹션 크기 복사
#             width = original_header.sectionSize(i)
#             self.resizeSection(i, width)
            
#             # 숨김 상태 복사 - 설정 모드에서는 모든 컬럼 표시
#             hidden = i in self.model._hidden_columns
#             self.setSectionHidden(i, False)  # 설정 모드에서는 모든 컬럼 표시
        
#         # 정렬 표시기 복사
#         if hasattr(original_header, 'sortIndicatorSection'):
#             self.setSortIndicator(original_header.sortIndicatorSection(), 
#                                  original_header.sortIndicatorOrder())

#         ### google AI
#         # for section in range( self.model.columnCount() ):
#         #     self.setSectionHidden(section, original_header.isSectionHidden(section))
#         #     self.resizeSection(section, original_header.sectionSize(section))

#         # self.setSortIndicator(original_header.sortIndicatorSection(), original_header.sortIndicatorOrder())

#     def showContextMenu(self, pos):
#         """컨텍스트 메뉴 표시"""
#         logical_index = self.logicalIndexAt(pos)
#         if logical_index < 0:
#             return
            
#         menu = QMenu(self)
        
#         # 컬럼 숨김 토글 액션
#         toggle_action = QAction("숨기기" if logical_index not in self.model._hidden_columns else "표시하기", self)
#         toggle_action.triggered.connect(lambda: self.toggleColumnVisibility(logical_index))
#         menu.addAction(toggle_action)
        
#         # 모든 컬럼 표시 액션
#         show_all_action = QAction("모든 컬럼 표시", self)
#         show_all_action.triggered.connect(self.showAllColumns)
#         menu.addAction(show_all_action)
        
#         menu.exec(self.mapToGlobal(pos))

#     def event(self, event):
#         if event.type() == QEvent.Type.Paint:

#         return super().event(event)
    
#     def paintEvent(self, event):

#         # super().paintEvent(event)
#         painter = QPainter(self)
#         painter.begin(self)
#         self.paintSection(painter, QRect(), 0)
#         painter.end()


#     def paintSection(self, painter, rect, logicalIndex):

#         try:
#             painter.save()

#             ### 숨겨질 컬럼이면 회색 배경
#             if logicalIndex in self.model._hidden_columns:

#                 painter.fillRect(rect, QColor(200, 200, 1000))
#                 painter.setPen(QPen(QColor(100, 100, 100)))
#                 text = f"\u274C {self.handler._headers[logicalIndex]}"
#             else:
#                 # 일반 컬럼은 기본 배경

#                 painter.fillRect(rect, QColor(255, 255, 255))  # #ffcc80
#                 painter.setPen(QPen(QColor(0, 0, 0)))
#                 text = self.handler._headers[logicalIndex]
#             painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, text)

#             painter.restore()
#             # 디버그 메시지

#         except Exception as e:

#             painter.restore()
