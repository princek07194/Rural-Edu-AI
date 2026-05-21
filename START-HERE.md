# Quick Start (Windows)

## Easiest — double-click
**`RUN-PROJECT.bat`** — starts backend + frontend automatically

---

## Manual commands

### Frontend (React) — must be in `frontend` OR use root scripts:

```powershell
# Option A — from project root (recommended)
cd "E:\PROJECTS\Regional digital education rural"
npm install
npm run dev
```

```powershell
# Option B — from frontend folder
cd "E:\PROJECTS\Regional digital education rural\frontend"
npm install
npm run dev
```

Open: **http://localhost:5173**

### Backend (Flask) — separate terminal:

```powershell
cd "E:\PROJECTS\Regional digital education rural\backend"
pip install -r requirements.txt
python run.py
```

Backend: **http://localhost:5000**

---

## Common error

| Error | Fix |
|-------|-----|
| `Could not read package.json` in root | Run `npm install` then `npm run dev` from root, OR `cd frontend` first |
| Registration / server error | Start backend first: `cd backend` → `python run.py` |
| Process failed | Use manual transcript paste on Process Video page |
