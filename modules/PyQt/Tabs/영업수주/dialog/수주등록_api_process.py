from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import TypeAlias

import pandas as pd
import urllib
from datetime import date, datetime, timedelta
import copy

import pathlib
import openpyxl
import typing

import concurrent.futures
import asyncio
import time
import base64
import os

### 😀😀 user : ui...
from modules.PyQt.Tabs.영업수주.ui.Ui_tab_영업수주_관리 import Ui_Tab_App as Ui_Tab
###################
from modules.PyQt.compoent_v2.dialog_조회조건.dialog_조회조건 import Dialog_Base_조회조건
from modules.PyQt.compoent_v2.pdfViwer.dlg_pdfViewer import Dlg_Pdf_Viewer_by_webengine
from modules.PyQt.User.validator import YearMonth_Validator
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
from modules.user.utils_qwidget import Utils_QWidget
from modules.PyQt.User.toast import User_Toast
from config import Config as APP
from modules.user.async_api import Async_API_SH
from info import Info_SW as INFO
import modules.user.utils as Utils


from modules.PyQt.QRunnable.work_async import Worker, Worker_Post
from modules.PyQt.Qthreads.WS_Thread_Sync import WS_Thread_Sync
from icecream import ic
import traceback
from modules.logging_config import get_plugin_logger

ic.configureOutput(prefix= lambda: f"{datetime.now()} | ", includeContext=True )
if hasattr( INFO, 'IC_ENABLE' ) and INFO.IC_ENABLE :
	ic.enable()
