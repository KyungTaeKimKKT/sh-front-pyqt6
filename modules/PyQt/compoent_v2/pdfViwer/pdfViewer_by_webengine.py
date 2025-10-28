from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import os

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class PDFViewer_by_Webengine(QWidget):
	def __init__(self, **kwargs):
		super().__init__()
		self.layout = QVBoxLayout()
		self.viewer = QWebEngineView()

		# PDF 뷰어 설정 추가
		self.viewer.settings().setAttribute(
			self.viewer.settings().WebAttribute.PluginsEnabled, True
		)
		self.viewer.settings().setAttribute(
			self.viewer.settings().WebAttribute.PdfViewerEnabled, True
		)
		
		
		# PDF 뷰어 초기화
		self.layout.addWidget(self.viewer)
		self.setLayout(self.layout)

		# HTML 템플릿 설정
		self.pdf_template = """
			<!DOCTYPE html>
			<html>
			<head>
				<title>PDF Viewer</title>
				<style>
					body, html {{ margin: 0; padding: 0; height: 100%; }}
					#pdf-viewer {{ width: 100%; height: 100%; }}
				</style>
			</head>
			<body>
				<embed id="pdf-viewer" type="application/pdf" src="{}" width="100%" height="100%">
			</body>
			</html>
		"""
		
		# URL 또는 파일 경로로 PDF 로드
		if 'url' in kwargs:
			self.load_from_url(kwargs['url'])
		elif 'file' in kwargs:
			self.load_from_file(kwargs['file'])
	
	def load_from_url(self, url):
		try:		
			self.viewer.setUrl(QUrl(url))

		except Exception as e:
			logger.error(f"load_from_url 오류: {e}")
			logger.error(f"{traceback.format_exc()}")

	
	def load_from_file(self, file_path):
		"""로컬 파일에서 PDF 로드"""
		if os.path.exists(file_path):
			try:
				self.viewer.setUrl(QUrl.fromLocalFile(file_path))
			except Exception as e:
				logger.error(f"load_from_file 오류: {e}")
				logger.error(f"{traceback.format_exc()}")
