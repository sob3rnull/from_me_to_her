import os
from pathlib import Path
from alembic import context
from sqlalchemy import create_engine
from app.models import Base

Path("private-data").mkdir(exist_ok=True)
url = os.getenv("DATABASE_URL", "sqlite:///./private-data/archive.db")
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
