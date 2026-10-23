"""Offline transport and real-Qt input checks; no Radxa hardware required."""

import ctypes
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import uic
from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication

import state
from screens.keyboard_controller import KeyboardController
from screens.menu_screen import MenuController
from screens.settings_screen import SettingsController
from services.touch_service import (
    CANCEL, FT6336Touch, I2C_ADDRESS, I2C_M_RD, I2C_RDWR,
    QtTouchService, _I2CTransfer, decode_touch, touch_to_ui,
)


class TransportTests(unittest.TestCase):
    def test_measured_corners_and_inverse_rotation(self):
        measurements = [(314, 38), (287, 451), (50, 444), (46, 34)]
        self.assertEqual(
            [touch_to_ui(point) for point in measurements],
            [(38, 5), (451, 32), (444, 269), (34, 273)],
        )
        for raw in [(0, 0), (319, 479), (100, 200)]:
            ui90 = touch_to_ui(raw, 90)
            ui270 = touch_to_ui(raw, 270)
            self.assertEqual(ui270, (479 - ui90[0], 319 - ui90[1]))

    def test_decode_does_not_click_on_multitouch_or_bad_samples(self):
        self.assertEqual(decode_touch(bytes([1, 0x81, 0x3A, 0, 38])), (314, 38))
        self.assertIsNone(decode_touch(bytes([0, 0, 0, 0, 0])))
        self.assertIsNone(decode_touch(bytes([1, 0x40, 0, 0, 0])))
        self.assertEqual(decode_touch(bytes([2, 0, 0, 0, 0])), CANCEL)
        self.assertEqual(decode_touch(bytes([1, 0xC0, 0, 0, 0])), CANCEL)
        self.assertEqual(decode_touch(bytes([1, 1, 64, 0, 0])), CANCEL)
        with self.assertRaises(ValueError):
            decode_touch(b"short sample")

    def test_combined_ioctl_uses_valid_pointers_and_register_order(self):
        device = FT6336Touch.__new__(FT6336Touch)
        device._fd = 42

        def ioctl(fd, operation, argument):
            self.assertEqual((fd, operation), (42, I2C_RDWR))
            transfer = _I2CTransfer.from_buffer(argument)
            self.assertEqual(transfer.count, 2)
            first, second = transfer.messages[0], transfer.messages[1]
            self.assertEqual((first.addr, first.flags, first.length), (I2C_ADDRESS, 0, 1))
            self.assertEqual(first.buffer[0], 0x02)
            self.assertEqual((second.addr, second.flags, second.length), (I2C_ADDRESS, I2C_M_RD, 5))
            ctypes.memmove(second.buffer, bytes([1, 0, 50, 1, 188]), 5)
            return 2

        device._ioctl = ioctl
        self.assertEqual(device.read_sample(), (50, 444))
        device._ioctl = lambda *_args: 1
        with self.assertRaisesRegex(OSError, "incomplete"):
            device.read_sample()

    def test_missing_device_is_optional_and_cleanup_is_idempotent(self):
        with patch("services.touch_service.os.path.exists", return_value=False):
            with self.assertRaisesRegex(FileNotFoundError, "/dev/i2c-5 not found"):
                FT6336Touch()
        device = FT6336Touch.__new__(FT6336Touch)
        device._fd, device._rst, device._chip = 42, Mock(), Mock()
        rst, chip = device._rst, device._chip
        with patch("services.touch_service.os.close") as close_fd:
            device.close()
            device.close()
        close_fd.assert_called_once_with(42)
        rst.release.assert_called_once()
        chip.close.assert_called_once()

    def test_initial_read_failure_releases_reset_and_i2c(self):
        gpio = Mock()
        ioctl = Mock()
        chip = gpio.Chip.return_value
        rst = chip.get_line.return_value
        with (
            patch.dict(sys.modules, {"gpiod": gpio, "fcntl": Mock(ioctl=ioctl)}),
            patch("services.touch_service.os.path.exists", return_value=True),
            patch("services.touch_service.os.open", return_value=42),
            patch("services.touch_service.os.close") as close_fd,
            patch("services.touch_service.time.sleep"),
            patch.object(FT6336Touch, "read_sample", side_effect=OSError("no ACK")),
        ):
            with self.assertRaisesRegex(OSError, "no ACK"):
                FT6336Touch()
        gpio.Chip.assert_called_once_with("gpiochip3")
        chip.get_line.assert_called_once_with(1)
        self.assertEqual(rst.request.call_args.kwargs["default_vals"], [0])
        rst.set_value.assert_called_once_with(1)
        rst.release.assert_called_once()
        chip.close.assert_called_once()
        close_fd.assert_called_once_with(42)


