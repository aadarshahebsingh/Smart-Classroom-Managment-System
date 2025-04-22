import os
import json
import requests

class StudyBotAPI:
    """
    A utility class for interacting with the OpenRouter API to provide study assistance
    while filtering out non-academic content.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.0-flash-thinking-exp:free"
        
    def is_study_related(self, query):
        """
        Determines if a query is related to academic studies.
        """
        prompt = f"""
        Determine if the following query is related to academic studies, education, learning,
        school subjects, homework help, or educational questions. 
        
        Query: "{query}"
        
        Respond with only 'yes' if it is related to education or studies, or 'no' if it is not.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a filter that determines if content is related to academics."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response_data = response.json()
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                answer = response_data['choices'][0]['message']['content'].strip().lower()
                return 'yes' in answer
            return False
        except Exception as e:
            print(f"Error checking if query is study-related: {e}")
            return False
            
    def get_study_response(self, query):
        """
        Gets a response for a study-related query.
        """
        if not self.is_study_related(query):
            return "I'm only allowed to help with academic topics and study-related questions. Please ask me about your studies, homework, or educational topics."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": """You are StudyBot, an AI assistant dedicated to helping students with 
                 their academic studies. You provide clear, concise explanations for academic topics.
                 You only answer questions that are directly related to education, learning, or academic subjects.
                 You refuse to discuss any non-academic topics including but not limited to: personal advice, 
                 entertainment, sports, politics, or any content that would be inappropriate in an educational setting.
                 Your goal is to help students learn and understand academic concepts."""},
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
            print(f"Error getting study response: {e}")
            return "I'm experiencing technical difficulties. Please try again later."