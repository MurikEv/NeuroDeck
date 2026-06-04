from services.network_service import is_online

class AiService:
    def local_ai(self, prompt):
        return "local", prompt

    def api_ai(self, prompt):
        return "api", prompt

    def ask_ai(self, prompt):
        if is_online():
            return self.api_ai(prompt)
        else:
            return self.local_ai(prompt)