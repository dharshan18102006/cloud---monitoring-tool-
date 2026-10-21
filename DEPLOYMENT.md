# Deployment Guide - Cloud & System Monitoring Tool

This guide provides instructions for deploying the **Cloud Monitoring Tool & Observability Stack** in production environments.

---

## 🏗️ Architecture Overview

The production deployment consists of 6 microservices orchestrated via Docker Compose:

```
                      ┌────────────────────────────────────────┐
                      │              Web Client                │
                      └───────────────────┬────────────────────┘
                                          │ HTTP (Port 80)
                                          ▼
                      ┌────────────────────────────────────────┐
                      │            Frontend (Nginx)            │
                      │  - Static assets (HTML/CSS/JS)         │
                      │  - Reverse proxy /api & /socket.io     │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │             Backend (Flask)            │
                      │  - System Telemetry & Process Control  │
                      │  - ML Chatbot Engine (Scikit-Learn)    │
                      │  - Prometheus /api/metrics exporter    │
                      └───┬───────────────────┬──────────────┬─┘
                          │                   │              │
            Metrics Scrape│       Alerts / Log│       PromQL │
                          ▼                   ▼              ▼
                   ┌──────────────┐    ┌──────────────┐ ┌─────────────┐
                   │  Prometheus  │    │   MongoDB    │ │   Grafana   │
                   │ (Port 9090)  │    │ (Port 27017) │ │ (Port 3000) │
                   └──────┬───────┘    └──────────────┘ └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Loki Logs   │
                   │ (Port 3100)  │
                   └──────────────┘
```

---

## 🚀 Quick Deployment (Single Command)

### Prerequisites
- [Docker Engine & Docker Compose](https://docs.docker.com/get-docker/) installed.

### On Linux / macOS / Cloud VM:
```bash
chmod +x deploy.sh
./deploy.sh
```

### On Windows (PowerShell):
```powershell
.\deploy.ps1
```

### Or using Docker Compose directly:
```bash
docker compose up -d --build
```

---

## 🌐 Deployed Service Endpoints

| Service | Port | URL | Default Credentials |
| :--- | :--- | :--- | :--- |
| **Frontend Dashboard** | `80` | `http://<server-ip>/` | `admin` / `password` |
| **Backend REST API** | `5000` | `http://<server-ip>:5000/api/` | — |
| **Grafana Dashboards** | `3000` | `http://<server-ip>:3000/` | `admin` / `admin` |
| **Prometheus Exporter**| `9090` | `http://<server-ip>:9090/` | — |
| **Loki Log Engine** | `3100` | `http://<server-ip>:3100/` | — |
| **MongoDB Database** | `27017`| `mongodb://<server-ip>:27017/` | — |

---

## ☁️ Cloud VPS Deployment (AWS EC2 / DigitalOcean / Azure / GCP)

1. **Launch a Linux Instance** (Ubuntu 22.04 LTS or Debian recommended, min 2GB RAM).
2. **Open Security Group / Firewall Ports**:
   - `80` (Web UI)
   - `3000` (Grafana, optional)
   - `22` (SSH)
3. **Connect to your server and clone the repository**:
   ```bash
   git clone https://github.com/abishek003-tech/Cloud_Monitoring_tool.git
   cd Cloud_Monitoring_tool
   ```
4. **Run the deployment script**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
5. Access your dashboard at `http://<your-ec2-or-droplet-public-ip>/`.

---

## 🛠️ Management Commands

- **Check container status**:
  ```bash
  docker compose ps
  ```
- **View live backend logs**:
  ```bash
  docker compose logs -f backend
  ```
- **Restart stack**:
  ```bash
  docker compose restart
  ```
- **Stop stack**:
  ```bash
  docker compose down
  ```
