"""Explicit demo / HTTPS configuration. No production secrets have defaults."""
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    mode: str
    origin: str
    database_url: str = field(repr=False)
    encryption_key: str | None = field(default=None, repr=False)

    @property
    def secure(self):
        return self.mode == "secure"

    @property
    def cookie_name(self):
        return "__Host-vault_session" if self.secure else "vault_session"

    @classmethod
    def from_env(cls, origin=None):
        mode = os.getenv("APP_MODE", "demo")
        origin = origin or os.getenv("VAULT_ORIGIN", "http://localhost:3001")
        database = os.getenv("DATABASE_URL", "sqlite:///./private-data/archive.db")
        key = os.getenv("TOTP_ENCRYPTION_KEY")
        if mode not in {"demo", "secure"}:
            raise ValueError("APP_MODE must be demo or secure")
        parsed = urlsplit(origin)
        if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or not parsed.hostname:
            raise ValueError("VAULT_ORIGIN must be an origin without credentials, path, query or fragment")
        if mode == "secure":
            if parsed.scheme != "https" or parsed.hostname in {"localhost", "127.0.0.1"}:
                raise ValueError("Secure mode requires a non-loopback HTTPS VAULT_ORIGIN")
            if not database.startswith("postgresql+psycopg://") or not key:
                raise ValueError("Secure mode requires PostgreSQL and TOTP_ENCRYPTION_KEY")
        elif origin not in {"http://localhost:3001", "http://127.0.0.1:3001"}:
            raise ValueError("Demo mode requires a loopback vault origin")
        return cls(mode, origin, database, key)
