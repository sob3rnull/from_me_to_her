"""Account enrollment and factor replacement, invoked by the local admin CLI."""
import re
import secrets
from uuid import uuid4
import pyotp
from sqlalchemy import delete, select
from .models import AuditEvent, BrowserSession, RecoveryCode, User
from .security import digest, normalize, now, passwords


def recovery_digest(user_id, code):
    # Codes have 128 random bits; SHA-256 is appropriate for these lookup secrets.
    return digest(user_id + ":" + code.lower())


def replace_recovery_codes(db, user):
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    codes = [secrets.token_hex(16) for _ in range(8)]
    db.add_all([RecoveryCode(user_id=user.id, code_hash=recovery_digest(user.id, code)) for code in codes])
    return codes


def enroll(db, box, username, role, password, secret, confirmation):
    username = normalize(username)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", username) or username.startswith("demo-"):
        raise ValueError("Use a 3–64 character username; demo- is reserved")
    if role not in {"OWNER", "READER"} or not 15 <= len(password) <= 200:
        raise ValueError("Role must be OWNER/READER and password must contain 15–200 characters")
    if db.scalar(select(User.id).where((User.username == username) | (User.role == role))):
        raise ValueError("That username or role already exists; use a fresh database for non-demo accounts")
    if not pyotp.TOTP(secret).verify(confirmation):
        raise ValueError("Authenticator confirmation failed; no account created")
    user = User(id=str(uuid4()), username=username, role=role,
                password_hash=passwords.hash(password), totp_secret="", last_totp_step=now() // 30, is_demo=False)
    user.totp_secret = box.encrypt(secret, user.id)
    db.add(user)
    db.flush()
    codes = replace_recovery_codes(db, user)
    db.add(AuditEvent(id=str(uuid4()), actor_id=user.id, action="ACCOUNT_ENROLLED", created_at=now()))
    db.commit()
    return codes


def replace_factor(db, box, username, password, recovery_code, new_secret, confirmation):
    user = db.scalar(select(User).where(User.username == normalize(username)).with_for_update())
    if not user or not passwords.verify(password, user.password_hash):
        raise ValueError("Unable to replace authenticator")
    if not pyotp.TOTP(new_secret).verify(confirmation):
        raise ValueError("New authenticator confirmation failed")
    consumed = db.execute(delete(RecoveryCode).where(
        RecoveryCode.user_id == user.id, RecoveryCode.code_hash == recovery_digest(user.id, recovery_code)))
    if consumed.rowcount != 1:
        db.rollback()
        raise ValueError("Unable to replace authenticator")
    user.totp_secret = box.encrypt(new_secret, user.id)
    user.last_totp_step = now() // 30
    db.execute(delete(BrowserSession).where(BrowserSession.user_id == user.id))
    codes = replace_recovery_codes(db, user)
    db.add(AuditEvent(id=str(uuid4()), actor_id=user.id, action="AUTHENTICATOR_REPLACED", created_at=now()))
    db.commit()
    return codes
