# V1 architecture and implementation status

Public site (static Next.js export) → link to vault (Next.js) → same-origin /api
proxy → FastAPI modular backend → database. Private object storage and the
scheduled backup/lifecycle process are the next infrastructure components.

This first slice uses SQLite to avoid requiring Docker for a local trial.
SQLAlchemy models and Alembic migrations are the path to PostgreSQL; production
database validation is still outstanding. npm workspaces and package-lock.json
keep the two frontend dependencies reproducible; no separate package manager is required.

## Data and permissions

There is one owner and one invited reader in this version. Entries are drafts by
default. Only the owner creates/edits/shares. Readers can list/read shared entries;
every detail lookup rechecks visibility. Promises extend entries and preserve all
five README statuses. Body text is stored as text and React escapes it on display.

Authentication uses server-side expiring pre-auth sessions. Gate weights/answers
stay in the database; only the current prompts are returned. Personal questions
are an experience layer. Gate 3 requires password + TOTP. Owner authentication
bypasses the experience gates but requires the same real credentials. Sessions
rotate at login, are stored by token hash, and are deleted on logout. Consumed TOTP
timesteps are updated atomically. Origin + session-bound CSRF checks protect writes.

Audit events contain action, actor ID, target ID, and timestamp; never bodies,
answers, passwords, OTPs, or tokens. Production needs retention and monitoring.

## Next milestones

1. Production identity provisioning, recovery, secret encryption, HTTPS, CSP,
   trusted-proxy configuration, PostgreSQL integration and migration checks.
2. Private image storage with validated uploads and authorized downloads.
3. Encrypted exports, manifests, integrity checks, and isolated restore tests.
4. Owner-only 90-day keepalive and a resumable lifecycle state machine. Disable
   access only after verified restore; permanent deletion remains simulated.
5. First isolated IDOR lab, documentation and regression test. Chat links later.

Inactivity means no owner login/keepalive, not no reader activity. Recheck that
condition before lifecycle transitions. “Delete public archive” in the original
README means retiring the online private vault; the public website survives.

No lab implementation is imported by the application. Future production image
builds must exclude lab files and fixtures. No vulnerable production-mode switch.
