from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import numpy as np
import traceback
from modules.logging_config import get_plugin_logger


# class PandasModel(QAbstractTableModel):
#     def __init__(self, data):
#         super().__init__()
#         self._data = data

#     def rowCount(self, parent=None):
#         return len(self._data.index)

#     def columnCount(self, parent=None):
#         return len(self._data.columns)

#     def data(self, index, role=Qt.ItemDataRole.DisplayRole):
#         if role == Qt.ItemDataRole.DisplayRole:
#             value = self._data.iloc[index.row(), index.column()]
#             return str(value)
#         return None

#     def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
#         if role == Qt.ItemDataRole.DisplayRole:
#             if orientation == Qt.Orientation.Horizontal:
#                 return str(self._data.columns[section])
#             if orientation == Qt.Orientation.Vertical:
#                 return str(self._data.index[section])
#         return None

#     def sort(self, column, order):
#         self.layoutAboutToBeChanged.emit()
#         col_name = self._data.columns[column]
#         self._data = self._data.sort_values(col_name, 
#                                           ascending=order == Qt.SortOrder.AscendingOrder)
#         self.layoutChanged.emit()


# class PivotTableDialog(QDialog):
#     def __init__(self, parent, json_data:list[dict], **kwargs):
#         super().__init__(parent)
#         self.setWindowTitle("치수별 수량 피벗 테이블")
#         self.resize(400, 600)
        
#         # DataFrame 생성
#         df = pd.DataFrame(json_data)

#         # 치수 분리 함수
#         def split_dimensions(dim_str):
#             if pd.isna(dim_str) or dim_str == '':
#                 return pd.Series({'두께': np.nan, '가로': np.nan, '세로': np.nan})
#             try:
#                 parts = dim_str.split('*')
#                 if len(parts) == 3:
#                     두께 = float(parts[0].replace('T', ''))
#                     가로 = int(parts[1])
#                     세로 = int(parts[2])
#                     return pd.Series({'두께': 두께, '가로': 가로, '세로': 세로})
#             except:
#                 return pd.Series({'두께': np.nan, '가로': np.nan, '세로': np.nan})
#             return pd.Series({'두께': np.nan, '가로': np.nan, '세로': np.nan})
        
#         # 치수 분리
#         dimensions = df['치수'].apply(split_dimensions)
#         df = pd.concat([df, dimensions], axis=1)

#         # 피벗 테이블 생성
#         pivot_data = df.groupby(['치수', '두께', '가로', '세로'])['수량'].sum().reset_index()
#         pivot_data = pivot_data[pivot_data['치수'] != '']  # 빈 치수 제외
        
#         # 테이블 뷰 설정
#         self.table_view = QTableView()
#         self.model = PandasModel(pivot_data)
#         self.table_view.setModel(self.model)
#         self.table_view.setSortingEnabled(True)
        
#         # 레이아웃
#         layout = QVBoxLayout()
#         layout.addWidget(self.table_view)
#         self.setLayout(layout)
        


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class PivotTableDialog(QDialog):
    def __init__(self, parent, json_data, **kwargs ):
        super().__init__(parent)
        self.setWindowTitle("치수별 수량 피벗 테이블")
        self.resize(800, 600)
        
        # DataFrame 생성
        df = pd.DataFrame(json_data)
        
        # 치수 분리 함수
        def split_dimensions(row):
            if pd.isna(row['치수']) or row['치수'] == '':
                return pd.Series({'두께': None, '가로': None, '세로': None})
            try:
                dims = row['치수'].split('*')
                thickness = float(dims[0].replace('T', ''))
                width = int(float(dims[1]))  # float로 변환 후 int로 변환
                length = int(float(dims[2]))  # float로 변환 후 int로 변환
                return pd.Series({'두께': thickness, '가로': width, '세로': length})
            except:
                return pd.Series({'두께': None, '가로': None, '세로': None})
        
        # 치수 분리 적용
        df[['두께', '가로', '세로']] = df.apply(split_dimensions, axis=1)
        
        # 피벗 테이블 생성
        pivot_table = pd.pivot_table(df, 
                                   values='수량',
                                   index=['치수', '두께', '가로', '세로'],
                                   aggfunc='sum').reset_index()
        
        # GUI 설정
        layout = QVBoxLayout()
        table_view = QTableView()
        
        # 모델 생성
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['치수', '두께', '가로', '세로', '수량'])
        
        # 데이터 추가
        for _, row in pivot_table.iterrows():
            items = [
                QStandardItem(str(row['치수'])),
                QStandardItem(str(row['두께']) if pd.notna(row['두께']) else ''),
                QStandardItem(str(int(row['가로'])) if pd.notna(row['가로']) else ''),  # int로 변환
                QStandardItem(str(int(row['세로'])) if pd.notna(row['세로']) else ''),  # int로 변환
                QStandardItem(str(int(row['수량'])))
            ]
            model.appendRow(items)
        
        # 정렬 프록시 모델 설정
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        table_view.setModel(proxy_model)
        
        # 정렬 활성화
        table_view.setSortingEnabled(True)
        
        layout.addWidget(table_view)
        self.setLayout(layout)