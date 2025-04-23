import os
import json
import requests

class ChatBotAPI:
    """
    A utility class for interacting with the OpenRouter API to provide general assistance.
    """

    def __init__(self):
        self.api_key = "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"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.0-flash-exp:free"

    def get_response(self, query):
        """
        Gets a response for any user query (no academic-only restriction).
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful, friendly, and knowledgeable AI assistant ready to answer any kind of question."},
                {"role": "user", "content": query}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response_data = response.json()

            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            return "I'm having trouble generating a response. Please try again later."
        except Exception as e:
            print(f"Error getting response: {e}")
            return "I'm experiencing technical difficulties. Please try again later."