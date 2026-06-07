from services.network_service import is_online
from services.ai_service import AiService
from PyQt6.QtCore import QTimer,QObject
import state
import threading
import queue

class AiScreen(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.ai_service = AiService()

        self.ai_answer_queue = queue.Queue()

        self.ai_queue_timer = QTimer(self)
        self.ai_queue_timer.timeout.connect(self.check_ai_queue)
        self.ai_queue_timer.start(100)

        timer = QTimer(self)
        timer.timeout.connect(self.status_label)
        timer.start(1000)

        self.window.ai_send_btn.clicked.connect(self.send_message)
        self.window.ai_clear_btn.clicked.connect(self.clear_chat)

    def status_label(self):
        if is_online():
            self.window.ai_status_label.setText("Online")
        else:
            self.window.ai_status_label.setText("Offline")

    def user_input(self):
        state.ai_input_text = self.window.ai_input.toPlainText()

    def run_ai_request(self, prompt):
        answer = self.ai_service.ask_ai(prompt)        
        self.ai_answer_queue.put(answer)
    
    def check_ai_queue(self):
        if self.ai_answer_queue.empty():
            return

        answer = self.ai_answer_queue.get()

        self.window.ai_output.append(f"AI: {answer}\n")
        self.window.ai_send_btn.setEnabled(True)

    def send_message(self):
        prompt = self.window.ai_input.toPlainText().strip()

        self.window.ai_output.append(f"You: {prompt}\n")
        self.window.ai_input.clear()
        self.window.ai_status_label.setText("Thinking...")
        self.window.ai_send_btn.setEnabled(False)

        threading.Thread(target=self.run_ai_request, args=(prompt,), daemon=True).start()

    def clear_chat(self):
        self.window.ai_output.clear()
        self.ai_service.clear_memory()
    

