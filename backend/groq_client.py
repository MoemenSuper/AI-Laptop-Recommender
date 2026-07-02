import requests

from .ai_training_system import LAPTOP_EXPERT_SYSTEM_PROMPT


class GroqClient:
    def __init__(self, api_key, base_url, model="llama3-70b-8192"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @property
    def configured(self):
        return bool(self.api_key)

    def complete_prompt(self, prompt, use_expert_prompt=True):
        system_prompt = (
            LAPTOP_EXPERT_SYSTEM_PROMPT
            if use_expert_prompt
            else "You are a helpful laptop consultant."
        )
        return self.complete_messages([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ])

    def complete_messages(self, messages):
        if not self.configured:
            return None

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
                timeout=15,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()

            print(f"Groq API error {response.status_code}: {response.text}")
            return None
        except Exception as error:
            print(f"Groq API error: {error}")
            return None
