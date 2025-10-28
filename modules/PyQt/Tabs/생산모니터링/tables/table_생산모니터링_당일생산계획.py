from modules.common_import import *


TABLE_NAME = '당일생산계획'
HOVER_LIST = []


class TableModel_당일생산계획(Base_Table_Model):

	def _is_time_field(self, col: int) -> bool:
		return col in (self.get_column_No_by_field_name('start_time'), self.get_column_No_by_field_name('end_time'))

	def _role_display(self, row: int, col: int) -> str:		
		try:
			if self._is_time_field(col):
				attr_name = self.get_field_name_by_column_no(col)
				value = self._data[row][attr_name]
				if value and isinstance(value, str):
					try:
						# DRF 기본 포맷이 ISO 8601이므로 파싱
						dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Z(UTC) 지원
						return dt.strftime('%H:%M')  # 시:분만 출력
					except ValueError:
						return value  # 실패 시 원래 값 그대로 반환

			return super()._role_display(row, col)
		except Exception as e:
			logger.error(f"TableModel_당일생산계획._role_display : {e}")

			return 'error'

	def _role_edit(self, row: int, col: int) -> any:
		if self._is_time_field(col):
			value = self._data[row][self.get_field_name_by_column_no(col)]
			if value and isinstance(value, str):
				try:
					dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Z(UTC) 지원
					return QTime(dt.hour, dt.minute)  # 시:분만 출력				    
				except ValueError:
					return QTime.currentTime()  # 실패 시 원래 값 그대로 반환

		return super()._role_edit(row, col)

	def setData(self, index, value, role):
		if role == Qt.ItemDataRole.EditRole:
			if self._is_time_field(index.column()):
				# value가 QTime이면 그대로 사용
				if isinstance(value, QTime):
					qtime = value
				elif isinstance(value, str):
					qtime = QTime.fromString(value, 'hh:mm:ss')
				else:
					return False  # 처리 불가능한 타입

				qDate = QDate.currentDate()
				value = QDateTime(qDate, qtime).toPyDateTime().isoformat()
				self._data[index.row()][self.get_field_name_by_column_no(index.column())] = value

				return self.setData_by_edit_mode(index, value, role)	
				
			return super().setData(index, value, role)		
	


class TableView_당일생산계획(Base_Table_View):
	pass

class Delegate_당일생산계획(Base_Delegate):
	def __init__(self, parent, **kwargs):
		super().__init__(parent, **kwargs)

	def createEditor(self, parent: Optional[QObject], option: QStyleOptionViewItem, index: QModelIndex) -> Optional[QWidget]:
		model:TableModel_당일생산계획 = index.model()
		if model._is_time_field(index.column()):
			editor = QTimeEdit(parent)
			editor.setDisplayFormat('HH:mm')
			return editor
		return super().createEditor(parent, option, index)
	
	def setEditorData(self, editor: QWidget, index: QModelIndex):
		model: TableModel_당일생산계획 = index.model()
		value = model.data(index, Qt.ItemDataRole.EditRole)

		if isinstance(editor, QTimeEdit):
			if isinstance(value, QTime):
				editor.setTime(value)
			elif isinstance(value, str):  # 혹시 str이 들어오는 경우도 대비
				try:
					dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
					editor.setTime(QTime(dt.hour, dt.minute))
				except ValueError:
					pass
			return

		super().setEditorData(editor, index)  # 나머지는 부모 처리

	def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
		if isinstance(editor, QTimeEdit):
			time = editor.time()
			model.setData(index, time, Qt.ItemDataRole.EditRole)
			return

		super().setModelData(editor, model, index)

	# def user_defined_setEditorData(self, editor:QWidget, index:QModelIndex, **kwargs) -> None:

	# 	if 'time' in kwargs['key'] and kwargs['value'] is not None and isinstance(editor, QTimeEdit):

	# 		editor.setTime( QTime.fromString( kwargs['value'], 'hh:mm:ss' ) )



class Wid_Table_for_당일생산계획( Wid_table_Base_for_stacked ):

	def setup_table(self):
		self.view = TableView_당일생산계획(self)
		self.model = TableModel_당일생산계획(self.view)
		self.delegate = Delegate_당일생산계획(self.view)
		self.view.setModel(self.model)
		self.view.setItemDelegate(self.delegate)

	def init_by_parent(self):
		self.init_attributes()
		self.init_ui()
		self.connect_signals()
