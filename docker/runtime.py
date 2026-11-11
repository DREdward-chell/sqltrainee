"""Single-container local trainer: persistent PostgreSQL + unprivileged Jupyter."""
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

BASE = Path('/var/lib/sqltrainee')
WORK = BASE / 'work'
PGDATA = BASE / 'pgdata'
SOURCE = Path('/opt/sqltrainee')
SOCKET = Path('/tmp/sqltrainee-pg')
SECRETS = BASE / '.secrets.json'


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def pgctl(*args):
    return run(['gosu', 'postgres', 'pg_ctl', '-D', str(PGDATA), *args])


def admin(sql=None, file=None, db='sqltrainee'):
    args = ['psql', '-X', '-h', str(SOCKET), '-U', 'sqltrainer_admin', '-d', db,
            '-v', 'ON_ERROR_STOP=1', '--no-psqlrc']
    if sql is not None:
        return run(args + ['-Atc', sql], capture_output=True, text=True).stdout.strip()
    with (WORK / 'data/bootstrap.log').open('w') as log:
        run(args + ['--single-transaction', '-f', str(file)], stdout=log)


def owned_file(path, text, uid=1000, mode=0o600):
    path.write_text(text)
    path.chmod(mode)
    os.chown(path, uid, uid)


def prepare_work():
    WORK.mkdir(parents=True, exist_ok=True)
    # Update program files, but never overwrite notebooks, answers or progress.
    for name in ('trainer', 'solutions', 'sql', 'tests', 'scripts'):
        shutil.copytree(SOURCE / name, WORK / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('training.ipynb', 'exam.ipynb', 'README.md'):
        if not (WORK / name).exists():
            shutil.copy2(SOURCE / name, WORK / name)
    if not (WORK / 'models').exists():
        shutil.copytree(SOURCE / 'models', WORK / 'models')
    (WORK / 'answers').mkdir(exist_ok=True)
    (WORK / 'data').mkdir(exist_ok=True)
    for n in range(1, 51):
        answer = WORK / f'answers/{n:02}.sql'
        if not answer.exists():
            answer.write_text('-- Напиши SQL-запрос.\n')
    run(['chown', '-R', 'learner:learner', str(WORK)])


def credentials():
    if not SECRETS.exists():
        owned_file(SECRETS, json.dumps({k: secrets.token_urlsafe(32)
                   for k in ('admin', 'reader', 'token')}), uid=0)
    return json.loads(SECRETS.read_text())


def seed(reset=False):
    run(['python', str(WORK / 'scripts/seed.py')])
    target = WORK / 'data/bootstrap.sql'
    content = (WORK / 'data/seed.sql').read_text()
    if reset:
        content = 'DROP SCHEMA IF EXISTS public,check_1,check_2,check_3,check_empty CASCADE;\n' + content
    content += '\nREVOKE CREATE ON SCHEMA public FROM PUBLIC;\n'
    target.write_text(content)
    # DDL and all five fixtures commit together; failed initialization is retryable.
    admin(file=target)
    run(['chown', '-R', 'learner:learner', str(WORK / 'data')])


def start_database(keys):
    SOCKET.mkdir(exist_ok=True)
    run(['chown', 'postgres:postgres', str(SOCKET)])
    SOCKET.chmod(0o700)
    if not (PGDATA / 'PG_VERSION').exists():
        PGDATA.mkdir(exist_ok=True)
        run(['chown', 'postgres:postgres', str(PGDATA)])
        password_file = SOCKET / 'init-password'
        # postgres uid is image-defined, so use chown by name.
        password_file.write_text(keys['admin'])
        password_file.chmod(0o600)
        run(['chown', 'postgres:postgres', str(password_file)])
        try:
            run(['gosu', 'postgres', 'initdb', '-D', str(PGDATA), '-U', 'sqltrainer_admin',
                 '--encoding=UTF8', '--locale=C', '--auth-local=trust', '--auth-host=scram-sha-256',
                 '--pwfile=' + str(password_file)])
        finally:
            password_file.unlink(missing_ok=True)
        with (PGDATA / 'postgresql.conf').open('a') as f:
            f.write("\nlisten_addresses = '127.0.0.1'\nport = 5432\ntimezone = 'Europe/Moscow'\n"
                    f"unix_socket_directories = '{SOCKET}'\n")
    pgctl('-w', 'start')
    if admin("SELECT count(*) FROM pg_database WHERE datname='sqltrainee'", db='postgres') == '0':
        admin('CREATE DATABASE sqltrainee', db='postgres')
    if admin("SELECT count(*) FROM pg_roles WHERE rolname='sqltrainee'") == '0':
        # Passwords are generated URL-safe strings, never user-supplied SQL.
        admin(f"CREATE ROLE sqltrainee LOGIN PASSWORD '{keys['reader']}'; "
              'ALTER ROLE sqltrainee SET default_transaction_read_only=on;')
    admin('REVOKE TEMP ON DATABASE sqltrainee FROM PUBLIC; REVOKE CREATE ON SCHEMA public FROM PUBLIC;')
    if admin("SELECT to_regclass('public.projects') IS NULL") == 't':
        seed()


def learner_environment(keys):
    env = os.environ.copy()
    env.pop('SQLTRAINER_ADMIN_PASSWORD', None)
    env.update(HOME='/home/learner', SQLTRAINER_PASSWORD=keys['reader'],
               PGPASSWORD=keys['reader'], JUPYTER_TOKEN=keys['token'])
    return env


def health():
    run(['pg_isready', '-h', '127.0.0.1', '-p', '5432'], stdout=subprocess.DEVNULL)
    with urllib.request.urlopen('http://127.0.0.1:8888/api', timeout=3) as r:
        assert r.status == 200


def serve():
    BASE.mkdir(parents=True, exist_ok=True)
    prepare_work()
    keys = credentials()
    jupyter = None
    stopping = False

    def terminate(signum, frame):
        nonlocal stopping
        stopping = True
        if jupyter and jupyter.poll() is None:
            jupyter.terminate()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        start_database(keys)
        if stopping:
            return
        owned_file(WORK / '.reader-password', keys['reader'])
        owned_file(WORK / '.jupyter-token', keys['token'])
        print('\nSQL-тренажёр готов. Открой ссылку в браузере:\n'
              f"http://127.0.0.1:8888/lab/tree/training.ipynb?token={keys['token']}\n", flush=True)
        jupyter = subprocess.Popen(['gosu', 'learner', 'jupyter', 'lab', '--ip=0.0.0.0', '--port=8888',
                      '--no-browser', '--ServerApp.port_retries=0', '--ServerApp.root_dir=' + str(WORK),
                      '--ServerApp.default_url=/lab/tree/training.ipynb'],
                      cwd=WORK, env=learner_environment(keys))
        while jupyter.poll() is None and not stopping:
            time.sleep(1)
            if subprocess.run(['pg_isready', '-q', '-h', '127.0.0.1'], check=False).returncode:
                raise RuntimeError('PostgreSQL stopped unexpectedly')
        if not stopping and jupyter.returncode:
            raise RuntimeError(f'Jupyter exited with code {jupyter.returncode}')
    finally:
        if jupyter and jupyter.poll() is None:
            jupyter.terminate()
            try:
                jupyter.wait(timeout=15)
            except subprocess.TimeoutExpired:
                jupyter.kill()
                jupyter.wait()
        if (PGDATA / 'postmaster.pid').exists():
            pgctl('-m', 'fast', '-w', 'stop')


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    if command == 'serve':
        serve()
    elif command == 'health':
        health()
    elif command == 'url':
        print('http://127.0.0.1:8888/lab/tree/training.ipynb?token=' + (WORK / '.jupyter-token').read_text())
    elif command == 'reset-db' and sys.argv[2:] == ['--yes']:
        seed(reset=True)
    elif command == 'test':
        keys = credentials()
        env = learner_environment(keys)
        env['SQLTRAINER_ADMIN_PASSWORD'] = keys['admin']
        run(['python', 'tests/selftest.py'], cwd=WORK, env=env)
        run(['python', '/opt/sqltrainee/docker/notebook_test.py'], cwd=WORK, env=env)
    else:
        raise SystemExit('Commands: serve, health, url, test, reset-db --yes')

if __name__ == '__main__':
    main()