else :
	ic.disable()



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class 영업수주_등록_ApiProcess_Message(QDialog):
	def __init__(self, parent, msg:dict={},**kwargs):
		super().__init__(parent)
		# 파일 저장 경로
		self.save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
		# os.makedirs(self.save_dir, exist_ok=True)
		
		# 파일 정보 저장
		self.file_data = None
		self.validation_failed = False
		self.validation_completed = False  # 검증 완료 여부 추가

		self.msg = msg
		self.setWindowTitle('수주등록_ApiProcess')
		self.start_time = datetime.now()
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_elapsed_time)
		self.timer.start(1000)  # 1초마다 업데이트

		# 진행 상태 추적
		self.subjects = ["일정", "금액", "검증"]
		self.sub_subjects = {
			"일정": ["Excel reading", "Data 처리", "DB 저장"],
			"금액": ["Excel reading", "Data 처리", "DB 저장"],
			"검증": ["검증결과"]
		}
		self.current_subject = None
		self.current_sub_subject = None
		self.completed_steps = set()

		self.UI()
		if msg :
			self.update_message(msg)
		
		# 웹소켓 연결 설정
		self.ws_manager = WS_Thread_Sync(self, url=INFO.WS_영업수주_등록_ApiProcess)
		self.ws_manager.signal_receive_message.connect(self.update_message)
		self.ws_manager.start()

	def closeEvent(self, event):
		"""위젯이 닫힐 때 호출되는 이벤트 핸들러"""
		# 웹소켓 연결 종료
		if hasattr(self, 'ws_manager') and self.ws_manager:
			self.ws_manager.close()
		super().closeEvent(event)

	def UI(self):
		layout = QVBoxLayout()
		
		# 제목 라벨
		self.lbl_subject = QLabel("처리 중...")
		self.lbl_subject.setStyleSheet("font-size: 16px; font-weight: bold;")
		layout.addWidget(self.lbl_subject)
		
		# 메시지 라벨
		self.lbl_message = QLabel("")
		self.lbl_message.setWordWrap(True)
		layout.addWidget(self.lbl_message)
		# 파일 다운로드 버튼 (처음에는 숨김)
		self.btn_download = QPushButton("파일 다운로드")
		self.btn_download.clicked.connect(self.save_file_dialog)
		self.btn_download.setVisible(False)
		layout.addWidget(self.btn_download)
		
		# 진행 상태 표시 프레임
		status_frame = QFrame()
		status_layout = QGridLayout(status_frame)
		
		# 각 subject와 sub_subject에 대한 상태 표시 라벨 생성
		self.status_labels = {}
		
		for i, subject in enumerate(self.subjects):
			# Subject 라벨
			subject_label = QLabel(subject)
			subject_label.setStyleSheet("font-weight: bold; padding: 5px;")
			status_layout.addWidget(subject_label, i, 0)
			
			# 해당 subject의 sub_subjects에 대한 라벨
			for j, sub_subject in enumerate(self.sub_subjects[subject]):
				label = QLabel(sub_subject)
				label.setStyleSheet("background-color: white; padding: 5px; border: 1px solid #ccc;")
				status_layout.addWidget(label, i, j+1)
				self.status_labels[(subject, sub_subject)] = label
		
		layout.addWidget(status_frame)
		
		# 시간 정보 프레임
		time_frame = QFrame()
		time_layout = QHBoxLayout(time_frame)
		
		# 시작 시간
		self.lbl_start_time = QLabel("시작: ")
		time_layout.addWidget(self.lbl_start_time)
		
		# 경과 시간
		self.lbl_elapsed_time = QLabel("경과: 00:00:00")
		time_layout.addWidget(self.lbl_elapsed_time)
		
		layout.addWidget(time_frame)
		
		# 진행 상태 바
		self.progress_bar = QProgressBar()
		self.progress_bar.setRange(0, 100)
		self.progress_bar.setValue(0)
		layout.addWidget(self.progress_bar)
		
		# 닫기 버튼
		self.btn_close = QPushButton("닫기")
		self.btn_close.clicked.connect(self.close)
		layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignRight)
		
		self.setLayout(layout)
		self.resize(600, 300)
	
	def update_message(self, msg:dict):
		"""메시지 업데이트"""

		try:
			subject = msg.get('subject', '')
			sub_subject = msg.get('sub_subject', '')
			sub_type = msg.get('sub_type', '')
			progress = msg.get('progress', 0)
			message = msg.get('message', '')
			send_time = msg.get('send_time', '')
			if progress == 100:
				self.validation_completed = True  # 검증 완료 표시
				if 'file' in msg :
					self.file_data = {
						'filename': msg['file']['filename'],
						'content_type': msg['file']['content_type'],
						'content': msg['file']['content']
					}

					# 다운로드 버튼 표시
					self.btn_download.setVisible(True)
					self.btn_download.setText(f"파일 다운로드: {self.file_data['filename']}")
					self.btn_download.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold; padding: 5px;")
					message += f"\n파일이 준비되었읍니다. 다운로드 버튼을 클릭하여 저장하세요."

					# 검증 실패 표시
					self.validation_failed = True
				else:
					self.validation_failed = False

			# 현재 진행 중인 단계 업데이트
			self.current_subject = subject
			self.current_sub_subject = sub_subject
			
			# 이전 단계 완료 처리 로직 추가
			if subject and sub_subject:
				# 현재 단계의 인덱스 찾기
				if subject in self.subjects:
					subject_idx = self.subjects.index(subject)
					if sub_subject in self.sub_subjects[subject]:
						sub_subject_idx = self.sub_subjects[subject].index(sub_subject)
						
						# 이전 단계들을 모두 완료로 표시
						for s_idx, s in enumerate(self.subjects):
							for ss_idx, ss in enumerate(self.sub_subjects[s]):
								# 이전 subject의 모든 sub_subject는 완료
								if s_idx < subject_idx:
									self.completed_steps.add((s, ss))
								# 현재 subject의 이전 sub_subject는 완료
								elif s_idx == subject_idx and ss_idx < sub_subject_idx:
									self.completed_steps.add((s, ss))
			# 현재 진행 중인 단계 업데이트
			self.current_subject = subject
			self.current_sub_subject = sub_subject
			
			# 진행률이 100%인 경우 현재 단계 완료 처리
			if progress == 100:
				self.completed_steps.add((subject, sub_subject))
				
			# 상태 라벨 업데이트
			self.update_status_labels()
		except Exception as e:
			ic(e)
			return
		
		self.lbl_subject.setText(f"{subject} - {sub_subject}")
		self.lbl_message.setText(message)
		self.progress_bar.setValue(int(progress))
		try:
			send_time_obj = datetime.fromisoformat(send_time)
			self.lbl_start_time.setText(f"시작: {send_time_obj.strftime('%H:%M:%S')}")
		except:
			pass

	def update_status_labels(self):
		"""상태 라벨 색상 업데이트"""
		for (subject, sub_subject), label in self.status_labels.items():
			if subject == "검증" and sub_subject == "검증결과":
				if self.validation_completed:  # 검증이 완료된 경우에만 결과 표시
					if self.validation_failed:
						# 검증 실패 시 빨간색 배경, 흰색 글자
						label.setText("Fail")
						label.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold; padding: 5px; border: 1px solid #ccc;")
					else:
						# 검증 성공 시 녹색 배경
						label.setText("Ok")
						label.setStyleSheet("background-color: #a3e4a3; padding: 5px; border: 1px solid #ccc;")
				else:
					# 검증이 아직 완료되지 않은 경우 기본 스타일
					label.setText("")
					label.setStyleSheet("background-color: white; padding: 5px; border: 1px solid #ccc;")
				continue

			if (subject, sub_subject) in self.completed_steps:
				# 완료된 단계는 녹색
				label.setStyleSheet("background-color: #a3e4a3; padding: 5px; border: 1px solid #ccc;")
			elif subject == self.current_subject and sub_subject == self.current_sub_subject:
				# 현재 진행 중인 단계는 노란색
				label.setStyleSheet("background-color: #ffff99; padding: 5px; border: 1px solid #ccc;")
			else:
				# 미진행 단계는 흰색
				label.setStyleSheet("background-color: white; padding: 5px; border: 1px solid #ccc;")
	
	def update_elapsed_time(self):
		"""경과 시간 업데이트"""
		elapsed = datetime.now() - self.start_time
		hours, remainder = divmod(elapsed.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		self.lbl_elapsed_time.setText(f"경과: {hours:02}:{minutes:02}:{seconds:02}")

	def save_file_dialog(self):
		"""파일 저장 다이얼로그 표시"""
		if not self.file_data:
			return
			
		filename = self.file_data['filename']
		default_path = os.path.join(self.save_dir, filename)
		
		file_path, _ = QFileDialog.getSaveFileName(
			self,
			"파일 저장",
			default_path,
			f"모든 파일 (*.*)"
		)
		
		if file_path:
			try:
				decoded_content = base64.b64decode(self.file_data['content'])
				with open(file_path, 'wb') as f:
					f.write(decoded_content)
				
				QMessageBox.information(self, "저장 완료", f"파일이 성공적으로 저장되었읍니다:\n{file_path}")
			except Exception as e:
				QMessageBox.critical(self, "저장 오류", f"파일 저장 중 오류가 발생했읍니다:\n{str(e)}")