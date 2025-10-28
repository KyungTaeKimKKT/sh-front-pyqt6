from modules.common_import_v2 import *

class View_job_status(Base_Table_View):
    pass

class Model_job_status(Base_Table_Model):
    pass

class Delegate_job_status(Base_Delegate):
    pass

class Wid_table_job_status(Wid_table_Base_V2):

    def setup_table(self):
        self.view = View_job_status(self)
        self.model = Model_job_status(self.view)
        self.delegate = Delegate_job_status(self.view)

        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

