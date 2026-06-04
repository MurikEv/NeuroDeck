from services.ai_service import AiService
from PyQt6.QtCore import QTimer,QObject

class AiScreen(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.ai_service = AiService()

        timer = QTimer(self)
        timer.timeout.connect(self.status_label)
        timer.start(100)

    def status_label(self):
        if self.ai_service.is_online():
            self.window.ai_status_label.setText("Online")
        else:
            self.window.ai_status_label.setText("Offline")
