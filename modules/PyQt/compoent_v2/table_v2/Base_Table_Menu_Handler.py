from __future__ import annotations
from typing import TYPE_CHECKING    

from config import Config as APP
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


import modules.user.utils as Utils
import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from modules.PyQt.compoent_v2.table.Base_Table_View import Base_Table_View
    from modules.PyQt.compoent_v2.table.Base_Table_Model import Base_Table_Model

class Base_Table_Menu_Handler:
    def __init__(self, view:Base_Table_View):
        self.view = view
      

    #### sorting 관련
    def enable_sorting(self, enable:bool=True):
        logger.debug(f" {self.__class__.__name__} : enable_sorting: {enable}")
        header = self.view.horizontalHeader()
        header.setSortIndicatorShown(enable)
        self.view.setSortingEnabled(enable)
    
    def is_sorting_enabled(self):
        return self.view.isSortingEnabled()

    #### slot_h_header
    def slot_h_header__sort_ascend(self, colNo:int):
        logger.info(f"[Base] 오름차순 정렬 실행 colNo: {colNo}")
        self.view.sortByColumn(colNo, Qt.SortOrder.AscendingOrder)
        # self.view.sortByColumn(...) 예시

    def slot_h_header__sort_descend(self, colNo:int):
        logger.info(f"[Base] 내림차순 정렬 실행 colNo: {colNo}")        
        self.view.sortByColumn(colNo, Qt.SortOrder.DescendingOrder)


    ### slot v_header
    def slot_v_header__add_row(self, rowNo: int):
        model = self.view.model()
        model.request_on_add_row(rowNo)

        # logger.info(f"[Base] Row 추가 rowNo: {rowNo}")
        # model = self.view.model()
        # model.beginInsertRows(QModelIndex(), rowNo, rowNo)
        # model.insertRow(rowNo)
        # model.endInsertRows()
        # logger.info(f"[Base] Row {rowNo+1} 추가 완료")

    def slot_v_header__del_row(self, rowNo: int):
        def _del_row(model:Base_Table_Model, rowNo:int):
            model.beginRemoveRows(QModelIndex(), rowNo, rowNo)
            model.removeRow(rowNo)
            model.endRemoveRows()

        logger.info(f"[Base] Row 삭제 rowNo: {rowNo}")
                   
        try:
            id = self.view.model().get_id_dict(rowNo).get('id', -1)
            if  not id > 0:
                _del_row(self.view.model(), rowNo)
                return
            
            # tab_widget = self.view.parent().parent()
            url = f"{self.view.model().url}{id}"

            # Confirm dialog
            confirm_dialog = QMessageBox()
            confirm_dialog.setWindowTitle("DB 삭제")
            confirm_dialog.setText("DB에서 완전히 삭제됩니다.\n삭제하시겠습니까?")
            confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
            if confirm_dialog.exec() == QMessageBox.StandardButton.Yes:
                try:
                    _isok = APP.API.delete(url)
                    if _isok:
                        _del_row(self.view.model(), rowNo)
                    else:
                        logger.error(f"[Base] 삭제 실패:")

                except Exception as e:
                    logger.info(f"[Base] id is not ingeger {rowNo}, error: {e}")
                    _del_row(self.view.model(), rowNo)
            else:
                logger.info(f"[Base] 삭제 취소됨")

        except Exception as e:
            logger.info(f"[Base] id is not ingeger {rowNo}, error: {e}")
            _del_row(self.view.model(), rowNo)

    ### slot cell

    def slot_cell_menu__file_upload(self, rowNo:int, colNo:int):
        logger.info(f"[Base] Cell 파일 업로드 rowNo: {rowNo}, colNo: {colNo}")


    def slot_cell_menu__file_download(self, rowNo:int, colNo:int):
        logger.info(f"[Base] Cell 파일 다운로드 rowNo: {rowNo}, colNo: {colNo}")
        file_path = self.view.model()._data[rowNo][colNo]
        logger.info(f"[Base] Cell 파일 다운로드 file_path: {file_path}")
        Utils.func_filedownload(file_path)

    def slot_cell_menu__file_view(self, rowNo:int, colNo:int):
        logger.info(f"[Base] Cell 파일 뷰 rowNo: {rowNo}, 업로드colNo: {colNo}")
        file_path = self.view.model()._data[rowNo][colNo]
        logger.info(f"[Base] Cell 파일 view file_path: {file_path}")

        from modules.PyQt.compoent_v2.fileview.wid_fileview import FileViewer_Dialog
        dlg = FileViewer_Dialog(self.view.parent())
        dlg.add_file(file_path)
        dlg.exec()



    #### slot default
    def default_slot(self, **kwargs):
        logger.warning(f"[Base] 정의되지 않은 메뉴 액션입니다. kwargs: {kwargs}")