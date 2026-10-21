# from_me_to_her

## Development status

The first local development slice is implemented: public page, staged reader
authentication, owner login, private drafts/shared entries, and promise editing.
Use fictional data only; production security, uploads, backups, lifecycle and lab
exercises remain future milestones.

- [Run locally and test](docs/local-development.md)
- [Architecture and remaining work](docs/architecture.md)
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

Public website ≠ private archive.

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
  ↓
90-day keepalive
  ↓
No login
  ↓
Backup/export
  ↓
Verify backup
  ↓
Delete public archive
  ↓
Private copy remains
  ↓
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
