import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QSlider, QLabel, QHBoxLayout, QLineEdit
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl
import requests
import os
os.environ["QT_QUICK_BACKEND"] = "software"

class MoviePlayer(QWidget):
    def __init__(self, parent=None, url: str = None):
        super().__init__(parent)
        self.setWindowTitle("PyQt6 Movie Player")
        self.setMinimumSize(800, 600)
        self.is_fullscreen = False

        # Core components
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.init_UI()

        # Connect signals
        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.update_duration)
        self.player.playbackStateChanged.connect(self.update_button)

        if url:
            self.url_input.setText(url)
            self.load_video(url)

    def init_UI(self):
        main_layout = QVBoxLayout(self)

        # --- Video Widget ---
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.video_widget.mouseDoubleClickEvent = self.toggle_fullscreen_event
        self.player.setVideoOutput(self.video_widget)
        main_layout.addWidget(self.video_widget)

        # --- URL input + Load Button ---
        file_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("동영상 URL 또는 파일 경로 입력...")
        file_layout.addWidget(self.url_input)

        self.btn_load = QPushButton("열기")
        self.btn_load.clicked.connect(self.on_load_clicked)
        file_layout.addWidget(self.btn_load)
        main_layout.addLayout(file_layout)

        # --- Control Buttons (Play, Fullscreen) ---
        control_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶ 재생")
        self.btn_play_pause.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.btn_play_pause)

        self.btn_fullscreen = QPushButton("⛶ 전체화면")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_button)
        control_layout.addWidget(self.btn_fullscreen)

        main_layout.addLayout(control_layout)

        # --- Position Slider ---
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        main_layout.addWidget(self.slider)

        # --- Speed Control (Compact Layout) ---
        speed_layout = QHBoxLayout()
        speed_layout.addStretch()

        self.speed_label = QLabel("속도: 1.00x")
        speed_layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self.update_speed)
        speed_layout.addWidget(self.speed_slider)

        speed_layout.addStretch()
        main_layout.addLayout(speed_layout)

        # --- Status Label ---
        self.label = QLabel("대기 중")
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main_layout.addWidget(self.label)

    def on_load_clicked(self):
        self.load_video(self.url_input.text().strip())

    def load_video(self, input_path:str):
        if not input_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "비디오 파일 열기", "", "Videos (*.mp4 *.avi *.mkv *.mov)")
            if not file_path:
                return
            input_path = file_path

        url = QUrl.fromUserInput(input_path)
        if not url.isValid():
            self.label.setText("잘못된 경로 또는 URL입니다.")
            return
        
        if url.isLocalFile():
            # ✅ 로컬 파일 존재 여부 확인
            local_path = url.toLocalFile()
            if not os.path.exists(local_path):
                self.label.setText("로컬 파일이 존재하지 않읍니다.")
                return
        else:
            # ✅ 네트워크 URL 유효성 확인 (HEAD 요청으로 존재 여부만 확인)
            try:
                response = requests.head(url.toString(), allow_redirects=True, timeout=5)
                if response.status_code >= 400:
                    self.label.setText(f"URL:{url.toString()} 에 접근할 수 없거나 콘텐츠가 없읍니다.")
                    return
            except requests.RequestException as e:
                self.label.setText(f"URL:{url.toString()} 검사 실패: {e}")
                return
            
        # 🔍 확장자 확인
        suffix = os.path.splitext(url.fileName() or url.toString())[1].lower()
        supported_exts = ['.mp4', '.mov', '.m4v', '.webm']
        is_supported = suffix in supported_exts

        # 🔧 UI 조정
        self.speed_slider.setEnabled(is_supported)
        self.speed_label.setEnabled(is_supported)
        if not is_supported:
            prev_text = self.speed_label.text()
            self.speed_label.setText(f"{prev_text} [알림] 해당 형식은 속도 제어 불가: {suffix}")

        self.player.setSource(url)
        self.label.setText(f"재생 중: {url.toString()}")
        self.player.play()
        # print(f"[DEBUG] Media error: {self.player.errorString()}")

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def set_position(self, position):
        self.player.setPosition(position)

    def update_slider(self, position):
        self.slider.setValue(position)

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    def update_button(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play_pause.setText("⏸ 일시정지")
        else:
            self.btn_play_pause.setText("▶ 재생")

    
    def update_speed(self, value):
        speed = value / 100
        self.player.setPlaybackRate(speed)
        self.speed_label.setText(f"속도: {speed:.2f}x")

        # # 디버그 로그
        # print(f"[DEBUG] setPlaybackRate({speed:.2f})")
        # print(f"[DEBUG] State: {self.player.playbackState().name}")
        # print(f"[DEBUG] Source loaded: {self.player.source().toString()}")

        # 💡 일부 환경에서는 속도 변경 후 자동 정지되므로 다시 재생
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.play()

    def toggle_fullscreen_event(self, event):
        self.toggle_fullscreen()

    def toggle_fullscreen_button(self):
        self.toggle_fullscreen()

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.video_widget.setFullScreen(False)
            self.is_fullscreen = False
            self.btn_fullscreen.setText("⛶ 전체화면")
        else:
            self.video_widget.setFullScreen(True)
            self.is_fullscreen = True
            self.btn_fullscreen.setText("🗗 창 모드")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MoviePlayer()
    player.show()
    sys.exit(app.exec())