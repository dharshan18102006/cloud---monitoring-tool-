# System Monitor Web Application

A full-stack, real-time System Monitoring Dashboard with an integrated AI Chatbot and an Observability Stack.

## Features
- Real-Time dashboard displaying CPU, Memory, Disk, and Process stats.
- Kill processes directly from the UI.
- System warnings when thresholds are exceeded.
- AI Chatbot that answers questions about current system health using a custom ML NLP Model.
- Backend observability via Prometheus, Grafana, and Loki (Docker).

## Prerequisites
- Python 3.8+
- Docker & Docker Compose (for Observability Stack & MongoDB)

## Getting Started

### 1. Database & Observability Stack
Start the docker containers:
```bash
cd backend
docker-compose up -d
```
*Note: If Docker is unavailable, the application will still run smoothly utilizing local system APIs for the core dashboard features, but without Grafana dashboards.*

### 2. Backend Application
Create a virtual environment and install the requirements:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Start the Flask server:
```bash
python app.py
```
*The server will start on port 5000 and automatically train the chatbot model on first launch.*

### 3. Frontend Dashboard
Run a simple HTTP server to serve the static frontend files:
```bash
cd frontend
python -m http.server 8000
```
Navigate to [http://localhost:8000/login.html](http://localhost:8000/login.html) in your browser.
**Default Credentials:** `admin` / `password`
