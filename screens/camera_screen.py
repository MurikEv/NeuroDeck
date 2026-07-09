from PyQt6.QtCore import QObject, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap

import cv2
import state
from services.camera_service import CameraService


class CameraScreen(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.camera_service = CameraService()
        self.current_frame = None
        self.captured_frame = None
        self.is_active = False

        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)

        self.window.camera_capture_btn.clicked.connect(self.capture_photo)
        self.window.camera_back_btn.clicked.connect(self.back_to_menu)
        self.window.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window.camera_preview.setStyleSheet("background-color: black; color: white;")

    def start(self):
        if self.is_active:
            return

        if not self.camera_service.open_camera():
            self.window.camera_preview.setText("Camera not available")
            return

        self.is_active = True
        self.captured_frame = None
        self.window.camera_preview.setText("")
        self.preview_timer.start(30)

    def stop(self):
        self.preview_timer.stop()
        self.camera_service.release_camera()
        self.current_frame = None
        self.captured_frame = None
        self.is_active = False
        self.window.camera_preview.clear()

    def update_preview(self):
        frame = self.camera_service.read_frame()
        if frame is None:
            return

        self.current_frame = frame
        self.show_frame(frame)

    def capture_photo(self):
        self.captured_frame = self.camera_service.capture_photo(self.current_frame)
        if self.captured_frame is None:
            return

        self.preview_timer.stop()
        self.show_frame(self.captured_frame)
        QTimer.singleShot(500, self.resume_preview)

    def resume_preview(self):
        if self.is_active:
            self.preview_timer.start(30)

    def back_to_menu(self):
        state.ui_queue.put(("menu", None))

    def show_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.window.camera_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.window.camera_preview.setPixmap(scaled_pixmap)
