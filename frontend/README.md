# CyberRisk360 Frontend

React + TypeScript + Vite SPA consuming the CyberRisk360 API. This is the
first slice: **Auth, Dashboard, and Vulnerabilities** only. Assets, Risks,
Controls, Frameworks, Reports, Imports, Evidence, and Admin/Org management
are not implemented yet — see `../docs/ROADMAP.md` Phase 6.

## Prerequisites

- Node.js (LTS) and npm
- The backend running locally at `http://localhost:8000`, with:
  - Migrations applied and reference data seeded — from `backend/`, run
    `python scripts/bootstrap_database.py` (this also seeds the "default"
    organization that registration below relies on).
  - `CORS_ALLOWED_ORIGINS=http://localhost:5173` set in the repo-root
    `.env` — required for the browser to be allowed to call the API from
    the Vite dev server. **Restart the backend after changing this** — it's
    read once at process start, not per-request, and `--reload` doesn't
    re-read `.env`.

## Setup

```
npm install
npm run dev
```

Opens at `http://localhost:5173`.

## Configuration

Optional `.env.local` (gitignored) to point at a non-default backend:

```
VITE_API_BASE_URL=http://localhost:8000   # this is already the default
```

## Getting a test login

There's no seeded user out of the box. Register one against the public
endpoint (the backend must already be bootstrapped — see Prerequisites):

```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"tester","email":"tester@example.com","password":"changeme123","role":"analyst"}'
```

`org_slug` can be omitted — it defaults to the seeded `"default"` org. Use
`role: "analyst"` (or `admin`/`auditor`) to see the Vulnerabilities page;
any of the 7 org roles (`admin, analyst, pentester, grc_analyst, auditor,
manager, ciso`) can reach the Dashboard. `super_admin` is **not** a valid
self-registration role and cannot be created this way (see
`backend/scripts/bootstrap_super_admin.py`).

`POST /login` is rate-limited to 5 attempts/minute per IP by the backend.

## How auth works here

- Login POSTs form-encoded credentials to `/login` (not JSON — the backend
  expects `OAuth2PasswordRequestForm`) and gets back a JWT, good for 60
  minutes with **no refresh** — expect a hard re-login once it lapses.
- The token is kept in `sessionStorage` (cleared when the tab closes) and
  attached as `Authorization: Bearer <token>` on every API call.
- "Logout" is purely local — there's no server-side session to invalidate.
- Which nav links you see depends on your JWT's `role` claim, decoded
  client-side — not every authenticated role can see every page (e.g.
  Vulnerabilities requires `admin`/`analyst`/`auditor`; a role outside that
  set sees an in-app "Access denied" if it hits the URL directly).

## Available scripts

```
npm run dev            # start the dev server
npm run build           # type-check + production build
npm run lint             # eslint
npm run format           # prettier --write
npm run format:check    # prettier --check
```
