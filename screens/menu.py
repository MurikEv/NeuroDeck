from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
import state

class MainMenu:
    def __init__(self, window):
        self.window = window
        self.selected_row = 0
        self.selected_col = 0

        self.buttons = [
            [window.ai_btn, window.calculator_btn],
            [window.camera_btn, window.browser_btn],
            [window.notepad_btn, window.fileexplorer_btn],
            [window.messenger_btn, window.settings_btn],
        ]

        for row in self.buttons:
            for btn in row:
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        window.ai_btn.clicked.connect(lambda: state.ui_queue.put(("ai", None)))
        window.calculator_btn.clicked.connect(lambda: state.ui_queue.put(("calculator", None)))
        window.camera_btn.clicked.connect(lambda: state.ui_queue.put(("camera", None)))
        window.browser_btn.clicked.connect(lambda: state.ui_queue.put(("browser", None)))
        window.notepad_btn.clicked.connect(lambda: state.ui_queue.put(("notepad", None)))
        window.fileexplorer_btn.clicked.connect(lambda: state.ui_queue.put(("fileexplorer", None)))
        window.messenger_btn.clicked.connect(lambda: state.ui_queue.put(("messenger", None)))
        window.settings_btn.clicked.connect(lambda: state.ui_queue.put(("settings", None)))

        window.keyPressEvent = self.on_key
        self.highlight()
        
    base_style = "background-color: transparent; color: cyan; border-style: outset; border-width: 2px; border-radius: 10px;"
    active_style = base_style.replace("background-color: transparent",
                                      "background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a4a4a, stop:1 #111111)").replace("border-width: 2px",
                                                                                                                                           "border-width: 3px")

    def highlight(self):
        for r, row in enumerate(self.buttons):
            for c, btn in enumerate(row):
                if r == self.selected_row and c == self.selected_col:
                    btn.setStyleSheet(self.active_style)
                else:
                    btn.setStyleSheet(self.base_style)

    def on_key(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Right:
            self.selected_col = (self.selected_col + 1) % len(self.buttons[self.selected_row])
        elif key == Qt.Key.Key_Left:
            self.selected_col = (self.selected_col - 1) % len(self.buttons[self.selected_row])
        elif key == Qt.Key.Key_Down:
            self.selected_row = (self.selected_row + 1) % len(self.buttons)
            self.selected_col = min(self.selected_col, len(self.buttons[self.selected_row]) - 1)
        elif key == Qt.Key.Key_Up:
            self.selected_row = (self.selected_row - 1) % len(self.buttons)
            self.selected_col = min(self.selected_col, len(self.buttons[self.selected_row]) - 1)
        elif key == Qt.Key.Key_Return:
            self.buttons[self.selected_row][self.selected_col].click()
        self.highlight()
