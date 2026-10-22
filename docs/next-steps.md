# What to do next

This guide starts from the existing Windows checkout and the hardening milestone
in commit `9360a79`. The immediate task is to try the working demo, check the
owner/reader behavior, and review the current PR. The next implementation milestone
is private image attachments, followed by verified backup/restore.

Use fictional content until backup/restore and live-host validation are complete.
The local application works; a public production service has not been deployed.

## 1. Open the right project

Open PowerShell and run:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_'
git status --short
git branch --show-current
git log -1 --oneline
```

The current branch is `feat/v1-foundation`. An empty `git status --short` means
the working tree is clean. The documentation commit will be newer than `9360a79`.

This machine already has Node 24, Python 3.12, `.venv`, the demo database and its
encryption-key file. You do not need to create another environment or seed again.
Docker is not required for the local demo.

On a second machine, clone the repository and check out `feat/v1-foundation` while
the PR is unmerged. Follow [local development](local-development.md) for first-time
dependency installation and seeding. Do not copy someone else's real secrets into
that checkout. If updating an existing clean checkout, use `git pull --ff-only`;
stop and inspect if Git reports local changes or divergence.

## 2. Prepare the existing demo database

Stop any running API process with Ctrl+C first. In PowerShell:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_\apps\api'
$env:APP_MODE = 'demo'
$env:VAULT_ORIGIN = 'http://localhost:3001'
$env:DATABASE_URL = 'sqlite:///./private-data/archive.db'

# This terminal is for the local demo: use its existing private key file.
Remove-Item Env:TOTP_ENCRYPTION_KEY -ErrorAction SilentlyContinue
Remove-Item Env:TOTP_PREVIOUS_ENCRYPTION_KEY -ErrorAction SilentlyContinue

& ../../.venv/Scripts/python.exe -m alembic upgrade head
& ../../.venv/Scripts/python.exe -m app.admin encrypt-secrets
& ../../.venv/Scripts/python.exe -m app.admin verify-secrets
```

Run each command separately and stop if it fails. Migrations should finish without
an exception. `Encrypted 0 legacy secrets` is normal after the previous setup.
Verification should report two accounts for the existing demo.

Do **not** run `app.demo seed` again on this initialized database. Its refusal to
overwrite accounts is intentional. Do not delete or regenerate
`apps/api/private-data/totp.key`: the existing encrypted demo secrets depend on it.
The environment removals above affect this terminal, not the file or saved keys.

The `.env.example` file documents settings; the Python application does not
automatically load it. PowerShell environment variables apply to that terminal
and processes started from it.

## 3. Run the application in three terminals

### Terminal A: API

Continue in the terminal from step 2:

```powershell
& ../../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Expected: Uvicorn reports that it is running on `http://127.0.0.1:8000`.
Leave this terminal running.

### Terminal B: public website

Open a new PowerShell terminal:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_'
npm.cmd run dev:public
```

Expected: Next reports that it is ready on port 3000. Leave it running.

### Terminal C: private vault

Open another PowerShell terminal:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_'
$env:VAULT_API_URL = 'http://127.0.0.1:8000'
npm.cmd run dev:vault
```

Expected: Next reports that it is ready on port 3001. Leave it running.

Open these addresses:

- Public website: <http://127.0.0.1:3000>
- Private vault: <http://localhost:3001>
- API health: <http://127.0.0.1:8000/api/health>

Health should return `{"status":"ok","mode":"demo"}`. Use `localhost` for the
vault exactly as shown: origin checks distinguish it from `127.0.0.1`.

## 4. Sign in as the owner and create test entries

