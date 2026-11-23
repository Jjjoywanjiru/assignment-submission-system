"""The Edit button on My submissions appears only while the deadline is open."""
from datetime import datetime, timedelta

from src.db import get_db
from tests.test_student import upload


def _submission_id(app):
    with app.app_context():
        return get_db().execute('SELECT id FROM submissions').fetchone()['id']


def _set_deadline(app, assignment_id, when):
    with app.app_context():
        db = get_db()
        db.execute('UPDATE assignments SET deadline = ? WHERE id = ?',
                   (when.isoformat(timespec='minutes'), assignment_id))
        db.commit()


def test_edit_button_shown_before_deadline(app, client, make_user,
                                           make_assignment, login_as):
    assignment_id = make_assignment(days=7)
    student_id, _ = make_user('student')
    login_as(student_id)
    upload(client, assignment_id)
    link = f'/submissions/{_submission_id(app)}/edit'

    html = client.get('/my-submissions').get_data(as_text=True)
    assert link in html
    assert client.get(link).status_code == 200


def test_edit_button_hidden_after_deadline(app, client, make_user,
                                           make_assignment, login_as):
    assignment_id = make_assignment(days=7)
    student_id, _ = make_user('student')
    login_as(student_id)
    upload(client, assignment_id)
    link = f'/submissions/{_submission_id(app)}/edit'

    _set_deadline(app, assignment_id, datetime.now() - timedelta(days=1))
    html = client.get('/my-submissions').get_data(as_text=True)
    assert link not in html
    assert client.get(link).status_code == 403
