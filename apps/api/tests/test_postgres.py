"""Real PostgreSQL coverage in an isolated random schema; enabled by CI."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.demo import seed
from app.main import create_app
from app.secret_box import SecretBox
from app.admin import rotate_secrets, verify_secrets
from sqlalchemy.orm import Session
from test_accounts import issue_codes
from test_security import client, entry, login


@pytest.mark.skipif(not os.getenv('TEST_POSTGRES_URL'), reason='Disposable PostgreSQL service not configured')
def test_postgres_migrations_permissions_and_atomic_recovery(monkeypatch):
    root_url = make_url(os.environ['TEST_POSTGRES_URL'])
    schema = 'test_' + uuid4().hex
    admin = create_engine(root_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    url = root_url.update_query_dict({'options': f'-csearch_path={schema}'})
    application = None
    try:
        monkeypatch.setenv('DATABASE_URL', url.render_as_string(hide_password=False))
        directory = Path(__file__).resolve().parents[1]
        config = Config(str(directory / 'alembic.ini'))
        config.set_main_option('script_location', str(directory / 'migrations'))
        command.upgrade(config, 'head')
        command.check(config)
        application = create_app(secret_box=SecretBox(Fernet.generate_key()))
        seed(application.state.engine, application.state.box)
        owner = client(application); login(owner)
        draft = owner.post('/api/entries', json=entry()).json()
        shared = owner.post('/api/entries', json=entry(shared=True)).json()
        reader = client(application); login(reader, 'reader')
        assert reader.get('/api/entries/' + draft['id']).status_code == 404
        assert reader.get('/api/entries/' + shared['id']).status_code == 200
        assert reader.put('/api/entries/' + shared['id'], json=entry()).status_code == 403
        code = issue_codes(application)[0]
        clients = [client(application), client(application)]
        data = {'username':'demo-owner','password':'fictional-demo-only','recovery_code':code}
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(lambda c: c.post('/api/auth/login/owner',json=data).status_code, clients))
        assert sorted(result) == [200,403]
        assert owner.get('/api/entries').status_code == 401
        new_key = Fernet.generate_key()
        transition = SecretBox(new_key)
        transition.reader = application.state.box.reader
        with Session(application.state.engine) as db:
            assert rotate_secrets(db, transition) == 2
            assert verify_secrets(db, SecretBox(new_key)) == 2
        for c in clients:
            assert c.get('/api/entries').status_code == 401
    finally:
        if application:
            application.state.engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()
