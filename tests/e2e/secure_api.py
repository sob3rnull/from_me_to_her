"""Fictional HTTPS fixture only. Never import from application code."""
import os
from pathlib import Path

import pyotp
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.accounts import enroll, recovery_digest
from app.admin import configure_gates
from app.models import RecoveryCode, User
from app.secret_box import SecretBox


database_url = os.environ['TEST_HTTPS_DATABASE_URL']
os.chdir(Path(__file__).resolve().parents[2] / 'apps' / 'api')
os.environ['DATABASE_URL'] = database_url
command.upgrade(Config('alembic.ini'), 'head')
command.check(Config('alembic.ini'))
engine = create_engine(database_url)
box = SecretBox(os.environ['TOTP_ENCRYPTION_KEY'])
with Session(engine) as db:
    configure_gates(db, [
        {'prompt': 'Demo: which planet has rings?', 'answer': 'saturn', 'weight': 2},
        {'prompt': 'Demo: tea or coffee?', 'answer': 'tea', 'weight': 1},
    ], 3, '2020-01-01', 'Alex Example')
    for role in ('OWNER', 'READER'):
        enroll(db, box, 'test-' + role.lower(), role, 'fictional-demo-only',
               'JBSWY3DPEHPK3PXP', pyotp.TOTP('JBSWY3DPEHPK3PXP').now())
    # Avoid waiting for enrollment's consumed TOTP step in this disposable fixture.
    for user in db.scalars(select(User)):
        user.last_totp_step = -1
        if user.role == 'OWNER':
            db.add(RecoveryCode(user_id=user.id, code_hash=recovery_digest(user.id, 'a' * 32)))
    db.commit()
engine.dispose()

os.environ['APP_MODE'] = 'secure'
os.environ['VAULT_ORIGIN'] = 'https://vault.localhost:8443'
# The local rehearsal injects SQLite into the factory, like existing secure-mode
# unit tests. CI supplies real PostgreSQL. Production config is never relaxed.
if database_url.startswith('sqlite:'):
    os.environ['DATABASE_URL'] = 'postgresql+psycopg://unused:unused@localhost/unused'
from app.main import create_app
import uvicorn

application = create_app(database_url, secret_box=box)
try:
    uvicorn.run(application, host='127.0.0.1', port=8100,
                proxy_headers=True, forwarded_allow_ips='127.0.0.1')
finally:
    application.state.engine.dispose()
