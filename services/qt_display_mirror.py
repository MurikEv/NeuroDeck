import queue
import sys
import threading

from PyQt6.QtCore import QObject, QPoint, QTimer
from PyQt6.QtGui import QImage, QPainter, QRegion, QTransform


UI_WIDTH = 480
UI_HEIGHT = 320
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480
DEFAULT_CAPTURE_INTERVAL_MS = 250


class QtDisplayMirror(QObject):
    """Render the existing Qt window and send only the latest frame to SPI."""

    def __init__(
        self,
        window,
        display,
        rotation=90,
        capture_interval_ms=DEFAULT_CAPTURE_INTERVAL_MS,
    ):
        super().__init__(window)
        if rotation not in (90, 270):
            raise ValueError("ST7796 mirror rotation must be 90 or 270 degrees")
        if capture_interval_ms <= 0:
            raise ValueError("capture interval must be positive")

        self._window = window
        self._display = display
        self._rotation = rotation
        self._frames = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._failure_lock = threading.Lock()
        self._failure_reported = False
        self._last_frame = None
        self._worker = None

        self._timer = QTimer(self)
        self._timer.setInterval(capture_interval_ms)
        self._timer.timeout.connect(self._capture_frame)

    def start(self):
        if self._worker is not None:
            return
        if self._stop_event.is_set():
            raise RuntimeError("a stopped ST7796 mirror cannot be restarted")

        worker = threading.Thread(
            target=self._worker_loop,
            name="st7796-mirror",
            daemon=True,
        )
        worker.start()
        self._worker = worker
        self._timer.start()
        QTimer.singleShot(0, self._capture_frame)

    def stop(self):
        self._timer.stop()
        self._stop_event.set()

        try:
            while True:
                self._frames.get_nowait()
        except queue.Empty:
            pass

        try:
            self._frames.put_nowait(None)
        except queue.Full:
            pass

        worker = self._worker
        if worker is not None:
            worker.join(timeout=2.0)
            if worker.is_alive():
                print(
                    "ST7796 mirror cleanup warning: SPI worker did not stop",
                    file=sys.stderr,
                )
                return False
        self._worker = None
        return True

    def _capture_frame(self):
        if self._stop_event.is_set():
            self._timer.stop()
            return

        try:
            frame = self._render_rgb565_frame()
        except Exception as exc:
            self._timer.stop()
            self._report_failure("Qt capture failed", exc)
            return

        if frame == self._last_frame:
            return
        self._last_frame = frame

        try:
            self._frames.put_nowait(frame)
            return
        except queue.Full:
            pass

        try:
            self._frames.get_nowait()
        except queue.Empty:
            pass

        try:
            self._frames.put_nowait(frame)
        except queue.Full:
            pass

    def _render_rgb565_frame(self):
        if (
            self._window.width() < UI_WIDTH
            or self._window.height() < UI_HEIGHT
        ):
            raise RuntimeError(
                "Qt window is smaller than the required 480x320 canvas: "
                f"{self._window.width()}x{self._window.height()}"
            )

        canvas = QImage(
            UI_WIDTH,
            UI_HEIGHT,
            QImage.Format.Format_RGB32,
        )
        canvas.fill(0xFF000000)

        painter = QPainter(canvas)
        try:
            self._window.render(
                painter,
                QPoint(0, 0),
                QRegion(0, 0, UI_WIDTH, UI_HEIGHT),
            )
        finally:
            painter.end()

        transform = QTransform()
        transform.rotate(self._rotation)
        rotated = canvas.transformed(transform)
        if (
            rotated.width() != DISPLAY_WIDTH
            or rotated.height() != DISPLAY_HEIGHT
        ):
            raise RuntimeError(
                "rotated Qt frame is not 320x480: "
                f"{rotated.width()}x{rotated.height()}"
            )

        rgb565 = rotated.convertToFormat(QImage.Format.Format_RGB16)
        return self._rgb565_big_endian_bytes(rgb565)

    @staticmethod
    def _rgb565_big_endian_bytes(image):
        row_size = image.width() * 2
        pointer = image.constBits()
        pointer.setsize(image.sizeInBytes())
        raw = bytes(pointer)

        if image.bytesPerLine() != row_size:
            stride = image.bytesPerLine()
            raw = b"".join(
                raw[offset:offset + row_size]
                for offset in range(0, stride * image.height(), stride)
            )

        if sys.byteorder == "big":
            return raw

        converted = bytearray(len(raw))
        converted[0::2] = raw[1::2]
        converted[1::2] = raw[0::2]
        return bytes(converted)

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                frame = self._frames.get(timeout=0.1)
            except queue.Empty:
                continue

            if frame is None or self._stop_event.is_set():
                return

            try:
                self._display.blit_rgb565(
                    frame,
                    DISPLAY_WIDTH,
                    DISPLAY_HEIGHT,
                )
            except Exception as exc:
                self._report_failure("SPI frame write failed", exc)
                return

    def _report_failure(self, reason, error):
        with self._failure_lock:
            if self._failure_reported:
                return
            self._failure_reported = True

        self._stop_event.set()
        print(f"ST7796 mirror unavailable: {reason}: {error}", file=sys.stderr)
