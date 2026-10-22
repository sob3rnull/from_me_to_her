import pytest
import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.demo import seed
from app.main import create_app
from app.models import Base, BrowserSession, User
from app.security import now

ORIGIN = 'http://localhost:3001'


@pytest.fixture
def app(tmp_path):
    application = create_app(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(application.state.engine)
    seed(application.state.engine)
    yield application
    application.state.engine.dispose()


def client(app):
    c = TestClient(app, headers={'origin': ORIGIN})
    c.headers['x-csrf-token'] = c.get('/api/auth/session').json()['csrf']
    return c


def gates(c):
    assert c.post('/api/auth/gate1', json={'answers': {'planet': 'SATURN', 'drink': ' tea '}}).status_code == 200
    assert c.post('/api/auth/gate2', json={'anniversary':'2020-01-01', 'full_name':'Alex Example'}).status_code == 200


def credentials(role):
    return {'username': f'demo-{role}', 'password':'fictional-demo-only', 'code':pyotp.TOTP('JBSWY3DPEHPK3PXP').now()}


def login(c, role='owner'):
    if role == 'reader': gates(c)
    response = c.post(f'/api/auth/login/{role}', json=credentials(role))
    assert response.status_code == 200, response.text
    c.headers['x-csrf-token'] = response.json()['csrf']


def entry(**kwargs):
    return {'category':'Letters', 'title':'Fictional letter', 'body':'<script>alert(1)</script>', **kwargs}


def test_anonymous_and_skipped_gates_denied(app):
    c = client(app)
    assert c.get('/api/entries').status_code == 401
    assert c.post('/api/auth/gate2', json={'anniversary':'2020-01-01','full_name':'Alex Example'}).status_code == 403
    assert c.post('/api/auth/login/reader', json=credentials('reader')).status_code == 403
    challenge = c.get('/api/auth/challenge').json()
    assert 'fields' not in challenge
    assert all(set(q) == {'id', 'prompt'} for q in challenge['questions'])


def test_weighted_gate_requires_threshold_and_does_not_reveal_next(app):
    c = client(app)
    assert c.post('/api/auth/gate1', json={'answers':{'planet':'saturn'}}).status_code == 403
    assert c.get('/api/auth/session').json()['stage'] == 0
    assert 'fields' not in c.get('/api/auth/challenge').json()


def test_owner_reader_authorization_and_edit(app):
    owner = client(app); login(owner)
    draft = owner.post('/api/entries', json=entry()).json()
    shared = owner.post('/api/entries', json=entry(shared=True)).json()
    reader = client(app); login(reader, 'reader')
    assert [e['id'] for e in reader.get('/api/entries').json()] == [shared['id']]
    assert reader.get('/api/entries/' + draft['id']).status_code == 404
    assert reader.post('/api/entries', json=entry()).status_code == 403
    assert reader.put('/api/entries/' + shared['id'], json=entry()).status_code == 403
    assert owner.put('/api/entries/' + shared['id'], json=entry(shared=False)).status_code == 200
    assert reader.get('/api/entries/' + shared['id']).status_code == 404


def test_csrf_and_origin(app):
    c = client(app); login(c)
    assert c.post('/api/entries', json=entry(), headers={'x-csrf-token':'wrong'}).status_code == 403
    assert c.post('/api/entries', json=entry(), headers={'origin':'https://evil.example'}).status_code == 403
    c.headers.pop('origin')
    assert c.post('/api/entries', json=entry()).status_code == 403


def test_rotation_logout_and_expiry(app):
    c = client(app); old = c.cookies.get('vault_session'); login(c)
    assert c.cookies.get('vault_session') != old
    stale = TestClient(app, cookies={'vault_session':old})
    assert stale.get('/api/entries').status_code == 401
    assert c.post('/api/auth/logout').status_code == 200
    assert c.get('/api/entries').status_code == 401
    fresh = client(app)
    with Session(app.state.engine) as db:
        db.execute(update(BrowserSession).values(expires_at=now()-1)); db.commit()
    assert fresh.get('/api/auth/challenge').status_code == 401


def test_totp_replay_and_reader_owner_bypass(app):
    c = client(app); data = credentials('owner')
    assert c.post('/api/auth/login/owner', json=data).status_code == 200
    other = client(app)
    assert other.post('/api/auth/login/owner', json=data).status_code == 403
    assert other.post('/api/auth/login/owner', json=credentials('reader')).status_code == 403


def test_invalid_totp_and_password(app):
    c = client(app)
    data = credentials('owner'); data['password'] = 'wrong'
    assert c.post('/api/auth/login/owner', json=data).status_code == 403
    data = credentials('owner'); data['code'] = '000000' if data['code'] != '000000' else '111111'
    assert c.post('/api/auth/login/owner', json=data).status_code == 403


def test_persistent_limits_survive_new_sessions(app):
    c = client(app)
    for _ in range(10):
        assert c.post('/api/auth/gate1', json={'answers':{}}).status_code == 403
    fresh = client(app)
    assert fresh.post('/api/auth/gate1', json={'answers':{}}).status_code == 429


def test_promises_validation_and_roundtrip(app):
    c = client(app); login(c)
    assert c.post('/api/entries', json=entry(category='Unknown')).status_code == 422
    assert c.post('/api/entries', json=entry(category='Promises')).status_code == 422
    data = entry(category='Promises', promise={'promise':'Send a postcard','status':'ONGOING','still_intended':True})
    response = c.post('/api/entries', json=data)
    assert response.status_code == 201
    assert response.json()['promise']['promise'] == 'Send a postcard'
    assert response.json()['body'] == '<script>alert(1)</script>'  # UI must render as text.
    assert response.headers['cache-control'] == 'no-store'


def test_seed_refuses_existing_database(app):
    with pytest.raises(RuntimeError): seed(app.state.engine)
