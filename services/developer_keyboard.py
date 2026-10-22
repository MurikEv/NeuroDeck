"""Physical keyboard input policy and optional developer navigation.

Enable explicitly with ENABLE_DEVELOPER_KEYBOARD = True in main.py.
Developer controls: arrows select a menu card, Enter opens it, Esc returns
to the menu. The selected card keeps its highlight in developer mode.
By default physical key events are blocked inside NeuroDeck; pointer events
and the on-screen keyboard (which edits text directly) remain available.
"""

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QWidget
import state


class DeveloperKeyboardController(QObject):
    def __init__(self, app, window, enabled=False):
        super().__init__(window)
        self.window = window
        self._enabled = enabled
        self._menu_controller = window.menu_controller
        self.selected_row = 0
        self.selected_col = 0
        self._app = app
        app.installEventFilter(self)
        app.aboutToQuit.connect(self.close)
        window.stackedWidget.currentChanged.connect(self._refresh_menu_highlight)
        for row in self._menu_controller.cards:
            for card in row:
                card["button"].pressed.connect(self._refresh_menu_highlight)
                card["button"].released.connect(self._refresh_menu_highlight)
        self._refresh_menu_highlight()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)
        self._refresh_menu_highlight()

    def _refresh_menu_highlight(self, *_args):
        selected_button = None
        if self.enabled:
            selected_button = self._menu_controller.cards[
                self.selected_row
            ][self.selected_col]["button"]
        self._menu_controller.highlight(selected_button)

    def close(self):
        self._app.removeEventFilter(self)
        self.enabled = False

    def eventFilter(self, obj, event):
        event_type = event.type()
        if event_type not in (
            QEvent.Type.KeyPress,
            QEvent.Type.KeyRelease,
            QEvent.Type.ShortcutOverride,
        ):
            return False
        if not isinstance(obj, QWidget):
            return False
        if obj is not self.window and not self.window.isAncestorOf(obj):
            return False

        if not self.enabled:
            event.accept()
            return True

        if event.key() == Qt.Key.Key_Escape:
            if event_type == QEvent.Type.KeyPress and not event.isAutoRepeat():
                keyboard = getattr(self.window, "keyboard_controller", None)
                if keyboard is not None and self.window.keyboard_frame.isVisible():
                    keyboard.close_keyboard()
                if self.window.stackedWidget.currentWidget() is not self.window.menu_screen:
                    state.ui_queue.put(("menu", None))
            event.accept()
            return True

        if (
            event_type == QEvent.Type.KeyPress
            and self.window.stackedWidget.currentWidget() is self.window.menu_screen
        ):
            return self._handle_menu_key(event)

        return False

    def _handle_menu_key(self, event):
        controller = self.window.menu_controller
        if controller is None:
            return False

        cards = controller.cards
        key = event.key()
        if key == Qt.Key.Key_Right:
            self.selected_col = (self.selected_col + 1) % len(cards[self.selected_row])
        elif key == Qt.Key.Key_Left:
            self.selected_col = (self.selected_col - 1) % len(cards[self.selected_row])
        elif key == Qt.Key.Key_Down:
            self.selected_row = (self.selected_row + 1) % len(cards)
            self.selected_col = min(self.selected_col, len(cards[self.selected_row]) - 1)
        elif key == Qt.Key.Key_Up:
            self.selected_row = (self.selected_row - 1) % len(cards)
            self.selected_col = min(self.selected_col, len(cards[self.selected_row]) - 1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.isAutoRepeat():
                cards[self.selected_row][self.selected_col]["button"].click()
        else:
            return False

        self._refresh_menu_highlight()
        event.accept()
        return True
