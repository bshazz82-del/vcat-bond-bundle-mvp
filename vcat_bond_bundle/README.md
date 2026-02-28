# VCAT Bond Bundle (MVP)

This repository contains:
- **Backend (FastAPI)**: `vcat_bond_bundle/` (the “engine”)
- **Frontend (Streamlit)**: `frontend/streamlit_app.py` (the “website”)

> This software is **not legal advice**. It is limited to tenant-initiated bond recovery under s 419A.

## Run locally

### 1) Install Python 3.11+
### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Start backend (FastAPI)
```bash
uvicorn vcat_bond_bundle.app.main:app --reload --host 127.0.0.1 --port 8000
```
Check it here:
- http://127.0.0.1:8000/docs

### 4) Start website (Streamlit)
Open a second terminal:
```bash
# Windows (PowerShell):
$env:VCAT_BOND_BUNDLE_API_BASE="http://127.0.0.1:8000"
streamlit run frontend/streamlit_app.py

# macOS/Linux:
export VCAT_BOND_BUNDLE_API_BASE="http://127.0.0.1:8000"
streamlit run frontend/streamlit_app.py
```

## Deploy (recommended)

### Backend on Render
Build command:
- `pip install -r requirements.txt`

Start command:
- `uvicorn vcat_bond_bundle.app.main:app --host 0.0.0.0 --port $PORT`

Test:
- `https://YOUR-RENDER-URL/docs`

### Frontend on Streamlit Cloud
Main file path:
- `frontend/streamlit_app.py`

Secrets / Env var:
- `VCAT_BOND_BUNDLE_API_BASE = https://YOUR-RENDER-URL`

## Notes
- For MVP, files are stored in `data/` on the server.
- Stripe is stubbed if keys are not provided.
