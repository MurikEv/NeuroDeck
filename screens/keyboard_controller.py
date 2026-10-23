from PyQt6.QtCore import QObject, QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QTextEdit


class KeyboardController(QObject):
    """Share the existing touch keyboard between registered text fields."""

    keyboard_closed = pyqtSignal()
    LETTER_ORDER = "qwertyuiopasdfghjklzxcvbnm"
    SYMBOLS = "1234567890@#%&*-_()/.,!?:="

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.active_text_widget = None
        self.is_syncing = False
        self._text_widgets = {}

        self.ai_input = window.ai_input
        self.ai_input_viewport = self.ai_input.viewport()
        self.register_text_widget(self.ai_input)

        window.keyboard_text_input.textChanged.connect(self.sync_to_active_widget)
        window.keyboard_text_input.cursorPositionChanged.connect(self._sync_cursor)
        window.stackedWidget.currentChanged.connect(self.close_keyboard)

        window.hide_key.clicked.connect(self.close_keyboard)
        window.key_comma.clicked.connect(lambda: self.insert_text(","))
        window.key_dot.clicked.connect(lambda: self.insert_text("."))
        window.key_space.clicked.connect(lambda: self.insert_text(" "))
        window.key_backspace.clicked.connect(self.backspace)

        key_buttons = [
            window.hide_key, window.key_comma, window.key_dot,
            window.key_space, window.key_backspace,
        ]
        for letter in "abcdefghijklmnopqrstuvwxyz":
            button = getattr(window, f"key_{letter}")
            button.clicked.connect(
                lambda checked=False, letter=letter: self.insert_text(
                    self._key_value(letter)
                )
            )
            key_buttons.append(button)
        for button in key_buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Reuse the existing keyboard and letter rows; only its input header
        # needs three small touch controls for note text and titles.
        window.keyboard_text_input.setGeometry(0, 10, 356, 61)
        self.shift_key = self._header_key("key_shift", "SHIFT", (364, 8, 52, 30))
        self.number_key = self._header_key("key_numbers", "123", (422, 8, 52, 30))
        self.enter_key = self._header_key("key_enter", "ENTER", (364, 42, 110, 30))
        self.shift_key.setCheckable(True)
        self.number_key.setCheckable(True)
        self.shift_key.toggled.connect(self._update_key_labels)
        self.number_key.toggled.connect(self._update_key_labels)
        self.enter_key.clicked.connect(self._enter)
        self._update_key_labels()

    def _header_key(self, name, text, geometry):
        button = QPushButton(text, self.window.keyboard_frame)
        button.setObjectName(name)
        button.setGeometry(*geometry)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(
            "QPushButton { background: #02141d; color: #00f4ff;"
            "border: 1px solid #00a9b7; border-radius: 3px;"
            "font-size: 11px; font-weight: bold; }"
            "QPushButton:pressed, QPushButton:checked {"
            "background: #00a9b7; color: #02141d; }"
            "QPushButton:disabled { color: #477078; border-color: #477078; }"
        )
        setattr(self.window, name, button)
        return button

    def _key_value(self, letter):
        if self.number_key.isChecked():
            return self.SYMBOLS[self.LETTER_ORDER.index(letter)]
        return letter.upper() if self.shift_key.isChecked() else letter

    def _update_key_labels(self, *_args):
        for letter in self.LETTER_ORDER:
            getattr(self.window, f"key_{letter}").setText(self._key_value(letter))
        numeric = self.number_key.isChecked()
        self.number_key.setText("ABC" if numeric else "123")
        self.shift_key.setEnabled(not numeric)

    def _enter(self):
        if isinstance(self.active_text_widget, QLineEdit):
            self.close_keyboard()
        elif self.active_text_widget is not None:
            self.insert_text("\n")

    def register_text_widget(self, widget):
        """Open the touch keyboard when this editable field is tapped."""
        if not isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
            raise TypeError("The touch keyboard requires a text input widget")
        self._text_widgets[widget] = widget
        widget.installEventFilter(self)
        if not isinstance(widget, QLineEdit):
            viewport = widget.viewport()
            self._text_widgets[viewport] = widget
            viewport.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            widget = self._text_widgets.get(obj)
            if widget is not None and widget.isEnabled() and not widget.isReadOnly():
                # Resolve the tapped caret before the full-screen keyboard covers
                # the field. Consuming the press avoids stealing keyboard focus.
                point = event.position().toPoint()
                if isinstance(widget, QLineEdit):
                    widget.setCursorPosition(widget.cursorPositionAt(point))
                elif obj is widget.viewport():
                    widget.setTextCursor(widget.cursorForPosition(point))
                self.open_keyboard(widget)
                return True
        return False

    @staticmethod
    def _cursor_positions(widget):
        if isinstance(widget, QLineEdit):
            position = widget.cursorPosition()
            start = widget.selectionStart()
            if start < 0:
                return position, position
            # Qt cursor offsets are UTF-16 code units, not Python characters.
            length = len(widget.selectedText().encode("utf-16-le")) // 2
            anchor = start + length if position == start else start
            return position, anchor
        cursor = widget.textCursor()
        return cursor.position(), cursor.anchor()

    @staticmethod
    def _set_cursor(widget, position, anchor):
        if isinstance(widget, QLineEdit):
            if position == anchor:
                widget.setCursorPosition(position)
            else:
                widget.setSelection(anchor, position - anchor)
            return
        cursor = widget.textCursor()
        end = widget.document().characterCount() - 1
        cursor.setPosition(min(anchor, end))
        cursor.setPosition(min(position, end), QTextCursor.MoveMode.KeepAnchor)
        widget.setTextCursor(cursor)

    def open_keyboard(self, text_widget):
        if not isinstance(text_widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
            raise TypeError("The touch keyboard requires a text input widget")
        if text_widget.isReadOnly() or not text_widget.isEnabled():
            return
        self.active_text_widget = text_widget
        text = (
            text_widget.text() if isinstance(text_widget, QLineEdit)
            else text_widget.toPlainText()
        )
        position, anchor = self._cursor_positions(text_widget)
        self.is_syncing = True
        try:
            self.window.keyboard_text_input.setPlainText(text)
            self._set_cursor(self.window.keyboard_text_input, position, anchor)
        finally:
            self.is_syncing = False

        self.enter_key.setText("DONE" if isinstance(text_widget, QLineEdit) else "ENTER")
        self.window.keyboard_frame.show()
        self.window.keyboard_frame.raise_()
        overlay = getattr(self.window, "brightness_overlay", None)
        if overlay is not None:
            overlay.raise_()
        self.window.keyboard_text_input.setFocus()

    def sync_to_active_widget(self):
        if self.is_syncing or self.active_text_widget is None:
            return
        text = self.window.keyboard_text_input.toPlainText()
        position, anchor = self._cursor_positions(self.window.keyboard_text_input)
        self.is_syncing = True
        try:
            if isinstance(self.active_text_widget, QLineEdit):
                # A title/search stays single-line even when multiline text is
                # pasted into the keyboard's existing QTextEdit buffer.
                normalized = text.translate(str.maketrans({
                    "\r": " ", "\n": " ", "\u2028": " ", "\u2029": " ",
                }))
                if normalized != text:
                    self.window.keyboard_text_input.setPlainText(normalized)
                    self._set_cursor(self.window.keyboard_text_input, position, anchor)
                self.active_text_widget.setText(normalized)
            else:
                self.active_text_widget.setPlainText(text)
            self._set_cursor(self.active_text_widget, position, anchor)
        finally:
            self.is_syncing = False

    def _sync_cursor(self):
        if not self.is_syncing and self.active_text_widget is not None:
            self._set_cursor(
                self.active_text_widget,
                *self._cursor_positions(self.window.keyboard_text_input),
            )

    def close_keyboard(self, *_args):
        old_active_widget = self.active_text_widget
        self.active_text_widget = None
        self.is_syncing = True
        try:
            self.window.keyboard_text_input.clear()
        finally:
            self.is_syncing = False
        self.window.keyboard_frame.hide()
        if old_active_widget is not None:
            if old_active_widget.isVisible():
                old_active_widget.setFocus()
            self.keyboard_closed.emit()

    def insert_text(self, text):
        self.window.keyboard_text_input.setFocus()
        cursor = self.window.keyboard_text_input.textCursor()
        cursor.insertText(text)
        self.window.keyboard_text_input.setTextCursor(cursor)
        self._sync_cursor()

    def backspace(self):
        self.window.keyboard_text_input.setFocus()
        cursor = self.window.keyboard_text_input.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()
        self.window.keyboard_text_input.setTextCursor(cursor)
        self._sync_cursor()
