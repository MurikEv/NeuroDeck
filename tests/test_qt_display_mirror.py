"""Regressions for short presses while the SPI transport is busy."""

import os
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import uic
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

import state
from screens.menu_screen import MenuController
from services.qt_display_mirror import MAX_PENDING_PRESS_FRAMES, QtDisplayMirror


class SlowDisplay:
    def __init__(self):
        self.entered = threading.Event()
        self.allow_write = threading.Event()
        self.frames = []

    def blit_rgb565(self, frame, width, height):
        if not self.frames:
            self.entered.set()
            if not self.allow_write.wait(timeout=3):
                raise TimeoutError("test SPI gate was not released")
        self.frames.append(frame)


class MirrorFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        while not state.ui_queue.empty():
            state.ui_queue.get_nowait()
        ui = Path(__file__).resolve().parents[1] / "screens" / "main_window.ui"
        self.window = uic.loadUi(str(ui))
        self.window.keyboard_frame.hide()
        self.window.stackedWidget.setCurrentWidget(self.window.menu_screen)
        self.menu = MenuController(self.window)
        self.window.show()
        self.app.processEvents()
        self.display = SlowDisplay()
        self.mirror = QtDisplayMirror(self.window, self.display)

    def tearDown(self):
        self.display.allow_write.set()
        self.mirror.stop()
        self.window.close()
        self.app.processEvents()

    def start_busy_spi(self):
        self.mirror.start()
        self.mirror._timer.stop()  # Reproduce a tap entirely between timer ticks.
        self.mirror._capture_frame()
        self.assertTrue(self.display.entered.wait(timeout=1))

    def finish_transfers(self, count):
        self.display.allow_write.set()
        deadline = time.monotonic() + 1
        while len(self.display.frames) < count and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertEqual(len(self.display.frames), count)

    def test_fast_press_survives_release_and_next_screen_during_busy_spi(self):
        self.start_busy_spi()
        button = self.window.ai_btn
        QTest.mousePress(button, Qt.MouseButton.LeftButton)
        pressed_frame = self.mirror._last_frame
        self.assertEqual(len(pressed_frame), 320 * 480 * 2)
        QTest.mouseRelease(button, Qt.MouseButton.LeftButton)
        self.assertEqual(state.ui_queue.get_nowait(), ("ai", None))
        self.assertFalse(button.isDown())  # UI release never waits for SPI.
        self.window.stackedWidget.setCurrentWidget(self.window.ai_screen)
        final_frame = self.mirror._last_frame
        self.assertNotEqual(pressed_frame, final_frame)
        self.finish_transfers(3)
        self.assertEqual(self.display.frames[1:], [pressed_frame, final_frame])

    def test_drag_outside_still_cancels_click_and_sends_unpressed_state(self):
        self.start_busy_spi()
        button = self.window.ai_btn
        QTest.mousePress(button, Qt.MouseButton.LeftButton)
        pressed_frame = self.mirror._last_frame
        outside = QPoint(-10, -10)
        move = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(outside),
            QPointF(button.mapToGlobal(outside)), Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(button, move)
        QTest.mouseRelease(button, Qt.MouseButton.LeftButton, pos=outside)
        self.assertTrue(state.ui_queue.empty())
        self.assertFalse(button.isDown())
        final_frame = self.mirror._last_frame
        self.assertNotEqual(pressed_frame, final_frame)
        self.finish_transfers(3)
        self.assertEqual(self.display.frames[1:], [pressed_frame, final_frame])

    def test_ordinary_frames_still_keep_only_the_latest(self):
        with patch.object(self.mirror, "_render_rgb565_frame", return_value=b"initial"):
            self.start_busy_spi()
            for frame in (b"camera-1", b"camera-2", b"camera-3"):
                self.mirror._render_rgb565_frame.return_value = frame
                self.mirror._capture_frame()
            self.finish_transfers(2)
        self.assertEqual(self.display.frames, [b"initial", b"camera-3"])

    def test_press_backlog_is_bounded_and_final_frame_is_not_lost(self):
        with patch.object(self.mirror, "_render_rgb565_frame", return_value=b"initial"):
            self.start_busy_spi()
            for i in range(20):
                self.mirror._render_rgb565_frame.return_value = f"press-{i}".encode()
                self.mirror._capture_press()
                self.assertLessEqual(len(self.mirror._press_frames), MAX_PENDING_PRESS_FRAMES)
                self.mirror._render_rgb565_frame.return_value = b"released"
                self.mirror._capture_changed()
            self.finish_transfers(4)
        self.assertEqual(self.display.frames, [b"initial", b"press-0", b"press-19", b"released"])

    def test_press_is_protected_even_if_timer_captured_the_same_state(self):
        with patch.object(self.mirror, "_render_rgb565_frame", return_value=b"initial"):
            self.start_busy_spi()
            self.mirror._render_rgb565_frame.return_value = b"pressed"
            self.mirror._capture_frame()
            self.mirror._capture_press()
            self.mirror._render_rgb565_frame.return_value = b"released"
            self.mirror._capture_changed()
            self.finish_transfers(3)
        self.assertEqual(self.display.frames, [b"initial", b"pressed", b"released"])

    def test_start_failure_stop_and_capture_failure_are_safe(self):
        with patch("services.qt_display_mirror.threading.Thread") as thread:
            thread.return_value.start.side_effect = RuntimeError("cannot start")
            with self.assertRaisesRegex(RuntimeError, "cannot start"):
                self.mirror.start()
        self.assertIsNone(self.mirror._worker)
        with patch.object(self.mirror, "_render_rgb565_frame", side_effect=RuntimeError("capture failed")):
            self.mirror._capture_frame()
        self.assertTrue(self.mirror._stop_event.is_set())
        self.assertTrue(self.mirror.stop())


if __name__ == "__main__":
    unittest.main()
