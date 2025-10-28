# 코덱 오류 해결을 위해서는 시스템에 필요한 코덱을 설치해야 합니다:
# Windows: K-Lite Codec Pack 설치, vlc 미디어 플레이어 최신 버젼 설치
# Linux: sudo apt-get install ubuntu-restricted-extras
# macOS: VLC 미디어 플레이어 설치

# VLC 대신 다른 대안 고려:
# MPV: 더 가볍고 안정적
# GStreamer: 크로스플랫폼 지원이 우수

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
import os
from urllib.parse import unquote
import vlc
from pathlib import Path
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class MoviePlayer(QWidget):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.auto_play = kwargs.get('auto_play', True)  # 기본값은 True
        self.safe_end_time = 3000   ### 안전한 종료를 위해 3초 전에 속도를 정상화 하는 시간

        # VLC 인스턴스 생성 시 추가 옵션 설정
        vlc_args = [
            '--no-xlib',  # Linux에서 X11 관련 문제 해결
            '--avcodec-hw=none',  # 하드웨어 가속 비활성화
            '--quiet',  # 불필요한 로그 출력 제거
            '--no-video-deco',  # 비디오 데코레이션 비활성화
            '--no-embedded-video'  # 임베디드 비디오 비활성화
        ]
        # VLC 인스턴스 및 플레이어 생성
        try:
            self.instance = vlc.Instance(' '.join(vlc_args))
        except Exception as e:
            raise RuntimeError("VLC가 올바르게 설치되지 않았읍니다.") from e
        self.player = self.instance.media_player_new()
        
        # 상태 변수
        self._repeat = False
        self._playlist = []
        self._current_index = 0
        
        # 미디어 소스 설정
        self.media_source = kwargs.get('url') or kwargs.get('file')
        if not self.media_source:
            raise ValueError("URL 또는 파일 경로가 필요합니다.")
            
        self.init_ui()
        self.setup_player()
        self.connect_signals()

            # 초기 미디어 소스를 재생목록에 추가
        self.add_to_playlist(self.media_source) 

        # auto_play 옵션에 따라 재생 여부 결정
        if not self.auto_play:
            self.player.stop()
            self.play_button.setText("재생")
            self.play_button.setProperty("playing", "false")
        
    def init_ui(self):
        # 메인 레이아웃을 QHBoxLayout으로 변경
        main_layout = QHBoxLayout(self) 
        main_layout.setSpacing(10)  # 레이아웃 간격 설정

        # 왼쪽 패널 (비디오 + 컨트롤)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(5)

        # 비디오 출력을 위한 프레임
        self.video_frame = QFrame()
        self.video_frame.setMinimumSize(400, 300)  # 최소 크기 설정
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_frame.setStyleSheet("background-color: black; border: 1px solid #666;")

        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        left_panel.addWidget(self.video_frame)
        
        # 현재 재생 중인 파일명 표시
        self.current_file_label = QLabel()
        self.current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_file_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_panel.addWidget(self.current_file_label)

        # 컨트롤 레이아웃 수정
        controls_layout = QVBoxLayout()  # 수직 레이아웃으로 변경
        
        # 재생 시간과 위치 슬라이더를 포함하는 상단 레이아웃
        position_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimumWidth(300)  # 위치 슬라이더 크기 증가
        position_layout.addWidget(self.time_label)
        position_layout.addWidget(self.position_slider, stretch=1)

        # 버튼과 볼륨 컨트롤을 포함하는 하단 레이아웃
        buttons_layout = QHBoxLayout()

        # 볼륨 컨트롤을 작게 만들기
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(2)  # 간격을 줄임
        volume_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        
        volume_container = QWidget()  # 새로운 컨테이너 위젯
        volume_container.setLayout(volume_layout)
        volume_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        volume_label = QLabel("🔊")
        volume_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setFixedWidth(100)  # 고정 너비 설정
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
      
        # 기본 컨트롤
        self.play_button = QPushButton("재생")
        self.stop_button = QPushButton("정지")
        
        # 추가 컨트롤
        self.fullscreen_button = QPushButton("전체화면")
        self.mute_button = QPushButton("음소거")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(['0.5x', '1.0x', '1.5x', '2.0x'])
        self.repeat_button = QPushButton("반복")
        self.prev_button = QPushButton("이전")
        self.next_button = QPushButton("다음")
        
        # 버튼들을 하단 레이아웃에 추가
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.prev_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addWidget(volume_container)  # volume_layout 대신 container 추가
        buttons_layout.addWidget(self.fullscreen_button)
        buttons_layout.addWidget(self.mute_button)
        buttons_layout.addWidget(self.speed_combo)
        buttons_layout.addWidget(self.repeat_button)

        # 모든 컨트롤을 메인 컨트롤 레이아웃에 추가
        controls_layout.addLayout(position_layout)
        controls_layout.addLayout(buttons_layout)

        # 컨트롤 레이아웃을 left_panel에 추가
        left_panel.addLayout(controls_layout)  # 이 줄이 누락되어 있었읍니다
        
        # 오른쪽 패널 (재생목록)
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)  # 여백 제거

        playlist_label = QLabel("재생목록")
        playlist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        playlist_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f0f0f0;")
        right_panel.addWidget(playlist_label)
        
        self.playlist_widget = QListWidget()
        self.playlist_widget.setFixedWidth(300)  # 너비 증가
        self.playlist_widget.setMinimumHeight(200)  # 최소 높이 증가
        self.playlist_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.playlist_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self.playlist_widget.setAlternatingRowColors(True)  # 행 색상 교차
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)

        # 재생 버튼 스타일 설정
        self.play_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton[playing="true"] {
                background-color: #0078d7;
                color: white;
            }
            QPushButton[playing="false"] {
                background-color: white;
                color: black;
            }
        """)

        right_panel.addWidget(self.playlist_widget)
        # 메인 레이아웃에 패널 추가
        main_layout.addLayout(left_panel, stretch=7)
        main_layout.addLayout(right_panel, stretch=3)
        
    def setup_player(self):
        # VLC 플레이어 설정
        try:
            if sys.platform.startswith('linux'):
                # Linux: X11/XCB 처리 개선
                wid = self.video_frame.winId().__int__()
                if wid is not None:
                    self.player.set_xwindow(wid)
            elif sys.platform == "win32":
                # Windows: HWND 처리
                self.player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":
                # macOS: NSView 처리
                self.player.set_nsobject(int(self.video_frame.winId()))
        except Exception as e:
            logger.error(f"setup_player 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            
        # 초기 볼륨 설정
        self.player.audio_set_volume(50)
        self.volume_slider.setValue(50)
        
        # 미디어 로드
        media = self.instance.media_new(self.media_source)
        self.player.set_media(media)
        
    def play_media(self, source):
        try:
            media = self.instance.media_new(source)
            self.player.set_media(media)
            self.player.play()
            
            self.start_update_timer()  # 재생 시작 시 타이머 시작

            # 디버깅을 위한 로그

            decoded_filename = unquote(source)

            
            display_name = os.path.basename(decoded_filename)
            self.current_file_label.setText(display_name)
            self.current_file_label.setToolTip(decoded_filename)
            
            # 재생목록 강조 표시
            for i in range(self.playlist_widget.count()):
                item = self.playlist_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == source:
                    self._current_index = i  # 현재 인덱스 업데이트
                    item.setBackground(QColor("#e0e0e0"))
                else:
                    item.setBackground(QColor("white"))
        except Exception as e:
            logger.error(f"play_media 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    @pyqtSlot()
    def start_update_timer(self):
        """GUI 스레드에서 타이머를 시작하는 메서드"""

        if not self.update_timer.isActive():
            self.update_timer.start()

    @pyqtSlot()
    def stop_update_timer(self):
        """GUI 스레드에서 타이머를 중지하는 메서드"""
        if self.update_timer.isActive():
            self.update_timer.stop()

    def add_to_playlist(self, source):
        try:
            if source not in self._playlist:  # 중복 추가 방지
                self._playlist.append(source)
                decoded_filename = unquote(source)  # URL 디코딩
                filename = os.path.basename(decoded_filename)  # 파일명 추출
                
                item = QListWidgetItem(filename)
                item.setData(Qt.ItemDataRole.UserRole, source)
                self.playlist_widget.addItem(item)
                
                # 첫 번째 항목이 추가되면 자동 재생
                if len(self._playlist) == 1:
                    self.play_media(source)
  # 디버깅용 로그
        except Exception as e:
            logger.error(f"add_to_playlist 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    def connect_signals(self):
        # 버튼 시그널
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        self.prev_button.clicked.connect(self.play_previous)
        self.next_button.clicked.connect(self.play_next)

        # 재생 속도 콤보박스 시그널 연결
        self.speed_combo.setCurrentText('1.0x')  # 초기값 설정
        self.speed_combo.currentTextChanged.connect(self.change_playback_speed)
        
        # 슬라이더 시그널
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        # 클릭 이벤트 추가
        self.position_slider.mouseReleaseEvent = self.on_slider_clicked

        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # 기존 시그널 연결에 미디어 종료 이벤트 추가
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_media_end)

        # 타이머 설정 (위치 업데이트용)
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_interface)
        # self.update_timer.start()
        
    def play_pause(self):

        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("재생")
            self.play_button.setProperty("playing", "false")
            self.stop_update_timer()  # 타이머 중지 추가
        else:
            # 미디어가 종료된 상태에서 재생 시 처리
            if hasattr(self, '_media_ended') and self._media_ended:
                current_media = self._playlist[self._current_index]
                media = self.instance.media_new(current_media)
                self.player.set_media(media)
                self._media_ended = False
        
            self.player.play()
            self.play_button.setText("일시정지")
            self.play_button.setProperty("playing", "true")
            self.start_update_timer()  # 타이머 시작 추가

        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.play_button.update()  # 강제 업데이트 추가

    def stop(self):
        self.player.stop()
        self.play_button.setText("재생")
        # GUI 스레드에서 타이머 중지
        self.start_update_timer()  # 재생 시작 시 타이머 시작
        # QMetaObject.invokeMethod(self, "stop_update_timer", Qt.ConnectionType.QueuedConnection)
        
    def on_slider_pressed(self):
        self.update_timer.stop()  # 타이머 일시 중지

    def on_slider_released(self):
        self.set_position(self.position_slider.value())
        self.update_timer.start()  # 타이머 재시작
    
    def on_slider_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 클릭한 위치의 값을 계산
            value = QStyle.sliderValueFromPosition(
                self.position_slider.minimum(),
                self.position_slider.maximum(),
                event.pos().x(),
                self.position_slider.width()
            )
            self.position_slider.setValue(value)
            self.set_position(value)
        # 기본 이벤트 처리
        super(type(self.position_slider), self.position_slider).mouseReleaseEvent(event)

    def set_position(self, position):
        length = self.player.get_length()
        if length > 0:
            target_time = int((position / 100.0) * length)

            self.player.set_time(target_time)
            

        
    def set_volume(self, volume):
        self.player.audio_set_volume(volume)
        # 볼륨이 0이 아닐 때는 음소거 해제
        if volume > 0:
            self.player.audio_set_mute(False)
            self.mute_button.setText("음소거")
        else:
            self.player.audio_set_mute(True)
            self.mute_button.setText("음소거 해제")
        
    def update_interface(self):
        # 재생 상태에 따른 버튼 업데이트
        is_playing = self.player.is_playing()
        self.play_button.setText("일시정지" if is_playing else "재생")
        self.play_button.setProperty("playing", "true" if is_playing else "false")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.play_button.update()  # 강제 업데이트 추가

        if not self.player.is_playing():
            # 재생이 멈췄을 때 초기화
            self.time_label.setText("00:00 / 00:00")
            self.position_slider.setValue(0)
            self.stop_update_timer()  # 타이머 중지 추가
            return
            
        # 시간 업데이트 로직 개선
        try:
            length = self.player.get_length()
            time = self.player.get_time()
            
            if length > 0 and time >= 0:  # 유효한 시간값 확인
                # 재생 종료 직전에 속도 정상화
                if length - time <= self.safe_end_time:  # 마지막 ??초
                    self.player.set_rate(1.0)
                    self.speed_combo.setCurrentText('1.0x')
                
                # 재생 종료 체크 개선
                if time >= length - 200:  # 종료 0.1초 전
                    self.player.stop()
                    self.play_button.setText("재생")
                    self.play_button.setProperty("playing", "false")
                    self.time_label.setText("00:00 / 00:00")
                    self.position_slider.setValue(0)
                    self.stop_button.setStyleSheet("background-color: #0078d7; color: white;")
                    self.stop_update_timer()  # 타이머 중지 추가
                    return
            
                position = min((time / length) * 100, 100)  # 최대값 제한

                self.position_slider.blockSignals(True)
                self.position_slider.setValue(int(position))
                self.position_slider.blockSignals(False)
                    
                # 재생 종료 직전 처리
                if length - time <= 1000:  # 마지막 1초 이내
                    self.player.set_rate(1.0)  # 재생 속도 정상화

            # 시간 표시 업데이트
            def format_time(ms):
                s = ms // 1000
                m = s // 60
                s = s % 60
                return f"{m:02d}:{s:02d}"
                
            self.time_label.setText(f"{format_time(time)} / {format_time(length)}")
        except Exception as e:      
            logger.error(f"update_interface 오류: {e}")
            logger.error(f"{traceback.format_exc()}")

        
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("전체화면")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("이전화면")
            
    def toggle_mute(self):
        is_muted = self.player.audio_get_mute()
        self.player.audio_set_mute(not is_muted)
        self.mute_button.setText("음소거 해제" if not is_muted else "음소거")

        # 음소거 상태에 따라 버튼 텍스트와 볼륨 슬라이더 상태 업데이트
        if not is_muted:  # 음소거로 변경될 때
            self.mute_button.setText("음소거 해제")
            self.volume_slider_previous = self.volume_slider.value()  # 현재 볼륨 저장
            self.volume_slider.setValue(0)
        else:  # 음소거 해제될 때
            self.mute_button.setText("음소거")
            if hasattr(self, 'volume_slider_previous'):
                self.volume_slider.setValue(self.volume_slider_previous)
            else:
                self.volume_slider.setValue(50)  # 기본값으로 설정
        
    def toggle_repeat(self):
        self._repeat = not self._repeat
        self.repeat_button.setText("반복 끄기" if self._repeat else "반복")
        
    def play_previous(self):
        if len(self._playlist) > 0:
            self._current_index = (self._current_index - 1) % len(self._playlist)
            self.play_media(self._playlist[self._current_index])
            
    def play_next(self):
        if len(self._playlist) > 0:
            self._current_index = (self._current_index + 1) % len(self._playlist)
            self.play_media(self._playlist[self._current_index])

    def change_playback_speed(self, speed_text):
        try:
            speed = float(speed_text.replace('x', ''))
            # 재생 시간이 끝나갈 때는 속도 변경하지 않음
            length = self.player.get_length()
            time = self.player.get_time()
            if length - time <= self.safe_end_time  :  # 끝나기 ??초 전
                self.speed_combo.setCurrentText('1.0x')
                self.player.set_rate(1.0)  # 속도를 기본값으로 리셋
                return
                
            self.player.set_rate(speed)
        except Exception as e:

            self.speed_combo.setCurrentText('1.0x')

    def on_media_end(self, event):

        try:    
            # 반복 재생 상태 확인을 위해 현재 상태 저장
            self._media_ended = True
            # GUI 스레드에서 안전하게 타이머 처리
            QMetaObject.invokeMethod(self, "handle_media_end", 
                                Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            logger.error(f"on_media_end 오류: {e}")
            logger.error(f"{traceback.format_exc()}")


    @pyqtSlot()
    def handle_media_end(self):
        """GUI 스레드에서 실행될 미디어 종료 처리 메서드"""

        self.stop_update_timer()

        if self._repeat:
            # 반복 재생 시 새로운 미디어 객체 생성
            current_media = self._playlist[self._current_index]
            media = self.instance.media_new(current_media)
            self.player.set_media(media)
            self.player.play()
            self.play_button.setText("일시정지")
            self.play_button.setProperty("playing", "true")
            self.start_update_timer()
        elif len(self._playlist) > 1:
            # 재생목록의 다음 항목 재생
            self._current_index = (self._current_index + 1) % len(self._playlist)
            QTimer.singleShot(100, lambda: self.play_media(self._playlist[self._current_index]))
        else:

            self.player.stop()
            self.play_button.setText("재생")
            self.time_label.setText("00:00 / 00:00")
            self.position_slider.setValue(0)
            self.play_button.setProperty("playing", "false")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    player = MoviePlayer(url='http://192.168.7.108:9999/media/%EC%98%81%EC%97%85-%EB%94%94%EC%9E%90%EC%9D%B8%EA%B4%80%EB%A6%AC/%EC%98%81%EC%97%85image/%EC%9D%98%EB%A2%B0%ED%8C%8C%EC%9D%BC/2025-1-10/c8277c1a-d0e6-4e83-9539-6d597121321d/%EC%83%81%EC%B2%98%EB%A5%BC_%EA%BF%B0%EB%A7%A4%EC%A7%80_%EC%95%8A%EB%8A%94_%ED%8F%B4%EB%8D%94%EB%B8%94_%EB%B4%89%ED%95%A9%ED%82%A4%ED%8A%B8_5cm_%EC%82%AC%EC%9A%A9%EB%B0%A9%EB%B2%95.mp4')

    player.resize(800, 600)
    player.show()
    sys.exit(app.exec())

    