from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    totp_secret: Mapped[str] = mapped_column(Text)
    last_totp_step: Mapped[int] = mapped_column(Integer, default=-1)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"
    code_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)


class BrowserSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf: Mapped[str] = mapped_column(String(64))
    stage: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[int] = mapped_column(Integer)


class Attempt(Base):
    __tablename__ = "attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[int] = mapped_column(Integer)


class GateConfig(Base):
    __tablename__ = "gate_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    questions_json: Mapped[str] = mapped_column(Text)
    threshold: Mapped[int] = mapped_column(Integer)
    anniversary_hash: Mapped[str] = mapped_column(Text)
    name_hash: Mapped[str] = mapped_column(Text)


class Entry(Base):
    __tablename__ = "entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[int] = mapped_column(Integer)


class Promise(Base):
    __tablename__ = "promises"
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id"), primary_key=True)
    promise: Mapped[str] = mapped_column(Text)
    date_made: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))
    context: Mapped[str] = mapped_column(Text, default="")
    still_intended: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[int] = mapped_column(Integer)
