from services.network_service import is_online
from services.ai_service import AiService
from PyQt6.QtCore import QTimer,QObject
import state

class AiScreen(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.ai_service = AiService()

        timer = QTimer(self)
        timer.timeout.connect(self.status_label)
        timer.start(1000)

        self.window.ai_send_btn.clicked.connect(self.messages)
        self.window.ai_clear_btn.clicked.connect(self.clear_output)

    def status_label(self):
        if is_online():
            self.window.ai_status_label.setText("Online")
        else:
            self.window.ai_status_label.setText("Offline")

    def user_input(self):
        state.ai_input_text = self.window.ai_input.toPlainText()

    def messages(self):
        prompt = self.window.ai_input.toPlainText().strip()

        answer, message = self.ai_service.ask_ai(prompt)
        self.window.ai_output.append(f"You: {prompt}\n")
        self.window.ai_output.append(f"AI: {answer}\n")
        self.window.ai_input.clear()

    def clear_output(self):
        self.window.ai_output.clear()

