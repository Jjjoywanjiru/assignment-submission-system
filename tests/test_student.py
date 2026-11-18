import io
import os

from src.db import get_db
from src.student import is_late


def upload(client, assignment_id, filename='work.pdf', data=b'my work',
           comment=''):
    return client.post(
        f'/assignments/{assignment_id}/submit',
        data={'file': (io.BytesIO(data), filename), 'comment': comment},
        content_type='multipart/form-data',
    )


# --- access control ---------------------------------------------------------

def test_student_pages_redirect_to_login_when_logged_out(client):
    for url in ('/assignments', '/my-submissions', '/assignments/1/submit'):
        resp = client.get(url)
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/login')


def test_lecturer_cannot_open_student_pages(client, make_user, login_as):
    lecturer_id, _ = make_user('lecturer')
    login_as(lecturer_id, 'lecturer')
    assert client.get('/assignments').status_code == 403
    assert client.get('/my-submissions').status_code == 403


# --- list assignments -------------------------------------------------------

def test_student_sees_available_assignments(client, make_user, make_assignment,
                                            login_as):
    make_assignment(title='Lab 1')
    make_assignment(title='Lab 2')
    student_id, _ = make_user('student')
    login_as(student_id)
    html = client.get('/assignments').get_data(as_text=True)
    assert 'Lab 1' in html and 'Lab 2' in html
    assert 'Not submitted' in html


# --- upload -----------------------------------------------------------------

def test_student_can_upload_on_time(app, client, make_user, make_assignment,
                                    login_as):
    assignment_id = make_assignment(days=7)
    student_id, _ = make_user('student')
    login_as(student_id)

    resp = upload(client, assignment_id, comment='Done')
    assert resp.status_code == 302
    with app.app_context():
        row = get_db().execute('SELECT * FROM submissions').fetchone()
    assert row['student_id'] == student_id
    assert row['status'] == 'Submitted'
    assert row['comment'] == 'Done'
    path = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
    with open(path, 'rb') as f:
        assert f.read() == b'my work'


def test_late_upload_is_marked_late(app, client, make_user, make_assignment,
                                    login_as):
    assignment_id = make_assignment(days=-1)
    student_id, _ = make_user('student')
    login_as(student_id)
    upload(client, assignment_id)
    with app.app_context():
        row = get_db().execute('SELECT status FROM submissions').fetchone()
    assert row['status'] == 'Late'


def test_upload_rejects_missing_and_bad_files(app, client, make_user,
                                              make_assignment, login_as):
    assignment_id = make_assignment()
    student_id, _ = make_user('student')
    login_as(student_id)
    assert upload(client, assignment_id, filename='').status_code == 400
    assert upload(client, assignment_id, filename='virus.exe').status_code == 400
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM submissions').fetchone()[0] == 0


def test_cannot_submit_twice(app, client, make_user, make_assignment, login_as):
    assignment_id = make_assignment()
    student_id, _ = make_user('student')
    login_as(student_id)
    upload(client, assignment_id)
    resp = upload(client, assignment_id)
    assert resp.status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM submissions').fetchone()[0] == 1


def test_submit_unknown_assignment_404(client, make_user, login_as):
    student_id, _ = make_user('student')
    login_as(student_id)
    assert client.get('/assignments/999/submit').status_code == 404


# --- status -----------------------------------------------------------------

def test_my_submissions_shows_only_own_with_timing(client, make_user,
                                                   make_assignment, login_as):
    on_time = make_assignment(days=7, title='Future lab')
    overdue = make_assignment(days=-1, title='Past lab')
    other, _ = make_user('student')
    login_as(other)
    upload(client, on_time)

    me, _ = make_user('student')
    login_as(me)
    upload(client, overdue)
    html = client.get('/my-submissions').get_data(as_text=True)
    assert 'Past lab' in html
    assert 'Future lab' not in html
    assert 'Late' in html


def test_is_late_helper():
    assert is_late('2026-01-02T10:00', '2026-01-01T10:00')
    assert not is_late('2026-01-01T10:00', '2026-01-01T10:00')
    assert not is_late('2025-12-31T23:59', '2026-01-01T10:00')
