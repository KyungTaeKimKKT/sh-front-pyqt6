from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from OpenGL.GL import *
from OpenGL.GLU import *
import ezdxf  # DWG/DXF 파일 처리를 위한 라이브러리

import requests
import tempfile
import os
import subprocess
from math import cos, sin, radians

import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class CADViewer(QOpenGLWidget):
    def __init__(self, parent=None, **kwargs):
        # 😀QOpenGLContext::makeCurrent() called with non-opengl surface 0x6528b2da1840
        # QRhiGles2: Failed to make context current. Expect bad things to happen
        # QOpenGLWidget의 서피스 포맷 설정을 추가
        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(2, 0)  # OpenGL 2.0 사용
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.NoProfile)
        # format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        QSurfaceFormat.setDefaultFormat(format)

        super().__init__(parent)
        self.setFormat(format)  # 위젯에 포맷 적용
        self.url = kwargs.get('url', None)
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_pos = None
        self.cad_data = None
        self.temp_dir = tempfile.gettempdir()
        self.layers = {}  # 레이어 관리를 위한 딕셔너리

        self.background_color = QColor(255, 255, 255)  # 배경색
        self.line_color = QColor(0, 0, 0)  # 선 색상
        self.line_width = 1.0  # 선 두께
        self.selected_entities = set()  # 선택된 엔티티

        self.rotation_angle = 0  # 회전 각도 추가
        self.scale_factor = 1.0  # 스케일 팩터 추가
        self.measuring_mode = False  # 측정 모드 추가
        self.measurement_points = []  # 측정 포인트 저장
            
        self.oda_path = kwargs.get('oda_path', 'C:/Program Files/ODA/ODAFileConverter/ODAFileConverter.exe')  # ODA File Converter 경로

        if self.url:
            self.load_cad_file(self.url)

    def convert_dwg_to_dxf(self, dwg_file):
        """DWG 파일을 DXF로 변환"""
        try:
            # 임시 DXF 파일 경로 생성
            output_path = os.path.join(self.temp_dir, 'converted.dxf')
            input_dir = os.path.dirname(dwg_file)
            
            # ODA File Converter 실행
            cmd = f'"{self.oda_path}" "{input_dir}" "{self.temp_dir}" "ACAD2018" "DXF" "0" "1"'
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            
            # 변환된 파일 확인
            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("변환 실패")
                
        except Exception as e:

            return None

    def load_cad_file(self, url):
        try:
            if url.startswith('http'):
                # URL에서 파일 다운로드
                response = requests.get(url)
                file_ext = os.path.splitext(url)[1].lower()
                temp_file = os.path.join(self.temp_dir, f'temp{file_ext}')
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                url = temp_file

                # DWG 파일인 경우 DXF로 변환
            if url.lower().endswith('.dwg'):
                dxf_file = self.convert_dwg_to_dxf(url)
                if dxf_file:
                    url = dxf_file
                else:
                    raise Exception("DWG 변환 실패")
                
            self.cad_data = ezdxf.readfile(url)
 
            self.initialize_layers()
            # 도면의 경계 상자 계산
            self.calculate_bounds()
            self.reset_view()
        except Exception as e:
            logger.error(f"load_cad_file 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

    def initialize_layers(self):
        if self.cad_data:
            for layer in self.cad_data.layers:
                self.layers[layer.dxf.name] = True  # 모든 레이어 기본적으로 표시

    def reset_view(self):
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # 뷰포트 설정 수정
        if hasattr(self, 'bounds'):
            width_ratio = width / (self.bounds[1][0] - self.bounds[0][0])
            height_ratio = height / (self.bounds[1][1] - self.bounds[0][1])
            self.scale_factor = min(width_ratio, height_ratio) * 0.8  # 여백을 위해 0.8 적용
            
            # 도면의 중심을 화면 중앙에 맞추기 위한 계산
            center_x = (self.bounds[0][0] + self.bounds[1][0]) / 2
            center_y = (self.bounds[0][1] + self.bounds[1][1]) / 2
            self.pan_x = -center_x * self.scale_factor
            self.pan_y = -center_y * self.scale_factor
        
        gluOrtho2D(-width/2, width/2, -height/2, height/2)
        glMatrixMode(GL_MODELVIEW)

    def set_colors(self):
        glColor3f(self.line_color.redF(), 
                 self.line_color.greenF(), 
                 self.line_color.blueF())
        glLineWidth(self.line_width)

    def paintGL(self):
        glClearColor(self.background_color.redF(),
            self.background_color.greenF(),
            self.background_color.blueF(),
            1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glPushMatrix()  # 현재 변환 행렬 저장
        
        # 줌, 패닝, 회전 적용
        glTranslatef(self.pan_x, self.pan_y, 0)
        glScalef(self.zoom_factor * self.scale_factor, 
                self.zoom_factor * self.scale_factor, 1.0)
        glRotatef(self.rotation_angle, 0, 0, 1)
        
        # CAD 데이터 렌더링 (한 번만 수행)
        if self.cad_data:
            self.set_colors()  # 색상 설정 추가
            self.render_cad_data()
            
        # 측정 모드 렌더링
        if self.measuring_mode and self.measurement_points:
            self.render_measurement_points()
        
        glPopMatrix()  # 변환 행렬 복원

    def calculate_bounds(self):
        """도면의 경계 상자를 계산하는 메서드"""
        if not self.cad_data:
            return
        
        modelspace = self.cad_data.modelspace()
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
 
        
        for entity in modelspace:
            if entity.dxftype() == 'LINE':
                points = [entity.dxf.start, entity.dxf.end]
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                r = entity.dxf.radius
                points = [(center[0]-r, center[1]-r), (center[0]+r, center[1]+r)]
            elif entity.dxftype() == 'ARC':
                center = entity.dxf.center
                r = entity.dxf.radius
                points = [(center[0]-r, center[1]-r), (center[0]+r, center[1]+r)]
            elif entity.dxftype() == 'LWPOLYLINE':
                points = [(vertex[0], vertex[1]) for vertex in entity]
            else:
                continue
                
            for point in points:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
        
        self.bounds = ((min_x, min_y), (max_x, max_y))

    def render_cad_data(self):
        if not self.cad_data:
            return

        modelspace = self.cad_data.modelspace()
        
        for entity in modelspace:
            # 레이어가 숨겨져 있으면 건너뛰기
            if not self.layers.get(entity.dxf.layer, True):
                continue

            if entity.dxftype() == 'LINE':
                self.render_line(entity)
            elif entity.dxftype() == 'CIRCLE':
                self.render_circle(entity)
            elif entity.dxftype() == 'ARC':
                self.render_arc(entity)
            elif entity.dxftype() == 'LWPOLYLINE':
                self.render_polyline(entity)

    def render_circle(self, entity):
        glBegin(GL_LINE_LOOP)
        for i in range(32):  # 32개의 선분으로 원 근사
            angle = 2.0 * 3.141592 * i / 32
            x = entity.dxf.center[0] + entity.dxf.radius * cos(angle)
            y = entity.dxf.center[1] + entity.dxf.radius * sin(angle)
            glVertex2f(x, y)
        glEnd()

    def render_line(self, entity):
        glBegin(GL_LINES)
        glVertex2f(entity.dxf.start[0], entity.dxf.start[1])
        glVertex2f(entity.dxf.end[0], entity.dxf.end[1])
        glEnd()

    def render_arc(self, entity):
        start_angle = radians(entity.dxf.start_angle)
        end_angle = radians(entity.dxf.end_angle)
        
        glBegin(GL_LINE_STRIP)
        for i in range(32):  # 32개의 선분으로 호 근사
            angle = start_angle + (end_angle - start_angle) * i / 31
            x = entity.dxf.center[0] + entity.dxf.radius * cos(angle)
            y = entity.dxf.center[1] + entity.dxf.radius * sin(angle)
            glVertex2f(x, y)
        glEnd()

    def render_polyline(self, entity):
        glBegin(GL_LINE_STRIP)
        for vertex in entity:
            glVertex2f(vertex[0], vertex[1])
        if entity.closed:
            first_vertex = entity[0]
            glVertex2f(first_vertex[0], first_vertex[1])
        glEnd()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # 뷰 리셋 액션
        reset_action = menu.addAction("뷰 리셋")
        reset_action.triggered.connect(self.reset_view)
        
        # 레이어 서브메뉴
        layer_menu = menu.addMenu("레이어")
        for layer_name, visible in self.layers.items():
            action = layer_menu.addAction(layer_name)
            action.setCheckable(True)
            action.setChecked(visible)
            action.triggered.connect(lambda checked, ln=layer_name: self.toggle_layer(ln))
        
        # 색상 설정 메뉴
        color_menu = menu.addMenu("색상 설정")
        bg_color_action = color_menu.addAction("배경색 변경")
        line_color_action = color_menu.addAction("선 색상 변경")
        bg_color_action.triggered.connect(self.change_background_color)
        line_color_action.triggered.connect(self.change_line_color)
        
        # 선 두께 메뉴
        line_width_menu = menu.addMenu("선 두께")
        for width in [0.5, 1.0, 2.0, 3.0]:
            action = line_width_menu.addAction(f"{width}px")
            action.triggered.connect(lambda checked, w=width: self.set_line_width(w))

            # 새로운 메뉴 항목 추가
        menu.addSeparator()
        fit_action = menu.addAction("화면에 맞추기")
        fit_action.triggered.connect(self.fit_to_view)
        
        rotate_menu = menu.addMenu("회전")
        for angle in [90, 180, 270]:
            action = rotate_menu.addAction(f"{angle}°")
            action.triggered.connect(lambda checked, a=angle: self.rotate_view(a))
        
        measure_action = menu.addAction("거리 측정")
        measure_action.setCheckable(True)
        measure_action.triggered.connect(lambda checked: setattr(self, 'measuring_mode', checked))
        
        menu.exec(event.globalPos())

    def fit_to_view(self):
        """도면을 뷰에 맞게 자동 스케일링"""
        if not hasattr(self, 'bounds') or not self.bounds:
            return
            
        width = self.bounds[1][0] - self.bounds[0][0]
        height = self.bounds[1][1] - self.bounds[0][1]
        
        # 뷰포트 크기에 맞게 스케일 계산
        scale_x = (self.width() - 20) / width
        scale_y = (self.height() - 20) / height
        self.scale_factor = min(scale_x, scale_y)
        
        # 중심점 계산
        center_x = (self.bounds[0][0] + self.bounds[1][0]) / 2
        center_y = (self.bounds[0][1] + self.bounds[1][1]) / 2
        
        self.pan_x = -center_x * self.scale_factor
        self.pan_y = -center_y * self.scale_factor
        self.update()

    def rotate_view(self, angle):
        """도면 회전"""
        self.rotation_angle += angle
        self.update()

    def measure_distance(self):
        """두 점 사이 거리 측정"""
        if len(self.measurement_points) == 2:
            p1, p2 = self.measurement_points
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            distance = ((dx ** 2) + (dy ** 2)) ** 0.5
            QMessageBox.information(self, "측정 결과", f"거리: {distance:.2f}")
            self.measurement_points.clear()
            self.measuring_mode = False
        self.update()

    def mousePressEvent(self, event):
        if self.measuring_mode and event.buttons() & Qt.MouseButton.LeftButton:
            # 측정 모드에서 점 추가
            pos = self.screen_to_world(event.pos())
            self.measurement_points.append(pos)
            if len(self.measurement_points) == 2:
                self.measure_distance()
        else:
            self.last_pos = event.pos()

    def change_background_color(self):
        color = QColorDialog.getColor(self.background_color, self)
        if color.isValid():
            self.background_color = color
            self.update()

    def change_line_color(self):
        color = QColorDialog.getColor(self.line_color, self)
        if color.isValid():
            self.line_color = color
            self.update()

    def set_line_width(self, width):
        self.line_width = width
        self.update()

    def save_image(self, filename):
        """현재 뷰를 이미지로 저장"""
        self.grabFramebuffer().save(filename)


    def toggle_layer(self, layer_name):
        self.layers[layer_name] = not self.layers[layer_name]
        self.update()

    def wheelEvent(self, event):
        # 마우스 휠로 줌 인/아웃
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9
        self.update()

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        # 마우스 드래그로 패닝
        if event.buttons() & Qt.MouseButton.LeftButton:
            dx = event.pos().x() - self.last_pos.x()
            dy = event.pos().y() - self.last_pos.y()
            self.pan_x += dx
            self.pan_y -= dy
            self.last_pos = event.pos()
            self.update()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    player =CADViewer (url='http://192.168.7.108:9999/media/%EC%98%81%EC%97%85-%EB%94%94%EC%9E%90%EC%9D%B8%EA%B4%80%EB%A6%AC/%EC%98%81%EC%97%85image/%EC%9D%98%EB%A2%B0%ED%8C%8C%EC%9D%BC/2025-1-10/b0496731-7bc2-4e2f-b801-0d9deeb2e445/3.dxf')

    player.resize(800, 600)
    player.show()
    sys.exit(app.exec())