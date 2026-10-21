FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application files
COPY backend ./backend
COPY chatbot ./chatbot

EXPOSE 5000

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
