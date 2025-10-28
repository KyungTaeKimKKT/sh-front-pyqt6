from modules.common_import_v2 import *

class TableView_Config_Table(Base_Table_View):
	pass

class TableModel_Config_Table(Base_Table_Model):
	pass

class Delegate_Config_Table(Base_Delegate):
	pass


class Wid_table_Config_Table( Wid_table_Base_V2   ):
	""" ✅ 25-7-15 기준 :  Table_Menus는 없다.
		수동으로 table 설정은 막아놓은 상태다
	"""
	
	def setup_table(self):
		self.view = TableView_Config_Table(self) 
		self.model = TableModel_Config_Table(self.view)
		self.delegate = Delegate_Config_Table(self.view)
		self.view.setModel(self.model)
		self.view.setItemDelegate(self.delegate)

		

