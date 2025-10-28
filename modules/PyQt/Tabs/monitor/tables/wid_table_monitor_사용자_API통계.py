from modules.common_import_v2 import *


class View_monitor_사용자_API통계(Base_Table_View):
    pass

class Model_monitor_사용자_API통계(Base_Table_Model):
    pass

class Delegate_monitor_사용자_API통계(Base_Delegate):
    pass

class Wid_table_monitor_사용자_API통계(Wid_table_Base_V2):
    
    def setup_table(self):
        self.view = View_monitor_사용자_API통계(self)
        self.model = Model_monitor_사용자_API통계(self.view)
        self.delegate = Delegate_monitor_사용자_API통계(self.view)

        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)



