from PyQt6.QtCore import QObject, QEvent, Qt

class KeyboardController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window

        self.active_text_widget = None
        self.is_syncing = False

        self.ai_input = self.window.ai_input
        self.ai_input_viewport = self.ai_input.viewport()
        self.ai_input.installEventFilter(self)
        self.ai_input_viewport.installEventFilter(self)

        self.window.keyboard_text_input.textChanged.connect(self.sync_to_active_widget)

        # --- Keys --- #
        self.window.hide_key.clicked.connect(self.close_keyboard)
        self.window.key_comma.clicked.connect(lambda: self.insert_text(","))
        self.window.key_dot.clicked.connect(lambda: self.insert_text("."))
        self.window.key_space.clicked.connect(lambda: self.insert_text(" "))
        self.window.key_backspace.clicked.connect(self.backspace)

        for letter in "abcdefghijklmnopqrstuvwxyz":
            button = getattr(self.window, f"key_{letter}")
            button.clicked.connect(
                lambda checked=False, letter=letter: self.insert_text(letter)
            )
        
        # --- Keys Focus --- #

        self.window.hide_key.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_a.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_d.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_e.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_f.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_g.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_h.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_i.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_j.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_k.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_l.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_m.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_n.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_o.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_p.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_q.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_r.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_s.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_u.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_v.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_x.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_y.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_z.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_comma.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.window.key_dot.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def backspace(self):
        self.window.keyboard_text_input.setFocus()

        cursor = self.window.keyboard_text_input.textCursor()
        cursor.deletePreviousChar()
        self.window.keyboard_text_input.setTextCursor(cursor)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj == self.ai_input_viewport:
                self.open_keyboard(self.ai_input)

        return False

    def open_keyboard(self, text_widget):
        self.active_text_widget = text_widget

        self.is_syncing = True
        self.window.keyboard_text_input.clear()
        self.window.keyboard_text_input.setPlainText(text_widget.toPlainText())
        self.is_syncing = False

        cursor = self.window.keyboard_text_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.window.keyboard_text_input.setTextCursor(cursor)

        self.window.keyboard_frame.show()
        self.window.keyboard_frame.raise_()
        self.window.brightness_overlay.raise_()
        self.window.keyboard_text_input.setFocus()

    def sync_to_active_widget(self):
        if self.is_syncing:
            return

        if self.active_text_widget is None:
            return

        text = self.window.keyboard_text_input.toPlainText()

        self.is_syncing = True
        self.active_text_widget.setPlainText(text)
        self.is_syncing = False

        cursor = self.active_text_widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.active_text_widget.setTextCursor(cursor)

    def close_keyboard(self):
        old_active_widget = self.active_text_widget

        self.is_syncing = True
        self.window.keyboard_text_input.clear()
        self.is_syncing = False

        self.window.keyboard_frame.hide()

        if old_active_widget is not None:
            old_active_widget.setFocus()

            cursor = old_active_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            old_active_widget.setTextCursor(cursor)

    def insert_text(self, text):
        self.window.keyboard_text_input.setFocus()

        cursor = self.window.keyboard_text_input.textCursor()
        cursor.insertText(text)
        self.window.keyboard_text_input.setTextCursor(cursor)