Open a fourth PowerShell terminal for commands while the servers keep running:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_\apps\api'
& ../../.venv/Scripts/python.exe -m app.demo code
```

This prints the current six-digit demo authenticator code. It is a public test
fixture, not a code generator for real accounts.

At the vault:

1. Click **Owner**.
2. Enter username `demo-owner`.
3. Enter password `fictional-demo-only`.
4. Enter the current code and click **Continue**.
5. Create a letter titled `Owner-only test`. Leave **Share with reader** unchecked.
6. Save it. Its card should say **Private draft**.
7. Create another letter titled `Shared test`. Check **Share with reader** and save.
8. Create a **Promises** entry and try its status, context, notes and still-intended
   fields. This checks the existing structured promise editor too.

A TOTP code is usable only once per account per 30-second step. If you sign out
and immediately sign back in, wait for the next code. Keep your computer clock
correct; do not remove replay protection to make a reused code work.

## 5. Check the reader's view separately

Use a private/incognito browser window so the owner and reader do not share cookies.
Open <http://localhost:3001> and use:

| Field | Fictional value |
|---|---|
| Gate 1: planet | `saturn` |
| Gate 1: drink | `tea` |
| Gate 2: anniversary | `2020-01-01` |
| Gate 2: full name | `Alex Example` |
| Username | `demo-reader` |
| Password | `fictional-demo-only` |
| Authenticator code | Generate the current code with `app.demo code` |

Verify all of these:

- `Shared test` is visible.
- `Owner-only test` is absent.
- The reader has no editor or **Save entry** button.
- Back in the owner's window, click **Edit entry** on `Shared test`, uncheck
  **Share with reader**, and save. Refresh the reader window: it should disappear.
- Refresh the owner window: both entries should still exist.

Unsharing blocks subsequent reads; it cannot erase content someone already saw
or copied. The current UI does not push a live removal into an already open page.

To check the mobile layout on your laptop, open browser developer tools, enable
device emulation, and choose a narrow phone-sized viewport. The editor should fit
without horizontal scrolling. Actual phone access is not configured: the servers
bind to your laptop's loopback interface. Keep that binding while using demo accounts.

## 6. Run the automated checks

Stop all three servers with Ctrl+C. Open a fresh PowerShell terminal at the project
root and run these commands **in this order**, one at a time:

```powershell
Set-Location 'C:\Users\Zwe Nyi Nyar\OneDrive\Documents\ChatGPT\summer_ptoject_'

