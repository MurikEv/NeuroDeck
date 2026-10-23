"""Single-finger FT6336U input for the application-owned ST7796 display."""

import ctypes
import os
import sys
import threading
import time

from PyQt6 import sip
from PyQt6.QtCore import QEvent, QObject, QPoint, QPointF, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication


I2C_PATH = "/dev/i2c-5"
I2C_ADDRESS = 0x38
GPIO_CHIP = "gpiochip3"
RST_LINE = 1  # Physical pin 11 -> L3; H3 -> CTP_RST.
I2C_SLAVE = 0x0703
I2C_RDWR = 0x0707
I2C_M_RD = 0x0001
CANCEL = "cancel"


class _I2CMessage(ctypes.Structure):
    _fields_ = [
        ("addr", ctypes.c_uint16),
        ("flags", ctypes.c_uint16),
        ("length", ctypes.c_uint16),
        ("buffer", ctypes.POINTER(ctypes.c_uint8)),
    ]


class _I2CTransfer(ctypes.Structure):
    _fields_ = [
        ("messages", ctypes.POINTER(_I2CMessage)),
        ("count", ctypes.c_uint32),
    ]


def decode_touch(data):
    """Decode registers 0x02..0x06. Never turn invalid/multitouch data into a tap."""
    if len(data) != 5:
        raise ValueError("FT6336U sample must contain five bytes")
    count = data[0] & 0x0F
    if count == 0:
        return None
    if count != 1:
        return CANCEL
    event = data[1] >> 6
    if event == 1:  # Lift up.
        return None
    if event not in (0, 2):  # Down or contact.
        return CANCEL
    x = ((data[1] & 0x0F) << 8) | data[2]
    y = ((data[3] & 0x0F) << 8) | data[4]
    if not (0 <= x < 320 and 0 <= y < 480):
        return CANCEL
    return x, y


def touch_to_ui(point, rotation=90):
    """Invert the mirror's software rotation: native 320x480 -> Qt 480x320."""
    x, y = point
    if rotation == 90:
        return y, 319 - x
    if rotation == 270:
        return 479 - y, x
    raise ValueError("touch rotation must be 90 or 270 degrees")


class FT6336Touch:
    """Linux I2C/GPIO transport. A single worker owns it for its whole lifetime."""

    def __init__(self):
        self._fd = None
        self._chip = None
        self._rst = None
        try:
            if not os.path.exists(I2C_PATH):
                raise FileNotFoundError(f"{I2C_PATH} not found")
            # Hardware-only imports remain optional on HDMI/development machines.
            import fcntl
            import gpiod

            self._ioctl = fcntl.ioctl
            self._fd = os.open(I2C_PATH, os.O_RDWR)
            # Refuse an address already owned by a kernel driver; never use FORCE.
            self._ioctl(self._fd, I2C_SLAVE, I2C_ADDRESS)
            self._chip = gpiod.Chip(GPIO_CHIP)
            self._rst = self._chip.get_line(RST_LINE)
            self._rst.request(
                consumer="neurodeck-touch",
                type=gpiod.LINE_REQ_DIR_OUT,
                default_vals=[0],
            )
            time.sleep(0.05)
            self._rst.set_value(1)
            time.sleep(0.5)
            self.read_sample()  # Fail early if reset did not restore communication.
        except Exception:
            self.close()
            raise

    def read_sample(self):
        if self._fd is None:
            raise RuntimeError("touch device is closed")
        register = (ctypes.c_uint8 * 1)(0x02)
        result = (ctypes.c_uint8 * 5)()
        messages = (_I2CMessage * 2)(
            _I2CMessage(I2C_ADDRESS, 0, 1, register),
            _I2CMessage(I2C_ADDRESS, I2C_M_RD, 5, result),
        )
        transfer = _I2CTransfer(messages, 2)
        # I2C_RDWR keeps register selection and read in one repeated-start
        # transaction, just like the working i2ctransfer hardware test.
        completed = self._ioctl(self._fd, I2C_RDWR, bytearray(transfer))
        if completed != 2:
            raise OSError("incomplete FT6336U I2C transfer")
        return decode_touch(bytes(result))

    def close(self):
        fd, self._fd = self._fd, None
        rst, self._rst = self._rst, None
        chip, self._chip = self._chip, None
        for resource, release in (
            (fd, os.close),
            (rst, lambda line: line.release()),
            (chip, lambda handle: handle.close()),
        ):
            if resource is not None:
                try:
                    release(resource)
                except Exception as exc:
                    print(f"FT6336 touch cleanup warning: {exc}", file=sys.stderr)


