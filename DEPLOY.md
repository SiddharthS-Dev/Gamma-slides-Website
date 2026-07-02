# SlideVault — Deployment Guide

## Phase 1 — Cloudflare Tunnel (Zero Cost, This Week)

Get the whole org online in ~2 hours using your existing Windows machine.

### 1. Build the frontend
```powershell
cd frontend
npm run build        # produces frontend/dist/
```

### 2. Start the backend (serves built frontend + API from one port)
```powershell
cd backend
venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The built `frontend/dist/` is automatically served at `/` by the backend.

### 3. Install cloudflared and expose
```powershell
# Option A: Install via winget
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000

# Option B: Direct download via PowerShell (if winget is unavailable)
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
.\cloudflared.exe tunnel --url http://localhost:8000
```
This prints a `*.trycloudflare.com` URL — share it with your team immediately.

### 4. Make it permanent (optional)
```powershell
# Option A: Install via winget
winget install NSSM.NSSM
# Register uvicorn as a Windows service
nssm install SlideVaultAPI "D:\Gamma Slides\slidevault\backend\venv\Scripts\uvicorn.exe"
nssm set SlideVaultAPI AppParameters "app.main:app --host 0.0.0.0 --port 8000"
nssm set SlideVaultAPI AppDirectory "D:\Gamma Slides\slidevault\backend"
nssm start SlideVaultAPI

# Option B: Direct download via PowerShell (if winget is unavailable)
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "nssm.zip"
Expand-Archive -Path "nssm.zip" -DestinationPath "nssm-extracted"
# Move to the extracted directory containing nssm.exe:
cd nssm-extracted/nssm-2.24/win64/
.\nssm.exe install SlideVaultAPI "D:\Gamma Slides\slidevault\backend\venv\Scripts\uvicorn.exe"
.\nssm.exe set SlideVaultAPI AppParameters "app.main:app --host 0.0.0.0 --port 8000"
.\nssm.exe set SlideVaultAPI AppDirectory "D:\Gamma Slides\slidevault\backend"
.\nssm.exe start SlideVaultAPI

# Register cloudflared as a Windows service
# (For Option A, run 'cloudflared service install'. For Option B, run '.\cloudflared.exe service install')
```

---

## Phase 2 — Hetzner VPS + Docker Compose (Recommended)

### Prerequisites
- Hetzner account → provision CX22 (Ubuntu 22.04, €3.79/mo)
- Domain pointing to server IP via Cloudflare (free tier, proxy enabled)
- Docker + Docker Compose installed on server

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env: set DB_PASSWORD and DOMAIN
```

### 2. Upload presentation files
```powershell
# From your Windows machine (requires rsync via Git Bash or WSL):
rsync -avz --progress "D:/Gamma Slides/PPT/" user@YOUR_VPS_IP:/opt/slidevault/presentations/
```
Or use [WinSCP](https://winscp.net) with SFTP.

### 3. Initialize the Docker volume
```bash
# On VPS — copy files from host into Docker volume
docker run --rm -v slidevault_presentations:/data -v /opt/slidevault/presentations:/src alpine \
  sh -c "cp -r /src/* /data/"
```

### 4. Launch
```bash
docker compose up -d
docker compose logs -f   # watch startup
```

The app will be live at `https://your-domain.com` within ~2 minutes (Caddy provisions SSL automatically).

### 5. Set up automatic file sync (run on your Windows machine)
Create a Windows Task Scheduler task to run nightly:
```powershell
# sync_presentations.ps1
rsync -avz --update "D:/Gamma Slides/PPT/" user@YOUR_VPS_IP:/opt/slidevault/presentations/
# The backend file watcher detects new files automatically
```

---

## Phase 3 — Azure (Long-term, 500+ users)

See the full architecture plan at `.claude/plans/typed-humming-swing.md` for the Azure setup with:
- Azure App Service (FastAPI)
- Azure Blob Storage (presentations + thumbnails)
- Azure CDN (edge caching)
- Azure Database for PostgreSQL Flexible
- GitHub Actions CI/CD

Estimated cost: ~$28/month

---

## Verification Checklist

```bash
# Backend health
curl https://your-domain.com/health

# API working
curl https://your-domain.com/api/v1/presentations | python -m json.tool

# File serving with byte-range support (PDF seeking)
curl -I https://your-domain.com/files/sample.pdf
# → Should include: Accept-Ranges: bytes

# Sync version endpoint
curl https://your-domain.com/api/v1/search/sync/version

# PWA installable
# Open Chrome → address bar → Install icon should appear
```

---

## Category Consolidation (Run Once)

If you have an existing database with 65+ categories, consolidate to 6:
```powershell
cd backend
venv\Scripts\python.exe scripts\consolidate_categories.py
```

---

## Files Created by This Deployment Setup

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all services |
| `Caddyfile` | Reverse proxy + auto-HTTPS |
| `backend/Dockerfile` | API container |
| `backend/requirements.txt` | Python dependencies (no Windows-only packages) |
| `frontend/Dockerfile` | Multi-stage React build |
| `frontend/nginx.conf` | SPA serving config |
| `frontend/public/manifest.json` | PWA manifest |
| `frontend/public/sw.js` | Service Worker (offline support) |
| `.env.example` | Environment variable template |
| `backend/scripts/consolidate_categories.py` | DB migration: 65→6 categories |
