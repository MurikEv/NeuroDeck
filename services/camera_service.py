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

    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
