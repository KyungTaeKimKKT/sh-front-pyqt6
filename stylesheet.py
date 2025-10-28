from PyQt6 import QtCore, QtGui, QtWidgets
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class StyleSheet:
	COLOR_edit_disable = '#d9d9d9'
	COLOR_editing = '#f7f7b7'

	edit_disable = f"background-color:{COLOR_edit_disable};"
	edit_enable = f"background-color:white;font-weight:normal;"
	edit_ =f"background-color:{COLOR_editing};color:black;font-weight:bold;selection-color:white;selection-background-color:blue;"

	sw_upgrade_msgbox = f"background-color:yellow;color:black;font-weight:bold;"

	tb_header_stylesheet = """
						QHeaderView::section { 
							color: blue;
							border: 1px solid #6c6c6c;
							font-weight:bold;
							font-size:bolder;
							text-align:center;
							padding-top:5px;
							padding-bottom: 5px;
						}
						QTableView QHeaderView::section:vertical {
							color: black;
							background-color: #e0e0e0;
							border: 1px solid #6c6c6c;
						}
						"""
	
	progress_bar_normal = """
					border: 2px solid black;
					border-radius: 5px;
					text-align: center;
					background-color: green;
					color: black;
					height: 24px;
					"""
	
	progress_bar_attention = """
					border: 2px solid yellow;
					border-radius: 5px;
					text-align: center;
					background-color: yellow;
					color: black;
					height: 24px;
					"""
	
	progress_bar_warning = """
					border: 2px solid red;
					border-radius: 5px;
					text-align: center;
					background-color: red;
					color: black;
					height: 24px;
					"""
	
	작지_중요도1 = {
		'fg': 'black',
		'bg': '#FFFF90'
	}
	작지_중요도2 = {
		'fg': 'white',
		'bg': '#000089'
	}
	작지_중요도3 = {
		'fg': 'white',
		'bg': '#004e00'
	}
	작지_중요도4 = {
		'fg': 'white',
		'bg': '#7A7A82'
	}
	작지_중요도5 = {
		'fg': 'black',
		'bg': 'white'
	}
	작지_중요도6 = {
		'fg': 'black',
		'bg': 'white'
	}
	작지_중요도7 = {
		'fg': 'black',
		'bg': 'white'
	}
	작지_중요도8 = {
		'fg': 'black',
		'bg': 'white'
	}

	COLOR_생지_head_noEdit_bg = "#dcf5e2"