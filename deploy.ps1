# =============================================================================
# Windows Production Deployment Script - System Monitor Stack
# =============================================================================
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting System Monitoring Tool deployment..." -ForegroundColor Cyan

# Check Docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: Docker is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Building and starting all containers..." -ForegroundColor Yellow
docker compose down --remove-orphans 2>$null
docker compose up -d --build

Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "📋 Service status:" -ForegroundColor Cyan
docker compose ps

Write-Host "=================================================================" -ForegroundColor Green
Write-Host "✅ Deployment Successful!" -ForegroundColor Green
Write-Host "🌐 Frontend Dashboard: http://localhost (Port 80)" -ForegroundColor White
Write-Host "🔌 Backend API:        http://localhost:5000" -ForegroundColor White
Write-Host "📊 Grafana:            http://localhost:3000 (admin / admin)" -ForegroundColor White
Write-Host "📈 Prometheus:         http://localhost:9090" -ForegroundColor White
Write-Host "🗄️ MongoDB:            http://localhost:27017" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Green
