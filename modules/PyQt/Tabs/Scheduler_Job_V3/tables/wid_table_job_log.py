from modules.common_import_v2 import *

class View_job_log(Base_Table_View):
    pass

class Model_job_log(Base_Table_Model):
    pass

class Delegate_job_log(Base_Delegate):
    pass

class Wid_table_job_log(Wid_table_Base_V2):

    def setup_table(self):
        self.view = View_job_log(self)
        self.model = Model_job_log(self.view)
        self.delegate = Delegate_job_log(self.view)

        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)