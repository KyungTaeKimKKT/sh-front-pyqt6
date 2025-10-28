from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from modules.PyQt.compoent_v2.custom_상속.custom_combo import Custom_Combo_PageSize
class Custom_Combo_PageSizePlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialized = False
        
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return Custom_Combo_PageSize(parent)

    def name(self):
        return "Custom_Combo_PageSize"

    def group(self):
        return "Custom Widgets"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return "페이지 크기 선택을 위한 커스텀 콤보박스"

    def whatsThis(self):
        return "페이지 크기 선택을 위한 커스텀 콤보박스 위젯입니다."

    def isContainer(self):
        return False

    def domXml(self):
        return '<widget class="Custom_Combo_PageSize" name="customComboPageSize">\n' \
               '</widget>\n'

    def includeFile(self):
        return "modules.PyQt.compoent_v2.custom_상속.custom_combo_pagesize"