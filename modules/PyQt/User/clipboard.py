from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from datetime import datetime

# https://stackoverflow.com/questions/75095259/PyQt6-copy-paste-from-a-qtablewidget-with-contextmenu-and-with-keyboardpress
class PasteClipboard_Table:
    def __init__(self, **kwargs ):
        self.datas : list[list] = []

    def run(self):
        self.clipboard = QApplication.clipboard()


        rows = self.clipboard.text().split('\n')
        # for indx_row, row in enumerate(rows):
        #     values = row.split('\t')
        #     for indx_col, value in enumerate(values):


        first_len = len( rows[0].split('\t') )
        for indx_row, row in enumerate(rows):
            values = row.split('\t')
            if len(values) == first_len:
                self.datas.append ( [value for value in  values])

        return self.datas
    
    # def check_validite(self) -> None:
    #     for data in self.datas:
    #         data:list
            
    
class PasteClipboard_Table_생지_도면정보_현대:
    def __init__(self, **kwargs ):
        self.datas : list[list] = []

        self.popList = [ 6, -3]
        self.dateList = [6,7]
        self.intList = list(range(9,19)) + [ -2]
        self.floatList = [19, -1]

    def run(self) -> None|list:
        self.clipboard = QApplication.clipboard()
        txt = self.clipboard.text()
        if not txt or '\n' not in txt or '\t' not in txt: 
            return None

        rows = self.clipboard.text().split('\n')


        first_len = len( rows[0].split('\t') )
        for indx_row, row in enumerate(rows):
            values = row.split('\t')
            if len(values) == first_len:
                valueList = [value for value in  values]
                self.datas.append ( self.convert_data(valueList) )

        return self.datas
    
    def convert_data(self, valueList:list[str]) -> list:
        ### pop and id insert
        valueList.insert(0, -1)
        for idx in self.popList:
            valueList.pop( idx)

        ### 날짜 conversion
        for idx in self.dateList:
            try:
                valueList[idx] = datetime.strptime(  valueList[idx], '%y/%m/%d' ).date()
            except:
                pass

        ### int conversion
        for idx in self.intList:
            try:
                valueList[idx] = int(valueList[idx])
            except:
                pass

        ### float conversion
        for idx in self.floatList:
            try:
                valueList[idx] = float(valueList[idx])
            except:
                pass

        return valueList

class PasteClipboard_Table_생지_HTM_현대:
    def __init__(self, **kwargs ):
        self.datas : list[list] = []

    def run(self) -> None|list:
        self.clipboard = QApplication.clipboard()
        txt = self.clipboard.text()
        if not txt or '\n' not in txt or '\t' not in txt: 
            return None

        rows = self.clipboard.text().split('\n')


        first_len = len( rows[0].split('\t') )
        for indx_row, row in enumerate(rows):
            values = row.split('\t')
            if len(values) == first_len:
                valueList = [value for value in  values]
                self.datas.append ( self.convert_data(valueList) )

        return self.datas
    
    def convert_data(self, valueList:list[str]) -> list:
 
        result = [ value for value in valueList if value ]

        
        match len(result):
            case 1:
                if 'T' in result[0].upper():
                    result[0] = self._get_치수_by_format(result[0])
                else :
                    try:
                        result[0] = int(result[0])
                    except Exception as e:

            case 2:
                if 'T' in result[0].upper():
                    result[0] = self._get_치수_by_format(result[0])
                try:
                    result[1] = int(result[1])
                except Exception as e:

        return result
    

    def _get_치수_by_format(self, data:str) -> str:
        data = data.replace('t','T').replace(' ','')
        return  data.replace("4'", '1219').replace('x','*')


class PasteClipboard_Table_생지_SPG_현대:
    def __init__(self, **kwargs ):
        self.datas : list[list] = []

    def run(self) -> None|list:
        self.clipboard = QApplication.clipboard()
        txt = self.clipboard.text()

        if not txt or '\n' not in txt or '\t' not in txt: 
            return None

        rows = self.clipboard.text().split('\n')


        first_len = len( rows[0].split('\t') )
        for indx_row, row in enumerate(rows):
            values = row.split('\t')
            if len(values) == first_len:
                valueList = [value for value in  values]
                self.datas.append ( self.convert_data(valueList) )

        return self.datas
    
    def convert_data(self, valueList:list[str]) -> list:
        result = [ value.strip().replace(' ','\n') for value in valueList if value ]

        return result
    