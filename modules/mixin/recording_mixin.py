from __future__ import annotations
from modules.common_import_v2 import *
import cv2
import numpy as np
from PIL import Image
import ffmpeg

class RecordingMixin:
    """녹화 기능 믹스인. recording_method='cv2' 또는 'ffmpeg' default='ffmpeg' 지원"""

    def __init__(self, recording_method: str = 'ffmpeg'):
        self._recording = False
        self._record_method = recording_method  # 'cv2' or 'ffmpeg'
        self._record_fps = 4
        self._record_size = (1600, 1200)
        
        self._record_file_name = "recorded_output.mp4"
        self._record_dir = Utils.makeDir("debug")
        self._record_path = os.path.join(self._record_dir, self._record_file_name)

        self._video_writer = None            # cv2 용
        self._recorded_frames = []           # ffmpeg 용

        if self._record_method == 'ffmpeg':
            self._ffmpeg_path = Utils.get_ffmpeg_path()

    def start_recording(self, output_path=None, size=None, fps=None):
        if self._recording:
            return  # 이미 녹화 중

        self._record_path = output_path or self._record_path
        self._record_size = size or self._record_size
        self._record_fps = fps or self._record_fps
        self._recording = True

        if self._record_method == 'cv2':
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self._video_writer = cv2.VideoWriter(
                self._record_path, fourcc, self._record_fps, self._record_size
            )
        elif self._record_method == 'ffmpeg':
            self._recorded_frames = []

        print(f"[녹화 시작] ({self._record_method}) → {self._record_path}")

    def get_record_path(self) -> str:
        return self._record_path

    def stop_recording(self):
        if not self._recording:
            return

        if self._record_method == 'cv2':
            if self._video_writer:
                self._video_writer.release()
                self._video_writer = None

        elif self._record_method == 'ffmpeg':
            if self._recorded_frames:
                self._save_video_with_ffmpeg(self._recorded_frames)

        self._recorded_frames = []
        self._recording = False
        print(f"[녹화 종료] → {self._record_path}")

    def write_frame_by_pixmap(self, pixmap: QPixmap):
        """QPixmap 프레임을 기록"""
        if not self._recording:
            return

        qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
        w, h = qimg.width(), qimg.height()
        buffer = qimg.bits().asstring(w * h * 3)
        frame = np.frombuffer(buffer, dtype=np.uint8).reshape((h, w, 3))

        if self._record_method == 'cv2':
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if (w, h) != self._record_size:
                frame_bgr = cv2.resize(frame_bgr, self._record_size)
            self._video_writer.write(frame_bgr)

        elif self._record_method == 'ffmpeg':
            pil_image = Image.fromarray(frame)
            self._recorded_frames.append(pil_image)

    def write_frame_by_pil_image(self, pil_image: Image.Image):
        """PIL.Image 프레임을 기록"""
        if not self._recording:
            return

        if self._record_method == 'cv2':
            frame_rgb = np.array(pil_image.convert("RGB"))
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            if (frame_bgr.shape[1], frame_bgr.shape[0]) != self._record_size:
                frame_bgr = cv2.resize(frame_bgr, self._record_size)
            self._video_writer.write(frame_bgr)

        elif self._record_method == 'ffmpeg':
            self._recorded_frames.append(pil_image.copy())

    def _save_video_with_ffmpeg(self, frames: list[Image.Image]):
        w, h = frames[0].size
        process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', s=f'{w}x{h}', framerate=self._record_fps)
            .output(self._record_path, pix_fmt='yuv420p', vcodec='libx264', crf=23)
            .overwrite_output()
            .run_async(pipe_stdin=True, cmd=self._ffmpeg_path if self._ffmpeg_path else None)
        )
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        process.wait()

