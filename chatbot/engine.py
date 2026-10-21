import json
import random
import os


class ChatbotEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        intents_path = os.path.join(base_dir, 'intents.json')

        with open(intents_path, 'r') as f:
            self.intents = json.load(f)['intents']

        self.intent_dict = {intent['tag']: intent for intent in self.intents}

        # Train model in-memory — avoids pickle/numpy version mismatch on serverless (Vercel)
        self.model = self._train()

    def _train(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline

        texts, labels = [], []
        for intent in self.intents:
            for pattern in intent['patterns']:
                if pattern.strip():
                    texts.append(pattern.lower())
                    labels.append(intent['tag'])

        model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
        model.fit(texts, labels)
        return model

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
