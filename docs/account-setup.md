# Account setup and recovery

This milestone adds controlled enrollment, encrypted authenticator secrets,
single-use recovery codes, and HTTPS configuration guards. It is not a completed
production deployment: private media, verified backups, lifecycle and a live-host
security review are still outstanding. Continue using fictional data. CSP and an
isolated HTTPS rehearsal are described in [deployment hardening](deployment-hardening.md).

## Existing local demo

From `apps/api`, after installing the updated locked dependencies:

```powershell
& ../../.venv/Scripts/python.exe -m alembic upgrade head
& ../../.venv/Scripts/python.exe -m app.admin encrypt-secrets
```

This encrypts legacy secrets in place and revokes old sessions, preserving entries.
Rerunning it is safe. `private-data/totp.key` is generated only for demo mode and
ignored by Git. Do not delete or regenerate it; existing secrets require that key.
The command does not erase old plaintext from database journals or backups. Use a
fresh database for real accounts. All legacy accounts remain marked as demo.

## Create accounts on a fresh database

Run migrations first. There is no public signup endpoint. Run the following commands
in an interactive terminal on the trusted application host, from `apps/api`:

```powershell
& ../../.venv/Scripts/python.exe -m app.admin configure-gates
& ../../.venv/Scripts/python.exe -m app.admin enroll --username archive-owner --role OWNER
& ../../.venv/Scripts/python.exe -m app.admin enroll --username archive-reader --role READER
```

There is exactly one account per role. Passwords must be 15–200 characters. Passwords,
gate answers, OTPs and recovery codes are entered through hidden prompts, not command
arguments. A new authenticator URI is displayed privately and must be confirmed with
a current code before the account is created. Eight random recovery codes are shown
once; only their account-bound hashes are stored. Keep them in a password manager
or another private location outside the repository. Wait for the next TOTP code
after enrollment because the confirmation timestep is already consumed.

For this small V1, the operator controls enrollment. Deliver the reader's credentials
and authenticator setup privately; never send them in issues, commits or logs.

## Lost authenticator

At login choose **Use a recovery code**, then supply the password and one unused
recovery code. Readers must still complete both gates. A successful recovery login
consumes the code atomically and revokes the account's other sessions. It does not
replace the old authenticator: if it is lost or compromised, replace it promptly.

From a trusted interactive terminal:

```powershell
& ../../.venv/Scripts/python.exe -m app.admin replace-factor --username archive-owner
```

This requires the password, another unused recovery code, and confirmation of the
new authenticator. It replaces the TOTP secret, revokes all sessions, invalidates
all old recovery codes, and displays a fresh set once. Replace the username for
the reader. There is no email reset, password-recovery bypass, or recovery based
on personal questions. Losing both the password and recovery material requires
a separately designed administrative recovery process; do not improvise a bypass.

## HTTPS deployment preparation

For the API, set these runtime variables outside Git:

- `APP_MODE=secure`
- `DATABASE_URL=postgresql+psycopg://...` pointing to a fresh private PostgreSQL database
- `VAULT_ORIGIN=https://your-vault-host` with no trailing slash
- `TOTP_ENCRYPTION_KEY` containing a Fernet key generated with `python -m app.admin keygen`

Keep the key in a secret manager and retain a separate recovery copy. Secure mode
never generates a fallback key, refuses demo accounts or unreadable TOTP secrets
at startup, and rejects HTTP requests. A schema migration is required before startup.
The key must be the same for enrollment, the API and maintenance commands. Key
rotation uses an explicit maintenance command; do not replace the variable without
following the [rotation procedure](deployment-hardening.md#encryption-key-rotation).

Set `NEXT_PUBLIC_VAULT_URL` and `NEXT_PUBLIC_PUBLIC_SITE_URL` to the intended HTTPS
origins before building the frontends. These URLs are public and baked into builds.
Never put secrets in `NEXT_PUBLIC_*`. The public origin must differ from the vault.

`infrastructure/Caddyfile` is a deployment template. It sends `/api/*` directly
to the API and other vault requests to Next.js. Caddy owns public TLS; both backend
listeners stay bound to loopback. The API may trust forwarding headers **only from
that local proxy**:

```text
uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Never use `--forwarded-allow-ips '*'`, expose port 8000 publicly, or configure Caddy
to trust client-supplied forwarding headers. Demo mode continues using
`--no-proxy-headers`. The Caddy template is exercised by the isolated HTTPS test;
public DNS, certificate issuance/renewal and a real host firewall remain unverified.
Secure mode sets `__Host-vault_session` cookies with Secure, HttpOnly, SameSite=Strict
and no Domain attribute. It also enforces origin/CSRF checks and an allowed Host.

## Verification

Local pytest covers enrollment confirmation, ciphertext/account binding, invalid
keys, code reuse/concurrency, factor replacement, session revocation, HTTPS/cookie
guards and the original authorization tests. Browser tests cover normal login and
recovery-code sign-in/replay. CI provisions disposable PostgreSQL, applies migrations,
checks model consistency, and exercises permissions and concurrent recovery in a
random schema that is removed afterward. No test calls an external identity provider.