& ./.venv/Scripts/python.exe -m pytest apps/api/tests -q
npm.cmd run build
npx.cmd playwright install chromium
& ./.venv/Scripts/python.exe tests/e2e/https_stack.py --download-caddy
npm.cmd run test:e2e
```

Expected results at this milestone:

| Check | Expected result |
|---|---|
| Python tests | 26 passed; PostgreSQL test skipped unless a test database is configured |
| Frontend builds | Public site builds statically; vault builds dynamically |
| HTTPS rehearsal | Two tests pass through Caddy and the production vault build |
| Demo browser tests | Two tests pass |

The HTTPS helper downloads a pinned, checksum-verified Caddy executable and uses
temporary fictional data and a temporary local certificate authority. It does not
deploy a website or install that authority into your machine's trust store. Locally
it uses SQLite; GitHub Actions supplies PostgreSQL for the real-database rehearsal.

The production HTTPS check must run before the development browser tests: Next dev
changes build output. If you run it later, run `npm.cmd run build` again first.
No need to run Docker on your laptop just to repeat the CI database check.

If dependencies are missing, run this from the repository root before retrying:

```powershell
& ./.venv/Scripts/python.exe -m pip install -r apps/api/requirements-dev.lock.txt
& ./.venv/Scripts/python.exe -m pip install --no-deps -e apps/api
npm.cmd ci
```

Create `.venv` with `python -m venv .venv` only on a fresh checkout where it does
not already exist. Stop development servers before reinstalling dependencies.

## 7. Review the current PR

Open [PR #1](https://github.com/sob3rnull/from_me_to_her/pull/1).

1. Review **Files changed**, especially the authentication code, tests and docs.
2. Confirm the checks are green for the latest code commit. The hardening commit
   `9360a79` passed the API, PostgreSQL and web jobs.
3. Complete the manual owner/reader checks above and note any behavior you dislike.
4. Keep the PR as a draft while you are still reviewing. When satisfied, use
   **Ready for review**, then the repository's merge option.

Merging is a repository decision; it does not deploy the application. There is no
requirement to merge before trying the existing branch. Do not delete a branch with
unmerged work. On this OneDrive checkout, Git's ignore rules also do not control
OneDrive synchronization: choose an appropriate private location for future real
data and key material instead of assuming `.gitignore` makes it local-only.

## 8. Build private image attachments next

This feature does not exist yet. There is no bucket setting or command that turns
it on. Keep the next change limited to attaching images to an existing entry.

The intended workflow is:

`Owner saves entry → uploads image → API validates and stores it privately → permitted viewer requests it through the API`

Implementation sequence:

1. Inspect the existing entry authorization in `apps/api/app/main.py` and models
   in `apps/api/app/models.py`. Reuse owner/reader checks and CSRF protection.
2. Add an attachment model and Alembic migration. Record the entry ID, opaque
   storage key, media type, size, dimensions, content hash and creation time.
3. Add image validation. Proposed initial limits: JPEG/PNG/WebP, 5 MiB per image,
   10 megapixels, and five images per entry. Reject SVG, HTML and malformed files;
   decode and re-encode accepted images and remove metadata.
4. Add private storage behind a small adapter. The demo can use ignored local
   storage; choose and verify a private cloud backend before claiming cloud support.
   Never save attachments under either frontend's `public/` directory.
5. Add owner-only upload/removal routes and authenticated download routes. Every
   download must recheck entry visibility. For this small V1, stream through the
   API so unsharing blocks new requests without waiting for a signed URL to expire.
6. Add a small upload control and gallery to the existing vault editor. Keep
   authorization in the API, not only in the UI.
7. Test unauthorized reads, reader uploads, draft visibility, unsharing, CSRF,
   malformed/oversized files and failed storage/database writes. Add one mobile
   browser flow from upload through reader viewing.

Finish line: the owner can attach an image, the reader can see it only while its
entry is shared, and failure cases do not expose files or leave visible broken
attachments. Video, audio, chat ingestion and image AI are outside this milestone.

You can give the coding agent this prompt:

> Implement private image attachments as the next bounded V1 milestone. Inspect
> the current architecture and repository instructions first. Preserve existing
> login, CSRF, owner/reader permissions and the public-site/private-archive boundary.
> Follow the image scope and acceptance criteria in docs/next-steps.md. Use only
> fictional fixtures. Add the smallest appropriate schema, API, storage and UI
> changes, test authorization and upload validation, run relevant browser/build
> checks, and report exactly what is verified and which cloud checks remain.
> Do not deploy, merge, introduce chat/lifecycle features or use real archive data.

## 9. Implement backup and restore before real content

This is also unfinished. Copying a database file is not the complete future
archive backup once attachments exist.

The next backup milestone should:

1. Export database content and attachment objects as a consistent snapshot.
2. Record schema/application version, IDs, counts and file hashes in a manifest.
3. Encrypt the export with a separate backup key kept outside Git and separately
   from the backup location. Preserve the TOTP encryption key required by that
   snapshot; rotating the runtime key does not rewrite historical backups.
4. Store a second copy away from the running application.
5. Restore into an isolated empty database/storage location, never over the live
   archive during a test.
6. Verify counts, hashes, entries, attachments, sign-in and owner/reader permissions.
7. Report missing files, corrupted archives and wrong keys clearly. Add scheduling
   only after a manual export-and-restore drill succeeds.

Finish line: a documented command restores a working archive from an encrypted
backup into an empty environment, and automated tests detect corrupted backups.
Do not enable permanent deletion or treat untested exports as recoverable backups.

## 10. Prepare hosting and real accounts after those milestones

The current deployment template assumes Caddy, FastAPI and the Next vault run on
one trusted host, with API/Next bound to loopback. The public site is a static
export. PostgreSQL and future object storage must remain private.

Before writing host-specific install commands, choose the host/OS, two public
origins, private database/storage location, secret storage and backup destination.
For example, `example.com` and `vault.example.com` illustrate separate origins;
they are placeholders, not domains already configured for this project. Do not
split the existing architecture across providers without explicitly planning the
new network and proxy boundaries.

The deployment sequence will be:

1. Prepare the host and restricted service accounts. Install pinned project
   dependencies, PostgreSQL connectivity and Caddy. Configure service supervision.
2. Create a fresh database for real accounts; never promote the demo database.
3. Supply runtime secrets privately: `APP_MODE=secure`, the PostgreSQL
   `DATABASE_URL`, the HTTPS `VAULT_ORIGIN`, and a newly generated
   `TOTP_ENCRYPTION_KEY`. Use the same key for API and operator commands.
4. Apply migrations, configure private gates and enroll the two real accounts.
5. Set `NEXT_PUBLIC_VAULT_URL` and `NEXT_PUBLIC_PUBLIC_SITE_URL` to the selected
   origins **before** building the frontends. These variables contain public URLs,
   never secrets.
6. Configure `PUBLIC_HOST`, `VAULT_HOST` and `PUBLIC_ROOT` for the Caddy template.
   Start the API/Next services on loopback, then Caddy on public HTTPS.
7. Verify DNS, public certificate issuance and renewal, HTTP-to-HTTPS redirects,
   firewall restrictions, service restart behavior and secure cookies on that host.
8. Repeat owner/reader, recovery, unshare and backup/restore checks before putting
   real archive content there.

For step 4, after the fresh database and secure environment are configured, the
existing Python commands are:

```text
python -m alembic upgrade head
python -m app.admin configure-gates
python -m app.admin enroll --username archive-owner --role OWNER
python -m app.admin enroll --username archive-reader --role READER
```

Run these from `apps/api` using the host's project virtual environment. Enrollment
prompts for a password, displays a private authenticator provisioning URI, asks
for a code from that authenticator, and shows eight recovery codes once. Store
the credentials and recovery material privately. Wait for the next TOTP step
before the first login. The current CLI displays a URI, not a ready-made QR image;
use an authenticator that supports provisioning URI import, or its manual TOTP
setup using the URI's secret in a trusted local workflow. Do not paste the URI
into an online QR generator.

Exactly one owner and one reader are supported. There is no public signup or email
password reset. See [account setup](account-setup.md) for factor replacement and
[deployment hardening](deployment-hardening.md) for encryption-key rotation.
Routine use does not require rotating a key now; perform rotation only through
the documented maintenance procedure when needed.

## 11. Leave lifecycle, labs and chat until the archive is recoverable

Once the archive and restore drill work:

- Implement owner-only keepalive and the 90-day inactivity state machine. Reader
  visits must not reset the timer. Recheck inactivity and restore evidence before
  disabling access; permanent deletion remains simulated.
- Add one isolated IDOR lab using fake accounts/data and a separate process,
  database and credentials. Keep it out of production builds.
- Add chat ingestion last. Start with owner-only draft creation; require review
  in the existing editor before sharing. The mobile editor already covers V1 entry
  creation, so chat is optional rather than a blocker.

## Troubleshooting the current workflow

| Actual symptom | What to check first |
|---|---|
| `npm.ps1 cannot be loaded` | Use `npm.cmd` and `npx.cmd` as shown; changing machine-wide execution policy is unnecessary. |
| Missing Python module | Use this checkout's `.venv/Scripts/python.exe`; install the locked requirements and editable API package. |
| Seed refuses to overwrite | Existing accounts are present. Skip seeding; do not delete the database to silence the error. |
| `Unable to decrypt authenticator secret` | Check the original demo key file and whether an environment variable is overriding it. Do not generate a replacement key. |
| Login fails immediately after logout | Wait for a new TOTP step, verify username/password and check the computer clock. |
| HTTP 429 | Stop repeated attempts. The current rate-limit window is 15 minutes; wait for it to expire. |
| `Invalid request origin` | Open `http://localhost:3001` and confirm `VAULT_ORIGIN` matches exactly. |
| Vault cannot reach API | Check terminal A and API health, then confirm `VAULT_API_URL` points to port 8000. |
| Port already in use | Stop the process you started in its terminal; do not kill unrelated processes blindly. |
| HTTPS helper cannot find production output | Stop dev servers, run `npm.cmd run build`, then retry the HTTPS helper. |
| Browser executable missing | Run `npx.cmd playwright install chromium`. |
| PostgreSQL test skipped locally | Expected without `TEST_POSTGRES_URL`; inspect the PostgreSQL CI job for database coverage. |
| Next changes `next-env.d.ts` | Inspect `git diff` first. Dev/build can regenerate type paths; do not discard unrelated changes. |

If another error appears, capture the exact command and relevant terminal output.
Fix that failing step before running the next one. Redact credentials, tokens,
authenticator URIs and private content before sharing logs.
