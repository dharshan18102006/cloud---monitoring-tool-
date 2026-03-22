import pickle
import json
import random
import os

class ChatbotEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, 'intent_model.pkl')
        intents_path = os.path.join(base_dir, 'intents.json')
        
        # Auto-train if model doesn't exist
        if not os.path.exists(model_path):
            from .train import train_model
            train_model()
            
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
            
        with open(intents_path, 'r') as f:
            self.intents = json.load(f)['intents']
            
        self.intent_dict = {intent['tag']: intent for intent in self.intents}

    def predict_intent(self, text):
        if not text or not text.strip():
            return 'fallback'
        tag = self.model.predict([text.lower()])[0]
        return tag

    def generate_response(self, text, system_stats):
        """
        system_stats expected: {'cpu': 45, 'memory': 60, 'disk': 75, 'top_process': 'chrome.exe', 'warning_count': 0}
        """
        tag = self.predict_intent(text)
        intent = self.intent_dict.get(tag, self.intent_dict['fallback'])
        response_template = random.choice(intent['responses'])
        
        try:
            return response_template.format(**system_stats)
        except KeyError:
            return response_template