class QtInputTests(unittest.TestCase):
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
        self.keyboard = KeyboardController(self.window)
        self.settings = SettingsController(self.window)
        self.touch = QtTouchService(self.window)
        self.window.show()
        self.window.activateWindow()
        self.app.processEvents()

    def tearDown(self):
        self.touch.close()
        self.window.close()
        self.app.processEvents()

    def sample(self, position):
        self.touch._on_sample((319 - position.y(), position.x()))

    def center(self, widget):
        return widget.mapTo(self.window, widget.rect().center())

    def test_hold_release_and_double_tap(self):
        button = self.window.ai_btn
        position = self.center(button)
        self.sample(position)
        self.assertTrue(button.isDown())
        self.assertEqual(button.styleSheet(), self.menu.active_button_style)
        self.assertTrue(state.ui_queue.empty())
        self.touch._on_sample(None)
        self.assertEqual(state.ui_queue.get_nowait(), ("ai", None))
        self.assertFalse(button.isDown())
        self.assertEqual(button.styleSheet(), self.menu.base_button_style)
        self.sample(position)
        self.touch._on_sample(None)
        self.assertEqual(state.ui_queue.get_nowait(), ("ai", None))
        self.assertTrue(state.ui_queue.empty())

    def test_drag_outside_cancels_and_never_activates_another_button(self):
        button = self.window.ai_btn
        self.sample(self.center(button))
        self.sample(self.center(self.window.calculator_btn))
        self.assertFalse(button.isDown())
        self.assertFalse(self.window.calculator_btn.isDown())
        self.touch._on_sample(None)
        self.assertTrue(state.ui_queue.empty())

    def test_multitouch_page_change_and_io_failure_cancel_press(self):
        for reason in ("multitouch", "page", "error"):
            self.window.stackedWidget.setCurrentWidget(self.window.menu_screen)
            self.touch._on_sample(None)
            button = self.window.ai_btn
            self.sample(self.center(button))
            self.assertTrue(button.isDown())
            if reason == "multitouch":
                self.touch._on_sample(CANCEL)
            elif reason == "page":
                self.window.stackedWidget.setCurrentWidget(self.window.settings_screen)
            else:
                self.touch._on_failure("simulated I2C failure")
            self.assertFalse(button.isDown())
            self.touch._on_sample(None)
            self.assertTrue(state.ui_queue.empty())

    def test_on_screen_keyboard_still_receives_pointer_input(self):
        self.window.stackedWidget.setCurrentWidget(self.window.ai_screen)
        self.touch._on_sample(None)
        self.sample(self.center(self.window.ai_input))
        self.touch._on_sample(None)
        self.assertTrue(self.window.keyboard_frame.isVisible())
        self.sample(self.center(self.window.key_a))
        self.touch._on_sample(None)
        self.assertEqual(self.window.ai_input.toPlainText(), "a")

    def test_worker_start_failure_and_hung_stop_keep_resource_ownership(self):
        with patch("services.touch_service.threading.Thread") as thread:
            thread.return_value.start.side_effect = RuntimeError("cannot start")
            with self.assertRaisesRegex(RuntimeError, "cannot start"):
                self.touch.start()
            self.assertIsNone(self.touch._worker)
        worker = Mock()
        worker.is_alive.return_value = True
        self.touch._worker = worker
        self.assertFalse(self.touch.close())
        self.assertIs(self.touch._worker, worker)
        worker.is_alive.return_value = False
        self.assertTrue(self.touch.close())


if __name__ == "__main__":
    unittest.main()
