"""Rehearse the real Caddy template with isolated keys/data and loopback listeners.

Run with .venv's Python after npm run build. CADDY_BIN or PATH supplies Caddy;
--download-caddy fetches a pinned release and verifies its published SHA512.
TEST_POSTGRES_URL selects a disposable random PostgreSQL schema; otherwise SQLite.
"""
import argparse
import hashlib
import io
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from uuid import uuid4
import zipfile

import httpx
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
VERSION = '2.11.7'


def download_caddy(folder):
    platform = 'windows' if os.name == 'nt' else 'linux'
    extension = 'zip' if os.name == 'nt' else 'tar.gz'
    filename = f'caddy_{VERSION}_{platform}_amd64.{extension}'
    base = f'https://github.com/caddyserver/caddy/releases/download/v{VERSION}'
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        checksum = client.get(f'{base}/caddy_{VERSION}_checksums.txt')
        checksum.raise_for_status()
        expected = next(line.split()[0] for line in checksum.text.splitlines() if line.split()[-1] == filename)
        archive = client.get(f'{base}/{filename}')
        archive.raise_for_status()
    if hashlib.sha512(archive.content).hexdigest() != expected:
        raise RuntimeError('Caddy archive checksum mismatch')
    name = 'caddy.exe' if os.name == 'nt' else 'caddy'
    # Extract exactly the executable, never arbitrary archive paths.
    if os.name == 'nt':
        with zipfile.ZipFile(io.BytesIO(archive.content)) as package:
            data = package.read(name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive.content), mode='r:gz') as package:
            data = package.extractfile(name).read()
    target = folder / name
    target.write_bytes(data)
    target.chmod(0o700)
    print(f'Using SHA512-verified Caddy {VERSION}', flush=True)
    return str(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-caddy', action='store_true')
    args = parser.parse_args()
    for port in (3001, 8100, 8443, 8444):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))  # Fail rather than touching an existing server.
    admin = None
    schema = 'https_test_' + uuid4().hex
    processes, logs = [], []
    with tempfile.TemporaryDirectory(prefix='archive-https-') as temporary:
        folder = Path(temporary)
        try:
            caddy = os.getenv('CADDY_BIN') or shutil.which('caddy')
            if not caddy and args.download_caddy:
                caddy = download_caddy(folder)
            if not caddy:
                raise RuntimeError('Set CADDY_BIN or pass --download-caddy')
            if os.getenv('TEST_POSTGRES_URL'):
                root_url = make_url(os.environ['TEST_POSTGRES_URL'])
                admin = create_engine(root_url)
                with admin.begin() as db:
                    db.execute(text(f'CREATE SCHEMA {schema}'))
                database = root_url.update_query_dict({'options': f'-csearch_path={schema}'}).render_as_string(hide_password=False)
                print('HTTPS fixture: PostgreSQL random schema', flush=True)
            else:
                database = 'sqlite:///' + (folder / 'fixture.db').as_posix()
                print('HTTPS fixture: SQLite rehearsal; PostgreSQL is covered in CI', flush=True)
            env = dict(os.environ, APP_MODE='demo', VAULT_ORIGIN='http://localhost:3001',
                       TEST_HTTPS_DATABASE_URL=database, TOTP_ENCRYPTION_KEY=Fernet.generate_key().decode(),
                       PUBLIC_HOST='https://public.localhost:8444', VAULT_HOST='https://vault.localhost:8443',
                       PUBLIC_ROOT=(ROOT / 'apps/public-web/out').as_posix(), API_PORT='8100', VAULT_PORT='3001')
            env.pop('TOTP_PREVIOUS_ENCRYPTION_KEY', None)
            caddy_env = dict(env, XDG_DATA_HOME=str(folder / 'data'), XDG_CONFIG_HOME=str(folder / 'config'),
                             APPDATA=str(folder / 'appdata'), LOCALAPPDATA=str(folder / 'localappdata'))
            config = folder / 'Caddyfile'
            config.write_text('''{
    admin off
    persist_config off
    local_certs
    skip_install_trust
    auto_https disable_redirects
    default_bind 127.0.0.1
}
import "''' + (ROOT / 'infrastructure/Caddyfile').as_posix() + '"\n')
            subprocess.run([caddy, 'validate', '--config', str(config), '--adapter', 'caddyfile'], env=caddy_env, check=True,
                           stdout=subprocess.DEVNULL)
            def start(name, command, cwd=ROOT, child_env=env):
                log = (folder / f'{name}.log').open('w+')
                logs.append(log)
                processes.append(subprocess.Popen(command, cwd=cwd, env=child_env, stdout=log, stderr=subprocess.STDOUT))
            start('api', [sys.executable, str(ROOT / 'tests/e2e/secure_api.py')])
            start('next', ['node', str(ROOT / 'node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', '3001'], ROOT / 'apps/vault-web')
            start('caddy', [caddy, 'run', '--config', str(config), '--adapter', 'caddyfile'], child_env=caddy_env)
            with httpx.Client(verify=False, trust_env=False, timeout=2) as client:
                deadline = time.monotonic() + 90
                while True:
                    if any(process.poll() is not None for process in processes):
                        raise RuntimeError('HTTPS fixture process exited')
                    try:
                        headers = {'Host': 'vault.localhost:8443'}
                        health = client.get('https://127.0.0.1:8443/api/health', headers=headers, extensions={'sni_hostname': 'vault.localhost'})
                        page = client.get('https://127.0.0.1:8443/', headers=headers, extensions={'sni_hostname': 'vault.localhost'})
                        if health.status_code == page.status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError('HTTPS fixture startup timed out')
                    time.sleep(.5)
                assert health.json()['mode'] == 'secure'
                # Caddy must replace spoofed forwarding headers from untrusted clients.
                forged = client.get('https://127.0.0.1:8443/api/health', headers={**headers,
                                    'X-Forwarded-Proto': 'http', 'X-Forwarded-For': '192.0.2.10', 'X-Forwarded-Host': 'evil.test'}, extensions={'sni_hostname': 'vault.localhost'})
                assert forged.status_code == 200
                direct = client.get('http://127.0.0.1:8100/api/health', headers=headers)
                assert direct.status_code == 400
                # Caddy's unmatched host has an empty response, never the API body.
                unknown = client.get('https://127.0.0.1:8443/api/health', headers={'Host': 'evil.test'}, extensions={'sni_hostname': 'vault.localhost'})
                assert not unknown.content
                # As the trusted loopback proxy, exercise the API Host check too.
                assert client.get('http://127.0.0.1:8100/api/health', headers={
                    'Host': 'evil.test', 'X-Forwarded-Proto': 'https'}).status_code == 400
            subprocess.run(['node', str(ROOT / 'node_modules/@playwright/test/cli.js'), 'test', '--config', 'playwright.https.config.ts'],
                           cwd=ROOT, env=env, check=True)
        except Exception:
            for log in logs:
                log.flush(); log.seek(0)
                print(f'--- {Path(log.name).name} ---\n{log.read()[-6000:]}', file=sys.stderr)
            raise
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    if os.name == 'nt':
                        # Windows venv Python is a launcher with a child interpreter.
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    else:
                        process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
            for log in logs:
                log.close()
            if admin is not None:
                with admin.begin() as db:
                    db.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
                admin.dispose()


if __name__ == '__main__':
    main()
