# KHABARDAR — Public Demo Deployment

Simplest reliable split: **frontend on Vercel**, **backend on Render** (free
tier), **SQLite on a Render persistent disk** (single-instance, single-user
demo).

## Security limitations of this public demo (read first)

- **No authentication.** Req 18 (JWT/RBAC/lockout) is Scope B and NOT built.
  The deployed backend is an **unauthenticated public demo** with no access
  control. To avoid exposing a shared record store, public-demo mode
  (`KHABARDAR_PUBLIC_DEMO=true`) **disables scan-history persistence and the
  `/api/history` endpoint** — anonymous visitors can run detection but cannot
  create or read any shared history.
- **Do not submit real personal data / real secrets.** The demo is shared and
  unauthenticated; although detection masks OTPs/passwords/PII, nothing is
  persisted in demo mode anyway.
- The MVP's intended posture is **local-only** (bind `127.0.0.1`). Binding to
  `0.0.0.0` for the hosted demo is an explicit, documented deviation for demo
  purposes only.
- SQLite file lives on the backend host disk; it is not publicly served, and
  no DB file is committed.

## Backend (Render)

`backend/render.yaml` is a ready blueprint. Required steps:

1. Create a Render Web Service from the repo, root dir `backend/`.
2. Build: `pip install -r requirements.txt && alembic upgrade head`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Health check path: `/api/health`
5. Attach a 1GB persistent disk mounted at `/var/data`.
6. Environment variables:
   - `KHABARDAR_HOST=0.0.0.0`
   - `KHABARDAR_PUBLIC_DEMO=true`  **(required for public exposure)** — disables
     scan-history persistence and the `/api/history` endpoint so no shared,
     unauthenticated record store is created. Detection still works fully.
   - `KHABARDAR_DATABASE_URL=sqlite:////var/data/khabardar.db`
   - `KHABARDAR_CORS_ORIGINS=https://<your-vercel-app>.vercel.app` (exact origin,
     NO wildcard)
   - `KHABARDAR_HASH_SALT=<random 32+ char secret>` — generate with
     `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Leave all AI/threat-intel keys UNSET (app runs fully; reports "unavailable").

## Frontend (Vercel)

`frontend/vercel.json` is ready. Steps:

1. Import the repo into Vercel, root dir `frontend/`.
2. Framework: Vite. Build: `npm run build`. Output: `dist`.
3. Environment variable:
   - `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`
4. The SPA rewrite in `vercel.json` sends all paths to `index.html` so deep
   links (`/dashboard`, `/detector`) work with the browser router.

## Verification after deploy

1. `GET https://<backend>/api/health` → `{"ok":true,...,"local_only":false}`
2. Open the Vercel URL → splash → dashboard → Scam Detector.
3. Submit an OTP scam → expect HIGH RISK / SUSPICIOUS with signals + evidence +
   EN/Urdu explanation.
4. Submit a benign message → SAFE + explicit no-signal notice.
5. Submit empty input → handled error, no crash.
6. Check `/history` shows masked content only (no raw OTP/password).

## Manual actions required from the operator

- Create the Render and Vercel accounts / authorize the repo (requires your
  login — cannot be done headlessly here).
- Set the two `sync: false` secrets on Render (`KHABARDAR_CORS_ORIGINS`,
  `KHABARDAR_HASH_SALT`) and `VITE_API_BASE_URL` on Vercel.
