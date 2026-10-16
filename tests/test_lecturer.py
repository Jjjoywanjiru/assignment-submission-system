from src.db import get_db


def make_lecturer_assignment(app, make_assignment):
    """make_assignment() creates its own lecturer; return (assignment_id, lecturer_id)."""
    assignment_id = make_assignment()
    with app.app_context():
        row = get_db().execute(
            'SELECT created_by FROM assignments WHERE id = ?', (assignment_id,)
        ).fetchone()
    return assignment_id, row['created_by']


# --- Step 1: create + list --------------------------------------------------

def test_lecturer_pages_redirect_to_login_when_logged_out(client):
    resp = client.get('/lecturer/assignments')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_student_cannot_open_lecturer_pages(client, make_user, login_as):
    student_id, _ = make_user('student')
    login_as(student_id, 'student')
    assert client.get('/lecturer/assignments').status_code == 403
    assert client.get('/lecturer/assignments/new').status_code == 403


def test_lecturer_can_create_assignment(app, client, make_user, login_as):
    lecturer_id, _ = make_user('lecturer')
    login_as(lecturer_id, 'lecturer')
    resp = client.post('/lecturer/assignments/new', data={
        'title': 'Lab 3', 'description': 'Do the thing.',
        'deadline': '2026-12-01T10:00',
    })
    assert resp.status_code == 302
    with app.app_context():
        row = get_db().execute('SELECT * FROM assignments').fetchone()
    assert row['title'] == 'Lab 3'
    assert row['deadline'] == '2026-12-01T10:00'
    assert row['created_by'] == lecturer_id


def test_create_assignment_rejects_missing_fields_and_bad_deadline(
        app, client, make_user, login_as):
    lecturer_id, _ = make_user('lecturer')
    login_as(lecturer_id, 'lecturer')
    blank = client.post('/lecturer/assignments/new', data={
        'title': '', 'description': 'x', 'deadline': '2026-12-01T10:00'})
    bad_date = client.post('/lecturer/assignments/new', data={
        'title': 'T', 'description': 'x', 'deadline': 'next friday'})
    assert blank.status_code == 400
    assert bad_date.status_code == 400
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM assignments').fetchone()[0] == 0


def test_lecturer_only_sees_their_own_assignments(
        app, client, make_user, make_assignment, login_as):
    make_assignment(title='Someone elses')           # created by another lecturer
    me, _ = make_user('lecturer')
    login_as(me, 'lecturer')
    client.post('/lecturer/assignments/new', data={
        'title': 'Mine', 'description': 'x', 'deadline': '2026-12-01T10:00'})
    page = client.get('/lecturer/assignments').get_data(as_text=True)
    assert 'Mine' in page
    assert 'Someone elses' not in page
