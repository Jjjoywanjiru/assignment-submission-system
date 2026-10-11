import itertools
from datetime import datetime, timedelta

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from src.db import get_db, init_db, now_str

_counter = itertools.count(1)


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
        'DATABASE': str(tmp_path / 'test.db'),
        'UPLOAD_FOLDER': str(tmp_path / 'uploads'),
    })
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(role='student', password='secret123'):
        n = next(_counter)
        email = f'{role}{n}@usiu.ac.ke'
        reg_no = f'REG{n}' if role == 'student' else None
        with app.app_context():
            db = get_db()
            cur = db.execute(
                'INSERT INTO users (full_name, email, reg_no, password_hash, role) '
                'VALUES (?, ?, ?, ?, ?)',
                (f'{role.title()} {n}', email, reg_no,
                 generate_password_hash(password), role),
            )
            db.commit()
            return cur.lastrowid, email
    return _make


@pytest.fixture
def login_as(client):
    def _login(user_id, role='student'):
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['role'] = role
            sess['name'] = role.title()
    return _login


@pytest.fixture
def make_assignment(app, make_user):
    def _make(days=7, title='Lab 1'):
        lecturer_id, _ = make_user('lecturer')
        deadline = (datetime.now() + timedelta(days=days)).isoformat(timespec='minutes')
        with app.app_context():
            db = get_db()
            cur = db.execute(
                'INSERT INTO assignments (title, description, deadline, created_by, created_at) '
                'VALUES (?, ?, ?, ?, ?)',
                (title, 'Complete the exercises.', deadline, lecturer_id, now_str()),
            )
            db.commit()
            return cur.lastrowid
    return _make