import secrets
from concurrent.futures import ThreadPoolExecutor

import pyotp
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts import enroll, replace_factor, replace_recovery_codes
from app.admin import encrypt_legacy_secrets
from app.config import Settings
from app.main import create_app
from app.models import Base, BrowserSession, RecoveryCode, User
from app.secret_box import SecretBox
from test_security import app, client, credentials, gates, login


def issue_codes(application, username='demo-owner'):
    with Session(application.state.engine) as db:
        user = db.scalar(select(User).where(User.username == username))
        codes = replace_recovery_codes(db, user)
        db.commit()
        return codes


def test_encryption_binds_secret_to_account_and_rejects_wrong_key(app):
    with Session(app.state.engine) as db:
        user = db.scalar(select(User).where(User.role == 'OWNER'))
        assert 'JBSWY3DPEHPK3PXP' not in user.totp_secret
        assert app.state.box.decrypt(user.totp_secret, user.id) == 'JBSWY3DPEHPK3PXP'
        with pytest.raises(ValueError): app.state.box.decrypt(user.totp_secret, 'another-account')
        with pytest.raises(ValueError): SecretBox(Fernet.generate_key()).decrypt(user.totp_secret, user.id)


def test_recovery_is_one_use_requires_password_and_revokes_sessions(app):
    codes = issue_codes(app)
    original = client(app); login(original)
    recovering = client(app)
    data = {'username':'demo-owner', 'password':'wrong', 'recovery_code':codes[0]}
    assert recovering.post('/api/auth/login/owner', json=data).status_code == 403
    data['password'] = 'fictional-demo-only'
    response = recovering.post('/api/auth/login/owner', json=data)
    assert response.status_code == 200 and response.json()['recovered']
    assert original.get('/api/entries').status_code == 401
    assert client(app).post('/api/auth/login/owner', json=data).status_code == 403
    with Session(app.state.engine) as db:
        rows = list(db.scalars(select(RecoveryCode)))
        assert len(rows) == 7
        assert not any(row.code_hash in codes for row in rows)


def test_recovery_cannot_skip_reader_gates_or_change_role(app):
    code = issue_codes(app, 'demo-reader')[0]
    c = client(app)
    data = {'username':'demo-reader', 'password':'fictional-demo-only', 'recovery_code':code}
    assert c.post('/api/auth/login/reader', json=data).status_code == 403
    assert c.post('/api/auth/login/owner', json=data).status_code == 403
    gates(c)
    assert c.post('/api/auth/login/reader', json=data).status_code == 200


def test_concurrent_recovery_has_exactly_one_winner(app):
    code = issue_codes(app)[0]
    clients = [client(app), client(app)]
    data = {'username':'demo-owner', 'password':'fictional-demo-only', 'recovery_code':code}
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda c: c.post('/api/auth/login/owner', json=data).status_code, clients))
    assert sorted(statuses) == [200,403]


def test_enrollment_checks_factor_before_creating_user(tmp_path):
    application = create_app(f'sqlite:///{tmp_path / "fresh.db"}', secret_box=SecretBox(Fernet.generate_key()))
    Base.metadata.create_all(application.state.engine)
    secret = pyotp.random_base32()
    password = secrets.token_urlsafe(24)
    with Session(application.state.engine) as db:
        with pytest.raises(ValueError):
            enroll(db, application.state.box, 'archive-owner', 'OWNER', password, secret, 'invalid')
        assert db.scalar(select(User.id)) is None
        codes = enroll(db, application.state.box, 'archive-owner', 'OWNER', password, secret, pyotp.TOTP(secret).now())
        assert len(set(codes)) == 8
        user = db.scalar(select(User))
        assert not user.is_demo
        assert application.state.box.decrypt(user.totp_secret, user.id) == secret
        assert user.password_hash != password
        with pytest.raises(ValueError):
            enroll(db, application.state.box, 'second-owner', 'OWNER', password, secret, pyotp.TOTP(secret).now())
    application.state.engine.dispose()


def test_factor_replacement_invalidates_codes_and_sessions(app):
    old_codes = issue_codes(app)
    c = client(app); login(c)
    new_secret = pyotp.random_base32()
    with Session(app.state.engine) as db:
        new_codes = replace_factor(db, app.state.box, 'demo-owner', 'fictional-demo-only', old_codes[0], new_secret, pyotp.TOTP(new_secret).now())
        assert not set(new_codes) & set(old_codes)
        user = db.scalar(select(User).where(User.role == 'OWNER'))
        assert app.state.box.decrypt(user.totp_secret, user.id) == new_secret
    assert c.get('/api/entries').status_code == 401
    attempt = client(app)
    data = {'username':'demo-owner','password':'fictional-demo-only','recovery_code':old_codes[1]}
    assert attempt.post('/api/auth/login/owner',json=data).status_code == 403
    data['recovery_code'] = new_codes[0]
    assert attempt.post('/api/auth/login/owner',json=data).status_code == 200


def test_legacy_encryption_is_idempotent(app):
    with Session(app.state.engine) as db:
        user = db.scalar(select(User).where(User.role == 'OWNER'))
        user.totp_secret = 'JBSWY3DPEHPK3PXP'
        db.commit()
        assert encrypt_legacy_secrets(db, app.state.box) == 1
        assert encrypt_legacy_secrets(db, app.state.box) == 0


def test_secure_config_fails_closed(monkeypatch):
    monkeypatch.setenv('APP_MODE','secure')
    monkeypatch.delenv('TOTP_ENCRYPTION_KEY',raising=False)
    with pytest.raises(ValueError): Settings.from_env()
    monkeypatch.setenv('VAULT_ORIGIN','https://vault.example.test')
    with pytest.raises(ValueError): Settings.from_env()
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test:test@localhost/archive_test')
    monkeypatch.setenv('TOTP_ENCRYPTION_KEY',Fernet.generate_key().decode())
    assert Settings.from_env().cookie_name == '__Host-vault_session'


def test_secure_mode_refuses_demo_accounts(app, monkeypatch):
    monkeypatch.setenv('APP_MODE','secure')
    monkeypatch.setenv('VAULT_ORIGIN','https://vault.example.test')
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test:test@localhost/archive_test')
    monkeypatch.setenv('TOTP_ENCRYPTION_KEY',Fernet.generate_key().decode())
    secure = create_app(str(app.state.engine.url),secret_box=app.state.box)
    with pytest.raises(RuntimeError, match='refuses demo'):
        with TestClient(secure,base_url='https://vault.example.test'): pass
    secure.state.engine.dispose()


def test_secure_cookies_origin_host_and_transport(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_MODE','secure')
    monkeypatch.setenv('VAULT_ORIGIN','https://vault.example.test')
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test:test@localhost/archive_test')
    monkeypatch.setenv('TOTP_ENCRYPTION_KEY',Fernet.generate_key().decode())
    application = create_app(f'sqlite:///{tmp_path / "secure.db"}')
    Base.metadata.create_all(application.state.engine)
    with TestClient(application,base_url='https://vault.example.test') as c:
        response = c.get('/api/auth/session')
        cookie = response.headers['set-cookie']
        assert '__Host-vault_session=' in cookie and 'Secure' in cookie and 'HttpOnly' in cookie
        assert 'Domain=' not in cookie
        assert c.get('/api/health',headers={'host':'evil.test'}).status_code == 400
        assert c.get('http://vault.example.test/api/health').status_code == 400
        assert c.post('/api/auth/logout',headers={'origin':'https://evil.test'}).status_code == 403
    application.state.engine.dispose()
