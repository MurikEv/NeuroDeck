from groq import Groq
from dotenv import load_dotenv
import os

class GroqService:
    def __init__(self):
        load_dotenv()

        self.chat_history = [
                {"role": "system", "content": "You are AI assistant. Answer clearly and shortly."}
            ]
        
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
        )

    def ask(self, prompt):
        self.chat_history.append({"role": "user", "content": prompt})
        self.chat_completion = self.client.chat.completions.create(
            messages=self.chat_history,
            model="llama-3.1-8b-instant",
        )

        answer = self.chat_completion.choices[0].message.content

        self.chat_history.append({"role": "assistant", "content": answer})

        return answer