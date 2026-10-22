"""Disposable migrated database for browser tests; never opens the demo database."""
import os
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet

with tempfile.TemporaryDirectory(prefix="from-me-to-her-e2e-") as folder:
    os.environ["APP_MODE"] = "demo"
    os.environ["TOTP_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    os.environ["DATABASE_URL"] = "sqlite:///" + (Path(folder) / "archive.db").as_posix()
    os.chdir(Path(__file__).resolve().parents[2] / "apps" / "api")
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config("alembic.ini"), "head")
    from app.main import app
    from app.demo import seed
    seed(app.state.engine)
    # Public fictional recovery fixture used only by the disposable browser test.
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.accounts import recovery_digest
    from app.models import User, RecoveryCode
    with Session(app.state.engine) as db:
        owner = db.scalar(select(User).where(User.role == "OWNER"))
        db.add(RecoveryCode(user_id=owner.id, code_hash=recovery_digest(owner.id, "a" * 32)))
        db.commit()
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8100, proxy_headers=False)
    finally:
        app.state.engine.dispose()
