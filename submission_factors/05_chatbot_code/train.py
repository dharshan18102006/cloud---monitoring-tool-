import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

def train_model():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    intents_path = os.path.join(base_dir, 'intents.json')
    model_path = os.path.join(base_dir, 'intent_model.pkl')
    
    with open(intents_path, 'r') as f:
        data = json.load(f)

    texts = []
    labels = []
    
    for intent in data['intents']:
        for pattern in intent['patterns']:
            if pattern.strip():
                texts.append(pattern.lower())
                labels.append(intent['tag'])

    # Create ML pipeline
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
    model.fit(texts, labels)

    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model trained and saved to {model_path}")

if __name__ == '__main__':
    train_model()
