from datetime import datetime
from pathlib import Path

import cv2


class CameraService:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def open_camera(self):
        if self.cap is not None and self.cap.isOpened():
            return True

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.release_camera()
            return False

        return True

    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def capture_photo(self, frame):
        if frame is None:
            return None

        return frame.copy()

    def save_photo(self, frame, folder_path="data/camera_pictures"):
        if frame is None:
            return None

        folder = Path(folder_path)
        folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = folder / f"{timestamp}.jpg"
        counter = 1
        while file_path.exists():
            file_path = folder / f"{timestamp}_{counter}.jpg"
            counter += 1

        if not cv2.imwrite(str(file_path), frame):
            return None

        return file_path

    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
