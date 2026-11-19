# V1 architecture and implementation status

The public notebook is a static Next.js export served on Vercel. Its page assembles the public writing from `apps/public-web/src/lib/writing.ts`. Treat this file as published content. [Live notebook](https://somewhere-to-put-it.vercel.app/).

The footer prompt can open a vault URL sealed at build time. Anyone who already knows the URL can go directly to the vault. The vault authenticates each session and the API checks access to each entry.

The private deployment template routes requests through Caddy. It sends vault pages to Next.js and same-origin `/api/*` requests to FastAPI, which uses SQLAlchemy to access the database. The local HTTP demo uses a Next.js rewrite for the API. Live hosting for this private stack remains unverified.

The local demo uses SQLite to avoid requiring Docker for a local trial.
SQLAlchemy models and Alembic migrations support PostgreSQL, with a dedicated CI
integration job. npm workspaces and package-lock.json
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

Account enrollment and factor replacement are local operator commands. TOTP
secrets use authenticated encryption bound to account IDs. Recovery codes contain
128 random bits, are stored as account-bound hashes, and are consumed atomically.
Recovery sign-in revokes other sessions; factor replacement also invalidates every
old recovery code. Secure mode requires PostgreSQL, HTTPS and an external encryption
key and refuses demo accounts. See [account setup](account-setup.md).

## Next milestones

1. Add private image storage with validated uploads and authorized downloads.
2. Implement encrypted exports, integrity manifests and an isolated restore drill.
3. Validate the private stack on its intended host before adding real archive records. CI exercises Caddy, HTTPS and PostgreSQL. Public DNS, certificate renewal and firewall restrictions require host-specific checks. See [deployment hardening](deployment-hardening.md).

4. Owner-only 90-day keepalive and a resumable lifecycle state machine. Disable
   access only after verified restore; permanent deletion remains simulated.
5. First isolated IDOR lab, documentation and regression test. Chat links later.

Inactivity means no owner login/keepalive, not no reader activity. Recheck that
condition before lifecycle transitions. “Delete public archive” in the original
README means retiring the online private vault; the public website survives.

No lab implementation is imported by the application. Future production image
builds must exclude lab files and fixtures. No vulnerable production-mode switch.
