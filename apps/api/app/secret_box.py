import json
import os
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

PREFIX = "fernet:v1:"


class SecretBox:
    def __init__(self, key, previous_key=None):
        try:
            self.fernet = Fernet(key)
            self.reader = MultiFernet([self.fernet, Fernet(previous_key)] if previous_key else [self.fernet])
        except (ValueError, TypeError) as error:
            raise ValueError("Invalid TOTP encryption key") from error

    def encrypt(self, secret, user_id):
        payload = json.dumps({"user_id": user_id, "secret": secret}).encode()
        return PREFIX + self.fernet.encrypt(payload).decode()

    def decrypt(self, ciphertext, user_id, *, primary_only=False):
        try:
            if not ciphertext.startswith(PREFIX):
                raise ValueError("Unencrypted secret")
            reader = self.fernet if primary_only else self.reader
            payload = json.loads(reader.decrypt(ciphertext[len(PREFIX):].encode()))
            if payload["user_id"] != user_id:
                raise ValueError("Secret belongs to another account")
            return payload["secret"]
        except (InvalidToken, ValueError, KeyError, TypeError) as error:
            raise ValueError("Unable to decrypt authenticator secret") from error


def load_box(settings):
    if settings.encryption_key:
        return SecretBox(settings.encryption_key, settings.previous_encryption_key)
    if settings.secure:
        raise ValueError("Missing TOTP_ENCRYPTION_KEY")
    # Only the fictional demo can generate a local key. Never regenerate a lost key.
    path = Path("private-data/totp.key")
    path.parent.mkdir(exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return SecretBox(path.read_bytes().strip())
    with os.fdopen(fd, "wb") as file:
        key = Fernet.generate_key()
        file.write(key)
    return SecretBox(key)
