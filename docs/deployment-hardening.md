# Deployment hardening and verification

The vault uses a fresh 256-bit CSP nonce per HTML response. Next's `src/proxy.ts`
replaces incoming CSP/nonce headers; the root layout waits for a request so Next
can apply the nonce to framework scripts. Production forbids unnonced inline
scripts, eval, frames, objects and external connections. Development permits eval,
inline styles and local WebSockets for Next's development tools only. There is no
change to API authorization: every protected API call still checks its session.
The public site remains a separate static export.

Caddy terminates TLS and routes `/api/*` directly to FastAPI. Other vault requests
go to Next. Keep both upstream listeners bound to loopback and allow Uvicorn to
trust forwarding headers only from `127.0.0.1`. This assumes Caddy and the API run
on the same trusted host; local processes can impersonate that proxy. Do not expose
the upstream ports or use a wildcard forwarding allow-list. No additional CDN or
proxy trust chain is configured. Caddy replaces untrusted forwarding headers.

## Encryption-key rotation

Use a maintenance window; this is an offline operation for the small V1. The
`--offline` flag records the operator's acknowledgement, not a process detector.
Row locks and one database transaction protect the rewrite, but they do not replace
stopping every writer. No keys belong in Git, command arguments, CI logs or chat.

1. Preserve the current key in your secret manager and take a private database
   snapshot. Keep the snapshot outside this repository. Stop the API and every
   other process or operator that can enroll accounts or replace factors.
2. Generate a new key with `python -m app.admin keygen` in a private terminal. Save
   it before proceeding. In the maintenance process, set `TOTP_ENCRYPTION_KEY` to
   the new key and `TOTP_PREVIOUS_ENCRYPTION_KEY` to the old key using your secret
   manager. Both keys are validated; writes use only the new primary.
3. From `apps/api`, using the installed project environment, run:

   ```powershell
   & ../../.venv/Scripts/python.exe -m app.admin rotate-secrets --offline
   & ../../.venv/Scripts/python.exe -m app.admin verify-secrets
   ```

   Rotation validates all existing secrets and account bindings, re-encrypts them,
   verifies every stored ciphertext using only the primary key, revokes all
   sessions (including unfinished gate progress), and records a content-free audit
   event. These changes commit together. Any read, write or verification failure
   rolls back the transaction. Passwords, recovery codes and TOTP replay counters
   are preserved. Re-running after success is safe but revokes sessions again.
4. Remove `TOTP_PREVIOUS_ENCRYPTION_KEY` from the runtime configuration. Verify
   again, then restart all application processes with the new primary key only.
   Confirm a fresh sign-in and verify an old session no longer works. A TOTP code
   consumed before rotation stays consumed; wait for the next code if necessary.
5. Retain the old key separately for any historical backups that still need it.
   Removing a runtime fallback does not mean old backups can be decrypted with
   the new key. Retire the old key only when the corresponding backups are retired.

If rotation fails before commit, the old database and sessions remain unchanged;
restore the old primary configuration before restarting. If the client disconnects
and commit status is uncertain, retain both keys, run `verify-secrets` with the new
primary and inspect the `TOTP_KEY_ROTATED` audit event before deciding. Never roll
back to an old-key-only runtime against a successfully rotated database. A snapshot
restore must use its matching key. Loss of both keys is not recoverable by this CLI.

## Reproduce verification

From the repository root, install the documented Python/npm dependencies first:

```powershell
& ./.venv/Scripts/python.exe -m pytest apps/api/tests -q
npm run build
npx playwright install chromium
& ./.venv/Scripts/python.exe tests/e2e/https_stack.py --download-caddy
npm run test:e2e
```

The HTTPS command downloads the pinned Caddy 2.11.7 AMD64 release and verifies its
published SHA512 checksum. Alternatively set `CADDY_BIN` to your installed Caddy
executable and omit the download option. The helper supports Windows/Linux AMD64.
It refuses occupied ports 3001, 8100, 8443 and 8444. Run it after the production
build and before starting any development server; Next dev rewrites build output.

The rehearsal imports `infrastructure/Caddyfile` with test-only global options:
loopback binding, a temporary local CA, disabled trust-store installation and
disabled HTTP redirects. Browser certificate errors are ignored only in this test
configuration. No certificate is installed on the machine and no public service
is provisioned. Child processes, private keys and temporary fixtures are removed
on exit. Screenshots contain fictional data only and live in ignored `test-results/`.

By default it uses a migrated SQLite fixture injected through the existing app
factory; this is not production database validation. With `TEST_POSTGRES_URL`, it
creates and removes its own random PostgreSQL schema and exercises the normal
secure-mode database configuration. CI supplies disposable PostgreSQL 17. Never
point this variable at a real archive database, even though schema names are random.

Coverage includes production CSP/hydration, fresh nonces, blocked injected inline
scripts, public static page, owner editing, shared reader access, unshare denial,
recovery-code replay denial, secure host-only cookies, no-store responses, CSRF and
origin rejection, rejected direct HTTP, unknown hosts and spoofed forwarding headers.
Backend tests also cover failed rotation after flush, transaction rollback, session
revocation and sign-in using only the new key.

## What remains before real archive use

The rehearsal proves the application/proxy path using fictional accounts. It does
not prove public DNS, ACME issuance/renewal, redirect behavior on ports 80/443, host
firewall isolation, service restarts, secret-manager access or operational recovery.
Validate those on the chosen host before exposing real accounts. Keep request
bodies, cookies and credentials out of logs; configure audit retention separately.

Private media and encrypted archive backup/restore are still separate milestones.
Do not store irreplaceable content or enable inactivity deletion until a restore
drill has succeeded. Permanent deletion remains simulated.

References: [Next.js CSP](https://nextjs.org/docs/app/guides/content-security-policy),
[Fernet rotation](https://cryptography.io/en/latest/fernet/),
[Caddy proxy headers](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#headers).
