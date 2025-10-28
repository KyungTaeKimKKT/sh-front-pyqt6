from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from info import Info_SW as INFO
from stylesheet import StyleSheet as ST
from modules.PyQt.User.toast import User_Toast
from datetime import datetime

from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model

from icecream import ic
ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()
ic.disable()

import traceback
import logging
logger = logging.getLogger(__name__)

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
#                 text = f"\u274C {self.model._headers[logicalIndex]}"
#             else:
#                 # 일반 컬럼은 기본 배경

#                 painter.fillRect(rect, QColor(255, 255, 255))  # #ffcc80
#                 painter.setPen(QPen(QColor(0, 0, 0)))
#                 text = self.model._headers[logicalIndex]
#             painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, text)

#             painter.restore()
#             # 디버그 메시지

#         except Exception as e:

#             painter.restore()



class Base_Table_View_환경설정:
    """ 환경설정 모드 클래스 : 환경 설정 METHOD 정의 """


    def enable_table_config_mode(self):
        """테이블 설정 모드 활성화"""
        try:
            # 설정 모드 활성화 플래그 설정 및 현재 model
            self.config_mode_active = True            
            model_instance = self.model()
            self.setupConfigHeader()
            from copy import deepcopy
            # 원래 상태 저장
            self.original_state = {
                'hidden_columns': [i for i in range(model_instance.columnCount()) if self.isColumnHidden(i)],
                'column_widths': [self.columnWidth(i) for i in range(model_instance.columnCount())],
                'column_order': [self.horizontalHeader().visualIndex(i) for i in range(model_instance.columnCount())],
                'headers': [ header for header in model_instance._headers ],
                'table_config_api_datas': [ deepcopy(obj) for obj in model_instance._table_config_api_datas ],
                # 'api_datas_변경': [ deepcopy(obj) for obj in model_instance._table_config_api_datas ],
            }
            #### 변경이록 기록 api_datas_변경 생성
            self.api_datas_변경 = [ deepcopy(obj) for obj in model_instance._table_config_api_datas ]

            # 1. 모든 숨겨진 컬럼 표시
            for i in range(model_instance.columnCount()):
                self.setColumnHidden(i, False)
            
            self.render_header(model_instance)
            
            # 사용자에게 설정 모드 알림
            User_Toast(INFO.MAIN_WINDOW, title="테이블 설정 모드", text="테이블 설정 모드가 활성화되었읍니다.", duration=3000, style='INFORMATION')
            self.horizontalHeader().viewport().update()

        except Exception as e:

            import traceback
            traceback.print_exc()

    def render_header(self, model_instance):
        """헤더 렌더링"""
        # 2. 체크박스 + name 동시 표시
        txt_hidden , txt_visible =  '[V] ', '[ ] '
        display_name_with_checkbox = {
            col_idx: txt_hidden + (model_instance._headers[col_idx]).replace('[V] ', '').replace('[ ] ', '') if col_idx in model_instance._hidden_columns else txt_visible + (model_instance._headers[col_idx]).replace('[V] ', '').replace('[ ] ', '')
            for col_idx in range(model_instance.columnCount())
        }

        for col_idx, display_name in display_name_with_checkbox.items():
            model_instance.setHeaderData(col_idx, Qt.Orientation.Horizontal, display_name, Qt.ItemDataRole.DisplayRole)
        self.horizontalHeader().update()

     
    def setupConfigHeader(self):
        """설정 모드용 커스텀 헤더 설정"""
        header = self.horizontalHeader()
        
        # 헤더 설정
        header.setSectionsMovable(True)  # 드래그 앤 드롭으로 order 변경 가능
        header.setSectionsClickable(True)
        header.sectionDoubleClicked.connect(self.onHeaderSectionDoubleClicked)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self.showHeaderContextMenu)
        header.sectionMoved.connect(self.onHeaderSectionMoved)
        header.sectionResized.connect(self.onColumnResized)

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

            import traceback
            traceback.print_exc()

    def onHeaderSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        """헤더 섹션이 이동되었을 때 호출되는 메서드"""
        if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
            return

        
        # 모든 컬럼의 현재 order 업데이트
        model_instance = self.model()
        header = self.horizontalHeader()
        
        # 모든 컬럼에 대해 order 업데이트
        for i in range(model_instance.columnCount()):
            visual_index = header.visualIndex(i)
            column_header_text = model_instance.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            column_header_text = column_header_text.replace('[V] ', '').replace('[ ] ', '')
            
            for api_data in self.api_datas_변경:
                if api_data['display_name'] == column_header_text:
                    api_data['order'] = visual_index
                    break


    def resotre_and_disable_table_config_mode(self):
        """테이블 설정 모드 비활성화"""
        try:
            if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
                return
            
            # 1. 설정 모드 비활성화
            self.config_mode_active = False
            
            # 2. 이벤트 필터 제거
            self.horizontalHeader().viewport().removeEventFilter(self)
            
            # 3. 헤더 이벤트 연결 해제
            header = self.horizontalHeader()
            try:
                header.sectionDoubleClicked.disconnect(self.onHeaderSectionDoubleClicked)
            except:
                pass
            
            # 4. 모델에 숨김 컬럼 정보 업데이트
            model_instance = self.model()
            if hasattr(model_instance, '_hidden_columns'):
                model_instance._hidden_columns = [i for i, checked in self.column_checkboxes.items() if checked]
            
            # 5. 원래 헤더 텍스트 복원
            if hasattr(self, 'original_headers'):
                for i, text in self.original_headers.items():
                    model_instance.setHeaderData(i, Qt.Orientation.Horizontal, text, Qt.ItemDataRole.DisplayRole)
            
            # 6. 숨김 상태 적용
            for i, checked in self.column_checkboxes.items():
                self.setColumnHidden(i, checked)
            
            # 7. 헤더 업데이트
            header.update()
            
            # 사용자에게 알림
            User_Toast(INFO.MAIN_WINDOW, title="테이블 설정 모드", text="테이블 설정 모드가 종료되었읍니다.", duration=3000, style='INFORMATION')
        
        except Exception as e:

            import traceback
    
    
    def onHeaderSectionDoubleClicked(self, logicalIndex):
        """헤더 섹션 더블 클릭 시 이름 변경 다이얼로그 표시"""
        if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
            return
        
        model = self.model()
        current_text = model.headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        current_text = current_text.replace('[V] ', '').replace('[ ] ', '')
        
        # 입력 다이얼로그 표시
        new_text, ok = QInputDialog.getText(
            self, 
            "컬럼 이름 변경", 
            "새 이름을 입력하세요:", 
            QLineEdit.EchoMode.Normal, 
            str(current_text)
        )
        
        # 확인 버튼 클릭 시 이름 변경
        if ok and new_text:
            model.setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.DisplayRole)
            if ( obj:=self.__get_obj_by_order(logicalIndex) ):
                obj['display_name'] = new_text
            self.render_header(model)
        
    def showHeaderContextMenu(self, pos):
        """헤더 컨텍스트 메뉴 표시"""
        if not hasattr(self, 'config_mode_active') or not self.config_mode_active:
            return
        
        header = self.horizontalHeader()
        logical_index = header.logicalIndexAt(pos)
        model = self.model()
        
        if logical_index >= 0:
            menu = QMenu(self)
            
            # 이름 변경 액션
            rename_action = menu.addAction("이름 변경")
            rename_action.triggered.connect(lambda: self.onHeaderSectionDoubleClicked(logical_index))
            
            # 숨김 토글 액션
            is_checked = bool ( logical_index in model._hidden_columns )
            hide_text = "숨기기" if not is_checked else "표시하기"
            hide_action = menu.addAction(hide_text)
            hide_action.triggered.connect(lambda: self.toggleColumnVisibility(logical_index))
            
            menu.exec(header.mapToGlobal(pos))
    

    def __get_obj_by_order(self, order):
        """order에 해당하는 obj 반환"""
        for obj in self.api_datas_변경:
            if obj['order'] == order:
                return obj
        return None
    
    def toggleColumnVisibility(self, logical_index):
        """컬럼 숨김 상태 토글"""
        if logical_index in self.model()._hidden_columns:
            self.model()._hidden_columns.remove(logical_index)
            if ( obj:=self.__get_obj_by_order(logical_index) ):    
                obj['is_hidden'] = False
        else:
            self.model()._hidden_columns.append(logical_index)
            if ( obj:=self.__get_obj_by_order(logical_index) ):
                obj['is_hidden'] = True

        self.render_header(self.model())

        
    def get_changed_api_datas(self):
        """원본 API 데이터와 비교하여 변경된 데이터만 반환"""
        try:
            if not hasattr(self, 'original_state'):
                return []
                
            current_api_datas = self.api_datas_변경
            original_api_datas = self.original_state.get('table_config_api_datas', [])
            changed_api_datas = [ _obj1 for _obj1, _obj2 in zip(current_api_datas, original_api_datas) 
                                 if _obj1 != _obj2 ]
            logger.info(f"변경된 API 데이터: {changed_api_datas}")

            return changed_api_datas
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            return []