# 🚀 Deployment Guide

## Option 1: Local Machine (RTX 4090)

### Requirements
- Ubuntu 22.04+ / Debian 12+
- NVIDIA Driver 535+
- CUDA 12.4
- Python 3.10+
- ffmpeg
- 50GB+ free disk space (for model weights)

### Steps

```bash
# 1. Clone
git clone https://github.com/yourname/fitstream.git
cd fitstream

# 2. Setup
bash scripts/setup.sh

# 3. Download model
python scripts/download_models.py --model vace-1.3b

# 4. Test
PYTHONPATH=. python scripts/demo.py
PYTHONPATH=. python -m pytest tests/ -v

# 5. Run
PYTHONPATH=. python -m fitstream.api.server
```

Access at `http://localhost:8000/app`

---

## Option 2: Docker

### Requirements
- Docker 24+
- NVIDIA Container Toolkit (`nvidia-docker`)
- NVIDIA GPU with 16GB+ VRAM

### Steps

```bash
# 1. Clone
git clone https://github.com/yourname/fitstream.git
cd fitstream

# 2. Download model (before Docker build — mounted as volume)
pip install huggingface-hub
huggingface-cli download Wan-AI/Wan2.1-VACE-1.3B-Preview \
    --local-dir ./models/VACE-Wan2.1-1.3B-Preview

# 3. Build and run
docker compose up --build -d

# 4. Check logs
docker compose logs -f fitstream

# 5. Access
open http://localhost:8000/app
```

### Docker Compose Configuration

The `docker-compose.yml` mounts these volumes:
- `./models` → Persists model weights across restarts
- `./outputs` → Generated videos
- `./uploads` → User-uploaded images
- `./jobs` → Job persistence (survives restarts)
- `./frontend` → Live-editable frontend (read-only mount)

---

## Option 3: Cloud GPU (RunPod / Lambda Labs / Vast.ai)

### RunPod

1. Create a pod with:
   - GPU: RTX 4090 or A100
   - Image: `nvidia/cuda:12.4.1-devel-ubuntu22.04`
   - Disk: 100GB+
   - Expose port: 8000

2. SSH into the pod and run:
```bash
git clone https://github.com/yourname/fitstream.git
cd fitstream
bash scripts/setup.sh
python scripts/download_models.py --model vace-1.3b
PYTHONPATH=. python -m fitstream.api.server
```

3. Access via the RunPod proxy URL.

### Lambda Labs

Same steps as RunPod but use Lambda's GPU instance dashboard.

---

## Production Considerations

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name fitstream.yourdomain.com;

    client_max_body_size 50M;   # Allow large image uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";    # WebSocket support
        proxy_set_header Host $host;
        proxy_read_timeout 600s;                  # Long generation times
    }
}
```

### HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d fitstream.yourdomain.com
```

### Process Manager (systemd)

Create `/etc/systemd/system/fitstream.service`:
```ini
[Unit]
Description=FitStream AI Video Generation
After=network.target

[Service]
Type=simple
User=fitstream
WorkingDirectory=/opt/fitstream
Environment=PYTHONPATH=/opt/fitstream
ExecStart=/opt/fitstream/.venv/bin/python -m fitstream.api.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fitstream
sudo systemctl start fitstream
sudo systemctl status fitstream
```

### Monitoring

- Health check: `GET /health` (used by Docker healthcheck)
- GPU status: `GET /gpu`
- Job list: `GET /api/v1/jobs`

Set up external monitoring (e.g. UptimeRobot) to ping `/health` every minute.
