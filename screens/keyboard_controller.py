from PyQt6.QtCore import QObject, QEvent, Qt

class KeyboardController(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.active_text_widget = None
        self.is_syncing = False

        self.ai_input = self.window.ai_input
        self.ai_input_viewport = self.ai_input.viewport()
        self.ai_input.installEventFilter(self)
        self.ai_input_viewport.installEventFilter(self)

        self.window.keyboard_text_input.textChanged.connect(self.sync_to_active_widget)

        # --- Keys --- #
        self.window.hide_key.pressed.connect(self.close_keyboard)
        self.window.key_a.pressed.connect(lambda: self.insert_text("a"))
        self.window.key_b.pressed.connect(lambda: self.insert_text("b"))
        self.window.key_c.pressed.connect(lambda: self.insert_text("c"))
        self.window.key_d.pressed.connect(lambda: self.insert_text("d"))
        self.window.key_e.pressed.connect(lambda: self.insert_text("e"))
        self.window.key_f.pressed.connect(lambda: self.insert_text("f"))
        self.window.key_g.pressed.connect(lambda: self.insert_text("g"))
        self.window.key_h.pressed.connect(lambda: self.insert_text("h"))
        self.window.key_i.pressed.connect(lambda: self.insert_text("i"))
        self.window.key_j.pressed.connect(lambda: self.insert_text("j"))
        self.window.key_k.pressed.connect(lambda: self.insert_text("k"))
        self.window.key_l.pressed.connect(lambda: self.insert_text("l"))
        self.window.key_m.pressed.connect(lambda: self.insert_text("m"))
        self.window.key_n.pressed.connect(lambda: self.insert_text("n"))
        self.window.key_o.pressed.connect(lambda: self.insert_text("o"))
        self.window.key_p.pressed.connect(lambda: self.insert_text("p"))
        self.window.key_q.pressed.connect(lambda: self.insert_text("q"))
        self.window.key_r.pressed.connect(lambda: self.insert_text("r"))
        self.window.key_s.pressed.connect(lambda: self.insert_text("s"))
        self.window.key_t.pressed.connect(lambda: self.insert_text("t"))
        self.window.key_u.pressed.connect(lambda: self.insert_text("u"))
        self.window.key_v.pressed.connect(lambda: self.insert_text("v"))
        self.window.key_w.pressed.connect(lambda: self.insert_text("w"))
        self.window.key_x.pressed.connect(lambda: self.insert_text("x"))
        self.window.key_y.pressed.connect(lambda: self.insert_text("y"))
        self.window.key_z.pressed.connect(lambda: self.insert_text("z"))
        self.window.key_comma.pressed.connect(lambda: self.insert_text(","))
        self.window.key_dot.pressed.connect(lambda: self.insert_text("."))
        self.window.key_space.pressed.connect(lambda: self.insert_text(" "))
        self.window.key_backspace.pressed.connect(self.backspace)

        
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
        if obj == self.ai_input_viewport:
            if event.type() == QEvent.Type.MouseButtonPress:
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