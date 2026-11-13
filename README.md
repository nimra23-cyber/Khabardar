# KHABARDAR

**Think Before You Trust.**

KHABARDAR is an AI-powered, multilingual (English / Urdu / Roman Urdu) personal scam & fraud
protection platform with a SOC-inspired threat intelligence experience. It detects scam messages,
malicious URLs, and fraudulent QR codes, with explainable results.

> **Local-only.** This is the Hackathon MVP (Scope A). It runs as a single-user local environment
> and **must never be exposed on a public or shared network** until the authentication and access
> controls (Req 18) are implemented. The backend binds to `127.0.0.1` only.

## Architecture

Modular monorepo:

```
khabardar/
  backend/     Python 3.11+ / FastAPI / Pydantic / SQLAlchemy / Alembic
  frontend/    React / TypeScript / Vite / Tailwind CSS / Recharts / Cytoscape.js
  .kiro/specs/ Approved requirements, design, and tasks (do not delete)
```

## Prerequisites (Windows 10 / 11)

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend runtime |
| Node.js | LTS (18+) | Frontend build |
| Tesseract OCR | latest | Phase 4 (OCR) — UB-Mannheim installer, `eng` + best-effort `urd` |
| zbar | latest | Phase 4 (QR) — via `pyzbar`; OpenCV fallback available |

Tesseract and zbar are only required for the Screenshot & QR module (Phase 4) and are documented in
`docs/WINDOWS_SETUP.md` when that phase lands.

## Quick start

See `docs/WINDOWS_SETUP.md` (added in a later task) for full detail. Summary:

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # fill OPTIONAL keys; the app runs fully without them
alembic upgrade head          # create the SQLite schema (added in Phase 2)

# IMPORTANT: --no-access-log disables Uvicorn's RAW access logger (which would
# record raw paths + query strings, possibly containing sensitive values).
# Sanitized access logging is provided by the application instead.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

> Do not remove `--no-access-log`. Uvicorn's built-in access logger records the
> raw request target (path parameters and query strings). The application emits
> a sanitized access log (method, route template, status, duration, request id)
> in its place. The `python -m app.main` dev runner applies this automatically.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Security & privacy principles

- No API keys in the frontend or source — backend `.env` only.
- Raw OTPs, passwords, tokens, and unnecessary PII are never persisted (masked/hashed).
- Scan history is privacy-preserving by default.
- URL analysis is SSRF-safe; suspicious URLs are never opened in a browser.
- No fabricated AI results, threat intelligence, or accuracy metrics — measured-only.

## Branding

The official Khabardar shield logo must be placed at `frontend/public/assets/logo.png`
(or `.svg`) exactly as supplied — not redesigned, recolored, or distorted. If the asset is
absent, the splash screen falls back to the name + tagline on a Deep Navy background.