class QtTouchService(QObject):
    """Read I2C off-thread and deliver pointer events only in the Qt thread."""

    sample = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, window, rotation=90):
        super().__init__(window)
        touch_to_ui((0, 0), rotation)  # Validate configuration before starting.
        self._window = window
        self._rotation = rotation
        self._stop = threading.Event()
        self._worker = None
        self._target = None
        self._position = QPoint()
        self._press_position = QPoint()
        self._ignore_until_release = False
        self._last_tap = None
        self._tap_candidate = False
        self.sample.connect(self._on_sample)
        self.failed.connect(self._on_failure)
        window.stackedWidget.currentChanged.connect(self._cancel)
        window.installEventFilter(self)
        QApplication.instance().aboutToQuit.connect(self.close)

    def start(self):
        if self._worker is not None:
            return
        if self._stop.is_set():
            raise RuntimeError("a stopped touch service cannot be restarted")
        worker = threading.Thread(target=self._poll, name="ft6336-touch", daemon=True)
        worker.start()
        self._worker = worker

    def _poll(self):
        device = None
        try:
            device = FT6336Touch()
            previous = object()
            print("FT6336 touch ready: /dev/i2c-5 address 0x38")
            while not self._stop.is_set():
                sample = device.read_sample()
                if sample != previous:
                    self.sample.emit(sample)
                    previous = sample
                self._stop.wait(0.02)
        except Exception as exc:
            if not self._stop.is_set():
                self.failed.emit(str(exc))
        finally:
            if device is not None:
                device.close()

    def _send(self, target, event_type, position, held):
        if sip.isdeleted(target):
            return
        local = target.mapFrom(self._window, position)
        button = (
            Qt.MouseButton.NoButton if event_type == QEvent.Type.MouseMove
            else Qt.MouseButton.LeftButton
        )
        event = QMouseEvent(
            event_type,
            QPointF(local),
            QPointF(position),
            QPointF(self._window.mapToGlobal(position)),
            button,
            Qt.MouseButton.LeftButton if held else Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(target, event)

    @pyqtSlot(object)
    def _on_sample(self, sample):
        if self._stop.is_set():
            return
        if sample == CANCEL:
            self._cancel()
            return
        if sample is None:
            if not self._ignore_until_release:
                self._release()
            self._ignore_until_release = False
            return
        if self._ignore_until_release:
            return
        position = QPoint(*touch_to_ui(sample, self._rotation))
        self._position = position
        if self._target is None:
            if not self._window.isVisible() or not self._window.isActiveWindow():
                self._ignore_until_release = True
                return
            target = self._window.childAt(position)
            if target is None or not target.isEnabled():
                self._ignore_until_release = True
                return
            self._target = target
            self._press_position = position
            self._tap_candidate = True
            event_type = QEvent.Type.MouseButtonPress
            if self._last_tap is not None:
                last_target, last_position, last_time = self._last_tap
                if (
                    target is last_target
                    and (position - last_position).manhattanLength()
                    <= QApplication.startDragDistance()
                    and (time.monotonic() - last_time) * 1000
                    <= QApplication.doubleClickInterval()
                ):
                    event_type = QEvent.Type.MouseButtonDblClick
                    self._tap_candidate = False
            self._last_tap = None
            self._send(target, event_type, position, held=True)
        else:
            target = self._target
            if sip.isdeleted(target) or not target.isVisible() or not target.isEnabled():
                self._cancel()
                return
            if (position - self._press_position).manhattanLength() > QApplication.startDragDistance():
                self._tap_candidate = False
            # Keep the original recipient while dragging outside a button.
            # Qt then cancels clicked() when release happens outside its bounds.
            self._send(target, QEvent.Type.MouseMove, position, held=True)

    def _release(self):
        target, self._target = self._target, None
        if target is None or sip.isdeleted(target):
            return
        local = target.mapFrom(self._window, self._position)
        if self._tap_candidate and target.rect().contains(local):
            self._last_tap = (target, self._position, time.monotonic())
        self._send(target, QEvent.Type.MouseButtonRelease, self._position, held=False)

    def _cancel(self, *_args):
        target, self._target = self._target, None
        self._last_tap = None
        self._ignore_until_release = True
        if target is None or sip.isdeleted(target):
            return
        # Never turn a device failure, page change or multitouch into a click.
        outside = target.mapTo(self._window, QPoint(-10, -10))
        self._send(target, QEvent.Type.MouseMove, outside, held=True)
        self._send(target, QEvent.Type.MouseButtonRelease, outside, held=False)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Hide, QEvent.Type.WindowDeactivate):
            self._cancel()
        return False

    @pyqtSlot(str)
    def _on_failure(self, message):
        self._stop.set()
        self._cancel()
        print(f"FT6336 touch unavailable: {message}", file=sys.stderr)

    def close(self):
        self._stop.set()
        self._cancel()
        self._window.removeEventFilter(self)
        worker = self._worker
        if worker is not None:
            worker.join(timeout=2.0)
            if worker.is_alive():
                # The worker retains sole ownership of I2C/RST until it exits.
                print("FT6336 touch cleanup warning: worker still active", file=sys.stderr)
                return False
        self._worker = None
        return True
