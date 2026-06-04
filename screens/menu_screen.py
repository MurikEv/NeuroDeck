from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
import state

class MainMenu:
    def __init__(self, window):
        self.window = window
        self.selected_row = 0
        self.selected_col = 0

        self.cards = [
            [
                # ROW 1
                {
                    "button": window.ai_btn,
                    "highlight_frame": window.ai_btn_highlight_frame,
                    "light": window.ai_btn_highlight_light,
                    "bg": window.ai_btn_bg
                },
                {
                    "button": window.calculator_btn,
                    "highlight_frame": window.calculator_btn_highlight_frame,
                    "light": window.calculator_btn_highlight_light,
                    "bg": window.calculator_btn_bg
                }
            ],
            [
                #ROW 2
                {
                    "button": window.camera_btn,
                    "highlight_frame": window.camera_btn_highlight_frame,
                    "light": window.camera_btn_highlight_light,
                    "bg": window.camera_btn_bg
                },
                {
                    "button": window.browser_btn,
                    "highlight_frame": window.browser_btn_highlight_frame,
                    "light": window.browser_btn_highlight_light,
                    "bg": window.browser_btn_bg
                }
            ],
            [
                #ROW3 
                {
                    "button": window.notepad_btn,
                    "highlight_frame": window.notepad_btn_highlight_frame,
                    "light": window.notepad_btn_highlight_light,
                    "bg": window.notepad_btn_bg
                },
                {
                    "button": window.files_btn,
                    "highlight_frame": window.files_btn_highlight_frame,
                    "light": window.files_btn_highlight_light,
                    "bg": window.files_btn_bg
                }
            ],
            [
                #ROW 4
                {
                    "button": window.chat_btn,
                    "highlight_frame": window.chat_btn_highlight_frame,
                    "light": window.chat_btn_highlight_light,
                    "bg": window.chat_btn_bg
                },
                {
                    "button": window.settings_btn,
                    "highlight_frame": window.settings_btn_highlight_frame,
                    "light": window.settings_btn_highlight_light,
                    "bg": window.settings_btn_bg
                }
            ]

        ]

        for row in self.cards:
            for card in row:
                card["button"].setFocusPolicy(Qt.FocusPolicy.NoFocus)

        window.ai_btn.clicked.connect(lambda: state.ui_queue.put(("ai", None)))
        window.calculator_btn.clicked.connect(lambda: state.ui_queue.put(("calculator", None)))
        window.camera_btn.clicked.connect(lambda: state.ui_queue.put(("camera", None)))
        window.browser_btn.clicked.connect(lambda: state.ui_queue.put(("browser", None)))
        window.notepad_btn.clicked.connect(lambda: state.ui_queue.put(("notepad", None)))
        window.files_btn.clicked.connect(lambda: state.ui_queue.put(("fileexplorer", None)))
        window.chat_btn.clicked.connect(lambda: state.ui_queue.put(("messenger", None)))
        window.settings_btn.clicked.connect(lambda: state.ui_queue.put(("settings", None)))

        self.highlight()
        
    base_button_style = """
border: 2px solid #ff0000;
border-radius:5px;
background-color: transparent;"""
    base_highlight_frame_style = """
background-color: black;
border-top: 2px solid #f79ca3;
border-left: 2px solid #ff0017;
border-right: 2px solid #fa283b;
border-bottom: 2px solid #ff0017;
border-radius:10px;"""
    base_bg_style = "background-color: #02141d;"
    base_light_style = "background-color:red;"

    active_button_style = base_button_style.replace("border: 2px solid #ff0000", "border: 4px solid #ff3333")
    active_highlight_frame_style = base_highlight_frame_style.replace(
        "border-top: 2px solid #f79ca3", "border-top: 3px solid #ff3333").replace(
        "border-left: 2px solid #ff0017", "border-left: 3px solid #ff3333").replace(
        "border-right: 2px solid #fa283b", "border-right: 3px solid #ff3333").replace(
        "border-bottom: 2px solid #ff0017", "border-bottom: 3px solid #ff3333")
    active_light_style = base_light_style.replace("background-color:red", "background-color:#00f4ff")
    active_bg_style = base_bg_style.replace("background-color: #02141d",
                                            "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,stop:0 #02141d,stop:0.87 #02141d,stop:1 #00f4ff)")

    def highlight(self):
        for r, row in enumerate(self.cards):
            for c, card in enumerate(row):
                if r == self.selected_row and c == self.selected_col:
                    card["button"].setStyleSheet(self.active_button_style)
                    card["highlight_frame"].setStyleSheet(self.active_highlight_frame_style)
                    card["light"].setStyleSheet(self.active_light_style)
                    card["bg"].setStyleSheet(self.active_bg_style)
                else:
                    card["button"].setStyleSheet(self.base_button_style)
                    card["highlight_frame"].setStyleSheet(self.base_highlight_frame_style)
                    card["light"].setStyleSheet(self.base_light_style)
                    card["bg"].setStyleSheet(self.base_bg_style)

    def handle_key(self, event):
        key = event.key()
        if key == Qt.Key.Key_Right:
            self.selected_col = (self.selected_col + 1) % len(self.cards[self.selected_row])
        elif key == Qt.Key.Key_Left:
            self.selected_col = (self.selected_col - 1) % len(self.cards[self.selected_row])
        elif key == Qt.Key.Key_Down:
            self.selected_row = (self.selected_row + 1) % len(self.cards)
            self.selected_col = min(self.selected_col, len(self.cards[self.selected_row]) - 1)
        elif key == Qt.Key.Key_Up:
            self.selected_row = (self.selected_row - 1) % len(self.cards)
            self.selected_col = min(self.selected_col, len(self.cards[self.selected_row]) - 1)
        elif key == Qt.Key.Key_Return:
            self.cards[self.selected_row][self.selected_col]["button"].click()
        self.highlight()
