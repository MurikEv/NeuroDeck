from services.network_service import is_online
from services.groq_service import GroqService

class AiService:
    def __init__(self):
        self.groq_service = GroqService()

    def local_ai(self):
        return "local"

    def ask_ai(self, prompt):
        if not prompt:
            return "Write something first."
        
        if is_online():
            return self.groq_service.ask(prompt)
        else:
            return self.local_ai(prompt)
    
    def clear_memory(self):
        self.groq_service.chat_history = [
                {"role": "system", "content": "You are AI assistant. Answer clearly and shortly."}
            ]