import hashlib
import secrets
import time
from pwdlib import PasswordHash

passwords = PasswordHash.recommended()


def now():
    return int(time.time())


def token():
    return secrets.token_urlsafe(32)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def normalize(value):
    return " ".join(value.strip().casefold().split())
