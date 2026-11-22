# 💻 PulsePipe V2 — CLI & Development Handbook

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Local Development Quickstart

### Prerequisites
- Python 3.10+ (Tested on Python 3.14.0)
- Node.js 18+ & npm
- .NET 8.0 SDK (Optional for gateway build)

### Step 1: Environment Setup
```powershell
cd "C:\Vijay-Projects\PulsePipe - V2"
copy .env.example .env
```

### Step 2: Install Python Dependencies & Run Test Suite
```powershell
pip install -r services/api/requirements.txt
python -m pytest tests/ -v
```

### Step 3: Run the Automated Release Evals Gate
```powershell
python -m evals.run_evals
```

### Step 4: Install & Build Frontend
```powershell
npm --prefix "frontend" install
npm --prefix "frontend" run build
```

---

## 2. Launching Services

### Start FastAPI Application Core (Port 8093)
```powershell
python -m uvicorn services.api.app.main:app --host 0.0.0.0 --port 8093 --reload
```

### Start Vite Frontend Dev Server (Port 5175)
```powershell
npm --prefix "frontend" run dev
```

### Verify Endpoints
- **Frontend Workstation:** http://localhost:5175/
- **Interactive Swagger Docs:** http://localhost:8093/docs
- **Health Check Probe:** http://localhost:8093/healthz
