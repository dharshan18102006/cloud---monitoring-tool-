#!/usr/bin/env bash
# =============================================================================
# Production Deployment Script - System Monitor Stack
# =============================================================================
set -e

echo "🚀 Starting System Monitoring Tool deployment..."

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker and Docker Compose."
    exit 1
fi

echo "📦 Building and starting all containers..."
docker compose down --remove-orphans || true
docker compose up -d --build

echo "⏳ Waiting for services to become healthy..."
sleep 5

echo "📋 Service status:"
docker compose ps

echo "================================================================="
echo "✅ Deployment Successful!"
echo "🌐 Frontend Dashboard: http://localhost (Port 80)"
echo "🔌 Backend API:        http://localhost:5000"
echo "📊 Grafana:            http://localhost:3000 (admin / admin)"
echo "📈 Prometheus:         http://localhost:9090"
echo "🗄️ MongoDB:            http://localhost:27017"
echo "================================================================="
