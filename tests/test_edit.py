"""Tests for CR-001: edit a submission before the deadline."""
import io
import os
from datetime import datetime, timedelta

import pytest

from app import create_app
from src.db import get_db, init_db

FMT = '%Y-%m-%dT%H:%M'


def _when(days):
    return (datetime.now() + timedelta(days=days)).strftime(FMT)


@pytest.fixture
def edit_app(tmp_path):
    app = create_app({
        'TESTING': True,
        'DATABASE': str(tmp_path / 'test.db'),
        'UPLOAD_FOLDER': str(tmp_path / 'uploads'),
    })
    with app.app_context():
        init_db()
        db = get_db()
        for uid, name, email, role in [
            (1, 'Lecturer', 'l@x.com', 'lecturer'),
            (10, 'Student A', 'a@x.com', 'student'),
            (11, 'Student B', 'b@x.com', 'student'),
        ]:
            db.execute('INSERT INTO users (id, full_name, email, password_hash,'
                       ' role) VALUES (?, ?, ?, ?, ?)',
                       (uid, name, email, 'x', role))
        # assignment 1 open, assignment 2 closed
        db.execute("INSERT INTO assignments VALUES (1, 'Open task', 'd', ?, 1, ?)",
                   (_when(2), _when(-5)))
        db.execute("INSERT INTO assignments VALUES (2, 'Closed task', 'd', ?, 1, ?)",
                   (_when(-2), _when(-9)))
        # sub 1: student 10 open | sub 2: student 10 closed | sub 3: student 11 open
        for sid, aid, stu, fn in [(1, 1, 10, '1_10_old.txt'),
                                  (2, 2, 10, '2_10_old.txt'),
                                  (3, 1, 11, '1_11_old.txt')]:
            db.execute('INSERT INTO submissions (id, assignment_id, student_id,'
                       ' filename, comment, submitted_at, status) '
                       "VALUES (?, ?, ?, ?, 'first', ?, 'Submitted')",
                       (sid, aid, stu, fn, _when(-3)))
        db.commit()
    upload = tmp_path / 'uploads'
    upload.mkdir(exist_ok=True)
    (upload / '1_10_old.txt').write_text('old')
    return app


@pytest.fixture
def edit_client(edit_app):
    return edit_app.test_client()


def login(client, user_id=10, role='student'):
    with client.session_transaction() as s:
        s['user_id'] = user_id
        s['role'] = role


def post(client, sid, file=None, comment='first'):
    data = {'comment': comment}
    if file:
        data['file'] = (io.BytesIO(b'new content'), file)
    return client.post(f'/submissions/{sid}/edit', data=data,
                       content_type='multipart/form-data')


def row(app, sid):
    with app.app_context():
        return dict(get_db().execute(
            'SELECT * FROM submissions WHERE id = ?', (sid,)).fetchone())


def test_requires_login(edit_client):
    r = edit_client.get('/submissions/1/edit')
    assert r.status_code == 302
    assert r.headers['Location'].endswith('/login')


def test_lecturer_forbidden(edit_client):
    login(edit_client, user_id=1, role='lecturer')
    assert edit_client.get('/submissions/1/edit').status_code == 403


def test_other_students_submission_is_404(edit_client):
    login(edit_client, user_id=10)
    assert edit_client.get('/submissions/3/edit').status_code == 404


def test_unknown_submission_is_404(edit_client):
    login(edit_client)
    assert edit_client.get('/submissions/999/edit').status_code == 404


def test_edit_page_loads_before_deadline(edit_client):
    login(edit_client)
    r = edit_client.get('/submissions/1/edit')
    assert r.status_code == 200
    assert b'Save changes' in r.data


def test_replace_file_before_deadline(edit_client, edit_app):
    login(edit_client)
    r = post(edit_client, 1, file='new.txt', comment='updated')
    assert r.status_code == 302
    data = row(edit_app, 1)
    assert data['filename'].endswith('_new.txt')
    assert data['comment'] == 'updated'
    assert data['updated_at'] is not None
    assert data['status'] == 'Submitted'
    uploads = edit_app.config['UPLOAD_FOLDER']
    assert os.path.exists(os.path.join(uploads, data['filename']))
    assert not os.path.exists(os.path.join(uploads, '1_10_old.txt'))


def test_comment_only_edit_keeps_file(edit_client, edit_app):
    login(edit_client)
    post(edit_client, 1, comment='better comment')
    data = row(edit_app, 1)
    assert data['filename'] == '1_10_old.txt'
    assert data['comment'] == 'better comment'
    assert data['updated_at'] is not None


def test_edit_blocked_after_deadline(edit_client, edit_app):
    login(edit_client)
    assert edit_client.get('/submissions/2/edit').status_code == 403
    r = post(edit_client, 2, file='new.txt', comment='hack')
    assert r.status_code == 403
    data = row(edit_app, 2)
    assert data['filename'] == '2_10_old.txt'
    assert data['comment'] == 'first'
    assert data['updated_at'] is None


def test_rejects_disallowed_file_type(edit_client, edit_app):
    login(edit_client)
    r = post(edit_client, 1, file='virus.exe')
    assert r.status_code == 400
    assert row(edit_app, 1)['filename'] == '1_10_old.txt'
