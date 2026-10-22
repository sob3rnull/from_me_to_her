import os
import subprocess
import sys

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin import rotate_secrets, verify_secrets
from app.config import Settings
from app.main import create_app
from app.models import AuditEvent, BrowserSession, User
from app.secret_box import SecretBox
from test_security import app, client, login


def test_rotation_revokes_sessions_preserves_factor_and_allows_new_key_login(app):
    old = client(app); login(old)
    client(app)  # Pre-auth sessions must also be revoked.
    new_key = Fernet.generate_key()
    box = SecretBox(new_key)
    # A transition reader can read the existing key without exposing it to this test.
    box.reader = app.state.box.reader
    with Session(app.state.engine) as db:
        assert rotate_secrets(db, box) == 2
        assert verify_secrets(db, SecretBox(new_key)) == 2
        assert db.scalar(select(BrowserSession)) is None
        assert db.scalar(select(AuditEvent.action).where(AuditEvent.action == 'TOTP_KEY_ROTATED'))
        for user in db.scalars(select(User)):
            assert box.decrypt(user.totp_secret, user.id, primary_only=True) == 'JBSWY3DPEHPK3PXP'
            with pytest.raises(ValueError): app.state.box.decrypt(user.totp_secret, user.id)
    assert old.get('/api/entries').status_code == 401
    restarted = create_app(str(app.state.engine.url), secret_box=SecretBox(new_key))
    try:
        login(client(restarted), 'reader')
    finally:
        restarted.state.engine.dispose()


@pytest.mark.parametrize('failure', ['corrupt-account', 'verification'])
def test_failed_rotation_rolls_back_every_ciphertext_and_session(app, monkeypatch, failure):
    owner = client(app); login(owner)
    box = SecretBox(Fernet.generate_key())
    box.reader = app.state.box.reader
    if failure == 'verification':
        original = box.decrypt
        def fail_verification(ciphertext, user_id, *, primary_only=False):
            if primary_only:
                raise ValueError('Simulated verification failure after flush')
            return original(ciphertext, user_id)
        monkeypatch.setattr(box, 'decrypt', fail_verification)
    with Session(app.state.engine) as db:
        if failure == 'corrupt-account':
            users = list(db.scalars(select(User).order_by(User.id)))
            users[-1].totp_secret = 'fernet:v1:corrupt'
            db.commit()
        before = dict(db.execute(select(User.id, User.totp_secret)).all())
        sessions = list(db.scalars(select(BrowserSession.token_hash)))
        with pytest.raises(ValueError): rotate_secrets(db, box)
        assert dict(db.execute(select(User.id, User.totp_secret)).all()) == before
        assert list(db.scalars(select(BrowserSession.token_hash))) == sessions
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == 'TOTP_KEY_ROTATED')) is None
    assert owner.get('/api/entries').status_code == 200


def test_transition_reads_both_keys_but_writes_only_primary():
    old_key, new_key = Fernet.generate_key(), Fernet.generate_key()
    old, new = SecretBox(old_key), SecretBox(new_key)
    transition = SecretBox(new_key, old_key)
    ciphertext = old.encrypt('fictional', 'owner')
    assert transition.decrypt(ciphertext, 'owner') == 'fictional'
    with pytest.raises(ValueError): transition.decrypt(ciphertext, 'owner', primary_only=True)
    with pytest.raises(ValueError): transition.decrypt(ciphertext, 'reader')
    assert new.decrypt(transition.encrypt('fictional', 'owner'), 'owner') == 'fictional'
    with pytest.raises(ValueError): SecretBox(new_key, 'invalid')


def test_rotation_config_requires_distinct_explicit_keys(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv('TOTP_PREVIOUS_ENCRYPTION_KEY', key)
    monkeypatch.delenv('TOTP_ENCRYPTION_KEY', raising=False)
    with pytest.raises(ValueError): Settings.from_env()
    monkeypatch.setenv('TOTP_ENCRYPTION_KEY', key)
    with pytest.raises(ValueError): Settings.from_env()


def test_operator_cli_rotation_and_fallback_retirement(app):
    old_key, new_key = Fernet.generate_key(), Fernet.generate_key()
    old_box = SecretBox(old_key)
    with Session(app.state.engine) as db:
        for user in db.scalars(select(User)):
            user.totp_secret = old_box.encrypt(app.state.box.decrypt(user.totp_secret, user.id), user.id)
        db.commit()
        before = list(db.execute(select(User.id, User.password_hash, User.last_totp_step)).all())
    env = dict(os.environ, APP_MODE='demo', VAULT_ORIGIN='http://localhost:3001',
               DATABASE_URL=str(app.state.engine.url), TOTP_ENCRYPTION_KEY=new_key.decode(),
               TOTP_PREVIOUS_ENCRYPTION_KEY=old_key.decode())
    command = [sys.executable, '-m', 'app.admin']
    refused = subprocess.run(command + ['rotate-secrets'], env=env, capture_output=True, text=True)
    assert refused.returncode != 0 and '--offline' in refused.stderr
    result = subprocess.run(command + ['rotate-secrets', '--offline'], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'Rotated and verified 2 secrets' in result.stdout
    env.pop('TOTP_PREVIOUS_ENCRYPTION_KEY')
    verified = subprocess.run(command + ['verify-secrets'], env=env, capture_output=True, text=True)
    assert verified.returncode == 0 and 'Verified 2 secrets' in verified.stdout
    assert old_key.decode() not in result.stdout + result.stderr
    assert new_key.decode() not in result.stdout + result.stderr
    with Session(app.state.engine) as db:
        assert list(db.execute(select(User.id, User.password_hash, User.last_totp_step)).all()) == before
