"""Disposable migrated database for browser tests; never opens the demo database."""
import os
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="from-me-to-her-e2e-") as folder:
    os.environ["DATABASE_URL"] = "sqlite:///" + (Path(folder) / "archive.db").as_posix()
    os.chdir(Path(__file__).resolve().parents[2] / "apps" / "api")
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config("alembic.ini"), "head")
    from app.main import app
    from app.demo import seed
    seed(app.state.engine)
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8100, proxy_headers=False)
    finally:
        app.state.engine.dispose()
