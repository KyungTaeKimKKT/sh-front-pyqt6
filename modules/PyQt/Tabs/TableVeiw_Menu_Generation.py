import traceback
from modules.logging_config import get_plugin_logger
# 




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Table_menu:

	table_Sorting = False	

	New = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				"title": "New",
				"tooltip" :"신규 작성합니다",
				"objectName" : 'New',
				"enabled" : True,
	}

	Upgrade = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-upgrade_row')",
				"title": "Upgrade",
				"tooltip" :"Upgrade합니다.",
				"objectName" : 'Upgrade',
				"enabled" : True,
	}

	Edit = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-edit_row')",
				"title": "Edit",
				"tooltip" :"Edit합니다.",
				"objectName" : 'Edit',
				"enabled" : False,
	}

	Delete = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-delete_row')",
				"title": "Delete",
				"tooltip" :"DB에서 Delete합니다.",
				"objectName" : 'Delete',
				"enabled" : True,
	}

	View = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-view_row')",
				"title": "View",
				"tooltip" :"View합니다.",
				"objectName" : 'View',
				"enabled" : False,
	}

	Search = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-search')",
				"title": "Search",
				"tooltip" :"Search합니다.",
				"objectName" : 'Search',
				"enabled" : True,
	}

	Export_to_Excel = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				"title": "Export_to_excel",
				"tooltip" :"Excel로 table을 저장합니다.",
				"objectName" : 'Export_to_excel',
				"enabled" : True,
	}

	Preview = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-preview')",
				"title": "Preview",
				"tooltip" :"Preview합니다.",
				"objectName" : 'Preview',
				"enabled" : True,
	}

	Print = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-print')",
				"title": "Print",
				"tooltip" :"Print 합니다.",
				"objectName" : 'Print',
				"enabled" : True,
	}

	Form_New = {
				"icon" : "QtGui.QIcon(':/table-icons/form-new')",
				"title": "Form_New",
				"tooltip" :"Form_New합니다.",
				"objectName" : 'Form_New',
				"enabled" : True,
	}

	Form_New_현대 = {
				"icon" : "QtGui.QIcon(':/table-icons/form-new')",
				"title": "Form_New_현대",
				"tooltip" :"Form_New합니다.",
				"objectName" : 'Form_New_현대',
				"enabled" : True,
	}
	Form_New_OTIS = {
				"icon" : "QtGui.QIcon(':/table-icons/form-new')",
				"title": "Form_New_OTIS",
				"tooltip" :"Form_New합니다.",
				"objectName" : 'Form_New_OTIS',
				"enabled" : True,
	}
	Form_New_TKE = {
				"icon" : "QtGui.QIcon(':/table-icons/form-new')",
				"title": "Form_New_TKE",
				"tooltip" :"Form_New합니다.",
				"objectName" : 'Form_New_TKE',
				"enabled" : True,
	}
	Form_New_기타 = {
				"icon" : "QtGui.QIcon(':/table-icons/form-new')",
				"title": "Form_New_기타",
				"tooltip" :"Form_New합니다.",
				"objectName" : 'Form_New_기타',
				"enabled" : True,
	}

	Form_Edit = {
				"icon" : "QtGui.QIcon(':/table-icons/form-edit')",
				"title": "Form_Edit",
				"tooltip" :"Form_Edit합니다.",
				"objectName" : 'Form_Edit',
				"enabled" : True,
	}

	Form_View = {
				"icon" : "QtGui.QIcon(':/table-icons/form-view')",
				"title": "Form_View",
				"tooltip" :"Form_View합니다.",
				"objectName" : 'Form_View',
				"enabled" : True,
	}

	Set_row_span = {
					"icon" : "QtGui.QIcon(':/table-icons/tb-set_row_span')",
					"title": "Set_row_span",
					"tooltip" :"row cell 통합합니다.",
					"objectName" : 'Set_row_span',
					"enabled" : True,
		}

	Reset_row_span = {
					"icon" : "QtGui.QIcon(':/table-icons/tb-reset_row_span')",
					"title": "Reset_row_span",
					"tooltip" :"row cell 통합 해제합니다.",
					"objectName" : 'Reset_row_span',
					"enabled" : True,
		}

	Hide_column = {
					"icon" : "QtGui.QIcon(':/table-icons/tb-hide_column')",
					"title": "Hide_column",
					"tooltip" :"column을 숨깁니다.",
					"objectName" : 'Hide_column',
					"enabled" : False,
		}

	Show_column = {
					"icon" : "QtGui.QIcon(':/table-icons/tb-show_column')",
					"title": "Show_column",
					"tooltip" :"숨겨진 column을 해제합니다.",
					"objectName" : 'Show_column',
					"enabled" : False,
		}

	완료처리 = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				"title": "완료",
				"tooltip" :"완료합니다",
				"objectName" : '완료처리',
				"enabled" : True,
	}

	ECO = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-ECO')",
				"title": "ECO(수정)",
				"tooltip" :"배포된 내용을 변경, 버젼 UP합니다.",
				"objectName" : 'ECO',
				"enabled" : True,
	}
	
	작성완료= {
				"icon" : "QtGui.QIcon(':/table-icons/tb-작성완료')",
				"title": "작성완료(배포)",
				"tooltip" :"배포하게 됩니다.(등록page에서 삭제되고, 배포page에서 확인 가능합니다.)",
				"objectName" : '작성완료',
				"enabled" : True,
	}
	디자인의뢰= {
				"icon" : "QtGui.QIcon(':/table-icons/tb-디자인의뢰')",
				"title": "디자인의뢰",
				"tooltip" :"디자인의뢰 처리됩니다.(등록page에서 삭제되고, 이력조회 page에서 확인 가능합니다.)",
				"objectName" : '디자인의뢰',
				"enabled" : True,
	}
	디자인접수= {
			"icon" : "QtGui.QIcon(':/table-icons/tb-디자인접수')",
			"title": "디자인접수",
			"tooltip" :"디자인접수 처리됩니다.",
			"objectName" : '디자인접수',
			"enabled" : True,
	}
	디자인완료= {
			"icon" : "QtGui.QIcon(':/table-icons/tb-디자인완료')",
			"title": "디자인완료",
			"tooltip" :"디자인완료 처리됩니다.",
			"objectName" : '디자인완료',
			"enabled" : True,
	}

	File첨부 = {
			"icon" : "QtGui.QIcon(':/table-icons/tb-File첨부')",
			"title": "File첨부",
			"tooltip" :"File을 첨부합니다.",
			"objectName" : 'File첨부',
			"enabled" : True,
	}

	활동현황_추가 = {
			"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_추가')",
			"title": "활동현황_추가",
			"tooltip" :"활동현황을 추가합니다.",
			"objectName" : '활동현황_추가',
			"enabled" : True,
	}

	활동현황_보기 = {
			"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_보기')",
			"title": "활동현황_보기",
			"tooltip" :"File을 첨부합니다.",
			"objectName" : '활동현황_보기',
			"enabled" : True,
	}
	활동종료 = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-활동종료')",
				"title": "활동종료",
				"tooltip" :"활동종료합니다",
				"objectName" : '활동종료',
				"enabled" : True,
	}

	Select = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				"title": "Select",
				"tooltip" :"해당 row를 선택합니다.",
				"objectName" : 'Select',
				"enabled" : True,
	}

	MRP = {
				"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				"title": "MRP(소요량계산)",
				"tooltip" :"HTM sheet 소요량계산을 합니다.",
				"objectName" : 'MRP',
				"enabled" : True,
	}
	의장도_등록 = {
		"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_삭제')",
		"title": "의장도_등록",
		"tooltip" :"의장도 등록합니다.",
		"objectName" : '의장도_등록',
		"enabled" : True,
	}

	Paste_Table = {
		"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_삭제')",
		"title": "Paste Table from clipboard",
		"tooltip" :"excel table에서 copy된 table을 붙여넣기 합니다.",
		"objectName" : 'Paste_Table',
		"enabled" : True,
	}

	JAMB_지시서 = {
		"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_삭제')",
		"title": "JAMB_지시서",
		"tooltip" :"JAMB_지시서를 등록합니다.",
		"objectName" : 'JAMB_지시서',
		"enabled" : True,
	}

	위치보기 =  {
		"icon" : "QtGui.QIcon(':/table-icons/tb-활동현황_삭제')",
		"title": "위치보기",
		"tooltip" :"구글맵으로 위치를 봅니다..",
		"objectName" : '위치보기',
		"enabled" : True,
	}


	# with open(':/json-table-menu/h-context-menu.json') as json_file:
	# 	h_header_context_menu = json.load(json_file)

	def __init__(self):
		self.default_h_list = [
			'New','Upgrade','Edit','Delete','View',
			'seperator',
			'Search',
			'seperator',
			'Export_to_Excel',
			'seperator',
			'Preview', 'Print',
			'seperator',
			'Form_New'
						 ]
		self.default_v_list = [
			'Set_row_span', 'Reset_row_span',
			'seperator',
			'Hide_column', 'Show_column',
		]

		self.default_h_menu = self.generate(self.default_h_list)
		self.default_v_menu = self.generate(self.default_v_list)
	########## h_header_context_Menu

	def generate(self, menulist:list=[]) ->dict:
		menuDict={}
		for index, menu in enumerate(menulist):
			if menu == 'seperator':
				menuDict[f'seperator-{index}'] = ''
			
			else :
				menuDict[menu] = getattr(self, menu)

		return menuDict

