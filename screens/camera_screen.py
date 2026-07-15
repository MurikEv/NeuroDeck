from PyQt6.QtCore import QObject, QThread, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

import cv2
import state
from services.camera_service import CameraService


class CameraWorker(QThread):
    frame_ready = pyqtSignal(object)
    camera_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.camera_service = CameraService()
        self.is_running = False

    def run(self):
        if not self.camera_service.open_camera():
            self.camera_error.emit("Camera not available")
            return

        self.is_running = True
        try:
            while self.is_running:
                frame = self.camera_service.read_frame()
                if frame is not None:
                    self.frame_ready.emit(frame.copy())
                self.msleep(30)
        finally:
            self.camera_service.release_camera()
            self.is_running = False

    def stop(self):
        self.is_running = False
        return self.wait(1000)


class CameraController(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.camera_worker = None
        self.current_frame = None
        self.captured_frame = None
        self.last_saved_photo_path = None
        self.is_active = False
        self.is_preview_paused = False

        self.window.camera_capture_btn.clicked.connect(self.capture_photo)
        self.window.camera_back_btn.clicked.connect(self.back_to_menu)
        self.window.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window.camera_preview.setStyleSheet("background-color: black; color: white;")

    def start(self):
        if self.is_active:
            return

        self.is_active = True
        self.captured_frame = None
        self.window.camera_preview.setText("")

        self.camera_worker = CameraWorker()
        self.camera_worker.frame_ready.connect(self.handle_frame)
        self.camera_worker.camera_error.connect(self.handle_camera_error)
        self.camera_worker.finished.connect(self.handle_worker_finished)
        self.camera_worker.start()

    def stop(self):
        if self.camera_worker is not None:
            if self.camera_worker.stop():
                self.camera_worker = None

        self.current_frame = None
        self.captured_frame = None
        self.is_active = False
        self.is_preview_paused = False
        self.window.camera_preview.clear()

    def handle_frame(self, frame):
        if not self.is_active:
            return

        self.current_frame = frame
        if not self.is_preview_paused:
            self.show_frame(frame)

    def handle_camera_error(self, message):
        self.is_active = False
        self.window.camera_preview.setText(message)

    def handle_worker_finished(self):
        if self.sender() == self.camera_worker:
            self.camera_worker = None

    def capture_photo(self):
        self.captured_frame = CameraService.capture_photo(self.current_frame)
        if self.captured_frame is None:
            return

        self.is_preview_paused = True
        self.last_saved_photo_path = CameraService.save_photo(self.captured_frame)
        self.show_frame(self.captured_frame)
        QTimer.singleShot(500, self.resume_preview)

    def resume_preview(self):
        self.is_preview_paused = False
        if self.is_active and self.current_frame is not None:
            self.show_frame(self.current_frame)

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
