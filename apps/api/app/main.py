import json
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pyotp
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from urllib.parse import urlsplit

from .models import Attempt, AuditEvent, BrowserSession, Entry, GateConfig, Promise, RecoveryCode, User
from .accounts import recovery_digest
from .config import Settings
from .secret_box import load_box
from .schemas import CATEGORIES, EntryInput, GateOneInput, GateTwoInput, LoginInput
from .security import digest, normalize, now, passwords, token


def create_app(database_url=None, origin=None, secret_box=None):
    settings = Settings.from_env(origin)
    origin = settings.origin
    box = secret_box or load_box(settings)
    Path("private-data").mkdir(exist_ok=True)
    url = database_url or settings.database_url
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})

    @asynccontextmanager
    async def lifespan(application):
        if settings.secure:
            with Session(engine) as db:
                for user in db.scalars(select(User)):
                    if user.is_demo:
                        raise RuntimeError("Secure mode refuses demo accounts; use a fresh database")
                    box.decrypt(user.totp_secret, user.id)
        yield

    app = FastAPI(title="from_me_to_her", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.engine = engine
    app.state.box = box
    app.state.settings = settings
    if settings.secure:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlsplit(origin).hostname])
    dummy_hash = passwords.hash(token())

    def database():
        with Session(engine) as db:
            yield db

    def audit(db, action, actor=None, target=None):
        db.add(AuditEvent(id=str(uuid4()), actor_id=actor, action=action, target_id=target, created_at=now()))

    def session(request: Request, db: Session = Depends(database)):
        raw = request.cookies.get(settings.cookie_name, "")
        row = db.get(BrowserSession, digest(raw))
        if not row or row.expires_at <= now():
            raise HTTPException(401, "Session expired or missing")
        if request.method not in {"GET", "HEAD"}:
            if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), row.csrf):
                raise HTTPException(403, "Invalid CSRF token")
        return row

    def authenticated(row=Depends(session), db: Session = Depends(database)):
        user = db.get(User, row.user_id) if row.user_id else None
        if not user:
            raise HTTPException(401, "Authentication required")
        return user

    def owner(user=Depends(authenticated)):
        if user.role != "OWNER":
            raise HTTPException(403, "Owner access required")
        return user

    def throttle(db, key, limit=10):
        key = digest(key)
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.dialects.postgresql import insert as postgres_insert
        db.execute(delete(Attempt).where(Attempt.key == key, Attempt.expires_at <= now()))
        insert = sqlite_insert if engine.dialect.name == "sqlite" else postgres_insert
        statement = insert(Attempt).values(key=key, count=1, expires_at=now() + 900)
        db.execute(statement.on_conflict_do_update(index_elements=[Attempt.key], set_={"count": Attempt.count + 1}))
        db.commit()
        row = db.get(Attempt, key)
        if row.count > limit:
            raise HTTPException(429, "Too many attempts. Try again later.")

    def set_cookie(response, raw):
        response.set_cookie(settings.cookie_name, raw, httponly=True, samesite="strict", secure=settings.secure, path="/", max_age=3600)

    def gate_config(db):
        config = db.get(GateConfig, 1)
        if not config:
            raise HTTPException(503, "Archive setup is incomplete")
        return config

    @app.middleware("http")
    async def boundary(request, call_next):
        if settings.secure and request.url.scheme != "https":
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "HTTPS required"}, status_code=400)
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("origin") != origin:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Invalid request origin"}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if settings.secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": settings.mode}

    @app.get("/api/auth/session")
    def bootstrap(request: Request, response: Response, db: Session = Depends(database)):
        row = db.get(BrowserSession, digest(request.cookies.get(settings.cookie_name, "")))
        if not row or row.expires_at <= now():
            throttle(db, "bootstrap:" + request.client.host, 100)
            raw = token()
            row = BrowserSession(token_hash=digest(raw), csrf=token(), stage=0, expires_at=now() + 600)
            db.add(row)
            db.commit()
            set_cookie(response, raw)
        user = db.get(User, row.user_id) if row.user_id else None
        return {"csrf": row.csrf, "stage": row.stage, "role": user.role if user else None, "mode": settings.mode}

    @app.get("/api/auth/challenge")
    def challenge(row=Depends(session), db: Session = Depends(database)):
        config = gate_config(db)
        if row.stage == 0:
            return {"questions": [{"id": q["id"], "prompt": q["prompt"]} for q in json.loads(config.questions_json)]}
        if row.stage == 1:
            return {"fields": ["Anniversary (YYYY-MM-DD)", "His full name"]}
        return {"fields": ["Username", "Password", "Authenticator code"]}

    @app.post("/api/auth/gate1")
    def gate1(data: GateOneInput, request: Request, row=Depends(session), db: Session = Depends(database)):
        throttle(db, "gates:" + request.client.host)
        if row.stage != 0 or row.user_id:
            raise HTTPException(403, "Invalid stage")
        config = gate_config(db)
        score = sum(q["weight"] for q in json.loads(config.questions_json)
                    if passwords.verify(normalize(data.answers.get(q["id"], ""))[:200], q["hash"]))
        if score < config.threshold:
            audit(db, "GATE1_FAIL")
            db.commit()
            raise HTTPException(403, "Unable to continue")
        row.stage = 1
        audit(db, "GATE1_PASS")
        db.commit()
        return {"stage": 1}

    @app.post("/api/auth/gate2")
    def gate2(data: GateTwoInput, request: Request, row=Depends(session), db: Session = Depends(database)):
        throttle(db, "gates:" + request.client.host)
        if row.stage != 1 or row.user_id:
            raise HTTPException(403, "Invalid stage")
        config = gate_config(db)
        date_ok = passwords.verify(normalize(data.anniversary), config.anniversary_hash)
        name_ok = passwords.verify(normalize(data.full_name), config.name_hash)
        if not (date_ok and name_ok):
            audit(db, "GATE2_FAIL")
            db.commit()
            raise HTTPException(403, "Unable to continue")
        row.stage = 2
        audit(db, "GATE2_PASS")
        db.commit()
        return {"stage": 2}

    @app.post("/api/auth/login/{kind}")
    def login(kind: str, data: LoginInput, request: Request, response: Response,
              row=Depends(session), db: Session = Depends(database)):
        throttle(db, "login-ip:" + request.client.host)
        throttle(db, "login-user:" + normalize(data.username))
        if kind not in {"owner", "reader"} or row.user_id or (kind == "reader" and row.stage != 2):
            raise HTTPException(403, "Invalid login stage")
        user = db.scalar(select(User).where(User.username == normalize(data.username)).with_for_update())
        valid_password = passwords.verify(data.password, user.password_hash if user else dummy_hash)
        step = now() // 30
        valid = user and valid_password and user.role == kind.upper() and not (settings.secure and user.is_demo)
        recovered = False
        if valid and data.recovery_code:
            consumed = db.execute(delete(RecoveryCode).where(
                RecoveryCode.user_id == user.id,
                RecoveryCode.code_hash == recovery_digest(user.id, data.recovery_code)))
            valid = consumed.rowcount == 1
            recovered = bool(valid)
        elif valid:
            try:
                secret = box.decrypt(user.totp_secret, user.id)
            except ValueError:
                raise HTTPException(503, "Authenticator configuration unavailable")
            valid = secrets.compare_digest(pyotp.TOTP(secret).at(step * 30), data.code)
        if valid and not recovered:
            # Atomic compare-and-set prevents concurrent reuse of the same TOTP step.
            accepted = db.execute(update(User).where(User.id == user.id, User.last_totp_step < step).values(last_totp_step=step))
            valid = accepted.rowcount == 1
        if not valid:
            audit(db, "LOGIN_FAIL")
            db.commit()
            raise HTTPException(403, "Unable to sign in")
        raw = token()
        new = BrowserSession(token_hash=digest(raw), csrf=token(), stage=3, user_id=user.id, expires_at=now() + 3600)
        if recovered:
            db.execute(delete(BrowserSession).where(BrowserSession.user_id == user.id))
            audit(db, "RECOVERY_CODE_USED", user.id)
        db.delete(row)
        db.add(new)
        audit(db, "SESSION_CREATED", user.id)
        db.commit()
        set_cookie(response, raw)
        return {"csrf": new.csrf, "role": user.role, "stage": 3, "recovered": recovered}

    @app.post("/api/auth/logout")
    def logout(response: Response, row=Depends(session), db: Session = Depends(database)):
        db.delete(row)
        db.commit()
        response.delete_cookie(settings.cookie_name, path="/", secure=settings.secure, httponly=True, samesite="strict")
        return {"ok": True}

    @app.get("/api/categories")
    def categories(user=Depends(authenticated)):
        return CATEGORIES

    def serialize(entry, db):
        result = {k: getattr(entry, k) for k in ("id", "category", "title", "body", "shared", "occurred_on", "created_at", "updated_at")}
        promise = db.get(Promise, entry.id)
        result["promise"] = {k: getattr(promise, k) for k in ("promise", "date_made", "status", "context", "still_intended", "notes")} if promise else None
        return result

    @app.get("/api/entries")
    def entries(user=Depends(authenticated), db: Session = Depends(database)):
        query = select(Entry).order_by(Entry.created_at.desc(), Entry.id).limit(100)
        if user.role != "OWNER":
            query = query.where(Entry.shared.is_(True))
        return [serialize(entry, db) for entry in db.scalars(query)]

    @app.get("/api/entries/{entry_id}")
    def detail(entry_id: str, user=Depends(authenticated), db: Session = Depends(database)):
        entry = db.get(Entry, entry_id)
        if not entry or (user.role != "OWNER" and not entry.shared):
            raise HTTPException(404, "Entry not found")
        return serialize(entry, db)

    def save(data, db, user, entry=None):
        values = data.model_dump(exclude={"promise"})
        if entry is None:
            entry = Entry(id=str(uuid4()), created_at=now(), updated_at=now(), **values)
            db.add(entry)
            db.flush()
        else:
            for key, value in values.items():
                setattr(entry, key, value)
            entry.updated_at = now()
        existing = db.get(Promise, entry.id)
        if data.promise:
            if existing:
                for key, value in data.promise.model_dump().items():
                    setattr(existing, key, value)
            else:
                db.add(Promise(entry_id=entry.id, **data.promise.model_dump()))
        elif existing:
            db.delete(existing)
        audit(db, "ENTRY_SAVED", user.id, entry.id)
        db.commit()
        return serialize(entry, db)

    @app.post("/api/entries", status_code=201)
    def create_entry(data: EntryInput, user=Depends(owner), db: Session = Depends(database)):
        return save(data, db, user)

    @app.put("/api/entries/{entry_id}")
    def edit_entry(entry_id: str, data: EntryInput, user=Depends(owner), db: Session = Depends(database)):
        entry = db.get(Entry, entry_id)
        if not entry:
            raise HTTPException(404, "Entry not found")
        return save(data, db, user, entry)

    return app


app = create_app()
