# from_me_to_her

## Project status Â· 19 November 2026

The public notebook is live on Vercel. It includes notes, dreams, fragments and unfinished writing, with page turns, section tabs and a theme switch. [Open the notebook](https://somewhere-to-put-it.vercel.app/).

The cover opens with a tap, and a progress line follows your place as you read. Keyboard arrows, section tabs and touch swipes navigate the pages. Reduced-motion mode turns pages immediately. On Vercel, the footer entrance is enabled only when an HTTPS vault destination is configured at build time.

The private vault is at the **working V1 demo** stage. The owner can edit drafts, share entries and track promises. The reader signs in through staged gates and sees shared entries. Enrollment, account recovery and an HTTPS rehearsal are implemented. Live private-vault hosting remains unverified.

The next archive milestone is **private image attachments**, followed by encrypted backup and a tested restore. Keep private archive content and credentials outside Git. The public notebook's writing ships to every visitor.

Reviewed `main` at `3368e67` (PR #12, notebook binding). The API, PostgreSQL and web checks passed for that revision. [GitHub Actions run](https://github.com/sob3rnull/from_me_to_her/actions/runs/44530130973)

- [Run locally and test](docs/local-development.md)
- [What to do next: step-by-step guide](docs/next-steps.md)
- [Architecture and remaining work](docs/architecture.md)
- [Account enrollment, recovery and HTTPS preparation](docs/account-setup.md)
- [CSP, key rotation and HTTPS verification](docs/deployment-hardening.md)
- [Security lab boundary](lab/README.md)

The original project brief is preserved below.

## Project Memory Dump

DO NOT FORGET THIS PROJECT.

This is a personal web/security project consisting of:

1. Public weird website
2. Private cloud-hosted archive
3. Staged authentication system
4. Security laboratory
5. Mobile/chat-based CMS
6. Archive lifecycle + backup system

---

## CORE IDEA

Public website â‰  private archive.

The GitHub project contains:
- application code
- fake/demo data
- security tests
- documentation

The actual archive lives separately in private cloud storage
and is NEVER committed to this repository.

---

## ARCHIVE CATEGORIES

- Letters
- Memories
- Promises
- Achievements I Wanted to Share
- Happy Moments
- Sad Moments
- Times I Missed You
- Vacations I Wish We Had Together
- I Really Want You Beside Me Right Now
- Life Updates
- Weird Dreams
- I Thought About You Again
- I Need To Move On

---

## PROMISES

Record promises made to her.

Each entry:
- Promise
- Date made
- Status
- Context
- Whether still intended
- Notes

Statuses:
- KEPT
- BROKEN
- PARTIALLY KEPT
- ONGOING
- UNCERTAIN

---

## AUTHENTICATION

Gate 1:
Weighted personalized questions.

FAIL:
Do not reveal Gate 2.

PASS:
Reveal Gate 2 server-side.

Gate 2:
- Anniversary
- His full name

Gate 3:
2FA

Only after all gates:
Private archive access.

---

## SECURITY LAB

Use the project to practice:

- IDOR
- XSS
- CSRF
- SQL injection
- Authentication bypass
- Authorization escalation
- Session attacks
- Rate-limit bypass
- File-upload attacks
- 2FA replay
- Lifecycle/kill-switch abuse
- Backup integrity

Every discovered vulnerability gets:
- identifier
- severity
- reproduction
- root cause
- fix
- regression test

---

## IMPORTANT STUPIDITY

zwe_vulnerability_1 = "myae"

Do not remove this because it is funny.

---

## ARCHIVE LIFECYCLE

ACTIVE
  â†“
90-day keepalive
  â†“
No login
  â†“
Backup/export
  â†“
Verify backup
  â†“
Delete public archive
  â†“
Private copy remains
  â†“
Website survives

NEVER delete the public archive before
the private backup has been successfully
verified.

---

## DEVELOPMENT ORDER

1. Evidence/data model
2. Public website
3. Authentication
4. Private archive API
5. Cloud storage
6. Security testing
7. Mobile CMS
8. Keepalive
9. Backup/deletion lifecycle
10. Documentation

---

## DO NOT BUILD THIS DURING FINALS

Seriously.

The README exists specifically so the
idea can survive until exams are over.

Go study.
