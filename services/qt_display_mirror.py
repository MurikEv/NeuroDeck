from collections import deque
import sys
import threading
from weakref import WeakSet

from PyQt6.QtCore import QEvent, QObject, QPoint, QTimer
from PyQt6.QtGui import QImage, QPainter, QRegion, QTransform
from PyQt6.QtWidgets import QAbstractButton, QApplication, QWidget


UI_WIDTH = 480
UI_HEIGHT = 320
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480
DEFAULT_CAPTURE_INTERVAL_MS = 250
MAX_PENDING_PRESS_FRAMES = 2


class QtDisplayMirror(QObject):
    """Mirror Qt, preserving short button presses ahead of the latest UI frame."""

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
        self._frame_ready = threading.Condition()
        self._press_frames = deque()
        self._pending_frame = None
        self._stop_event = threading.Event()
        self._failure_lock = threading.Lock()
        self._failure_reported = False
        self._last_frame = None
        self._worker = None
        self._registered_buttons = WeakSet()
        self._registration_pending = False
        self._application = QApplication.instance()

        self._timer = QTimer(self)
        self._timer.setInterval(capture_interval_ms)
        self._timer.timeout.connect(self._capture_frame)

        # Connect after the screen controllers so their highlight/text updates
        # are already applied when render() captures the signal's exact state.
        for button in window.findChildren(QAbstractButton):
            self.register_button(button)
        window.stackedWidget.currentChanged.connect(self._capture_changed)
        self._application.installEventFilter(self)

    def register_button(self, button):
        if (
            self._stop_event.is_set()
            or button in self._registered_buttons
            or not self._window.isAncestorOf(button)
        ):
            return
        button.pressed.connect(self._capture_press)
        button.released.connect(self._capture_changed)
        button.clicked.connect(self._capture_changed)
        self._registered_buttons.add(button)

    def _register_new_buttons(self):
        self._registration_pending = False
        if self._stop_event.is_set():
            return
        for button in self._window.findChildren(QAbstractButton):
            self.register_button(button)

    def eventFilter(self, obj, event):
        if self._stop_event.is_set():
            return False
        if event.type() == QEvent.Type.Show and isinstance(obj, QAbstractButton):
            self.register_button(obj)
        elif (
            event.type() in (QEvent.Type.ChildAdded, QEvent.Type.ChildPolished)
            and isinstance(obj, QWidget)
            and (obj is self._window or self._window.isAncestorOf(obj))
            and not self._registration_pending
        ):
            self._registration_pending = True
            QTimer.singleShot(0, self._register_new_buttons)
        return False

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
        self._application.removeEventFilter(self)
        with self._frame_ready:
            self._stop_event.set()
            self._press_frames.clear()
            self._pending_frame = None
            self._frame_ready.notify_all()

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

    def _capture_press(self):
        self._capture_frame(preserve_press=True)

    def _capture_changed(self, *_args):
        self._capture_frame()

    def _capture_frame(self, preserve_press=False):
        if self._stop_event.is_set():
            self._timer.stop()
            return

        try:
            frame = self._render_rgb565_frame()
        except Exception as exc:
            self._timer.stop()
            self._report_failure("Qt capture failed", exc)
            return

        if frame == self._last_frame and not preserve_press:
            return
        self._last_frame = frame

        with self._frame_ready:
            if self._stop_event.is_set():
                return
            if preserve_press:
                # A timer/release/next-screen frame must not erase a short tap
                # while a previous SPI transfer is still in progress.
                self._pending_frame = None
                if not self._press_frames or self._press_frames[-1] != frame:
                    if len(self._press_frames) == MAX_PENDING_PRESS_FRAMES:
                        # Bound latency under a burst: retain the oldest pending
                        # feedback and replace the newest with the latest press.
                        self._press_frames.pop()
                    self._press_frames.append(frame)
            else:
                self._pending_frame = frame
            self._frame_ready.notify()

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
        while True:
            with self._frame_ready:
                self._frame_ready.wait_for(
                    lambda: self._stop_event.is_set()
                    or bool(self._press_frames)
                    or self._pending_frame is not None
                )
                if self._stop_event.is_set():
                    return
                if self._press_frames:
                    frame = self._press_frames.popleft()
                else:
                    frame, self._pending_frame = self._pending_frame, None

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

        with self._frame_ready:
            self._stop_event.set()
            self._frame_ready.notify_all()
        print(f"ST7796 mirror unavailable: {reason}: {error}", file=sys.stderr)
