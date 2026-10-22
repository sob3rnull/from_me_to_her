# Local development: first working slice

This milestone is for fictional local data only. It includes the public page,
owner/reader login, weighted reader gates, password + TOTP, entries, promises,
draft/share editing, database migrations, and security regression tests.

Account enrollment/recovery and encrypted TOTP storage are now implemented; see
[account setup](account-setup.md). Production deployment, uploads, backup/restore,
keepalive, deletion, chat and lab exercises remain unfinished. Do not put real
archive content into this development database.

## Setup (PowerShell, repository root)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps/api/requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e apps/api
npm.cmd ci
Set-Location apps/api
& ../../.venv/Scripts/python.exe -m alembic upgrade head
& ../../.venv/Scripts/python.exe -m app.demo seed
```

The seed refuses to overwrite an initialized database. Run it once. SQLite data
is created under `apps/api/private-data/`, ignored by Git. `.env.example` documents
settings; it is not loaded automatically. Set overrides with PowerShell `$env:NAME`.

## Run (three terminals)

API, from `apps/api`:

```powershell
& ../../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Public site, from repository root:

```powershell
npm.cmd run dev:public
```

Vault, from repository root:

```powershell
npm.cmd run dev:vault
```

Open public site at http://127.0.0.1:3000 and vault at http://localhost:3001.
Use the exact vault origin above; requests from other origins are rejected.

## Fictional accounts

| Field | Value |
|---|---|
| Owner username | `demo-owner` |
| Reader username | `demo-reader` |
| Password for both | `fictional-demo-only` |
| Demo TOTP secret | `JBSWY3DPEHPK3PXP` |
| Gate 1 | `saturn`, `tea` |
| Gate 2 | `2020-01-01`, `Alex Example` |

Get the current demo authenticator code, from `apps/api`:

```powershell
& ../../.venv/Scripts/python.exe -m app.demo code
```

A code is accepted once per account per 30-second timestep. If you log out and
immediately log in again, wait for the next code. This is intentional replay protection.

Owner flow: choose Owner → log in → create a draft → check Share with reader → save.
Reader flow: choose Reader → complete both gates → log in → see shared entries only.
The reader receives a 404 for draft IDs and cannot create or edit entries.

## Checks

From repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/api/tests -q
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Stop local development servers before E2E tests. The tests start their own servers
and use a fresh temporary database, never the local archive database.

## Development limits

- Cookies lack Secure only because this preview uses loopback HTTP. Production
  requires HTTPS, host-only Secure cookies, a configured trusted proxy and CSP.
- The fixed demo TOTP secret is public test data, now encrypted at rest.
  For existing demo databases, run `python -m app.admin encrypt-secrets` after migrating.
- Gates and logins are rate limited in the database. Behind the local Next proxy,
  clients share the backend's loopback address. Trusted proxy/IP handling is not built.
- The archive returns the latest 100 entries; pagination is a later addition.
- SQLite is tested locally. A separate GitHub Actions job runs real PostgreSQL
  migrations, permission checks and concurrent recovery-code consumption.
- No offline caching, localStorage archive persistence, public archive assets,
  cloud credentials, or deletion operation is included.
