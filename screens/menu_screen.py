"""Main-menu routes and touch/developer selection; visual code is separate."""

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QWidget

from screens.menu_widgets import MenuCanvas, MenuCard
from services.menu_status import read_menu_status
import state


# Row-major ordering is shared with the optional developer keyboard.
MENU_ITEMS = (
    (("ai_btn", "AI", "ai", "ai"),
     ("calculator_btn", "CALCULATOR", "calculator", "calculator")),
    (("camera_btn", "CAMERA", "camera", "camera"),
     ("browser_btn", "BROWSER", "browser", "browser")),
    (("notepad_btn", "NOTEPAD", "notepad", "notepad"),
     ("files_btn", "FILE EXP", "files", "file_explorer")),
    (("chat_btn", "MESS", "messenger", "messenger"),
     ("settings_btn", "SETTINGS", "settings", "settings")),
)


class MenuController(QObject):
    base_button_style = "background: transparent; border: none;"
    active_button_style = "background: transparent; border: none; color: #b8faff;"

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        # Keep the stackedWidget page identity and all existing routes.
        # Designer's old card artwork is not drawn/interactive at runtime.
        for widget in window.menu_screen.findChildren(QWidget):
            widget.hide()
            widget.setObjectName("legacy_menu_" + widget.objectName())
        self.canvas = MenuCanvas(window.menu_screen)
        self.cards = []
        for row_index, row in enumerate(MENU_ITEMS):
            cards = []
            for column, (name, title, icon, action) in enumerate(row):
                button = MenuCard(title, icon, self.canvas)
                button.setObjectName(name)
                button.setGeometry(26 if column == 0 else 329, 34 + row_index * 62, 126, 59)
                button.pressed.connect(self.highlight)
                button.released.connect(self.highlight)
                button.clicked.connect(lambda _checked=False, action=action: state.ui_queue.put((action, None)))
                setattr(window, name, button)
                cards.append({"button": button})
            self.cards.append(cards)
        window.menu_canvas = self.canvas
        self.highlight()
        self.refresh_status()
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start()
        self.canvas.show()
        self.canvas.raise_()

    def refresh_status(self):
        self.canvas.set_status(read_menu_status())

    def highlight(self, selected_button=None):
        pressed = next((card["button"] for row in self.cards for card in row if card["button"].isDown()), None)
        active_button = pressed or selected_button
        for row in self.cards:
            for card in row:
                button = card["button"]
                active = button is active_button
                button.set_selected(active)
                style = self.active_button_style if active else self.base_button_style
                if button.styleSheet() != style:
                    button.setStyleSheet(style)
